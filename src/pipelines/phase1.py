from __future__ import annotations

from datetime import UTC, datetime

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the reproducible clean-data baseline pipeline."""
    settings = load_settings()
    raw_path = settings.paths.raw_records_json
    records = fetch_source_records(settings) if settings.refresh_source or not raw_path.exists() else load_raw_records(raw_path)
    clean_df = build_clean_dataframe(records, datetime.now(UTC))
    if clean_df.empty:
        raise RuntimeError("Cleaning produced no usable records; inspect the Crossref raw snapshot.")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)
    bundle = evaluate_pipeline(settings, index, settings.paths.eval_testset, settings.paths.baseline_metrics, settings.paths.baseline_answers)
    quality = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    generate_phase1_report(settings.paths.baseline_report, {"source": settings.source_api, "query": settings.source_query,
                           "filter": settings.source_filter, "records": len(records)}, bundle.summary, quality, freshness)
    print(f"Baseline complete: {len(clean_df)} clean papers, {bundle.summary['samples']} evaluation questions.")
