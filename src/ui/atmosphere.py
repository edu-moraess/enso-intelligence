"""Small atmospheric confirmation layer for the ENSO Signal section."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def classify_soi_signal(soi: float, state: str) -> str:
    """Classify whether the latest SOI supports the observed ENSO state."""
    if state == "El Niño":
        return "Supports El Niño" if soi < 0 else "Not supportive"
    if state == "La Niña":
        return "Supports La Niña" if soi > 0 else "Not supportive"
    return "Neutral / mixed"


def render_atmospheric_confirmation(soi_df: pd.DataFrame, state: str) -> None:
    """Render a compact atmospheric confirmation card beneath ENSO Signal."""
    if soi_df is None or soi_df.empty or "soi" not in soi_df.columns:
        return

    latest = soi_df.iloc[-1]
    soi = float(latest["soi"])
    date = pd.to_datetime(latest["date"])
    signal = classify_soi_signal(soi, state)

    recent = soi_df["soi"].astype(float).tail(3)
    mean3 = float(recent.mean()) if len(recent) else soi
    if state == "El Niño":
        persistence = "Supportive" if mean3 < 0 else "Mixed"
    elif state == "La Niña":
        persistence = "Supportive" if mean3 > 0 else "Mixed"
    else:
        persistence = "Mixed"

    st.markdown('<div class="section-subtitle">Atmospheric confirmation · Southern Oscillation Index (SOI).</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="surface"><h4>ATMOSPHERE</h4><p><strong>SOI {soi:+.1f}</strong><br>{date:%b %Y} · {signal}</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="surface"><h4>3-MONTH SIGNAL</h4><p><strong>{mean3:+.1f}</strong><br>Running mean · {persistence.lower()}</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="surface"><h4>INTERPRETATION</h4><p><strong>{signal}</strong><br>Pressure-gradient signal from Tahiti–Darwin observations.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-note">Negative SOI values are generally associated with El Niño; positive values with La Niña. This is confirmation of the observed regime, not an independent forecast.</div>', unsafe_allow_html=True)
