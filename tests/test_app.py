"""Integrity checks for the single-page Streamlit entrypoint."""
from pathlib import Path


APP = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")


def test_main_page_contains_required_observatory_sections():
    for heading in ("ENSO State", "RONI history", "Pacific Ocean", "Climate Impacts", "Methodology", "Data Quality"):
        assert heading in APP
    assert "Use the sidebar to navigate" not in APP
    assert '[data-testid="stSidebar"]' in APP


def test_main_page_has_no_synthetic_climate_series():
    forbidden_data_construction = ("np.array", "pd.DataFrame([", "synthetic_values", "dummy_values", "fake_values")
    assert not any(token in APP for token in forbidden_data_construction)
    assert "fetch_roni" in APP and "fetch_oni" in APP and "fetch_nino_indices" in APP


def test_main_page_handles_source_outages_without_fallback_values():
    assert "data_unavailable_message" in APP
    assert "if roni_df is None or roni_df.empty" in APP
    assert "if nino_df is None or nino_df.empty" in APP
