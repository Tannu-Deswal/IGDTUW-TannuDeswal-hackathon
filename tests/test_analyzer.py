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
        
    
    def test_negated_investigation_does_not_add_negative_sentiment(self):
        record = NormalizedRecord(
            "r_neg_sentiment",
            "synthetic_news",
            "2026-10-09T10:00:00Z",
            "Acme Corporation reported record profits, with no regulatory investigation."
        )
        signal = analyze_record(record)

        self.assertEqual(signal.sentiment["label"], "positive")
        self.assertAlmostEqual(signal.sentiment["score"], 0.9)
        self.assertEqual(
            signal.evidence["matched_sentiment_phrases"],
            ["record profit"],
        )

    def test_real_losses_remain_negative_after_negated_investigation(self):
        record = NormalizedRecord(
            "r_mixed_negation",
            "synthetic_news",
            "2026-10-09T10:00:00Z",
            "No investigation was found, but the company suffered major losses."
        )
        signal = analyze_record(record)

        self.assertEqual(signal.sentiment["label"], "negative")
        self.assertIn("loss", signal.evidence["matched_sentiment_phrases"])


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
        
    
    def test_negated_regulatory_event(self):
        record = NormalizedRecord(
            "r_negated", "synthetic_news", "2026-10-09T10:00:00Z",
            "Acme Corporation reported record profits and strong revenue growth, "
            "with no regulatory investigation or threat to its operations."
        )
        signal = analyze_record(record)

        # A negated investigation should not be treated as an active regulatory threat.
        self.assertEqual(signal.event["type"], "REGULATORY")
        self.assertEqual(signal.event["status"], "NEGATED")

    def test_affirmed_regulatory_event(self):
        record = NormalizedRecord(
            "r_affirmed", "synthetic_news", "2026-10-09T10:00:00Z",
            "Acme Corporation faces a regulatory investigation that threatens operations."
        )
        signal = analyze_record(record)
        self.assertEqual(signal.event["status"], "AFFIRMED")

        self.assertEqual(signal.event["type"], "REGULATORY")
        self.assertGreaterEqual(signal.impact["score"], 6)

    def test_uncertain_regulatory_event(self):
        record = NormalizedRecord(
            "r_uncertain", "synthetic_news", "2026-10-09T10:00:00Z",
            "Acme Corporation may face a regulatory investigation."
        )
        signal = analyze_record(record)
        self.assertEqual(signal.event["status"], "UNCERTAIN")

        self.assertEqual(signal.event["type"], "REGULATORY")
        # Uncertainty should be handled explicitly in the implementation.
        self.assertLess(signal.event["confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
