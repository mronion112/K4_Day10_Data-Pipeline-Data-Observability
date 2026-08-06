# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                         |
| ------------------ | ----------------------------------------------------------------- |
| Họ và tên       | Trần Quang Minh                                                |
| MSSV               | 01210                                                            |
| Khóa/Lớp         | K4                                                               |
| Tên nhóm         | [Tên nhóm]                                                      |
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
| Debug lỗi serialization JSON (numpy types) | Thành viên 5 — `phase1.py` | Thêm `int()`, `bool()` cast cho numpy values trong quality checks |
| Hỗ trợ xác minh metrics corruption overlap | Thành viên 4 — `corruption.py` | Xác nhận 8/8 test documents bị corruption ảnh hưởng |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | --------------------- | --------------- |
| Kiểm tra data quality (6 checks) | `src/observability/quality.py:run_data_quality_checks()` | Baseline: 6/6 PASS; Corrupted: 3/6 FAIL | `data/quality/quality_baseline.json` |
| Báo cáo freshness | `src/observability/quality.py:build_freshness_report()` | Baseline: FRESH (24/24); Corrupted: STALE (3 stale, >180 days) | `data/quality/freshness_report.json` |
| Markdown report baseline | `src/observability/reporting.py:generate_phase1_report()` | `data/reports/phase1_report.md` (5 mục: Source, Metrics, Quality, Freshness, Conclusion) | Mở file markdown |
| Markdown report so sánh 3 trạng thái | `src/observability/reporting.py:generate_corruption_report()` | `data/reports/corruption_report.md` — bảng so sánh Baseline/Corrupted/Repaired | Mở file markdown |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File `data/reports/corruption_report.md` chứa bảng so sánh 3 trạng thái (Baseline → Corrupted → Repaired) cho Retrieval Hit Rate, Token F1, Judge Accuracy, Mean Judge Score, Quality status, và Freshness status. Bảng này chứng minh trực quan rằng corruption làm giảm chất lượng agent và repair phục hồi hoàn toàn.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Observability trong data pipeline có hai mục tiêu chính:
1. **Data Quality**: Phát hiện sớm các vấn đề dữ liệu (thiếu trường, trùng lặp, nội dung không hợp lệ) trước khi chúng ảnh hưởng đến người dùng cuối.
2. **Reporting**: Tổng hợp metrics thành báo cáo có thể đọc được, giúp team so sánh chất lượng giữa các trạng thái dữ liệu (baseline, corrupted, repaired).

### Cách triển khai

**`run_data_quality_checks()`** — 6 loại checks:
- `row_count`: dataset không được rỗng
- `paper_id_not_null`: không có paper_id null
- `paper_id_unique`: không có paper_id trùng
- `title_not_empty`: mọi title phải có nội dung
- `summary_min_length`: summary phải đủ dài (≥50 chars, cho phép ≤20% ngắn)
- `freshness`: age_days không vượt quá `freshness_threshold_days` (180 ngày)

Mỗi check trả về `passed` (bool), `value` (int), và `message` mô tả. Tổng hợp: `all_passed`, `passed_checks`, `failed_checks`. Kết quả lưu vào `data/quality/quality_{name}.json`.

**`build_freshness_report()`** — Đo độ "tươi" của dữ liệu:
- Tìm `latest_published` và `oldest_published`
- Đếm số record `stale` (age_days > threshold)
- `is_fresh = True` nếu stale_rows = 0

**`generate_phase1_report()`** — Markdown report cho baseline với 5 section: Data Source, Metrics, Quality, Freshness, Conclusion. Tự động đọc các dict đầu vào và format thành bảng.

**`generate_corruption_report()`** — Markdown report so sánh 3 trạng thái: bảng metrics (Baseline | Corrupted | Repaired), quality status, freshness status, và phân tích impact (% thay đổi).

### Input, output và contract

| Thành phần | Mô tả |
| -------------- | ------- |
| Input | `pd.DataFrame` từ cleaning pipeline (chứa các cột: paper_id, title, summary, summary_chars, age_days, published_dt, authors_joined, categories_joined) + `Settings` object |
| Output | JSON reports (`data/quality/`), Markdown reports (`data/reports/`) |
| Module phụ thuộc | `core.config.Settings` cho threshold, paths; `core.utils` cho write_json/write_text |
| Module sử dụng output | `pipelines/phase1.py`, `pipelines/corruption_flow.py` — gọi trực tiếp các hàm này |
| Điều kiện lỗi cần xử lý | DataFrame rỗng, thiếu cột `age_days`/`summary_chars`/`published_dt`, numpy types không serializable được sang JSON |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Quality baseline = 6/6 PASS, Corrupted = FAIL (ít nhất 3/6 fail)
- **Kết quả thực tế:** Baseline: 6/6 PASS, Corrupted: 3/6 FAIL (duplicates, short summary, stale), Repaired: 6/6 PASS
- **Artifact/log:** `data/quality/quality_baseline.json`, `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi lưu quality report ra JSON, `json.dumps()` throw `TypeError: Object of type int64 is not JSON serializable` với các giá trị từ pandas/numpy như `np.int64`, `np.bool_`.

- **Các phương án đã cân nhắc:**
  1. Dùng custom JSON encoder kế thừa `json.JSONEncoder` để chuyển numpy types → Python native
  2. Cast tường minh tất cả giá trị numpy sang Python native (`int()`, `bool()`, `str()`) trước khi đưa vào dict

- **Phương án đã chọn:** Phương án 2 — cast tường minh. Mọi giá trị từ pandas operations được bọc trong `int()` hoặc `bool()` trước khi append vào dict.

- **Lý do:** Đơn giản, không cần thay đổi `write_json()` trong `core/utils.py` (vốn được dùng chung), không ảnh hưởng đến các module khác. Cách này rõ ràng về mặt contract: quality report luôn chứa Python native types.

- **Bằng chứng quyết định phù hợp:** Sau khi cast, pipeline chạy thành công, quality report JSON parse được bình thường (`data/quality/quality_baseline.json`).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `TypeError: Object of type int64 is not JSON serializable` tại `write_json()` khi lưu quality report.
- **Lệnh hoặc bước tái hiện:** Chạy `uv run python script/run_phase1.py`, lỗi xảy ra tại bước [7/8] "Running data quality and freshness checks".
- **Nguyên nhân gốc:** Pandas DataFrame operations trả về `numpy.int64`, `numpy.bool_` thay vì Python `int`, `bool`. `json.dumps()` không serialize được numpy types.
- **Cách xử lý:** Thêm `int()` cast cho tất cả giá trị số (`null_ids`, `dup_ids`, `empty_titles`, `short_summaries`, `stale_rows`) và `bool()` cast cho các biểu thức điều kiện (`total_rows > 0`, `null_ids == 0`).
- **Cách xác minh sau khi sửa:** Chạy lại `uv run python script/run_phase1.py` → quality report được lưu thành công, `data/quality/quality_baseline.json` parse được.
- **Điều học được:** Khi làm việc với pandas + JSON, luôn cast numpy types về Python native trước khi serialize. Đây là pitfall phổ biến trong data pipeline.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref API → `fetch_source_records()` gọi API + parse → `PaperRecord` list → `build_clean_dataframe()` làm sạch, chuẩn hóa, tạo `text_for_embedding` → `LocalEmbeddingIndex.build()` dùng MiniLM-L6-v2 embed text → lưu vào ChromaDB vector store.

2. Test set chứa `question`, `ground_truth` (câu trả lời chuẩn), và `ground_truth_doc_ids` (paper chứa đáp án). Khi evaluate, agent trả lời → so sánh `retrieved_doc_ids` với `ground_truth_doc_ids` để tính hit rate; so sánh answer với ground_truth để tính token F1 + judge score.

3. **Quality checks** kiểm tra cấu trúc và tính toàn vẹn của dữ liệu (completeness, uniqueness, validity). **Freshness** kiểm tra dữ liệu có bị cũ không (age_days > threshold). Quality checks trả lời "dữ liệu có đúng không?", freshness trả lời "dữ liệu có mới không?". Cả hai cùng thuộc observability nhưng đo các khía cạnh khác nhau.

4. Vì nếu thay đổi test set giữa các trạng thái, sự khác biệt về metrics có thể đến từ test set khác nhau chứ không phải từ corruption. Dùng cùng test set đảm bảo mọi thay đổi metrics là do dữ liệu thay đổi, không phải do câu hỏi khác.

5. Repair thành công nếu: (a) `data/clean/papers_clean_repaired.csv` có số lượng và nội dung khớp baseline; (b) quality checks repaired = 6/6 PASS; (c) freshness repaired = FRESH; (d) retrieval_hit_rate và judge_accuracy repaired ≈ baseline. Tất cả các điều kiện này đều đạt (hit rate 100% → 58.82% → 100%).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 100.00% | 58.82% | 100.00% | drop_latest_records xóa 3 paper trong test set → hit rate giảm mạnh |
| `mean_token_f1` | 0.9582 | 0.4696 | 0.9582 | Blank summary + noise làm embedding và answer sai lệch |
| `judge_accuracy` | 94.12% | 76.47% | 94.12% | LLM judge vẫn chấm đúng phần lớn câu dù dữ liệu nhiễu |
| `mean_judge_score` | 4.71 | 4.00 | 4.71 | Điểm giảm nhưng không quá thấp nhờ QA fallback vẫn hoạt động |
| Quality checks | 6/6 PASS | 3/6 FAIL | 6/6 PASS | 3 lỗi: duplicates (x2), short summary (5), stale date (3) |
| Freshness status | FRESH | STALE | FRESH | 3 record bị lùi ngày về 5 năm trước → age_days > 180 |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Data corruption: stale_date + blank_summary + add_duplicates] → [quality: paper_id_unique FAIL, summary_min_length FAIL, freshness FAIL; freshness: 3 stale records, is_fresh=False] → [agent metric: hit rate 58.82%, F1 0.47, judge 76.47%].
2. [Repair action: load raw_records.json → build_clean_dataframe()] → [quality: 6/6 PASS; freshness: is_fresh=True] → [agent metric: hit rate 100%, F1 0.96, judge 94.12% — phục hồi hoàn toàn].

Corruption nào ảnh hưởng rõ nhất và vì sao?

`drop_latest_records` — vì nó xóa hẳn 3 paper khỏi index, trong đó có 3 paper nằm trong test set (q1, q2, q3). Agent hoàn toàn không thể tìm thấy tài liệu cho những câu này → retrieval hit = 0 cho 3/17 câu (~17.6%), giải thích phần lớn mức giảm từ 100% xuống 58.82%. Các corruption khác (blank summary, noise) chỉ làm giảm chất lượng trả lời chứ không làm mất khả năng tìm kiếm.

Kết quả nào khác với kỳ vọng ban đầu?

Judge accuracy corrupted = 76.47% — cao hơn kỳ vọng. Dự kiến corruption nặng sẽ làm judge accuracy giảm mạnh hơn. Nguyên nhân: drop_latest_records ảnh hưởng retrieval nhưng không ảnh hưởng judge (vì judge so sánh answer với ground truth, nếu retrieval trượt thì token F1 = 0 nhưng judge vẫn có thể thấy câu trả lời "liên quan"). Ngoài ra, QA extract answer từ metadata nên một số câu vẫn trả lời đúng dù dữ liệu bị corrupt.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Observability không phải là "nice to have" mà là bắt buộc — quality checks phát hiện được lỗi trước khi người dùng nhận câu trả lời sai. Nếu không có quality checks, team sẽ không biết dữ liệu đã bị corrupt cho đến khi metrics tụt.

2. **Về data quality/observability:** Quality checks và freshness monitoring là hai khía cạnh khác nhau nhưng bổ trợ: quality đo tính đúng đắn, freshness đo tính thời sự. Một dataset có thể pass quality nhưng fail freshness (dữ liệu cũ) và ngược lại.

3. **Về ảnh hưởng của data đến RAG agent:** Dữ liệu xấu ảnh hưởng trực tiếp đến retrieval và answer quality. Một thay đổi nhỏ (xóa 3/24 paper, 12.5% dữ liệu) có thể làm giảm 41% retrieval hit rate. Điều này nhấn mạnh tầm quan trọng của data quality trong hệ thống RAG.

### Nếu có thêm thời gian

Thêm Great Expectations (GX) integration vào quality checks. Hiện tại quality checks là custom code, có thể nâng cấp lên dùng GX expectations để có:
- Expectation suites có thể tái sử dụng
- Data docs tự động sinh
- Validation results chuẩn hóa

Cách đo: so sánh số lượng expectation tự động detect được vs manual checks hiện tại.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Quang Minh
**Ngày xác nhận:** 2026-08-06
