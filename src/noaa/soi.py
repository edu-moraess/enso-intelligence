"""Southern Oscillation Index (SOI) data access from NOAA CPC.

The NOAA CPC SOI product contains two monthly tables. This module uses only
the official STANDARDIZED DATA section and excludes NOAA's -999.9 missing-value
sentinel. No interpolation, imputation, fallback, or synthetic observations
are introduced.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
import requests

from src.data.models import DataStatus, NOAAConfig, SeriesMetadata, utc_now

logger = logging.getLogger(__name__)

MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
MISSING_VALUE = -999.9


def fetch_soi(
    url: Optional[str] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Download and parse the live monthly SOI ASCII file from NOAA CPC."""
    url = url or NOAAConfig.SOI_URL
    meta = SeriesMetadata(
        source="NOAA CPC",
        dataset="Southern Oscillation Index (SOI)",
        url=url,
        status=DataStatus.UNAVAILABLE,
    )
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as exc:
        logger.error("SOI download failed: %s", exc)
        meta.message = f"NOAA data unavailable: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    try:
        df = _parse_soi_text(text)
    except Exception as exc:
        logger.error("SOI parse failed: %s", exc)
        meta.message = f"Failed to parse SOI data: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    if df.empty:
        meta.message = "SOI series is empty after parsing."
        meta.status = DataStatus.WARNING
        return None, meta

    meta.n_records = len(df)
    meta.start = df["date"].min().to_pydatetime()
    meta.end = df["date"].max().to_pydatetime()
    meta.last_update = utc_now()
    meta.status = DataStatus.UPDATED
    meta.message = "OK"
    return df, meta


def _parse_soi_text(text: str) -> pd.DataFrame:
    """Parse NOAA's STANDARDIZED DATA table into chronological monthly rows."""
    lines = text.splitlines()
    standard_idx = next(
        (i for i, line in enumerate(lines) if "STANDARDIZED" in line.upper()),
        None,
    )
    if standard_idx is None:
        raise ValueError("NOAA SOI standardized-data section not found.")

    header_idx = next(
        (
            i for i in range(standard_idx + 1, len(lines))
            if lines[i].strip().upper().split()[:13] == ["YEAR", *MONTHS]
        ),
        None,
    )
    if header_idx is None:
        raise ValueError("NOAA SOI standardized-data header not found.")

    rows: list[dict] = []
    for line in lines[header_idx + 1:]:
        parts = line.strip().split()
        if not parts:
            continue
        year_token = parts[0]
        if not year_token.isdigit() or len(year_token) != 4:
            continue

        year = int(year_token)
        values = parts[1:]
        if len(values) < 12:
            continue

        for month, raw_value in zip(MONTHS, values[:12]):
            try:
                value = float(raw_value)
            except ValueError:
                continue
            if value == MISSING_VALUE:
                continue
            rows.append({
                "date": datetime(year, MONTHS.index(month) + 1, 15),
                "soi": value,
            })

    if not rows:
        raise ValueError("No valid SOI standardized observations found.")

    df = pd.DataFrame(rows)
    if df["date"].duplicated().any():
        raise ValueError("Duplicate SOI dates found.")
    return df.sort_values("date").reset_index(drop=True)
