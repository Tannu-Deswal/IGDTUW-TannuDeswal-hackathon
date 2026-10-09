"""Validated data contracts for the AI/NLP Risk Engine (stdlib-only baseline)."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import math

EVENT_TYPES = {
    "GEOPOLITICAL", "MACROECONOMIC", "CREDIT_EVENT", "MERGER_ACQUISITION",
    "REGULATORY", "EARNINGS", "MANAGEMENT", "LEGAL", "OPERATIONAL",
    "PRODUCT", "MARKET", "OTHER",
}
SENTIMENT_LABELS = {"negative", "neutral", "positive"}


def _is_iso_datetime(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _bounded_number(name: str, value: Any, low: float, high: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")


@dataclass
class NormalizedRecord:
    record_id: str
    source: str
    published_at: str
    text: str
    source_id: str | None = None
    source_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "NormalizedRecord":
        for name in ("record_id", "source", "text"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required and cannot be blank")
        if not _is_iso_datetime(self.published_at):
            raise ValueError("published_at must be an ISO-8601 datetime")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object/dict")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskSignal:
    signal_id: str
    record_id: str
    timestamp: str
    source: dict[str, Any]
    entities: list[dict[str, Any]]
    sentiment: dict[str, Any]
    event: dict[str, Any]
    impact: dict[str, Any]
    evidence: dict[str, Any]
    methodology_version: str = "baseline-1.0"

    def validate(self) -> "RiskSignal":
        for name in ("signal_id", "record_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if not _is_iso_datetime(self.timestamp):
            raise ValueError("timestamp must be an ISO-8601 datetime")
        for key in ("source", "sentiment", "event", "impact", "evidence"):
            if not isinstance(getattr(self, key), dict):
                raise ValueError(f"{key} must be an object/dict")
        if not isinstance(self.entities, list):
            raise ValueError("entities must be a list")
        _bounded_number("sentiment.score", self.sentiment.get("score"), -1, 1)
        _bounded_number("sentiment.confidence", self.sentiment.get("confidence"), 0, 1)
        if self.sentiment.get("label") not in SENTIMENT_LABELS:
            raise ValueError(f"sentiment.label must be one of {sorted(SENTIMENT_LABELS)}")
        if self.event.get("type") not in EVENT_TYPES:
            raise ValueError(f"event.type must be one of {sorted(EVENT_TYPES)}")
        _bounded_number("event.confidence", self.event.get("confidence"), 0, 1)
        impact_score = self.impact.get("score")
        if isinstance(impact_score, bool) or not isinstance(impact_score, int) or not 1 <= impact_score <= 10:
            raise ValueError("impact.score must be an integer from 1 to 10")
        _bounded_number("impact.confidence", self.impact.get("confidence"), 0, 1)
        if not self.source.get("type"):
            raise ValueError("source.type is required for traceability")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
