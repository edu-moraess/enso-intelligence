"""Read-only production inference for the Streamlit observatory."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .features import feature_columns

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "roni_forecast.joblib"
DEFAULT_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "metadata.json"


def load_production_model(model_path: Path = DEFAULT_MODEL_PATH):
    """Load the published champion; return None when no champion exists."""
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def load_metadata(metadata_path: Path = DEFAULT_METADATA_PATH) -> dict | None:
    if not metadata_path.exists():
        return None
    import json
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def predict_next_roni(table: pd.DataFrame, model=None) -> float | None:
    """Predict the next RONI from the latest complete feature row."""
    if table is None or table.empty:
        return None
    model = model or load_production_model()
    if model is None:
        return None
    cols = feature_columns(table)
    row = table[cols].iloc[[-1]]
    return float(model.predict(row)[0])
