"""ENSO regime timeline utilities for the observatory."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.analysis.enso import classify_enso_state


def build_regime_timeline(df: pd.DataFrame, minimum_periods: int = 5) -> go.Figure | None:
    """Build a compact historical ENSO regime timeline from real RONI data.

    Only contiguous non-neutral regimes lasting at least ``minimum_periods``
    overlapping seasons are shown. The classification follows the same RONI
    operational thresholds already used by the observatory.
    """
    if df is None or df.empty or "roni" not in df.columns:
        return None

    work = df.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
    else:
        work["date"] = pd.to_datetime(work.index, errors="coerce")
    work["roni"] = pd.to_numeric(work["roni"], errors="coerce")
    work = work.dropna(subset=["date", "roni"]).sort_values("date").reset_index(drop=True)
    if len(work) < minimum_periods:
        return None

    states = [classify_enso_state(float(value)).value for value in work["roni"]]
    runs: list[dict] = []
    start = 0
    for i in range(1, len(states) + 1):
        if i == len(states) or states[i] != states[start]:
            state = states[start]
            length = i - start
            if state != "Neutral" and length >= minimum_periods:
                segment = work.iloc[start:i]
                runs.append({
                    "state": state,
                    "start": segment["date"].iloc[0],
                    "end": segment["date"].iloc[-1],
                    "peak": float(segment["roni"].max()) if state == "El Niño" else float(segment["roni"].min()),
                    "periods": length,
                })
            start = i

    if not runs:
        return None

    fig = go.Figure()
    y_map = {"La Niña": 0, "Neutral": 1, "El Niño": 2}
    state_labels = ["La Niña", "Neutral", "El Niño"]
    for state in state_labels:
        fig.add_trace(go.Scatter(
            x=[work["date"].min(), work["date"].max()],
            y=[y_map[state], y_map[state]],
            mode="lines",
            line=dict(color="#eef2f7", width=14),
            hoverinfo="skip",
            showlegend=False,
            cliponaxis=False,
        ))

    for episode in runs:
        y = y_map[episode["state"]]
        color = {"El Niño": "#dc2626", "La Niña": "#2563eb"}[episode["state"]]
        duration = episode["periods"]
        fig.add_trace(go.Scatter(
            x=[episode["start"], episode["end"]],
            y=[y, y],
            mode="lines",
            line=dict(color=color, width=14),
            customdata=[[episode["state"], duration, episode["peak"]], [episode["state"], duration, episode["peak"]]],
            hovertemplate=(
                "%{customdata[0]}<br>"
                "%{x|%b %Y}<br>"
                "Duration: %{customdata[1]} overlapping seasons<br>"
                "Peak RONI: %{customdata[2]:+.2f} °C<extra></extra>"
            ),
            showlegend=False,
            cliponaxis=False,
        ))

    # Explicit, conservative margins: avoid edge clipping without relying on
    # axis properties that vary across Plotly versions.
    fig.update_layout(
        height=225,
        margin=dict(l=92, r=56, t=14, b=52),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        showlegend=False,
        hovermode="closest",
        font=dict(color="#475569"),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=10),
        ticklen=0,
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=[0, 1, 2],
        ticktext=state_labels,
        tickfont=dict(size=11),
        showgrid=False,
        zeroline=False,
        fixedrange=True,
        range=[-0.35, 2.35],
    )
    return fig
