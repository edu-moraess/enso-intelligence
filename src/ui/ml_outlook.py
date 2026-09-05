"""Compact ML training and outlook panel for the one-page ENSO observatory."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.ml.features import build_feature_table
from src.ml.inference import load_metadata, load_production_model, predict_next_roni

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "roni_forecast.joblib"
METADATA_PATH = ROOT / "models" / "metadata.json"
BENCHMARK_PATH = ROOT / "models" / "benchmark.json"


def _render_benchmark(results: list[dict], winner: str | None) -> None:
    st.markdown("**Benchmark — expanding walk-forward**")
    for result in results:
        name = result.get("name", "—")
        rmse = float(result.get("rmse", 0.0))
        mae = float(result.get("mae", 0.0))
        n_test = int(result.get("n_test", 0))
        if name == "Persistence":
            label = "Baseline"
        elif name == winner:
            label = "🏆 Champion"
        else:
            label = "Candidate"
        st.markdown(f"`{name}` · **{label}** · RMSE {rmse:.3f} °C · MAE {mae:.3f} °C · n={n_test}")


def _train_now(roni_df, oni_df) -> dict:
    """Run the same auditable training pipeline used by automation."""
    from scripts.train_enso_ml import train

    # The Streamlit process writes only the same model artifacts used by inference.
    return train(ROOT / "models")


def _render_training_panel(roni_df, oni_df) -> None:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ML OUTLOOK</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Experimental one-step statistical outlook for the next RONI observation.</div>', unsafe_allow_html=True)

    model_exists = MODEL_PATH.exists() and METADATA_PATH.exists()
    c1, c2 = st.columns([1, 3])
    with c1:
        train_clicked = st.button(
            "Train model now",
            key="enso_ml_train_now",
            type="primary",
            use_container_width=True,
            help="Executa o benchmark walk-forward e salva o champion somente se ele superar a persistência.",
        )
    with c2:
        st.caption("RONI + ONI · Persistence vs Ridge vs Gradient Boosting · sem random split")

    if train_clicked:
        with st.status("Treinando ENSO ML…", expanded=True) as status:
            try:
                result = _train_now(roni_df, oni_df)
                st.write(f"Supervised rows: {result.get('rows', '—')}")
                _render_benchmark(result.get("results", []), result.get("winner"))
                if result.get("published"):
                    status.update(label=f"Champion salvo: {result['winner']}", state="complete", expanded=True)
                    st.success("Modelo validado contra a baseline de persistência e salvo em models/roni_forecast.joblib.")
                else:
                    status.update(label="Nenhum modelo aprendido superou a persistência", state="complete", expanded=True)
                    st.warning("Nenhum modelo aprendido superou a baseline. O champion anterior permanece intacto.")
            except Exception as exc:
                status.update(label="Treinamento falhou", state="error", expanded=True)
                st.error(f"Não foi possível concluir o treinamento: {exc}")

    # Read the persisted benchmark after training (or from a previous run).
    if BENCHMARK_PATH.exists():
        try:
            import json
            payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
            results = payload.get("results", [])
            metadata = load_metadata(METADATA_PATH)
            winner = metadata.get("model") if metadata and metadata.get("status") == "production" else None
            if results and not train_clicked:
                _render_benchmark(results, winner)
        except (OSError, ValueError, TypeError):
            pass


def _render_outlook(roni_df, oni_df) -> None:
    if roni_df is None or oni_df is None or roni_df.empty or oni_df.empty:
        return

    model = load_production_model(MODEL_PATH)
    metadata = load_metadata(METADATA_PATH)
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


def render_ml_outlook(roni_df, oni_df) -> None:
    """Render training controls and the outlook when a validated model exists."""
    if roni_df is None or oni_df is None or roni_df.empty or oni_df.empty:
        return
    _render_training_panel(roni_df, oni_df)
    _render_outlook(roni_df, oni_df)
