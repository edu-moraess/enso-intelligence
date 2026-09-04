"""Integrity checks for the single-page Streamlit entrypoint."""
from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
COMPONENTS = (ROOT / "src" / "ui" / "components.py").read_text(encoding="utf-8")


def test_main_page_contains_required_observatory_sections():
    # Headings rendered directly from app.py
    for heading in (
        "CURRENT CONDITIONS",
        "ENSO SIGNAL",
        "HISTORICAL ANALOGUES",
        "PACIFIC CONDITIONS",
        "ANALYTICAL VIEW",
        "METHODOLOGY",
        "DATA & PROVENANCE",
    ):
        assert heading in APP

    # Regime timeline is owned by components.render_regime_timeline and
    # invoked explicitly from app.py with the already-loaded RONI frame.
    assert "render_regime_timeline(roni_df)" in APP
    assert "ENSO REGIME TIMELINE" in COMPONENTS

    assert "Use the sidebar to navigate" not in APP
    assert "st.sidebar" not in APP
    assert "stSidebar" in APP


def test_main_page_has_no_synthetic_climate_series():
    forbidden_data_construction = (
        "synthetic_values",
        "dummy_values",
        "fake_values",
        "mock_climate",
        "fallback_climate",
    )
    assert not any(token in APP for token in forbidden_data_construction)
    assert "fetch_roni" in APP and "fetch_oni" in APP and "fetch_nino_indices" in APP


def test_main_page_handles_source_outages_without_fallback_values():
    assert "data_unavailable_message" in APP
    assert "if roni_df is None or roni_df.empty" in APP
    assert "if nino_df is None or nino_df.empty" in APP
    assert "fetch_nino_indices" in APP


def test_refined_ui_keeps_scientific_guardrails():
    # Operational wording actually present in the current one-page UI
    assert "3-month running mean" in APP
    assert "+0.5" in APP
    assert "−0.5" in APP
    assert "intensity" in APP
    assert "not a category official" not in APP
    # Forecast disclaimer is written in Portuguese in the product copy
    assert "não representam erro de previsão" in APP
    assert "not a forecast" in APP
