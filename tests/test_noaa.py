"""Unit tests for NOAA parsers (offline, using sample text)."""

from __future__ import annotations

import pytest

from src.noaa.roni import _parse_roni_text
from src.noaa.cpc import _parse_oni_text, _parse_weekly_nino


SAMPLE_RONI = """SEAS   YR  ANOM
DJF  1950 -1.19
JFM  1950 -1.08
FMA  1950 -0.96
MAM  1950 -1.00
AMJ  2026  0.49
MJJ  2026  0.98
"""

SAMPLE_ONI = """ SEAS  YR   TOTAL   ANOM
  DJF 1950  25.01  -1.32
  JFM 1950  25.36  -1.20
  FMA 1950  25.88  -1.12
  MJJ 2026  28.10   0.95
"""

SAMPLE_WEEKLY = """
 Weekly SST data starts week centered on 3Jan1990

                Nino1+2      Nino3        Nino34        Nino4
 Week          SST SSTA     SST SSTA     SST SSTA     SST SSTA
 03JAN1990     23.4-0.4     25.1-0.3     26.6-0.0     28.6 0.3
 10JAN1990     23.4-0.8     25.2-0.3     26.6 0.1     28.6 0.3
 26AUG2026     24.1 1.2     27.5 1.5     28.2 1.8     29.1 0.9
"""


class TestRoniParser:
    def test_basic_parse(self):
        df = _parse_roni_text(SAMPLE_RONI)
        assert len(df) == 6
        assert list(df.columns) == ["season", "year", "roni", "date"]
        assert df.iloc[0]["roni"] == pytest.approx(-1.19)
        assert df.iloc[-1]["roni"] == pytest.approx(0.98)
        assert df.iloc[-1]["year"] == 2026

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _parse_roni_text("garbage\nno data")


class TestOniParser:
    def test_basic_parse(self):
        df = _parse_oni_text(SAMPLE_ONI)
        assert len(df) == 4
        assert "oni" in df.columns
        assert df.iloc[0]["oni"] == pytest.approx(-1.32)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _parse_oni_text("")


class TestWeeklyParser:
    def test_basic_parse(self):
        df = _parse_weekly_nino(SAMPLE_WEEKLY)
        assert len(df) >= 2
        assert "nino34_ssta" in df.columns
        assert df.iloc[0]["nino12_sst"] == pytest.approx(23.4)
        assert df.iloc[0]["nino12_ssta"] == pytest.approx(-0.4)
