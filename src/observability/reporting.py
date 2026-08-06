from __future__ import annotations

from typing import Any

from core.utils import ensure_parent, write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report cho baseline phase.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    quality_all_passed = quality.get("all_passed", quality.get("status") == "ok")
    freshness_ok = freshness.get("is_fresh", freshness.get("status") == "ok")

    lines = [
        "# Baseline Report - Phase 1",
        "",
        "## 1. Data Source",
        f"- API: {source_summary.get('api', 'N/A')}",
        f"- Query: `{source_summary.get('query', 'N/A')}`",
        f"- Max results: {source_summary.get('max_results', 'N/A')}",
        f"- Raw records: {source_summary.get('raw_records', 'N/A')}",
        f"- Cleaned records: {source_summary.get('clean_records', 'N/A')}",
        "",
        "## 2. Retrieval & Evaluation Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Samples | {metrics.get('samples', 'N/A')} |",
        f"| Retrieval Hit Rate | {metrics.get('retrieval_hit_rate', 0):.2%} |",
        f"| Mean Token F1 | {metrics.get('mean_token_f1', 0):.4f} |",
        f"| Judge Accuracy | {metrics.get('judge_accuracy', 0):.2%} |",
        f"| Mean Judge Score | {metrics.get('mean_judge_score', 0):.2f}/5 |",
        "",
        "### Ragas Metrics",
        "",
    ]

    ragas = metrics.get("ragas", {})
    if ragas and "skipped" not in ragas:
        for key, value in ragas.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("Ragas evaluation was skipped (set RUN_RAGAS=1 to enable).")

    lines += [
        "",
        "## 3. Data Quality",
        f"- Total checks: {quality.get('total_checks', 'N/A')}",
        f"- Passed: {quality.get('passed_checks', 'N/A')}",
        f"- Failed: {quality.get('failed_checks', 'N/A')}",
        f"- All passed: **{'PASS' if quality_all_passed else 'FAIL'}**",
        "",
    ]

    # Chi tiet tung check
    for check in quality.get("checks", []):
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- [{status}] {check.get('check')}: {check.get('message')}")

    lines += [
        "",
        "## 4. Data Freshness",
        f"- Latest published: {freshness.get('latest_published', 'N/A')}",
        f"- Oldest published: {freshness.get('oldest_published', 'N/A')}",
        f"- Total rows: {freshness.get('total_rows', 'N/A')}",
        f"- Fresh rows: {freshness.get('fresh_rows', 'N/A')}",
        f"- Stale rows: {freshness.get('stale_rows', 'N/A')}",
        f"- Threshold: {freshness.get('threshold_days', 'N/A')} days",
        f"- Status: **{'FRESH' if freshness_ok else 'STALE'}**",
        "",
        "## 5. Conclusion",
        f"The baseline pipeline processed {source_summary.get('clean_records', 0)} papers. "
        f"Retrieval hit rate đạt {metrics.get('retrieval_hit_rate', 0):.2%}, "
        f"Judge accuracy đạt {metrics.get('judge_accuracy', 0):.2%}. "
        f"Data quality checks: **{'PASS' if quality_all_passed else 'FAIL'}**. "
        f"Freshness: **{'FRESH' if freshness_ok else 'STALE'}**.",
    ]

    markdown = "\n".join(lines)
    ensure_parent(report_path)
    write_text(report_path, markdown)


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
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    lines = [
        "# Corruption Report - Phase 2",
        "",
        "## Comparison: Baseline vs Corrupted vs Repaired",
        "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|--------|----------|-----------|----------|",
        f"| Retrieval Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0):.2%} | {corrupted_metrics.get('retrieval_hit_rate', 0):.2%} | {repaired_metrics.get('retrieval_hit_rate', 0):.2%} |",
        f"| Mean Token F1 | {baseline_metrics.get('mean_token_f1', 0):.4f} | {corrupted_metrics.get('mean_token_f1', 0):.4f} | {repaired_metrics.get('mean_token_f1', 0):.4f} |",
        f"| Judge Accuracy | {baseline_metrics.get('judge_accuracy', 0):.2%} | {corrupted_metrics.get('judge_accuracy', 0):.2%} | {repaired_metrics.get('judge_accuracy', 0):.2%} |",
        f"| Mean Judge Score | {baseline_metrics.get('mean_judge_score', 0):.2f} | {corrupted_metrics.get('mean_judge_score', 0):.2f} | {repaired_metrics.get('mean_judge_score', 0):.2f} |",
        "",
        "## Data Quality",
        "",
        "| Check | Corrupted | Repaired |",
        "|-------|-----------|----------|",
        f"| Quality passed | {corrupted_quality.get('all_passed', 'N/A')} | {repaired_quality.get('all_passed', 'N/A')} |",
        f"| Freshness | {corrupted_freshness.get('is_fresh', 'N/A')} | {repaired_freshness.get('is_fresh', 'N/A')} |",
        "",
        "## Impact Analysis",
        f"Corruption làm giảm Retrieval Hit Rate từ {baseline_metrics.get('retrieval_hit_rate', 0):.2%} "
        f"xuống {corrupted_metrics.get('retrieval_hit_rate', 0):.2%} "
        f"(thay đổi: {(corrupted_metrics.get('retrieval_hit_rate', 0) - baseline_metrics.get('retrieval_hit_rate', 0)):.2%}).",
        "",
        f"Sau repair, Retrieval Hit Rate phục hồi về {repaired_metrics.get('retrieval_hit_rate', 0):.2%}.",
    ]

    markdown = "\n".join(lines)
    ensure_parent(report_path)
    write_text(report_path, markdown)
