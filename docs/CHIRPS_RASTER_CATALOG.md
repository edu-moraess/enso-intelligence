# CHIRPS v3 raster catalog adapter

The adapter validates local monthly CHIRPS v3 Latin America GeoTIFF files and
registers their metadata in an external JSONL catalog.

## Storage policy

- Keep GeoTIFF files in Colab Drive, another mounted volume, or object storage.
- Do not commit raster binaries to Git.
- The catalog stores period, source URL, CRS, bounds, resolution, dimensions,
  NoData accounting, basic precipitation statistics and SHA-256 provenance.
- A changed checksum for an existing month is retained as a new catalog event.
- This adapter does not download data automatically or convert monthly totals
  into anomalies.

## Requirements

Install the optional GeoTIFF dependency in the execution environment:

    pip install rasterio

## Colab example

    from src.data.chirps import register_chirps_raster

    metadata = register_chirps_raster(
        "/content/chirps-v3.0.2026.08.tif",
        period="2026-08",
        catalog_root="/content/enso_chirps_catalog",
    )

    print(metadata)

The catalog is written to
/content/enso_chirps_catalog/chirps_v3_monthly_latam.jsonl. The adapter
uses -9999 as an explicit fallback NoData sentinel only when the GeoTIFF does
not declare NoData metadata. This reflects the observed pilot-file condition;
it is configurable and must be checked against the source file.

## Current scope

This is a local-file inspection and catalog registration layer. It does not
download the 549-month historical inventory, persist pixels in the tabular
Foundation, calculate a 1991-2020 climatology, or claim that the entire series
has been validated. Those are subsequent controlled steps.
