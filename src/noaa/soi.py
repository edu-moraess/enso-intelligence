"""NOAA CPC Southern Oscillation Index parser and live reader."""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests


SOI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/soi"


def _parse_soi_text(text: str) -> pd.DataFrame:
    """Parse the CPC monthly standardized SOI table into long form."""
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
            continue
        year = int(match.group(1))
        values = re.findall(r"[-+]?\d+(?:\.\d+)?", match.group(2))
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
