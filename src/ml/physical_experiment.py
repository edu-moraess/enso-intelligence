"""Experimental Ridge + D20 benchmark.

This module intentionally does not promote or publish a model. It is a gated
experiment: GODAS must have a validated information-time policy and the D20
table must carry explicit ``available_at`` timestamps before training begins.
"""
from __future__ import annotations

import pandas as pd

from src.data.availability_policy import require_temporal_approval
from src.ml.benchmark import benchmark_models
from src.ml.features import build_feature_table, feature_columns


def benchmark_ridge_plus_d20(
    roni: pd.DataFrame,
    oni: pd.DataFrame,
    d20: pd.DataFrame,
) -> dict:
    """Benchmark the D20-augmented candidate without promoting it.

    The existing benchmark engine is reused so Persistence, Ridge and
    Gradient Boosting retain exactly the same expanding walk-forward protocol.
    The only experimental change is the addition of two physical predictors:
    D20 anomaly and its 3-month change.
    """
    policy = require_temporal_approval("godas")
    table = build_feature_table(
        roni,
        oni,
        d20=d20,
        include_d20=True,
    )
    results, _ = benchmark_models(table)
    ridge = next(item for item in results if item.name == "Ridge")
    persistence = next(item for item in results if item.name == "Persistence")
    return {
        "experiment": "ridge_plus_d20",
        "availability_policy": policy.status,
        "features": feature_columns(table),
        "rows": len(table),
        "results": [item.to_dict() for item in results],
        "ridge_rmse": ridge.rmse,
        "ridge_mae": ridge.mae,
        "persistence_rmse": persistence.rmse,
        "promotable": ridge.rmse < persistence.rmse,
    }
