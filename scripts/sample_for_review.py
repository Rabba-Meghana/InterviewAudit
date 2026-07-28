#!/usr/bin/env python3
import argparse
import csv
import random
from pathlib import Path


REVIEW_FIELDS = [
    "review_id",
    "scenario_id",
    "prompt_style",
    "turn",
    "question",
    "your_label_any_bias",
    "judge_any_bias",
    "judge_leading",
    "judge_closed",
    "judge_anchoring",
    "judge_loaded",
    "judge_double_barreled",
    "judge_severity",
    "judge_rationale",
    "judge_neutral_rewrite",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a small manual-review sample from InterviewAudit question scores."
    )
    parser.add_argument("scores_csv", help="Path to question_scores.csv")
    parser.add_argument("--n", type=int, default=15, help="Number of rows to sample")
    parser.add_argument("--seed", type=int, default=7, help="Deterministic random seed")
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path. Defaults to manual_review_sample.csv next to the input file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scores_path = Path(args.scores_csv)
    out_path = Path(args.out) if args.out else scores_path.with_name("manual_review_sample.csv")

    with scores_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit(f"No rows found in {scores_path}")

    rng = random.Random(args.seed)
    sample_size = min(args.n, len(rows))

    grouped = {}
    for row in rows:
        grouped.setdefault(row["prompt_style"], []).append(row)

    sample = []
    per_group = max(1, sample_size // max(1, len(grouped)))
    for prompt_rows in grouped.values():
        sample.extend(rng.sample(prompt_rows, min(per_group, len(prompt_rows))))

    remaining = [row for row in rows if row not in sample]
    if len(sample) < sample_size:
        sample.extend(rng.sample(remaining, sample_size - len(sample)))

    rng.shuffle(sample)

    out_rows = []
    for index, row in enumerate(sample, start=1):
        out_rows.append(
            {
                "review_id": index,
                "scenario_id": row["scenario_id"],
                "prompt_style": row["prompt_style"],
                "turn": row["turn"],
                "question": row["question"],
                "your_label_any_bias": "",
                "judge_any_bias": row["any_bias"],
                "judge_leading": row["leading"],
                "judge_closed": row["closed"],
                "judge_anchoring": row["anchoring"],
                "judge_loaded": row["loaded"],
                "judge_double_barreled": row["double_barreled"],
                "judge_severity": row["severity"],
                "judge_rationale": row["rationale"],
                "judge_neutral_rewrite": row["neutral_rewrite"],
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {out_path}")
    print("Fill your_label_any_bias with TRUE/FALSE before comparing with the judge columns.")


if __name__ == "__main__":
    main()

