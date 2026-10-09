import tempfile
import unittest
from pathlib import Path
from risk_engine.pipeline import analyze_items, read_records
from risk_engine.storage import RiskEngineStore

ROOT = Path(__file__).resolve().parents[1]

class TestStorage(unittest.TestCase):
    def test_saves_records_signals_and_summary(self):
        records = read_records(ROOT / "data/synthetic/sample_records.json")
        signals = analyze_items(records)
        with tempfile.TemporaryDirectory() as tmp:
            store = RiskEngineStore(Path(tmp) / "test.db")
            result = store.save_batch(records, signals)
            self.assertEqual(result["records_total"], len(records))
            self.assertEqual(result["signals_total"], len(signals))
            self.assertEqual(len(store.latest_signals(20)), len(signals))
            self.assertTrue(store.impact_summary())

    def test_repeat_batch_is_idempotent(self):
        records = read_records(ROOT / "data/synthetic/sample_records.json")
        signals = analyze_items(records)
        with tempfile.TemporaryDirectory() as tmp:
            store = RiskEngineStore(Path(tmp) / "test.db")
            store.save_batch(records, signals)
            result = store.save_batch(records, signals)
            self.assertEqual(result["records_total"], len(records))
            self.assertEqual(result["signals_total"], len(signals))

if __name__ == "__main__":
    unittest.main()
