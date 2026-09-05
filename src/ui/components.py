"""Reusable Streamlit UI components for the ENSO observatory."""
from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go
import streamlit as st


def _configure_observatory_chart(fig):
    if not isinstance(fig, go.Figure):
        return fig
    margin = fig.layout.margin
    current = margin.to_plotly_json() if margin is not None else {}
    fig.update_layout(
        margin=dict(
            l=max(72, int(current.get("l") or 0)),
            r=max(28, int(current.get("r") or 0)),
            t=max(42, int(current.get("t") or 0)),
            b=max(34, int(current.get("b") or 0)),
            pad=max(4, int(current.get("pad") or 0)),
        )
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    fig.update_traces(cliponaxis=False)
    return fig


def _install_chart_guard() -> None:
    if getattr(st, "_enso_chart_guard_installed", False):
        return
    original_plotly_chart = st.plotly_chart

    def guarded_plotly_chart(figure_or_data, *args, **kwargs):
        return original_plotly_chart(_configure_observatory_chart(figure_or_data), *args, **kwargs)

    st.plotly_chart = guarded_plotly_chart
    st._enso_chart_guard_installed = True


def apply_light_theme() -> None:
    """Inject the observatory light theme without rendering page navigation."""
    _install_chart_guard()
    st.markdown(
        """
        <style>
        .stApp { background-color:#f5f7fa; color:#1a1a1a; }
        section[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e5e7eb; }
        h1,h2,h3 { color:#111827 !important; font-weight:650 !important; letter-spacing:-.02em; }
        div[data-testid="stMetric"] { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:.9rem 1.1rem; box-shadow:0 1px 2px rgba(0,0,0,.04); }
        div[data-testid="stMetric"] label { color:#6b7280 !important; font-size:.75rem !important; text-transform:uppercase; letter-spacing:.04em; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#111827 !important; font-weight:650; }
        .obs-card { background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:1.25rem 1.4rem; margin-bottom:.85rem; box-shadow:0 1px 2px rgba(0,0,0,.04); }
        .current-condition-card { min-height:132px; display:flex; flex-direction:column; justify-content:center; }
        .current-condition-card .metric-value { font-size:1.72rem !important; letter-spacing:-.025em; }
        .current-condition-card.state-card .metric-value { font-size:1.9rem !important; font-weight:800 !important; }
        .current-condition-card.roni-card .metric-value { font-size:1.85rem !important; font-weight:800 !important; }
        .metric-detail { margin-top:.38rem !important; }
        .obs-footer { border-top:1px solid #e5e7eb; margin-top:1rem; padding:.8rem 0 .25rem; color:#94a3b8; font-size:.68rem; line-height:1.45; text-align:center; letter-spacing:.01em; }
        .section-label { font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:#6b7280; margin-bottom:.35rem; }
        .section-title { margin:0; color:#111827; font-size:1.42rem; font-weight:750; letter-spacing:-.025em; }
        .section-subtitle { color:#64748b; font-size:.84rem; margin-top:.22rem; line-height:1.45; }
        .section-rule { border-top:1px solid #dbe2ea; margin:1.65rem 0 1.05rem; }
        .provenance-note,.executive-note { background:#f8fafc; border:1px solid #dbe5f0; border-radius:12px; padding:.85rem 1rem; color:#475569; line-height:1.5; }
        .flow { display:flex; flex-wrap:nowrap; align-items:center; justify-content:center; gap:.35rem; margin:.8rem 0; }
        .flow-step { display:inline-block; background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:.52rem .62rem; font-size:.82rem; color:#374151; white-space:nowrap; }
        .flow-arrow { color:#94a3b8; flex:0 0 auto; }
        .analogue-card { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:.7rem .85rem; min-height:82px; box-sizing:border-box; display:flex; flex-direction:column; justify-content:center; }
        .analogue-card strong { color:#0f172a; }
        .analogue-card small { color:#64748b; }
        .chart-meta { color:#64748b; font-size:.8rem; margin-bottom:.65rem; }
        .insight { background:#f8fafc; border:1px solid #e2e8f0; border-radius:13px; padding:.75rem 1rem; color:#334155; }
        .model-nav-footer { margin-top:1.25rem; padding:1rem 0 .15rem; text-align:center; border-top:1px solid #e5e7eb; }
        .model-nav-caption { color:#64748b; font-size:.72rem; margin-bottom:.45rem; letter-spacing:.02em; }
        .stButton > button { border-radius:10px; border:1px solid #dbe4ee; background:#fff; color:#334155; font-weight:700; }
        .stButton > button:hover { border-color:#94a3b8; color:#0f172a; }
        @media (max-width:700px) {
            .block-container { padding:.9rem .75rem 2.5rem !important; }
            .obs-card { padding:.9rem 1rem; margin-bottom:.6rem; }
            .current-condition-card { min-height:112px; }
            .current-condition-card .metric-value { font-size:1.48rem !important; }
            .current-condition-card.state-card .metric-value { font-size:1.62rem !important; }
            .current-condition-card.roni-card .metric-value { font-size:1.58rem !important; }
            .section-title { font-size:1.18rem; }
            .section-subtitle { font-size:.78rem; }
            .section-rule { margin:1.25rem 0 .85rem; }
            .flow { display:block; }
            .flow-step { display:block; margin:.25rem 0; text-align:center; white-space:normal; }
            .analogue-card { min-height:74px; }
            .obs-footer { font-size:.64rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_regime_timeline(roni_df) -> None:
    from src.ui.regime_timeline import build_regime_timeline
    regime_fig = build_regime_timeline(roni_df)
    if regime_fig is None:
        return
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ENSO REGIME TIMELINE</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Episódios históricos de El Niño e La Niña identificados no histórico do RONI.</div>', unsafe_allow_html=True)
    st.plotly_chart(regime_fig, use_container_width=True, config={"displaylogo":False,"responsive":True})
    st.markdown('<div class="chart-note">Episódios não neutros com pelo menos cinco estações sobrepostas consecutivas. Passe o cursor para ver duração e pico do RONI.</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, detail: Optional[str] = None) -> None:
    current_labels = {"Estado atual", "RONI", "Último período", "3-season change"}
    current_class = " current-condition-card" if label in current_labels else ""
    if label == "Estado atual":
        current_class += " state-card"
    elif label == "RONI":
        current_class += " roni-card"
    detail_html = f'<div class="metric-detail" style="color:#6b7280;font-size:.82rem;margin-top:.3rem;">{detail}</div>' if detail else ""
    st.markdown(
        f'<div class="obs-card{current_class}"><div class="section-label">{label}</div>'
        f'<div class="metric-value" style="font-size:1.55rem;font-weight:750;color:#111827;line-height:1.15;">{value}</div>{detail_html}</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the observatory footer and the dedicated ML navigation at the bottom."""
    st.markdown('<div class="model-nav-footer"><div class="model-nav-caption">ADVANCED ANALYTICS</div>', unsafe_allow_html=True)
    if st.button("🧠  ModelLBs", key="open_model_lbs", use_container_width=False):
        st.switch_page("pages/1_ModelLBs.py")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="obs-footer">Data: NOAA CPC · PSL · NCEI | ARQTECH LABS · © 2026</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    mapping = {"Connected":"badge-ok","Updated":"badge-ok","Available":"badge-ok","Warning":"badge-warn","Error":"badge-err","Unavailable":"badge-err"}
    return f'<span class="badge {mapping.get(status, "badge-info")}">{status}</span>'


def data_unavailable_message(source: str = "NOAA", detail: Optional[str] = None) -> None:
    msg = f"**{source} data unavailable.** Please try again later."
    if detail:
        msg += f"\n\n_{detail}_"
    st.warning(msg)


def enso_state_class(state: str) -> str:
    return {"El Niño":"state-el-nino","La Niña":"state-la-nina","Neutral":"state-neutral"}.get(state,"state-neutral")


def state_emoji(state: str) -> str:
    return {"El Niño":"🔴","La Niña":"🔵","Neutral":"⚪"}.get(state,"⚪")
