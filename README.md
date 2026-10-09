# AI/NLP Risk Engine

An explainable prototype that normalizes financial text from multiple source types and emits structured risk signals for downstream analysis. The repository currently includes a deterministic, rule-based baseline and synthetic replay fixtures so the end-to-end path can be tested without API credentials.

> **Prototype limitation:** sentiment and event classification are phrase/keyword heuristics, not a trained financial NLP model. Impact is an expert-weighted heuristic, not a learned or empirically validated prediction. Confidence fields are heuristic indicators, not calibrated probabilities. Do not use for trading or investment decisions.

## Problem and approach

Unstructured financial text is difficult to compare across channels. This prototype standardizes records, retains source traceability, derives a sentiment score, assigns an event taxonomy, estimates impact using documented components, validates the output contract, and emits JSON for a downstream module.

## Architecture

```mermaid
flowchart TD
  A[News-like source] --> C[Source adapters / normalized records]
  B[Social-like source] --> C
  C --> D[Timestamp and schema validation]
  D --> E[Deduplication]
  E --> F[Sentiment baseline]
  E --> G[Event taxonomy baseline]
  F --> H[Impact scoring]
  G --> H
  H --> I[Validated RiskSignal JSON]
  I --> J[Downstream risk dashboard / scenario module]
```

## Repository layout

- `risk_engine/schema.py`: validated normalized-input and risk-output contracts.
- `risk_engine/analyzer.py`: deterministic sentiment/event baseline and risk-signal assembly.
- `risk_engine/scoring.py`: documented weighted impact formula.
- `risk_engine/pipeline.py`: JSON/JSONL loading, normalization and deduplication.
- `risk_engine/storage.py`: SQLite persistence for normalized records and risk signals, with indexed summary queries.
- `persist_demo.py`: replay the synthetic records and persist records/signals to the local database.
- `data/synthetic/`: invented example records from two simulated source types.
- `data/sample/`: generated JSON outputs.
- `docs/impact_methodology.md`: weights, interpretation and evaluation requirements.
- `docs/data_sources.md`: source candidates and data visibility rules.
- `downstream/stress_test.py`: synthetic portfolio stress scenarios driven by risk signals.
- `run_demo.py`: end-to-end synthetic replay and downstream stress-test run.
- `source_adapters/gdelt.py`: live GDELT DOC API headline adapter.
- `source_adapters/csv_text.py`: adapter for a local financial/social-text CSV.
- `fetch_gdelt.py` / `analyze_csv.py`: source ingestion entry points.
- `tests/`: contract, scoring, classification, deduplication and stress-module tests.

## Quickstart

Requires Python 3.10+; the core engine uses only the Python standard library.

```bash
python -m unittest discover -s tests -v
python run_engine.py
python run_demo.py
# Persist records/signals to SQLite and print an impact summary:
python persist_demo.py
# Optional: choose a different SQLite path
python persist_demo.py --db data/runtime/my_risk_engine.db
# Optional live news ingestion (requires internet access):
python fetch_gdelt.py --max-records 15 --timespan 1day
# Optional local social/financial CSV (supply the actual column names):
python analyze_csv.py path/to/your_dataset.csv --text-column text --timestamp-column created_at --id-column id --ticker-column ticker
```

To use another input file:

```bash
python run_engine.py --input path/to/records.json --output data/sample/my_signals.json
```

Input must be a JSON array or JSONL file. Each record requires `record_id`, `source`, `published_at` (ISO-8601), and `text`. Optional fields: `source_id`, `source_url`, `metadata`.

## Output contract

Each signal includes a stable signal ID, input record ID, timestamp, source traceability, heuristic entities, sentiment (`score` in [-1,1]), controlled event type, impact (`score` 1–10), component breakdown, weights, and evidence/limitations.

## Database

The prototype uses SQLite through Python’s standard library, so no database server or credentials are needed for the local demo. The default database is created at `data/runtime/risk_engine.db` (ignored by Git). It stores normalized source records and their generated risk signals, with foreign-key traceability and indexes for source, event type, impact and timestamp. Run `python persist_demo.py` to initialize and populate it. This local SQLite connection is the first persistence layer; a hosted PostgreSQL/Supabase connection can be added later if remote multi-user access is required.

## Dataset and licensing

Bundled demo records are synthetic and clearly labelled. A GDELT DOC API headline adapter and configurable local CSV adapter are included. The default replay still uses synthetic records so tests and the demo remain deterministic. See [`docs/data_sources.md`](docs/data_sources.md) before downloading or committing external data. Online availability does not imply redistribution permission. Never commit API keys; `.env.example` contains placeholders only.

## Evaluation and results

The current automated tests check expected behavior on controlled fixtures and invalid inputs; they do not establish real-world model accuracy. Do not present synthetic-fixture test success as model performance. Before making quality claims, evaluate on a separate human-labelled dataset and report sample size, label definitions and suitable metrics.

## Downstream stress-test demonstration

`run_demo.py` passes the generated risk signals to a synthetic portfolio stress module and writes `data/sample/stress_test_results.json`. Event-to-sector shocks are explicitly illustrative assumptions, not empirical estimates. The GDELT adapter fetches headlines (not full article bodies) and the CSV adapter requires the user to supply a permitted local dataset. The portfolio model remains illustrative, not calibrated.

## Candidate details and demo

- Candidate: Tannu Deswal
- Hackathon: S&P Global & Crisil Campus Hackathon 2026
- Demo video: add the public/unlisted link after recording.
