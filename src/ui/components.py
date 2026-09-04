"""Reusable Streamlit UI components — light theme, climate observatory aesthetic."""

from __future__ import annotations

from typing import Optional

import streamlit as st


def apply_light_theme() -> None:
    """Inject CSS for a clean light scientific observatory look."""
    st.markdown(
        """
        <style>
        .stApp { background-color: #f5f7fa; color: #1a1a1a; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
        h1, h2, h3 { color: #111827 !important; font-weight: 650 !important; letter-spacing: -0.02em; }
        div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 0.9rem 1.1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
        div[data-testid="stMetric"] label { color: #6b7280 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.04em; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #111827 !important; font-weight: 650; }
        .obs-hero { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 1.75rem 2rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .obs-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.25rem 1.4rem; margin-bottom: 0.85rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
        .state-el-nino { color: #b91c1c; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .state-la-nina { color: #1d4ed8; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .state-neutral { color: #374151; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .intensity-label { color: #4b5563; font-size: 1.05rem; margin-top: 0.15rem; }
        .badge { display: inline-block; padding: 0.18rem 0.6rem; border-radius: 999px; font-size: 0.72rem; font-weight: 650; letter-spacing: 0.03em; }
        .badge-ok { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
        .badge-warn { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
        .badge-err { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-info { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .badge-hot { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-cold { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .badge-neu { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
        .flow-step { display: inline-block; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.35rem 0.7rem; margin: 0.2rem; font-size: 0.85rem; color: #374151; }
        .section-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #6b7280; margin-bottom: 0.35rem; }
        .section-title { margin: 0; color: #111827; font-size: 1.42rem; font-weight: 750; letter-spacing: -0.025em; }
        .section-subtitle { color: #64748b; font-size: 0.84rem; margin-top: 0.22rem; line-height: 1.45; }
        .section-rule { border-top: 1px solid #dbe2ea; margin: 1.65rem 0 1.05rem; }
        .provenance-note { background: #f8fafc; border: 1px solid #dbe5f0; border-radius: 12px; padding: 0.85rem 1rem; color: #475569; font-size: 0.86rem; line-height: 1.5; }
        .block-container { padding-top: 1.25rem; max-width: 1100px; }
        hr { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }
        .js-plotly-plot .modebar { display: none !important; }
        @media (max-width:700px) {
            .block-container { padding: .9rem .75rem 2.5rem !important; }
            .obs-card { padding: .9rem 1rem; margin-bottom: .6rem; }
            .section-title { font-size: 1.18rem; }
            .section-subtitle { font-size: .78rem; line-height: 1.4; }
            .section-rule { margin: 1.25rem 0 .85rem; }
            .state-el-nino,.state-la-nina,.state-neutral { font-size: 1.55rem; }
            .flow-step { display: block; margin: .25rem 0; text-align: center; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_regime_timeline(roni_df) -> None:
    """Render the RONI regime timeline using data already loaded by the app."""
    from src.ui.regime_timeline import build_regime_timeline

    regime_fig = build_regime_timeline(roni_df)
    if regime_fig is None:
        return
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ENSO REGIME TIMELINE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Episódios históricos de El Niño e La Niña identificados no histórico do RONI.</div>', unsafe_allow_html=True)
    st.plotly_chart(regime_fig, use_container_width=True, config={"displaylogo": False, "responsive": True})
    st.markdown('<div class="chart-note">Episódios não neutros com pelo menos cinco estações sobrepostas consecutivas. Passe o cursor para ver duração e pico do RONI.</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Render a section header; callers own section separators to avoid duplicates."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, detail: Optional[str] = None) -> None:
    """Render a compact metric card used by the one-page observatory."""
    st.markdown(
        f'<div class="obs-card"><div class="section-label">{label}</div>'
        f'<div style="font-size:1.55rem;font-weight:750;color:#111827;line-height:1.15;">{value}</div>'
        f'{f"<div style=\"color:#6b7280;font-size:.82rem;margin-top:.3rem;\">{detail}</div>" if detail else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    mapping = {
        "Connected": "badge-ok", "Updated": "badge-ok", "Available": "badge-ok",
        "Warning": "badge-warn", "Error": "badge-err", "Unavailable": "badge-err",
    }
    cls = mapping.get(status, "badge-info")
    return f'<span class="badge {cls}">{status}</span>'


def data_unavailable_message(source: str = "NOAA", detail: Optional[str] = None) -> None:
    msg = f"**{source} data unavailable.** Please try again later."
    if detail:
        msg += f"\n\n_{detail}_"
    st.warning(msg)


def enso_state_class(state: str) -> str:
    return {"El Niño": "state-el-nino", "La Niña": "state-la-nina", "Neutral": "state-neutral"}.get(state, "state-neutral")


def state_emoji(state: str) -> str:
    return {"El Niño": "🔴", "La Niña": "🔵", "Neutral": "⚪"}.get(state, "⚪")
