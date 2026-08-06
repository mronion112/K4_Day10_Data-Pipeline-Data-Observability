# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin       | Nội dung                               |
| --------------- | -------------------------------------- |
| Khóa/Lớp        | K4                                     |
| Tên nhóm        | 5AESieuNhan                            |
| Repository      | *(https://github.com/mronion112/K4_Day10_Data-Pipeline-Data-Observability)* |
| Ngày hoàn thành | 2026-08-06                             |

### Thành viên và phân công

| STT | Họ và tên            | MSSV        | Vai trò chính            | Module/Deliverable                                    |
| --: | -------------------- | ----------- | ------------------------ | ----------------------------------------------------- |
|   1 | Phạm Khắc Khương Duy     | 2A202601982     | Data Ingestion           | Crossref Fetching                                     |
|   2 | Ngô Văn Nam     | 2A202601340   | Cleaning & Embedding     | Cleaning Pipeline, ChromaDB                           |
|   3 | Trần Quang Minh     | 2A2202601210    | Evaluation               | Test Set & Metrics                                    |
|   4 | Nguyễn Hoàng Anh    | 2A2202601186   | Corruption & Repair      | Controlled Corruption, Repair Pipeline                |
|   5 | Đào Kiều Thịnh Quang | 2A202601014 | Integration & Comparison | Baseline Pipeline, Corruption Flow, Agent Integration |

---

# 2. Tóm tắt kết quả

Nhóm đã hoàn thành toàn bộ pipeline Data Pipeline & Data Observability theo yêu cầu của bài lab. Pipeline thực hiện quá trình thu thập dữ liệu từ Crossref, chuẩn hóa dữ liệu, xây dựng ChromaDB vector index, đánh giá Retrieval-Augmented Generation (RAG), theo dõi chất lượng dữ liệu (Data Quality) và độ mới dữ liệu (Freshness), sau đó mô phỏng các lỗi dữ liệu (corruption), thực hiện repair và so sánh kết quả giữa ba trạng thái.

Baseline pipeline tạo đầy đủ các artifact gồm raw records, cleaned dataset, embedding index, frozen evaluation set, baseline metrics, quality report, freshness report và phase1 report. Controlled corruption tạo duplicate record, blank summary và stale publish date, làm giảm chất lượng câu trả lời trong khi retrieval hit rate vẫn giữ nguyên do tài liệu đúng vẫn nằm trong top-k. Repair được thực hiện từ raw snapshot thay vì chỉnh sửa trực tiếp dữ liệu lỗi, giúp phục hồi hoàn toàn quality checks, freshness và toàn bộ metrics về mức baseline.

Blocker lớn nhất của nhóm là việc tích hợp OpenAI GPT-5.6 với LangChain agent khi sử dụng function tools. Nhóm đã điều chỉnh reasoning configuration phù hợp và bổ sung metadata cho retrieval tools để agent hoạt động ổn định.

---

# 3. Kiến trúc và luồng dữ liệu

## Luồng end-to-end

```text
Crossref API
    ↓
Raw response / Raw records
    ↓
Cleaning & Data Modeling
    ↓
Embedding + ChromaDB Index
    ↓
Baseline Evaluation
    ↓
Quality Checks + Freshness Monitoring
    ↓
Controlled Corruption
    ↓
Rebuild Index + Re-evaluation
    ↓
Repair from Raw Records
    ↓
Comparison Report
```

## Trách nhiệm từng khối

| Khối              | Input                   | Xử lý                                  | Output                       |
| ----------------- | ----------------------- | -------------------------------------- | ---------------------------- |
| Ingestion         | Crossref API            | Fetch, parse, lưu raw snapshot         | `data/raw/`                  |
| Cleaning          | Raw records             | Chuẩn hóa metadata, tạo text embedding | `data/clean/`                |
| Embedding         | Clean dataset           | Sinh vector embedding, build ChromaDB  | `data/embeddings/`           |
| Evaluation        | Index + Frozen test set | Retrieval & Answer Evaluation          | `data/results/`              |
| Observability     | Metrics                 | Quality checks, Freshness              | `data/quality/`              |
| Corruption/Repair | Clean dataset           | Controlled corruption, rebuild, repair | Corrupted/Repaired artifacts |
| Orchestration     | Các module trên         | Điều phối toàn bộ pipeline             | Reports                      |

---

# 4. Cách tái hiện kết quả

## Cấu hình

| Thành phần          | Giá trị                                |
| ------------------- | -------------------------------------- |
| LLM Provider        | OpenAI                                 |
| LLM Model           | gpt-5.6-luna                           |
| Embedding Model     | sentence-transformers/all-MiniLM-L6-v2 |
| Crossref Records    | 24                                     |
| Retrieval Top-k     | 4                                      |
| Freshness Threshold | 180 ngày                               |

## Cài đặt

```bash
uv sync
```

## Chạy Baseline

```bash
uv run python script/run_phase1.py
```

## Chạy Corruption Flow

```bash
uv run python script/run_corruption_flow.py
```

## Chạy Agent Demo

```bash
uv run python script/run_agent_demo.py
```

---

# 5. Ingestion, Cleaning và Data Contract

Nguồn dữ liệu sử dụng Crossref REST API với 24 bài báo khoa học. Sau khi tải về, dữ liệu được lưu thành raw snapshot để đảm bảo khả năng audit và reproducibility.

Cleaning pipeline chuẩn hóa metadata, loại bỏ dữ liệu không hợp lệ, tạo `text_for_embedding`, tính `age_days`, chuẩn hóa authors và categories trước khi build ChromaDB index.

Repair không sửa trực tiếp dữ liệu corrupted mà đọc lại `data/raw/crossref_records.json`, chạy lại toàn bộ cleaning pipeline để tái tạo dữ liệu sạch, đảm bảo khả năng tái hiện và truy vết.

---

# 6. Evaluation Setup

| Thành phần      | Giá trị                        |
| --------------- | ------------------------------ |
| Frozen Test Set | 12 câu hỏi factual             |
| Embedding Model | all-MiniLM-L6-v2               |
| Vector Store    | ChromaDB                       |
| Top-k           | 4                              |
| LLM             | OpenAI GPT-5.6-luna            |
| Test Set        | Giữ nguyên cho cả 3 trạng thái |

Việc sử dụng cùng một frozen evaluation set cho Baseline, Corrupted và Repaired giúp đảm bảo mọi thay đổi của metrics phản ánh đúng tác động của dữ liệu và vector index, thay vì do thay đổi tập câu hỏi.

---

# 7. Baseline Artifacts

| Artifact         | Đường dẫn                            |
| ---------------- | ------------------------------------ |
| Raw Records      | `data/raw/`                          |
| Clean Dataset    | `data/clean/papers_clean.csv`        |
| Embedding Index  | `data/embeddings/`                   |
| Evaluation Set   | `data/eval/test_set.json`            |
| Baseline Metrics | `data/results/baseline_metrics.json` |
| Quality Reports  | `data/quality/`                      |
| Baseline Report  | `data/reports/phase1_report.md`      |

---

# 8. Data Quality & Freshness

Quality checks kiểm tra duplicate records, missing values, empty summary, invalid metadata và các điều kiện về tính toàn vẹn dữ liệu.

Freshness monitoring đánh giá độ mới của dữ liệu dựa trên ngày xuất bản. Corrupted state cố ý thay đổi publish date về năm 2000 làm trạng thái chuyển sang STALE.

---

# 9. Corruption và Repair

Các corruption được sử dụng gồm:

* Blank Summary
* Duplicate Record
* Stale Publish Date

Repair được thực hiện từ raw snapshot đáng tin cậy bằng cách chạy lại cleaning pipeline và rebuild toàn bộ embedding index thay vì chỉnh sửa trực tiếp dữ liệu lỗi.

Corruption log được lưu tại:

```
data/results/corruption_log.json
```

---

# 10. So sánh ba trạng thái

| Metric             | Baseline | Corrupted | Repaired | Nhận xét                                      |
| ------------------ | -------: | --------: | -------: | --------------------------------------------- |
| Retrieval Hit Rate |     1.00 |      1.00 |     1.00 | Document đúng vẫn nằm trong Top-4             |
| Mean Token F1      |     1.00 |      0.75 |     1.00 | Blank summary làm giảm chất lượng câu trả lời |
| Judge Accuracy     |     1.00 |      0.75 |     1.00 | Corruption ảnh hưởng factual answers          |
| Mean Judge Score   |     5.00 |      4.00 |     5.00 | Repair phục hồi hoàn toàn                     |
| Quality Checks     |     PASS |      FAIL |     PASS | Duplicate và missing summary bị phát hiện     |
| Freshness          |    FRESH |     STALE |    FRESH | Publish date bị làm cũ trong corruption       |

### Kết luận

Kết quả thực nghiệm cho thấy retrieval hit rate không phải là chỉ số duy nhất phản ánh chất lượng của hệ thống RAG. Trong kịch bản corruption, mặc dù document đúng vẫn được retrieve, việc mất nội dung summary khiến chất lượng câu trả lời giảm đáng kể, thể hiện qua Mean Token F1 và Judge Accuracy. Điều này chứng minh Data Quality có ảnh hưởng trực tiếp đến hiệu năng của Retrieval-Augmented Generation.

Repair được thực hiện từ raw snapshot thay vì chỉnh sửa trực tiếp dữ liệu corrupted giúp đảm bảo tính reproducible, khả năng audit và phục hồi hoàn toàn các quality checks, freshness cũng như toàn bộ evaluation metrics. Việc sử dụng cùng một frozen evaluation set trong cả ba trạng thái giúp các kết quả so sánh phản ánh đúng tác động của dữ liệu và pipeline, thay vì do thay đổi tập đánh giá.
