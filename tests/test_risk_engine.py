import unittest
from risk_engine import NormalizedRecord, RiskSignal, score_impact, sentiment_label

class TestRiskEngine(unittest.TestCase):
    def test_weights_sum_to_one_and_default_example(self):
        result = score_impact(event_severity=.95, business_consequence=.90, scope=.70,
                              entity_relevance=1.0, sentiment_score=-.85,
                              evidence={"event_severity":"confirmed default", "business_consequence":"debt default", "scope":"company", "entity_relevance":"direct"})
        self.assertEqual(result.score, 9)
        self.assertAlmostEqual(sum(result.weights.values()), 1.0)

    def test_sentiment_labels(self):
        self.assertEqual(sentiment_label(-.6), "negative")
        self.assertEqual(sentiment_label(0), "neutral")
        self.assertEqual(sentiment_label(.5), "positive")

    def test_normalized_record_validation(self):
        NormalizedRecord("r1", "synthetic", "2026-10-09T10:00:00Z", "Example event").validate()

    def test_signal_validation(self):
        signal = RiskSignal(
            signal_id="sig_1", record_id="r1", timestamp="2026-10-09T10:00:00Z",
            source={"type":"synthetic", "source_id":"r1"}, entities=[],
            sentiment={"score":-.5,"label":"negative","confidence":.8},
            event={"type":"CREDIT_EVENT","confidence":.7},
            impact={"score":7,"confidence":.6}, evidence={"text_span":"Example"})
        signal.validate()

    def test_reject_out_of_range_sentiment(self):
        with self.assertRaises(ValueError):
            score_impact(event_severity=.5, business_consequence=.5, scope=.5,
                         entity_relevance=.5, sentiment_score=-1.1)

    def test_reject_invalid_impact_score(self):
        signal = RiskSignal(
            signal_id="sig_1", record_id="r1", timestamp="2026-10-09T10:00:00Z",
            source={"type":"synthetic"}, entities=[],
            sentiment={"score":0,"label":"neutral","confidence":.8},
            event={"type":"OTHER","confidence":.7},
            impact={"score":11,"confidence":.6}, evidence={})
        with self.assertRaises(ValueError):
            signal.validate()

if __name__ == "__main__":
    unittest.main()
