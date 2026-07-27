# LinkedIn Post Draft

I ran a small audit of LLM-moderated user-research interviews.

The question was simple:

> When an AI interviewer conducts customer interviews, how often does it accidentally lead the participant?

This matters because leading questions can quietly ruin qualitative research. "Don't you think this checkout flow is easier?" is very different from "What do you think of this checkout flow?"

I built a Groq-powered eval with:

- simulated research scenarios
- an AI interviewer
- an AI participant
- an LLM judge scoring each interviewer question
- a rubric for leading, closed, anchoring, loaded, and double-barreled questions

In the pilot run, the generic interviewer prompt produced bias issues in 75.0% of questions. A UX-guidelines prompt reduced that to 62.5%. A stricter bias-guardrail prompt reduced it to 25.0%.

The interesting takeaway:

Better prompting helps, but the bigger product opportunity is automatic moderator QA. AI research platforms should not only score participant response quality. They should also score whether the AI moderator shaped the answer in the first place.

This is especially relevant for AI-moderated research products like Listen Labs, where trust depends on interviews being scalable and methodologically clean.

Repo: https://github.com/Rabba-Meghana/InterviewAudit

