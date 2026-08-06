from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import ensure_parent, first_sentence

logger = logging.getLogger(__name__)


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Tạo bộ câu hỏi đánh giá (evaluation set) từ DataFrame đã làm sạch."""
    if len(df) < 5:
        raise ValueError("Cần ít nhất 5 bài báo trong dữ liệu sạch để tạo bộ test.")
    required_columns = {"paper_id", "title", "authors_joined", "published", "summary"}
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Dữ liệu sạch thiếu các cột bắt buộc: {', '.join(missing_columns)}")

    # Lấy mẫu 5 bài báo để tạo câu hỏi
    sample_df = df.sample(n=min(5, len(df)), random_state=42)
    test_set = []
    question_id_counter = 1

    for _, row in sample_df.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]

        # Câu hỏi về tác giả
        test_set.append({
            "id": f"q{question_id_counter}",
            "question_type": "authors",
            "question": f"Who are the authors of the paper titled '{title}'?",
            "ground_truth": row["authors_joined"],
            "ground_truth_doc_ids": [paper_id],
        })
        question_id_counter += 1

        # Câu hỏi về ngày xuất bản
        test_set.append({
            "id": f"q{question_id_counter}",
            "question_type": "published_date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": row["published"],
            "ground_truth_doc_ids": [paper_id],
        })
        question_id_counter += 1

        # Câu hỏi về tóm tắt
        test_set.append({
            "id": f"q{question_id_counter}",
            "question_type": "summary",
            "question": f"What is the main topic of the paper titled '{title}'?",
            "ground_truth": first_sentence(row["summary"]),
            "ground_truth_doc_ids": [paper_id],
        })
        question_id_counter += 1

    # Lưu bộ câu hỏi vào file JSON
    ensure_parent(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)

    logger.info(f"Đã tạo và lưu {len(test_set)} câu hỏi vào {output_path}")
    return test_set
