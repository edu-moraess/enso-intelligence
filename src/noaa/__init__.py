"""NOAA data access modules."""

from __future__ import annotations

from src.data.foundation import ingest_and_archive

from .cpc import fetch_nino_indices as _fetch_nino_indices
from .cpc import fetch_oni as _fetch_oni
from .cpc import load_nino_indices, load_oni
from .ersstv6 import get_ersst_status
from .roni import fetch_roni as _fetch_roni
from .roni import load_roni


def fetch_roni():
    """Fetch live NOAA RONI and archive a validated content-addressed snapshot."""
    df, meta, _ = ingest_and_archive(
        _fetch_roni,
        dataset="roni",
        required_columns=("date", "season", "year", "roni"),
    )
    return df, meta


def fetch_oni():
    """Fetch live NOAA ONI and archive a validated content-addressed snapshot."""
    df, meta, _ = ingest_and_archive(
        _fetch_oni,
        dataset="oni",
        required_columns=("date", "season", "year", "oni"),
    )
    return df, meta


def fetch_nino_indices():
    """Fetch live weekly Niño indices and archive a validated snapshot."""
    df, meta, _ = ingest_and_archive(
        _fetch_nino_indices,
        dataset="weekly_nino",
        required_columns=(
            "date",
            "nino12_sst", "nino12",
            "nino3_sst", "nino3",
            "nino34_sst", "nino34",
            "nino4_sst", "nino4",
        ),
    )
    return df, meta


__all__ = [
    "fetch_roni",
    "load_roni",
    "fetch_oni",
    "load_oni",
    "fetch_nino_indices",
    "load_nino_indices",
    "get_ersst_status",
]
