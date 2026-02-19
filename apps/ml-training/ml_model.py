from __future__ import annotations

from typing import Tuple
import pathlib
import joblib

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_pipeline(random_state: int = 0) -> Pipeline:
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

    # metrics
    for i, col in enumerate(y.columns):
        mse = mean_squared_error(y_test.iloc[:, i], y_pred[:, i])
        rmse = mse**0.5
        r2 = r2_score(y_test.iloc[:, i], y_pred[:, i])
        print(f"{col}: RMSE={rmse:.4f}, R2={r2:.4f}")

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


def load_model(path: str | pathlib.Path):
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return joblib.load(path)


def predict_text(model, text: str, tokens: int):
    import pandas as pd

    X = pd.DataFrame([{"input_text": text, "input_tokens": tokens}])
    pred = model.predict(X)
    return float(pred[0, 0]), float(pred[0, 1])
