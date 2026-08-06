from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run transparent, dependency-light quality checks and persist an audit artifact."""
    row_count = len(df)
    def result(name: str, passed: bool, actual: Any, expectation: str) -> dict[str, Any]:
        return {"name": name, "passed": bool(passed), "actual": actual, "expectation": expectation}
    checks = [
        result("row_count", row_count > 0, row_count, "> 0"),
        result("paper_id_not_null", "paper_id" in df and int(df["paper_id"].notna().sum()) == row_count, int(df.get("paper_id", pd.Series(dtype=object)).notna().sum()), "all rows"),
        result("paper_id_unique", "paper_id" in df and bool(df["paper_id"].is_unique), int(df.get("paper_id", pd.Series(dtype=object)).duplicated().sum()), "0 duplicates"),
        result("title_not_blank", "title" in df and bool(df["title"].fillna("").str.strip().ne("").all()), int(df.get("title", pd.Series(dtype=object)).fillna("").str.strip().eq("").sum()), "0 blank titles"),
        result("summary_minimum_length", "summary" in df and bool((df["summary"].fillna("").str.len() >= 100).all()), int((df.get("summary", pd.Series(dtype=object)).fillna("").str.len() < 100).sum()), "0 summaries shorter than 100 chars"),
        result("freshness", "age_days" in df and bool((pd.to_numeric(df["age_days"], errors="coerce") <= settings.freshness_threshold_days).all()), int((pd.to_numeric(df.get("age_days", pd.Series(dtype=float)), errors="coerce") > settings.freshness_threshold_days).sum()), f"no rows older than {settings.freshness_threshold_days} days"),
    ]
    payload = {"report_name": report_name, "row_count": row_count, "passed": all(check["passed"] for check in checks), "checks": checks}
    write_json(settings.paths.quality_dir / f"{report_name}.json", payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarise freshness from normalized publication dates."""
    dates = pd.to_datetime(df.get("published", pd.Series(dtype=object)), errors="coerce", utc=True)
    ages = pd.to_numeric(df.get("age_days", pd.Series(dtype=float)), errors="coerce")
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    payload = {"latest_published": dates.max().date().isoformat() if not dates.dropna().empty else None,
               "oldest_published": dates.min().date().isoformat() if not dates.dropna().empty else None,
               "stale_rows": stale_rows, "total_rows": len(df),
               "threshold_days": settings.freshness_threshold_days,
               "is_fresh": bool(len(df) > 0 and stale_rows == 0 and dates.notna().all())}
    write_json(report_path, payload)
    return payload
