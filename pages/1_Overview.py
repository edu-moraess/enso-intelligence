"""Overview — current ENSO state from real NOAA RONI/ONI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ui.components import (
    apply_light_theme,
    data_unavailable_message,
    enso_state_html,
    section_header,
)
from src.noaa.roni import fetch_roni
from src.noaa.cpc import fetch_oni
from src.analysis.enso import (
    classify_enso_state,
    classify_intensity,
    compute_recent_trend,
)

st.set_page_config(page_title="Overview | ENSO Intelligence", layout="wide")
apply_light_theme()

st.title("Overview")
st.caption("Current ENSO state derived exclusively from NOAA CPC RONI and ONI.")


@st.cache_data(ttl=3600, show_spinner="Loading RONI from NOAA CPC…")
def get_roni():
    return fetch_roni()


@st.cache_data(ttl=3600, show_spinner="Loading ONI from NOAA CPC…")
def get_oni():
    return fetch_oni()


roni_df, roni_meta = get_roni()
oni_df, oni_meta = get_oni()

section_header("Current ENSO State", "Based on the most recent RONI value (operational index)")

if roni_df is None or roni_df.empty:
    data_unavailable_message("NOAA CPC (RONI)", roni_meta.message)
else:
    latest = roni_df.iloc[-1]
    roni_val = float(latest["roni"])
    state = classify_enso_state(roni_val)
    intensity = classify_intensity(roni_val)
    trend_label, trend_delta = compute_recent_trend(roni_df["roni"], n_seasons=3)

    col_status, col_meta = st.columns([1.2, 2])
    with col_status:
        st.markdown(
            f"""
            <div class=\"enso-card\">
                <div style=\"font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;\">
                    ENSO STATUS
                </div>
                {enso_state_html(state.value)}
                <div style=\"margin-top:0.5rem;color:#4b5563;\">
                    Intensity: <strong>{intensity.value}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_meta:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("RONI (latest)", f"{roni_val:+.2f} \u00b0C")
        period = f"{latest['season']} {int(latest['year'])}"
        m2.metric("Period", period)
        m3.metric("Recent trend", trend_label.title())
        if trend_delta is not None:
            m4.metric("\u0394 (3 seasons)", f"{trend_delta:+.2f} \u00b0C")
        else:
            m4.metric("\u0394 (3 seasons)", "\u2014")

    st.caption(
        f"Last RONI record: {period} \u00b7 Source: NOAA CPC \u00b7 "
        f"Records available: {roni_meta.n_records} \u00b7 "
        f"Coverage: {roni_meta.start.strftime('%Y-%m') if roni_meta.start else '\u2014'} \u2192 "
        f"{roni_meta.end.strftime('%Y-%m') if roni_meta.end else '\u2014'}"
    )

st.markdown("---")
section_header("Complementary indicator \u2014 ONI", "Traditional Oceanic Ni\u00f1o Index (for historical comparison)")

if oni_df is None or oni_df.empty:
    data_unavailable_message("NOAA CPC (ONI)", oni_meta.message)
else:
    latest_oni = oni_df.iloc[-1]
    oni_val = float(latest_oni["oni"])
    oni_state = classify_enso_state(oni_val)
    c1, c2, c3 = st.columns(3)
    c1.metric("ONI (latest)", f"{oni_val:+.2f} \u00b0C")
    c2.metric("ONI classification", oni_state.value)
    c3.metric("Period", f"{latest_oni['season']} {int(latest_oni['year'])}")

with st.expander("Classification methodology (documented)"):
    st.markdown(
        """
        **Operational thresholds (NOAA CPC):**
        - **El Ni\u00f1o** \u2014 index \u2265 +0.5 \u00b0C  
        - **La Ni\u00f1a** \u2014 index \u2264 \u22120.5 \u00b0C  
        - **Neutral** \u2014 otherwise  

        **Intensity** (from absolute peak of the 3-month running mean):
        - Weak: 0.5 \u2013 0.9  
        - Moderate: 1.0 \u2013 1.4  
        - Strong: 1.5 \u2013 1.9  
        - Very Strong: \u2265 2.0  

        RONI is the official operational index since February 2026.  
        ONI remains available for continuity with the historical record.
        """
    )
