# InterviewAudit

InterviewAudit measures whether LLM-moderated user-research interviews ask biased, leading, closed, or anchoring questions.

The project is built around a practical pain point for AI research-interview products: customers trust AI moderators to collect clean user feedback, but leading questions can quietly distort the answers and waste researcher review time.

## Research Anchor

This project uses well-established survey and qualitative research guidance:

- Leading and loaded questions can bias participant responses.
- Open-ended, neutral questions are preferred for exploratory user research.
- Interview quality can be audited at the question level with a structured rubric.

The core evaluation question:

> When an LLM is asked to moderate user interviews, how often does it lead the participant, and how much does explicit UX-research prompting reduce that risk?

Company relevance:

- Listen Labs says its platform replaces manual research methods with AI-moderated customer interviews: https://listenlabs.ai/
- Its AI moderator page emphasizes adaptive probing, neutral tone, and research best practices: https://listenlabs.ai/features/ai-moderator
- Its Quality Guard page describes quality scoring and human review for interview responses: https://listenlabs.ai/features/quality-guard
- AAPOR survey best practices warn against biased wording that pushes respondents toward a specific answer: https://aapor.org/standards-and-ethics/best-practices/

## What It Runs

The evaluation uses Groq-hosted models to run simulated user interviews:

1. An LLM interviewer asks questions about a product-research scenario.
2. An LLM participant answers as a realistic user persona.
3. A separate LLM judge scores every interviewer question with a bias rubric.
4. The pipeline writes transcripts, CSV results, JSON summaries, and SVG charts.

No training, GPU, web app, or paid infrastructure is required.

## Setup

Create a Groq API key at `console.groq.com`, then set it as an environment variable:

```bash
export GROQ_API_KEY="your_key_here"
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run a quick live test:

```bash
python3 run_eval.py --max-scenarios 1 --turns 3
```

Run a larger evaluation:

```bash
python3 run_eval.py --max-scenarios 12 --turns 6
```

## Outputs

Results are written to `outputs/<run_id>/`:

- `transcripts.jsonl`: full interview transcripts
- `question_scores.csv`: one row per interviewer question
- `summary.json`: aggregate metrics
- `summary.md`: readable findings
- `bias_by_prompt.svg`: chart for LinkedIn or email

The included full run is in `outputs/20260727_192301/`.

Full-run headline:

- Total scored interviewer questions: 216
- Bare interviewer prompt: 87.5% biased-question rate
- UX-guidelines prompt: 75.0% biased-question rate
- Strict bias-guardrail prompt: 38.9% biased-question rate
- Relative reduction from bare to guardrail: 55.6%

Create a manual review sample:

```bash
python3 scripts/sample_for_review.py outputs/20260727_192301/question_scores.csv
```

Open `outputs/20260727_192301/manual_review_blind.csv`, fill `your_label_any_bias` with `TRUE` or `FALSE`, then compare against the judge labels. This is a lightweight sanity check, not a replacement for a full human-annotation study.

After labeling the sample, calculate agreement:

```bash
python3 scripts/score_manual_review.py outputs/20260727_192301/manual_review_blind.csv --answers outputs/20260727_192301/manual_review_sample.csv
```

## Why This Matters

For a company running AI-moderated interviews, biased questions are not just a research-quality issue. They create operational cost:

- Researchers spend more time reviewing flawed transcripts.
- Customers may make product decisions from contaminated feedback.
- Trust drops if the AI moderator appears suggestive or salesy.

InterviewAudit estimates how much automated bias screening can reduce manual QA review while preserving methodological quality. The cost model is illustrative and should be recalibrated with a real team's interview volume, QA workflow, and reviewer cost.

## Outreach Angle

Suggested framing:

> I ran a 216-question audit of LLM-moderated user interviews and found that generic "be a good interviewer" prompting still produced measurable leading and anchoring questions. Research-methods prompting helped, and a stricter bias guardrail helped more, but neither eliminated the issue. The useful product opportunity is moderator QA: automatically flag when the AI interviewer shaped the answer before customers ever read the transcript.
