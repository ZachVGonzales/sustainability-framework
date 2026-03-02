"""Simple training script for predicting `output_tokens` and `gpu_energy_j`
from the dataset produced in `datagen_output.parquet`.

Usage (from repo root):
  python apps/ml-training/train_model.py --data-path apps/ml-training/datagen_output.parquet

Produces a trained model file (`apps/ml-training/models/model.joblib`) and prints
train/test metrics.
"""

from __future__ import annotations

import argparse
import pathlib
from typing import Tuple

import pandas as pd

from ml_data import load_data
from ml_model import train_and_evaluate, save_model


# Core training logic has been refactored into `ml_data.py` and `ml_model.py`.
# This script is now a thin CLI wrapper that delegates to those modules.


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-path", default="apps/ml-training/merged.parquet")
    p.add_argument("--model-out", default="apps/ml-training/models/model.joblib")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--random-state", type=int, default=0)
    return p.parse_args()


def main():
    args = parse_args()
    df = load_data(args.data_path)
    pipe, sample_df = train_and_evaluate(
        df, test_size=args.test_size, random_state=args.random_state
    )
    save_model(pipe, args.model_out)
    print("\nExample predictions (first 5 rows):")
    print(
        sample_df[
            ["input_text", "input_tokens", "pred_output_tokens", "pred_gpu_energy_j"]
        ].head()
    )


if __name__ == "__main__":
    main()
