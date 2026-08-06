from __future__ import annotations

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Create deterministic, auditable corruption that overlaps frozen test records."""
    if len(df) < 3:
        raise ValueError("At least three rows are required for meaningful corruption.")
    corrupted = df.copy().reset_index(drop=True)
    target_indices = list(range(min(3, len(corrupted))))
    events: list[dict] = []
    for index in target_indices:
        events.append({"scenario": "blank_summary", "paper_id": corrupted.at[index, "paper_id"]})
        corrupted.at[index, "summary"] = ""
        corrupted.at[index, "summary_chars"] = 0
        corrupted.at[index, "text_for_embedding"] = "[CORRUPTED RECORD: content unavailable]"

    stale_index = target_indices[-1]
    corrupted.at[stale_index, "published"] = "2000-01-01"
    corrupted.at[stale_index, "age_days"] = 9_999
    events.append({"scenario": "stale_date", "paper_id": corrupted.at[stale_index, "paper_id"], "published": "2000-01-01"})
    noise_index = target_indices[0]
    corrupted.at[noise_index, "text_for_embedding"] += " ### @@ irrelevant corrupted noise 0000 ###"
    events.append({"scenario": "embedding_noise", "paper_id": corrupted.at[noise_index, "paper_id"]})
    duplicate = corrupted.iloc[[target_indices[1]]].copy()
    corrupted = pd.concat([corrupted, duplicate], ignore_index=True)
    events.append({"scenario": "duplicate_paper_id", "paper_id": duplicate.iloc[0]["paper_id"]})
    write_json(output_log_path, {"original_rows": len(df), "corrupted_rows": len(corrupted), "events": events})
    return corrupted
