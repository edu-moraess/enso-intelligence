# E.N.S.O — Operational ENSO Intelligence

**Operational monitoring of the El Niño–Southern Oscillation using official NOAA climate products.**

E.N.S.O is a focused, single-page climate intelligence observatory that turns official NOAA CPC ENSO products into a compact and traceable view of the current regime, recent evolution, historical context, and Pacific conditions.

> **Product principle:** observe first, interpret clearly, document the source. E.N.S.O is an observational intelligence product — not a forecasting system.

## What it answers

1. **What is the current ENSO state?**
2. **How strong is the current signal?**
3. **Is the signal strengthening or weakening?**
4. **Which historical RONI trajectories look similar?**
5. **What are the latest conditions across the Niño regions?**

## Observatory view

| Section | Purpose |
|---|---|
| **Current Conditions** | Current ENSO state, intensity, latest RONI and recent change |
| **ENSO Signal** | Historical RONI trajectory and operational thresholds |
| **Historical Analogues** | Descriptive trajectory similarity against historical RONI windows |
| **ENSO Regime Timeline** | Historical non-neutral episodes detected from the RONI series |
| **Pacific Conditions** | Weekly SST anomalies across Niño 1+2, 3, 3.4 and 4 |
| **Analytical View** | RONI vs ONI and concise climate context |
| **Methodology** | Processing logic and scientific guardrails |
| **Data & Provenance** | Products, sources and data-integrity policy |

## Data provenance

E.N.S.O uses three official NOAA CPC products as its current Foundation datasets:

| Product | Role | Source |
|---|---|---|
| **RONI** | Primary operational ENSO signal | NOAA CPC — `RONI.ascii.txt` |
| **ONI** | Complementary reference | NOAA CPC — `oni.ascii.txt` |
| **Weekly Niño indices** | Latest regional Pacific SST anomalies | NOAA CPC — `wksst9120.for` |

The application reads the latest validated canonical snapshots from the repository Data Foundation. It does not use synthetic, mocked, or silent fallback climate observations.

## Data Foundation

```text
NOAA CPC
   ↓
External Cloudflare Cron Worker
   ↓
Canonicalization + validation
   ↓
Content-addressed snapshots
   ↓
GitHub repository via API
   ↓
Streamlit observatory
```

The foundation provides:

- **Ingestion:** repeatable acquisition of live RONI, ONI and weekly Niño products.
- **Canonical dataset:** stable fields and chronological ordering before downstream analysis.
- **Validation:** required columns, dates, duplicates and numeric observations are checked before a snapshot is accepted.
- **Versioning:** snapshots are identified by a SHA-256 content hash, so revisions create immutable snapshots rather than silently overwriting observations.
- **Provenance:** each snapshot records dataset, source, source URL, retrieval time, row count and validation result.

The durable refresh runs outside GitHub Actions through a Cloudflare Worker Cron Trigger. The Worker fetches the official NOAA products directly and publishes validated snapshots through the GitHub Contents API. The repository is the durable Foundation record; Streamlit consumes the latest committed Foundation snapshot and never substitutes an older snapshot when the Foundation read path fails.

The GitHub credential is configured as a Cloudflare secret and is not stored in source code or Wrangler configuration.

## Scientific methodology

### ENSO phase

- **El Niño:** RONI ≥ **+0.5 °C**
- **Neutral:** −0.5 °C < RONI < +0.5 °C
- **La Niña:** RONI ≤ **−0.5 °C**

### Intensity

- **Weak:** 0.5–0.9 °C
- **Moderate:** 1.0–1.4 °C
- **Strong:** 1.5–1.9 °C
- **Very Strong:** ≥2.0 °C

These bands describe index magnitude and do not, by themselves, constitute an independent official event declaration.

### Historical regimes

Historical El Niño and La Niña episodes are identified from the real RONI series as contiguous same-state periods lasting at least **five consecutive overlapping seasons**.

### Historical analogues

The analogue engine compares the latest eight RONI observations with historical eight-observation windows. Similarity is based on the trajectory of change within each window and ranked by RMSE, while excluding the current period and nearby continuation windows.

Analogues are **descriptive, not predictive**.

## Architecture

```text
app.py
  ├── Data Foundation read path
  │     ├── RONI
  │     ├── ONI
  │     └── Weekly Niño indices
  ├── Analysis
  │     ├── ENSO classification
  │     ├── intensity bands
  │     ├── recent evolution
  │     └── historical regime / analogue analysis
  └── Streamlit observatory UI

cloudflare/
├── worker.js       # NOAA ingestion + GitHub publication
└── wrangler.jsonc  # Cron and non-secret configuration

tests/              # offline unit and integrity tests
scripts/             # validation and local Foundation ingestion helpers
```

The application keeps the interactive path deliberately small and uses only published index products for the core observatory.

## Cloudflare deployment

The external scheduler is defined in `cloudflare/wrangler.jsonc` with a daily **16:05 UTC** Cron Trigger. Cloudflare Cron Triggers execute on UTC time and invoke the Worker's `scheduled()` handler.

Configure the GitHub token as a **Cloudflare secret** named `GITHUB_TOKEN`. Do not place the token in `wrangler.jsonc`, source code, or committed `.env` files.

```bash
cd cloudflare
npx wrangler secret put GITHUB_TOKEN
npx wrangler deploy
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Validate

```bash
python -m compileall -q .
pytest -q
python scripts/validate_streamlit.py
```

## Design principles

- **Official data first:** NOAA products are the observational source.
- **No fabricated observations:** no mock, synthetic, or fallback climate values.
- **Observation ≠ forecast:** the interface does not present observed indices as predictions.
- **Primary signal is explicit:** RONI is the operational core; ONI is complementary.
- **Traceable interpretation:** methodology and provenance remain visible in the product.
- **Focused scope:** the observatory prioritizes clarity over feature accumulation.
- **Infrastructure follows need:** the Data Foundation stays lightweight.
- **Least-privilege automation:** external credentials are secrets and scoped to the smallest practical repository permission.

## Limitations

- E.N.S.O is observational; it does not generate seasonal forecasts.
- Recent official index values may be revised by NOAA.
- Intensity bands are a project communication layer aligned with CPC thresholds.
- Weekly and seasonal indices summarize different products and can legitimately diverge.
- Climate-impact context is qualitative; the core application does not claim validated regional impact prediction for Brazil.
- No gridded Pacific anomaly map is required for core operation.
- The Streamlit runtime is ephemeral; durable snapshot history is maintained by the external Cloudflare ingestion worker.

## Project status

**Operational Foundation v1.2.**

The core observatory is intentionally frozen around ENSO monitoring, historical context, and transparent provenance. The Data Foundation adds controlled ingestion, validation, content-addressed versioning, and durable snapshot refresh without expanding the user-facing product into an infrastructure dashboard.

## Attribution

Climate data are provided by NOAA. Publications or analyses derived from this software should cite the original NOAA CPC products.
