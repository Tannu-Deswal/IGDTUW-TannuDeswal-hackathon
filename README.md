# AI/NLP Risk Engine — core baseline

A small, auditable starting point for normalizing financial text and producing structured risk signals. This starter implements data contracts, range validation, sentiment-label mapping, and a transparent rule-assisted impact formula. It does **not** yet implement source ingestion, a production NLP model, event classification, an API, or a downstream portfolio module.

## Run tests

Requires Python 3.10+; no third-party packages needed.

```bash
python -m unittest discover -s tests -v
```

## Core contracts

- `NormalizedRecord`: source traceability, timestamp, text, optional source metadata.
- `RiskSignal`: sentiment in `[-1, 1]`, confidence in `[0, 1]`, controlled event type, impact integer `1..10`, and evidence.
- `score_impact(...)`: expert-weighted baseline documented in `docs/impact_methodology.md`.

## Important limitations

- Impact weights are hand-designed, not learned or empirically validated.
- Model confidence must come from a defined model/calibration method; do not invent it.
- Publicly accessible data is not automatically redistributable. Add only data allowed by its licence/terms; put clearly labelled synthetic fixtures in `data/synthetic/`.
- Never commit API keys. Use `.env.example` for variable names only.
