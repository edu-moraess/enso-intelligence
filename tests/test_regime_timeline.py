import pandas as pd

from src.ui.regime_timeline import build_regime_timeline


def test_regime_timeline_requires_five_overlapping_seasons():
    dates = pd.date_range("2000-01-15", periods=9, freq="3MS")
    values = [0.6, 0.7, 0.8, 0.9, 1.0, 0.2, -0.6, -0.7, -0.8]
    df = pd.DataFrame({"date": dates, "roni": values})

    fig = build_regime_timeline(df)

    assert fig is not None
    assert len(fig.data) >= 4


def test_regime_timeline_returns_none_without_qualifying_episode():
    dates = pd.date_range("2000-01-15", periods=6, freq="3MS")
    df = pd.DataFrame({"date": dates, "roni": [0.6, 0.7, 0.2, 0.1, -0.6, 0.0]})

    assert build_regime_timeline(df) is None
