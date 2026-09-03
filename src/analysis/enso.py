"""Deterministic ENSO classification helpers."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any

import pandas as pd


class ENSOState(str, Enum):
    EL_NINO = "El Niño"
    LA_NINA = "La Niña"
    NEUTRAL = "Neutral"


class Intensity(str, Enum):
    NONE = "None"
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def classify_enso_state(value: Any) -> ENSOState:
    number = _finite(value)
    if number is None:
        return ENSOState.NEUTRAL
    if number >= 0.5:
        return ENSOState.EL_NINO
    if number <= -0.5:
        return ENSOState.LA_NINA
    return ENSOState.NEUTRAL


def classify_intensity(value: Any) -> Intensity:
    number = _finite(value)
    if number is None:
        return Intensity.NONE
    magnitude = abs(number)
    if magnitude < 0.5:
        return Intensity.NONE
    if magnitude < 1.0:
        return Intensity.WEAK
    if magnitude < 1.5:
        return Intensity.MODERATE
    if magnitude < 2.0:
        return Intensity.STRONG
    return Intensity.VERY_STRONG


def compute_recent_trend(values: pd.Series, n_seasons: int = 3) -> tuple[str, float | None]:
    if values is None or n_seasons < 2:
        return "insufficient data", None
    clean = pd.to_numeric(values, errors="coerce").dropna().tail(n_seasons)
    if len(clean) < n_seasons:
        return "insufficient data", None
    delta = float(clean.iloc[-1] - clean.iloc[0])
    if delta > 0.1:
        return "warming", delta
    if delta < -0.1:
        return "cooling", delta
    return "stable", delta


@dataclass(frozen=True)
class ENSOEvent:
    event_type: str
    start_season: str
    start_year: int
    end_season: str
    end_year: int
    duration_seasons: int
    peak_value: float


def detect_enso_events(df: pd.DataFrame | None, min_consecutive: int = 5) -> list[ENSOEvent]:
    if df is None or df.empty or min_consecutive < 1:
        return []
    required = {"season", "year", "roni"}
    if not required.issubset(df.columns):
        return []
    events: list[ENSOEvent] = []
    current: list[tuple[str, int, float, ENSOState]] = []

    def flush() -> None:
        nonlocal current
        if len(current) >= min_consecutive:
            state = current[0][3]
            values = [row[2] for row in current]
            events.append(ENSOEvent(
                event_type=state.value,
                start_season=current[0][0], start_year=current[0][1],
                end_season=current[-1][0], end_year=current[-1][1],
                duration_seasons=len(current), peak_value=max(values) if state == ENSOState.EL_NINO else min(values),
            ))
        current = []

    for _, row in df.iterrows():
        value = _finite(row.get("roni"))
        state = classify_enso_state(value)
        if state == ENSOState.NEUTRAL:
            flush()
            continue
        if current and state != current[0][3]:
            flush()
        if value is not None:
            current.append((str(row["season"]), int(row["year"]), value, state))
    flush()
    return events
