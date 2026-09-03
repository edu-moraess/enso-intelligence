"""ENSO classification, intensity, event detection and trend utilities.

All thresholds follow NOAA operational definitions for RONI/ONI.
No synthetic values are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data.models import (
    THRESHOLD_EL_NINO,
    THRESHOLD_LA_NINA,
)

class ENSOState(str, Enum):
    EL_NINO = "El Niño"
    LA_NINA = "La Niña"
    NEUTRAL = "Neutral"


class Intensity(str, Enum):
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"
    NONE = "—"


def classify_enso_state(value: float) -> ENSOState:
    if pd.isna(value):
        return ENSOState.NEUTRAL
    if value >= THRESHOLD_EL_NINO:
        return ENSOState.EL_NINO
    if value <= THRESHOLD_LA_NINA:
        return ENSOState.LA_NINA
    return ENSOState.NEUTRAL


def classify_intensity(value: float) -> Intensity:
    if pd.isna(value):
        return Intensity.NONE
    abs_v = abs(float(value))
    if abs_v < THRESHOLD_EL_NINO:
        return Intensity.NONE
    if abs_v >= 2.0:
        return Intensity.VERY_STRONG
    if abs_v >= 1.5:
        return Intensity.STRONG
    if abs_v >= 1.0:
        return Intensity.MODERATE
    return Intensity.WEAK


def compute_recent_trend(
    series: pd.Series,
    n_seasons: int = 3,
) -> Tuple[str, Optional[float]]:
    clean = series.dropna()
    if len(clean) < n_seasons:
        return "insufficient data", None
    recent = clean.iloc[-n_seasons:]
    delta = float(recent.iloc[-1] - recent.iloc[0])
    if abs(delta) < 0.15:
        return "stable", delta
    if delta > 0:
        return "warming", delta
    return "cooling", delta


@dataclass
class ENSOEvent:
    event_type: str
    start_season: str
    end_season: str
    start_year: int
    end_year: int
    duration_seasons: int
    peak_value: float
    peak_season: str
    intensity: str


def detect_enso_events(
    df: pd.DataFrame,
    value_col: str = "roni",
    season_col: str = "season",
    year_col: str = "year",
    min_consecutive: int = 5,
) -> List[ENSOEvent]:
    if df is None or df.empty or value_col not in df.columns:
        return []
    work = df[[season_col, year_col, value_col]].copy()
    work = work.dropna(subset=[value_col]).reset_index(drop=True)
    if work.empty:
        return []
    values = work[value_col].astype(float).values
    states = np.array([classify_enso_state(v).value for v in values])
    events: List[ENSOEvent] = []
    i = 0
    n = len(states)
    while i < n:
        current = states[i]
        if current == ENSOState.NEUTRAL.value:
            i += 1
            continue
        j = i
        while j < n and states[j] == current:
            j += 1
        length = j - i
        if length >= min_consecutive:
            segment = work.iloc[i:j]
            peak_idx = segment[value_col].abs().idxmax()
            peak_row = segment.loc[peak_idx]
            peak_val = float(peak_row[value_col])
            intensity = classify_intensity(peak_val).value
            events.append(
                ENSOEvent(
                    event_type=current,
                    start_season=str(segment.iloc[0][season_col]),
                    end_season=str(segment.iloc[-1][season_col]),
                    start_year=int(segment.iloc[0][year_col]),
                    end_year=int(segment.iloc[-1][year_col]),
                    duration_seasons=length,
                    peak_value=peak_val,
                    peak_season=str(peak_row[season_col]),
                    intensity=intensity,
                )
            )
        i = j
    return events


def recent_evolution_metrics(series: pd.Series, ols_window: int = 5) -> dict:
    clean = series.dropna().astype(float)
    out: dict = {
        "delta_1": None,
        "delta_3": None,
        "delta_5": None,
        "delta_12": None,
        "label_3": "insufficient data",
        "slope": None,
        "r_squared": None,
        "ols_n": 0,
        "ols_window": int(ols_window),
        "n": int(len(clean)),
        "slope_5": None,
    }
    if len(clean) >= 2:
        out["delta_1"] = float(clean.iloc[-1] - clean.iloc[-2])
    if len(clean) >= 3:
        d3 = float(clean.iloc[-1] - clean.iloc[-3])
        out["delta_3"] = d3
        if abs(d3) < 0.15:
            out["label_3"] = "stable"
        elif d3 > 0:
            out["label_3"] = "warming"
        else:
            out["label_3"] = "cooling"
    if len(clean) >= 5:
        out["delta_5"] = float(clean.iloc[-1] - clean.iloc[-5])
    if len(clean) >= 12:
        out["delta_12"] = float(clean.iloc[-1] - clean.iloc[-12])
    n_ols = min(int(ols_window), len(clean))
    if n_ols >= 3:
        y = clean.iloc[-n_ols:].values.astype(float)
        x = np.arange(n_ols, dtype=float)
        x_mean = float(x.mean())
        y_mean = float(y.mean())
        denom = float(((x - x_mean) ** 2).sum())
        if denom > 0:
            slope = float(((x - x_mean) * (y - y_mean)).sum() / denom)
            intercept = y_mean - slope * x_mean
            y_hat = intercept + slope * x
            ss_res = float(((y - y_hat) ** 2).sum())
            ss_tot = float(((y - y_mean) ** 2).sum())
            r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else None
            out["slope"] = slope
            out["slope_5"] = slope
            out["r_squared"] = r2
            out["ols_n"] = n_ols
    return out


def historical_percentile(series: pd.Series, value: float) -> Optional[float]:
    clean = series.dropna().astype(float)
    if clean.empty or pd.isna(value):
        return None
    v = float(value)
    n = len(clean)
    less = float((clean < v).sum())
    equal = float((clean == v).sum())
    return 100.0 * (less + 0.5 * equal) / n


def intensity_gauge_position(value: float) -> float:
    if pd.isna(value):
        return 0.5
    return float(np.clip((float(value) + 1.5) / 3.0, 0.0, 1.0))


def extreme_events_summary(events: List[ENSOEvent]) -> dict:
    summary = {
        "n_events": len(events),
        "strongest_el_nino": None,
        "strongest_la_nina": None,
        "longest": None,
    }
    if not events:
        return summary
    el = [e for e in events if e.event_type == "El Niño"]
    la = [e for e in events if e.event_type == "La Niña"]
    if el:
        summary["strongest_el_nino"] = max(el, key=lambda e: e.peak_value)
    if la:
        summary["strongest_la_nina"] = min(la, key=lambda e: e.peak_value)
    summary["longest"] = max(events, key=lambda e: e.duration_seasons)
    return summary
