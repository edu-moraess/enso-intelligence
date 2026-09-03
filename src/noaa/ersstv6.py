"""Optional NOAA ERSSTv6 access.

The dashboard does not synthesize spatial data. These helpers expose the real
source when a caller supplies a supported URL or dataset; otherwise they report
that the spatial product is unavailable.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

from src.data.models import DataFetchMeta

SOURCE = "NOAA ERSSTv6"


def fetch_ersst_anomaly_subset(url: str | None = None, timeout: int = 30):
    if not url:
        return None, DataFetchMeta.unavailable(SOURCE, "NOAA ERSSTv6", "No gridded ERSSTv6 endpoint was configured for this deployment.")
    fetched_at = datetime.now(timezone.utc)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        # Do not guess a schema: callers must provide a tabular NOAA export.
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        if df.empty:
            raise ValueError("NOAA returned an empty ERSSTv6 product.")
        return df, DataFetchMeta(SOURCE, url, len(df), fetched_at)
    except (requests.RequestException, ValueError, pd.errors.ParserError) as exc:
        return None, DataFetchMeta.unavailable(SOURCE, url, str(exc))


def get_ersst_status() -> DataFetchMeta:
    return DataFetchMeta.unavailable(SOURCE, "NOAA ERSSTv6", "Spatial data are not configured in the current project.")
