"""NOAA data access modules and canonical observatory read paths."""

from __future__ import annotations

from src.data.foundation import ingest_and_archive, load_latest_snapshot
from src.data.models import DataStatus, SeriesMetadata

from .cpc import fetch_nino_indices as _fetch_nino_indices
from .cpc import fetch_oni as _fetch_oni
from .cpc import load_nino_indices as _parse_or_fetch_nino_indices
from .cpc import load_oni as _parse_or_fetch_oni
from .ersstv6 import get_ersst_status
from .roni import fetch_roni as _fetch_roni
from .roni import load_roni as _parse_or_fetch_roni


RONI_REQUIRED = ("date", "season", "year", "roni")
ONI_REQUIRED = ("date", "season", "year", "oni")
WEEKLY_NINO_REQUIRED = (
    "date",
    "nino12_sst", "nino12",
    "nino3_sst", "nino3",
    "nino34_sst", "nino34",
    "nino4_sst", "nino4",
)


def _foundation_metadata(snapshot, df) -> SeriesMetadata:
    """Expose foundation provenance through the existing metadata contract."""
    return SeriesMetadata(
        source=snapshot.source,
        dataset=snapshot.dataset,
        start=pd.to_datetime(df["date"]).min().to_pydatetime() if "date" in df.columns else None,
        end=pd.to_datetime(df["date"]).max().to_pydatetime() if "date" in df.columns else None,
        last_update=None,
        n_records=snapshot.rows,
        status=DataStatus.UPDATED,
        message=f"Foundation snapshot {snapshot.snapshot_id}",
        url=snapshot.source_url,
    )


def _foundation_error(dataset: str, exc: Exception) -> SeriesMetadata:
    """Return the existing metadata contract when the foundation cannot be read."""
    return SeriesMetadata(
        source="NOAA CPC",
        dataset=dataset,
        status=DataStatus.ERROR,
        message=f"Foundation data unavailable: {exc}",
    )


def _read_foundation(dataset, required_columns, label):
    try:
        df, snapshot = load_latest_snapshot(dataset, required_columns)
        return df, _foundation_metadata(snapshot, df)
    except (FileNotFoundError, KeyError, ValueError, OSError, pd.errors.ParserError) as exc:
        return None, _foundation_error(label, exc)


def fetch_roni():
    """Load the latest committed RONI foundation snapshot for the observatory."""
    return _read_foundation("roni", RONI_REQUIRED, "Relative Oceanic Niño Index (RONI)")


def fetch_oni():
    """Load the latest committed ONI foundation snapshot for the observatory."""
    return _read_foundation("oni", ONI_REQUIRED, "Oceanic Niño Index (ONI)")


def fetch_nino_indices():
    """Load the latest committed weekly Niño foundation snapshot for the observatory."""
    return _read_foundation(
        "weekly_nino",
        WEEKLY_NINO_REQUIRED,
        "Weekly Niño region SSTA (OISST.v2.1, 1991–2020)",
    )


# Explicit ingestion entry points used by the external Cloudflare automation.
# They remain live NOAA readers and are deliberately separate from the
# observatory fetch_* functions above.
def ingest_roni():
    return ingest_and_archive(
        _fetch_roni,
        dataset="roni",
        required_columns=RONI_REQUIRED,
    )


def ingest_oni():
    return ingest_and_archive(
        _fetch_oni,
        dataset="oni",
        required_columns=ONI_REQUIRED,
    )


def ingest_nino_indices():
    return ingest_and_archive(
        _fetch_nino_indices,
        dataset="weekly_nino",
        required_columns=WEEKLY_NINO_REQUIRED,
    )


# Parser/backward-compatible names remain available to tests and ingestion code.
def load_roni(text=None):
    if text is not None:
        return _parse_or_fetch_roni(text)
    return fetch_roni()


def load_oni(text=None):
    if text is not None:
        return _parse_or_fetch_oni(text)
    return fetch_oni()[0]


def load_nino_indices(text=None):
    if text is not None:
        return _parse_or_fetch_nino_indices(text)
    return fetch_nino_indices()[0]


__all__ = [
    "fetch_roni",
    "load_roni",
    "fetch_oni",
    "load_oni",
    "fetch_nino_indices",
    "load_nino_indices",
    "ingest_roni",
    "ingest_oni",
    "ingest_nino_indices",
    "get_ersst_status",
]
