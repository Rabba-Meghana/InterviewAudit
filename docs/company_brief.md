# Company Brief: Listen Labs

## One-Line Pitch

I built a Groq-powered audit that measures when AI interviewers accidentally ask leading, closed, or anchoring questions during user-research interviews.

## Why Listen Labs Should Care

Listen Labs sells AI-moderated interviews at scale. Their public product pages emphasize adaptive probing, research best practices, traceability, and Quality Guard. That is exactly where question neutrality matters: a participant-quality system can still miss a moderator-quality problem.

The risk:

> A transcript can look rich and useful while the AI interviewer subtly shaped the participant's answers.

That creates three costs:

- More human QA time spent reviewing questionable interviews.
- Lower customer trust if AI moderation feels suggestive.
- Worse product decisions if teams act on biased qualitative data.

## What I Tested

I ran simulated user-research interviews with three prompt styles:

- Generic AI interviewer prompt.
- UX-research-guideline prompt.
- Strict bias-guardrail prompt.

Each interviewer question was scored for:

- leading wording
- closed wording
- anchoring
- loaded language
- double-barreled structure
- severity

## Full-Run Result

In the full 216-question Groq run:

- Bare prompt: 87.5% of questions had at least one bias issue.
- UX-guidelines prompt: 75.0%.
- Bias-guardrail prompt: 38.9%.

That is a 55.6% relative reduction versus the bare prompt.

Important limitation: these labels come from an LLM judge. Before using the result as a strong public claim, run the included manual-review sample and report human agreement honestly.

## Practical Product Angle

This suggests a useful product feature:

> Moderator Quality Guard: score the AI interviewer's questions in real time, not only the participant's answers.

Instead of only checking whether participants are low-quality or fraudulent, the system can also check whether the moderator caused the quality problem.

## Why This Saves Money

The cost model assumes:

- 1,000 interviews/month
- 10 minutes of manual QA per interview
- $45/hour reviewer cost

All-manual QA would cost about $7,500/month. If automated screening routes only flagged interviews to human review, the full-run model estimates about $4,583/month in QA savings.

The exact dollar value should be recalibrated with real Listen Labs volumes and review workflows, but the direction is clear: better moderator QA means fewer bad transcripts need expensive human cleanup.
