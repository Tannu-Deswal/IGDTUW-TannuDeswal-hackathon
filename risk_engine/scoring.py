"""Transparent rule-assisted impact scoring; weights are expert-designed, not learned."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping

WEIGHTS = {
    "event_severity": 0.35,
    "business_consequence": 0.25,
    "scope": 0.20,
    "entity_relevance": 0.10,
    "sentiment_magnitude": 0.10,
}

@dataclass(frozen=True)
class ImpactResult:
    score: int
    normalized_risk: float
    components: dict[str, float]
    weights: dict[str, float]
    explanation: str
    methodology: str = "expert-weighted transparent baseline; not trained on impact labels"

    def to_dict(self) -> dict:
        return asdict(self)


def score_impact(*, event_severity: float, business_consequence: float,
                 scope: float, entity_relevance: float, sentiment_score: float,
                 evidence: Mapping[str, str] | None = None) -> ImpactResult:
    """Score an event from five explicit inputs, each normalized to [0, 1].

    sentiment_score must be in [-1, 1]. Unknown values should not be guessed:
    upstream callers should flag missing evidence and avoid presenting the result
    as high-confidence. This function intentionally requires all five inputs.
    """
    components = {
        "event_severity": event_severity,
        "business_consequence": business_consequence,
        "scope": scope,
        "entity_relevance": entity_relevance,
        "sentiment_magnitude": abs(sentiment_score),
    }
    for name, value in components.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be numeric and between 0 and 1")
    if isinstance(sentiment_score, bool) or not isinstance(sentiment_score, (int, float)) or not -1 <= sentiment_score <= 1:
        raise ValueError("sentiment_score must be numeric and between -1 and 1")
    total_weight = sum(WEIGHTS.values())
    if abs(total_weight - 1.0) > 1e-9:
        raise RuntimeError("Impact weights must sum to 1.0")
    risk = sum(components[name] * WEIGHTS[name] for name in WEIGHTS)
    impact = max(1, min(10, round(1 + 9 * risk)))
    if evidence:
        missing = [name for name in ("event_severity", "business_consequence", "scope", "entity_relevance") if not evidence.get(name)]
        explanation = ("Weighted impact estimate. Evidence recorded for supplied components." if not missing
                       else "Weighted impact estimate; evidence missing for: " + ", ".join(missing) + ". Treat as provisional.")
    else:
        explanation = "Weighted impact estimate; component evidence was not supplied, so treat as provisional."
    return ImpactResult(
        score=impact,
        normalized_risk=round(risk, 4),
        components={k: round(float(v), 4) for k, v in components.items()},
        weights=dict(WEIGHTS),
        explanation=explanation,
    )


def sentiment_label(score: float, neutral_band: float = 0.10) -> str:
    """Map a normalized sentiment score to a label using an explicit neutral band."""
    if not -1 <= score <= 1:
        raise ValueError("score must be between -1 and 1")
    if not 0 <= neutral_band < 1:
        raise ValueError("neutral_band must be in [0, 1)")
    if score > neutral_band:
        return "positive"
    if score < -neutral_band:
        return "negative"
    return "neutral"
