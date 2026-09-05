"""Compact ML training and outlook panel for the one-page ENSO observatory."""
from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.ml.features import build_feature_table
from src.ml.inference import load_metadata, load_production_model, predict_next_roni

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "roni_forecast.joblib"
METADATA_PATH = ROOT / "models" / "metadata.json"
BENCHMARK_PATH = ROOT / "models" / "benchmark.json"


def _load_benchmark() -> dict | None:
    if not BENCHMARK_PATH.exists():
        return None
    try:
        return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _render_benchmark(results: list[dict], winner: str | None) -> None:
    """Render the model comparison as a compact visual benchmark."""
    if not results:
        return

    names = [str(item.get("name", "—")) for item in results]
    rmse = [float(item.get("rmse", 0.0)) for item in results]
    mae = [float(item.get("mae", 0.0)) for item in results]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=names,
            y=rmse,
            name="RMSE",
            text=[f"{value:.3f}" for value in rmse],
            textposition="outside",
            hovertemplate="%{x}<br>RMSE: %{y:.3f} °C<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=names,
            y=mae,
            name="MAE",
            text=[f"{value:.3f}" for value in mae],
            textposition="outside",
            hovertemplate="%{x}<br>MAE: %{y:.3f} °C<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=8, r=8, t=22, b=8),
        barmode="group",
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Error (°C)", gridcolor="#edf2f7", zeroline=False),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True})
    st.caption("Expanding walk-forward validation · no random split · lower is better.")

    with st.expander("Validation details", expanded=False):
        for result in results:
            name = result.get("name", "—")
            rmse_value = float(result.get("rmse", 0.0))
            mae_value = float(result.get("mae", 0.0))
            n_test = int(result.get("n_test", 0))
            label = "🏆 Champion" if name == winner else ("Baseline" if name == "Persistence" else "Candidate")
            st.markdown(
                f"`{name}` · **{label}** · RMSE {rmse_value:.3f} °C · "
                f"MAE {mae_value:.3f} °C · n={n_test}"
            )


def _train_now(roni_df, oni_df) -> dict:
    """Run the same auditable training pipeline used by automation."""
    from scripts.train_enso_ml import train

    return train(ROOT / "models")


def _render_training_panel(roni_df, oni_df) -> None:
    st.markdown('<div id="modelos-treinados"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">MODELOS TREINADOS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Laboratório operacional dos modelos validados e do outlook produzido pelo champion.</div>',
        unsafe_allow_html=True,
    )

    model_exists = MODEL_PATH.exists() and METADATA_PATH.exists()
    benchmark_payload = _load_benchmark()
    metadata = load_metadata(METADATA_PATH) if model_exists else None
    winner = (
        metadata.get("model")
        if metadata and metadata.get("status") == "production"
        else (benchmark_payload or {}).get("winner")
    )

    status_col, action_col = st.columns([4, 1], vertical_alignment="center")
    with status_col:
        if model_exists and metadata and metadata.get("status") == "production":
            st.markdown(
                f"**Model status** · 🟢 **{winner or 'Champion'}**  \n"
                "Validated against Persistence with expanding walk-forward validation."
            )
        else:
            st.markdown(
                "**Model status** · ⚪ **Not available**  \n"
                "Train a validated model before showing an ML outlook."
            )
    with action_col:
        train_clicked = st.button(
            "↻ Update model",
            key="enso_ml_train_now",
            type="secondary",
            use_container_width=True,
            help="Runs the walk-forward benchmark and saves a learned model only when it beats Persistence.",
        )

    if train_clicked:
        with st.status("Updating ENSO ML model…", expanded=True) as status:
            try:
                result = _train_now(roni_df, oni_df)
                st.write(f"Supervised rows: {result.get('rows', '—')}")
                _render_benchmark(result.get("results", []), result.get("winner"))
                if result.get("published"):
                    status.update(
                        label=f"Champion updated: {result['winner']}",
                        state="complete",
                        expanded=False,
                    )
                    st.success(
                        "Validated model updated successfully. The previous champion remains protected unless the new benchmark wins."
                    )
                    st.rerun()
                else:
                    status.update(label="Champion unchanged", state="complete", expanded=False)
                    st.info("No learned model beat Persistence. The existing champion was left unchanged.")
            except Exception as exc:
                status.update(label="Model update failed", state="error", expanded=True)
                st.error(f"Não foi possível concluir a atualização: {exc}")

    if benchmark_payload and not train_clicked:
        _render_benchmark(benchmark_payload.get("results", []), winner)


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
    fig.add_trace(
        go.Scatter(
            x=history["date"],
            y=history["roni"],
            mode="lines+markers",
            name="Observed",
            line=dict(width=2.4),
            marker=dict(size=5),
            hovertemplate="%{x|%b %Y}<br>Observed RONI: %{y:+.2f} °C<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[history.iloc[-1]["date"], future_date],
            y=[latest, prediction],
            mode="lines+markers",
            name="ML outlook",
            line=dict(width=2.4, dash="dash"),
            marker=dict(size=8),
            hovertemplate="%{x|%b %Y}<br>ML outlook: %{y:+.2f} °C<extra></extra>",
        )
    )
    fig.add_hline(y=0.5, line_dash="dot", line_width=1, annotation_text="El Niño")
    fig.add_hline(y=-0.5, line_dash="dot", line_width=1, annotation_text="La Niña")
    fig.update_layout(
        height=330,
        margin=dict(l=8, r=8, t=12, b=8),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(title="RONI (°C)", gridcolor="#edf2f7", zeroline=False),
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
    """Render the model laboratory when a validated dataset is available."""
    if roni_df is None or oni_df is None or roni_df.empty or oni_df.empty:
        return
    _render_training_panel(roni_df, oni_df)
    _render_outlook(roni_df, oni_df)
