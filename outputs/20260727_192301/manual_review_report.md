# Manual Review Report

Manual validation was run on a deterministic 15-question sample from the full 216-question evaluation.

Result:

- Completed human labels: 15
- Agreement with LLM judge: 12/15 (80.0%)

All three disagreements were cases where the human label was stricter than the judge label:

- `review_id=6`: Human marked the question biased because "effective workout recommendations and progress tracking" implies a positive product outcome.
- `review_id=12`: Human marked the question biased because "most frustrating" assumes the experience was frustrating.
- `review_id=15`: Human marked the question biased because it assumes simultaneous note-taking becomes difficult.

Interpretation:

The judge labels are directionally useful, but likely conservative on subtle assumptions and positive-outcome wording. Public claims should describe the result as an LLM-judged audit with a small manual sanity check, not as a fully human-annotated benchmark.

