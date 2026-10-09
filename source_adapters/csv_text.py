"""Configurable adapter for a local CSV of financial/social text."""
from __future__ import annotations
import csv
from hashlib import sha256
from pathlib import Path
from typing import Any


def load_text_csv(path: str | Path, *, text_column: str, timestamp_column: str | None = None,
                  id_column: str | None = None, entity_column: str | None = None,
                  ticker_column: str | None = None, source_name: str = "financial_text_csv",
                  default_timestamp: str = "2026-01-01T00:00:00Z") -> list[dict[str, Any]]:
    """Read a local CSV and map selected columns to NormalizedRecord-compatible dicts.

    Column names must match the CSV headers exactly. Missing/blank timestamps use
    the explicit default timestamp and are flagged in metadata; prefer source time.
    """
    path = Path(path)
    output = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        if text_column not in reader.fieldnames:
            raise ValueError(f"text_column {text_column!r} not found; available columns: {reader.fieldnames}")
        for row_num, row in enumerate(reader, start=2):
            text = (row.get(text_column) or "").strip()
            if not text:
                continue
            source_id = (row.get(id_column) or "").strip() if id_column else ""
            if not source_id:
                source_id = sha256(f"{path.name}:{row_num}:{text}".encode("utf-8")).hexdigest()[:20]
            timestamp = (row.get(timestamp_column) or "").strip() if timestamp_column else ""
            timestamp_inferred = not bool(timestamp)
            timestamp = timestamp or default_timestamp
            metadata: dict[str, Any] = {"dataset_file": path.name, "row_number": row_num,
                                       "timestamp_inferred": timestamp_inferred}
            if entity_column and row.get(entity_column):
                metadata["company"] = row[entity_column].strip()
            if ticker_column and row.get(ticker_column):
                metadata["ticker"] = row[ticker_column].strip()
            output.append({"record_id": f"csv_{source_id}", "source": source_name,
                           "source_id": source_id, "published_at": timestamp, "text": text,
                           "source_url": None, "metadata": metadata})
    return output
