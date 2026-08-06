from __future__ import annotations

import random

import numpy as np
import pandas as pd

from core.utils import ensure_parent, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """TODO(student): simulate nhieu dang data corruption.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    df_corrupted = df.copy()
    log: list[dict] = []
    rng = np.random.RandomState(42)
    total = len(df_corrupted)

    # --- 1. Drop mot so latest records (xoa ~15% paper moi nhat) ---
    drop_count = max(1, int(total * 0.15))
    drop_indices = df_corrupted.head(drop_count).index
    df_corrupted = df_corrupted.drop(drop_indices)
    log.append({
        "action": "drop_latest_records",
        "count": len(drop_indices),
        "paper_ids": df.loc[drop_indices, "paper_id"].tolist(),
    })

    # --- 2. Blank summary o mot so dong (~20% so dong con lai) ---
    remaining = df_corrupted.index
    blank_count = max(1, int(len(remaining) * 0.2))
    blank_indices = rng.choice(remaining, size=blank_count, replace=False)
    df_corrupted.loc[blank_indices, "summary"] = ""
    df_corrupted.loc[blank_indices, "summary_chars"] = 0
    log.append({
        "action": "blank_summary",
        "count": len(blank_indices),
        "paper_ids": df_corrupted.loc[blank_indices, "paper_id"].tolist(),
    })

    # --- 3. Inject noise vao summary (~25% so dong) ---
    noise_indices = rng.choice(remaining, size=max(1, int(len(remaining) * 0.25)), replace=False)
    noise_texts = [
        "asdfghjkl qwertyuiop zxcvbnm 1234567890",
        "lorem ipsum dolor sit amet consectetur adipiscing elit",
        "BUY NOW!!! CLICK HERE!!! LIMITED OFFER!!! $$$",
        "data data data data data data data data data data",
    ]
    for idx in noise_indices:
        orig = df_corrupted.loc[idx, "summary"]
        noise = noise_texts[rng.randint(0, len(noise_texts))]
        df_corrupted.loc[idx, "summary"] = str(orig) + " [NOISE] " + noise
        df_corrupted.loc[idx, "summary_chars"] = len(df_corrupted.loc[idx, "summary"])
    log.append({
        "action": "inject_noise",
        "count": len(noise_indices),
        "paper_ids": df_corrupted.loc[noise_indices, "paper_id"].tolist(),
    })

    # --- 4. Lam title bi truncate (~15% so dong) ---
    trunc_indices = rng.choice(remaining, size=max(1, int(len(remaining) * 0.15)), replace=False)
    for idx in trunc_indices:
        orig_title = str(df_corrupted.loc[idx, "title"])
        if len(orig_title) > 10:
            df_corrupted.loc[idx, "title"] = orig_title[:len(orig_title)//2] + "..."
    log.append({
        "action": "truncate_title",
        "count": len(trunc_indices),
        "paper_ids": df_corrupted.loc[trunc_indices, "paper_id"].tolist(),
    })

    # --- 5. Lam published date cu di (~15% so dong lui lai 5 nam) ---
    stale_indices = rng.choice(remaining, size=max(1, int(len(remaining) * 0.15)), replace=False)
    for idx in stale_indices:
        if pd.notna(df_corrupted.loc[idx, "published_dt"]):
            old_date = df_corrupted.loc[idx, "published_dt"] - pd.DateOffset(years=5)
            df_corrupted.loc[idx, "published_dt"] = old_date
            df_corrupted.loc[idx, "published"] = old_date.strftime("%Y-%m-%d")
            # Cap nhat age_days
            df_corrupted.loc[idx, "age_days"] = (
                pd.Timestamp.now(tz="UTC") - old_date
            ).days
    log.append({
        "action": "stale_date",
        "count": len(stale_indices),
        "paper_ids": df_corrupted.loc[stale_indices, "paper_id"].tolist(),
    })

    # --- 6. Add duplicate rows (~10% so dong, clone va them vao) ---
    dup_count = max(1, int(len(remaining) * 0.1))
    dup_indices = rng.choice(remaining, size=dup_count, replace=False)
    duplicates = df_corrupted.loc[dup_indices].copy()
    df_corrupted = pd.concat([df_corrupted, duplicates], ignore_index=True)
    log.append({
        "action": "add_duplicates",
        "count": len(dup_indices),
        "paper_ids": df_corrupted.loc[df_corrupted.index[-len(dup_indices):], "paper_id"].tolist(),
    })

    # --- 7. Rebuild text_for_embedding cho cac dong bi thay doi ---
    df_corrupted["text_for_embedding"] = (
        "Title: " + df_corrupted["title"].fillna("")
        + "\nSummary: " + df_corrupted["summary"].fillna("")
        + "\nAuthors: " + df_corrupted["authors_joined"].fillna("")
        + "\nCategories: " + df_corrupted["categories_joined"].fillna("")
    )

    # --- 8. Ghi corruption log ---
    summary = {
        "original_rows": total,
        "corrupted_rows": len(df_corrupted),
        "actions": log,
    }
    ensure_parent(output_log_path)
    write_json(output_log_path, summary)

    return df_corrupted
