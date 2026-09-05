import pandas as pd
import pytest

from src.ml.availability import (
    assert_available_at_or_before,
    available_by_forecast_origin,
    require_available_at,
)


def test_require_available_at_normalizes_to_utc():
    df = pd.DataFrame({"date": ["2026-01-01"], "available_at": ["2026-01-15 12:00"]})
    out = require_available_at(df)
    assert str(out.loc[0, "available_at"]) == "2026-01-15 12:00:00+00:00"


def test_missing_available_at_is_rejected():
    with pytest.raises(ValueError, match="available_at"):
        require_available_at(pd.DataFrame({"date": ["2026-01-01"]}))


def test_missing_or_invalid_available_at_is_rejected():
    df = pd.DataFrame({"available_at": [None]})
    with pytest.raises(ValueError, match="invalid or missing"):
        require_available_at(df)


def test_filter_keeps_only_information_available_at_origin():
    df = pd.DataFrame(
        {
            "value": [1, 2, 3],
            "available_at": [
                "2026-01-01T00:00:00Z",
                "2026-01-10T00:00:00Z",
                "2026-01-20T00:00:00Z",
            ],
        }
    )
    out = available_by_forecast_origin(df, "2026-01-10T00:00:00Z")
    assert out["value"].tolist() == [1, 2]


def test_exact_origin_is_allowed():
    df = pd.DataFrame({"available_at": ["2026-01-10T00:00:00Z"]})
    assert len(available_by_forecast_origin(df, "2026-01-10T00:00:00Z")) == 1


def test_future_information_raises_in_strict_assertion():
    df = pd.DataFrame(
        {"available_at": ["2026-01-10T00:00:00Z", "2026-01-11T00:00:00Z"]}
    )
    with pytest.raises(ValueError, match="unavailable at forecast origin"):
        assert_available_at_or_before(df, "2026-01-10T12:00:00Z")
