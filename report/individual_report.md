# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Ngô Văn Nam |
| MSSV | 2A202601340 |
| Khóa/Lớp | K4 |
| Tên nhóm | 5AESieuNhan |
| Vai trò chính | Thành viên 2: Cleaning & Test Set |
| Repository | https://github.com/mronion112/K4_Day10_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning và data modeling | `src/ingestion/cleaning.py` — `build_clean_dataframe` | Danh sách `PaperRecord` đọc từ `crossref_records.json` | `papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Frozen evaluation set | `src/evaluation/testset.py` — `build_test_set` | Cleaned DataFrame | `data/eval/test_set.json` | Hoàn thành |

Đầu ra của tôi được bàn giao cho module Vector Database để embedding/index và cho các thành viên phụ trách Evaluation, Observability, Corruption/Repair.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Xác minh contract dữ liệu | Vector index và Observability | Clean dataset có đủ `text_for_embedding`, `age_days`, `summary_chars` và các trường joined |
| Xác minh frozen test set | Evaluation/Corruption flow | 15 câu hỏi giữ nguyên cho cả baseline, corrupted và repaired |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xóa HTML/XML và chuẩn hóa văn bản | `cleaning.py`, `_clean_text` | Giải mã HTML entity, xóa thẻ như `<jats:p>`, gộp whitespace | Chạy smoke test và kiểm tra CSV/JSON |
| Lọc dữ liệu không hợp lệ | `build_clean_dataframe` | Loại title/summary rỗng, summary dưới 100 ký tự, ngày lỗi và DOI trùng | Clean artifact có 24 bản ghi hợp lệ |
| Tạo trường phái sinh | `age_days`, `summary_chars`, `text_for_embedding` | Schema sẵn sàng cho freshness và embedding | Kiểm tra header `papers_clean.csv` |
| Tạo bộ đề cố định | `build_test_set` | 5 paper mẫu × 3 loại câu hỏi = 15 samples | Kiểm tra `data/eval/test_set.json` |

Artifact cụ thể: `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` gồm 24 paper; `data/eval/test_set.json` gồm 15 mẫu có đủ `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Metadata Crossref chứa HTML/XML, khoảng trắng không nhất quán, trường dạng list và ngày có thể lỗi. Dữ liệu thô chưa phù hợp để embedding hoặc dùng làm ground truth. Đồng thời evaluation cần một bộ đề tái lập được để so sánh công bằng ba trạng thái dữ liệu.

### Cách triển khai

Cleaning chuyển danh sách dataclass sang DataFrame, dùng regex loại thẻ, `html.unescape` giải mã entity và regex whitespace để chuẩn hóa chuỗi. Các dòng thiếu title/summary, summary ngắn hơn 100 ký tự hoặc ngày không parse được bị loại. Authors/categories được nối thành chuỗi; `age_days`, `summary_chars` và `text_for_embedding` được tạo; DOI trùng bị loại và dữ liệu được sắp theo ngày mới nhất.

Test-set builder kiểm tra tối thiểu 5 dòng và đủ cột bắt buộc. Hàm lấy mẫu 5 paper bằng `random_state=42`, sau đó sinh câu hỏi tác giả, ngày xuất bản và nội dung chính. Ground truth document ID luôn là DOI của paper nguồn. Khi pipeline không bật `REFRESH_TEST_SET`, file đã tạo được tái sử dụng như frozen evaluation set.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `list[PaperRecord]` và `run_date`; cleaned DataFrame cho test-set builder |
| Output | DataFrame sạch; danh sách JSON evaluation samples |
| Module phụ thuộc | `ingestion.crossref.PaperRecord`, utilities `ensure_parent`, `first_sentence` |
| Module sử dụng output | Retrieval index, Evaluation, Observability, Corruption/Repair |
| Điều kiện lỗi cần xử lý | Input rỗng, thiếu cột, dưới 5 paper, HTML/entity, ngày lỗi, summary ngắn, DOI trùng |

### Cách xác minh

```powershell
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
python -m compileall -q src script
```

- **Kết quả mong đợi:** clean dataset và frozen test set đúng schema; pipeline sử dụng được ở cả ba trạng thái.
- **Kết quả thực tế:** 24 clean records, 15 evaluation samples; baseline và repaired đạt retrieval hit rate 1.0.
- **Artifact/log:** `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`, `data/eval/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn paper cho evaluation sao cho kết quả có thể tái lập.
- **Các phương án đã cân nhắc:** lấy 5 dòng đầu; hoặc random sampling không seed; hoặc sampling với seed cố định.
- **Phương án đã chọn:** lấy 5 paper bằng `DataFrame.sample(..., random_state=42)` và đóng băng file JSON.
- **Lý do:** đa dạng hơn lấy các dòng đầu nhưng vẫn deterministic; cùng bộ câu hỏi có thể dùng để đo đúng ảnh hưởng của corruption và repair.
- **Bằng chứng quyết định phù hợp:** cả ba lượt evaluation đều có đúng 15 samples; metrics giảm ở corrupted và phục hồi ở repaired.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** dữ liệu HTML như `<jats:p>...</jats:p>` và HTML entities có thể đi vào nội dung embedding.
- **Lệnh hoặc bước tái hiện:** kiểm tra summary trong raw Crossref và chạy hàm `_clean_text` với chuỗi chứa tag/entity.
- **Nguyên nhân gốc:** abstract Crossref có thể dùng JATS XML; chỉ gọi `.strip()` không làm sạch markup.
- **Cách xử lý:** dùng regex thay tag bằng khoảng trắng, `html.unescape`, sau đó gộp whitespace.
- **Cách xác minh sau khi sửa:** smoke test cleaning thành công; `compileall` không báo lỗi; clean artifacts được pipeline sử dụng để build index.
- **Điều học được:** cleaning cho RAG cần giữ nội dung ngữ nghĩa nhưng loại markup có thể làm nhiễu embedding.

## 7. Hiểu biết về luồng end-to-end

1. Crossref trả metadata, ingestion lưu raw response/records; cleaning chuẩn hóa thành corpus sạch; MiniLM biến `text_for_embedding` thành vector và ChromaDB lưu để semantic search.
2. Mỗi câu hỏi lưu đáp án chuẩn và DOI chuẩn. Retrieval hit kiểm tra DOI có xuất hiện trong tài liệu được lấy về; token F1/judge so sánh câu trả lời với ground truth.
3. Quality checks đo schema, completeness, uniqueness và độ dài; freshness tập trung vào tuổi/ngày cập nhật của dữ liệu.
4. Phải dùng cùng frozen test set để biến độc lập duy nhất là trạng thái corpus. Nếu đổi câu hỏi, so sánh baseline/corrupted/repaired sẽ không công bằng.
5. Repair thành công khi clean/repaired artifacts trở lại hợp lệ, quality/freshness phục hồi và evaluation metrics quay gần hoặc bằng baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Mất/biến dạng document làm retrieval giảm 20 điểm phần trăm |
| `mean_token_f1` | 1.0000 | 0.6733 | 1.0000 | Nội dung rỗng/nhiễu làm đáp án sai lệch rõ |
| `judge_accuracy` | 1.0000 | 0.7333 | 1.0000 | Corrupted corpus giảm độ chính xác câu trả lời |
| `mean_judge_score` | 5.0000 | 4.0000 | 5.0000 | Repair khôi phục mức baseline |
| Quality checks | PASS (8/8) | FAIL (6/8) | PASS (8/8) | Phát hiện duplicate và summary ngắn/rỗng |
| Freshness status | Fresh, 0 stale | Fresh, 3 stale | Fresh, 0 stale | Trạng thái tổng vẫn fresh vì còn bản ghi mới, nhưng stale count phát hiện lỗi |

### Kết luận từ số liệu

1. Drop latest, blank/noise summary, truncate title, stale date và duplicate → quality fail, stale rows tăng 0 lên 3 → retrieval hit giảm 1.0 xuống 0.8 và token F1 giảm xuống 0.6733.
2. Rebuild dữ liệu từ raw records → quality trở lại 8/8, stale rows về 0 → toàn bộ metrics trở lại baseline.

Corruption ảnh hưởng rõ nhất là drop latest kết hợp blank summary: tài liệu ground-truth có thể biến mất hoặc mất nội dung cần để trả lời, tác động trực tiếp tới cả retrieval hit và answer F1.

Điểm khác kỳ vọng là freshness tổng vẫn báo `is_fresh=true` ở corrupted. Kiểm tra artifact cho thấy logic yêu cầu còn ít nhất một record fresh; tuy vậy `stale_rows=3` vẫn thể hiện chính xác lỗi cục bộ.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data contract rõ ràng giúp các bước ingestion, embedding và evaluation ghép nối ổn định.
2. Quality signal chi tiết như duplicate count hoặc stale rows hữu ích hơn chỉ nhìn một cờ pass/fail.
3. Chất lượng corpus ảnh hưởng trực tiếp tới cả khả năng tìm đúng tài liệu và độ đúng của câu trả lời RAG.

### Nếu có thêm thời gian

Tôi sẽ bổ sung unit test theo tham số cho nhiều biến thể JATS/HTML, timezone và ngày Crossref thiếu tháng/ngày; đo bằng tỷ lệ test pass và số raw records hợp lệ giữ lại sau cleaning.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngô Văn Nam
**Ngày xác nhận:** 2026-08-06
