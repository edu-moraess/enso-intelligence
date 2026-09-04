# E.N.S.O. — LinkedIn Case

## Post-ready version

I built **E.N.S.O. — Operational ENSO Intelligence**, a focused climate intelligence observatory for monitoring El Niño and La Niña using official NOAA climate products.

The goal was not to build another weather dashboard. It was to turn institutional climate data into a compact, traceable operational view.

The system combines:

- **RONI** as the primary operational ENSO signal
- **ONI** as a complementary reference
- weekly Niño-region SST anomalies
- historical ENSO regime detection
- trajectory-based historical analogues using RMSE
- recent signal evolution metrics
- explicit data provenance and scientific guardrails

A core design decision was to keep **observation separate from forecasting**. The application does not fabricate values, use mock/fallback climate observations, or present historical analogues as predictions.

From an engineering perspective, the project follows a simple pipeline:

**NOAA source → acquisition & parsing → validation → analysis → interpretation → Streamlit observatory**

The result is intentionally lean: one page, eight analytical sections, official data, reproducible logic, and visible provenance.

This project was an exercise in building the full chain from **institutional data to an operational intelligence product** — not just a visualization.

🔗 GitHub: https://github.com/edu-moraess/enso-intelligence

#Python #DataScience #ClimateTech #DataEngineering #Streamlit #NOAA #ENSO
