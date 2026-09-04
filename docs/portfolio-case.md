# E.N.S.O. — Portfolio Case

## Operational ENSO Intelligence

E.N.S.O. is a single-page climate intelligence observatory built to turn official NOAA ENSO products into a compact, traceable operational view.

### The problem

Climate indices are authoritative but often distributed across separate institutional products. The challenge was not to create another generic weather dashboard, but to build a focused interface that answers a small set of operational questions without hiding the methodology or source data.

### What I built

- Live acquisition and parsing of official NOAA CPC products.
- RONI as the primary operational ENSO signal, with ONI as a complementary reference.
- Explicit ENSO state and magnitude classification.
- Recent observed evolution metrics.
- Historical ENSO regime detection from the RONI series.
- Historical analogue analysis based on trajectory similarity and RMSE.
- Weekly Niño-region SST anomaly monitoring for Niño 1+2, 3, 3.4 and 4.
- A Streamlit interface organized as an executive reading sequence rather than a collection of unrelated charts.
- Data provenance and scientific guardrails exposed directly in the product.

### Technical architecture

```text
NOAA CPC products
       ↓
Acquisition + parsing
       ↓
Validated observational data
       ↓
ENSO analysis
 ┌─────┼──────────┐
 ↓     ↓          ↓
Phase Evolution  Historical
                regimes/analogues
       ↓
Streamlit observatory
```

The core interactive path deliberately remains small. The application uses published index products directly and does not require a large gridded SST pipeline for its primary operation.

### Scientific design decisions

**RONI is the operational core.** The application uses the NOAA RONI threshold convention for phase classification: El Niño at or above +0.5 °C, La Niña at or below −0.5 °C, and Neutral between those thresholds.

**Magnitude is separated from phase.** Weak, moderate, strong and very strong bands communicate index magnitude and are aligned with CPC thresholds; they are not presented as an independent official event declaration.

**Historical regimes are rule-based.** Non-neutral episodes are detected from contiguous same-state periods lasting at least five consecutive overlapping seasons.

**Analogues are descriptive, not predictive.** The engine compares recent RONI trajectories with historical windows using RMSE. A similar historical trajectory is not presented as a forecast of future ENSO behavior.

**Observation is separated from retrieval time.** The interface distinguishes the period represented by the climate observation from when the source was retrieved.

### Data integrity

The project intentionally avoids synthetic, mocked or fallback climate observations. If an official source cannot be loaded or parsed, the application reports the data as unavailable rather than manufacturing a value.

### Engineering principles

- Official institutional data over static datasets.
- Small, explicit analytical pipeline over feature accumulation.
- Reproducible rules over opaque interpretation.
- Provenance visible at the point of use.
- Tests covering parsing, ENSO logic, regime detection and application integrity.
- Production UI designed for rapid interpretation.

### Outcome

E.N.S.O. demonstrates an end-to-end workflow from institutional data acquisition to a deployable intelligence product:

**source → validation → analysis → interpretation → interface → provenance**

The project is intentionally frozen at v1.0 around ENSO monitoring, historical context and transparent provenance rather than expanding into an unfocused climate platform.

### Stack

Python · Streamlit · Pandas · NumPy · Plotly · Requests · Pytest · NOAA CPC

### Repository

`edu-moraess/enso-intelligence`
