"""
ENSO Intelligence
Real-time monitoring of El Niño and La Niña using NOAA data.

Entry point for Streamlit. Light theme only. No synthetic climate values.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path when launched via streamlit run app.py
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ui.components import apply_light_theme

st.set_page_config(
    page_title="ENSO Intelligence",
    page_icon="\U0001F321\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_light_theme()

# Sidebar brand
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 1.35rem; font-weight: 700; color: #111827;">
                ENSO Intelligence
            </div>
            <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.35;">
                Real-time monitoring of El Niño and La Niña<br/>using official NOAA data
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Data sources: NOAA CPC \u00b7 NOAA PSL \u00b7 NOAA NCEI")
    st.caption("RONI is the operational ENSO index (since 2026).")

# Landing content when no page is selected (Streamlit shows pages from pages/)
st.markdown(
    """
    # ENSO Intelligence

    Professional dashboard for monitoring the **El Niño\u2013Southern Oscillation (ENSO)**  
    using exclusively **official NOAA datasets**.

    Use the sidebar to navigate:

    | Page | Purpose |
    |------|---------|
    | **Overview** | Current ENSO state, RONI / ONI, intensity and recent trend |
    | **ENSO Monitor** | Detailed RONI / ONI time series with interactive controls |
    | **Historical Analysis** | Detected El Niño / La Niña events derived from the real series |
    | **Pacific SST** | Niño-region SST & anomaly indices (real CPC/OISST data) |
    | **Outlook** | Official NOAA CPC ENSO probabilities and strength outlook |
    | **Data Quality** | Source, coverage, last update and connection status |

    ---
    **Principle:** every numeric indicator shown to the user is derived from live or  
    cached NOAA products. If a source is unreachable the interface reports it clearly  
    and never substitutes synthetic values.
    """
)
