"""Unit tests for ENSO classification and event detection (no network)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.enso import (
    classify_enso_state,
    classify_intensity,
    compute_recent_trend,
    detect_enso_events,
    ENSOState,
    Intensity,
)


class TestClassifyState:
    def test_el_nino(self):
        assert classify_enso_state(0.5) == ENSOState.EL_NINO
        assert classify_enso_state(1.2) == ENSOState.EL_NINO
        assert classify_enso_state(2.5) == ENSOState.EL_NINO

    def test_la_nina(self):
        assert classify_enso_state(-0.5) == ENSOState.LA_NINA
        assert classify_enso_state(-1.8) == ENSOState.LA_NINA

    def test_neutral(self):
        assert classify_enso_state(0.0) == ENSOState.NEUTRAL
        assert classify_enso_state(0.49) == ENSOState.NEUTRAL
        assert classify_enso_state(-0.49) == ENSOState.NEUTRAL

    def test_nan(self):
        assert classify_enso_state(float("nan")) == ENSOState.NEUTRAL


class TestIntensity:
    def test_none_below_threshold(self):
        assert classify_intensity(0.3) == Intensity.NONE
        assert classify_intensity(-0.2) == Intensity.NONE

    def test_weak(self):
        assert classify_intensity(0.7) == Intensity.WEAK
        assert classify_intensity(-0.9) == Intensity.WEAK

    def test_moderate(self):
        assert classify_intensity(1.2) == Intensity.MODERATE
        assert classify_intensity(-1.4) == Intensity.MODERATE

    def test_strong(self):
        assert classify_intensity(1.6) == Intensity.STRONG
        assert classify_intensity(-1.9) == Intensity.STRONG

    def test_very_strong(self):
        assert classify_intensity(2.0) == Intensity.VERY_STRONG
        assert classify_intensity(-2.5) == Intensity.VERY_STRONG


class TestTrend:
    def test_warming(self):
        s = pd.Series([0.1, 0.3, 0.6])
        label, delta = compute_recent_trend(s, n_seasons=3)
        assert label == "warming"
        assert delta == pytest.approx(0.5)

    def test_cooling(self):
        s = pd.Series([0.8, 0.4, 0.1])
        label, delta = compute_recent_trend(s, n_seasons=3)
        assert label == "cooling"

    def test_stable(self):
        s = pd.Series([0.5, 0.52, 0.55])
        label, delta = compute_recent_trend(s, n_seasons=3)
        assert label == "stable"

    def test_insufficient(self):
        s = pd.Series([0.1])
        label, delta = compute_recent_trend(s, n_seasons=3)
        assert label == "insufficient data"
        assert delta is None


class TestEventDetection:
    def _make_series(self, values, start_year=2000):
        seasons = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
        rows = []
        year = start_year
        si = 0
        for v in values:
            rows.append({"season": seasons[si], "year": year, "roni": v})
            si += 1
            if si == 12:
                si = 0
                year += 1
        return pd.DataFrame(rows)

    def test_detect_el_nino_event(self):
        vals = [0.0, 0.2] + [0.8] * 6 + [0.1, 0.0]
        df = self._make_series(vals)
        events = detect_enso_events(df, min_consecutive=5)
        assert len(events) == 1
        assert events[0].event_type == "El Niño"
        assert events[0].duration_seasons == 6
        assert events[0].peak_value == pytest.approx(0.8)

    def test_detect_la_nina_event(self):
        vals = [0.0] + [-0.9] * 5 + [0.1]
        df = self._make_series(vals)
        events = detect_enso_events(df, min_consecutive=5)
        assert len(events) == 1
        assert events[0].event_type == "La Niña"

    def test_short_run_ignored(self):
        vals = [0.0, 0.8, 0.9, 0.7, 0.1]
        df = self._make_series(vals)
        events = detect_enso_events(df, min_consecutive=5)
        assert len(events) == 0

    def test_empty_input(self):
        assert detect_enso_events(pd.DataFrame()) == []
        assert detect_enso_events(None) == []
