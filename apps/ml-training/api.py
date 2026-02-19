"""FastAPI endpoints for the ml-training model.

Endpoint: GET /estimate-tokens?text=...
Response: { tokens, power, model, len }

Run locally:
  uvicorn api:app --app-dir apps/ml-training --port 8001 --reload

Notes:
- The app loads `apps/ml-training/models/model.joblib` at startup.
- Uses `ml_data.estimate_tokens` and `ml_model.predict_text`.
"""

from __future__ import annotations

import pathlib
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

import ml_data
import ml_model

APP = FastAPI(title="ml-training API")
# resolve model path relative to this module so it works when uvicorn is run
MODEL_PATH = pathlib.Path(__file__).resolve().parent / "models" / "model.joblib"


@APP.on_event("startup")
def _load_model_on_startup() -> None:
    try:
        APP.state.model = ml_model.load_model(MODEL_PATH)
        APP.state.model_path = MODEL_PATH
    except FileNotFoundError:
        # keep model None and return an error on requests
        APP.state.model = None
        APP.state.model_path = None


@APP.get("/health")
def health() -> dict:
    return {"ok": APP.state.model is not None}


@APP.get("/estimate-tokens")
def estimate_tokens_endpoint(text: str = Query(..., description="Input text")) -> dict:
    """Return token estimate and predicted power for the input text."""
    if APP.state.model is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded — train the model first"
        )

    tokens = ml_data.estimate_tokens(text)
    out_tokens, out_energy = ml_model.predict_text(APP.state.model, text, tokens)

    return {
        "tokens": int(out_tokens),
        "power": float(out_energy),
        "model": str(APP.state.model_path.name) if APP.state.model_path else "unknown",
        "len": len(text),
    }


# exported symbol the server expects
app = APP
