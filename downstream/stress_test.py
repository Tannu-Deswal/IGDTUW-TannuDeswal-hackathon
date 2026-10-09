"""Synthetic portfolio stress test driven by RiskSignal outputs.

Illustrative prototype only: shocks are transparent scenario assumptions, not
estimated market sensitivities and not investment advice.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

# Synthetic asset buckets and baseline values, denominated in arbitrary units.
DEFAULT_PORTFOLIO = [
    {"asset": "Government Bonds", "sector": "RATES", "value": 2_000_000.0},
    {"asset": "Banking Equities", "sector": "FINANCIALS", "value": 1_500_000.0},
    {"asset": "Energy Equities", "sector": "ENERGY", "value": 1_000_000.0},
    {"asset": "Consumer Equities", "sector": "CONSUMER", "value": 1_000_000.0},
    {"asset": "Cash", "sector": "CASH", "value": 500_000.0},
]

# Shock rates are explicit scenario assumptions, not empirical estimates.
EVENT_SHOCKS = {
    "CREDIT_EVENT": {"FINANCIALS": -0.12, "CONSUMER": -0.04, "ENERGY": -0.03, "RATES": 0.02, "CASH": 0.0},
    "REGULATORY": {"FINANCIALS": -0.08, "CONSUMER": -0.03, "ENERGY": -0.03, "RATES": 0.0, "CASH": 0.0},
    "GEOPOLITICAL": {"ENERGY": -0.10, "CONSUMER": -0.06, "FINANCIALS": -0.05, "RATES": 0.03, "CASH": 0.0},
    "MACROECONOMIC": {"FINANCIALS": -0.07, "CONSUMER": -0.07, "ENERGY": -0.05, "RATES": -0.04, "CASH": 0.0},
    "OPERATIONAL": {"FINANCIALS": -0.04, "CONSUMER": -0.04, "ENERGY": -0.04, "RATES": 0.0, "CASH": 0.0},
    "LEGAL": {"FINANCIALS": -0.06, "CONSUMER": -0.04, "ENERGY": -0.04, "RATES": 0.0, "CASH": 0.0},
        "EARNINGS": {
        "FINANCIALS": -0.07,
        "CONSUMER": -0.06,
        "ENERGY": -0.06,
        "RATES": -0.02,
        "CASH": 0.0,
    },
    "MERGER_ACQUISITION": {
        "FINANCIALS": -0.06,
        "CONSUMER": -0.04,
        "ENERGY": -0.04,
        "RATES": 0.0,
        "CASH": 0.0,
    },
    "MANAGEMENT": {
        "FINANCIALS": -0.06,
        "CONSUMER": -0.03,
        "ENERGY": -0.03,
        "RATES": 0.0,
        "CASH": 0.0,
    },
    "PRODUCT": {
        "FINANCIALS": -0.02,
        "CONSUMER": -0.06,
        "ENERGY": -0.03,
        "RATES": 0.0,
        "CASH": 0.0,
    },
    "MARKET": {
        "FINANCIALS": -0.08,
        "CONSUMER": -0.06,
        "ENERGY": -0.07,
        "RATES": -0.02,
        "CASH": 0.0,
    },
}


def run_stress_test(signals: list[dict[str, Any]], portfolio: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    holdings = [dict(x) for x in (portfolio or DEFAULT_PORTFOLIO)]
    for h in holdings:
        if not isinstance(h.get("value"), (int, float)) or h["value"] < 0:
            raise ValueError("Each portfolio holding must have a non-negative numeric value")
        if not h.get("sector"):
            raise ValueError("Each portfolio holding must have a sector")
    before = sum(float(h["value"]) for h in holdings)
    scenarios = []
    for signal in signals:
        event = signal.get("event", {}).get("type", "OTHER")
        impact = signal.get("impact", {}).get("score", 1)
        if not isinstance(impact, int) or not 1 <= impact <= 10:
            raise ValueError("Risk signal impact.score must be an integer from 1 to 10")
        base_shocks = EVENT_SHOCKS.get(event)
        mapping_status = "mapped" if base_shocks is not None else "unmapped"
        base_shocks = base_shocks or {}
        # Scale the scenario shock from 0.2x at impact 1 to 1.0x at impact 10.
        multiplier = 0.2 + 0.8 * ((impact - 1) / 9)
        per_holding = []
        after = 0.0
        for holding in holdings:
            shock = base_shocks.get(holding["sector"], 0.0) * multiplier
            post_value = float(holding["value"]) * (1.0 + shock)
            after += post_value
            per_holding.append({**holding, "shock_pct": round(shock * 100, 2), "after_value": round(post_value, 2)})
        scenarios.append({
            "signal_id": signal.get("signal_id"), "event_type": event, "impact_score": impact,
            "scenario_multiplier": round(multiplier, 3), "portfolio_before": round(before, 2),
            "portfolio_after": round(after, 2), "absolute_change": round(after - before, 2),
            "change_pct": round((after / before - 1) * 100, 2) if before else 0.0,
            "holdings": per_holding,
            "assumption": (
                "Illustrative adverse-event sector shocks; not empirically calibrated."
                if mapping_status == "mapped"
                else "No sector-shock mapping defined; zero change means unmodelled, not zero risk."
            ),
            "mapping_status": mapping_status,
            "scenario_type": "illustrative_adverse_scenario",
        })
    return {"portfolio_type": "synthetic_demo_portfolio", "currency": "arbitrary units", "portfolio_before": round(before, 2), "scenarios": scenarios}
