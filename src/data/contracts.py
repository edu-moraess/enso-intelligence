"""Versioned, dependency-free contracts for environmental and geospatial data.

These contracts are intended as the stable exchange boundary between E.N.S.O,
MIE, and Vyra. They describe observations and provenance; they do not encode
any one application's internal models or imply that a source was validated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import math
import re
from typing import Any


SCHEMA_VERSION = "1.0"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_timestamp(name: str, value: str) -> None:
    _require_text(name, value)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone offset")


def _require_optional_number(name: str, value: float | None) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number or None")


@dataclass(frozen=True)
class GeoReference:
    """Point location in a declared coordinate reference system."""

    latitude: float
    longitude: float
    crs: str = "EPSG:4326"

    def __post_init__(self) -> None:
        _require_optional_number("latitude", self.latitude)
        _require_optional_number("longitude", self.longitude)
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        _require_text("crs", self.crs)


@dataclass(frozen=True)
class Provenance:
    """Traceable origin and integrity metadata for a source artifact."""

    source: str
    dataset: str
    retrieved_at: str
    source_version: str | None = None
    sha256: str | None = None
    validation_status: str = "unverified"

    def __post_init__(self) -> None:
        _require_text("source", self.source)
        _require_text("dataset", self.dataset)
        _require_timestamp("retrieved_at", self.retrieved_at)
        _require_text("validation_status", self.validation_status)
        if self.source_version is not None:
            _require_text("source_version", self.source_version)
        if self.sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", self.sha256):
            raise ValueError("sha256 must contain exactly 64 hexadecimal characters")


@dataclass(frozen=True)
class Observation:
    """A single measured value, distinct from derived environmental context."""

    variable: str
    value: float
    unit: str
    measured_at: str
    source: str
    geo_reference: GeoReference | None = None
    provenance: Provenance | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text("variable", self.variable)
        _require_optional_number("value", self.value)
        _require_text("unit", self.unit)
        _require_timestamp("measured_at", self.measured_at)
        _require_text("source", self.source)
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")


@dataclass(frozen=True)
class EnvironmentalCondition:
    """Environmental state at a location and observation time.

    All measurements are optional because different sensors and datasets
    provide different subsets. Units are fixed by field names to avoid
    ambiguity across producers.
    """

    observed_at: str
    provenance: Provenance
    geo_reference: GeoReference | None = None
    precipitation_mm: float | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_timestamp("observed_at", self.observed_at)
        if not isinstance(self.provenance, Provenance):
            raise ValueError("provenance must be a Provenance instance")
        for field_name in (
            "precipitation_mm", "temperature_c", "humidity_pct", "wind_speed_ms"
        ):
            _require_optional_number(field_name, getattr(self, field_name))
        if self.precipitation_mm is not None and self.precipitation_mm < 0:
            raise ValueError("precipitation_mm cannot be negative")
        if self.humidity_pct is not None and not 0 <= self.humidity_pct <= 100:
            raise ValueError("humidity_pct must be between 0 and 100")
        if self.wind_speed_ms is not None and self.wind_speed_ms < 0:
            raise ValueError("wind_speed_ms cannot be negative")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")


def contract_to_dict(value: Any) -> dict[str, Any]:
    """Convert a contract dataclass into a JSON-compatible dictionary."""
    if not hasattr(value, "__dataclass_fields__"):
        raise TypeError("value must be a contract dataclass")
    return asdict(value)


def contract_to_json(value: Any) -> str:
    """Serialize a contract using deterministic key ordering."""
    return json.dumps(contract_to_dict(value), sort_keys=True, separators=(",", ":"))
