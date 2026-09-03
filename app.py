"""ENSO Intelligence — one-page climate observatory backed by NOAA."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis.enso import classify_enso_state, classify_intensity, compute_recent_trend
from src.noaa import fetch_nino_indices, fetch_oni, fetch_roni
from src.ui.components import apply_light_theme, data_unavailable_message, metric_card, section_header

st.set_page_config(page_title="ENSO Intelligence | Climate Observatory", page_icon="🌎", layout="wide", initial_sidebar_state="collapsed")
apply_light_theme()

st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none; }
.block-container { max-width:1480px; padding:2rem 2.4rem 4.5rem; }
.hero { background:linear-gradient(135deg,#ffffff 0%,#f3f7fb 100%); border:1px solid #dbe4ee; border-radius:24px; padding:2.2rem 2.5rem; margin-bottom:1.4rem; box-shadow:0 8px 30px rgba(15,23,42,.04); }
.eyebrow { color:#2563eb; font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }
.hero h1 { color:#0f172a; font-size:clamp(2.3rem,5vw,4.2rem); line-height:1; margin:.45rem 0 .7rem; letter-spacing:-.055em; }
.hero p { color:#64748b; font-size:1rem; margin:0; }
.surface { background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:1.15rem 1.25rem; height:100%; }
.surface h4 { margin:.05rem 0 .45rem; color:#0f172a; }
.surface p { color:#475569; line-height:1.55; margin:0; }
.source-row { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:.85rem 1rem; margin:.45rem 0; }
.source-row small { color:#64748b; }
.section-rule { border-top:1px solid #e2e8f0; margin:2.5rem 0 1.8rem; }
.flow { display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:.55rem; margin:1rem 0; }
.flow-step { background:#f8fafc; border:1px solid #dbe5f0; border-radius:10px; padding:.65rem .85rem; font-weight:700; color:#334155; }
.flow-arrow { color:#94a3b8; font-size:1.15rem; }
.chart-meta { color:#64748b; font-size:.8rem; margin-top:-.2rem; margin-bottom:.35rem; }
@media (max-width:700px) { .block-container { padding:1rem .9rem 3rem; } .hero { padding:1.55rem 1.25rem; } .flow { display:block; } .flow-step { margin:.3rem 0; text-align:center; } .flow-arrow { display:block; text-align:center; } }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner="Carregando RONI da NOAA…")
def get_roni():
    return fetch_roni()

@st.cache_data(ttl=3600, show_spinner="Carregando ONI da NOAA…")
def get_oni():
    return fetch_oni()

@st.cache_data(ttl=3600, show_spinner="Carregando índices Niño da NOAA…")
def get_nino():
    return fetch_nino_indices()

roni_df, roni_meta = get_roni()
oni_df, oni_meta = get_oni()
nino_df, nino_meta = get_nino()

st.markdown('<div class="hero"><div class="eyebrow">Climate Observatory · El Niño–Southern Oscillation</div><h1>ENSO Intelligence</h1><p>Monitoramento operacional com produtos oficiais da NOAA Climate Prediction Center.</p></div>', unsafe_allow_html=True)

if roni_df is None or roni_df.empty:
    data_unavailable_message(roni_meta.source, roni_meta.message)
else:
    latest = roni_df.iloc[-1]
    roni_val = float(latest["roni"])
    state = classify_enso_state(roni_val)
    intensity = classify_intensity(roni_val)
    period = f"{latest['season']} {int(latest['year'])}"
    trend_label, trend_delta = compute_recent_trend(roni_df["roni"], n_seasons=3)
    state_color = {"El Niño":"#b91c1c", "La Niña":"#1d4ed8", "Neutral":"#15803d"}[state.value]

    section_header("ENSO State", "Condição atual baseada no RONI mais recente disponível.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Estado atual", state.value, f"Intensity · {intensity.value}")
    with c2: metric_card("RONI", f"{roni_val:+.2f} °C", "Relative Oceanic Niño Index")
    with c3: metric_card("Último período", period, "3-month running mean")
    with c4: metric_card("3-season change", f"{trend_delta:+.2f} °C" if trend_delta is not None else "—", trend_label)
    st.markdown(f'<div class="surface" style="margin-top:1rem;border-left:4px solid {state_color};"><strong>{state.value}</strong> · <span style="color:#64748b">{intensity.value} intensity</span><br><span style="color:#475569">RONI {roni_val:+.2f} °C · {period}</span></div>', unsafe_allow_html=True)

    section_header("RONI History", "Relative Niño 3.4 sea-surface-temperature anomaly · 3-month running mean.")
    plot = go.Figure()
    x = pd.to_datetime(roni_df["date"]) if "date" in roni_df.columns else pd.to_datetime(roni_df.index)
    ymin = min(-2.2, float(roni_df["roni"].min()) - .2)
    ymax = max(2.2, float(roni_df["roni"].max()) + .2)
    default_start = max(x.iloc[0], x.iloc[-1] - pd.DateOffset(years=30))
    plot.add_hrect(y0=.5, y1=ymax, fillcolor="rgba(220,38,38,.07)", line_width=0)
    plot.add_hrect(y0=-.5, y1=.5, fillcolor="rgba(22,163,74,.035)", line_width=0)
    plot.add_hrect(y0=ymin, y1=-.5, fillcolor="rgba(37,99,235,.07)", line_width=0)
    plot.add_hline(y=.5, line_color="#dc2626", line_dash="dash", line_width=1, annotation_text="El Niño +0.5°C", annotation_position="top left")
    plot.add_hline(y=-.5, line_color="#2563eb", line_dash="dash", line_width=1, annotation_text="La Niña −0.5°C", annotation_position="bottom left")
    plot.add_hline(y=0, line_color="#94a3b8", line_width=1)
    plot.add_trace(go.Scatter(x=x, y=roni_df["roni"], mode="lines", name="RONI", line=dict(color="#0f766e", width=2.2), hovertemplate="%{x|%b %Y}<br>RONI: %{y:+.2f} °C<extra></extra>"))
    plot.add_trace(go.Scatter(x=[x.iloc[-1]], y=[roni_val], mode="markers", name="Latest", marker=dict(size=9, color="#0f172a"), hovertemplate=f"{period}<br>RONI: {roni_val:+.2f} °C<extra></extra>"))
    plot.update_layout(height=440, margin=dict(l=8,r=8,t=14,b=8), hovermode="x", yaxis=dict(title="RONI (°C)", zeroline=False, range=[ymin,ymax]), xaxis=dict(title=None, range=[default_start, x.iloc[-1]], rangeslider=dict(visible=True, thickness=.045), rangeselector=dict(buttons=[dict(count=10,label="10Y",step="year",stepmode="backward"),dict(count=30,label="30Y",step="year",stepmode="backward"),dict(step="all",label="All")])), plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", showlegend=False, font=dict(color="#475569"))
    st.plotly_chart(plot, use_container_width=True, config={"displaylogo":False, "responsive":True})

    with st.expander("Como interpretar"):
        st.markdown("O RONI mede a anomalia relativa da temperatura da superfície do mar na região Niño 3.4 em uma média móvel de três meses. Valores acima de +0,5 °C correspondem à faixa operacional de El Niño; valores abaixo de −0,5 °C correspondem à faixa de La Niña. As categorias de intensidade seguem as faixas de intensidade publicadas pelo CPC.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Pacific Ocean", "Weekly relative SST anomalies from the four Niño regions published by NOAA CPC.")
if nino_df is None or nino_df.empty:
    data_unavailable_message(nino_meta.source, nino_meta.message)
else:
    regions = [("nino12_ssta","Niño 1+2"),("nino3_ssta","Niño 3"),("nino34_ssta","Niño 3.4"),("nino4_ssta","Niño 4")]
    available = [(col,label) for col,label in regions if col in nino_df.columns]
    if available:
        latest_week = pd.to_datetime(nino_df.iloc[-1]["date"])
        st.markdown(f'<div class="chart-meta">Latest weekly observation · {latest_week.strftime("%d %b %Y")}</div>', unsafe_allow_html=True)
        cards = st.columns(4)
        for card,(col,label) in zip(cards,available):
            with card: metric_card(label, f"{float(nino_df.iloc[-1][col]):+.2f} °C", "latest weekly anomaly")
        fig = go.Figure()
        series_colors = {"Niño 1+2":"#2563eb","Niño 3":"#60a5fa","Niño 3.4":"#dc2626","Niño 4":"#fca5a5"}
        for col,label in available:
            fig.add_trace(go.Scatter(x=pd.to_datetime(nino_df["date"]), y=nino_df[col], mode="lines", name=label, line=dict(width=2, color=series_colors.get(label))))
        fig.add_hline(y=0, line_color="#94a3b8", line_width=1)
        nino_x = pd.to_datetime(nino_df["date"])
        nino_start = max(nino_x.iloc[0], nino_x.iloc[-1] - pd.DateOffset(years=5))
        fig.update_layout(height=350, margin=dict(l=8,r=8,t=26,b=8), hovermode="x unified", yaxis=dict(title="Relative SST anomaly (°C)", zeroline=False), xaxis=dict(title=None, range=[nino_start, nino_x.iloc[-1]], rangeslider=dict(visible=True, thickness=.045), rangeselector=dict(buttons=[dict(count=2,label="2Y",step="year",stepmode="backward"),dict(count=5,label="5Y",step="year",stepmode="backward"),dict(step="all",label="All")])), plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", legend=dict(orientation="h",y=1.08,x=0), font=dict(color="#475569"))
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False, "responsive":True})
    else:
        data_unavailable_message(nino_meta.source, "Weekly regional index fields are unavailable.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Climate Context", "Historical relationships describe tendencies, not deterministic local outcomes.")
impact_cols = st.columns(3)
for col,title,body in zip(impact_cols,["Atmosphere","Precipitation & Temperature","Agriculture & Water"],["ENSO changes tropical convection and atmospheric circulation, producing teleconnections that can extend beyond the Pacific.","Historical ENSO relationships can shift regional precipitation and temperature patterns, with responses varying by season and location.","Changes in precipitation and temperature can influence water availability and agricultural conditions; local responses depend on the region and season."]):
    with col: st.markdown(f'<div class="surface"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Methodology", "How the observatory connects NOAA ocean observations to ENSO assessment.")
st.markdown('<div class="flow"><div class="flow-step">Observed SST</div><div class="flow-arrow">→</div><div class="flow-step">SST Anomaly</div><div class="flow-arrow">→</div><div class="flow-step">Niño Regions</div><div class="flow-arrow">→</div><div class="flow-step">RONI / ONI</div><div class="flow-arrow">→</div><div class="flow-step">ENSO Assessment</div></div>', unsafe_allow_html=True)
with st.expander("Methodological details"):
    st.markdown("**Anomaly = observed SST − climatological reference.** The weekly Niño products use the NOAA CPC relative SST products. RONI and ONI are related but methodologically distinct indices; RONI is the primary operational indicator in this observatory and ONI is complementary. An observation describes current or historical conditions, while a forecast estimates future conditions with uncertainty.")
with st.expander("ENSO 101"):
    st.markdown("ENSO is a coupled ocean–atmosphere pattern in the tropical Pacific. El Niño is the warm phase, La Niña the cool phase, and Neutral describes conditions between the operational thresholds. Niño 3.4 is a reference region in the equatorial Pacific. Atmospheric circulation and ocean conditions interact to produce teleconnections whose effects vary by location and season.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("RONI vs ONI", "Related ENSO indicators with different methodologies.")
if oni_df is not None and not oni_df.empty:
    oni_latest = oni_df.iloc[-1]
    oni_val = float(oni_latest["oni"])
    oc1,oc2,oc3 = st.columns(3)
    with oc1: metric_card("RONI",f"{roni_val:+.2f} °C",period)
    with oc2: metric_card("ONI",f"{oni_val:+.2f} °C",f"{oni_latest['season']} {int(oni_latest['year'])}")
    with oc3: metric_card("Difference",f"{roni_val-oni_val:+.2f} °C","RONI − ONI")
    st.caption("RONI is the primary operational indicator in this observatory. ONI remains a complementary NOAA series; the difference does not represent forecast error.")
else:
    data_unavailable_message(oni_meta.source, oni_meta.message)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Data & Sources", "NOAA CPC products used by the observatory.")
for meta in [roni_meta,oni_meta,nino_meta]:
    st.markdown(f'<div class="source-row"><strong>{meta.dataset}</strong><br><small>NOAA Climate Prediction Center (CPC)</small></div>', unsafe_allow_html=True)
st.caption("Source: NOAA Climate Prediction Center (CPC).")
