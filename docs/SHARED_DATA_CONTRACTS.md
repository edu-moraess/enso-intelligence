# Shared Data Contracts

Versioned exchange contracts for the ArqTech Labs ecosystem.

- **E.N.S.O Intelligence** produces climate and environmental observations.
- **MIE** can consume environmental context alongside maritime observations.
- **Vyra** can align environmental context with sensor, scene, and trajectory data.

The projects remain independently deployable. These contracts define a common
data boundary; they do not create a runtime dependency between repositories.

## Contracts in schema 1.0

| Contract | Purpose |
|---|---|
| `Observation` | A single measured variable, value, unit, observation time and source |
| `GeoReference` | Latitude, longitude and explicit CRS (defaults to EPSG:4326) |
| `EnvironmentalCondition` | Optional precipitation, temperature, humidity and wind at a time/location |
| `Provenance` | Source, dataset, retrieval timestamp, optional version/hash and validation status |

All timestamps must be ISO-8601 with an explicit timezone. Missing sensor values
remain `null`; producers must not fabricate values or silently convert units.
Precipitation is millimetres for the represented period, temperature is degrees
Celsius, humidity is percent, and wind speed is metres per second.

## Example: CHIRPS-derived environmental condition

This is an illustrative payload, not a live observation or a claim that the
CHIRPS series has already been ingested into the Foundation.

```json
{
  "schema_version": "1.0",
  "observed_at": "2026-08-01T00:00:00Z",
  "geo_reference": {
    "latitude": -23.55,
    "longitude": -46.63,
    "crs": "EPSG:4326"
  },
  "precipitation_mm": 67.6,
  "temperature_c": null,
  "humidity_pct": null,
  "wind_speed_ms": null,
  "provenance": {
    "source": "CHIRPS",
    "dataset": "chirps-v3-monthly-latam",
    "retrieved_at": "2026-11-10T00:00:00Z",
    "source_version": "v3.0",
    "sha256": null,
    "validation_status": "pilot"
  }
}
```

## Compatibility rules

1. Add optional fields in a minor schema revision.
2. Do not change units or field meaning in-place; introduce a new schema version.
3. Preserve source timestamps and distinguish observation time from retrieval time.
4. Keep large rasters, model weights and other binary assets in object storage;
   exchange references, checksums, spatial metadata and summaries.
5. A status such as `verified` must be assigned only after the producer's
   validation process has actually passed.

Python implementation: `src/data/contracts.py`.
