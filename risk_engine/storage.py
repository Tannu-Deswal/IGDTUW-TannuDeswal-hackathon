"""SQLite persistence for normalized input records and generated risk signals.

SQLite is used as the zero-configuration local database for the hackathon demo.
The JSON payloads preserve the full versioned contract while indexed columns make
basic querying practical. This is an educational prototype, not a production DB.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS normalized_records (
    record_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT,
    published_at TEXT NOT NULL,
    text TEXT NOT NULL,
    source_url TEXT,
    payload_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(source, source_id)
);
CREATE INDEX IF NOT EXISTS idx_records_published_at ON normalized_records(published_at);
CREATE INDEX IF NOT EXISTS idx_records_source ON normalized_records(source);
CREATE TABLE IF NOT EXISTS risk_signals (
    signal_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL UNIQUE REFERENCES normalized_records(record_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    sentiment_score REAL NOT NULL CHECK(sentiment_score >= -1 AND sentiment_score <= 1),
    impact_score INTEGER NOT NULL CHECK(impact_score BETWEEN 1 AND 10),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_signals_event_type ON risk_signals(event_type);
CREATE INDEX IF NOT EXISTS idx_signals_impact ON risk_signals(impact_score);
"""


class RiskEngineStore:
    """Small repository layer. Use a context-managed connection per operation."""
    def __init__(self, db_path: str | Path = "data/runtime/risk_engine.db") -> None:
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self):
        """Yield a transaction-managed connection and always close it.

        sqlite3.Connection's context manager commits/rolls back transactions,
        but does not close the connection. Explicitly closing it is important
        on Windows, where open handles can prevent temporary DB files being
        deleted by tests or tooling.
        """
        conn = self.connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    def save_batch(self, records: Iterable[dict[str, Any]], signals: Iterable[dict[str, Any]]) -> dict[str, int]:
        """Persist records and matching signals idempotently; invalid FK relationships fail."""
        record_rows = list(records)
        signal_rows = list(signals)
        self.initialize()
        with self.connection() as conn:
            for row in record_rows:
                conn.execute(
                    """INSERT INTO normalized_records
                    (record_id, source, source_id, published_at, text, source_url, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(record_id) DO UPDATE SET
                      source=excluded.source, source_id=excluded.source_id,
                      published_at=excluded.published_at, text=excluded.text,
                      source_url=excluded.source_url, payload_json=excluded.payload_json""",
                    (row["record_id"], row["source"], row.get("source_id"), row["published_at"],
                     row["text"], row.get("source_url"), json.dumps(row, ensure_ascii=False)),
                )
            for row in signal_rows:
                conn.execute(
                    """INSERT INTO risk_signals
                    (signal_id, record_id, timestamp, event_type, sentiment_score, impact_score, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(signal_id) DO UPDATE SET
                      record_id=excluded.record_id, timestamp=excluded.timestamp,
                      event_type=excluded.event_type, sentiment_score=excluded.sentiment_score,
                      impact_score=excluded.impact_score, payload_json=excluded.payload_json""",
                    (row["signal_id"], row["record_id"], row["timestamp"], row["event"]["type"],
                     row["sentiment"]["score"], row["impact"]["score"], json.dumps(row, ensure_ascii=False)),
                )
        return {"records_received": len(record_rows), "signals_received": len(signal_rows),
                "records_total": self.count("normalized_records"), "signals_total": self.count("risk_signals")}

    def count(self, table: str) -> int:
        if table not in {"normalized_records", "risk_signals"}:
            raise ValueError("Unsupported table")
        with self.connection() as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def latest_signals(self, limit: int = 20) -> list[dict[str, Any]]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM risk_signals ORDER BY timestamp DESC, signal_id LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def impact_summary(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT event_type, COUNT(*) AS signal_count, ROUND(AVG(impact_score), 2) AS avg_impact,
                          MAX(impact_score) AS max_impact
                   FROM risk_signals GROUP BY event_type ORDER BY avg_impact DESC, signal_count DESC"""
            ).fetchall()
        return [dict(row) for row in rows]
