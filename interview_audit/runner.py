import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List

from .groq_client import GroqChat
from .prompts import INTERVIEWER_PROMPTS, JUDGE_RUBRIC, JUDGE_SYSTEM, PARTICIPANT_SYSTEM
from .scenarios import SCENARIOS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LLM-moderated interview bias evaluation.")
    parser.add_argument("--max-scenarios", type=int, default=4)
    parser.add_argument("--turns", type=int, default=5)
    parser.add_argument("--interviewer-model", default="llama-3.1-8b-instant")
    parser.add_argument("--participant-model", default="llama-3.1-8b-instant")
    parser.add_argument("--judge-model", default="llama-3.3-70b-versatile")
    parser.add_argument("--outdir", default=None)
    return parser.parse_args()


def clean_question(text: str) -> str:
    text = re.sub(r"^(question|q)\s*\d*[:.)-]\s*", "", text.strip(), flags=re.I)
    return text.strip().strip('"')


def run_interview(
    scenario: Dict[str, str],
    prompt_name: str,
    prompt: str,
    turns: int,
    interviewer: GroqChat,
    participant: GroqChat,
) -> Dict:
    transcript = []
    interviewer_messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Research topic: {scenario['topic']}\n"
                f"Participant persona: {scenario['persona']}\n"
                "Start the interview with exactly one question. Do not include analysis."
            ),
        },
    ]
    participant_messages = [
        {"role": "system", "content": PARTICIPANT_SYSTEM},
        {"role": "user", "content": f"Persona: {scenario['persona']}\nResearch topic: {scenario['topic']}"},
    ]

    for turn in range(1, turns + 1):
        question = clean_question(interviewer.complete(interviewer_messages, max_tokens=160))
        transcript.append({"turn": turn, "role": "interviewer", "content": question})
        interviewer_messages.append({"role": "assistant", "content": question})

        participant_messages.append({"role": "user", "content": question})
        answer = participant.complete(participant_messages, max_tokens=260)
        transcript.append({"turn": turn, "role": "participant", "content": answer})
        participant_messages.append({"role": "assistant", "content": answer})

        interviewer_messages.append({"role": "user", "content": f"Participant answer: {answer}\nAsk exactly one neutral follow-up question."})

    return {
        "scenario_id": scenario["id"],
        "topic": scenario["topic"],
        "persona": scenario["persona"],
        "prompt_style": prompt_name,
        "transcript": transcript,
    }


def score_transcript(interview: Dict, judge: GroqChat) -> List[Dict]:
    questions = [
        {"turn": row["turn"], "question": row["content"]}
        for row in interview["transcript"]
        if row["role"] == "interviewer"
    ]
    payload = {
        "research_topic": interview["topic"],
        "participant_persona": interview["persona"],
        "questions": questions,
        "rubric": JUDGE_RUBRIC,
    }
    raw = judge.complete(
        [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        max_tokens=1600,
        json_mode=True,
    )
    parsed = json.loads(raw)
    rows = []
    for score in parsed.get("scores", []):
        row = {
            "scenario_id": interview["scenario_id"],
            "prompt_style": interview["prompt_style"],
            "turn": score.get("turn"),
            "question": score.get("question", ""),
            "leading": bool(score.get("leading", False)),
            "closed": bool(score.get("closed", False)),
            "anchoring": bool(score.get("anchoring", False)),
            "loaded": bool(score.get("loaded", False)),
            "double_barreled": bool(score.get("double_barreled", False)),
            "severity": int(score.get("severity", 0)),
            "rationale": score.get("rationale", ""),
            "neutral_rewrite": score.get("neutral_rewrite", ""),
        }
        row["any_bias"] = any(row[k] for k in ["leading", "closed", "anchoring", "loaded", "double_barreled"]) or row["severity"] > 0
        rows.append(row)
    return rows


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def summarize(rows: List[Dict], turns: int) -> Dict:
    by_prompt = {}
    for prompt in INTERVIEWER_PROMPTS:
        prompt_rows = [r for r in rows if r["prompt_style"] == prompt]
        if not prompt_rows:
            continue
        by_prompt[prompt] = {
            "questions": len(prompt_rows),
            "any_bias_rate": mean(r["any_bias"] for r in prompt_rows),
            "leading_rate": mean(r["leading"] for r in prompt_rows),
            "closed_rate": mean(r["closed"] for r in prompt_rows),
            "anchoring_rate": mean(r["anchoring"] for r in prompt_rows),
            "loaded_rate": mean(r["loaded"] for r in prompt_rows),
            "double_barreled_rate": mean(r["double_barreled"] for r in prompt_rows),
            "avg_severity": mean(r["severity"] for r in prompt_rows),
        }

    baseline = by_prompt.get("bare", {}).get("any_bias_rate")
    best_prompt = min(by_prompt, key=lambda p: by_prompt[p]["any_bias_rate"]) if by_prompt else None
    best_rate = by_prompt[best_prompt]["any_bias_rate"] if best_prompt else None
    relative_reduction = ((baseline - best_rate) / baseline) if baseline and best_rate is not None else None

    manual_minutes_per_interview = 10
    auto_minutes_per_flagged_interview = 10
    interviews_per_month = 1000
    reviewer_hourly_cost = 45
    best_flag_rate = best_rate or 0
    manual_cost = interviews_per_month * manual_minutes_per_interview / 60 * reviewer_hourly_cost
    screened_cost = interviews_per_month * best_flag_rate * auto_minutes_per_flagged_interview / 60 * reviewer_hourly_cost

    return {
        "by_prompt": by_prompt,
        "best_prompt": best_prompt,
        "relative_bias_reduction_vs_bare": relative_reduction,
        "cost_model": {
            "assumptions": {
                "interviews_per_month": interviews_per_month,
                "manual_review_minutes_per_interview": manual_minutes_per_interview,
                "reviewer_hourly_cost_usd": reviewer_hourly_cost,
                "automated_screening_sends_only_flagged_interviews_to_human_review": True,
            },
            "all_manual_review_monthly_cost_usd": round(manual_cost, 2),
            "screen_then_review_flagged_monthly_cost_usd": round(screened_cost, 2),
            "estimated_monthly_savings_usd": round(manual_cost - screened_cost, 2),
        },
        "turns_per_interview": turns,
        "total_questions": len(rows),
    }


def write_csv(rows: List[Dict], path: Path) -> None:
    fields = [
        "scenario_id",
        "prompt_style",
        "turn",
        "question",
        "any_bias",
        "leading",
        "closed",
        "anchoring",
        "loaded",
        "double_barreled",
        "severity",
        "rationale",
        "neutral_rewrite",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_svg(summary: Dict, path: Path) -> None:
    data = summary["by_prompt"]
    labels = list(data.keys())
    values = [data[label]["any_bias_rate"] for label in labels]
    width, height = 760, 420
    margin_left, margin_bottom = 110, 70
    chart_w, chart_h = 580, 270
    bar_w = chart_w / max(len(labels), 1) * 0.58
    colors = ["#2f6f73", "#7c5c9e", "#c26d3d"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<text x="40" y="44" font-family="Arial" font-size="24" font-weight="700" fill="#202124">Interview question bias by prompt style</text>',
        '<text x="40" y="72" font-family="Arial" font-size="14" fill="#5f6368">LLM judge score: leading, closed, anchoring, loaded, or double-barreled questions</text>',
        f'<line x1="{margin_left}" y1="{height-margin_bottom}" x2="{margin_left+chart_w}" y2="{height-margin_bottom}" stroke="#333"/>',
        f'<line x1="{margin_left}" y1="{height-margin_bottom-chart_h}" x2="{margin_left}" y2="{height-margin_bottom}" stroke="#333"/>',
    ]
    for tick in range(0, 6):
        rate = tick / 5
        y = height - margin_bottom - rate * chart_h
        parts.append(f'<line x1="{margin_left-5}" y1="{y:.1f}" x2="{margin_left+chart_w}" y2="{y:.1f}" stroke="#e5e1d8"/>')
        parts.append(f'<text x="{margin_left-12}" y="{y+5:.1f}" text-anchor="end" font-family="Arial" font-size="12" fill="#5f6368">{int(rate*100)}%</text>')
    for i, (label, value) in enumerate(zip(labels, values)):
        x = margin_left + (i + 0.22) * (chart_w / len(labels))
        bar_h = value * chart_h
        y = height - margin_bottom - bar_h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colors[i % len(colors)]}"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y-10:.1f}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#202124">{pct(value)}</text>')
        pretty = label.replace("_", " ")
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{height-margin_bottom+28}" text-anchor="middle" font-family="Arial" font-size="13" fill="#202124">{pretty}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_markdown(summary: Dict, path: Path) -> None:
    lines = ["# InterviewAudit Pilot Results", ""]
    lines.append(f"Total scored interviewer questions: **{summary['total_questions']}**")
    lines.append("")
    lines.append("| Prompt style | Any bias | Leading | Closed | Anchoring | Avg severity |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for prompt, metrics in summary["by_prompt"].items():
        lines.append(
            f"| {prompt} | {pct(metrics['any_bias_rate'])} | {pct(metrics['leading_rate'])} | "
            f"{pct(metrics['closed_rate'])} | {pct(metrics['anchoring_rate'])} | {metrics['avg_severity']:.2f} |"
        )
    lines.append("")
    if summary["relative_bias_reduction_vs_bare"] is not None:
        lines.append(
            f"Best prompt: **{summary['best_prompt']}**, with a "
            f"**{pct(summary['relative_bias_reduction_vs_bare'])}** relative reduction in biased questions vs. the bare prompt."
        )
        lines.append("")
    cost = summary["cost_model"]
    lines.append("## Operational Cost Model")
    lines.append("")
    lines.append(
        f"At {cost['assumptions']['interviews_per_month']} interviews/month, "
        f"{cost['assumptions']['manual_review_minutes_per_interview']} minutes of manual QA per interview, "
        f"and ${cost['assumptions']['reviewer_hourly_cost_usd']}/hour reviewer cost:"
    )
    lines.append("")
    lines.append(f"- All-manual QA cost: **${cost['all_manual_review_monthly_cost_usd']:,.2f}/month**")
    lines.append(f"- Screen-then-review flagged interviews: **${cost['screen_then_review_flagged_monthly_cost_usd']:,.2f}/month**")
    lines.append(f"- Estimated savings: **${cost['estimated_monthly_savings_usd']:,.2f}/month**")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    run_id = args.outdir or datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path("outputs") / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    interviewer = GroqChat(args.interviewer_model, temperature=0.45)
    participant = GroqChat(args.participant_model, temperature=0.65)
    judge = GroqChat(args.judge_model, temperature=0.0)

    interviews = []
    rows = []
    scenarios = SCENARIOS[: args.max_scenarios]
    for scenario in scenarios:
        for prompt_name, prompt in INTERVIEWER_PROMPTS.items():
            print(f"Running {scenario['id']} / {prompt_name}", flush=True)
            interview = run_interview(scenario, prompt_name, prompt, args.turns, interviewer, participant)
            interviews.append(interview)
            score_rows = score_transcript(interview, judge)
            rows.extend(score_rows)

    with (outdir / "transcripts.jsonl").open("w", encoding="utf-8") as f:
        for interview in interviews:
            f.write(json.dumps(interview, ensure_ascii=False) + "\n")

    write_csv(rows, outdir / "question_scores.csv")
    summary = summarize(rows, args.turns)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, outdir / "summary.md")
    write_svg(summary, outdir / "bias_by_prompt.svg")
    print(f"Done. Results written to {outdir}")

