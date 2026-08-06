from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import ensure_parent, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """TODO(student): tao bo evaluation set tu cleaned dataframe.

    Pseudo-code:
    1. Kiem tra so luong document toi thieu.
    2. Chon mot so paper dai dien.
    3. Tao nhieu loai cau hoi:
       - factual (single-hop specific): tac gia, ngay, linh vuc
       - abstract (single-hop abstract): y nghia, ung dung
       - comparison (multi-doc): so sanh 2 paper
       - multi-hop (multi-step): ket hop nhieu thong tin
    4. Moi row can co:
       - id
       - question_type
       - question
       - ground_truth
       - ground_truth_doc_ids
    5. Ghi file JSON vao output_path.
    """
    # Phai co it nhat 5 paper de tao test set
    min_docs = 5
    if len(df) < min_docs:
        raise RuntimeError(
            f"Can it nhat {min_docs} documents de tao test set, hien co {len(df)}."
        )

    # Chon toi da 10 paper dau tien lam mau, reset index de duyet de dang
    sample = df.head(min_docs + 5).reset_index(drop=True)

    test_set: list[dict[str, Any]] = []
    idx = 0

    for _, row in sample.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])

        # Bo qua paper thieu du lieu can thiet
        if not row.get("authors_joined") or not str(row["authors_joined"]).strip():
            continue

        # --- 1. factual: hoi truc tiep ve tac gia ---
        test_set.append({
            "id": f"q{idx + 1}",
            "question_type": "factual",
            "question": f"Tác giả của bài báo '{title}' là ai?",
            "ground_truth": str(row["authors_joined"]),
            "ground_truth_doc_ids": [paper_id],
        })
        idx += 1

        # --- 2. factual: hoi ve linh vuc ---
        if row.get("categories_joined") and str(row["categories_joined"]).strip():
            test_set.append({
                "id": f"q{idx + 1}",
                "question_type": "factual",
                "question": f"Bài báo '{title}' thuộc lĩnh vực nào?",
                "ground_truth": str(row["categories_joined"]),
                "ground_truth_doc_ids": [paper_id],
            })
            idx += 1

        # --- 3. abstract: hoi ve y nghia/ung dung cua nghien cuu ---
        if row.get("summary") and str(row["summary"]).strip():
            test_set.append({
                "id": f"q{idx + 1}",
                "question_type": "abstract",
                "question": f"Ý nghĩa và ứng dụng chính của nghiên cứu trong bài báo '{title}' là gì?",
                "ground_truth": str(row["summary"]),
                "ground_truth_doc_ids": [paper_id],
            })
            idx += 1

        # Gioi han moi paper 3 cau hoi, toi da ~15 cau
        if len(test_set) >= 15:
            break

    # --- 4. comparison: so sanh 2 paper (can it nhat 2 paper) ---
    if len(sample) >= 2:
        r1 = sample.iloc[0]
        r2 = sample.iloc[1]
        ground_truth = (
            f"Bài '{r1['title']}' tập trung vào: {str(r1['summary'])[:200]}. "
            f"Bài '{r2['title']}' tập trung vào: {str(r2['summary'])[:200]}."
        )
        test_set.append({
            "id": f"q{len(test_set) + 1}",
            "question_type": "comparison",
            "question": f"So sánh cách tiếp cận giữa bài báo '{r1['title']}' và '{r2['title']}'?",
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": [str(r1["paper_id"]), str(r2["paper_id"])],
        })

    # --- 5. multi-hop: ket hop nhieu thong tin tu cung 1 paper ---
    if len(sample) >= 1:
        r = sample.iloc[0]
        if r.get("authors_joined") and r.get("categories_joined"):
            ground_truth = (
                f"Tác giả: {str(r['authors_joined'])}. Lĩnh vực: {str(r['categories_joined'])}."
            )
            test_set.append({
                "id": f"q{len(test_set) + 1}",
                "question_type": "multi-hop",
                "question": (
                    f"Ai là tác giả của bài báo '{r['title']}' "
                    f"và nghiên cứu này thuộc lĩnh vực nào?"
                ),
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [str(r["paper_id"])],
            })

    # Ghi test set ra file JSON
    ensure_parent(output_path)
    write_json(output_path, test_set)

    return test_set
