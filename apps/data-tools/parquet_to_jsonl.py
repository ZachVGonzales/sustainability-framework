import re
import json
from pathlib import Path

import pandas as pd

ANALYSIS_PREFIX = re.compile(r"^\s*analysis\s*", re.IGNORECASE)


def clean_output(text: str) -> str:
    if text is None:
        return ""
    # If your generator stuck "analysis" onto the front, remove it.
    return ANALYSIS_PREFIX.sub("", str(text)).strip()


def parquet_to_utility_jsonl(
    parquet_paths,
    out_jsonl_path,
    *,
    input_col="input_text",
    output_col="output_text",
    id_col="example_id",
    keep_metrics=True,
):
    rows_written = 0
    out_jsonl_path = Path(out_jsonl_path)
    out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    with out_jsonl_path.open("w", encoding="utf-8") as f:
        for p in parquet_paths:
            df = pd.read_parquet(p)

            required = {input_col, output_col}
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"{p}: missing required columns: {sorted(missing)}")

            for idx, r in df.iterrows():
                ex_id = r[id_col] if id_col in df.columns else idx

                record = {
                    "example_id": int(ex_id) if str(ex_id).isdigit() else str(ex_id),
                    # Common “utility tracker” style fields:
                    "prompt": str(r[input_col]),
                    "response": clean_output(r[output_col]),
                }

                if keep_metrics:
                    # Keep everything else as metadata (optional)
                    meta = {}
                    for c in df.columns:
                        if c in {input_col, output_col, id_col}:
                            continue
                        v = r[c]
                        # Convert numpy/pandas scalars to plain python types
                        if hasattr(v, "item"):
                            v = v.item()
                        meta[c] = v
                    record["metadata"] = meta

                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows_written += 1

    return rows_written


# Example usage:
# count = parquet_to_utility_jsonl(
#     parquet_paths=["/path/to/shard1.parquet", "/path/to/shard2.parquet"],
#     out_jsonl_path="/path/to/utility_dataset.jsonl",
# )
# print("Wrote", count, "examples")

if __name__ == "__main__":
    file = "assets/merged.parquet"
    out = "assets/utility_dataset.jsonl"

    count = parquet_to_utility_jsonl(
        parquet_paths=[file],
        out_jsonl_path=out,
    )
