"""Tests for the optional CHIRPS GeoTIFF catalog adapter."""
import json
import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_origin

from src.data.chirps import inspect_chirps_raster, register_chirps_raster


def write_raster(path, values, nodata=None):
    height, width = values.shape
    with rasterio.open(
        path, "w", driver="GTiff", height=height, width=width,
        count=1, dtype="float32", crs="EPSG:4326",
        transform=from_origin(-50.0, 10.0, 0.05, 0.05), nodata=nodata,
    ) as dst:
        dst.write(values.astype("float32"), 1)


def test_inspect_chirps_uses_explicit_nodata_fallback(tmp_path):
    path = tmp_path / "chirps-v3.0.2026.08.tif"
    values = np.array([[10.0, 20.0], [30.0, -9999.0]], dtype="float32")
    write_raster(path, values, nodata=None)

    metadata = inspect_chirps_raster(path, period="2026-08")

    assert metadata.crs == "EPSG:4326"
    assert metadata.total_pixels == 4
    assert metadata.valid_pixels == 3
    assert metadata.nodata_pixels == 1
    assert metadata.valid_coverage_pct == 75.0
    assert metadata.mean_mm == 20.0
    assert metadata.provenance.sha256


def test_inspect_chirps_rejects_filename_period_mismatch(tmp_path):
    path = tmp_path / "chirps-v3.0.2026.08.tif"
    write_raster(path, np.ones((2, 2), dtype="float32"))
    with pytest.raises(ValueError, match="requested period"):
        inspect_chirps_raster(path, period="2026-07")


def test_inspect_chirps_rejects_negative_precipitation(tmp_path):
    path = tmp_path / "chirps-v3.0.2026.08.tif"
    values = np.array([[1.0, -2.0], [3.0, 4.0]], dtype="float32")
    write_raster(path, values)
    with pytest.raises(ValueError, match="negative values"):
        inspect_chirps_raster(path, period="2026-08")


def test_register_chirps_catalog_is_idempotent(tmp_path):
    path = tmp_path / "chirps-v3.0.2026.08.tif"
    values = np.array([[1.0, 2.0], [3.0, -9999.0]], dtype="float32")
    write_raster(path, values)
    catalog = tmp_path / "catalog"

    register_chirps_raster(path, period="2026-08", catalog_root=catalog)
    register_chirps_raster(path, period="2026-08", catalog_root=catalog)

    manifest = catalog / "chirps_v3_monthly_latam.jsonl"
    entries = [json.loads(line) for line in manifest.read_text().splitlines()]
    assert len(entries) == 1
    assert entries[0]["period"] == "2026-08"
