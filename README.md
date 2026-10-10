# AI/NLP Risk Engine

### S&P Global & Crisil Campus Hackathon 2026

An end-to-end financial risk analysis prototype that converts unstructured text into explainable, structured risk signals and connects them to portfolio stress testing.

> **Prototype limitations:** Sentiment and event classification use deterministic phrase and keyword heuristics, not a trained financial NLP model. Impact scores use a weighted heuristic and are not empirically calibrated predictions. Confidence fields are heuristic indicators, not calibrated probabilities. Portfolio shocks are illustrative assumptions. This prototype is not intended for trading or investment decisions.

## Problem and approach

Unstructured financial text is difficult to compare across channels. This prototype standardizes records, retains source traceability, derives a sentiment score, assigns an event taxonomy, estimates impact using documented components, validates the output contract, and emits JSON for a downstream module.

## Architecture

```mermaid
flowchart TD
    A["Financial Text Sources"] --> B["Normalization and Validation"]
    B --> C["Deduplication"]
    C --> D["Sentiment Analysis"]
    C --> E["Event Classification"]
    D --> F["Impact Scoring"]
    E --> F
    F --> G["Validated RiskSignal JSON"]
    G --> H["Portfolio Stress Testing"]
```

## Repository layout

* `risk_engine/schema.py`: validated normalized-input and risk-output contracts.
* `risk_engine/analyzer.py`: deterministic sentiment/event baseline and risk-signal assembly.
* `risk_engine/scoring.py`: documented weighted impact formula.
* `risk_engine/pipeline.py`: JSON/JSONL loading, normalization and deduplication.
* `risk_engine/storage.py`: SQLite persistence for normalized records and risk signals, with indexed summary queries.
* `persist_demo.py`: replay the synthetic records and persist records/signals to the local database.
* `data/synthetic/`: invented example records from two simulated source types.
* `data/sample/`: generated JSON outputs.
* `docs/impact_methodology.md`: weights, interpretation and evaluation requirements.
* `docs/data_sources.md`: source candidates and data visibility rules.
* `downstream/stress_test.py`: synthetic portfolio stress scenarios driven by risk signals.
* `run_demo.py`: end-to-end synthetic replay and downstream stress-test run.
* `source_adapters/gdelt.py`: live GDELT DOC API headline adapter.
* `source_adapters/csv_text.py`: adapter for a local financial/social-text CSV.
* `fetch_gdelt.py` / `analyze_csv.py`: source ingestion entry points.
* `tests/`: contract, scoring, classification, deduplication and stress-module tests.

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

# Optional local CSV input (replace the example path and column names):
python analyze_csv.py path/to/your_dataset.csv --text-column text --timestamp-column created_at --id-column id --ticker-column ticker
```

To use another input file:

```bash
python run_engine.py --input path/to/records.json --output data/sample/my_signals.json
```

Input must be a JSON array or JSONL file. Each record requires `record_id`, `source`, `published_at` (ISO-8601), and `text`. Optional fields: `source_id`, `source_url`, and `metadata`.

### Interactive dashboard

Install the dashboard dependencies and launch the Streamlit interface:

```bash

python -m pip install -r requirements.txt

python -m streamlit run app.py

```



The dashboard supports interactive headline analysis, RiskSignal JSON export, synthetic portfolio stress testing, and inspection of bundled sample signals.



The current analyzer uses deterministic keyword and phrase rules. Impact scores and portfolio shocks are illustrative heuristics, not calibrated financial predictions.

## Key Results

- **End-to-end pipeline:** Processes synthetic financial-text records into structured risk signals and passes them to the downstream stress-testing module.
- **Structured outputs:** Includes sentiment, event classification, impact scoring, evidence, and source traceability in the risk-signal contract.
- **Persistence:** Stores normalized records and generated signals in SQLite for local inspection and querying.
- **Automated tests:** The project includes tests for validation, scoring, classification, deduplication, and stress-test behavior. See the Evaluation section for the scope of these tests.
- **Interactive demo:** Supports manual text analysis, JSON export, bundled sample-signal inspection, and illustrative portfolio stress testing.


## Output contract

Each signal includes a stable signal ID, input record ID, timestamp, source traceability, heuristic entities, sentiment (`score` in \[-1,1]), controlled event type, impact (`score` 1–10), component breakdown, weights, and evidence/limitations.

## Database

The prototype uses SQLite through Python’s standard library, so no database server or credentials are needed for the local demo. The default database is created at `data/runtime/risk\_engine.db` (ignored by Git). It stores normalized source records and their generated risk signals, with foreign-key traceability and indexes for source, event type, impact and timestamp. Run `python persist\_demo.py` to initialize and populate it. This local SQLite connection is the first persistence layer; a hosted PostgreSQL/Supabase connection can be added later if remote multi-user access is required.

## Dataset and licensing

Bundled demo records are synthetic and clearly labelled. A GDELT DOC API headline adapter and configurable local CSV adapter are included. The default replay still uses synthetic records so tests and the demo remain deterministic. See [`docs/data\_sources.md`](docs/data_sources.md) before downloading or committing external data. Online availability does not imply redistribution permission. Never commit API keys; `.env.example` contains placeholders only.

## Evaluation and results

The automated test suite checks input validation, sentiment bounds, event classification, impact scoring, deduplication, persistence, and downstream stress-test behavior on controlled examples.

Run the tests locally:

```bash
python -m unittest discover -s tests -v
```

Passing tests demonstrate expected software behavior on the tested cases; they do not establish real-world NLP accuracy or financial predictive performance. The current baseline has not been validated against a separate human-labelled financial-text benchmark. Impact weights and portfolio shocks are illustrative assumptions, not empirically calibrated estimates.

## Downstream stress-test demonstration

`run\_demo.py` passes the generated risk signals to a synthetic portfolio stress module and writes `data/sample/stress\_test\_results.json`. Event-to-sector shocks are explicitly illustrative assumptions, not empirical estimates. The GDELT adapter fetches headlines (not full article bodies) and the CSV adapter requires the user to supply a permitted local dataset. The portfolio model remains illustrative, not calibrated.

## Candidate details and demo

* Candidate: Tannu Deswal
* Hackathon: S\&P Global \& Crisil Campus Hackathon 2026
* Demo video: [Watch Demo Video](https://youtu.be/s0adAc4fuoQ)
* Streamlit app: [Open Live Dashboard](https://hackathon-tannu-app.streamlit.app/)
* Presentation: docs/presentation.pdf* Presentation: [View Presentation](docs/presentation.pdf)
* Architecture: docs/architecture.png* Architecture: [View Architecture](docs/architecture.png)
