# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                         |
| ------------------ | ----------------------------------------------------------------- |
| Họ và tên       | Phạm Khắc Khương Duy                                               |
| MSSV               | 2A202601982                                                          |
| Khóa/Lớp         | K4                                                               |
| Tên nhóm         | [5AEsieunhan]                                                      |
| Vai trò chính    | Observability Owner — Data Quality & Reporting                    |
| Repository         | https://github.com/mronion112/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                                                        |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Data Quality Checks | `src/observability/quality.py` — `run_data_quality_checks()` | Cleaned DataFrame từ `cleaning.py` | `data/quality/quality_baseline.json`, `quality_corrupted.json`, `quality_repaired.json` | Hoàn thành |
| Freshness Report | `src/observability/quality.py` — `build_freshness_report()` | Cleaned DataFrame từ `cleaning.py` | `data/quality/freshness_report.json`, `freshness_corrupted.json`, `freshness_repaired.json` | Hoàn thành |
| Baseline Report | `src/observability/reporting.py` — `generate_phase1_report()` | Source summary, metrics, quality, freshness từ pipeline | `data/reports/phase1_report.md` | Hoàn thành |
| Comparison Report | `src/observability/reporting.py` — `generate_corruption_report()` | Baseline, corrupted, repaired metrics + quality/freshness từ 3 trạng thái | `data/reports/corruption_report.md` | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | ------------------------------------ | --------- |
| Debug lỗi serialization JSON (numpy types) | Pipeline integrator — `phase1.py` | Thêm `int()`, `bool()` cast cho numpy values trong quality checks |
| Hỗ trợ xác minh metrics corruption overlap | Cleaning & corruption owner — `corruption.py` | Xác nhận 3/6 quality check fail tương ứng với 3 nhóm corruption chính (duplicate, short summary, stale date) |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | --------------------- | --------------- |
| Kiểm tra data quality (6 checks) | `src/observability/quality.py:run_data_quality_checks()` | Baseline: 6/6 PASS; Corrupted: 3/6 FAIL; Repaired: 6/6 PASS | `data/quality/quality_baseline.json` |
| Báo cáo freshness | `src/observability/quality.py:build_freshness_report()` | Baseline: FRESH (24/24); Corrupted: STALE (3 stale, >180 days); Repaired: FRESH (24/24) | `data/quality/freshness_report.json` |
| Markdown report baseline | `src/observability/reporting.py:generate_phase1_report()` | `data/reports/phase1_report.md` (5 mục: Source, Metrics, Quality, Freshness, Conclusion) | Mở file markdown |
| Markdown report so sánh 3 trạng thái | `src/observability/reporting.py:generate_corruption_report()` | `data/reports/corruption_report.md` — bảng so sánh Baseline/Corrupted/Repaired | Mở file markdown |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File `data/reports/corruption_report.md` chứa bảng so sánh 3 trạng thái (Baseline → Corrupted → Repaired) cho Retrieval Hit Rate (100% → 58.82% → 100%), Token F1 (0.9582 → 0.4696 → 0.9582), Judge Accuracy (94.12% → 76.47% → 94.12%), Mean Judge Score (4.71 → 4.00 → 4.71), Quality status (PASS → FAIL → PASS), và Freshness status (FRESH → STALE → FRESH). Bảng này chứng minh trực quan rằng corruption làm giảm chất lượng agent và repair phục hồi hoàn toàn.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Observability trong data pipeline có hai mục tiêu chính:
1. **Data Quality**: Phát hiện sớm các vấn đề dữ liệu (thiếu trường, trùng lặp, nội dung không hợp lệ) trước khi chúng ảnh hưởng đến người dùng cuối.
2. **Reporting**: Tổng hợp metrics thành báo cáo có thể đọc được, giúp team so sánh chất lượng giữa các trạng thái dữ liệu (baseline, corrupted, repaired).

### Cách triển khai

**`run_data_quality_checks()`** — 6 loại checks:
- `row_count`: dataset không được rỗng (int cast từ `len(df)`)
- `paper_id_not_null`: không có paper_id null (đếm bằng `isna().sum()`)
- `paper_id_unique`: không có paper_id trùng (đếm bằng `duplicated().sum()`)
- `title_not_empty`: mọi title phải có nội dung (kết hợp `isna()` + `str.strip() == ""`)
- `summary_min_length`: summary phải đủ dài (≥50 chars, cho phép ≤20% ngắn — tolerance)
- `freshness`: age_days không vượt quá `freshness_threshold_days` (180 ngày từ Settings)

Mỗi check trả về `passed` (bool), `value` (int), và `message` mô tả. Tổng hợp: `all_passed`, `passed_checks`, `failed_checks`. Kết quả lưu vào `data/quality/quality_{report_name}.json`.

**`build_freshness_report()`** — Đo độ "tươi" của dữ liệu:
- Tìm `latest_published` và `oldest_published` từ cột `published_dt`
- Đếm số record `stale` (age_days > threshold)
- `is_fresh = True` nếu stale_rows = 0

**`generate_phase1_report()`** — Markdown report cho baseline với 5 section: Data Source, Metrics, Quality, Freshness, Conclusion. Tự động đọc các dict đầu vào và format thành bảng.

**`generate_corruption_report()`** — Markdown report so sánh 3 trạng thái: bảng metrics (Baseline | Corrupted | Repaired), quality status, freshness status, và phân tích impact (% thay đổi Retrieval Hit Rate).

### Input, output và contract

| Thành phần | Mô tả |
| -------------- | ------- |
| Input | `pd.DataFrame` từ cleaning pipeline (chứa các cột: paper_id, title, summary, summary_chars, age_days, published_dt, authors_joined, categories_joined) + `Settings` object |
| Output | JSON reports (`data/quality/quality_*.json`, `data/quality/freshness_*.json`), Markdown reports (`data/reports/phase1_report.md`, `data/reports/corruption_report.md`) |
| Module phụ thuộc | `core.config.Settings` cho threshold, paths; `core.utils` cho `write_json`, `write_text`, `ensure_parent` |
| Module sử dụng output | `pipelines/phase1.py` (gọi `run_data_quality_checks`, `build_freshness_report`, `generate_phase1_report`), `pipelines/corruption_flow.py` (gọi `run_data_quality_checks`, `build_freshness_report`, `generate_corruption_report`) |
| Điều kiện lỗi cần xử lý | DataFrame rỗng, thiếu cột `age_days`/`summary_chars`/`published_dt`, numpy types không serializable được sang JSON |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Quality baseline = 6/6 PASS, Corrupted = FAIL (ít nhất 3/6 fail)
- **Kết quả thực tế:** Baseline: 6/6 PASS, Corrupted: 3/6 FAIL (paper_id_unique, summary_min_length, freshness), Repaired: 6/6 PASS
- **Artifact/log:** `data/quality/quality_baseline.json`, `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi lưu quality report ra JSON, `json.dumps()` throw `TypeError: Object of type int64 is not JSON serializable` với các giá trị từ pandas/numpy như `np.int64`, `np.bool_`.

- **Các phương án đã cân nhắc:**
  1. Dùng custom JSON encoder kế thừa `json.JSONEncoder` để chuyển numpy types → Python native (sửa tại `core/utils.py:write_json`)
  2. Cast tường minh tất cả giá trị numpy sang Python native (`int()`, `bool()`, `str()`) trước khi đưa vào dict

- **Phương án đã chọn:** Phương án 2 — cast tường minh. Mọi giá trị từ pandas operations được bọc trong `int()` hoặc `bool()` trước khi append vào dict.

- **Lý do:** Đơn giản, không cần thay đổi `write_json()` trong `core/utils.py` (vốn được dùng chung bởi nhiều module khác như `metrics.py`, `phase1.py`), không ảnh hưởng đến các module khác. Cách này rõ ràng về mặt contract: quality report luôn chứa Python native types. Nếu sau này có ai viết thêm check mới và quên cast, lỗi sẽ xuất hiện ngay tại đường biên (boundary) của hàm, dễ debug hơn.

- **Bằng chứng quyết định phù hợp:** Sau khi cast, pipeline chạy thành công, quality report JSON parse được bình thường (`data/quality/quality_baseline.json` mở được bằng bất kỳ JSON viewer nào).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `TypeError: Object of type int64 is not JSON serializable` tại `write_json()` khi lưu quality report.
- **Lệnh hoặc bước tái hiện:** Chạy `uv run python script/run_phase1.py`, lỗi xảy ra tại bước `[7/8] Running data quality and freshness checks`.
- **Nguyên nhân gốc:** Pandas DataFrame operations trả về `numpy.int64`, `numpy.bool_` thay vì Python `int`, `bool`. `json.dumps()` mặc định không serialize được numpy types vì chúng không phải built-in Python types.
- **Cách xử lý:** Thêm `int()` cast cho tất cả giá trị số (`total_rows`, `null_ids`, `dup_ids`, `empty_titles`, `short_summaries`, `stale_rows`, `total_checks`, `passed_checks`, `failed_checks`, `threshold_days`, `fresh_rows`) và `bool()` cast cho các biểu thức điều kiện (`total_rows > 0`, `null_ids == 0`, `dup_ids == 0`, `empty_titles == 0`, `stale_rows == 0`, `all_passed`).
- **Cách xác minh sau khi sửa:** Chạy lại `uv run python script/run_phase1.py` → quality report được lưu thành công, `data/quality/quality_baseline.json` parse được bằng `json.load()`.
- **Điều học được:** Khi làm việc với pandas + JSON, luôn cast numpy types về Python native trước khi serialize. Đây là pitfall phổ biến trong data pipeline. Một cách phòng tránh hệ thống hơn là viết custom `NumpyJSONEncoder` trong `core/utils.py` để mọi module đều được hưởng lợi, nhưng đó là technical debt cho tương lai.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. **Crossref → vector index**: `fetch_source_records()` gọi Crossref REST API (`https://api.crossref.org/works`) với query `agentic retrieval augmented generation large language model` + filter + max_results=24 → parse JSON response thành list `PaperRecord` (DOI, title, abstract, authors, published date, categories, ...) → lưu raw response và raw records vào `data/raw/` để có thể audit/replay → `build_clean_dataframe()` chuẩn hóa (lowercase title, strip whitespace, parse date, dedupe theo DOI, đoán `text_for_embedding`, tính `age_days` so với run_date) → `LocalEmbeddingIndex.build()` dùng model `sentence-transformers/all-MiniLM-L6-v2` để encode `text_for_embedding` của mỗi paper → lưu vectors + metadata vào ChromaDB collection `papers-baseline` (path `data/embeddings/`).

2. **Test set đo gì**: Test set (`data/eval/test_set.json`) chứa `id`, `question`, `question_type`, `ground_truth` (câu trả lời chuẩn từ nội dung paper), và `ground_truth_doc_ids` (DOI của paper chứa đáp án — chính là paper_id từ clean dataframe). Khi evaluate, agent nhận question → dùng tool semantic_search hoặc exact lookup → sinh answer + retrieved_doc_ids → so sánh `retrieved_doc_ids` với `ground_truth_doc_ids` để tính `retrieval_hit_rate` (binary: retrieved có chứa ground_truth_doc_id không); so sánh answer với ground_truth bằng token-level F1 (`mean_token_f1`); dùng LLM judge chấm điểm 0–5 (`mean_judge_score`) và tính `judge_accuracy` (score ≥ threshold coi như đúng).

3. **Quality checks vs Freshness monitoring**: **Quality checks** kiểm tra cấu trúc và tính toàn vẹn của dữ liệu (completeness — `row_count`, `title_not_empty`, `summary_min_length`; uniqueness — `paper_id_unique`; validity — `paper_id_not_null`). Đây là các invariant về schema. **Freshness monitoring** kiểm tra dữ liệu có bị cũ không (`age_days > threshold_days`), một invariant về thời gian. Quality checks trả lời "dữ liệu có đúng không?", freshness trả lời "dữ liệu có mới không?". Một dataset có thể pass quality nhưng fail freshness (đủ trường, không trùng, nhưng đã 2 năm tuổi) và ngược lại (mới publish hôm qua nhưng title rỗng). Cả hai cùng thuộc observability nhưng đo các khía cạnh khác nhau của dữ liệu.

4. **Cùng test set cho 3 trạng thái**: Vì nếu thay đổi test set giữa các trạng thái, sự khác biệt về metrics có thể đến từ test set khác nhau (câu hỏi khác, paper khác) chứ không phải từ corruption. Dùng cùng test set đảm bảo mọi thay đổi metrics là do dữ liệu thay đổi, không phải do câu hỏi khác. Đây là nguyên tắc A/B testing cổ điển — chỉ thay đổi một biến (data state) giữa các lần đo.

5. **Repair thành công khi**: (a) `data/clean/papers_clean_repaired.csv` có số lượng row = baseline (24 papers) và schema khớp baseline; (b) `data/quality/quality_repaired.json` cho `all_passed: true`, 6/6 PASS; (c) `data/quality/freshness_repaired.json` cho `is_fresh: true`, stale_rows=0; (d) `data/results/repaired_metrics.json` có `retrieval_hit_rate ≈ baseline` (100%), `mean_token_f1 ≈ baseline` (0.9582), `judge_accuracy ≈ baseline` (94.12%), `mean_judge_score ≈ baseline` (4.71). Tất cả các điều kiện này đều đạt được trong lần chạy này — repair phục hồi hoàn toàn cả data signals lẫn agent metrics, chứng minh raw_records.json là single source of truth đáng tin cậy.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 100.00% | 58.82% | 100.00% | `drop_latest_records` xóa 3 paper; 3/17 câu test trỏ vào các paper bị xóa → hit = 0 cho 17.6%, giải thích phần lớn mức giảm 41.18% |
| `mean_token_f1` | 0.9582 | 0.4696 | 0.9582 | `blank_summary` (4 paper) + `inject_noise` (5 paper) làm embedding lệch → agent retrieve đúng paper nhưng trích đoạn text nhiễu, token overlap giảm mạnh |
| `judge_accuracy` | 94.12% | 76.47% | 94.12% | LLM judge vẫn chấm đúng phần lớn câu nhờ QA fallback extract từ metadata + LLM có khả năng đoán ngữ nghĩa; giảm ~18% |
| `mean_judge_score` | 4.71/5 | 4.00/5 | 4.71/5 | Điểm giảm nhưng không quá thấm nhờ LLM judge tolerant với paraphrase |
| Quality checks | 6/6 PASS | 3/6 FAIL | 6/6 PASS | 3 lỗi: `paper_id_unique` (2 dup do `add_duplicates`), `summary_min_length` (5 short do `blank_summary` + `inject_noise`), `freshness` (3 stale do `stale_date`) |
| Freshness status | FRESH | STALE | FRESH | `stale_date` lùi 3 record về 2021-06-15 → `oldest_published` nhảy từ 2026-02-13 về 2021-06-15, `age_days` vượt 180 ngày |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **[Data corruption: `stale_date` (3) + `blank_summary` (4) + `add_duplicates` (2)] → [quality: `paper_id_unique` FAIL (2 dup), `summary_min_length` FAIL (5 short), `freshness` FAIL (3 stale); freshness: 3 stale records, `is_fresh=False`] → [agent metric: hit rate 58.82%, F1 0.4696, judge accuracy 76.47%, judge score 4.00/5]**.
2. **[Repair action: `load_raw_records(raw_records_json)` → `build_clean_dataframe(raw_records, run_date)`] → [quality: 6/6 PASS; freshness: `is_fresh=True`, stale_rows=0] → [agent metric: hit rate 100%, F1 0.9582, judge accuracy 94.12%, judge score 4.71/5 — phục hồi hoàn toàn về baseline]**.

Corruption nào ảnh hưởng rõ nhất và vì sao?

`drop_latest_records` — vì nó xóa hẳn 3 paper khỏi vector index, trong đó có 3 paper nằm trong ground_truth_doc_ids của test set. Agent hoàn toàn không thể retrieve được tài liệu cho những câu này → retrieval hit = 0 cho 3/17 câu (~17.6%). Nhưng vì agent cũng không retrieve được nhầm paper khác (semantic search top-k chỉ chứa 21 paper còn lại, có thể một số câu trỏ vào paper còn lại nên vẫn hit), mức giảm thực tế là 41.18% (từ 100% xuống 58.82%). Các corruption khác (`blank_summary`, `inject_noise`) chỉ làm giảm chất lượng câu trả lời (token F1) chứ không làm mất khả năng retrieval, vì embedding vector của paper vẫn tồn tại trong index dù text bên trong bị corrupt.

Kết quả nào khác với kỳ vọng ban đầu?

`judge_accuracy` corrupted = 76.47% — cao hơn kỳ vọng. Dự kiến corruption nặng sẽ làm judge accuracy giảm mạnh hơn (xuống dưới 50%). Nguyên nhân: LLM judge (Gemini-2.5-flash theo config) có khả năng đoán ngữ nghĩa tốt — kể cả khi token overlap thấp, judge vẫn chấm đúng nếu answer về mặt semantic khớp với ground truth. Ngoài ra, QA layer trong agent có fallback extract câu trả lời từ metadata của paper (DOI, authors, categories) — một số câu test về `authors` hoặc `categories` vẫn trả lời đúng dù summary bị blank/noise vì metadata không bị corruption.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Observability không phải là "nice to have" mà là bắt buộc — quality checks phát hiện được lỗi trước khi người dùng nhận câu trả lời sai. Nếu không có quality checks, team sẽ không biết dữ liệu đã bị corrupt cho đến khi metrics tụt (lúc đó đã muộn để can thiệp). Bài lab này cho thấy quality checks phát hiện đúng cả 3 corruption "có thể phát hiện" (duplicate, short summary, stale date) — chỉ `drop_latest_records` và `truncate_title` không bị phát hiện vì không vi phạm invariant nào trong 6 check hiện tại.

2. **Về data quality/observability:** Quality checks và freshness monitoring là hai khía cạnh khác nhau nhưng bổ trợ: quality đo tính đúng đắn (schema, completeness, uniqueness), freshness đo tính thời sự (recency). Một dataset có thể pass quality nhưng fail freshness (dữ liệu cũ nhưng đầy đủ) và ngược lại (mới publish nhưng thiếu trường). Khi thiết kế monitoring cho production pipeline, nên tách rõ hai loại signal này thành hai dashboard/SLA khác nhau vì remediation cũng khác nhau (quality fail → re-clean/re-ingest, freshness fail → refresh source).

3. **Về ảnh hưởng của data đến RAG agent:** Dữ liệu xấu ảnh hưởng trực tiếp đến retrieval và answer quality. Một thay đổi nhỏ (xóa 3/24 paper = 12.5% dữ liệu) có thể làm giảm 41% retrieval hit rate. Điều này nhấn mạnh tầm quan trọng của data quality trong hệ thống RAG: vector index chỉ tốt khi dữ liệu nguồn tốt. Các phương pháp như re-ranking, query rewriting chỉ giảm nhẹ vấn đề chứ không thay thế được data quality tốt.

### Nếu có thêm thời gian

Thêm **Great Expectations (GX) integration** vào quality checks. Hiện tại quality checks là custom code trong `run_data_quality_checks()`, có thể nâng cấp lên dùng GX expectations để có:
- Expectation suites có thể tái sửụng giữa các dataset (cùng expectation `expect_column_values_to_not_be_null` áp dụng cho nhiều schema)
- Data Docs tự động sinh (HTML render đẹp hơn markdown hiện tại)
- Validation results chuẩn hóa theo GX schema, dễ integrate với monitoring tool (Prometheus, Datadog)

Cách đo: so sánh số lượng expectation tự động detect được vs manual checks hiện tại (6 checks). Mục tiêu: coverage ≥ 90% các corruption type trong bài lab với GX suite.

Ngoài ra, viết **unit test** cho `run_data_quality_checks()` và `build_freshness_report()` — hiện chỉ test qua end-to-end pipeline, nên bug ở edge case (DataFrame rỗng, thiếu cột) chỉ phát hiện khi chạy. Test riêng sẽ giúp debug nhanh hơn và refactor an toàn hơn.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Khắc Khương Duy
**Ngày xác nhận:** 2026-08-06
