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

from src.data.models import THRESHOLD_EL_NINO, THRESHOLD_LA_NINA


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


def compute_recent_trend(series: pd.Series, n_seasons: int = 3) -> Tuple[str, Optional[float]]:
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


_SEASON_ORDER = {
    season: rank
    for rank, season in enumerate(
        ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
    )
}


def _is_next_season(previous: pd.Series, current: pd.Series, season_col: str, year_col: str) -> bool:
    """Return whether two rows are adjacent overlapping seasons in time."""
    previous_season = str(previous[season_col])
    current_season = str(current[season_col])
    previous_year = int(previous[year_col])
    current_year = int(current[year_col])

    previous_rank = _SEASON_ORDER[previous_season]
    current_rank = _SEASON_ORDER[current_season]
    expected_rank = (previous_rank + 1) % len(_SEASON_ORDER)
    expected_year = previous_year + (1 if previous_rank == len(_SEASON_ORDER) - 1 else 0)
    return current_rank == expected_rank and current_year == expected_year


def detect_enso_events(
    df: pd.DataFrame,
    value_col: str = "roni",
    season_col: str = "season",
    year_col: str = "year",
    min_consecutive: int = 5,
) -> List[ENSOEvent]:
    """Detect contiguous non-neutral RONI regimes of at least N seasons.

    The input is normalized into chronological order before classification.
    A regime is only considered contiguous when every pair of rows represents
    adjacent overlapping seasons; gaps or duplicate/missing seasons therefore
    cannot inflate an event duration.
    """
    required = {value_col, season_col, year_col}
    if df is None or df.empty or not required.issubset(df.columns):
        return []
    if min_consecutive < 1:
        return []

    work = df[[season_col, year_col, value_col]].copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
    work["_season_rank"] = work[season_col].map(_SEASON_ORDER)
    work = work.dropna(subset=[value_col, year_col, "_season_rank"])
    if work.empty:
        return []
    work = work.sort_values([year_col, "_season_rank"]).reset_index(drop=True)

    events: List[ENSOEvent] = []
    i = 0
    n = len(work)
    while i < n:
        state = classify_enso_state(float(work.iloc[i][value_col]))
        if state == ENSOState.NEUTRAL:
            i += 1
            continue

        j = i + 1
        while j < n:
            previous = work.iloc[j - 1]
            current = work.iloc[j]
            if not _is_next_season(previous, current, season_col, year_col):
                break
            if classify_enso_state(float(current[value_col])) != state:
                break
            j += 1

        length = j - i
        if length >= min_consecutive:
            segment = work.iloc[i:j]
            peak_pos = int(np.argmax(np.abs(segment[value_col].to_numpy(dtype=float))))
            peak_row = segment.iloc[peak_pos]
            peak_val = float(peak_row[value_col])
            events.append(
                ENSOEvent(
                    event_type=state.value,
                    start_season=str(segment.iloc[0][season_col]),
                    end_season=str(segment.iloc[-1][season_col]),
                    start_year=int(segment.iloc[0][year_col]),
                    end_year=int(segment.iloc[-1][year_col]),
                    duration_seasons=length,
                    peak_value=peak_val,
                    peak_season=str(peak_row[season_col]),
                    intensity=classify_intensity(peak_val).value,
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
