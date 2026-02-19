"""Simple training script for predicting `output_tokens` and `gpu_energy_j`
from the dataset produced in `datagen_output.parquet`.

Usage (from repo root):
  python apps/ml-training/train_model.py --data-path apps/ml-training/datagen_output.parquet

Produces a trained model file (`apps/ml-training/model.joblib`) and prints
train/test metrics.
"""

from __future__ import annotations

import argparse
import pathlib
import joblib  # type: ignore
from typing import Tuple

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


TARGETS = ["output_tokens", "gpu_energy_j"]
REQUIRED_COLUMNS = ["input_text", "input_tokens"] + TARGETS


def load_data(path: str | pathlib.Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    # normalize possible column naming
    if "gpu_energy" in df.columns and "gpu_energy_j" not in df.columns:
        df = df.rename(columns={"gpu_energy": "gpu_energy_j"})
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns in dataset: {missing}")
    return df


def build_pipeline(random_state: int = 0) -> Pipeline:
    """Create a sklearn Pipeline that vectorizes text and scales numeric input
    then fits a multi-output RandomForestRegressor."""
    text_clf = TfidfVectorizer(
        max_features=2000, ngram_range=(1, 2), stop_words="english"
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", text_clf, "input_text"),
            ("num", StandardScaler(), ["input_tokens"]),
        ],
        remainder="drop",
    )

    model = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
    )

    pipe = Pipeline([("pre", preprocessor), ("reg", model)])
    return pipe


def train_and_evaluate(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 0
) -> Tuple[Pipeline, pd.DataFrame]:
    X = df[["input_text", "input_tokens"]]
    y = df[["output_tokens", "gpu_energy_j"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    pipe = build_pipeline(random_state=random_state)
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)

    # print metrics per target
    for i, col in enumerate(y.columns):
        mse = mean_squared_error(y_test.iloc[:, i], y_pred[:, i])
        rmse = mse**0.5
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        print(f"{col}: RMSE={rmse:.4f}, R2={r2:.4f}")

    # show a few sample predictions
    sample_df = X_test.reset_index(drop=True).copy()
    sample_df["actual_output_tokens"] = y_test.reset_index(drop=True)["output_tokens"]
    sample_df["pred_output_tokens"] = y_pred[:, 0]
    sample_df["actual_gpu_energy_j"] = y_test.reset_index(drop=True)["gpu_energy_j"]
    sample_df["pred_gpu_energy_j"] = y_pred[:, 1]

    return pipe, sample_df


def save_model(pipe: Pipeline, out_path: str | pathlib.Path) -> None:
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    print(f"Saved trained model to {out_path}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-path", default="apps/ml-training/datagen_output.parquet")
    p.add_argument("--model-out", default="apps/ml-training/model.joblib")
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
