from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Map Crossref's nested response to the stable raw-record contract."""
    def text(value: Any) -> str:
        if isinstance(value, list):
            value = " ".join(str(item) for item in value if item)
        return normalize_whitespace(str(value or ""))

    def published(item: dict[str, Any]) -> str:
        for key in ("published-print", "published-online", "issued", "created", "deposited"):
            parts = item.get(key, {}).get("date-parts", [[]])
            if parts and parts[0]:
                try:
                    values = [int(value) for value in parts[0]]
                    return date(values[0], values[1] if len(values) > 1 else 1, values[2] if len(values) > 2 else 1).isoformat()
                except (TypeError, ValueError):
                    continue
        return ""

    records: list[PaperRecord] = []
    for item in payload.get("message", {}).get("items", []):
        doi = text(item.get("DOI"))
        title = text(item.get("title"))
        summary = text(item.get("abstract"))
        if not doi or not title or not summary:
            continue
        authors = [text(" ".join(filter(None, [author.get("given", ""), author.get("family", "")])))
                   for author in item.get("author", [])]
        categories = [text(subject) for subject in item.get("subject", []) if text(subject)]
        url = text(item.get("URL"))
        records.append(PaperRecord(
            paper_id=doi, title=title, summary=summary, authors=[author for author in authors if author],
            categories=categories, primary_category=categories[0] if categories else "Uncategorized",
            published=published(item), updated=published({"created": item.get("created", {})}),
            abs_url=url, pdf_url=text(item.get("link", [{}])[0].get("URL")) if item.get("link") else "",
            comment=text(item.get("publisher")),
        ))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch a reproducible Crossref snapshot with bounded exponential backoff."""
    params = {"query": settings.source_query, "filter": settings.source_filter, "rows": settings.max_results,
              "select": "DOI,title,abstract,author,subject,published-print,published-online,issued,created,URL,link,publisher"}
    response = None
    for attempt in range(4):
        response = requests.get("https://api.crossref.org/works", params=params, timeout=30,
                                headers={"User-Agent": "day10-data-observability-lab/1.0 (educational)"})
        if response.status_code not in {429, 503}:
            response.raise_for_status()
            break
        if attempt == 3:
            response.raise_for_status()
        time.sleep(2 ** attempt)
    assert response is not None
    payload = response.json()
    records = parse_crossref_payload(payload)
    # A narrow publication window may legitimately contain no abstracts.  Keep
    # the same source/query but widen only the date constraint so the lab can
    # still produce a usable, auditable corpus.
    if not records:
        fallback_params = {**params, "filter": "has-abstract:true"}
        fallback = requests.get("https://api.crossref.org/works", params=fallback_params, timeout=30,
                                headers={"User-Agent": "day10-data-observability-lab/1.0 (educational)"})
        fallback.raise_for_status()
        payload = fallback.json()
        records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_api_response, payload)
    write_json(settings.paths.raw_records_json, [record.__dict__ for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the raw-record snapshot, tolerating optional fields from earlier runs."""
    return [PaperRecord(**{field: item.get(field, [] if field in {"authors", "categories"} else "")
                           for field in PaperRecord.__dataclass_fields__}) for item in read_json(path)]
