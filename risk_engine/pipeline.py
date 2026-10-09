"""Batch processing helpers for JSON/JSONL normalized records."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterable
from .schema import NormalizedRecord
from .analyzer import analyze_record


def record_from_dict(item: dict[str, Any]) -> NormalizedRecord:
    return NormalizedRecord(
        record_id=item["record_id"], source=item["source"],
        published_at=item["published_at"], text=item["text"],
        source_id=item.get("source_id"), source_url=item.get("source_url"),
        metadata=item.get("metadata", {}),
    )


def analyze_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        record = record_from_dict(item).validate()
        dedupe_key = (record.source, record.source_id or record.record_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        output.append(analyze_record(record).to_dict())
    return output


def read_records(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of records; JSONL is also supported")
    return payload


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
