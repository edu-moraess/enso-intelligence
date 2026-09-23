"""Focused tests for the NOAA CPC SOI parser."""

from __future__ import annotations

import pytest

from src.noaa.soi import _parse_soi_text


SAMPLE_SOI = """(STAND TAHITI - STAND DARWIN)  SEA LEVEL PRESS
                         ANOMALY

YEAR   JAN   FEB   MAR   APR   MAY   JUN   JUL   AUG   SEP   OCT   NOV   DEC
2025   0.3   0.9   2.8   0.9   0.7   0.5   1.0   0.7   0.1   1.9   1.8  -0.0
2026   1.8   2.4   2.0  -1.1  -1.5  -2.4  -4.0  -1.8 -999.9 -999.9 -999.9 -999.9

(STAND TAHITI - STAND DARWIN)  SEA LEVEL PRESS
                    STANDARDIZED    DATA

YEAR   JAN   FEB   MAR   APR   MAY   JUN   JUL   AUG   SEP   OCT   NOV   DEC
2025   0.2   0.5   1.7   0.5   0.4   0.3   0.6   0.4   0.1   1.2   1.1  -0.0
2026   1.1   1.5   1.2  -0.7  -0.9  -1.5  -2.5  -1.1-999.9-999.9-999.9-999.9
"""


def test_parser_uses_standardized_section():
    df = _parse_soi_text(SAMPLE_SOI)
    assert list(df.columns) == ["date", "soi"]
    assert len(df) == 20
    assert df.iloc[0]["soi"] == pytest.approx(0.2)


def test_parser_handles_compact_noaa_missing_values():
    df = _parse_soi_text(SAMPLE_SOI)
    assert df.iloc[-1]["date"].strftime("%Y-%m-%d") == "2026-08-15"
    assert df.iloc[-1]["soi"] == pytest.approx(-1.1)
    assert not (df["soi"] == -999.9).any()


def test_parser_returns_chronological_monthly_rows():
    df = _parse_soi_text(SAMPLE_SOI)
    assert df["date"].is_monotonic_increasing
    assert df.iloc[0]["date"].strftime("%Y-%m-%d") == "2025-01-15"
    assert df.iloc[-1]["date"].strftime("%Y-%m-%d") == "2026-08-15"


def test_parser_rejects_missing_standardized_section():
    with pytest.raises(ValueError, match="standardized-data section"):
        _parse_soi_text("YEAR JAN FEB MAR\n2026 1.0 2.0 3.0")


def test_parser_rejects_standardized_section_without_valid_rows():
    text = """STANDARDIZED DATA
YEAR JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
2026 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9 -999.9
"""
    with pytest.raises(ValueError, match="No valid SOI"):
        _parse_soi_text(text)
