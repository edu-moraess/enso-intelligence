"""NOAA CPC ONI and weekly Niño-region index access."""
from __future__ import annotations

from datetime import datetime, timezone
import re

import pandas as pd
import requests

from src.data.models import DataFetchMeta

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
WEEKLY_NINO_URL = "https://www.cpc.ncep.noaa.gov/data/indices/wksst8110.for"


def _parse_oni_text(text: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z]{3})\s+(\d{4})\s+([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)", line)
        if match:
            season, year, total, anomaly = match.groups()
            rows.append({"season": season.upper(), "year": int(year), "total": float(total), "oni": float(anomaly)})
    if not rows:
        raise ValueError("No valid ONI records were found in the NOAA response.")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-01-15", errors="coerce")
    return df[["season", "year", "total", "oni", "date"]].reset_index(drop=True)


def load_oni(text: str) -> pd.DataFrame:
    return _parse_oni_text(text)


def _parse_weekly_nino(text: str) -> pd.DataFrame:
    rows = []
    regions = [("nino12", "Nino1+2"), ("nino3", "Nino3"), ("nino34", "Nino34"), ("nino4", "Nino4")]
    for line in text.splitlines():
        date_match = re.match(r"^\s*(\d{2}[A-Za-z]{3}\d{4})\s+(.*)$", line)
        if not date_match:
            continue
        date_token, rest = date_match.groups()
        try:
            date = pd.to_datetime(date_token, format="%d%b%Y")
        except ValueError:
            continue
        # NOAA's fixed-width product may omit whitespace between SST and a negative SSTA.
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", rest)
        if len(numbers) < 8:
            continue
        row: dict[str, object] = {"date": date}
        for i, (prefix, _) in enumerate(regions):
            row[f"{prefix}_sst"] = float(numbers[i * 2])
            row[f"{prefix}_ssta"] = float(numbers[i * 2 + 1])
        rows.append(row)
    if not rows:
        raise ValueError("No valid weekly Niño records were found in the NOAA response.")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def load_nino_indices(text: str) -> pd.DataFrame:
    return _parse_weekly_nino(text)


def _fetch(url: str, source: str, parser, timeout: int):
    fetched_at = datetime.now(timezone.utc)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        df = parser(response.text)
        return df, DataFetchMeta(source, url, len(df), fetched_at)
    except (requests.RequestException, ValueError) as exc:
        return None, DataFetchMeta.unavailable(source, url, str(exc))


def fetch_oni(timeout: int = 20):
    return _fetch(ONI_URL, "NOAA CPC ONI", _parse_oni_text, timeout)


def fetch_nino_indices(timeout: int = 20):
    return _fetch(WEEKLY_NINO_URL, "NOAA CPC weekly Niño indices", _parse_weekly_nino, timeout)
