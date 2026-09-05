import numpy as np
import pandas as pd
import pytest

from src.data.godas import _d20_from_profile, add_d20_anomaly_and_trend, godas_temperature_url


def test_godas_url_uses_official_yearly_temperature_file():
    assert godas_temperature_url(2026).endswith("/pottmp.2026.nc")


def test_d20_interpolates_between_model_levels():
    assert _d20_from_profile(
        np.array([15.0, 25.0, 35.0]),
        np.array([22.0, 18.0, 15.0]),
    ) == pytest.approx(20.0)


def test_d20_returns_nan_without_a_20c_crossing():
    assert np.isnan(
        _d20_from_profile(
            np.array([15.0, 25.0, 35.0]),
            np.array([24.0, 22.0, 21.0]),
        )
    )


def test_d20_does_not_extrapolate_missing_profiles():
    assert np.isnan(
        _d20_from_profile(
            np.array([15.0, 25.0, 35.0]),
            np.array([np.nan, np.nan, np.nan]),
        )
    )


def test_d20_anomaly_uses_calendar_month_climatology_and_three_month_change():
    dates = pd.date_range("1991-01-01", periods=36, freq="MS", tz="UTC")
    df = pd.DataFrame({"date": dates, "d20_m": np.arange(36, dtype=float)})
    out = add_d20_anomaly_and_trend(df)

    assert "d20_anomaly_m" in out
    assert "d20_trend_3m_m" in out
    assert out.loc[3, "d20_trend_3m_m"] == pytest.approx(3.0)
    assert out.loc[12, "d20_climatology_m"] == pytest.approx(12.0)
    assert out.loc[13, "d20_climatology_m"] == pytest.approx(13.0)
