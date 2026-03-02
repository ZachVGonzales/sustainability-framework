#!/usr/bin/env python3
"""Combine all parquet files from a source directory into a single parquet file.

Example usage:

    python merge_parquets.py \
        --src ../ml-training/assets \
        --dst ../../assets/combined.parquet

By default the script looks in the ``apps/ml-training/assets`` folder and
writes ``assets/merged.parquet`` in the repository root.  Adjust the paths
to suit your project layout.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def merge_parquets(source_dir: Path, dest_path: Path) -> None:
    """Read every ``*.parquet`` file from *source_dir* and concatenate them.

    The result is written to *dest_path*, creating parent directories if
    necessary.
    """

    source_dir = source_dir.expanduser().resolve()
    dest_path = dest_path.expanduser().resolve()

    if not source_dir.is_dir():
        raise FileNotFoundError(f"source directory does not exist: {source_dir}")

    parquet_files = sorted(source_dir.glob("*.parquet"))
    if not parquet_files:
        raise ValueError(f"no parquet files found under {source_dir}")

    dfs = []
    total_rows = 0
    for p in parquet_files:
        df = pd.read_parquet(p)
        total_rows += len(df)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(dest_path)

    print(f"wrote {total_rows} rows from {len(parquet_files)} files to {dest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge parquet shards into a single file."
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(__file__).parent.parent / "ml-training" / "assets",
        help="directory containing parquet files to merge",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=Path.cwd() / "assets" / "merged.parquet",
        help="destination path for the combined parquet",
    )

    args = parser.parse_args()
    merge_parquets(args.src, args.dst)
