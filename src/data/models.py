"""Central configuration and data models for ENSO Intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DataStatus(str, Enum):
    CONNECTED = "Connected"
    UPDATED = "Updated"
    WARNING = "Warning"
    ERROR = "Error"
    UNAVAILABLE = "Unavailable"


@dataclass(frozen=True)
class NOAAConfig:
    """Centralized NOAA data source endpoints."""

    # RONI (official operational index since 2026)
    RONI_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
    RONI_PAGE: str = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/"

    # ONI (complementary / historical)
    ONI_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

    # Weekly Niño region SST / SSTA — OISST.v2.1, 1991–2020 base period
    # NOTE: wksst8110.for (1981–2010 base) stopped updating ~Jan 2021.
    # The operational weekly product is wksst9120.for.
    WEEKLY_NINO_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for"
    MONTHLY_NINO_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices"

    # Outlook / probabilities pages
    RONI_OUTLOOK_URL: str = (
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/outlook/"
    )
    RONI_PROBABILITIES_URL: str = (
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities/"
    )
    RONI_PROBABILITIES_PHP: str = (
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities.php"
    )

    # ERSSTv6 (PSL / NCEI)
    ERSST_PSL_CATALOG: str = (
        "https://psl.noaa.gov/thredds/catalog/Datasets/noaa.ersst.v6/catalog.html"
    )
    ERSST_NCEI_BASE: str = (
        "https://www.ncei.noaa.gov/data/sea-surface-temperature-extended-reconstructed/v6/access/"
    )

    HTTP_TIMEOUT: int = 30
    MAX_RETRIES: int = 2


@dataclass
class SeriesMetadata:
    """Metadata describing a loaded time series."""

    source: str
    dataset: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    last_update: Optional[datetime] = None
    n_records: int = 0
    status: DataStatus = DataStatus.UNAVAILABLE
    message: str = ""
    url: str = ""


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Classification thresholds
# ---------------------------------------------------------------------------
# Phase (NOAA operational definition for RONI/ONI):
#   El Niño  : index >= +0.5 °C
#   La Niña  : index <= -0.5 °C
#   Neutral  : otherwise
#
# Magnitude bands below are aligned with the NOAA CPC strength thresholds
# used for RONI communication. They describe index magnitude; they do not
# by themselves constitute an official event declaration.
# Half-open intervals: [low, high)
#   Weak         : [0.5, 1.0)
#   Moderate     : [1.0, 1.5)
#   Strong       : [1.5, 2.0)
#   Very Strong  : [2.0, +∞)
THRESHOLD_EL_NINO = 0.5
THRESHOLD_LA_NINA = -0.5

INTENSITY_BOUNDS = {
    "Weak": (0.5, 1.0),
    "Moderate": (1.0, 1.5),
    "Strong": (1.5, 2.0),
    "Very Strong": (2.0, float("inf")),
}
