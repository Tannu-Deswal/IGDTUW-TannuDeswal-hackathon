
"""Configurable adapter for a local CSV of financial/social text."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


def parse_timestamp(value: str) -> str:
    """Convert supported source timestamps to ISO-8601, preserving the timezone."""
    value = value.strip()

    # First try ISO-8601 timestamps.
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        # The Financial Tweets dataset uses Twitter-style timestamps.
        parsed = datetime.strptime(
            value, "%a %b %d %H:%M:%S %z %Y"
        )

    # Require a timezone so timestamps aren't silently interpreted as local time.
    if parsed.tzinfo is None:
        raise ValueError("Timestamp has no timezone")

    return parsed.isoformat()


def load_text_csv(
    path: str | Path,
    *,
    text_column: str,
    timestamp_column: str | None = None,
    id_column: str | None = None,
    entity_column: str | None = None,
    ticker_column: str | None = None,
    source_url_column: str | None = None,
    source_name: str = "financial_text_csv",
) -> list[dict[str, Any]]:
    """Map CSV rows to NormalizedRecord-compatible dictionaries."""
    path = Path(path)
    output: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        requested_columns = {
            "text_column": text_column,
            "timestamp_column": timestamp_column,
            "id_column": id_column,
            "entity_column": entity_column,
            "ticker_column": ticker_column,
            "source_url_column": source_url_column,
        }
        for option, column in requested_columns.items():
            if column and column not in reader.fieldnames:
                raise ValueError(
                    f"{option} {column!r} not found; "
                    f"available columns: {reader.fieldnames}"
                )

        for row_num, row in enumerate(reader, start=2):
            text = (row.get(text_column) or "").strip()
            if not text:
                continue

            source_id = (row.get(id_column) or "").strip() if id_column else ""
            if not source_id:
                source_id = sha256(
                    f"{path.name}:{row_num}:{text}".encode("utf-8")
                ).hexdigest()[:20]

            raw_timestamp = (
                (row.get(timestamp_column) or "").strip()
                if timestamp_column else ""
            )
            if not raw_timestamp:
                raise ValueError(
                    f"Missing timestamp at CSV row {row_num}; "
                    "provide a valid timestamp column."
                )

            try:
                timestamp = parse_timestamp(raw_timestamp)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid timestamp at CSV row {row_num}: "
                    f"{raw_timestamp!r}"
                ) from exc

            metadata: dict[str, Any] = {
                "dataset_file": path.name,
                "row_number": row_num,
            }

            if entity_column and row.get(entity_column):
                metadata["company"] = row[entity_column].strip()

            if ticker_column and row.get(ticker_column):
                metadata["ticker"] = row[ticker_column].strip()

            source_url = (
                (row.get(source_url_column) or "").strip()
                if source_url_column else ""
            )

            output.append({
                "record_id": f"csv_{source_id}",
                "source": source_name,
                "source_id": source_id,
                "published_at": timestamp,
                "text": text,
                "source_url": source_url or None,
                "metadata": metadata,
            })

    return output