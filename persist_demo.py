"""Run synthetic replay, persist source records/signals to SQLite, and print a summary."""
import argparse
import json
from risk_engine.pipeline import analyze_items, read_records
from risk_engine.storage import RiskEngineStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist Risk Engine outputs in SQLite")
    parser.add_argument("--input", default="data/synthetic/sample_records.json")
    parser.add_argument("--db", default="data/runtime/risk_engine.db")
    args = parser.parse_args()
    records = read_records(args.input)
    signals = analyze_items(records)
    store = RiskEngineStore(args.db)
    summary = store.save_batch(records, signals)
    print("SQLite database:", args.db)
    print("Persistence summary:", json.dumps(summary, indent=2))
    print("Impact summary:", json.dumps(store.impact_summary(), indent=2))


if __name__ == "__main__":
    main()
