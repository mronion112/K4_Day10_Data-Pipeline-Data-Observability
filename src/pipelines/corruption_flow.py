from __future__ import annotations

import pandas as pd

from retrieval.index import LocalEmbeddingIndex
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report
from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json


def main() -> None:
    """TODO(student): xay dung corruption -> evaluate -> repair -> compare flow.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    settings = load_settings()
    run_date = now_utc()

    print("=" * 60)
    print("PHASE 2 - CORRUPTION FLOW")
    print("=" * 60)

    # 1. Load baseline metrics & clean dataset
    print("\n[1/7] Loading baseline data...")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    df_clean = pd.read_csv(settings.paths.clean_csv, parse_dates=["published_dt", "updated_dt"])
    print(f"  -> Baseline metrics: retrieval_hit_rate={baseline_metrics['retrieval_hit_rate']:.2%}")
    print(f"  -> Clean dataset: {len(df_clean)} papers")

    # 2. Tao corrupted dataset
    print("\n[2/7] Corrupting data...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    print(f"  -> Corrupted: {len(df_corrupted)} rows (was {len(df_clean)})")

    # 3. Save corrupted artifacts
    print("\n[3/7] Saving corrupted artifacts...")
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    df_json = df_corrupted.copy()
    for col in df_json.select_dtypes(include=["datetime64[ns, UTC]", "datetime64[ns]"]).columns:
        df_json[col] = df_json[col].astype(str)
    write_json(settings.paths.corrupted_clean_json, df_json.to_dict(orient="records"))
    print(f"  -> CSV: {settings.paths.corrupted_clean_csv}")

    # 4. Rebuild index & evaluate corrupted
    print("\n[4/7] Evaluating corrupted pipeline...")
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    bundle_corrupted = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"  -> Retrieval hit rate: {bundle_corrupted.summary['retrieval_hit_rate']:.2%}")
    print(f"  -> Mean token F1:     {bundle_corrupted.summary['mean_token_f1']:.4f}")
    print(f"  -> Judge accuracy:    {bundle_corrupted.summary['judge_accuracy']:.2%}")

    # 5. Quality checks & freshness tren corrupted data
    print("\n[5/7] Quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "freshness_corrupted.json"
    )
    print(f"  -> Quality: {corrupted_quality['passed_checks']}/{corrupted_quality['total_checks']} passed")
    print(f"  -> Freshness: {'FRESH' if corrupted_freshness['is_fresh'] else 'STALE'}")

    # 6. Repair — từ raw records đã lưu ở C2, chạy lại cleaning chuẩn
    print("\n[6/7] Repairing from saved raw records...")
    from ingestion.crossref import load_raw_records

    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    print(f"  -> Repaired: {len(df_repaired)} papers (from raw snapshot)")

    # Save repaired artifacts
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    df_json2 = df_repaired.copy()
    for col in df_json2.select_dtypes(include=["datetime64[ns, UTC]", "datetime64[ns]"]).columns:
        df_json2[col] = df_json2[col].astype(str)
    write_json(settings.paths.repaired_clean_json, df_json2.to_dict(orient="records"))

    # Evaluate repaired
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    bundle_repaired = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"  -> Retrieval hit rate: {bundle_repaired.summary['retrieval_hit_rate']:.2%}")
    print(f"  -> Mean token F1:     {bundle_repaired.summary['mean_token_f1']:.4f}")
    print(f"  -> Judge accuracy:    {bundle_repaired.summary['judge_accuracy']:.2%}")

    # Quality checks & freshness tren repaired data
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "freshness_repaired.json"
    )

    # 7. Tao comparison report
    print("\n[7/7] Generating comparison report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=bundle_corrupted.summary,
        repaired_metrics=bundle_repaired.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"  -> Report: {settings.paths.comparison_report}")

    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print("=" * 60)
    print()
    print("Comparison Summary:")
    print(f"  Baseline  -> Hit: {baseline_metrics['retrieval_hit_rate']:.2%} | F1: {baseline_metrics['mean_token_f1']:.4f} | Judge: {baseline_metrics['judge_accuracy']:.2%}")
    print(f"  Corrupted -> Hit: {bundle_corrupted.summary['retrieval_hit_rate']:.2%} | F1: {bundle_corrupted.summary['mean_token_f1']:.4f} | Judge: {bundle_corrupted.summary['judge_accuracy']:.2%}")
    print(f"  Repaired  -> Hit: {bundle_repaired.summary['retrieval_hit_rate']:.2%} | F1: {bundle_repaired.summary['mean_token_f1']:.4f} | Judge: {bundle_repaired.summary['judge_accuracy']:.2%}")
