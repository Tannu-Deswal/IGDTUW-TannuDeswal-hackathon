"""Run the Risk Engine against a JSON or JSONL file."""
import argparse
import json
from risk_engine.pipeline import analyze_items, read_records, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze normalized financial text records")
    parser.add_argument("--input", default="data/synthetic/sample_records.json", help="JSON array or JSONL input path")
    parser.add_argument("--output", default="data/sample/risk_signals.json", help="Output JSON path")
    args = parser.parse_args()
    records = read_records(args.input)
    signals = analyze_items(records)
    write_json(args.output, signals)
    print(f"Processed {len(records)} input record(s); wrote {len(signals)} unique risk signal(s) to {args.output}")
    print(json.dumps(signals[:2], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
