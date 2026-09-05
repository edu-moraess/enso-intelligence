"""Availability-time contract for leakage-safe ENSO feature engineering.

Every predictor must carry an ``available_at`` timestamp: the earliest instant
at which the value could legitimately have been known to the forecasting
system.  Feature engineering may only use observations satisfying
``available_at <= forecast_origin``.

This module intentionally contains no source-specific publication assumptions.
Those mappings belong to the Foundation ingestion layer, where provenance can
be audited against the official source metadata.
"""
from __future__ import annotations

import pandas as pd


AVAILABILITY_COLUMN = "available_at"
FORECAST_ORIGIN_COLUMN = "forecast_origin"


def require_available_at(df: pd.DataFrame, *, name: str = "dataset") -> pd.DataFrame:
    """Validate and normalize the availability contract without mutating input."""
    if AVAILABILITY_COLUMN not in df.columns:
        raise ValueError(f"{name} must contain '{AVAILABILITY_COLUMN}'")

    work = df.copy()
    work[AVAILABILITY_COLUMN] = pd.to_datetime(
        work[AVAILABILITY_COLUMN], errors="coerce", utc=True
    )
    if work[AVAILABILITY_COLUMN].isna().any():
        raise ValueError(f"{name} contains invalid or missing '{AVAILABILITY_COLUMN}' values")
    return work


def available_by_forecast_origin(
    df: pd.DataFrame,
    forecast_origin: pd.Timestamp | str,
    *,
    name: str = "dataset",
) -> pd.DataFrame:
    """Return only observations known by ``forecast_origin``.

    The comparison is inclusive: an observation available exactly at the
    forecast origin is usable.  A missing availability timestamp is always an
    error; silently treating it as usable would create a leakage path.
    """
    work = require_available_at(df, name=name)
    origin = pd.Timestamp(forecast_origin)
    if origin.tzinfo is None:
        origin = origin.tz_localize("UTC")
    else:
        origin = origin.tz_convert("UTC")
    return work.loc[work[AVAILABILITY_COLUMN] <= origin].copy()


def assert_available_at_or_before(
    df: pd.DataFrame,
    forecast_origin: pd.Timestamp | str,
    *,
    name: str = "dataset",
) -> None:
    """Raise if any observation violates the forecast-time information set."""
    work = require_available_at(df, name=name)
    origin = pd.Timestamp(forecast_origin)
    if origin.tzinfo is None:
        origin = origin.tz_localize("UTC")
    else:
        origin = origin.tz_convert("UTC")
    invalid = work[work[AVAILABILITY_COLUMN] > origin]
    if not invalid.empty:
        first = invalid[AVAILABILITY_COLUMN].min().isoformat()
        raise ValueError(
            f"{name} contains {len(invalid)} observation(s) unavailable at "
            f"forecast origin {origin.isoformat()}; earliest violation: {first}"
        )
