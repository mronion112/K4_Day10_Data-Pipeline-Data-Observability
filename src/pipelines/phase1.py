from __future__ import annotations

from retrieval.index import LocalEmbeddingIndex
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from core.config import load_settings
from core.utils import now_utc, write_csv, write_json


def main() -> None:
    """TODO(student): xay dung baseline pipeline end-to-end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    # 1. Load settings tu .env va config mac dinh
    settings = load_settings()
    run_date = now_utc()

    print("=" * 60)
    print("PHASE 1 - BASELINE PIPELINE")
    print(f"Source: {settings.source_api}")
    print(f"Query:  {settings.source_query}")
    print(f"Filter: {settings.source_filter}")
    print(f"Max results: {settings.max_results}")
    print(f"LLM Provider: {settings.llm_provider} | Model: {settings.model_name}")
    print("=" * 60)

    # 2. Load raw records: uu tien cache, neu refresh_source=True thi fetch moi
    raw_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_path.exists():
        print("\n[1/8] Fetching raw records from Crossref API...")
        records = fetch_source_records(settings)
    else:
        print("\n[1/8] Loading raw records from cache...")
        records = load_raw_records(raw_path)
    print(f"  -> Loaded {len(records)} raw records")

    # 3. Clean data: lam sach, chuan hoa, tao text_for_embedding
    print("\n[2/8] Cleaning data...")
    df_clean = build_clean_dataframe(records, run_date)
    print(f"  -> Cleaned: {len(df_clean)} papers")

    # 4. Save clean artifacts (CSV + JSON)
    print("\n[3/8] Saving clean data...")
    write_csv(df_clean, settings.paths.clean_csv)
    # Chuyen Timestamp -> str de serializable JSON
    df_json = df_clean.copy()
    for col in df_json.select_dtypes(include=["datetime64[ns, UTC]", "datetime64[ns]"]).columns:
        df_json[col] = df_json[col].astype(str)
    write_json(settings.paths.clean_json, df_json.to_dict(orient="records"))
    print(f"  -> CSV: {settings.paths.clean_csv}")
    print(f"  -> JSON: {settings.paths.clean_json}")

    # 5. Build ChromaDB index: tao embedding, luu manifest
    print("\n[4/8] Building embedding index...")
    index = LocalEmbeddingIndex.build(
        df=df_clean,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"  -> Collection: {index.collection_name} ({len(index.documents)} docs)")

    # 6. Tao evaluation test set (frozen, luu de dung lai)
    print("\n[5/8] Creating evaluation test set...")
    test_set = build_test_set(df_clean, settings.paths.eval_testset)
    print(f"  -> Test set: {len(test_set)} questions")
    for q in test_set:
        print(f"     [{q['question_type']}] {q['id']}: {q['question'][:80]}...")

    # 7. Evaluate: chay agent + tinh metrics
    print("\n[6/8] Running evaluation...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"  -> Retrieval hit rate: {bundle.summary['retrieval_hit_rate']:.2%}")
    print(f"  -> Mean token F1:     {bundle.summary['mean_token_f1']:.4f}")
    print(f"  -> Judge accuracy:    {bundle.summary['judge_accuracy']:.2%}")
    print(f"  -> Mean judge score:  {bundle.summary['mean_judge_score']:.2f}/5")

    # 8. Data quality checks + freshness report
    print("\n[7/8] Running data quality and freshness checks...")
    from observability.quality import run_data_quality_checks, build_freshness_report
    from observability.reporting import generate_phase1_report

    quality = run_data_quality_checks(df_clean, settings, "baseline")
    freshness = build_freshness_report(df_clean, settings, settings.paths.freshness_report)
    print(f"  -> Quality: {quality['passed_checks']}/{quality['total_checks']} checks passed")
    print(f"  -> Freshness: {'FRESH' if freshness['is_fresh'] else 'STALE'}")

    # 9. Generate markdown report
    print("\n[8/8] Generating baseline report...")
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary={
            "api": settings.source_api,
            "query": settings.source_query,
            "max_results": settings.max_results,
            "raw_records": len(records),
            "clean_records": len(df_clean),
        },
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"  -> Report: {settings.paths.baseline_report}")

    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE")
    print(f"Baseline metrics: {settings.paths.baseline_metrics}")
    print(f"Baseline answers: {settings.paths.baseline_answers}")
    print("=" * 60)
