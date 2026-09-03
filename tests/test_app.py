"""Integrity checks for the single-page Streamlit entrypoint."""
from pathlib import Path


APP = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")


def test_main_page_contains_required_observatory_sections():
    for heading in (
        "Current ENSO State",
        "RONI",
        "Pacific Ocean",
        "Climate Implications",
        "Methodology",
        "Data Provenance",
        "Observation ≠ Forecast",
    ):
        assert heading in APP
    assert "Use the sidebar to navigate" not in APP
    assert "st.sidebar" in APP or "stSidebar" in APP or "with st.sidebar" in APP


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
    assert "weekly_df is not None and not weekly_df.empty" in APP
    assert "NOAA CPC weekly Niño indices" in APP


def test_etapa2_scientific_markers_present():
    assert "historical_percentile" in APP
    assert "Phase position" in APP or "intensity_gauge_position" in APP
    assert "Δ 12" in APP or "delta_12" in APP
    assert "threshold-defined" in APP
    assert "Spatial SST Analysis" in APP
