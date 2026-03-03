"""
Energy predictor – thin wrapper around the trained ML model in apps/ml-training/.

The model takes (input_text, input_tokens) and predicts (output_tokens, gpu_energy_j).
We only use gpu_energy_j (Joules of GPU energy consumed by the inference).

Model path is resolved relative to *this file*'s location so it works regardless
of the working directory the API is started from.

Environment variable MODEL_PATH can override the default location.
"""
from __future__ import annotations

import os
import pathlib
import sys
import logging

logger = logging.getLogger(__name__)

# ── Resolve model & ml-training source paths ─────────────────────────────────

_HERE = pathlib.Path(__file__).parent                        # apps/my-web-app/api/
_ML_TRAINING = _HERE.parent.parent / "ml-training"          # apps/ml-training/
_DEFAULT_MODEL = _ML_TRAINING / "models" / "model.joblib"

MODEL_PATH = pathlib.Path(os.environ.get("MODEL_PATH", str(_DEFAULT_MODEL)))

# Add ml-training to sys.path so we can import ml_model / ml_data
if str(_ML_TRAINING) not in sys.path:
    sys.path.insert(0, str(_ML_TRAINING))

# ── Lazy-loaded model singleton ───────────────────────────────────────────────

_model = None
_model_load_attempted = False


def _load_model():
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        from ml_model import load_model  # type: ignore[import]
        _model = load_model(MODEL_PATH)
        logger.info("ML energy model loaded from %s", MODEL_PATH)
    except Exception as exc:
        logger.warning(
            "Could not load ML model from %s – energy will be None. Error: %s",
            MODEL_PATH,
            exc,
        )
        _model = None
    return _model


# ── Public API ────────────────────────────────────────────────────────────────

def predict_energy(input_text: str, input_tokens: int) -> float | None:
    """
    Return estimated GPU energy in **Joules** for running inference on `input_text`.

    Returns None if the model is unavailable.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        import pandas as pd
        from ml_model import predict_text  # type: ignore[import]
        _out_tokens, energy_j = predict_text(model, input_text, input_tokens)
        return round(float(energy_j), 6)
    except Exception as exc:
        logger.error("Energy prediction failed: %s", exc)
        return None
