"""Reusable Streamlit UI components — light theme, climate observatory aesthetic."""

from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go
import streamlit as st


def _configure_observatory_chart(fig):
    """Apply safe Plotly margins and visible endpoints before rendering."""
    if not isinstance(fig, go.Figure):
        return fig

    margin = fig.layout.margin
    current_margin = margin.to_plotly_json() if margin is not None else {}
    fig.update_layout(
        margin=dict(
            l=max(72, int(current_margin.get("l") or 0)),
            r=max(28, int(current_margin.get("r") or 0)),
            t=max(42, int(current_margin.get("t") or 0)),
            b=max(34, int(current_margin.get("b") or 0)),
            pad=max(4, int(current_margin.get("pad") or 0)),
        )
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    fig.update_traces(cliponaxis=False)

    # Diagnostic endpoint markers make edge clipping immediately visible.
    endpoint_markers = []
    for trace in list(fig.data):
        mode = str(trace.mode or "") if hasattr(trace, "mode") else ""
        if trace.type != "scatter" or "lines" not in mode or "markers" in mode:
            continue
        x_values = list(trace.x) if trace.x is not None else []
        y_values = list(trace.y) if trace.y is not None else []
        if not x_values or not y_values:
            continue
        last_x = next((value for value in reversed(x_values) if value is not None), None)
        last_y = next((value for value in reversed(y_values) if value is not None), None)
        if last_x is None or last_y is None:
            continue
        line_color = getattr(trace.line, "color", None) or "#0f172a"
        endpoint_markers.append(
            go.Scatter(
                x=[last_x],
                y=[last_y],
                mode="markers",
                name=f"{trace.name or 'Series'} endpoint",
                marker=dict(size=8, color=line_color, line=dict(width=1, color="#ffffff")),
                showlegend=False,
                hoverinfo="skip",
                cliponaxis=False,
            )
        )
    if endpoint_markers:
        fig.add_traces(endpoint_markers)

    for annotation in fig.layout.annotations or []:
        text = str(annotation.text or "")
        if text.startswith("El Niño +0.5") or text.startswith("La Niña"):
            annotation.xref = "paper"
            annotation.x = 0.025
            annotation.xanchor = "left"
            annotation.xshift = 0
            annotation.yshift = 0
            annotation.bgcolor = "rgba(255,255,255,.82)"
            annotation.borderpad = 3

    return fig


def _install_chart_guard() -> None:
    """Ensure every Plotly chart gets the observatory layout guard once."""
    if getattr(st, "_enso_chart_guard_installed", False):
        return

    original_plotly_chart = st.plotly_chart

    def guarded_plotly_chart(figure_or_data, *args, **kwargs):
        return original_plotly_chart(_configure_observatory_chart(figure_or_data), *args, **kwargs)

    st.plotly_chart = guarded_plotly_chart
    st._enso_chart_guard_installed = True


def apply_light_theme() -> None:
    """Inject CSS for a clean light scientific observatory look."""
    _install_chart_guard()
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
        .current-condition-card { min-height: 132px; display: flex; flex-direction: column; justify-content: center; }
        .current-condition-card .metric-value { font-size: 1.72rem !important; letter-spacing: -0.025em; }
        .current-condition-card.state-card .metric-value { font-size: 1.9rem !important; font-weight: 800 !important; letter-spacing: -0.035em; }
        .current-condition-card.roni-card .metric-value { font-size: 1.85rem !important; font-weight: 800 !important; }
        .current-condition-card .metric-detail { margin-top: .38rem !important; }
        .obs-footer { border-top: 1px solid #e5e7eb; margin-top: 2.25rem; padding: .8rem 0 .25rem; color: #94a3b8; font-size: .68rem; line-height: 1.45; text-align: center; letter-spacing: .01em; }
        .obs-footer-brand { color: #64748b; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; white-space: nowrap; }
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
        .source-row { background: transparent; border: 0; border-bottom: 1px solid #eef2f6; border-radius: 0; padding: .32rem 0; margin: 0; }
        .source-row small { color: #64748b; font-size: .72rem; }
        .insight { display: none !important; }
        .flow { flex-wrap: nowrap !important; gap: .35rem !important; }
        .flow-step { padding: .52rem .62rem; font-size: .82rem; white-space: nowrap; }
        .flow-arrow { flex: 0 0 auto; }
        .executive-note { line-height: 1.7; }
        .analogue-card { min-height: 82px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; }
        .js-plotly-plot .rangeselector { transform: none !important; }
        .js-plotly-plot .rangeselector text { font-size: 10px !important; }
        .js-plotly-plot .rangeslider-container { opacity: .82; }
        .stPlotlyChart { margin-top: .15rem; overflow: visible !important; }
        .stPlotlyChart > div, .js-plotly-plot, .plot-container, .svg-container { max-width: 100% !important; }
        @media (min-width:701px) and (max-width:1100px) { .flow { flex-wrap: wrap !important; } }
        @media (max-width:700px) {
            .block-container { padding: .9rem .75rem 2.5rem !important; }
            .obs-card { padding: .9rem 1rem; margin-bottom: .6rem; }
            .current-condition-card { min-height: 112px; }
            .current-condition-card .metric-value { font-size: 1.48rem !important; }
            .current-condition-card.state-card .metric-value { font-size: 1.62rem !important; }
            .current-condition-card.roni-card .metric-value { font-size: 1.58rem !important; }
            .obs-footer { margin-top: 1.8rem; padding-bottom: .2rem; font-size: .64rem; }
            .section-title { font-size: 1.18rem; }
            .section-subtitle { font-size: .78rem; line-height: 1.4; }
            .section-rule { margin: 1.25rem 0 .85rem; }
            .state-el-nino,.state-la-nina,.state-neutral { font-size: 1.55rem; }
            .flow { display: block !important; }
            .flow-step { display: block; margin: .25rem 0; text-align: center; white-space: normal; }
            .analogue-card { min-height: 74px; }
            .js-plotly-plot .rangeselector text { font-size: 9px !important; }
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
    st.plotly_chart(regime_fig, use_container_width=True, config={"displaylogo": False, "responsive": True})
    st.markdown('<div class="chart-note">Episódios não neutros com pelo menos cinco estações sobrepostas consecutivas. Passe o cursor para ver duração e pico do RONI.</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, detail: Optional[str] = None) -> None:
    current_labels = {"Estado atual", "RONI", "Último período", "3-season change"}
    current_class = " current-condition-card"
    if label == "Estado atual":
        current_class += " state-card"
    elif label == "RONI":
        current_class += " roni-card"
    st.markdown(
        f'<div class="obs-card{current_class if label in current_labels else ""}"><div class="section-label">{label}</div>'
        f'<div class="metric-value" style="font-size:1.55rem;font-weight:750;color:#111827;line-height:1.15;">{value}</div>'
        f'{f"<div class=\"metric-detail\" style=\"color:#6b7280;font-size:.82rem;margin-top:.3rem;\">{detail}</div>" if detail else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown('<div class="obs-footer">Data: NOAA CPC · PSL · NCEI | ARQTECH LABS · © 2026</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    mapping = {"Connected": "badge-ok", "Updated": "badge-ok", "Available": "badge-ok", "Warning": "badge-warn", "Error": "badge-err", "Unavailable": "badge-err"}
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
