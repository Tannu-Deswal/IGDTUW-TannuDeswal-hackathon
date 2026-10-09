"""End-to-end demo: synthetic multi-source records -> RiskSignals -> stress scenarios."""
import json
from risk_engine.pipeline import analyze_items, read_records, write_json
from downstream.stress_test import run_stress_test

if __name__ == "__main__":
    records = read_records("data/synthetic/sample_records.json")
    signals = analyze_items(records)
    stress = run_stress_test(signals)
    write_json("data/sample/risk_signals.json", signals)
    write_json("data/sample/stress_test_results.json", stress)
    print(f"Risk Engine: {len(records)} synthetic records -> {len(signals)} signals")
    print(f"Stress module: {len(stress['scenarios'])} scenarios; portfolio baseline {stress['portfolio_before']:,.0f} arbitrary units")
    for scenario in stress["scenarios"]:
        print(f"  {scenario['event_type']:<20} impact={scenario['impact_score']}  change={scenario['change_pct']}%")
