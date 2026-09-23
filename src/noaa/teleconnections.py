"""Official climate teleconnection data access for ENSO Intelligence.

Sources:
- NOAA/CPC: central tropical Pacific OLR index.
- NOAA/PSL: PDO, DMI/IOD and SAM/AAO monthly indices.
- Australian Bureau of Meteorology: Wheeler-Hendon RMM MJO index.
All observations are ingested into the repository Foundation before UI use.
"""

from __future__ import annotations

from io import StringIO
from urllib.request import Request, urlopen

import pandas as pd

from src.data.foundation import ingest_and_archive, load_latest_snapshot
from src.data.models import DataStatus, SeriesMetadata


OLR_URL = "https://www.cpc.ncep.noaa.gov/data/indices/olr"
PDO_URL = "https://psl.noaa.gov/pdo/data/pdo.timeseries.sstens.data"
IOD_URL = "https://psl.noaa.gov/data/timeseries/month/data/dmi.had.long.data"
SAM_URL = "https://psl.noaa.gov/data/20thC_Rean/timeseries/monthly/SAM/sam.20crv3.long.data"
MJO_URL = "https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt"

REQUIRED = {
    "olr": ("date", "olr"),
    "pdo": ("date", "pdo"),
    "iod": ("date", "dmi"),
    "sam": ("date", "sam"),
    "mjo": ("date", "rmm1", "rmm2", "phase", "amplitude"),
}


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "enso-intelligence/1.0"})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8", errors="replace")
    if not text.strip():
        raise ValueError(f"Empty response from {url}")
    return text


def _parse_monthly_cpc_table(text: str, value_name: str, start_line: int = 0) -> pd.DataFrame:
    rows: list[dict] = []
    months = range(1, 13)
    for raw in text.splitlines()[start_line:]:
        line = raw.strip()
        if not line or not line[:4].isdigit():
            continue
        year = int(line[:4])
        values = [float(match.group(0)) for match in __import__("re").finditer(r"[-+]?\\d+(?:\\.\\d+)?", line[4:])]
        if len(values) < 12:
            continue
        for month in months:
            value = values[month - 1]
            if pd.isna(value) or float(value) <= -999:
                continue
            rows.append({"date": pd.Timestamp(year=year, month=month, day=15), value_name: float(value)})
    if not rows:
        raise ValueError(f"{value_name.upper()} parser returned no observations")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def _parse_psl_standard(text: str, value_name: str) -> pd.DataFrame:
    rows: list[dict] = []
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) != 13 or not parts[0].isdigit():
            continue
        year = int(parts[0])
        try:
            values = [float(value) for value in parts[1:]]
        except ValueError:
            continue
        for month, value in enumerate(values, start=1):
            if value <= -900 or value == 1.0e36:
                continue
            rows.append({"date": pd.Timestamp(year=year, month=month, day=15), value_name: value})
    if not rows:
        raise ValueError(f"{value_name.upper()} PSL parser returned no observations")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def parse_olr(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    anomaly_index = next(
        (i for i, line in enumerate(lines) if "ANOMALY" in line.upper()),
        None,
    )
    if anomaly_index is None:
        raise ValueError("NOAA OLR anomaly section not found")
    return _parse_monthly_cpc_table(text, "olr", anomaly_index + 2)


def parse_psl(text: str, value_name: str) -> pd.DataFrame:
    return _parse_psl_standard(text, value_name)


def parse_mjo(text: str) -> pd.DataFrame:
    rows: list[dict] = []
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) < 7 or not parts[0].isdigit():
            continue
        try:
            year, month, day = map(int, parts[:3])
            rmm1, rmm2 = float(parts[3]), float(parts[4])
            phase = int(parts[5])
            amplitude = float(parts[6])
        except (ValueError, IndexError):
            continue
        if amplitude >= 900 or abs(rmm1) >= 900 or abs(rmm2) >= 900:
            continue
        rows.append(
            {
                "date": pd.Timestamp(year=year, month=month, day=day),
                "rmm1": rmm1,
                "rmm2": rmm2,
                "phase": phase,
                "amplitude": amplitude,
            }
        )
    if not rows:
        raise ValueError("MJO RMM parser returned no observations")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def _meta(dataset: str, source: str, url: str, df: pd.DataFrame, snapshot) -> SeriesMetadata:
    return SeriesMetadata(
        source=source,
        dataset=dataset,
        start=pd.to_datetime(df["date"]).min().to_pydatetime(),
        end=pd.to_datetime(df["date"]).max().to_pydatetime(),
        last_update=pd.to_datetime(snapshot.retrieved_at).to_pydatetime(),
        n_records=snapshot.rows,
        status=DataStatus.UPDATED,
        message=f"Foundation snapshot {snapshot.snapshot_id}",
        url=url,
    )


def _error(dataset: str, source: str, exc: Exception) -> SeriesMetadata:
    return SeriesMetadata(source=source, dataset=dataset, status=DataStatus.ERROR, message=f"Foundation data unavailable: {exc}")


def _read(dataset: str, source: str):
    try:
        df, snapshot = load_latest_snapshot(dataset, REQUIRED[dataset])
        return df, _meta(dataset, source, snapshot.source_url, df, snapshot)
    except (FileNotFoundError, KeyError, ValueError, OSError, pd.errors.ParserError) as exc:
        return None, _error(dataset, source, exc)


def fetch_teleconnections() -> dict[str, tuple[pd.DataFrame | None, SeriesMetadata]]:
    return {
        "mjo": _read("mjo", "Bureau of Meteorology"),
        "olr": _read("olr", "NOAA CPC"),
        "pdo": _read("pdo", "NOAA PSL"),
        "iod": _read("iod", "NOAA PSL"),
        "sam": _read("sam", "NOAA PSL"),
    }


def _fetch_and_parse(url: str, parser, *args):
    return parser(_fetch_text(url), *args)


def ingest_mjo():
    return ingest_and_archive(lambda: _fetch_and_parse(MJO_URL, parse_mjo), dataset="mjo", required_columns=REQUIRED["mjo"])


def ingest_olr():
    return ingest_and_archive(lambda: _fetch_and_parse(OLR_URL, parse_olr), dataset="olr", required_columns=REQUIRED["olr"])


def ingest_pdo():
    return ingest_and_archive(lambda: _fetch_and_parse(PDO_URL, parse_psl, "pdo"), dataset="pdo", required_columns=REQUIRED["pdo"])


def ingest_iod():
    return ingest_and_archive(lambda: _fetch_and_parse(IOD_URL, parse_psl, "dmi"), dataset="iod", required_columns=REQUIRED["iod"])


def ingest_sam():
    return ingest_and_archive(lambda: _fetch_and_parse(SAM_URL, parse_psl, "sam"), dataset="sam", required_columns=REQUIRED["sam"])


__all__ = [
    "fetch_teleconnections",
    "ingest_mjo",
    "ingest_olr",
    "ingest_pdo",
    "ingest_iod",
    "ingest_sam",
    "parse_mjo",
    "parse_olr",
    "parse_psl",
]
