import unittest
from risk_engine.analyzer import analyze_record
from risk_engine.pipeline import analyze_items
from risk_engine.schema import NormalizedRecord

class TestAnalyzer(unittest.TestCase):
    def test_credit_default_classification_and_traceability(self):
        record = NormalizedRecord("r1", "synthetic_news", "2026-10-09T10:00:00Z",
            "Example Bank confirms debt default and possible bankruptcy.", "source-1", None,
            {"company": "Example Bank", "ticker": "EXBK"})
        signal = analyze_record(record)
        self.assertEqual(signal.event["type"], "CREDIT_EVENT")
        self.assertEqual(signal.sentiment["label"], "negative")
        self.assertEqual(signal.source["source_id"], "source-1")
        self.assertGreaterEqual(signal.impact["score"], 1)
        self.assertLessEqual(signal.impact["score"], 10)

    def test_positive_earnings(self):
        record = NormalizedRecord("r2", "synthetic_social", "2026-10-09T10:00:00Z",
            "Example Retail reports record profit and strong demand.", metadata={"company":"Example Retail"})
        signal = analyze_record(record)
        self.assertEqual(signal.sentiment["label"], "positive")
        self.assertEqual(signal.event["type"], "EARNINGS")

    def test_unknown_text_is_not_fabricated_as_specific_event(self):
        record = NormalizedRecord("r3", "synthetic", "2026-10-09T10:00:00Z", "Commentary remains mixed today.")
        signal = analyze_record(record)
        self.assertEqual(signal.event["type"], "OTHER")
        self.assertEqual(signal.sentiment["label"], "neutral")

    def test_deduplication_by_source_id(self):
        base = {"record_id":"r1", "source":"synthetic", "source_id":"same", "published_at":"2026-10-09T10:00:00Z", "text":"Company reports profit."}
        duplicate = {**base, "record_id":"r2"}
        self.assertEqual(len(analyze_items([base, duplicate])), 1)

if __name__ == "__main__":
    unittest.main()
