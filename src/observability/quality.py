from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import ensure_parent, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """TODO(student): tao bo data quality checks.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    total_rows = len(df)
    checks: list[dict[str, Any]] = []

    # Check 1: row count > 0
    checks.append({
        "check": "row_count",
        "passed": bool(total_rows > 0),
        "value": int(total_rows),
        "message": f"Dataset has {total_rows} rows." if total_rows > 0 else "Dataset is empty.",
    })

    # Check 2: paper_id not null & unique
    null_ids = int(df["paper_id"].isna().sum())
    dup_ids = int(df["paper_id"].duplicated().sum())
    checks.append({
        "check": "paper_id_not_null",
        "passed": bool(null_ids == 0),
        "value": null_ids,
        "message": f"{null_ids} null paper_id(s)." if null_ids else "No null paper_id.",
    })
    checks.append({
        "check": "paper_id_unique",
        "passed": bool(dup_ids == 0),
        "value": dup_ids,
        "message": f"{dup_ids} duplicate paper_id(s)." if dup_ids else "All paper_id are unique.",
    })

    # Check 3: title not null & not empty
    empty_titles = int(df["title"].isna().sum() + (df["title"].str.strip() == "").sum())
    checks.append({
        "check": "title_not_empty",
        "passed": bool(empty_titles == 0),
        "value": empty_titles,
        "message": f"{empty_titles} empty title(s)." if empty_titles else "All titles are present.",
    })

    # Check 4: summary length (phan lon summary du dai)
    if "summary_chars" in df.columns:
        short_summaries = int((df["summary_chars"] < 50).sum())
        checks.append({
            "check": "summary_min_length",
            "passed": bool(short_summaries <= total_rows * 0.2),
            "value": short_summaries,
            "message": (
                f"{short_summaries} summaries < 50 chars."
                if short_summaries else "All summaries have reasonable length."
            ),
        })

    # Check 5: freshness (age_days khong qua threshold)
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        checks.append({
            "check": "freshness",
            "passed": bool(stale_rows == 0),
            "value": stale_rows,
            "threshold_days": int(settings.freshness_threshold_days),
            "message": (
                f"{stale_rows} stale records (> {settings.freshness_threshold_days} days old)."
                if stale_rows else "All records are fresh."
            ),
        })
    else:
        stale_rows = 0

    # Tong hop ket qua
    all_passed = bool(all(c["passed"] for c in checks))
    report = {
        "report_name": report_name,
        "timestamp": str(pd.Timestamp.now()),
        "total_checks": len(checks),
        "passed_checks": int(sum(1 for c in checks if c["passed"])),
        "failed_checks": int(sum(1 for c in checks if not c["passed"])),
        "all_passed": all_passed,
        "checks": checks,
    }

    # Ghi JSON report
    output_path = settings.paths.quality_dir / f"quality_{report_name}.json"
    ensure_parent(output_path)
    write_json(output_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """TODO(student): tong hop freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    total_rows = len(df)

    # Tim ngay publish moi nhat va cu nhat
    if "published_dt" in df.columns and not df["published_dt"].isna().all():
        latest = df["published_dt"].max()
        oldest = df["published_dt"].min()
        latest_str = str(latest.date()) if pd.notna(latest) else "N/A"
        oldest_str = str(oldest.date()) if pd.notna(oldest) else "N/A"
    else:
        latest_str = "N/A"
        oldest_str = "N/A"

    # Dem so record stale (age_days > threshold)
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    freshness = {
        "total_rows": int(total_rows),
        "latest_published": latest_str,
        "oldest_published": oldest_str,
        "stale_rows": stale_rows,
        "fresh_rows": int(total_rows - stale_rows),
        "threshold_days": int(settings.freshness_threshold_days),
        "is_fresh": bool(stale_rows == 0),
    }

    ensure_parent(report_path)
    write_json(report_path, freshness)

    return freshness
