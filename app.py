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
from src.ui.components import apply_light_theme, data_unavailable_message, metric_card, section_header, status_badge

st.set_page_config(page_title="ENSO Intelligence | Climate Observatory", page_icon="🌎", layout="wide", initial_sidebar_state="collapsed")
apply_light_theme()
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.block-container { max-width: 1440px; padding: 2.4rem 2.5rem 5rem; }
.hero { background:linear-gradient(135deg,#ffffff 0%,#eef6ff 100%); border:1px solid #dbe5f0; border-radius:24px; padding:2.6rem 2.8rem; margin-bottom:1.5rem; }
.eyebrow { color:#2563eb; font-size:.76rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
.hero h1 { color:#0f172a; font-size:clamp(2.3rem,6vw,4.6rem); line-height:1; margin:.5rem 0 .8rem; letter-spacing:-.06em; }
.hero p { color:#475569; font-size:1.05rem; margin:0; }
.surface { background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:1.2rem 1.35rem; height:100%; }
.section-rule { border-top:1px solid #e2e8f0; margin:2.8rem 0 2rem; }
.flow { display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:.7rem; margin:1.2rem 0; }
.flow-step { background:#f8fafc; border:1px solid #dbe5f0; border-radius:12px; padding:.75rem 1rem; font-weight:700; text-align:center; }
.flow-arrow { color:#64748b; font-size:1.4rem; }
@media (max-width: 700px) { .block-container { padding:1.2rem 1rem 3rem; } .hero { padding:1.7rem 1.35rem; } .flow { display:block; } .flow-step { margin:.35rem 0; } .flow-arrow { display:block; text-align:center; } }
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

st.markdown('<div class="hero"><div class="eyebrow">Climate Observatory · El Niño–Southern Oscillation</div><h1>ENSO Intelligence</h1><p>Monitoramento operacional e educação climática com produtos oficiais da NOAA.</p></div>', unsafe_allow_html=True)

if roni_df is None or roni_df.empty:
    data_unavailable_message(roni_meta.source, roni_meta.message)
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    section_header("Data Quality", "O indicador principal não pôde ser carregado; nenhum valor foi substituído.")
else:
    latest = roni_df.iloc[-1]
    roni_val = float(latest["roni"])
    state = classify_enso_state(roni_val)
    intensity = classify_intensity(roni_val)
    period = f"{latest['season']} {int(latest['year'])}"
    trend_label, trend_delta = compute_recent_trend(roni_df["roni"], n_seasons=3)
    state_color = {"El Niño":"#b91c1c", "La Niña":"#1d4ed8", "Neutral":"#15803d"}[state.value]

    section_header("ENSO State", "O estado atual é derivado diretamente do RONI mais recente disponível.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Estado atual", state.value, intensity.value)
    with c2: metric_card("RONI atual", f"{roni_val:+.2f} °C", "índice operacional")
    with c3: metric_card("Último período", period, "frequência sazonal")
    with c4: metric_card("Tendência · 3 estações", trend_label, "sem previsão determinística" if trend_delta is None else f"variação {trend_delta:+.2f} °C")
    st.markdown(f'<div class="surface" style="margin-top:1rem;border-left:5px solid {state_color};"><strong>{state.value} · {intensity.value}</strong><br><span style="color:#475569">O RONI de {roni_val:+.2f} °C está {"acima" if roni_val >= 0 else "abaixo"} da referência climática no período {period}.</span></div>', unsafe_allow_html=True)

    section_header("RONI history", "Anomalia sazonal da temperatura da superfície do mar, com limiares operacionais de ±0,5 °C.")
    plot = go.Figure()
    x = roni_df["date"] if "date" in roni_df.columns else roni_df.index
    ymin = min(-1.0, float(roni_df["roni"].min()) - .2); ymax = max(1.0, float(roni_df["roni"].max()) + .2)
    plot.add_hrect(y0=.5, y1=ymax, fillcolor="rgba(220,38,38,.10)", line_width=0)
    plot.add_hrect(y0=ymin, y1=-.5, fillcolor="rgba(37,99,235,.10)", line_width=0)
    plot.add_hrect(y0=-.5, y1=.5, fillcolor="rgba(22,163,74,.06)", line_width=0)
    plot.add_hline(y=0, line_color="#64748b", line_width=1)
    plot.add_hline(y=.5, line_color="#dc2626", line_dash="dash", annotation_text="+0,5 °C")
    plot.add_hline(y=-.5, line_color="#2563eb", line_dash="dash", annotation_text="−0,5 °C")
    plot.add_trace(go.Scatter(x=x, y=roni_df["roni"], mode="lines+markers", name="RONI", line=dict(color="#0f766e", width=2.5), marker=dict(size=4), hovertemplate="%{x|%b %Y}<br>RONI: %{y:+.2f} °C<extra></extra>"))
    plot.update_layout(height=450, margin=dict(l=10,r=10,t=25,b=10), hovermode="x", yaxis_title="Anomalia (°C)", xaxis_title="Período", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", legend=dict(orientation="h"))
    st.plotly_chart(plot, width="stretch", config={"displaylogo":False, "responsive":True})

    with st.expander("Como interpretar este gráfico?"):
        st.markdown("**SST** é a temperatura da superfície do mar. Uma **anomalia** é a diferença entre a SST observada e uma referência climática. **Niño 3.4** é uma região do Pacífico equatorial usada para monitorar o ENSO; o **RONI** é o índice operacional relativo destacado pelo CPC. Valores positivos indicam aquecimento relativo e negativos indicam resfriamento relativo. Neste painel, ±0,5 °C são os limiares usados para separar El Niño, Neutral e La Niña.")
    with st.expander("Por que está nessa cor?"):
        st.markdown(f"O indicador aparece na faixa de **{state.value}** porque o RONI real mais recente é **{roni_val:+.2f} °C**, valor que está {('acima de +0,5 °C' if roni_val >= .5 else 'abaixo de −0,5 °C' if roni_val <= -.5 else 'entre −0,5 °C e +0,5 °C')}. A cor é semântica e acompanha a classificação, não um valor decorativo.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Pacific Ocean", "Índices semanais publicados pela NOAA; SST e anomalia são mantidas como séries distintas.")
if nino_df is None or nino_df.empty:
    data_unavailable_message(nino_meta.source, nino_meta.message)
else:
    regions = [("nino12_ssta","Niño 1+2"),("nino3_ssta","Niño 3"),("nino34_ssta","Niño 3.4"),("nino4_ssta","Niño 4")]
    available = [(col,label) for col,label in regions if col in nino_df.columns]
    if available:
        cards = st.columns(len(available))
        for card, (col,label) in zip(cards, available): metric_card(label, f"{float(nino_df.iloc[-1][col]):+.2f} °C", "anomalia semanal")
        fig = go.Figure()
        for col,label in available: fig.add_trace(go.Scatter(x=nino_df["date"], y=nino_df[col], mode="lines", name=label))
        fig.add_hline(y=0, line_color="#64748b"); fig.update_layout(height=360, margin=dict(l=10,r=10,t=20,b=10), hovermode="x unified", yaxis_title="Anomalia (°C)", plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig, width="stretch", config={"displaylogo":False, "responsive":True})
    else: st.caption("A NOAA respondeu, mas não retornou colunas regionais reconhecidas para este produto.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Climate Impacts", "Relações históricas alteram probabilidades e padrões; não constituem previsão determinística.")
impact_cols = st.columns(3)
for col, title, body in zip(impact_cols, ["Precipitação e temperatura", "Vegetação e agricultura", "Circulação atmosférica"], ["O ENSO pode estar historicamente associado a mudanças regionais de chuva e temperatura, com intensidade variável por estação.", "A cadeia plausível é ENSO → chuva/temperatura → disponibilidade hídrica → condições para agricultura e vegetação. Nenhum dado de produtividade ou NDVI é inventado aqui.", "Mudanças no Pacífico tropical afetam convecção e circulação, produzindo teleconexões que podem alcançar outras bacias."]):
    with col: st.markdown(f'<div class="surface"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)
with st.expander("Brazil"):
    st.markdown("No Brasil, as associações históricas entre ENSO e chuva ou temperatura dependem da fase, estação, região e interação com outros padrões atmosféricos. O Sul pode apresentar sinais diferentes do Norte e Nordeste em episódios distintos; por isso, este projeto apresenta apenas a interpretação qualitativa e não afirma uma relação determinística nem números regionais que não estejam em um dataset implementado.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Methodology", "Fluxo analítico aplicado aos produtos NOAA disponíveis.")
st.markdown('<div class="flow"><div class="flow-step">SST observada</div><div class="flow-arrow">→</div><div class="flow-step">Anomalia</div><div class="flow-arrow">→</div><div class="flow-step">Niño 3.4</div><div class="flow-arrow">→</div><div class="flow-step">RONI / ONI</div><div class="flow-arrow">→</div><div class="flow-step">Classificação</div><div class="flow-arrow">→</div><div class="flow-step">Possíveis impactos</div></div>', unsafe_allow_html=True)
with st.expander("Detalhes metodológicos"):
    st.markdown("**Anomalia = SST observada − SST de referência.** O RONI e o ONI são índices mensais/sazonais de anomalia oceânica, mas não são a mesma série: suas referências e procedimentos de cálculo podem diferir. O RONI é o indicador operacional primário desta aplicação; o ONI é complementar. Um indicador descreve condições observadas, enquanto uma previsão é uma estimativa futura com incerteza. O período de referência e a nomenclatura seguem os produtos publicados pela NOAA CPC; o dashboard não cria climatologia própria nem substitui dados ausentes.")
with st.expander("ENSO 101"):
    st.markdown("ENSO é um padrão acoplado entre oceano e atmosfera no Pacífico tropical. **El Niño** é a fase quente; **La Niña**, a fase fria; **Neutral** descreve condições que ficam entre os limiares operacionais. Niño 3.4 é uma região de referência do Pacífico equatorial. O oceano influencia a convecção, e a atmosfera redistribui essa energia por meio da circulação e de teleconexões. Vegetação e agricultura podem responder a mudanças de chuva, temperatura e umidade do solo, mas a resposta depende do local e não é uma determinação automática do ENSO.")
with st.expander("RONI vs ONI"):
    if oni_df is not None and not oni_df.empty:
        oni_latest = oni_df.iloc[-1]; st.markdown(f"**ONI mais recente:** {float(oni_latest['oni']):+.2f} °C · {oni_latest['season']} {int(oni_latest['year'])}.")
    else: data_unavailable_message(oni_meta.source, oni_meta.message)
    st.markdown("RONI e ONI podem diferir porque são produtos metodologicamente distintos. O RONI operacional é o indicador principal desta interface; o ONI permanece como série complementar histórica. Nenhum dos dois é uma previsão por si só.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
section_header("Data Quality", "Proveniência e estado das fontes, sem fallback sintético.")
for meta in [roni_meta, oni_meta, nino_meta]:
    status = "Available" if meta.status == "ok" else "Data unavailable"
    st.markdown(f'<div class="surface" style="margin:.6rem 0"><strong>{meta.source}</strong> · {status_badge(status)}<br><small>Registros: {meta.n_records or "—"} · Coleta: {meta.fetched_at.isoformat() if meta.fetched_at else "—"}<br>Endpoint: {meta.endpoint}</small>{("<br>Detalhe: " + str(meta.message)) if meta.message else ""}</div>', unsafe_allow_html=True)
st.caption("Fontes oficiais: NOAA CPC. O cache de uma hora reduz downloads repetidos; indisponibilidade é exibida como tal e nunca é preenchida com mock, sample, dummy, synthetic, fake ou fallback climático.")
