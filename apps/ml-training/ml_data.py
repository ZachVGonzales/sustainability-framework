from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from schemas import InferenceRecord


REQUIRED_COLUMNS = [
    "example_id",
    "input_text",
    "input_tokens",
    "output_text",
    "output_tokens",
    "new_tokens",
    "inference_time_s",
    "tokens_per_second",
    "gpu_num_samples",
    "gpu_duration_ms",
    "gpu_power_avg_w",
    "gpu_power_max_w",
    "gpu_power_min_w",
    "gpu_memory_avg_mib",
    "gpu_memory_max_mib",
    "gpu_gpu_util_avg",
    "gpu_gpu_util_max",
    "gpu_temp_avg_c",
    "gpu_temp_max_c",
    "gpu_energy_j",
]


def load_data(path: str | Path) -> pd.DataFrame:
    """Load parquet file and validate required columns."""
    df = pd.read_parquet(path)

    # normalize older column name
    if "gpu_energy" in df.columns and "gpu_energy_j" not in df.columns:
        df = df.rename(columns={"gpu_energy": "gpu_energy_j"})

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns in dataset: {missing}")

    # drop rows with entirely missing identifiers; these cannot be processed
    # downstream and often indicate failed data collection.  ``example_id`` is
    # the minimal key we require.
    if df["example_id"].isna().any():
        import warnings

        count = int(df["example_id"].isna().sum())
        warnings.warn(f"Dropping {count} rows with missing example_id")
        df = df.dropna(subset=["example_id"])

    return df


def estimate_tokens(text: str) -> int:
    """Estimate tokens using the empirical tokens-per-word ratio derived from
    the training dataset (~5.4 tokens/word).  The training data was generated
    with a tokenizer that produces roughly 5× more tokens than raw word count
    (system-prompt overhead, sub-word splits, special tokens, etc.), so raw
    word count wildly undershoots and causes the model to predict a constant
    value for all short inputs.
    """
    TOKENS_PER_WORD = 5.4  # empirical mean from merged.parquet (172 / 40.8)
    return max(1, round(len(text.split()) * TOKENS_PER_WORD))


def df_to_records(df: pd.DataFrame) -> List[InferenceRecord]:
    """Convert a DataFrame row-wise into typed InferenceRecord instances.

    The original implementation attempted to cast every field directly, which
    would raise a ``ValueError`` when a column value was ``NaN``.  In the
    dataset shipped with the notebook there were a few rows where
    ``example_id`` (and other numeric columns) were missing, so the cast to
    ``int`` failed with "cannot convert float NaN to integer".  Instead of
    blowing up we now coerce values safely and drop rows that do not contain a
    usable ``example_id`` because that's a primary key for downstream
    processing.
    """

    def _safe(val, cast, default):
        # pandas represents missing values as ``float('nan')``; ``pd.isna``
        # catches ``None`` as well.  We avoid importing pandas here to keep the
        # helper simple.
        try:
            if val is None:
                raise ValueError
            # ``val == val`` is False for NaN
            if val != val:
                raise ValueError
            return cast(val)
        except Exception:  # noqa: BLE001 - we want to catch anything
            return default

    # drop rows that lack a reliable example_id; nothing sensible can be done
    # with them so it's easier to just skip them entirely and warn the caller.
    df = df.dropna(subset=["example_id"])

    rows: List[InferenceRecord] = []
    for r in df.to_dict(orient="records"):
        rows.append(
            InferenceRecord(
                example_id=_safe(r.get("example_id"), int, 0),
                input_text=str(r.get("input_text", "")) or "",
                input_tokens=_safe(r.get("input_tokens"), int, 0),
                output_text=str(r.get("output_text", "")) or "",
                output_tokens=_safe(r.get("output_tokens"), int, 0),
                new_tokens=_safe(r.get("new_tokens"), int, 0),
                inference_time_s=_safe(r.get("inference_time_s"), float, 0.0),
                tokens_per_second=_safe(r.get("tokens_per_second"), float, 0.0),
                gpu_num_samples=_safe(r.get("gpu_num_samples"), int, 0),
                gpu_duration_ms=_safe(r.get("gpu_duration_ms"), int, 0),
                gpu_power_avg_w=_safe(r.get("gpu_power_avg_w"), float, 0.0),
                gpu_power_max_w=_safe(r.get("gpu_power_max_w"), float, 0.0),
                gpu_power_min_w=_safe(r.get("gpu_power_min_w"), float, 0.0),
                gpu_memory_avg_mib=_safe(r.get("gpu_memory_avg_mib"), float, 0.0),
                gpu_memory_max_mib=_safe(r.get("gpu_memory_max_mib"), int, 0),
                gpu_gpu_util_avg=_safe(r.get("gpu_gpu_util_avg"), float, 0.0),
                gpu_gpu_util_max=_safe(r.get("gpu_gpu_util_max"), int, 0),
                gpu_temp_avg_c=_safe(r.get("gpu_temp_avg_c"), float, 0.0),
                gpu_temp_max_c=_safe(r.get("gpu_temp_max_c"), int, 0),
                gpu_energy_j=_safe(r.get("gpu_energy_j"), float, 0.0),
            )
        )
    return rows
