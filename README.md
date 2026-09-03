# ENSO Intelligence

**Real-time monitoring of El Niño and La Niña using official NOAA data.**

Professional Streamlit dashboard for the El Niño–Southern Oscillation (ENSO).  
All indicators are derived exclusively from live NOAA products.  
No synthetic, mock or hand-crafted climate values are ever injected into the interface.

---

## Features

- **Overview** — current ENSO state (El Niño / La Niña / Neutral), RONI, intensity, recent trend  
- **ENSO Monitor** — interactive RONI (and optional ONI) time series with zoom, range slider and window selection  
- **Historical Analysis** — automatic detection of ENSO episodes (≥ 5 consecutive seasons) from the real RONI series  
- **Pacific SST** — weekly Niño 1+2, 3, 3.4 and 4 SST / SSTA indices (CPC / OISST)  
- **Outlook** — official NOAA CPC ENSO phase probabilities and RONI strength outlook  
- **Data Quality** — source, coverage, last probe and connection status for every stream  

Light scientific theme only (white / light-grey cards, high contrast, no dark mode).

---

## Data Sources

| Product | Role | Endpoint |
|---------|------|----------|
| **RONI** (Relative Oceanic Niño Index) | Primary operational index (since Feb 2026) | `https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt` |
| **ONI** (Oceanic Niño Index) | Complementary / historical | `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` |
| Weekly Niño region SST/SSTA | Pacific monitoring | `https://www.cpc.ncep.noaa.gov/data/indices/wksst8110.for` |
| CPC ENSO probabilities | Official outlook | CPC RONI probabilities page |
| **ERSSTv6** | Gridded SST foundation of RONI | NOAA NCEI / PSL |

When any source is unreachable the UI displays a clear message and never substitutes fabricated numbers.

---

## Methodology

### Phase classification (NOAA operational)

| Condition | State |
|-----------|--------|
| Index ≥ +0.5 °C | **El Niño** |
| Index ≤ −0.5 °C | **La Niña** |
| otherwise | **Neutral** |

### Intensity (absolute magnitude of the 3-month running mean)

| Range (°C) | Intensity |
|------------|-----------|
| 0.5 – 0.9 | Weak |
| 1.0 – 1.4 | Moderate |
| 1.5 – 1.9 | Strong |
| ≥ 2.0 | Very Strong |

### Event detection

Contiguous runs of the same non-neutral state lasting **≥ 5 overlapping seasons** are retained as events (NOAA historical convention).

---

## Installation

```bash
git clone https://github.com/edu-moraess/enso-intelligence.git
cd enso-intelligence
pip install -r requirements.txt
streamlit run app.py
```

## Testing

```bash
pytest -q
```

## Licence & attribution

Climate data © NOAA. This software is provided for research and educational use.
