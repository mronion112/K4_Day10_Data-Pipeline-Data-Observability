from __future__ import annotations

from typing import Any

from core.utils import write_text


def _metric(value: Any) -> str:
    return f"{value:.3f}" if isinstance(value, float) else str(value if value is not None else "N/A")


def _quality_status(payload: dict[str, Any]) -> str:
    return "PASS" if payload.get("passed") else "FAIL"


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a self-contained baseline report from persisted pipeline results."""
    lines = ["# Baseline Pipeline Report", "", "## Source", "",
             f"- Source: {source_summary.get('source', 'Crossref REST API')}",
             f"- Query: {source_summary.get('query', 'N/A')}",
             f"- Filter: {source_summary.get('filter', 'N/A')}",
             f"- Raw records: {source_summary.get('records', 0)}", "", "## Evaluation metrics", "",
             "| Metric | Value |", "| --- | ---: |"]
    lines += [f"| {key} | {_metric(metrics.get(key))} |" for key in ("samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")]
    lines += ["", "## Data quality", "", f"- Overall status: **{_quality_status(quality)}**"]
    lines += [f"- {check['name']}: {'PASS' if check['passed'] else 'FAIL'} (actual: {check['actual']}; expected: {check['expectation']})" for check in quality.get("checks", [])]
    lines += ["", "## Freshness", "", f"- Status: **{'FRESH' if freshness.get('is_fresh') else 'STALE'}**",
              f"- Latest published: {freshness.get('latest_published')}", f"- Oldest published: {freshness.get('oldest_published')}",
              f"- Stale rows: {freshness.get('stale_rows')} / {freshness.get('total_rows')}"]
    write_text(report_path, "\n".join(lines) + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write an evidence-based comparison across the three fixed-test-set states."""
    metrics = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
    lines = ["# Corruption, Repair & Comparison Report", "", "All three runs use the same frozen evaluation set.", "",
             "## Evaluation comparison", "", "| Metric | Baseline | Corrupted | Repaired | Corrupted - Baseline | Repaired - Baseline |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name in metrics:
        base, corrupt, repair = (float(item.get(name, 0.0)) for item in (baseline_metrics, corrupted_metrics, repaired_metrics))
        lines.append(f"| {name} | {base:.3f} | {corrupt:.3f} | {repair:.3f} | {corrupt - base:+.3f} | {repair - base:+.3f} |")
    lines += ["", "## Data observability", "", "| Signal | Corrupted | Repaired |", "| --- | --- | --- |",
              f"| Quality | {_quality_status(corrupted_quality)} | {_quality_status(repaired_quality)} |",
              f"| Freshness | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'} | {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'} |",
              f"| Stale rows | {corrupted_freshness.get('stale_rows', 0)} | {repaired_freshness.get('stale_rows', 0)} |", "",
              "## Interpretation", "", "The corrupted state is expected to fail quality checks because it contains blank summaries, a stale date, and a duplicate ID. Repair rebuilds the clean dataset from the immutable raw-record snapshot, then re-indexes and re-evaluates it."]
    write_text(report_path, "\n".join(lines) + "\n")
