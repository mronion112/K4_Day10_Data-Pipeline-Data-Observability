# Baseline Pipeline Report

## Source

- Source: Crossref REST API
- Query: agentic retrieval augmented generation large language model
- Filter: from-pub-date:2026-02-07,has-abstract:true
- Raw records: 24

## Evaluation metrics

| Metric | Value |
| --- | ---: |
| samples | 12 |
| retrieval_hit_rate | 1.000 |
| mean_token_f1 | 1.000 |
| judge_accuracy | 1.000 |
| mean_judge_score | 5 |

## Data quality

- Overall status: **PASS**
- row_count: PASS (actual: 24; expected: > 0)
- paper_id_not_null: PASS (actual: 24; expected: all rows)
- paper_id_unique: PASS (actual: 0; expected: 0 duplicates)
- title_not_blank: PASS (actual: 0; expected: 0 blank titles)
- summary_minimum_length: PASS (actual: 0; expected: 0 summaries shorter than 100 chars)
- freshness: PASS (actual: 0; expected: no rows older than 180 days)

## Freshness

- Status: **FRESH**
- Latest published: 2026-08-01
- Oldest published: 2026-02-12
- Stale rows: 0 / 24
