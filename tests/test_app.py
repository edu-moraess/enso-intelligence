"""Integrity checks for the single-page Streamlit entrypoint."""
from pathlib import Path


APP = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")


def test_main_page_contains_required_observatory_sections():
    for heading in (
        "ENSO State",
        "RONI History",
        "Pacific Ocean",
        "Climate Context",
        "Methodology",
        "RONI vs ONI",
        "Data & Sources",
    ):
        assert heading in APP
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
    assert "three-month" in APP
    assert "+0.5" in APP
    assert "−0.5" in APP
    assert "intensity" in APP
    assert "not a category official" not in APP
    assert "does not represent forecast error" in APP
