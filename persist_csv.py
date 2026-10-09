
"""Analyze a CSV dataset and persist normalized records and risk signals."""
import argparse
import json

from risk_engine.pipeline import analyze_items
from risk_engine.storage import RiskEngineStore
from source_adapters.csv_text import load_text_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze financial-text CSV and persist results to SQLite"
    )
    parser.add_argument("csv_path")
    parser.add_argument("--text-column", required=True)
    parser.add_argument("--timestamp-column", required=True)
    parser.add_argument("--id-column")
    parser.add_argument("--entity-column")
    parser.add_argument("--ticker-column")
    parser.add_argument("--source-url-column")
    parser.add_argument("--source-name", default="financial_tweets")
    parser.add_argument("--db", default="data/runtime/risk_engine.db")
    parser.add_argument(
        "--signals-json",
        default="data/runtime/financial_tweets_signals.json",
    )
    args = parser.parse_args()

    records = load_text_csv(
        args.csv_path,
        text_column=args.text_column,
        timestamp_column=args.timestamp_column,
        id_column=args.id_column,
        entity_column=args.entity_column,
        ticker_column=args.ticker_column,
        source_url_column=args.source_url_column,
        source_name=args.source_name,
    )

    
    # Keep the first occurrence of each source ID, matching analyze_items().
    unique_records = []
    seen = set()

    for record in records:
        key = (record["source"], record.get("source_id") or record["record_id"])
        if key in seen:
            continue
        seen.add(key)
        unique_records.append(record)

    signals = analyze_items(unique_records)

    store = RiskEngineStore(args.db)
    summary = store.save_batch(unique_records, signals)

    with open(args.signals_json, "w", encoding="utf-8") as handle:
        json.dump(signals, handle, ensure_ascii=False, indent=2)

    print("SQLite database:", args.db)
    print("Persistence summary:", json.dumps(summary, indent=2))
    print("Impact summary:", json.dumps(store.impact_summary(), indent=2))
    print("Signals JSON:", args.signals_json)


if __name__ == "__main__":
    main()