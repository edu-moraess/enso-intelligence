"""ModelLBs view rendered inside the single ENSO Intelligence application."""
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.noaa import fetch_oni, fetch_roni
from src.ui.ml_outlook import render_ml_outlook


def render_model_lbs() -> None:
    """Render the dedicated ModelLBs screen without Streamlit multipage navigation."""
    st.markdown(
        """
        <style>
        .model-page-header { background:linear-gradient(135deg,#ffffff 0%,#f3f7fb 100%); border:1px solid #dbe4ee; border-radius:18px; padding:1.25rem 1.5rem; margin-bottom:1rem; }
        .model-page-eyebrow { color:#2563eb; font-size:.7rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
        .model-page-title { color:#0f172a; font-size:clamp(1.45rem,3vw,2.1rem); font-weight:800; letter-spacing:-.035em; margin-top:.2rem; }
        .model-page-subtitle { color:#64748b; font-size:.82rem; margin-top:.25rem; }
        .model-view-nav { display:flex; gap:.45rem; align-items:center; margin:0 0 1.15rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="model-page-header"><div class="model-page-eyebrow">ENSO Intelligence</div><div class="model-page-title">ModelLBs</div><div class="model-page-subtitle">Validated machine-learning workspace for ENSO forecasting, benchmarking and model governance.</div></div>',
        unsafe_allow_html=True,
    )

    if st.button("← ENSO Intelligence", key="model_view_home", type="secondary"):
        st.query_params.clear()
        st.rerun()

    roni_df, _ = fetch_roni()
    oni_df, _ = fetch_oni()

    if roni_df is None or roni_df.empty or oni_df is None or oni_df.empty:
        st.warning("Foundation data unavailable. ModelLBs cannot run without the canonical NOAA inputs.")
        return

    render_ml_outlook(roni_df, oni_df)

    st.markdown(
        '<div class="obs-footer" style="margin-top:2rem;">ModelLBs · validated machine-learning workspace · ARQTECH LABS · © 2026</div>',
        unsafe_allow_html=True,
    )
