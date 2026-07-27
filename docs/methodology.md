# Methodology

## Company Pain Point

Listen Labs markets AI-moderated customer interviews, adaptive probing, traceable analysis, and quality screening. That makes interviewer neutrality a core product-quality issue: if the AI moderator asks leading questions, the resulting insights can look polished while being methodologically contaminated.

Relevant public product pages:

- Listen Labs home: https://listenlabs.ai/
- AI moderator page: https://listenlabs.ai/features/ai-moderator
- Quality Guard page: https://listenlabs.ai/features/quality-guard

## Research Basis

The rubric is grounded in basic survey and qualitative-research standards:

- Avoid question wording that pushes respondents toward one side.
- Ask about one concept at a time.
- Prefer short, clear, neutral wording.
- Avoid question order or framing that influences the answer.

Reference:

- AAPOR Best Practices for Survey Research: https://aapor.org/standards-and-ethics/best-practices/

## Evaluation Design

Each scenario is a realistic user-research objective, such as evaluating checkout flow abandonment or understanding student budgeting behavior.

For every scenario, the evaluation compares three interviewer prompt styles:

1. `bare`: generic AI user-research interviewer.
2. `ux_guidelines`: explicitly trained on neutral qualitative interviewing behavior.
3. `bias_guardrail`: strict pre-question self-check for leading, loaded, closed, double-barreled, or anchoring phrasing.

The evaluation uses three model roles:

- Interviewer model: asks one question at a time.
- Participant model: answers from a realistic persona.
- Judge model: scores every interviewer question with a structured rubric.

## Metrics

Question-level labels:

- `leading`
- `closed`
- `anchoring`
- `loaded`
- `double_barreled`
- `severity`, from 0 to 3

Aggregate metrics:

- Any-bias rate
- Leading-question rate
- Closed-question rate
- Anchoring-question rate
- Average severity
- Relative bias reduction versus the bare prompt

## Operational Value

The cost model is intentionally simple. It estimates what happens if every interview would otherwise receive 10 minutes of manual QA review, but an automated bias screen allows human researchers to focus only on flagged interviews.

This is not a financial claim about Listen Labs. It is a reusable ROI framing for why interviewer-bias detection matters in an AI-research platform.

