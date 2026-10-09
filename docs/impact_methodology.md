# Impact scoring methodology — baseline 1.0

This is an **explicit expert-designed baseline**, not a model trained on impact labels and not a validated financial-risk measure. The weights are initial design choices that must be tested and calibrated against reviewed examples.

| Component | Weight | Operational meaning |
|---|---:|---|
| Event severity | 35% | How severe the event itself is, supported by text/evidence |
| Business/financial consequence | 25% | Plausible revenue, cost, funding, credit, or operational consequences supported by evidence |
| Scope | 20% | Isolated, business-unit, company-wide, industry-wide, or systemic reach |
| Entity relevance | 10% | How directly the text concerns the company/asset being assessed |
| Sentiment magnitude | 10% | `abs(sentiment_score)`; captures strength, not direction |

Formula: `R = .35E + .25C + .20S + .10N + .10*abs(sentiment)` where each component is in `[0, 1]`.

Integer impact: `clip(round(1 + 9*R), 1, 10)`.

## Guardrails
- Do not infer broad scope from an article that does not establish it.
- Do not equate sentiment with impact. A strongly positive product announcement can be low impact; a neutral-sounding debt filing can be high impact.
- Unknown/missing evidence must be marked unknown upstream; do not silently substitute a high score. The baseline function requires numeric inputs and should not be called with fabricated defaults.
- Keep impact score separate from model confidence.
- Record component scores, weights, methodology version, source record ID, and evidence used.
- Test across event types, positive/negative/neutral wording, duplicate stories, missing entity metadata, and different company sizes. Expected score bands are reviewer-designed test expectations, not ground truth.
