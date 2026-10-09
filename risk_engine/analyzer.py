"""Transparent, deterministic baseline analyzer for demo/replay mode.

This is a rule-based baseline, not a trained financial NLP model. Confidence values
are heuristic indicators of rule evidence, not calibrated probabilities.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any

from .schema import NormalizedRecord, RiskSignal
from .scoring import score_impact, sentiment_label

POSITIVE = {
    "profit growth": 0.75, "record profit": 0.9, "beats estimates": 0.7,
    "strong demand": 0.6, "raises guidance": 0.7, "approval": 0.45,
    "successful launch": 0.65, "debt repaid": 0.7, "recovery": 0.4,
    "acquisition completed": 0.4,
}
NEGATIVE = {
    "bankruptcy": -0.95, "default": -0.9, "fraud": -0.85,
    "investigation": -0.55, "data breach": -0.8, "outage": -0.65,
    "recall": -0.6, "cuts guidance": -0.7, "loss": -0.45,
    "layoffs": -0.4, "sanctions": -0.6, "downgrade": -0.55,
    "misses estimates": -0.7, "lawsuit": -0.5, "disruption": -0.5,
}
EVENT_RULES = {
    "CREDIT_EVENT": ["bankruptcy", "default", "debt", "credit rating", "downgrade", "liquidity"],
    "REGULATORY": ["regulator", "regulatory", "investigation", "fine", "sanction", "compliance"],
    "GEOPOLITICAL": ["war", "geopolitical", "sanctions", "conflict", "tariff", "trade restriction"],
    "MACROECONOMIC": ["inflation", "interest rate", "central bank", "gdp", "recession", "unemployment"],
    "MERGER_ACQUISITION": ["merger", "acquisition", "acquires", "acquired", "takeover"],
    "EARNINGS": ["earnings", "profit", "revenue", "quarterly results", "guidance", "estimates"],
    "MANAGEMENT": ["ceo resigns", "appoints ceo", "executive", "management change", "steps down"],
    "LEGAL": ["lawsuit", "court", "legal action", "settlement", "charged with"],
    "OPERATIONAL": ["outage", "data breach", "production halted", "supply disruption", "recall", "cyberattack"],
    "PRODUCT": ["product launch", "launches product", "new product", "product recall"],
    "MARKET": ["shares rise", "shares fall", "stock drops", "market volatility", "trading halt"],
}


def _matches(text: str, phrases: dict[str, float]) -> list[tuple[str, float]]:
    low = text.lower()
    return [(phrase, value) for phrase, value in phrases.items() if phrase in low]


def _entity_mentions(text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    company = metadata.get("company")
    ticker = metadata.get("ticker")
    if isinstance(company, str) and company.strip():
        entities.append({"name": company.strip(), "type": "ORG", "ticker": ticker})
    elif isinstance(ticker, str) and ticker.strip():
        entities.append({"name": ticker.strip(), "type": "TICKER", "ticker": ticker.strip()})
    # Conservative surface-form extraction for company-like names; explicitly heuristic.
    for match in re.finditer(r"\b[A-Z][A-Za-z&.-]*(?:\s+[A-Z][A-Za-z&.-]*){0,2}\b", text):
        name = match.group(0).strip()
        if name.lower() not in {"the", "a", "an", "on", "in", "after", "following", "company", "shares"} and not any(e["name"] == name for e in entities):
            entities.append({"name": name, "type": "ORG_CANDIDATE", "ticker": None})
        if len(entities) >= 5:
            break
    return entities


def analyze_record(record: NormalizedRecord) -> RiskSignal:
    """Convert one normalized text record into a validated structured risk signal."""
    record.validate()
    text = record.text
    pos = _matches(text, POSITIVE)
    neg = _matches(text, NEGATIVE)
    # Average matched phrase values; unmatched text is neutral, with low evidence confidence.
    values = [v for _, v in pos + neg]
    sentiment = max(-1.0, min(1.0, sum(values) / len(values))) if values else 0.0
    sentiment = round(sentiment, 3)
    sentiment_conf = min(0.90, 0.45 + 0.12 * len(values)) if values else 0.25
    label = sentiment_label(sentiment)

    low = text.lower()
    event_matches = [(event, phrase) for event, phrases in EVENT_RULES.items() for phrase in phrases if phrase in low]
    if event_matches:
        # Choose the event category with most matched phrases; stable insertion order breaks ties.
        counts: dict[str, int] = {}
        for event, _ in event_matches:
            counts[event] = counts.get(event, 0) + 1
        event_type = max(counts, key=counts.get)
        event_conf = min(0.90, 0.5 + 0.1 * counts[event_type])
    else:
        event_type, event_conf = "OTHER", 0.25

    severity_map = {
        "CREDIT_EVENT": 0.95, "GEOPOLITICAL": 0.80, "REGULATORY": 0.75,
        "MACROECONOMIC": 0.65, "MERGER_ACQUISITION": 0.65, "EARNINGS": 0.55,
        "MANAGEMENT": 0.35, "LEGAL": 0.60, "OPERATIONAL": 0.70,
        "PRODUCT": 0.35, "MARKET": 0.55, "OTHER": 0.25,
    }
    severity = severity_map[event_type]
    consequence = min(1.0, 0.25 + 0.15 * len(neg) + (0.15 if event_type in {"CREDIT_EVENT", "REGULATORY", "OPERATIONAL", "GEOPOLITICAL"} else 0))
    scope = 0.75 if any(w in low for w in ["industry-wide", "systemic", "global", "across all markets"]) else 0.55 if any(w in low for w in ["company-wide", "nationwide", "multiple regions"]) else 0.35
    metadata = record.metadata if isinstance(record.metadata, dict) else {}
    entity_relevance = 1.0 if metadata.get("company") or metadata.get("ticker") else 0.4
    impact_result = score_impact(event_severity=severity, business_consequence=consequence,
                                 scope=scope, entity_relevance=entity_relevance,
                                 sentiment_score=sentiment,
                                 evidence={"event_severity": event_type, "business_consequence": "keyword-based heuristic",
                                           "scope": "text keyword heuristic", "entity_relevance": "source metadata presence"})
    stable = f"{record.source}:{record.source_id or record.record_id}"
    signal_id = "sig_" + hashlib.sha256(stable.encode()).hexdigest()[:12]
    matched_phrases = [p for p, _ in pos + neg]
    evidence_text = text[:280]
    signal = RiskSignal(
        signal_id=signal_id, record_id=record.record_id,
        timestamp=record.published_at,
        source={"type": record.source, "source_id": record.source_id, "url": record.source_url},
        entities=_entity_mentions(text, metadata),
        sentiment={"score": sentiment, "label": label, "confidence": round(sentiment_conf, 2), "method": "phrase_lexicon_baseline"},
        event={"type": event_type, "confidence": round(event_conf, 2), "method": "keyword_taxonomy_baseline"},
        impact={"score": impact_result.score, "confidence": 0.35, "normalized_risk": impact_result.normalized_risk,
                "components": impact_result.components, "weights": impact_result.weights,
                "method": "expert_weighted_heuristic_baseline"},
        evidence={"text_span": evidence_text, "matched_sentiment_phrases": matched_phrases,
                  "summary": f"Rule-based baseline detected {event_type.lower().replace('_', ' ')}; impact estimate is provisional.",
                  "limitations": "Not a trained or calibrated model; verify entity extraction, event class and impact manually."},
    )
    return signal.validate()
