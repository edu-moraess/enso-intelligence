from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml.features import build_feature_table


def _series(n: int = 150) -> pd.DataFrame:
    dates = pd.date_range("1955-01-15", periods=n, freq="MS") + pd.Timedelta(days=14)
    values = np.sin(np.arange(n) / 7.0) + np.arange(n) * 0.001
    return pd.DataFrame({"date": dates, "season": ["DJF"] * n, "year": dates.year, "roni": values})


def test_feature_table_is_temporally_aligned() -> None:
    roni = _series()
    oni = roni.rename(columns={"roni": "oni"})
    table = build_feature_table(roni, oni)

    assert not table.empty
    assert table["date"].is_monotonic_increasing
    assert "roni_lag_1" in table.columns
    assert "roni_lag_12" in table.columns
    assert "target" in table.columns
    latest = table.iloc[-1]
    source = roni.set_index("date")
    assert latest["roni_lag_1"] == source.loc[latest["date"] - pd.DateOffset(months=1), "roni"]


def test_regional_features_are_optional() -> None:
    roni = _series()
    oni = roni.rename(columns={"roni": "oni"})
    weekly = pd.DataFrame(
        {
            "date": pd.date_range("1955-01-01", periods=180, freq="7D"),
            "nino12": np.ones(180),
            "nino3": np.ones(180) * 2,
            "nino34": np.ones(180) * 3,
            "nino4": np.ones(180) * 4,
        }
    )
    plain = build_feature_table(roni, oni)
    regional = build_feature_table(roni, oni, weekly, include_regional=True)
    assert not any(name.startswith("nino34_") for name in plain.columns)
    assert any(name.startswith("nino34_") for name in regional.columns)
