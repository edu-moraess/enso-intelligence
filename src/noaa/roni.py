"""NOAA CPC Relative Oceanic Niño Index access."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import re

import pandas as pd
import requests

from src.data.models import DataFetchMeta

RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
SOURCE = "NOAA CPC RONI"


def _parse_roni_text(text: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z]{3})\s+(\d{4})\s+([-+]?\d+(?:\.\d+)?)\s*$", line)
        if match:
            season, year, value = match.groups()
            rows.append({"season": season.upper(), "year": int(year), "roni": float(value)})
    if not rows:
        raise ValueError("No valid RONI records were found in the NOAA response.")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-" + df["season"].map({"DJF":"01","JFM":"02","FMA":"03","MAM":"04","AMJ":"05","MJJ":"06","JJA":"07","JAS":"08","ASO":"09","SON":"10","OND":"11","NDJ":"12"}) + "-15", errors="coerce")
    return df[["season", "year", "roni", "date"]].reset_index(drop=True)


def load_roni(text: str) -> pd.DataFrame:
    return _parse_roni_text(text)


def fetch_roni(timeout: int = 20) -> tuple[pd.DataFrame | None, DataFetchMeta]:
    fetched_at = datetime.now(timezone.utc)
    try:
        response = requests.get(RONI_URL, timeout=timeout)
        response.raise_for_status()
        df = _parse_roni_text(response.text)
        return df, DataFetchMeta(SOURCE, RONI_URL, len(df), fetched_at)
    except (requests.RequestException, ValueError) as exc:
        return None, DataFetchMeta.unavailable(SOURCE, RONI_URL, str(exc))
