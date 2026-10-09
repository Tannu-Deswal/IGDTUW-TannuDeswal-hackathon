# Impact score methodology — baseline v1

This is a transparent, expert-designed heuristic, not a model trained on observed impact labels. Scores must be treated as provisional until evaluated by domain reviewers against labelled examples.

| Component | Weight | Meaning |
|---|---:|---|
| Event severity | 0.35 | Severity associated with the detected event category |
| Business consequence | 0.25 | Textual evidence of financial/operational consequences |
| Scope | 0.20 | Evidence about reach (local, business unit, company, industry/systemic) |
| Entity relevance | 0.10 | Directness of link to a company/ticker or relevant sector |
| Sentiment magnitude | 0.10 | Absolute sentiment score; polarity is separately retained |

Each component is normalized to [0,1].

`R = .35E + .25C + .20S + .10N + .10|sentiment|`

`Impact = clip(round(1 + 9R), 1, 10)`

Weights sum to 1. Sentiment magnitude is capped at 10% so strong wording alone cannot dominate severity and consequence. Current demo mappings for severity, consequence and scope are keyword/rule heuristics; they are not verified facts about actual financial outcomes. Missing/weak evidence should lower confidence and trigger review, not be filled in with invented values.

## Confidence warning

The bundled analyzer's confidence fields are heuristic evidence indicators, not calibrated probabilities. They must not be described as statistically calibrated confidence. Impact score and confidence are different quantities.

## Minimum evaluation before claiming performance

1. Create a human-labelled test set covering positive, negative, neutral, ambiguous, multi-event, and no-event text.
2. Report sentiment macro-F1/accuracy and event-class macro-F1 with the label set and sample size.
3. Evaluate impact separately against human-rated bands; report agreement and limitations.
4. Test duplicate records, missing source metadata, malformed timestamps, unseen entities, negation, sarcasm and mixed sentiment.
5. Do not report performance metrics from the synthetic demo fixtures as evidence of real-world model quality.
