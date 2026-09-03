"""ERSSTv6 access helpers.

Downloads only individual monthly NetCDF files (~170 KB each) from NOAA NCEI.
Never downloads the full multi-decade archive on interactive runs.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

from src.data.models import NOAAConfig, DataStatus, SeriesMetadata, utc_now

logger = logging.getLogger(__name__)

# Equatorial Pacific focus (degrees)
PACIFIC_LAT_MIN, PACIFIC_LAT_MAX = -30.0, 30.0
PACIFIC_LON_MIN, PACIFIC_LON_MAX = 120.0, 290.0  # 120E to 70W in 0-360

# Niño region boxes (lat_min, lat_max, lon_min, lon_max) in 0-360 lon
NINO_BOXES = {
    "Niño 1+2": (-10.0, 0.0, 270.0, 280.0),   # 90W-80W
    "Niño 3": (-5.0, 5.0, 210.0, 270.0),       # 150W-90W
    "Niño 3.4": (-5.0, 5.0, 190.0, 240.0),     # 170W-120W
    "Niño 4": (-5.0, 5.0, 160.0, 210.0),       # 160E-150W
}


def get_ersst_status() -> SeriesMetadata:
    """Return connectivity / availability status for ERSSTv6 without heavy download.

    Probes the NCEI directory listing or a known recent monthly file.
    Does not load the full gridded product into memory on interactive runs.
    """
    meta = SeriesMetadata(
        source="NOAA NCEI / PSL",
        dataset="ERSSTv6 (Extended Reconstructed SST)",
        url=NOAAConfig.ERSST_NCEI_BASE,
        status=DataStatus.UNAVAILABLE,
    )

    # Probe catalog / base URL with a light HEAD or GET
    try:
        # Prefer a small HEAD request to the catalog or base
        resp = requests.head(
            NOAAConfig.ERSST_PSL_CATALOG,
            timeout=NOAAConfig.HTTP_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            # Fallback: try NCEI base
            resp = requests.get(
                NOAAConfig.ERSST_NCEI_BASE,
                timeout=NOAAConfig.HTTP_TIMEOUT,
            )
        if resp.status_code < 400:
            meta.status = DataStatus.CONNECTED
            meta.message = (
                "ERSSTv6 endpoints reachable. "
                "Full spatial maps are not loaded in this observational build; "
                "see Methodology / Limitations."
            )
            meta.last_update = utc_now()
        else:
            meta.status = DataStatus.WARNING
            meta.message = f"ERSSTv6 probe returned HTTP {resp.status_code}"
    except requests.RequestException as exc:
        logger.warning("ERSSTv6 status probe failed: %s", exc)
        meta.status = DataStatus.ERROR
        meta.message = f"ERSSTv6 unavailable: {exc}"

    return meta


def list_available_months(
    year: Optional[int] = None,
    timeout: int = NOAAConfig.HTTP_TIMEOUT,
) -> List[str]:
    """Best-effort listing of available monthly files (year filter optional).

    Returns empty list on failure — never fabricates filenames.
    """
    try:
        resp = requests.get(NOAAConfig.ERSST_NCEI_BASE, timeout=timeout)
        resp.raise_for_status()
        # Very light scrape of hrefs that look like ersst.v6.*.nc
        import re
        names = re.findall(r"ersst\.v6\.\d{6}\.nc", resp.text, flags=re.IGNORECASE)
        names = sorted(set(names))
        if year is not None:
            y = str(int(year))
            names = [n for n in names if y in n]
        return names
    except Exception as exc:
        logger.warning("ERSSTv6 listing failed: %s", exc)
        return []


# Optional future expansion (not used by the one-page observatory):
# individual monthly NetCDF fetch + regional mean over Niño boxes.
# Kept minimal so interactive Streamlit runs stay light and honest about
# spatial SST limitations (see app Methodology section).
