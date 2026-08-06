# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                           |
| --------------- | ---------------------------------- |
| Họ và tên       | [Nguyễn Hoàng Anh]                        |
| MSSV            | [2A2202601186]                             |
| Khóa/Lớp        | [K4]                            |
| Tên nhóm        | [5AESieuNhan]                         |
| Vai trò chính   | Thành viên 4 – Corruption & Repair |
| Repository      | [NguyenHoangAnh-2A2202601186]                       |
| Ngày hoàn thành | [2026-08-06]                       |

---

# 2. Vai trò và phạm vi công việc

## Phần việc sở hữu

| Module/deliverable                 | File/hàm phụ trách                 | Input nhận vào                      | Output bàn giao        | Trạng thái |
| ---------------------------------- | ---------------------------------- | ----------------------------------- | ---------------------- | ---------- |
| Controlled Corruption              | `src/ingestion/corruption.py`      | `papers_clean.csv`                  | `papers_corrupted.csv` | Hoàn thành |
| Corruption Logging                 | `corruption.py`                    | Danh sách record bị thay đổi        | `corruption_log.json`  | Hoàn thành |
| Repair Pipeline                    | `src/pipelines/corruption_flow.py` | `crossref_records.json`             | Dữ liệu repaired       | Hoàn thành |
| Corrupted/Repaired Evaluation Flow | `corruption_flow.py`               | Corrupted dataset, repaired dataset | Báo cáo so sánh        | Hoàn thành |

Các phần việc tôi chịu trách nhiệm trực tiếp là tạo dữ liệu lỗi có kiểm soát, phục hồi dữ liệu từ nguồn raw và thực hiện pipeline đánh giá sau corruption và sau repair.

## Việc hỗ trợ ngoài phạm vi chính

| Hoạt động            | Thành viên/module được hỗ trợ | Kết quả                                                  |
| -------------------- | ----------------------------- | -------------------------------------------------------- |
| Kiểm tra integration | Retrieval Pipeline            | Đảm bảo index được rebuild đúng sau corruption và repair |
| Debug dữ liệu        | Cleaning Module               | Xác minh dữ liệu repaired giống dữ liệu clean ban đầu    |

---

# 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện         | File/hàm             | Kết quả bàn giao       | Cách xác minh                  |
| ----------------------------- | -------------------- | ---------------------- | ------------------------------ |
| Sinh dữ liệu lỗi có kiểm soát | `corruption.py`      | `papers_corrupted.csv` | So sánh số record trước và sau |
| Ghi log corruption            | `corruption.py`      | `corruption_log.json`  | Kiểm tra JSON log              |
| Repair dữ liệu                | `corruption_flow.py` | repaired dataset       | So sánh checksum hoặc schema   |
| Xuất báo cáo                  | `corruption_flow.py` | `corruption_report.md` | Kiểm tra report sinh tự động   |

Output chính mà tôi tạo ra là:

* `data/clean/papers_corrupted.csv`
* `data/results/corruption_log.json`
* `data/reports/corruption_report.md`

Các artifact này được sử dụng để đánh giá ảnh hưởng của corruption và hiệu quả của quá trình repair.

---

# 4. Giải thích phần kỹ thuật đã thực hiện

## Vấn đề cần giải quyết

Mục tiêu của phần việc là tạo ra các lỗi dữ liệu có kiểm soát để mô phỏng các tình huống thực tế trong data pipeline, sau đó phục hồi dữ liệu từ nguồn raw nhằm đánh giá khả năng phát hiện và sửa lỗi của hệ thống Data Observability.

## Cách triển khai

Tôi xây dựng module corruption theo hướng reproducible bằng cách áp dụng các quy tắc corruption cố định thay vì thay đổi ngẫu nhiên hoàn toàn.

Các kịch bản corruption gồm:

* Blank Summary: đặt trường `summary` của một số tài liệu thành chuỗi rỗng.
* Stale Date: thay đổi năm xuất bản của một số tài liệu thành năm 2000 để làm sai freshness.
* Add Noise: chèn chuỗi ký tự không liên quan vào `text_for_embedding`.
* Duplicates: tạo bản ghi trùng lặp với cùng document ID.

Các document bị chọn để corruption được ưu tiên nằm trong frozen test set để đảm bảo ảnh hưởng trực tiếp đến retrieval metrics.

Repair không sửa trực tiếp trên file corrupted mà đọc lại dữ liệu từ `crossref_records.json`, chạy lại toàn bộ cleaning pipeline để tái tạo dữ liệu sạch. Cách này giúp đảm bảo reproducibility và tránh tích lũy lỗi.

## Input, output và contract

| Thành phần              | Mô tả                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------- |
| Input                   | `papers_clean.csv`, `crossref_records.json`                                        |
| Output                  | `papers_corrupted.csv`, repaired dataset                                           |
| Module phụ thuộc        | Cleaning Pipeline                                                                  |
| Module sử dụng output   | Chroma Index, Evaluation Pipeline                                                  |
| Điều kiện lỗi cần xử lý | Missing summary, duplicate records, invalid publish year, corrupted embedding text |

## Cách xác minh

```bash
python src/pipelines/corruption_flow.py
```

**Kết quả mong đợi**

* Sinh file corrupted.
* Rebuild index thành công.
* Chạy evaluation cho corrupted.
* Repair dữ liệu.
* Rebuild index repaired.
* Xuất corruption report.

**Kết quả thực tế**

Pipeline chạy hoàn chỉnh và sinh đầy đủ các artifact theo yêu cầu.

**Artifact/log**

* `data/results/corruption_log.json`
* `data/reports/corruption_report.md`

---

# 5. Một quyết định kỹ thuật quan trọng

**Bối cảnh**

Cần lựa chọn cách repair dữ liệu sau khi corruption.

**Các phương án đã cân nhắc**

1. Sửa trực tiếp trên file corrupted.
2. Đọc lại dữ liệu raw và chạy lại cleaning pipeline.

**Phương án đã chọn**

Phương án 2.

**Lý do**

Repair từ raw giúp đảm bảo dữ liệu sau sửa giống hoàn toàn dữ liệu chuẩn, tránh bỏ sót lỗi phát sinh và bảo đảm tính reproducible của pipeline.

**Bằng chứng**

Sau repair, quality metrics và retrieval metrics phục hồi gần với baseline, đồng thời quality checks không còn báo lỗi.

---

# 6. Một lỗi hoặc blocker đã xử lý

**Triệu chứng**

Metrics gần như không thay đổi sau khi corruption.

**Lệnh tái hiện**

```bash
python src/pipelines/corruption_flow.py
```

**Nguyên nhân gốc**

Các document bị corruption không thuộc tập frozen evaluation nên retrieval không bị ảnh hưởng.

**Cách xử lý**

Ưu tiên corruption các document xuất hiện trong frozen test set.

**Cách xác minh**

Chạy lại evaluation sau khi thay đổi danh sách document bị corruption.

**Điều học được**

Data corruption chỉ có ý nghĩa khi tác động đến dữ liệu thực sự được sử dụng trong quá trình đánh giá.

---

# 7. Hiểu biết về luồng end-to-end

### 1.

Dữ liệu được lấy từ Crossref, lưu thành raw records, sau đó cleaning để chuẩn hóa metadata và tạo `text_for_embedding`. Dữ liệu sạch được index vào ChromaDB. Khi người dùng đặt câu hỏi, embedding của câu hỏi được dùng để truy vấn vector index và trả về các tài liệu liên quan.

### 2.

Evaluation set chứa tập câu hỏi cố định. Ground-truth document IDs xác định tài liệu đúng cho từng câu hỏi. Retrieval được đánh giá bằng khả năng lấy đúng document, còn answer quality được đánh giá dựa trên câu trả lời sinh ra từ các document được truy xuất.

### 3.

Quality checks kiểm tra tính đúng đắn của dữ liệu như missing field, duplicate hoặc invalid value. Freshness monitoring chỉ tập trung vào độ mới của dữ liệu dựa trên publish date.

### 4.

Sử dụng cùng một test set giúp đảm bảo mọi thay đổi của metrics chỉ đến từ dữ liệu, không phải do thay đổi bộ câu hỏi.

### 5.

Repair được xem là thành công khi quality checks được phục hồi, freshness trở lại bình thường và các retrieval metrics sau repair tiến gần baseline.

---

# 8. Phân tích kết quả

## Metrics chính

| Metric             | Baseline | Corrupted | Repaired | Nhận xét                                                     |
| ------------------ | -------: | --------: | -------: | ------------------------------------------------------------ |
| retrieval_hit_rate |      [ ] |       [ ] |      [ ] | Corruption làm giảm khả năng retrieval, repair giúp phục hồi |
| mean_token_f1      |      [ ] |       [ ] |      [ ] | Chất lượng câu trả lời giảm khi retrieval sai                |
| judge_accuracy     |      [ ] |       [ ] |      [ ] | Phục hồi gần baseline sau repair                             |
| mean_judge_score   |      [ ] |       [ ] |      [ ] | Xu hướng tương tự retrieval                                  |
| Quality checks     |      [ ] |       [ ] |      [ ] | Corruption sinh lỗi, repair loại bỏ lỗi                      |
| Freshness status   |      [ ] |       [ ] |      [ ] | Stale Date ảnh hưởng trực tiếp freshness                     |

## Kết luận từ số liệu

Data corruption → Quality/Freshness giảm → Retrieval hit rate và answer quality giảm.

Repair từ raw → Quality checks phục hồi → Retrieval metrics và answer quality phục hồi gần baseline.

Corruption ảnh hưởng mạnh nhất là Blank Summary và Add Noise vì chúng làm giảm chất lượng embedding, khiến hệ thống truy xuất sai tài liệu.

Kết quả khác với kỳ vọng là Duplicate Records không làm giảm metrics nhiều như dự đoán vì vector search vẫn có thể truy xuất đúng tài liệu mặc dù tồn tại bản ghi trùng.

---

# 9. Điều học được và hướng cải thiện

## Ba điều quan trọng nhất

1. Data pipeline cần có khả năng tái tạo dữ liệu từ nguồn raw để đảm bảo reproducibility.
2. Data observability cần theo dõi đồng thời quality và freshness thay vì chỉ kiểm tra schema.
3. Hiệu năng của RAG phụ thuộc trực tiếp vào chất lượng dữ liệu được index.

## Nếu có thêm thời gian

Tôi muốn bổ sung nhiều loại corruption hơn như sai author, sai DOI hoặc embedding corruption để đánh giá mức độ ảnh hưởng của từng loại lỗi đối với retrieval và answer quality.

---

# 10. Cam kết của thành viên

* [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
* [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
* [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
* [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
* [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
* [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Nguyễn Hoàng Anh]

**Ngày xác nhận:** [2026-08-06]
