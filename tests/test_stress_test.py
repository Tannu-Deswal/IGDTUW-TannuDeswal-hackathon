import unittest
from downstream.stress_test import run_stress_test

class TestStressTest(unittest.TestCase):
    def test_credit_event_creates_a_scenario_and_preserves_traceability(self):
        result = run_stress_test([{"signal_id":"sig_demo", "event":{"type":"CREDIT_EVENT"}, "impact":{"score":9}}])
        self.assertEqual(len(result["scenarios"]), 1)
        scenario = result["scenarios"][0]
        self.assertEqual(scenario["signal_id"], "sig_demo")
        self.assertLess(scenario["portfolio_after"], scenario["portfolio_before"])

    def test_impact_range_validated(self):
        with self.assertRaises(ValueError):
            run_stress_test([{"event":{"type":"OTHER"}, "impact":{"score":11}}])

if __name__ == "__main__":
    unittest.main()
