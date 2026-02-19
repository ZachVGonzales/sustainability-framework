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
    return df


def estimate_tokens(text: str) -> int:
    """Simple token estimator used by CLI/notebook (whitespace-based).
    Replace with a tokenizer if you need exact token counts.
    """
    return max(1, len(text.split()))


def df_to_records(df: pd.DataFrame) -> List[InferenceRecord]:
    """Convert a DataFrame row-wise into typed InferenceRecord instances."""
    rows: List[InferenceRecord] = []
    for r in df.to_dict(orient="records"):
        rows.append(
            InferenceRecord(
                example_id=int(r.get("example_id")),
                input_text=str(r.get("input_text", "")),
                input_tokens=int(r.get("input_tokens", 0)),
                output_text=str(r.get("output_text", "")),
                output_tokens=int(r.get("output_tokens", 0)),
                new_tokens=int(r.get("new_tokens", 0)),
                inference_time_s=float(r.get("inference_time_s", 0.0)),
                tokens_per_second=float(r.get("tokens_per_second", 0.0)),
                gpu_num_samples=int(r.get("gpu_num_samples", 0)),
                gpu_duration_ms=int(r.get("gpu_duration_ms", 0)),
                gpu_power_avg_w=float(r.get("gpu_power_avg_w", 0.0)),
                gpu_power_max_w=float(r.get("gpu_power_max_w", 0.0)),
                gpu_power_min_w=float(r.get("gpu_power_min_w", 0.0)),
                gpu_memory_avg_mib=float(r.get("gpu_memory_avg_mib", 0.0)),
                gpu_memory_max_mib=int(r.get("gpu_memory_max_mib", 0)),
                gpu_gpu_util_avg=float(r.get("gpu_gpu_util_avg", 0.0)),
                gpu_gpu_util_max=int(r.get("gpu_gpu_util_max", 0)),
                gpu_temp_avg_c=float(r.get("gpu_temp_avg_c", 0.0)),
                gpu_temp_max_c=int(r.get("gpu_temp_max_c", 0)),
                gpu_energy_j=float(r.get("gpu_energy_j", 0.0)),
            )
        )
    return rows
