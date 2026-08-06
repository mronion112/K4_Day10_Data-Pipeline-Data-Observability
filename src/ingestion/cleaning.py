from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """TODO(student): clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    if not records:
        return pd.DataFrame()

    # Chuyen list PaperRecord -> list dict de tao DataFrame
    rows = []
    for r in records:
        rows.append(
            {
                "paper_id": r.paper_id,
                "title": r.title,
                "summary": r.summary,
                "authors": r.authors,
                "categories": r.categories,
                "primary_category": r.primary_category,
                "published": r.published,
                "updated": r.updated,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
            }
        )
    df = pd.DataFrame(rows)

    # Loc bo cac dong khong co title (khong the su dung)
    df = df[df["title"].str.strip() != ""].copy()

    # Chuan hoa title: xoa khoang trang thua
    df["title"] = df["title"].str.strip()

    # Chuan hoa summary: xoa khoang trang thua, thay NaN bang ""
    df["summary"] = df["summary"].fillna("").str.strip()

    # Chuan hoa primary_category
    df["primary_category"] = df["primary_category"].fillna("").str.strip()

    # Parse ngay published thanh datetime (chuyen ve UTC de dong bo voi run_date)
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["updated_dt"] = pd.to_datetime(df["updated"], errors="coerce", utc=True)

    # Tinh tuoi cua paper (so ngay tu khi publish den run_date)
    df["age_days"] = (run_date - df["published_dt"]).dt.days
    # Neu khong parse duoc ngay, dat age_days = 9999 (rat cu)
    df["age_days"] = df["age_days"].fillna(9999).astype(int)

    # Cot helper: gop authors thanh chuoi "author1, author2, ..."
    df["authors_joined"] = df["authors"].apply(
        lambda lst: ", ".join(lst) if isinstance(lst, list) else ""
    )

    # Cot helper: gop categories thanh chuoi "cat1, cat2, ..."
    df["categories_joined"] = df["categories"].apply(
        lambda lst: ", ".join(lst) if isinstance(lst, list) else ""
    )

    # Cot helper: do dai summary (so ky tu)
    df["summary_chars"] = df["summary"].str.len()

    # Cot chinh cho embedding: gop title + summary + authors + categories
    # Day la text duoc dua vao vector de search
    df["text_for_embedding"] = (
        "Title: " + df["title"]
        + "\nSummary: " + df["summary"]
        + "\nAuthors: " + df["authors_joined"]
        + "\nCategories: " + df["categories_joined"]
    )

    # Drop duplicates theo paper_id, giu ban ghi dau tien
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Loc bo cac dong co summary qua ngan (< 10 ky tu tru khi la paper khong abstract)
    # Giữ lại dòng có summary_chars >= 10 hoặc ít nhất title khác rỗng
    df = df[df["summary_chars"] >= 10]

    # Sap xep theo ngay published moi nhat truoc
    df = df.sort_values("published_dt", ascending=False, na_position="last")

    # Reset index sau khi filter/sort
    df = df.reset_index(drop=True)

    return df
