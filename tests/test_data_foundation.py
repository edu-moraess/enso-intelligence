from pathlib import Path

import pandas as pd
import pytest

from src.data.foundation import ingest_and_archive, persist_snapshot, validate_dataset


REQUIRED = ("date", "roni")


def sample_df():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-05-15", "2026-06-15", "2026-07-15"]),
            "roni": [0.8, 1.1, 1.3],
        }
    )


def test_validation_accepts_clean_canonical_series():
    result = validate_dataset(sample_df(), REQUIRED)
    assert result.valid
    assert result.rows == 3
    assert result.duplicate_rows == 0
    assert result.duplicate_dates == 0


def test_validation_rejects_duplicate_dates():
    df = sample_df()
    df.loc[2, "date"] = df.loc[1, "date"]
    result = validate_dataset(df, REQUIRED)
    assert not result.valid
    assert result.duplicate_dates == 1


def test_validation_rejects_missing_columns():
    result = validate_dataset(sample_df()[["date"]], REQUIRED)
    assert not result.valid
    assert result.missing_required == ("roni",)


def test_validation_rejects_non_numeric_index_values():
    df = sample_df()
    df.loc[1, "roni"] = "bad"
    result = validate_dataset(df, REQUIRED)
    assert not result.valid
    assert result.non_numeric_values == ("roni",)


def test_persist_snapshot_is_content_addressed_and_idempotent(tmp_path: Path):
    first = persist_snapshot(
        sample_df(),
        dataset="roni",
        source="NOAA CPC",
        source_url="https://example.invalid/roni",
        required_columns=REQUIRED,
        root=tmp_path,
    )
    second = persist_snapshot(
        sample_df(),
        dataset="roni",
        source="NOAA CPC",
        source_url="https://example.invalid/roni",
        required_columns=REQUIRED,
        root=tmp_path,
    )

    assert first.snapshot_id == second.snapshot_id
    assert list((tmp_path / "roni").glob("*.csv")) == [
        tmp_path / "roni" / f"{first.snapshot_id}.csv"
    ]
    assert len((tmp_path / "roni" / "manifest.jsonl").read_text().splitlines()) == 1


def test_ingest_does_not_fallback_when_live_loader_fails(tmp_path: Path):
    def failed_loader():
        class Meta:
            source = "NOAA CPC"
            url = "https://example.invalid/roni"

        return None, Meta()

    df, meta, snapshot = ingest_and_archive(
        failed_loader,
        dataset="roni",
        required_columns=REQUIRED,
        root=tmp_path,
    )
    assert df is None
    assert snapshot is None
    assert not (tmp_path / "roni").exists()
