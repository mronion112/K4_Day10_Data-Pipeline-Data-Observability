from __future__ import annotations

from datetime import UTC, datetime
import re

import pandas as pd

from ingestion.crossref import PaperRecord
from core.utils import normalize_whitespace


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Produce the clean schema consumed by the index, evaluation, and quality modules."""
    def clean_text(value: str) -> str:
        return normalize_whitespace(re.sub(r"<[^>]+>", " ", str(value or "")))

    today = (run_date.astimezone(UTC) if run_date.tzinfo else run_date.replace(tzinfo=UTC)).date()
    rows = []
    for record in records:
        title, summary = clean_text(record.title), clean_text(record.summary)
        published = pd.to_datetime(record.published, errors="coerce", utc=True)
        if not record.paper_id or not title or len(summary) < 100 or pd.isna(published):
            continue
        authors = ", ".join(filter(None, (clean_text(author) for author in record.authors))) or "Unknown"
        categories = ", ".join(filter(None, (clean_text(category) for category in record.categories))) or "Uncategorized"
        published_day = published.date()
        rows.append({"paper_id": clean_text(record.paper_id).lower(), "title": title, "summary": summary,
                     "published": published_day.isoformat(), "updated": clean_text(record.updated),
                     "authors_joined": authors, "categories_joined": categories,
                     "age_days": max(0, (today - published_day).days), "summary_chars": len(summary),
                     "text_for_embedding": f"Title: {title} | Authors: {authors} | Categories: {categories} | Summary: {summary}",
                     "abs_url": clean_text(record.abs_url), "pdf_url": clean_text(record.pdf_url)})
    columns = ["paper_id", "title", "summary", "published", "updated", "authors_joined", "categories_joined", "age_days", "summary_chars", "text_for_embedding", "abs_url", "pdf_url"]
    df = pd.DataFrame(rows, columns=columns).drop_duplicates(subset="paper_id", keep="first")
    return df.sort_values(["published", "paper_id"], ascending=[False, True], ignore_index=True) if not df.empty else df
