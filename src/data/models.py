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

    RONI_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
    RONI_PAGE: str = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/"
    ONI_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    WEEKLY_NINO_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for"
    MONTHLY_NINO_URL: str = "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices"
    RONI_OUTLOOK_URL: str = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/outlook/"
    RONI_PROBABILITIES_URL: str = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities/"
    RONI_PROBABILITIES_PHP: str = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities.php"
    ERSST_PSL_CATALOG: str = "https://psl.noaa.gov/thredds/catalog/Datasets/noaa.ersst.v6/catalog.html"
    ERSST_NCEI_BASE: str = "https://www.ncei.noaa.gov/data/sea-surface-temperature-extended-reconstructed/v6/access/"
    HTTP_TIMEOUT: int = 30
    MAX_RETRIES: int = 2


@dataclass
class SeriesMetadata:
    """Metadata describing a loaded time series.

    ``available_at`` is deliberately separate from retrieval/update metadata
    and must only be populated after an authoritative information-time mapping
    has been established.
    """

    source: str
    dataset: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    last_update: Optional[datetime] = None
    available_at: Optional[datetime] = None
    availability_method: Optional[str] = None
    availability_evidence: Optional[str] = None
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
THRESHOLD_EL_NINO = 0.5
THRESHOLD_LA_NINA = -0.5

INTENSITY_BOUNDS = {
    "Weak": (0.5, 1.0),
    "Moderate": (1.0, 1.5),
    "Strong": (1.5, 2.0),
    "Very Strong": (2.0, float("inf")),
}
