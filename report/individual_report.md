# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đào Kiều Thịnh Quang |
| MSSV | 2A202601014 |
| Khóa/Lớp | K4 |
| Vai trò | Thành viên 5 — Integration & Comparison |

## 2. Phạm vi công việc

Tôi phụ trách ghép các module đã có thành hai luồng chạy hoàn chỉnh và tạo bằng chứng so sánh ba trạng thái dữ liệu. Phần sở hữu là:

| Module/deliverable | File/hàm phụ trách | Input | Output |
| --- | --- | --- | --- |
| Baseline orchestration | `src/pipelines/phase1.py::main` | Crossref raw records hoặc API, cấu hình, test set | Clean data, Chroma index, baseline metrics, quality/freshness và baseline report |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py::main` | Baseline artifacts, frozen test set, raw-record snapshot | Corrupted/repaired data, metrics, quality reports và comparison report |
| Agent demo integration | `script/run_agent_demo.py` | Baseline index, frozen test set, OpenAI configuration | Ba câu trả lời từ LLM agent thật tại `data/results/agent_demo_answers.json` |

## 3. Cách tích hợp end-to-end

### Baseline pipeline

`phase1.py` tải settings, dùng raw snapshot nếu đã tồn tại hoặc gọi Crossref API nếu chưa có. Sau đó pipeline làm sạch records, lưu CSV/JSON, build ChromaDB index, tạo frozen evaluation set khi cần và chạy evaluator. Cuối cùng pipeline chạy quality checks, freshness monitoring và sinh `data/reports/phase1_report.md`.

Lệnh tái hiện:

```bash
uv run python script/run_phase1.py
```

### Corruption, repair và comparison

`corruption_flow.py` không tạo test set mới. Nó đọc chính frozen set từ `data/eval/test_set.json`, tạo corruption có kiểm soát, re-index và đánh giá corrupted state. Repair được thực hiện bằng cách làm sạch lại `data/raw/crossref_records.json`, thay vì vá trực tiếp dữ liệu lỗi. Dataset repaired tiếp tục được re-index, đánh giá trên cùng frozen set, rồi xuất comparison report.

```bash
uv run python script/run_corruption_flow.py
```

### Demo agent thật

Sau khi cấu hình `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-5.6-luna` và `OPENAI_API_KEY` trong `.env`, chạy:

```bash
uv run python script/run_agent_demo.py
```

Agent đã gọi semantic-search/lookup trên index cục bộ và trả lời đúng ngày xuất bản của bài JADE-Plus là **2026-07-13**. Artifact demo nằm tại `data/results/agent_demo_answers.json`.

## 4. Kết quả và bằng chứng

### Artifact đã tạo

| Artifact | Đường dẫn | Kết quả |
| --- | --- | --- |
| Raw response và parsed records | `data/raw/` | 24 records Crossref |
| Clean baseline data | `data/clean/papers_clean.csv` | 24 records sạch |
| Frozen evaluation set | `data/eval/test_set.json` | 12 câu hỏi factual |
| Baseline metrics | `data/results/baseline_metrics.json` | Đã tạo |
| Corruption log | `data/results/corruption_log.json` | 6 sự kiện corruption được ghi lại |
| Corrupted/repaired metrics | `data/results/*_metrics.json` | Đã tạo |
| Baseline/comparison reports | `data/reports/` | Đã tạo |

### So sánh ba trạng thái

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.00 | 1.00 | 1.00 | Top-4 retrieval vẫn chứa document đúng. |
| `mean_token_f1` | 1.00 | 0.75 | 1.00 | Summary rỗng làm giảm độ khớp câu trả lời 0.25. |
| `judge_accuracy` | 1.00 | 0.75 | 1.00 | Ba câu hỏi summary của document bị tác động không còn đúng. |
| `mean_judge_score` | 5.00 | 4.00 | 5.00 | Repair phục hồi hoàn toàn mức baseline. |
| Quality checks | PASS | FAIL | PASS | Corrupted có duplicate ID và 4 summary ngắn/rỗng. |
| Freshness | FRESH | STALE | FRESH | Corrupted có 1 record bị đổi ngày về `2000-01-01`. |

## 5. Phân tích nguyên nhân–kết quả

1. Ba documents thuộc frozen test set bị làm rỗng `summary`; đồng thời một bản duplicate được thêm vào và một ngày xuất bản bị làm cũ. Vì vậy quality report chuyển từ PASS sang FAIL, freshness chuyển từ FRESH sang STALE. Retrieval hit rate không giảm do document vẫn tồn tại trong top-k, nhưng thiếu nội dung khiến `mean_token_f1` và `judge_accuracy` giảm từ 1.00 xuống 0.75.
2. Repair bắt đầu từ raw-record snapshot tin cậy, chạy lại cleaning chuẩn và rebuild index. Điều này loại bỏ duplicate, khôi phục summary/date gốc và đưa quality/freshness về PASS/FRESH. `mean_token_f1`, `judge_accuracy` và `mean_judge_score` trở lại đúng baseline.

Việc giữ nguyên 12 câu hỏi và `ground_truth_doc_ids` cho cả ba lần chạy là điều kiện cần để khác biệt metric phản ánh trạng thái dữ liệu/index, không phải thay đổi bộ câu hỏi.

## 6. Quyết định kỹ thuật quan trọng

- **Vấn đề:** Repair dữ liệu lỗi bằng cách nào để kết quả có thể kiểm chứng?
- **Phương án không chọn:** Sửa trực tiếp `papers_clean_corrupted.csv`. Cách này có thể che lỗi, không đảm bảo phục hồi đúng giá trị nguồn và khó audit.
- **Phương án đã chọn:** Đọc lại `data/raw/crossref_records.json`, chạy `build_clean_dataframe`, sau đó rebuild index và đánh giá lại.
- **Lý do:** Raw artifact là snapshot có thể truy vết; cùng logic cleaning tạo output nhất quán và cho phép tái hiện repair.
- **Bằng chứng:** Repaired state có 24 rows, quality PASS, freshness FRESH và tất cả metrics quay lại mức baseline.

## 7. Lỗi tích hợp đã xử lý

- **Triệu chứng:** Demo OpenAI agent trả lỗi HTTP 400: GPT-5.6-luna không hỗ trợ function tools trên Chat Completions khi reasoning effort đang bật.
- **Nguyên nhân:** `LangChain` agent dùng function tools qua Chat Completions, trong khi model yêu cầu dùng Responses API hoặc đặt reasoning effort thành `none` cho route này.
- **Cách xử lý:** Trong `src/retrieval/llm.py`, cấu hình `reasoning_effort="none"` cho model bắt đầu bằng `gpt-5.6`. Đồng thời bổ sung `published`, authors và categories vào output của hai tool trong `src/retrieval/agent.py` để LLM có metadata chính xác.
- **Xác minh:** `uv run python script/run_agent_demo.py` chạy thành công, sinh artifact demo và trả lời ngày xuất bản chính xác.

## 8. Kết luận cá nhân

Phần integration chứng minh pipeline không chỉ chạy độc lập từng module mà còn tạo được chuỗi artifacts nhất quán: raw → clean → index → evaluate → observe → corrupt → repair → compare. Kết quả cho thấy retrieval hit rate một mình chưa đủ để kết luận chất lượng hệ thống: context bị mất vẫn làm câu trả lời factual giảm chất lượng dù document đúng còn được retrieve. Quality checks và frozen evaluation set giúp phát hiện, định lượng và xác minh sự phục hồi sau repair một cách tái hiện được.

## 9. Tự kiểm tra

- [x] Báo cáo chỉ mô tả phạm vi Integration & Comparison được phân công.
- [x] Các metric khớp với files trong `data/results/`.
- [x] Các kết luận quality/freshness khớp với files trong `data/quality/`.
- [x] Không chứa `.env`, API key hoặc secret.
