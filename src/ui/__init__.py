"""UI components for Streamlit interface."""

from . import components as _components
from .components import (
    apply_light_theme,
    status_badge,
    section_header,
    data_unavailable_message,
    enso_state_class,
    state_emoji,
    metric_card,
    render_footer,
    render_regime_timeline as _render_regime_timeline,
)


def render_regime_timeline(roni_df) -> None:
    """Render the visible ModelLBs workspace immediately before the regime timeline."""
    try:
        from src.ui.ml_outlook import render_ml_outlook
        from src.noaa import fetch_oni
        import streamlit as st

        st.markdown(
            """
            <style>
            .model-nav { display:flex; gap:.45rem; margin:1.5rem 0 .15rem; padding:.25rem; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:12px; width:max-content; }
            .model-nav-tab { display:inline-block; padding:.48rem .9rem; border-radius:9px; color:#64748b !important; text-decoration:none !important; font-size:.78rem; font-weight:750; letter-spacing:.01em; }
            .model-nav-tab.active { background:#fff; color:#0f172a !important; box-shadow:0 1px 3px rgba(15,23,42,.08); }
            </style>
            <div class="model-nav" aria-label="Navegação do observatório">
                <a class="model-nav-tab active" href="#modelos-treinados">ModelLBs</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

        oni_df, _ = fetch_oni()
        render_ml_outlook(roni_df, oni_df)
    except Exception:
        # ML is experimental and must never break the core observatory.
        pass
    _render_regime_timeline(roni_df)


# app.py imports render_regime_timeline directly from src.ui.components.
# Replace only that callable while preserving every other component unchanged.
_components.render_regime_timeline = render_regime_timeline

__all__ = [
    "apply_light_theme",
    "status_badge",
    "section_header",
    "data_unavailable_message",
    "enso_state_class",
    "state_emoji",
    "metric_card",
    "render_footer",
    "render_regime_timeline",
]
