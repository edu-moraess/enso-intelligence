import pandas as pd
import pytest

from src.ml.provenance import attach_available_at, validate_temporal_order


def test_attach_available_at_requires_one_timestamp_per_observation():
    df = pd.DataFrame({"date": ["2026-01-01", "2026-02-01"], "value": [1.0, 2.0]})
    result = attach_available_at(
        df,
        ["2026-01-05T00:00:00Z", "2026-02-05T00:00:00Z"],
        name="test",
    )
    assert "available_at" in result.columns
    assert str(result["available_at"].dt.tz) == "UTC"


def test_attach_available_at_rejects_length_mismatch():
    df = pd.DataFrame({"date": ["2026-01-01"], "value": [1.0]})
    with pytest.raises(ValueError, match="length"):
        attach_available_at(df, [], name="test")


def test_temporal_order_rejects_availability_before_observation():
    df = pd.DataFrame(
        {
            "date": ["2026-01-15"],
            "available_at": ["2026-01-14T00:00:00Z"],
        }
    )
    with pytest.raises(ValueError, match="precedes"):
        validate_temporal_order(df, name="test")


def test_temporal_order_accepts_same_day_availability():
    df = pd.DataFrame(
        {
            "date": ["2026-01-15"],
            "available_at": ["2026-01-15T00:00:00Z"],
        }
    )
    result = validate_temporal_order(df, name="test")
    assert len(result) == 1
