"""ENSO Intelligence — one-page climate observatory.

Uses only the project's real NOAA loaders. The main user experience is a single
scrollable page; legacy Streamlit pages may remain in the repository but are not
part of the primary navigation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.components import apply_light_theme, data_unavailable_message, enso_state_html
from src.noaa import fetch_roni, fetch_oni, fetch_nino_indices
from src.analysis.enso import classify_enso_state, classify_intensity, compute_recent_trend

st.set_page_config(
    page_title="ENSO Intelligence — Climate Observatory",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_light_theme()

# Keep the primary experience intentionally free of navigation clutter.
try:
    st.markdown("""<style>
    [data-testid="stSidebar"] {display:none;}
    [data-testid="collapsedControl"] {display:none;}
    .block-container {max-width: 1500px; padding-top: 2rem; padding-bottom: 4rem;}
    .hero {padding:1.4rem 1.6rem; border:1px solid #e5e7eb; border-radius:18px; background:#fff; margin-bottom:1rem;}
    .hero h1 {margin:0; font-size:2.2rem; color:#111827;}
    .hero p {margin:.35rem 0 0; color:#6b7280; font-size:1rem;}
    .info {padding:1rem 1.1rem; border-radius:14px; border:1px solid #e5e7eb; background:#fff;}
    .info h3 {margin-top:0; color:#111827;}
    </style>""", unsafe_allow_html=True)
except Exception:
    pass

st.markdown("""
<div class="hero">
  <h1>🌎 ENSO Intelligence</h1>
  <p>Climate Observatory · El Niño, La Niña and Pacific climate signals using official NOAA data</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner="Loading NOAA RONI…")
def get_roni():
    return fetch_roni()

@st.cache_data(ttl=3600, show_spinner="Loading NOAA ONI…")
def get_oni():
    return fetch_oni()

@st.cache_data(ttl=3600, show_spinner="Loading NOAA Niño indices…")
def get_nino():
    return fetch_nino_indices()

roni_df, roni_meta = get_roni()
oni_df, oni_meta = get_oni()
nino_df, nino_meta = get_nino()

if roni_df is None or roni_df.empty:
    data_unavailable_message("NOAA CPC RONI", getattr(roni_meta, "message", None))
    st.stop()

latest = roni_df.iloc[-1]
roni_val = float(latest["roni"])
state = classify_enso_state(roni_val)
intensity = classify_intensity(roni_val)
period = f"{latest['season']} {int(latest['year'])}"
trend_label, trend_delta = compute_recent_trend(roni_df["roni"], n_seasons=3)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="info"><small>ENSO STATUS</small><br>{enso_state_html(state.value)}<br><b>{intensity.value}</b></div>', unsafe_allow_html=True)
with c2:
    st.metric("RONI", f"{roni_val:+.2f} °C")
with c3:
    st.metric("Period", period)
with c4:
    st.metric("3-season change", "—" if trend_delta is None else f"{trend_delta:+.2f} °C")

st.markdown("## 🧠 O que está acontecendo?")
st.info(
    f"O RONI mais recente é **{roni_val:+.2f} °C** ({period}). "
    f"Pelo critério operacional configurado, o estado é **{state.value}**. "
    "Valores positivos representam condições mais quentes que a referência; valores negativos, condições mais frias."
)

st.markdown("## 📈 Evolução do ENSO")
fig = go.Figure()
fig.add_hrect(y0=0.5, y1=max(2.5, float(roni_df["roni"].max()) + .2), fillcolor="rgba(220,38,38,.08)", line_width=0)
fig.add_hrect(y0=min(-2.5, float(roni_df["roni"].min()) - .2), y1=-0.5, fillcolor="rgba(37,99,235,.08)", line_width=0)
fig.add_hline(y=0, line_width=1)
fig.add_hline(y=0.5, line_dash="dash", line_width=1, annotation_text="El Niño threshold")
fig.add_hline(y=-0.5, line_dash="dash", line_width=1, annotation_text="La Niña threshold")
fig.add_trace(go.Scatter(x=roni_df.index if not isinstance(roni_df.index, pd.RangeIndex) else range(len(roni_df)), y=roni_df["roni"], mode="lines", name="RONI", line=dict(width=2.5)))
fig.update_layout(height=430, margin=dict(l=10,r=10,t=20,b=10), hovermode="x unified", yaxis_title="°C", xaxis_title="Time")
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔎 Como interpretar este gráfico?"):
    st.markdown("**Vermelho** indica a faixa positiva associada a El Niño; **azul**, a faixa negativa associada a La Niña; a região próxima de zero representa neutralidade. As linhas tracejadas mostram os limiares de ±0,5 °C usados para o estado ENSO.")
with st.expander("❓ Por que o indicador está nessa cor?"):
    st.markdown(f"O indicador está classificado como **{state.value}** porque o RONI atual é **{roni_val:+.2f} °C**. A classificação é derivada do valor real carregado da NOAA, não de uma cor definida manualmente.")

st.markdown("## 🌊 O Pacífico")
if nino_df is not None and not nino_df.empty:
    # Render available Niño columns without assuming a single parser schema.
    value_cols = [c for c in nino_df.columns if str(c).lower().replace(" ", "") in {"nino12","nino1+2","nino3","nino34","nino3.4","nino4"}]
    if not value_cols:
        value_cols = [c for c in nino_df.columns if "nino" in str(c).lower() and pd.api.types.is_numeric_dtype(nino_df[c])]
    if value_cols:
        latest_nino = nino_df.iloc[-1]
        cols = st.columns(min(4, len(value_cols)))
        for i, col in enumerate(value_cols[:4]):
            with cols[i]:
                try:
                    st.metric(str(col).replace("nino34", "Niño 3.4"), f"{float(latest_nino[col]):+.2f} °C")
                except (TypeError, ValueError):
                    st.metric(str(col), "—")
        chart_cols = value_cols[:4]
        chart = go.Figure()
        for col in chart_cols:
            chart.add_trace(go.Scatter(x=nino_df.index if not isinstance(nino_df.index, pd.RangeIndex) else range(len(nino_df)), y=nino_df[col], mode="lines", name=str(col)))
        chart.add_hline(y=0, line_width=1)
        chart.update_layout(height=360, margin=dict(l=10,r=10,t=20,b=10), hovermode="x unified", yaxis_title="Anomaly (°C)")
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.caption("NOAA returned Niño data, but no recognized numeric Niño columns were available for plotting.")
else:
    data_unavailable_message("NOAA CPC Niño indices", getattr(nino_meta, "message", None))

st.markdown("## 🎨 Como interpretar as cores")
a,b,c,d = st.columns(4)
a.markdown("**🔵 Azul**  \nCondições mais frias que a referência.")
b.markdown("**🟢 Verde**  \nCondições próximas da neutralidade.")
c.markdown("**🟡 Amarelo**  \nTransição ou atenção.")
d.markdown("**🔴 Vermelho**  \nCondições mais quentes / El Niño.")

st.markdown("## 🌱 Possíveis impactos")
imp1, imp2, imp3, imp4, imp5 = st.columns(5)
imp1.markdown("**🌧️ Chuva**\n\nO ENSO pode alterar padrões regionais de precipitação.")
imp2.markdown("**🌡️ Temperatura**\n\nPode modificar padrões de temperatura em diferentes regiões.")
imp3.markdown("**🌱 Vegetação**\n\nMudanças em chuva e temperatura podem afetar condições de vegetação.")
imp4.markdown("**🌾 Agricultura**\n\nDisponibilidade hídrica e temperatura podem influenciar safras.")
imp5.markdown("**🇧🇷 Brasil**\n\nOs efeitos variam por região, estação e interação com outros padrões.")

st.caption("Esses impactos são relações climáticas históricas e não constituem uma previsão determinística. Não são exibidos dados de vegetação inventados.")

st.markdown("## 🔬 Como chegamos a este resultado?")
st.markdown("""
**NOAA → Sea Surface Temperature → anomalia → região Niño → RONI/ONI → limiar → classificação ENSO**

A ideia central é simples:

$$Anomalia = SST_{observada} - SST_{referência}$$

O índice transforma a informação oceânica em um sinal que pode ser monitorado ao longo do tempo.
""")

with st.expander("📚 ENSO 101 — Entenda o fenômeno"):
    st.markdown("""
### O que é ENSO?
ENSO (El Niño–Southern Oscillation) é um padrão acoplado entre o oceano e a atmosfera no Pacífico tropical.

### El Niño
É a fase quente do ciclo ENSO, associada a condições persistentemente mais quentes que o padrão em partes do Pacífico Equatorial e a mudanças na circulação atmosférica.

### La Niña
É a fase fria, associada a condições persistentemente mais frias que o padrão em partes do Pacífico Equatorial e a mudanças na circulação atmosférica.

### O que é Niño 3.4?
É uma das regiões de referência do Pacífico usadas para acompanhar a variabilidade de temperatura da superfície do mar relacionada ao ENSO.

### Por que a atmosfera importa?
O aquecimento ou resfriamento do Pacífico modifica convecção e circulação atmosférica. Essas mudanças podem produzir **teleconexões**, alterando padrões climáticos longe do Pacífico.

### E a vegetação?
Mudanças de chuva, temperatura e umidade do solo associadas à variabilidade climática podem influenciar a vegetação. O efeito não é igual em todo lugar e não deve ser interpretado como causalidade determinística para uma região específica.
""")

with st.expander("📐 RONI vs ONI"):
    if oni_df is not None and not oni_df.empty:
        latest_oni = oni_df.iloc[-1]
        oni_val = float(latest_oni["oni"])
        st.write(f"**ONI mais recente:** {oni_val:+.2f} °C · período {latest_oni['season']} {int(latest_oni['year'])}.")
    st.write("RONI é o índice operacional destacado nesta aplicação; ONI permanece como indicador complementar para continuidade histórica. Os dois não devem ser tratados como valores necessariamente idênticos.")

st.markdown("## 📡 Qualidade dos dados")
q1,q2,q3 = st.columns(3)
q1.metric("RONI records", getattr(roni_meta, "n_records", "—"))
q2.metric("ONI records", getattr(oni_meta, "n_records", "—"))
q3.metric("Niño records", getattr(nino_meta, "n_records", "—"))
st.caption("Fontes: NOAA CPC · NOAA PSL · NOAA NCEI. Os dados são carregados pelos módulos NOAA do projeto e armazenados em cache apenas para reduzir chamadas repetidas.")

st.markdown("---")
st.caption("ENSO Intelligence · One-page Climate Observatory · Real NOAA data · Light theme")
