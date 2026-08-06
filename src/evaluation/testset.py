from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a deterministic frozen factual set grounded in the cleaned corpus."""
    required = {"paper_id", "title", "summary", "authors_joined", "published", "categories_joined"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Cannot build test set; missing columns: {sorted(missing)}")
    if len(df) < 2:
        raise ValueError("At least two clean documents are required to build the evaluation set.")

    samples: list[dict[str, Any]] = []
    selected = df.sort_values("paper_id", kind="stable").head(min(3, len(df)))
    for _, row in selected.iterrows():
        title, paper_id = str(row.title), str(row.paper_id)
        facts = [
            ("summary", f"What does the paper '{title}' describe?", first_sentence(str(row.summary))),
            ("authors", f"Who authored the paper '{title}'?", str(row.authors_joined)),
            ("date", f"When was the paper '{title}' published?", str(row.published)),
            ("categories", f"What categories does the paper '{title}' belong to?", str(row.categories_joined)),
        ]
        for question_type, question, truth in facts:
            samples.append({"id": f"q{len(samples) + 1:02d}", "question_type": question_type,
                            "question": question, "ground_truth": truth, "ground_truth_doc_ids": [paper_id]})
    write_json(output_path, samples)
    return samples
