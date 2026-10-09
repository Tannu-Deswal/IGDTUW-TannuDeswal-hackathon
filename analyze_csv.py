"""Map a downloaded financial/social-text CSV into Risk Engine signals."""
import argparse
from risk_engine.pipeline import analyze_items, write_json
from source_adapters.csv_text import load_text_csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a local CSV of financial text")
    parser.add_argument("csv_path")
    parser.add_argument("--text-column", required=True)
    parser.add_argument("--timestamp-column")
    parser.add_argument("--id-column")
    parser.add_argument("--entity-column")
    parser.add_argument("--ticker-column")
    parser.add_argument("--source-name", default="financial_text_csv")
    parser.add_argument("--output", default="data/runtime/csv_risk_signals.json")
    args = parser.parse_args()
    records = load_text_csv(args.csv_path, text_column=args.text_column,
        timestamp_column=args.timestamp_column, id_column=args.id_column,
        entity_column=args.entity_column, ticker_column=args.ticker_column,
        source_name=args.source_name)
    signals = analyze_items(records)
    write_json(args.output, signals)
    print(f"Loaded {len(records)} CSV record(s); produced {len(signals)} signal(s) at {args.output}")
