"""Shared data models for NOAA-backed ENSO streams."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class NOAAConfig:
    """Endpoint and timeout configuration for a NOAA product."""
    timeout_seconds: int = 20
    user_agent: str = "ENSO-Intelligence/1.0"


@dataclass(frozen=True)
class DataStatus:
    """Simple availability status retained for compatibility with the project API."""
    available: bool
    message: str | None = None


@dataclass(frozen=True)
class SeriesMetadata:
    """Descriptive metadata for an observed climate series."""
    name: str
    source: str = "NOAA"
    frequency: str | None = None
    units: str | None = "°C"
    reference_period: str | None = None


@dataclass(frozen=True)
class DataFetchMeta:
    """Operational metadata for a single NOAA request."""
    source: str
    endpoint: str
    n_records: int = 0
    fetched_at: datetime | None = None
    status: str = "ok"
    message: str | None = None

    @classmethod
    def unavailable(cls, source: str, endpoint: str, message: str) -> "DataFetchMeta":
        return cls(source=source, endpoint=endpoint, status="unavailable", message=message, fetched_at=datetime.now(timezone.utc))


__all__ = ["NOAAConfig", "DataStatus", "SeriesMetadata", "DataFetchMeta"]
