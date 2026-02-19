"""Load trained model and predict `output_tokens` and `gpu_energy_j` from user input text.

Usage (interactive):
  python apps/ml-training/predict.py
  (then paste/type a text line at the prompt)

Usage (non-interactive):
  echo "What is the work done...?" | python apps/ml-training/predict.py

The script auto-estimates `input_tokens` by splitting on whitespace; you can modify
`estimate_tokens()` if you need a different tokenizer.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict

import joblib
import pandas as pd

MODEL_PATH = pathlib.Path("apps/ml-training/model.joblib")


def estimate_tokens(text: str) -> int:
    """Very small token estimator (whitespace-based)."""
    return max(1, len(text.split()))


def load_model(path: pathlib.Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Trained model not found at {path}. Run the trainer first."
        )
    return joblib.load(path)


def predict_for_text(model, text: str) -> Dict[str, float]:
    tokens = estimate_tokens(text)
    X = pd.DataFrame([{"input_text": text, "input_tokens": tokens}])
    pred = model.predict(X)
    # model predicts [output_tokens, gpu_energy_j]
    return {
        "input_text": text,
        "input_tokens": int(tokens),
        "pred_output_tokens": float(pred[0, 0]),
        "pred_gpu_energy_j": float(pred[0, 1]),
    }


def main():
    model = load_model(MODEL_PATH)

    # read a single line from stdin / input()
    try:
        # prefer interactive prompt when stdout is a TTY
        if sys.stdin.isatty():
            text = input("Enter input text: ")
        else:
            text = sys.stdin.read().strip() or input("Enter input text: ")
    except (EOFError, KeyboardInterrupt):
        print("No input received; exiting.")
        return

    if not text.strip():
        print("Empty input; nothing to predict.")
        return

    out = predict_for_text(model, text)

    # print human-readable and JSON results
    print("\nPredicted results:")
    print(f"  input_tokens: {out['input_tokens']}")
    print(f"  pred_output_tokens: {out['pred_output_tokens']:.2f}")
    print(f"  pred_gpu_energy_j: {out['pred_gpu_energy_j']:.2f}")

    # also print JSON for downstream parsing
    print("\nJSON:")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
