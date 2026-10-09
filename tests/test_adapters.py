import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from source_adapters.csv_text import load_text_csv
from source_adapters.gdelt import _parse_gdelt_date, fetch_gdelt

class FakeResponse:
    headers = {"Content-Type": "application/json"}
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.payload).encode()

class TestAdapters(unittest.TestCase):
    def test_parse_gdelt_timestamp(self):
        self.assertEqual(_parse_gdelt_date("20261009T101500Z"), "2026-10-09T10:15:00+00:00")

    def test_gdelt_response_normalization(self):
        payload = {"articles": [{"title":"Bank reports default", "url":"https://example.com/a", "seendate":"20261009T101500Z", "domain":"example.com", "language":"English", "sourcecountry":"US"}]}
        with patch("source_adapters.gdelt.urlopen", return_value=FakeResponse(payload)):
            rows = fetch_gdelt(max_records=1)
        self.assertEqual(rows[0]["source"], "gdelt_doc_api")
        self.assertEqual(rows[0]["text"], "Bank reports default")
        self.assertEqual(rows[0]["metadata"]["text_field"], "headline_only")

    def test_csv_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tweets.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "created_at", "body", "ticker"])
                writer.writeheader(); writer.writerow({"id":"42", "created_at":"2026-10-09T10:00:00Z", "body":"Shares fall after fraud investigation", "ticker":"XYZ"})
            rows = load_text_csv(path, text_column="body", timestamp_column="created_at", id_column="id", ticker_column="ticker")
            self.assertEqual(rows[0]["source_id"], "42")
            self.assertEqual(rows[0]["metadata"]["ticker"], "XYZ")

if __name__ == "__main__": unittest.main()
