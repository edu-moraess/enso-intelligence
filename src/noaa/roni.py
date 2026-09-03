"""RONI (Relative Oceanic Niño Index) data access from NOAA CPC.

Primary operational index for ENSO monitoring (official since Feb 2026).
Source: https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
import requests

from src.data.models import NOAAConfig, DataStatus, SeriesMetadata, utc_now

logger = logging.getLogger(__name__)

SEASON_ORDER = [
    "DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
    "JJA", "JAS", "ASO", "SON", "OND", "NDJ",
]

# Approximate mid-month of the central month for each season label
SEASON_CENTRAL_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def _season_to_date(season: str, year: int) -> datetime:
    """Map seasonal label + year to a representative datetime (mid-month)."""
    month = SEASON_CENTRAL_MONTH.get(season, 6)
    # For DJF the year is the year of January/February
    return datetime(year, month, 15)


def fetch_roni(
    url: Optional[str] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Download and parse RONI ASCII file from NOAA CPC.

    Returns
    -------
    df : pd.DataFrame or None
        Columns: season, year, roni, date
    meta : SeriesMetadata
    """
    url = url or NOAAConfig.RONI_URL
    meta = SeriesMetadata(
        source="NOAA CPC",
        dataset="Relative Oceanic Niño Index (RONI)",
        url=url,
        status=DataStatus.UNAVAILABLE,
    )

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as exc:
        logger.error("RONI download failed: %s", exc)
        meta.message = f"NOAA data unavailable: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    try:
        df = _parse_roni_text(text)
    except Exception as exc:
        logger.error("RONI parse failed: %s", exc)
        meta.message = f"Failed to parse RONI data: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    if df is None or df.empty:
        meta.message = "RONI series is empty after parsing."
        meta.status = DataStatus.WARNING
        return None, meta

    meta.n_records = len(df)
    meta.start = df["date"].min().to_pydatetime()
    meta.end = df["date"].max().to_pydatetime()
    meta.last_update = utc_now()
    meta.status = DataStatus.UPDATED
    meta.message = "OK"
    return df, meta


def _parse_roni_text(text: str) -> pd.DataFrame:
    """Parse RONI.ascii.txt content.

    Expected format (header + rows):
        SEAS   YR  ANOM
        DJF  1950 -1.19
        ...
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Skip header if present
    data_lines = []
    for ln in lines:
        parts = ln.split()
        if len(parts) < 3:
            continue
        season, year_s, anom_s = parts[0], parts[1], parts[2]
        if season not in SEASON_ORDER:
            continue
        try:
            year = int(year_s)
            anom = float(anom_s)
        except ValueError:
            continue
        data_lines.append({"season": season, "year": year, "roni": anom})

    if not data_lines:
        raise ValueError("No valid RONI records found in response.")

    df = pd.DataFrame(data_lines)
    df["date"] = [
        _season_to_date(s, y) for s, y in zip(df["season"], df["year"])
    ]
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_roni(cached_df: Optional[pd.DataFrame] = None) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Convenience wrapper; prefers live fetch."""
    return fetch_roni()
