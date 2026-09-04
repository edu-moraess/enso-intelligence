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
.block-container { max-width:1480px; padding:1.35rem 2.25rem 4.2rem; }
.hero { background:linear-gradient(135deg,#ffffff 0%,#f3f7fb 100%); border:1px solid #dbe4ee; border-radius:22px; padding:1.65rem 2.2rem; margin-bottom:1rem; box-shadow:0 8px 30px rgba(15,23,42,.035); }
.eyebrow { color:#2563eb; font-size:clamp(2.2rem,5vw,4rem); line-height:1; font-weight:800; letter-spacing:-.055em; text-transform:uppercase; }
.hero p { color:#94a3b8; font-size:.72rem; font-style:italic; letter-spacing:.01em; margin:.18rem 0 0; }
.insight { background:#f8fafc; border:1px solid #e2e8f0; border-radius:13px; padding:.75rem 1rem; color:#334155; }
.surface { background:#fff; border:1px solid #e2e8f0; border-radius:15px; padding:1.05rem 1.15rem; height:100%; }
.surface h4 { margin:.02rem 0 .4rem; color:#0f172a; }
.surface p { color:#475569; line-height:1.5; margin:0; }
.source-row { background:#fff; border:1px solid #e2e8f0; border-radius:11px; padding:.7rem .9rem; margin:.4rem 0; }
.source-row small { color:#64748b; }
.section-rule { border-top:1px solid #e2e8f0; margin:1.9rem 0 1.25rem; }
.chart-meta,.chart-note { color:#64748b; font-size:.8rem; }
.flow { display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:.5rem; margin:.8rem 0; }
.flow-step { background:#f8fafc; border:1px solid #dbe5f0; border-radius:10px; padding:.58rem .78rem; font-weight:700; color:#334155; }
.flow-arrow { color:#94a3b8; font-size:1.1rem; }
@media print {
  @page { size: A4 portrait; margin: 10mm 9mm; }
  html, body { width: 100% !important; background: #fff !important; }
  .block-container { max-width: none !important; width: 100% !important; padding: 0 !important; }
  [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], .main { overflow: visible !important; }
  .hero { break-inside: avoid; page-break-inside: avoid; box-shadow: none; margin-bottom: 7mm; }
  .section-rule { break-after: avoid; page-break-after: avoid; }
  .surface, .source-row, .insight { break-inside: avoid; page-break-inside: avoid; }
  [data-testid="stVerticalBlock"] { overflow: visible !important; }
  .stPlotlyChart { break-inside: avoid; page-break-inside: avoid; overflow: visible !important; width: 100% !important; }
  .stPlotlyChart > div, .stPlotlyChart iframe { max-width: 100% !important; }
  .js-plotly-plot, .plot-container, .svg-container { width: 100% !important; }
  .stButton, [data-testid="stToolbar"], [data-testid="stDecoration"], header, footer { display: none !important; }
  .flow { break-inside: avoid; page-break-inside: avoid; }
}
@media (max-width:700px) { .block-container { padding:1rem .85rem 3rem; } .hero { padding:1.35rem 1.15rem; } .eyebrow { font-size:clamp(2rem,11vw,3rem); } .flow { display:block; } .flow-step { margin:.25rem 0; text-align:center; } .flow-arrow { display:block; text-align:center; } }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner="Carregando RONI da NOAA…")
def get_roni(): return fetch_roni()

@st.cache_data(ttl=3600, show_spinner="Carregando ONI da NOAA…")
def get_oni(): return fetch_oni()

@st.cache_data(ttl=3600, show_spinner="Carregando índices Niño da NOAA…")
def get_nino(): return fetch_nino_indices()

def window_start(x: pd.Series, years: int) -> pd.Timestamp:
    return max(x.iloc[0], x.iloc[-1] - pd.DateOffset(years=years))

def chart_layout(height: int, hovermode: str = "x", legend=None):
    d = dict(height=height, margin=dict(l=8,r=8,t=18,b=8), hovermode=hovermode,
             plot_bgcolor="#fff", paper_bgcolor="#fff", font=dict(color="#475569"),
             xaxis=dict(showgrid=False), yaxis=dict(zeroline=False, gridcolor="#edf2f7"))
    if legend is not None: d["legend"] = legend
    return d

roni_df, roni_meta = get_roni()
oni_df, oni_meta = get_oni()
nino_df, nino_meta = get_nino()

st.markdown('<div class="hero"><div class="eyebrow">E.N.S.O</div><p>operational ENSO monitoring · NOAA official data</p></div>', unsafe_allow_html=True)

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
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Estado atual", state.value, f"Intensity · {intensity.value}")
    with c2: metric_card("RONI", f"{roni_val:+.2f} °C", "Relative Oceanic Niño Index")
    with c3: metric_card("Último período", period, "3-month running mean")
    with c4: metric_card("3-season change", f"{trend_delta:+.2f} °C" if trend_delta is not None else "—", trend_label)
    st.markdown(f'<div class="insight" style="border-left:4px solid {state_color};"><strong>{state.value}</strong> · {intensity.value} intensity · RONI {roni_val:+.2f} °C · {period}</div>', unsafe_allow_html=True)

    section_header("RONI History", "Anomalia relativa de SST no Niño 3.4 · média móvel de três meses.")
    x = pd.to_datetime(roni_df["date"]) if "date" in roni_df.columns else pd.to_datetime(roni_df.index)
    ymin = min(-2.2, float(roni_df["roni"].min())-.2); ymax = max(2.2, float(roni_df["roni"].max())+.2)
    fig = go.Figure()
    fig.add_hrect(y0=.5,y1=ymax,fillcolor="rgba(220,38,38,.055)",line_width=0)
    fig.add_hrect(y0=-.5,y1=.5,fillcolor="rgba(22,163,74,.025)",line_width=0)
    fig.add_hrect(y0=ymin,y1=-.5,fillcolor="rgba(37,99,235,.055)",line_width=0)
    fig.add_hline(y=.5,line_color="#dc2626",line_dash="dash",line_width=1,annotation_text="El Niño +0.5°C",annotation_position="top left")
    fig.add_hline(y=-.5,line_color="#2563eb",line_dash="dash",line_width=1,annotation_text="La Niña −0.5°C",annotation_position="bottom left")
    fig.add_hline(y=0,line_color="#94a3b8",line_width=1)
    fig.add_trace(go.Scatter(x=x,y=roni_df["roni"],mode="lines",name="RONI",line=dict(color="#0f766e",width=2.5),hovertemplate="%{x|%b %Y}<br>RONI: %{y:+.2f} °C<extra></extra>"))
    fig.add_trace(go.Scatter(x=[x.iloc[-1]],y=[roni_val],mode="markers",name="Latest",marker=dict(size=10,color="#0f172a"),hovertemplate=f"{period}<br>RONI: {roni_val:+.2f} °C<extra></extra>"))
    lay=chart_layout(455); lay.update(yaxis=dict(title="RONI (°C)",range=[ymin,ymax],zeroline=False,gridcolor="#edf2f7"),xaxis=dict(range=[window_start(x,30),x.iloc[-1]],showgrid=False,rangeslider=dict(visible=True,thickness=.045),rangeselector=dict(buttons=[dict(count=10,label="10Y",step="year",stepmode="backward"),dict(count=30,label="30Y",step="year",stepmode="backward"),dict(step="all",label="All")])),showlegend=False)
    fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False,"responsive":True})
    with st.expander("Como interpretar"):
        st.markdown("O RONI mede a anomalia relativa da temperatura da superfície do mar na região Niño 3.4 em uma média móvel de três meses. Valores acima de +0,5 °C correspondem à faixa operacional de El Niño; valores abaixo de −0,5 °C correspondem à faixa de La Niña. As categorias de intensidade seguem as faixas de intensidade publicadas pelo CPC.")

st.markdown('<div class="section-rule"></div>',unsafe_allow_html=True)
section_header("Pacific Ocean", "Anomalias semanais de SST relativa nas quatro regiões Niño publicadas pela NOAA CPC.")
if nino_df is None or nino_df.empty:
    data_unavailable_message(nino_meta.source,nino_meta.message)
else:
    regions=[("nino12_ssta","Niño 1+2"),("nino3_ssta","Niño 3"),("nino34_ssta","Niño 3.4"),("nino4_ssta","Niño 4")]
    available=[r for r in regions if r[0] in nino_df.columns]
    if available:
        latest_week=pd.to_datetime(nino_df.iloc[-1]["date"])
        st.markdown(f'<div class="chart-meta">Última observação semanal · {latest_week.strftime("%d %b %Y")}</div>',unsafe_allow_html=True)
        cards=st.columns(4)
        for card,(col,label) in zip(cards,available):
            with card: metric_card(label,f"{float(nino_df.iloc[-1][col]):+.2f} °C","latest weekly anomaly")
        fig=go.Figure(); series_colors={"Niño 1+2":"#2563eb","Niño 3":"#60a5fa","Niño 3.4":"#dc2626","Niño 4":"#fca5a5"}
        for col,label in available:
            fig.add_trace(go.Scatter(x=pd.to_datetime(nino_df["date"]),y=nino_df[col],mode="lines",name=label,line=dict(width=2.8 if label=="Niño 3.4" else 1.9,color=series_colors[label]),hovertemplate=f"%{{x|%d %b %Y}}<br>{label}: %{{y:+.2f}} °C<extra></extra>"))
        fig.add_hline(y=0,line_color="#94a3b8",line_width=1)
        nino_x=pd.to_datetime(nino_df["date"])
        lay=chart_layout(350,"x unified",dict(orientation="h",y=1.07,x=0)); lay.update(yaxis=dict(title="Relative SST anomaly (°C)",zeroline=False,gridcolor="#edf2f7"),xaxis=dict(range=[window_start(nino_x,5),nino_x.iloc[-1]],showgrid=False,rangeslider=dict(visible=True,thickness=.045),rangeselector=dict(buttons=[dict(count=2,label="2Y",step="year",stepmode="backward"),dict(count=5,label="5Y",step="year",stepmode="backward"),dict(step="all",label="All")])))
        fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False,"responsive":True})
    else: data_unavailable_message(nino_meta.source,"Weekly regional index fields are unavailable.")

st.markdown('<div class="section-rule"></div>',unsafe_allow_html=True)
section_header("Climate Context", "Historical relationships describe tendencies, not deterministic local outcomes.")
for col,title,body in zip(st.columns(3),["Atmosphere","Precipitation & Temperature","Agriculture & Water"],["ENSO changes tropical convection and atmospheric circulation, producing teleconnections that can extend beyond the Pacific.","Historical ENSO relationships can shift regional precipitation and temperature patterns, with responses varying by season and location.","Changes in precipitation and temperature can influence water availability and agricultural conditions; local responses depend on the region and season."]):
    with col: st.markdown(f'<div class="surface"><h4>{title}</h4><p>{body}</p></div>',unsafe_allow_html=True)

st.markdown('<div class="section-rule"></div>',unsafe_allow_html=True)
section_header("Methodology", "How the observatory connects NOAA ocean observations to ENSO assessment.")
st.markdown('<div class="flow"><div class="flow-step">Observed SST</div><div class="flow-arrow">→</div><div class="flow-step">SST Anomaly</div><div class="flow-arrow">→</div><div class="flow-step">Niño Regions</div><div class="flow-arrow">→</div><div class="flow-step">RONI / ONI</div><div class="flow-arrow">→</div><div class="flow-step">ENSO Assessment</div></div>',unsafe_allow_html=True)
with st.expander("Methodological details"):
    st.markdown("**Anomaly = observed SST − climatological reference.** The weekly Niño products use the NOAA CPC relative SST products. RONI and ONI are related but methodologically distinct indices; RONI is the primary operational indicator in this observatory and ONI is complementary. An observation describes current or historical conditions, while a forecast estimates future conditions with uncertainty.")
with st.expander("ENSO 101"):
    st.markdown("ENSO is a coupled ocean–atmosphere pattern in the tropical Pacific. El Niño is the warm phase, La Niña the cool phase, and Neutral describes conditions between the operational thresholds. Niño 3.4 is a reference region in the equatorial Pacific. Atmospheric circulation and ocean conditions interact to produce teleconnections whose effects vary by location and season.")

st.markdown('<div class="section-rule"></div>',unsafe_allow_html=True)
section_header("RONI vs ONI", "Related ENSO indicators with different methodologies.")
if oni_df is not None and not oni_df.empty:
    oni_latest=oni_df.iloc[-1]; oni_val=float(oni_latest["oni"]); oc1,oc2,oc3=st.columns(3)
    with oc1: metric_card("RONI",f"{roni_val:+.2f} °C",period)
    with oc2: metric_card("ONI",f"{oni_val:+.2f} °C",f"{oni_latest['season']} {int(oni_latest['year'])}")
    with oc3: metric_card("Difference",f"{roni_val-oni_val:+.2f} °C","RONI − ONI")
    st.caption("RONI is the primary operational indicator in this observatory. ONI remains a complementary NOAA series; the difference does not represent forecast error.")
else: data_unavailable_message(oni_meta.source,oni_meta.message)

st.markdown('<div class="section-rule"></div>',unsafe_allow_html=True)
section_header("Data & Sources", "NOAA CPC products used by the observatory.")
for meta in [roni_meta,oni_meta,nino_meta]:
    st.markdown(f'<div class="source-row"><strong>{meta.dataset}</strong><br><small>NOAA Climate Prediction Center (CPC)</small></div>',unsafe_allow_html=True)
st.caption("Source: NOAA Climate Prediction Center (CPC).")
