# ENSO Intelligence

**Scientific Climate Observatory for the El Niño–Southern Oscillation**

Operational monitoring and scientific analysis of observed ENSO conditions using official NOAA climate products, transparent methods and reproducible processing.

> **UX:** Single-page vertical observatory (`streamlit run app.py`). Sidebar = Settings only. No multi-page navigation.

---

## Motivation

Provide a research-grade interface to:

1. retrieve official NOAA ENSO indices;
2. classify observed ENSO phase and communicate intensity;
3. document methodology, provenance and limitations;
4. support portfolio, academic demonstration and future TCC-oriented expansion.

## Scientific scope

| In scope | Out of scope (this version) |
|----------|------------------------------|
| Observational RONI / ONI / Niño indices | Seasonal forecast models |
| Phase classification (±0.5 °C) | Synthetic or fallback climate data |
| Observational trend metrics | Gridded SST maps without validated load |
| Historical episode detection from series | Quantitative Brazil impact scores |
| Qualitative teleconnection education | NDVI / agricultural models |

## Data sources

| Product | Role | Endpoint |
|---------|------|----------|
| **RONI** | Primary operational index | `cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt` |
| **ONI** | Complementary / historical | `.../oni.ascii.txt` |
| Weekly Niño | Regional weekly SSTA | `.../wksst9120.for` |
| Monthly Niño | Regional monthly SSTA | `.../sstoi.indices` |
| ERSSTv6 | Status / optional monthly fields | NOAA NCEI |

## Methodology (summary)

```
NOAA products → acquisition → parsing → validation
→ indicator processing → classification → visualization
```

- **Phase:** RONI ≥ +0.5 °C → El Niño; ≤ −0.5 °C → La Niña; else Neutral (NOAA operational thresholds).
- **Intensity:** project magnitude bands (Weak / Moderate / Strong / Very Strong) — documented, not an official NOAA categorical product.
- **Events:** ≥ 5 consecutive seasons beyond threshold on the real RONI series.
- **Trends:** observational deltas and OLS slope on recent seasons — not forecasts.

**Data integrity policy.** Observations come from official NOAA products. Unavailable observations are not replaced with synthetic, mocked or fallback climate values.

## Architecture

```
app.py                 # Single-page Streamlit observatory
src/noaa/              # RONI, ONI, Niño, ERSST access
src/analysis/          # Classification, trends, events
src/data/              # Config, thresholds, metadata
src/ui/                # Theme and components
tests/                 # Offline unit tests
pages_archive/         # Legacy multipage modules (not loaded)
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Testing

```bash
python -m compileall -q .
pytest -q
```

## Limitations

- Observational only — not a forecasting system.
- Intensity bands are a project convention.
- No validated gridded Pacific anomaly map is required for core operation.
- Brazil section is educational; no regional meteorological dataset is ingested.
- Weekly and seasonal indices are different summaries and may disagree.

## Future research

Statistical teleconnections, precipitation/temperature composites, agricultural indicators, multivariate indices, and a **separate** forecast module with explicit uncertainty — all requiring documented methods and no synthetic observational fill.

## Licence & attribution

Climate data © NOAA. Cite original NOAA CPC / NCEI products when publishing results derived from this software.
