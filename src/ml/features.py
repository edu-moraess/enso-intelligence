"""Feature construction for the one-step RONI ML experiment.

The feature builder uses only observations available at time t to predict
RONI at t+1. Physical features are opt-in and require an explicit
``available_at`` timestamp so temporal leakage fails closed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml.availability import require_available_at

RONI_LAGS = (1, 2, 3, 6, 12)
ONI_LAGS = (1, 3)
REGIONS = ("nino12", "nino3", "nino34", "nino4")


def _clean_series(df: pd.DataFrame, value: str) -> pd.DataFrame:
    work = df[["date", value]].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work[value] = pd.to_numeric(work[value], errors="coerce")
    return work.dropna(subset=["date", value]).sort_values("date").drop_duplicates("date")


def _monthly_nino(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate weekly regional anomalies to calendar-month means."""
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    for region in REGIONS:
        col = f"{region}_ssta"
        if col not in work.columns and region in work.columns:
            work[col] = work[region]
    keep = [f"{r}_ssta" for r in REGIONS if f"{r}_ssta" in work.columns]
    if not keep:
        return pd.DataFrame(columns=["date"])
    work = work.dropna(subset=["date"])
    for col in keep:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work["month"] = work["date"].dt.to_period("M")
    monthly = work.groupby("month", as_index=False)[keep].mean()
    monthly["date"] = monthly["month"].dt.to_timestamp("M")
    return monthly.drop(columns=["month"])


def _prepare_d20(d20: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize D20 information-time metadata."""
    required = {"date", "d20_m", "available_at"}
    missing = required.difference(d20.columns)
    if missing:
        raise ValueError(f"D20 table missing columns: {sorted(missing)}")

    work = d20[["date", "d20_m", "available_at"]].copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce", utc=True)
    work["d20_m"] = pd.to_numeric(work["d20_m"], errors="coerce")
    work = require_available_at(work, name="D20")
    work = work.dropna(subset=["date", "d20_m"])
    if work.empty:
        raise ValueError("D20 table contains no valid rows")

    work["month"] = work["date"].dt.to_period("M").astype(str)
    work = work.sort_values("date").drop_duplicates("month", keep="last")
    return work


def build_feature_table(
    roni: pd.DataFrame,
    oni: pd.DataFrame,
    nino: pd.DataFrame | None = None,
    d20: pd.DataFrame | None = None,
    *,
    include_regional: bool = False,
    include_d20: bool = False,
) -> pd.DataFrame:
    """Build a leakage-safe supervised table with target ``roni_t+1``.

    ``include_d20=True`` requires a D20 table with an explicit ``available_at``
    column. D20 is joined by calendar month, then filtered against the RONI
    forecast origin. No nearest-date merge is permitted.
    """
    r = _clean_series(roni, "roni")
    o = _clean_series(oni, "oni")
    base = pd.merge(r, o, on="date", how="inner")
    base = base.sort_values("date").reset_index(drop=True)

    if include_regional and nino is not None and not nino.empty:
        regional = _monthly_nino(nino)
        if not regional.empty:
            base["month"] = base["date"].dt.to_period("M")
            regional["month"] = regional["date"].dt.to_period("M")
            base = base.merge(regional.drop(columns=["date"]), on="month", how="left").drop(columns=["month"])

    if include_d20:
        if d20 is None or d20.empty:
            raise ValueError("include_d20=True requires a non-empty D20 table")
        physical = _prepare_d20(d20)
        base["month"] = base["date"].dt.to_period("M").astype(str)
        base["forecast_origin"] = pd.to_datetime(base["date"], utc=True)
        base = base.merge(
            physical[["month", "d20_m", "available_at"]],
            on="month",
            how="left",
            validate="one_to_one",
        )
        available = base["available_at"].notna() & (
            base["available_at"] <= base["forecast_origin"]
        )
        base = base.loc[available].copy()
        base["d20_anomaly_m"] = base["d20_m"]
        base["d20_trend_3m_m"] = base["d20_m"].diff(3)
        base = base.drop(columns=["month", "available_at", "forecast_origin"])

    features: dict[str, pd.Series] = {}
    for lag in RONI_LAGS:
        features[f"roni_lag_{lag}"] = base["roni"].shift(lag)
    for lag in ONI_LAGS:
        features[f"oni_lag_{lag}"] = base["oni"].shift(lag)

    for region in REGIONS:
        col = f"{region}_ssta"
        if col in base.columns:
            for lag in (1, 3, 6, 12):
                features[f"{region}_lag_{lag}"] = base[col].shift(lag)

    if include_d20:
        features["d20_anomaly_m"] = base["d20_anomaly_m"]
        features["d20_trend_3m_m"] = base["d20_trend_3m_m"]

    for window in (3, 6, 12):
        features[f"roni_mean_{window}"] = base["roni"].rolling(window).mean().shift(1)
        features[f"roni_trend_{window}"] = (
            base["roni"].rolling(window).apply(
                lambda x: np.polyfit(np.arange(len(x)), x, 1)[0], raw=True
            ).shift(1)
        )

    result = pd.DataFrame(features, index=base.index)
    result["date"] = base["date"]
    result["target"] = base["roni"].shift(-1)
    result = result.dropna().reset_index(drop=True)
    return result[["date", *[c for c in result.columns if c not in {"date", "target"}], "target"]]


def feature_columns(table: pd.DataFrame) -> list[str]:
    """Return deterministic predictor columns."""
    return [c for c in table.columns if c not in {"date", "target"}]
