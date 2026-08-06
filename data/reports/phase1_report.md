# Baseline Report - Phase 1

## 1. Data Source
- API: Crossref REST API
- Query: `agentic retrieval augmented generation large language model`
- Max results: 24
- Raw records: 24
- Cleaned records: 24

## 2. Retrieval & Evaluation Metrics

| Metric | Value |
|--------|-------|
| Samples | 17 |
| Retrieval Hit Rate | 100.00% |
| Mean Token F1 | 0.9582 |
| Judge Accuracy | 94.12% |
| Mean Judge Score | 4.71/5 |

### Ragas Metrics

Ragas evaluation was skipped (set RUN_RAGAS=1 to enable).

## 3. Data Quality
- Total checks: 6
- Passed: 6
- Failed: 0
- All passed: **PASS**

- [PASS] row_count: Dataset has 24 rows.
- [PASS] paper_id_not_null: No null paper_id.
- [PASS] paper_id_unique: All paper_id are unique.
- [PASS] title_not_empty: All titles are present.
- [PASS] summary_min_length: All summaries have reasonable length.
- [PASS] freshness: All records are fresh.

## 4. Data Freshness
- Latest published: 2026-08-01
- Oldest published: 2026-02-13
- Total rows: 24
- Fresh rows: 24
- Stale rows: 0
- Threshold: 180 days
- Status: **FRESH**

## 5. Conclusion
The baseline pipeline processed 24 papers. Retrieval hit rate đạt 100.00%, Judge accuracy đạt 94.12%. Data quality checks: **PASS**. Freshness: **FRESH**.