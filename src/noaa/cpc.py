"""NOAA CPC complementary products: ONI and Niño region SST indices."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
import requests

from src.data.models import NOAAConfig, DataStatus, SeriesMetadata, utc_now
from src.noaa.roni import SEASON_ORDER, _season_to_date

logger = logging.getLogger(__name__)


def fetch_oni(
    url: Optional[str] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Download and parse ONI ASCII from NOAA CPC.

    Source: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
    Columns in file: SEAS YR TOTAL ANOM
    """
    url = url or NOAAConfig.ONI_URL
    meta = SeriesMetadata(
        source="NOAA CPC",
        dataset="Oceanic Niño Index (ONI)",
        url=url,
        status=DataStatus.UNAVAILABLE,
    )

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as exc:
        logger.error("ONI download failed: %s", exc)
        meta.message = f"NOAA data unavailable: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    try:
        df = _parse_oni_text(text)
    except Exception as exc:
        logger.error("ONI parse failed: %s", exc)
        meta.message = f"Failed to parse ONI data: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    if df is None or df.empty:
        meta.message = "ONI series is empty after parsing."
        meta.status = DataStatus.WARNING
        return None, meta

    meta.n_records = len(df)
    meta.start = df["date"].min().to_pydatetime()
    meta.end = df["date"].max().to_pydatetime()
    meta.last_update = utc_now()
    meta.status = DataStatus.UPDATED
    meta.message = "OK"
    return df, meta


def _parse_oni_text(text: str) -> pd.DataFrame:
    """Parse oni.ascii.txt content."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    data_lines = []
    for ln in lines:
        parts = ln.split()
        if len(parts) < 4:
            continue
        season, year_s, total_s, anom_s = parts[0], parts[1], parts[2], parts[3]
        if season not in SEASON_ORDER:
            continue
        try:
            year = int(year_s)
            total = float(total_s)
            anom = float(anom_s)
        except ValueError:
            continue
        data_lines.append(
            {"season": season, "year": year, "total": total, "oni": anom}
        )

    if not data_lines:
        raise ValueError("No valid ONI records found in response.")

    df = pd.DataFrame(data_lines)
    df["date"] = [
        _season_to_date(s, y) for s, y in zip(df["season"], df["year"])
    ]
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_nino_indices(
    url: Optional[str] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Download and parse weekly Niño-region SSTA (wksst9120.for).

    Operational weekly product (1991–2020 base). The older wksst8110.for
    stopped updating ~Jan 2021.
    """
    url = url or NOAAConfig.WEEKLY_NINO_URL
    meta = SeriesMetadata(
        source="NOAA CPC",
        dataset="Weekly Niño region SSTA (OISST.v2.1, 1991–2020)",
        url=url,
        status=DataStatus.UNAVAILABLE,
    )

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as exc:
        logger.error("Weekly Niño download failed: %s", exc)
        meta.message = f"NOAA data unavailable: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    try:
        df = _parse_weekly_nino(text)
    except Exception as exc:
        logger.error("Weekly Niño parse failed: %s", exc)
        meta.message = f"Failed to parse weekly Niño data: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    if df is None or df.empty:
        meta.message = "Weekly Niño series is empty after parsing."
        meta.status = DataStatus.WARNING
        return None, meta

    meta.n_records = len(df)
    meta.start = df["date"].min().to_pydatetime()
    meta.end = df["date"].max().to_pydatetime()
    meta.last_update = utc_now()
    meta.status = DataStatus.UPDATED
    meta.message = "OK"
    return df, meta


def _parse_weekly_nino(text: str) -> pd.DataFrame:
    """Parse wksst9120.for (or similar fixed-width weekly file).

    Typical line starts with date (e.g. 03JAN2024) followed by SST/SSTA
    pairs for Nino1+2, Nino3, Nino34, Nino4. Numbers may be glued;
    regex extracts signed floats robustly.
    """
    rows = []
    date_re = re.compile(
        r"^\s*(\d{1,2}[A-Za-z]{3}\d{4})\s+(.*)$",
        re.IGNORECASE,
    )
    float_re = re.compile(r"[-+]?\d+\.\d+")

    for line in text.splitlines():
        m = date_re.match(line)
        if not m:
            continue
        date_s, rest = m.group(1), m.group(2)
        try:
            dt = datetime.strptime(date_s.upper(), "%d%b%Y")
        except ValueError:
            try:
                dt = datetime.strptime(date_s.upper(), "%d%b%y")
            except ValueError:
                continue
        nums = [float(x) for x in float_re.findall(rest)]
        if len(nums) < 8:
            continue
        rows.append(
            {
                "date": dt,
                "nino12_sst": nums[0],
                "nino12": nums[1],
                "nino3_sst": nums[2],
                "nino3": nums[3],
                "nino34_sst": nums[4],
                "nino34": nums[5],
                "nino4_sst": nums[6],
                "nino4": nums[7],
            }
        )

    if not rows:
        raise ValueError("No valid weekly Niño records found in response.")

    df = pd.DataFrame(rows)
    df = df.sort_values("date").reset_index(drop=True)
    # Keep the explicit anomaly names used by the one-page observatory UI.
    # The canonical parser fields above remain unchanged for compatibility.
    for region in ("nino12", "nino3", "nino34", "nino4"):
        df[f"{region}_ssta"] = df[region]
    return df


def fetch_monthly_nino(
    url: Optional[str] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> Tuple[Optional[pd.DataFrame], SeriesMetadata]:
    """Download and parse monthly Niño indices (sstoi.indices)."""
    url = url or NOAAConfig.MONTHLY_NINO_URL
    meta = SeriesMetadata(
        source="NOAA CPC",
        dataset="Monthly Niño region indices (sstoi.indices)",
        url=url,
        status=DataStatus.UNAVAILABLE,
    )

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as exc:
        logger.error("Monthly Niño download failed: %s", exc)
        meta.message = f"NOAA data unavailable: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    try:
        df = _parse_monthly_nino(text)
    except Exception as exc:
        logger.error("Monthly Niño parse failed: %s", exc)
        meta.message = f"Failed to parse monthly Niño data: {exc}"
        meta.status = DataStatus.ERROR
        return None, meta

    if df is None or df.empty:
        meta.message = "Monthly Niño series is empty after parsing."
        meta.status = DataStatus.WARNING
        return None, meta

    meta.n_records = len(df)
    meta.start = df["date"].min().to_pydatetime()
    meta.end = df["date"].max().to_pydatetime()
    meta.last_update = utc_now()
    meta.status = DataStatus.UPDATED
    meta.message = "OK"
    return df, meta


def _parse_monthly_nino(text: str) -> pd.DataFrame:
    """Parse sstoi.indices monthly file."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        parts = ln.split()
        if len(parts) < 10:
            continue
        try:
            year = int(parts[0])
            month = int(parts[1])
            n12 = float(parts[2])
            n12a = float(parts[3])
            n3 = float(parts[4])
            n3a = float(parts[5])
            n34 = float(parts[6])
            n34a = float(parts[7])
            n4 = float(parts[8])
            n4a = float(parts[9])
        except (ValueError, IndexError):
            continue
        if not (1 <= month <= 12) or year < 1950:
            continue
        rows.append(
            {
                "year": year,
                "month": month,
                "date": datetime(year, month, 15),
                "nino12_sst": n12,
                "nino12": n12a,
                "nino3_sst": n3,
                "nino3": n3a,
                "nino34_sst": n34,
                "nino34": n34a,
                "nino4_sst": n4,
                "nino4": n4a,
            }
        )

    if not rows:
        raise ValueError("No valid monthly Niño records found in response.")

    df = pd.DataFrame(rows)
    df = df.sort_values("date").reset_index(drop=True)
    return df


# Backward-compatible aliases used by some tests / older call sites
def load_oni(text: Optional[str] = None) -> pd.DataFrame:
    if text is not None:
        return _parse_oni_text(text)
    df, _ = fetch_oni()
    if df is None:
        raise ValueError("ONI load failed")
    return df


def load_nino_indices(text: Optional[str] = None) -> pd.DataFrame:
    if text is not None:
        return _parse_weekly_nino(text)
    df, _ = fetch_nino_indices()
    if df is None:
        raise ValueError("Weekly Niño load failed")
    return df
