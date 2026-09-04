"""Offline tests for the NOAA CPC SOI parser."""

from __future__ import annotations

import pytest

from src.noaa.soi import _parse_soi_text


SAMPLE_SOI = """(STAND TAHITI - STAND DARWIN) SEA LEVEL PRESS ANOMALY
YEAR   JAN   FEB   MAR   APR   MAY   JUN   JUL   AUG   SEP   OCT   NOV   DEC
2025   0.3   0.9   2.8   0.9   0.7   0.5   1.0   0.7   0.1   1.9   1.8  -0.0
2026   1.8   2.4   2.0  -1.1  -1.5  -2.4  -4.0-999.9-999.9-999.9-999.9-999.9
"""


def test_soi_parser_returns_long_monthly_series():
    df = _parse_soi_text(SAMPLE_SOI)
    assert len(df) == 19
    assert list(df.columns) == ["date", "year", "month", "soi"]
    assert df.iloc[-1]["date"].strftime("%Y-%m-%d") == "2026-07-15"
    assert df.iloc[-1]["soi"] == pytest.approx(-4.0)


def test_soi_parser_rejects_missing_header():
    with pytest.raises(ValueError):
        _parse_soi_text("2026 1.0 2.0")
