# Corruption, Repair & Comparison Report

All three runs use the same frozen evaluation set.

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired | Corrupted - Baseline | Repaired - Baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| retrieval_hit_rate | 1.000 | 1.000 | 1.000 | +0.000 | +0.000 |
| mean_token_f1 | 1.000 | 0.750 | 1.000 | -0.250 | +0.000 |
| judge_accuracy | 1.000 | 0.750 | 1.000 | -0.250 | +0.000 |
| mean_judge_score | 5.000 | 4.000 | 5.000 | -1.000 | +0.000 |

## Data observability

| Signal | Corrupted | Repaired |
| --- | --- | --- |
| Quality | FAIL | PASS |
| Freshness | STALE | FRESH |
| Stale rows | 1 | 0 |

## Interpretation

The corrupted state is expected to fail quality checks because it contains blank summaries, a stale date, and a duplicate ID. Repair rebuilds the clean dataset from the immutable raw-record snapshot, then re-indexes and re-evaluates it.
