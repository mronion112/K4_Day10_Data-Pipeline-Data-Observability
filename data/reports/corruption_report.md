# Corruption Report - Phase 2

## Comparison: Baseline vs Corrupted vs Repaired

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Retrieval Hit Rate | 100.00% | 58.82% | 100.00% |
| Mean Token F1 | 0.9582 | 0.4696 | 0.9582 |
| Judge Accuracy | 94.12% | 76.47% | 94.12% |
| Mean Judge Score | 4.71 | 4.00 | 4.71 |

## Data Quality

| Check | Corrupted | Repaired |
|-------|-----------|----------|
| Quality passed | False | True |
| Freshness | False | True |

## Impact Analysis
Corruption làm giảm Retrieval Hit Rate từ 100.00% xuống 58.82% (thay đổi: -41.18%).

Sau repair, Retrieval Hit Rate phục hồi về 100.00%.