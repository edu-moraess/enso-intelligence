"""ModelLBs — dedicated ENSO machine-learning workspace."""
from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.noaa import fetch_oni, fetch_roni
from src.ui.components import apply_light_theme
from src.ui.ml_outlook import render_ml_outlook

st.set_page_config(
    page_title="ModelLBs | ENSO Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_light_theme()

st.markdown(
    """
    <style>
    .model-page-header { background:linear-gradient(135deg,#ffffff 0%,#f3f7fb 100%); border:1px solid #dbe4ee; border-radius:18px; padding:1.25rem 1.5rem; margin-bottom:1rem; }
    .model-page-eyebrow { color:#2563eb; font-size:.7rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
    .model-page-title { color:#0f172a; font-size:clamp(1.45rem,3vw,2.1rem); font-weight:800; letter-spacing:-.035em; margin-top:.2rem; }
    .model-page-subtitle { color:#64748b; font-size:.82rem; margin-top:.25rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="model-page-header"><div class="model-page-eyebrow">ENSO Intelligence</div><div class="model-page-title">ModelLBs</div><div class="model-page-subtitle">Dedicated machine-learning workspace for validated ENSO models, benchmarking and statistical outlook.</div></div>',
    unsafe_allow_html=True,
)

roni_df, roni_meta = fetch_roni()
oni_df, oni_meta = fetch_oni()

if roni_df is None or roni_df.empty or oni_df is None or oni_df.empty:
    st.warning("Foundation data unavailable. ModelLBs cannot run without the canonical NOAA inputs.")
else:
    render_ml_outlook(roni_df, oni_df)

st.markdown('<div style="border-top:1px solid #e5e7eb;margin-top:2.5rem;padding-top:1rem;text-align:center;"></div>', unsafe_allow_html=True)
if st.button("🌎  Voltar ao ENSO Intelligence", key="back_to_enso"):
    st.switch_page("app.py")
st.caption("ModelLBs · validated machine-learning workspace")
