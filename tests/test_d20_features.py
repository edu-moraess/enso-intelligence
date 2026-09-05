import pandas as pd
import pytest

from src.ml.features import build_feature_table


def _base():
    dates = pd.date_range("2000-01-31", periods=18, freq="ME")
    roni = pd.DataFrame({"date": dates, "roni": [0.1 + i * 0.01 for i in range(18)]})
    oni = pd.DataFrame({"date": dates, "oni": [0.2 + i * 0.01 for i in range(18)]})
    return roni, oni


def test_d20_requires_available_at():
    roni, oni = _base()
    d20 = pd.DataFrame({
        "date": roni["date"],
        "d20_m": [120.0 + i for i in range(18)],
    })
    with pytest.raises(ValueError, match="available_at"):
        build_feature_table(roni, oni, d20=d20, include_d20=True)


def test_d20_excludes_values_not_available_at_forecast_origin():
    roni, oni = _base()
    d20 = pd.DataFrame({
        "date": roni["date"],
        "d20_m": [120.0 + i for i in range(18)],
        "available_at": roni["date"] + pd.Timedelta(days=2),
    })
    table = build_feature_table(roni, oni, d20=d20, include_d20=True)
    assert table.empty


def test_d20_uses_only_available_months():
    roni, oni = _base()
    d20 = pd.DataFrame({
        "date": roni["date"],
        "d20_m": [120.0 + i for i in range(18)],
        "available_at": roni["date"],
    })
    table = build_feature_table(roni, oni, d20=d20, include_d20=True)
    assert not table.empty
    assert "d20_anomaly_m" in table.columns
    assert "d20_trend_3m_m" in table.columns
    assert table["d20_anomaly_m"].notna().all()
