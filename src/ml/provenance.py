"""Temporal provenance contracts for ENSO forecasting inputs.

This module deliberately separates *observation time* from *information time*.
A dataset may describe conditions at date ``t`` while only becoming usable by a
forecasting system at a later publication/availability timestamp.  The latter
is the value used by leakage checks.

No source-specific lag is assumed here.  A source is considered temporally
validated only after an explicit availability mapping has been supplied and
checked against authoritative publication metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd

from .availability import AVAILABILITY_COLUMN, require_available_at


@dataclass(frozen=True)
class AvailabilityMapping:
    """Auditable mapping from an observation source to its information time."""

    dataset: str
    source: str
    method: str
    evidence: str
    notes: str = ""


def attach_available_at(
    df: pd.DataFrame,
    available_at: pd.Series | Mapping | list,
    *,
    name: str = "dataset",
) -> pd.DataFrame:
    """Attach an explicit availability timestamp without changing observations.

    The caller must provide the information-time series explicitly.  This
    function never derives availability from the observation date, retrieval
    time, or an undocumented fixed lag.
    """
    if len(df) != len(available_at):
        raise ValueError(f"{name}: available_at length must match dataframe length")
    work = df.copy()
    work[AVAILABILITY_COLUMN] = pd.to_datetime(available_at, errors="coerce", utc=True)
    return require_available_at(work, name=name)


def validate_temporal_order(
    df: pd.DataFrame,
    *,
    observation_column: str = "date",
    name: str = "dataset",
) -> pd.DataFrame:
    """Validate that information time is not earlier than observation time."""
    work = require_available_at(df, name=name)
    if observation_column not in work.columns:
        raise ValueError(f"{name} must contain '{observation_column}'")
    observation = pd.to_datetime(work[observation_column], errors="coerce", utc=True)
    if observation.isna().any():
        raise ValueError(f"{name} contains invalid '{observation_column}' values")
    invalid = work.loc[work[AVAILABILITY_COLUMN] < observation]
    if not invalid.empty:
        raise ValueError(
            f"{name} contains {len(invalid)} record(s) whose available_at precedes "
            f"their observation date"
        )
    return work
