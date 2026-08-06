from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


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
    """TODO(student): parse Crossref payload thanh list PaperRecord.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    records: list[PaperRecord] = []
    # payload["message"]["items"] chua danh sach cac paper tra ve tu Crossref API
    items = payload.get("message", {}).get("items", [])

    for item in items:
        # DOI la identifier duy nhat, bo qua neu thieu
        doi = item.get("DOI", "")
        if not doi:
            continue

        # Title nam trong list, lay phan tu dau tien
        title_parts = item.get("title", [])
        title = normalize_whitespace(title_parts[0]) if title_parts else ""

        # Abstract duoc su dung lam summary
        abstract = item.get("abstract", "")
        summary = normalize_whitespace(abstract) if abstract else ""

        # Authors: gop given + family thanh ten day du
        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            name = normalize_whitespace(f"{given} {family}")
            if name:
                authors.append(name)

        # Subject la danh sach categories, lay subject dau lam primary
        subjects = item.get("subject", [])
        primary_category = subjects[0] if subjects else ""

        # Ngay xuat ban: uu tien published-print > published-online > created
        published_date = item.get("published-print", {})
        if not published_date:
            published_date = item.get("published-online", {})
        if not published_date:
            published_date = item.get("created", {})
        # date-parts co dang [[year, month, day]] hoac ngan hon
        date_parts = published_date.get("date-parts", [[None]])[0]
        year = date_parts[0] or 0
        month = date_parts[1] if len(date_parts) > 1 else 1
        day = date_parts[2] if len(date_parts) > 2 else 1
        published = f"{year:04d}-{month:02d}-{day:02d}"

        # Ngay cap nhat: lay tu deposited date
        updated_date = item.get("deposited", {})
        updated_parts = updated_date.get("date-parts", [[None]])[0]
        u_year = updated_parts[0] or year
        u_month = updated_parts[1] if len(updated_parts) > 1 else 1
        u_day = updated_parts[2] if len(updated_parts) > 2 else 1
        updated = f"{u_year:04d}-{u_month:02d}-{u_day:02d}"

        # URL truy cap paper, fallback ve doi.org
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        # Tim link PDF trong danh sach link
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=subjects,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment="",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """TODO(student): goi source API, luu raw response, parse thanh records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    # Crossref REST API endpoint
    url = "https://api.crossref.org/works"
    # Tham so: tu khoa tim kiem, filter ngay/abstract, so luong ket qua
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }

    # Retry voi exponential backoff khi gap rate limit (429) hoac server error (503)
    max_retries = 3
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            break
        if response.status_code in (429, 503):
            wait = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait)
            continue
        response.raise_for_status()
    else:
        response.raise_for_status()

    # Parse JSON response
    payload = response.json()

    # Luu raw API response de truy vet sau nay
    ensure_parent(settings.paths.raw_api_response)
    write_json(settings.paths.raw_api_response, payload)

    # Goi ham parse_crossref_payload de chuyen raw JSON -> list PaperRecord
    records = parse_crossref_payload(payload)

    # Luu parsed records duoi dang JSON
    ensure_parent(settings.paths.raw_records_json)
    write_json(
        settings.paths.raw_records_json,
        [
            {
                "paper_id": r.paper_id,
                "title": r.title,
                "summary": r.summary,
                "authors": r.authors,
                "categories": r.categories,
                "primary_category": r.primary_category,
                "published": r.published,
                "updated": r.updated,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
            }
            for r in records
        ],
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    # Doc JSON da luu tu lan fetch truoc, tranh goi lai API
    data = read_json(path)
    records: list[PaperRecord] = []
    # Map tung dict trong JSON -> PaperRecord
    for item in data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item["authors"],
                categories=item["categories"],
                primary_category=item["primary_category"],
                published=item["published"],
                updated=item["updated"],
                abs_url=item["abs_url"],
                pdf_url=item["pdf_url"],
                comment=item["comment"],
            )
        )
    return records
