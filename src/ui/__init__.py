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
    """Render ML controls/outlook immediately before the regime timeline."""
    try:
        from src.ui.ml_outlook import render_ml_outlook
        from src.noaa import fetch_oni

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
