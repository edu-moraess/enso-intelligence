"""Time-series benchmark for the experimental RONI outlook."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import feature_columns

MIN_TRAIN = 120
RANDOM_STATE = 42


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    rmse: float
    mae: float
    n_test: int
    beats_persistence: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _models() -> dict[str, object]:
    return {
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Gradient Boosting": HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=200,
            max_leaf_nodes=15,
            l2_regularization=0.5,
            random_state=RANDOM_STATE,
        ),
    }


def _walk_forward_predictions(table: pd.DataFrame, model: object, min_train: int = MIN_TRAIN) -> tuple[np.ndarray, np.ndarray]:
    cols = feature_columns(table)
    X = table[cols].to_numpy(dtype=float)
    y = table["target"].to_numpy(dtype=float)
    predictions: list[float] = []
    actuals: list[float] = []

    for test_index in range(min_train, len(table)):
        model.fit(X[:test_index], y[:test_index])
        predictions.append(float(model.predict(X[test_index:test_index + 1])[0]))
        actuals.append(float(y[test_index]))

    return np.asarray(actuals), np.asarray(predictions)


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float]:
    error = actual - predicted
    return float(np.sqrt(np.mean(error ** 2))), float(np.mean(np.abs(error)))


def benchmark_models(table: pd.DataFrame, *, min_train: int = MIN_TRAIN) -> tuple[list[BenchmarkResult], object | None]:
    """Evaluate persistence, Ridge and gradient boosting using expanding windows.

    The returned champion is fit on the complete table only when a learned
    model beats persistence on RMSE. Otherwise ``None`` is returned and the
    production layer should remain without an ML forecast.
    """
    if len(table) <= min_train:
        raise ValueError(f"Need more than {min_train} supervised rows; received {len(table)}")

    actual = table["target"].to_numpy(dtype=float)[min_train:]
    persistence = table["roni_lag_1"].to_numpy(dtype=float)[min_train:]
    persistence_rmse, persistence_mae = _metrics(actual, persistence)
    results = [
        BenchmarkResult("Persistence", persistence_rmse, persistence_mae, len(actual), True)
    ]

    best_name: str | None = None
    best_rmse = float("inf")
    models = _models()
    for name, model in models.items():
        actual_i, predicted_i = _walk_forward_predictions(table, model, min_train=min_train)
        rmse, mae = _metrics(actual_i, predicted_i)
        beats = rmse < persistence_rmse
        results.append(BenchmarkResult(name, rmse, mae, len(actual_i), beats))
        if beats and rmse < best_rmse:
            best_name, best_rmse = name, rmse

    champion = None
    if best_name is not None:
        champion = _models()[best_name]
        champion.fit(table[feature_columns(table)], table["target"])

    return results, champion
