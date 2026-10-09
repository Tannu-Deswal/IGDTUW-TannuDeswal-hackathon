"""Fetch a small batch of GDELT headlines and process them locally."""
import argparse
from risk_engine.pipeline import analyze_items, write_json
from source_adapters.gdelt import DEFAULT_QUERY, fetch_gdelt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch recent GDELT headlines and generate risk signals")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--max-records", type=int, default=15)
    parser.add_argument("--timespan", default="1day", help="GDELT window, e.g. 6h, 1day, 1week")
    parser.add_argument("--output", default="data/runtime/gdelt_risk_signals.json")
    args = parser.parse_args()
    records = fetch_gdelt(args.query, args.max_records, args.timespan)
    signals = analyze_items(records)
    write_json(args.output, signals)
    print(f"Fetched {len(records)} GDELT headline(s); produced {len(signals)} signal(s) at {args.output}")
    print("Note: headline-only rule-based baseline; review the source article before interpreting impact.")
