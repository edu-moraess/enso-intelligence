"""CHIRPS v3 monthly GeoTIFF inspection and external catalog.

Raster files remain in user-controlled storage. This module registers only
metadata and checksums; it never copies large rasters into the Git repository.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .contracts import Provenance

CHIRPS_V3_MONTHLY_LATAM_URL = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/latam/tifs/"
)
_FILENAME = re.compile(r"^chirps-v3\.0\.(\d{4})\.(\d{2})\.tif$")


@dataclass(frozen=True)
class ChirpsRasterMetadata:
    """Validated spatial and statistical metadata for one monthly raster."""
    period: str
    filename: str
    source_url: str
    width: int
    height: int
    band_count: int
    crs: str
    bounds: dict[str, float]
    resolution: tuple[float, float]
    dtype: str
    nodata_value: float
    total_pixels: int
    valid_pixels: int
    nodata_pixels: int
    valid_coverage_pct: float
    minimum_mm: float
    maximum_mm: float
    mean_mm: float
    provenance: Provenance


def _validate_period(period: str) -> None:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
        raise ValueError("period must use YYYY-MM format")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_chirps_raster(
    path: str | Path,
    *,
    period: str,
    nodata_fallback: float = -9999.0,
    expected_crs: str = "EPSG:4326",
    expected_resolution: float = 0.05,
) -> ChirpsRasterMetadata:
    """Inspect one local CHIRPS v3 monthly Latin America GeoTIFF.

    nodata_fallback is explicit because the pilot encountered files where the
    -9999 sentinel existed although GeoTIFF nodata metadata was absent.
    """
    _validate_period(period)
    raster_path = Path(path)
    if not raster_path.is_file():
        raise FileNotFoundError(f"CHIRPS raster not found: {raster_path}")
    match = _FILENAME.fullmatch(raster_path.name)
    if not match or f"{match.group(1)}-{match.group(2)}" != period:
        raise ValueError(
            "filename must match chirps-v3.0.YYYY.MM.tif and the requested period"
        )

    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        raise RuntimeError(
            "CHIRPS GeoTIFF inspection requires optional dependency: pip install rasterio"
        ) from exc

    if not math.isfinite(nodata_fallback):
        raise ValueError("nodata_fallback must be finite")
    if not math.isfinite(expected_resolution) or expected_resolution <= 0:
        raise ValueError("expected_resolution must be a positive finite number")

    digest = _sha256(raster_path)
    with rasterio.open(raster_path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"expected one raster band, received {dataset.count}")
        if dataset.crs is None or dataset.crs.to_string() != expected_crs:
            raise ValueError(
                f"unexpected CRS: expected {expected_crs}, received {dataset.crs}"
            )
        if dataset.width <= 0 or dataset.height <= 0:
            raise ValueError("raster dimensions must be positive")

        xres, yres = dataset.res
        if (
            not math.isclose(abs(xres), expected_resolution, abs_tol=1e-6)
            or not math.isclose(abs(yres), expected_resolution, abs_tol=1e-6)
        ):
            raise ValueError(
                f"unexpected raster resolution: expected {expected_resolution}, "
                f"received {dataset.res}"
            )

        nodata = dataset.nodata
        if nodata is None:
            nodata = nodata_fallback

        total_pixels = dataset.width * dataset.height
        valid_pixels = 0
        minimum = math.inf
        maximum = -math.inf
        total = 0.0

        for _, window in dataset.block_windows(1):
            values = dataset.read(1, window=window, masked=False)
            valid_mask = np.isfinite(values)
            if math.isnan(float(nodata)):
                valid_mask &= ~np.isnan(values)
            else:
                valid_mask &= values != nodata
            valid = values[valid_mask].astype("float64", copy=False)
            if valid.size == 0:
                continue
            if np.any(valid < 0):
                raise ValueError("CHIRPS precipitation raster contains negative values")
            valid_pixels += int(valid.size)
            minimum = min(minimum, float(valid.min()))
            maximum = max(maximum, float(valid.max()))
            total += float(valid.sum(dtype="float64"))

        if valid_pixels == 0:
            raise ValueError("CHIRPS raster contains no valid precipitation pixels")

        bounds = dataset.bounds
        provenance = Provenance(
            source="Climate Hazards Center (CHC)",
            dataset="chirps-v3-monthly-latam",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            source_version="v3.0",
            sha256=digest,
            validation_status="verified",
        )
        return ChirpsRasterMetadata(
            period=period,
            filename=raster_path.name,
            source_url=CHIRPS_V3_MONTHLY_LATAM_URL + raster_path.name,
            width=dataset.width,
            height=dataset.height,
            band_count=dataset.count,
            crs=dataset.crs.to_string(),
            bounds={
                "west": float(bounds.left),
                "south": float(bounds.bottom),
                "east": float(bounds.right),
                "north": float(bounds.top),
            },
            resolution=(float(xres), float(yres)),
            dtype=str(dataset.dtypes[0]),
            nodata_value=float(nodata),
            total_pixels=total_pixels,
            valid_pixels=valid_pixels,
            nodata_pixels=total_pixels - valid_pixels,
            valid_coverage_pct=100.0 * valid_pixels / total_pixels,
            minimum_mm=minimum,
            maximum_mm=maximum,
            mean_mm=total / valid_pixels,
            provenance=provenance,
        )


def register_chirps_raster(
    path: str | Path,
    *,
    period: str,
    catalog_root: str | Path,
    nodata_fallback: float = -9999.0,
) -> ChirpsRasterMetadata:
    """Validate a raster and append metadata to an external JSONL catalog.

    Re-registering the same period and checksum is idempotent. A changed
    checksum is retained as a new event rather than overwriting provenance.
    """
    metadata = inspect_chirps_raster(
        path, period=period, nodata_fallback=nodata_fallback
    )
    catalog_dir = Path(catalog_root)
    catalog_dir.mkdir(parents=True, exist_ok=True)
    manifest = catalog_dir / "chirps_v3_monthly_latam.jsonl"
    existing = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if manifest.exists() else []

    fingerprint = metadata.provenance.sha256
    if any(
        item.get("period") == period
        and item.get("provenance", {}).get("sha256") == fingerprint
        for item in existing
    ):
        return metadata

    with manifest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(metadata), sort_keys=True) + "\n")
    return metadata
