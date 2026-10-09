"""Small GDELT DOC 2.0 Article List adapter using only the Python standard library.

GDELT's DOC API returns article metadata/headlines, not full article bodies. This
adapter uses the title as text and retains the source URL. Review provider terms
and downstream publisher rights before storing or redistributing fetched data.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = '(bankruptcy OR default OR "credit rating" OR earnings OR acquisition OR "data breach" OR sanctions)'


def _parse_gdelt_date(value: str) -> str:
    value = value.strip()
    # GDELT commonly returns YYYYMMDDTHHMMSSZ.
    if len(value) == 16 and value.endswith("Z") and "T" in value:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError as exc:
        raise ValueError(f"Unrecognized GDELT seendate format: {value!r}") from exc


def fetch_gdelt(query: str = DEFAULT_QUERY, max_records: int = 25, timespan: str = "1day", timeout: int = 20) -> list[dict[str, Any]]:
    """Fetch recent GDELT headlines and normalize them to this project's input contract."""
    if not query.strip():
        raise ValueError("query cannot be empty")
    if not 1 <= max_records <= 250:
        raise ValueError("max_records must be between 1 and 250")
    params = {"query": query, "mode": "artlist", "format": "json", "maxrecords": max_records, "timespan": timespan, "sort": "datedesc"}
    request = Request(BASE_URL + "?" + urlencode(params), headers={"User-Agent": "AINLPRiskEngine/0.1 (educational prototype)"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read().decode("utf-8", errors="replace")
    if "html" in content_type.lower() or raw.lstrip().lower().startswith("<!doctype html"):
        raise RuntimeError("GDELT returned an HTML error instead of JSON; check query syntax or retry later.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GDELT response was not valid JSON: {raw[:200]!r}") from exc
    articles = payload.get("articles", [])
    records: list[dict[str, Any]] = []
    for article in articles:
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        if not title or not url:
            continue
        source_id = sha256(url.encode("utf-8")).hexdigest()[:20]
        seen = article.get("seendate") or datetime.now(timezone.utc).isoformat()
        records.append({
            "record_id": f"gdelt_{source_id}", "source": "gdelt_doc_api", "source_id": source_id,
            "published_at": _parse_gdelt_date(seen), "text": title, "source_url": url,
            "metadata": {"domain": article.get("domain"), "language": article.get("language"),
                         "source_country": article.get("sourcecountry"), "text_field": "headline_only"},
        })
    return records
