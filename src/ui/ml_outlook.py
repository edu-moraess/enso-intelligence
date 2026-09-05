"""Compact ML outlook panel for the one-page ENSO observatory."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.ml.features import build_feature_table
from src.ml.inference import load_metadata, load_production_model, predict_next_roni


def render_ml_outlook(roni_df, oni_df) -> None:
    """Render the ML outlook only when a validated production model exists."""
    if roni_df is None or oni_df is None or roni_df.empty or oni_df.empty:
        return

    model_path = Path(__file__).resolve().parents[2] / "models" / "roni_forecast.joblib"
    metadata_path = Path(__file__).resolve().parents[2] / "models" / "metadata.json"
    model = load_production_model(model_path)
    metadata = load_metadata(metadata_path)
    if model is None or metadata is None or metadata.get("status") != "production":
        return

    table = build_feature_table(roni_df, oni_df)
    prediction = predict_next_roni(table, model=model)
    if prediction is None:
        return

    latest = float(roni_df.iloc[-1]["roni"])
    latest_date = roni_df.iloc[-1]["date"]
    future_date = table.iloc[-1]["date"]
    if future_date <= latest_date:
        future_date = latest_date

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown("<div class=\"section-subtitle\"><h3>ML OUTLOOK</h3><div class=\"chart-meta\">Experimental one-step statistical outlook for the next RONI observation.</div></div>", unsafe_allow_html=True)

    fig = go.Figure()
    history = roni_df.tail(24)
    fig.add_trace(go.Scatter(
        x=history["date"], y=history["roni"], mode="lines+markers", name="Observed",
        line=dict(width=2.4), marker=dict(size=5),
        hovertemplate="%{x|%b %Y}<br>Observed RONI: %{y:+.2f} °C<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[history.iloc[-1]["date"], future_date], y=[latest, prediction],
        mode="lines+markers", name="ML outlook", line=dict(width=2.4, dash="dash"),
        marker=dict(size=8), hovertemplate="%{x|%b %Y}<br>ML outlook: %{y:+.2f} °C<extra></extra>",
    ))
    fig.add_hline(y=0.5, line_dash="dot", line_width=1, annotation_text="El Niño")
    fig.add_hline(y=-0.5, line_dash="dot", line_width=1, annotation_text="La Niña")
    fig.update_layout(
        height=330, margin=dict(l=8, r=8, t=12, b=8),
        plot_bgcolor="#fff", paper_bgcolor="#fff", hovermode="x unified",
        xaxis=dict(showgrid=False), yaxis=dict(title="RONI (°C)", gridcolor="#edf2f7", zeroline=False),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Next RONI", f"{prediction:+.2f} °C")
    c2.metric("Model", metadata.get("model", "—"))
    c3.metric("Validation RMSE", f"{float(metadata['validation_rmse']):.2f} °C")
    c4.metric("Trained until", str(metadata.get("trained_until", "—")))
    st.caption("Experimental statistical/ML outlook — not an official NOAA forecast.")
