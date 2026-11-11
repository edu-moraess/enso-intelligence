"""Tests for the shared geospatial and environmental contracts."""

import json

import pytest

from src.data.contracts import (
    EnvironmentalCondition,
    GeoReference,
    Observation,
    Provenance,
    contract_to_dict,
    contract_to_json,
)


def provenance():
    return Provenance(
        source="CHIRPS",
        dataset="chirps-v3-monthly-latam",
        retrieved_at="2026-11-10T00:00:00Z",
        sha256="a" * 64,
        validation_status="verified",
    )


def test_georeference_accepts_wgs84_coordinates():
    location = GeoReference(latitude=-23.55, longitude=-46.63)
    assert location.crs == "EPSG:4326"


@pytest.mark.parametrize(
    "latitude,longitude",
    [(91, 0), (-91, 0), (0, 181), (0, -181)],
)
def test_georeference_rejects_out_of_range_coordinates(latitude, longitude):
    with pytest.raises(ValueError):
        GeoReference(latitude=latitude, longitude=longitude)


def test_provenance_requires_timezone_aware_retrieval_time():
    with pytest.raises(ValueError, match="timezone"):
        Provenance(
            source="NOAA",
            dataset="oni",
            retrieved_at="2026-11-10T00:00:00",
        )


def test_provenance_rejects_invalid_sha256():
    with pytest.raises(ValueError, match="64 hexadecimal"):
        Provenance(
            source="NOAA",
            dataset="oni",
            retrieved_at="2026-11-10T00:00:00Z",
            sha256="not-a-hash",
        )


def test_observation_serializes_as_json_compatible_contract():
    item = Observation(
        variable="precipitation",
        value=67.6,
        unit="mm/month",
        measured_at="2026-08-01T00:00:00Z",
        source="CHIRPS",
        geo_reference=GeoReference(-23.55, -46.63),
        provenance=provenance(),
    )
    payload = contract_to_dict(item)
    assert payload["schema_version"] == "1.0"
    assert payload["geo_reference"]["crs"] == "EPSG:4326"
    assert json.loads(contract_to_json(item))["value"] == 67.6


def test_environmental_condition_accepts_partial_sensor_coverage():
    item = EnvironmentalCondition(
        observed_at="2026-08-01T00:00:00Z",
        provenance=provenance(),
        precipitation_mm=67.6,
    )
    payload = contract_to_dict(item)
    assert payload["precipitation_mm"] == 67.6
    assert payload["temperature_c"] is None
    assert payload["geo_reference"] is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"precipitation_mm": -0.1},
        {"humidity_pct": 100.1},
        {"humidity_pct": -0.1},
        {"wind_speed_ms": -1.0},
        {"temperature_c": float("nan")},
    ],
)
def test_environmental_condition_rejects_invalid_measurements(kwargs):
    with pytest.raises(ValueError):
        EnvironmentalCondition(
            observed_at="2026-08-01T00:00:00Z",
            provenance=provenance(),
            **kwargs,
        )


def test_contract_rejects_unsupported_schema_version():
    with pytest.raises(ValueError, match="unsupported schema_version"):
        Observation(
            variable="sst",
            value=28.1,
            unit="degC",
            measured_at="2026-08-01T00:00:00Z",
            source="NOAA",
            schema_version="2.0",
        )
