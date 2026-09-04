"""NOAA CPC Southern Oscillation Index parser and live reader."""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests


SOI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/soi"


_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _parse_soi_text(text: str) -> pd.DataFrame:
    """Parse the CPC monthly standardized SOI table into long form.

    CPC currently publishes missing values as ``-999.9``. In the current
    file some missing fields are adjacent to the previous value without
    whitespace (for example ``-1.8-999.9``), so tokenizing the row with
    ``split()`` is not reliable. Parse the numeric fields directly instead.
    Only the first SOI table is consumed; the file also contains a second,
    differently scaled standardized table below it.
    """
    lines = text.splitlines()
    header_index = next(
        (i for i, line in enumerate(lines) if re.match(r"^\s*YEAR\s+JAN\s+FEB", line)),
        None,
    )
    if header_index is None:
        raise ValueError("SOI header not found")

    rows: list[dict] = []
    for line in lines[header_index + 1 :]:
        match = re.match(r"^\s*(\d{4})(.*)$", line)
        if not match:
            # Stop before the second table. This also prevents accidentally
            # parsing any later YEAR header/table as part of the first block.
            if rows and "STANDARDIZED" in line.upper():
                break
            continue

        year = int(match.group(1))
        values = _NUMBER_RE.findall(match.group(2))
        if len(values) < 12:
            continue

        for month, raw in zip(range(1, 13), values[:12]):
            value = float(raw)
            if value <= -999:
                continue
            rows.append(
                {
                    "date": datetime(year, month, 15),
                    "year": year,
                    "month": month,
                    "soi": value,
                }
            )

    if not rows:
        raise ValueError("No valid SOI records found")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def fetch_soi_live() -> tuple[pd.DataFrame | None, object]:
    """Fetch the current monthly CPC SOI dataset for external ingestion."""
    from src.data.models import DataStatus, SeriesMetadata

    try:
        response = requests.get(SOI_URL, timeout=20)
        response.raise_for_status()
        df = _parse_soi_text(response.text)
        return df, SeriesMetadata(
            source="NOAA CPC",
            dataset="Southern Oscillation Index (SOI)",
            start=df["date"].min().to_pydatetime(),
            end=df["date"].max().to_pydatetime(),
            last_update=None,
            n_records=len(df),
            status=DataStatus.UPDATED,
            message="Live NOAA CPC SOI",
            url=SOI_URL,
        )
    except (requests.RequestException, ValueError) as exc:
        return None, SeriesMetadata(
            source="NOAA CPC",
            dataset="Southern Oscillation Index (SOI)",
            status=DataStatus.ERROR,
            message=f"SOI unavailable: {exc}",
            url=SOI_URL,
        )
