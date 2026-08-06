from __future__ import annotations

import re
from html import unescape
from datetime import datetime

import pandas as pd

# Import dataclass PaperRecord từ module ingestion của Thành viên 1
from ingestion.crossref import PaperRecord

# Regex nhận diện các thẻ HTML/XML (ví dụ: <p>, <i>, <jats:p>) để loại bỏ khỏi văn bản
CLEAN_TEXT_REGEX = re.compile(r"<[^>]+>", flags=re.IGNORECASE)


def _clean_text(value: object) -> str:
    """
    Hàm nội bộ: Làm sạch một trường văn bản (Title hoặc Summary).
    Loại bỏ các thẻ HTML và khoảng trắng thừa.
    """
    # 1. Trả về chuỗi rỗng nếu giá trị đầu vào là None
    if value is None or pd.isna(value):
        return ""

    # 2. Ép kiểu về string, dùng Regex xóa sạch các thẻ HTML, sau đó dùng .strip() xóa khoảng trắng 2 đầu
    without_tags = re.sub(CLEAN_TEXT_REGEX, " ", str(value))
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _join_list_field(value: object) -> str:
    """
    Hàm nội bộ: Chuyển đổi một danh sách (list) thành một chuỗi duy nhất,
    các phần tử phân cách bằng dấu phẩy.
    """
    # 1. Nếu giá trị là danh sách (ví dụ danh sách tác giả hay danh mục)
    if isinstance(value, list):
        # Lọc bỏ phần tử None/rỗng, xóa khoảng trắng thừa từng phần tử rồi nối lại bằng phẩy và khoảng trắng ", "
        return ", ".join(str(item).strip() for item in value if item is not None and str(item).strip())

    # 2. Nếu không phải list thì chỉ ép kiểu về string và xóa khoảng trắng 2 đầu
    return str(value).strip()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """
    Hàm chính: Chuyển đổi danh sách PaperRecord thô thành một Pandas DataFrame
    được làm sạch hoàn chỉnh, bổ sung các trường tính toán và sẵn sàng cho Embedding/RAG.
    """
    # Bước 1: Chuyển đổi danh sách dataclass PaperRecord thành Pandas DataFrame
    df = pd.DataFrame([record.__dict__ for record in records])

    # Kiểm tra nếu DataFrame rỗng thì trả về ngay DataFrame rỗng để tránh lỗi phía sau
    if df.empty:
        return pd.DataFrame()

    # Bước 2: Làm sạch văn bản cho tiêu đề (title) và tóm tắt (summary) bằng cách xóa thẻ HTML
    df["title"] = df["title"].apply(_clean_text)
    df["summary"] = df["summary"].apply(_clean_text)

    # Bước 3: Lọc bỏ các bản ghi bị thiếu tiêu đề hoặc thiếu tóm tắt (chuỗi rỗng)
    df = df[df["title"].astype(bool) & df["summary"].astype(bool)].copy()

    # Bước 4: Kiểm soát chất lượng dữ liệu - Bỏ các bài báo có tóm tắt quá ngắn (< 100 ký tự)
    # Vì tóm tắt quá ngắn không đủ ngữ cảnh có giá trị cho mô hình RAG / Vector DB
    df = df[df["summary"].str.len() >= 100].copy()

    # Bước 5: Chuyển các trường dạng list ([tác giả 1, tác giả 2]) thành chuỗi duy nhất ("tác giả 1, tác giả 2")
    df["authors_joined"] = df["authors"].apply(_join_list_field)
    df["categories_joined"] = df["categories"].apply(_join_list_field)
    df["summary_chars"] = df["summary"].str.len()

    # Bước 6: Xử lý định dạng ngày xuất bản (published)
    # Chuyển chuỗi ngày thành kiểu dữ liệu datetime của Pandas, các ngày lỗi/không hợp lệ sẽ thành NaT (Not a Time)
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce")

    # Lọc bỏ các dòng có ngày xuất bản không hợp lệ (NaT)
    df = df[df["published_dt"].notna()].copy()

    # Chuẩn hóa lại cột published về định dạng chuỗi chuẩn 'YYYY-MM-DD'
    df["published"] = df["published_dt"].dt.strftime("%Y-%m-%d")

    # Bước 7: Tính toán độ tuổi bài báo (`age_days`) phục vụ cho Data Observability / Freshness check
    # Chuẩn hóa ngày chạy hệ thống (run_date) về định dạng không có múi giờ (timezone-naive)
    normalized_run_date = pd.Timestamp(run_date).tz_localize(None).normalize()
    df["published_dt"] = df["published_dt"].dt.tz_localize(None)

    # Số ngày tuổi = (Ngày chạy pipeline - Ngày xuất bản bài báo)
    df["age_days"] = (normalized_run_date - df["published_dt"]).dt.days

    # Bước 8: Tạo trường dữ liệu tổng hợp `text_for_embedding`
    # Đây là chuỗi văn bản hoàn chỉnh sẽ được đưa vào Vector Database (ChromaDB) để phục vụ việc truy vấn RAG
    df["text_for_embedding"] = (
        "Title: " + df["title"] +
        " | Authors: " + df["authors_joined"] +
        " | Summary: " + df["summary"]
    )

    # Bước 9: Dọn dẹp DataFrame trước khi xuất ra
    # Xóa cột trung gian published_dt
    df.drop(columns=["published_dt"], inplace=True)

    # Lọc trùng lặp bài báo dựa trên ID (mã DOI), giữ lại bản ghi đầu tiên xuất hiện
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Sắp xếp các bài báo theo ngày xuất bản mới nhất lên đầu và đánh lại chỉ số dòng (index)
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)

    # Trả về DataFrame đã được làm sạch hoàn toàn
    return df
