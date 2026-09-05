"""NOAA PSL GODAS ocean-state features for ENSO modeling.

This module is intentionally ingestion-first: it retrieves real GODAS data,
computes D20 from the 20 C isotherm, and never fabricates missing observations.
Temporal training remains blocked until an explicit ``available_at`` mapping is
attached by the availability policy layer.
"""

from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd

GODAS_BASE_URL: Final[str] = "https://psl.noaa.gov/thredds/dodsC/Datasets/godas"
GODAS_TEMPERATURE_VARIABLE: Final[str] = "pottmp"

# Equatorial Pacific envelope used for the first physical-state feature.
# Longitudes are expressed in the 0..360 convention used by GODAS.
LAT_MIN: Final[float] = -5.0
LAT_MAX: Final[float] = 5.0
LON_MIN: Final[float] = 170.0
LON_MAX: Final[float] = 280.0
DEPTH_MAX_M: Final[float] = 300.0
TARGET_ISOTHERM_C: Final[float] = 20.0


def godas_temperature_url(year: int) -> str:
    """Return the official NOAA PSL GODAS monthly temperature endpoint."""
    if year < 1980 or year > 2100:
        raise ValueError("year must be a plausible GODAS year")
    return f"{GODAS_BASE_URL}/pottmp.{year}.nc"


def _d20_from_profile(depth_m: np.ndarray, temperature_c: np.ndarray) -> float:
    """Estimate the depth of the 20 C isotherm by vertical interpolation.

    GODAS does not expose a native 20 m level in the temperature grid; the
    isotherm is therefore located between adjacent model levels. Profiles that
    never cross 20 C are returned as NaN rather than extrapolated.
    """
    depth = np.asarray(depth_m, dtype=float)
    temp = np.asarray(temperature_c, dtype=float)
    valid = np.isfinite(depth) & np.isfinite(temp)
    depth = depth[valid]
    temp = temp[valid]
    if depth.size < 2:
        return float("nan")

    order = np.argsort(depth)
    depth = depth[order]
    temp = temp[order]

    for i in range(depth.size - 1):
        t0, t1 = temp[i], temp[i + 1]
        if (t0 - TARGET_ISOTHERM_C) == 0:
            return float(depth[i])
        if (t0 - TARGET_ISOTHERM_C) * (t1 - TARGET_ISOTHERM_C) <= 0:
            if t1 == t0:
                return float(depth[i])
            fraction = (TARGET_ISOTHERM_C - t0) / (t1 - t0)
            return float(depth[i] + fraction * (depth[i + 1] - depth[i]))
    return float("nan")


def open_godas_temperature(year: int):
    """Open one official GODAS temperature year lazily through OPeNDAP.

    ``xarray`` and a NetCDF backend are imported only when this function is
    called, keeping the rest of the package importable without them.
    """
    try:
        import xarray as xr
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "GODAS ingestion requires xarray and a NetCDF backend."
        ) from exc

    ds = xr.open_dataset(godas_temperature_url(year), decode_times=True)
    required = {"lat", "lon", "level", GODAS_TEMPERATURE_VARIABLE}
    missing = required.difference(ds.variables)
    if missing:
        ds.close()
        raise ValueError(f"GODAS dataset missing required variables: {sorted(missing)}")

    return ds[[GODAS_TEMPERATURE_VARIABLE]].sel(
        lat=slice(LAT_MIN, LAT_MAX),
        lon=slice(LON_MIN, LON_MAX),
        level=slice(0, DEPTH_MAX_M),
    )


def monthly_d20_feature(ds) -> pd.DataFrame:
    """Compute monthly equatorial-Pacific mean D20 from an opened GODAS dataset.

    The spatial mean is computed after finding D20 at each grid-cell profile;
    no spatial or temporal interpolation is used to manufacture missing data.
    """
    temp = ds[GODAS_TEMPERATURE_VARIABLE]
    if not {"time", "level", "lat", "lon"}.issubset(temp.dims):
        raise ValueError("GODAS temperature must have time/level/lat/lon dimensions")

    depth = np.asarray(ds["level"].values, dtype=float)
    if np.nanmax(depth) <= 0:
        raise ValueError("GODAS depth levels are invalid")

    rows: list[dict[str, object]] = []
    times = pd.to_datetime(ds["time"].values, utc=True)
    values = np.asarray(temp.values, dtype=float)

    # Expected shape: time x level x lat x lon.
    if values.ndim != 4:
        raise ValueError("GODAS temperature must be a 4-D monthly field")

    values = np.where(values < -1e20, np.nan, values)
    for t_index, timestamp in enumerate(times):
        profiles = values[t_index]
        d20_grid = np.full(profiles.shape[1:], np.nan, dtype=float)
        for lat_index in range(profiles.shape[1]):
            for lon_index in range(profiles.shape[2]):
                d20_grid[lat_index, lon_index] = _d20_from_profile(
                    depth, profiles[:, lat_index, lon_index]
                )
        valid = d20_grid[np.isfinite(d20_grid)]
        rows.append(
            {
                "date": timestamp,
                "d20_m": float(valid.mean()) if valid.size else np.nan,
                "source": "NOAA PSL GODAS",
                "dataset": "godas",
            }
        )

    return pd.DataFrame(rows)


def add_d20_anomaly_and_trend(
    monthly: pd.DataFrame,
    climatology_start: str = "1991-01-01",
    climatology_end: str = "2020-12-31",
) -> pd.DataFrame:
    """Add calendar-month D20 anomaly and a 3-month change signal."""
    required = {"date", "d20_m"}
    missing = required.difference(monthly.columns)
    if missing:
        raise ValueError(f"D20 table missing columns: {sorted(missing)}")

    out = monthly.copy()
    out["date"] = pd.to_datetime(out["date"], utc=True)
    out = out.sort_values("date").reset_index(drop=True)
    baseline = out["date"].between(climatology_start, climatology_end)
    clim = out.loc[baseline].groupby(out.loc[baseline, "date"].dt.month)["d20_m"].mean()
    out["d20_climatology_m"] = out["date"].dt.month.map(clim)
    out["d20_anomaly_m"] = out["d20_m"] - out["d20_climatology_m"]
    out["d20_trend_3m_m"] = out["d20_m"].diff(3)
    return out
