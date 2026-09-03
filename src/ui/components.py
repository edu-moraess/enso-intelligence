"""Reusable Streamlit UI components — light theme, climate observatory aesthetic."""

from __future__ import annotations

from typing import Optional

import streamlit as st


def apply_light_theme() -> None:
    """Inject CSS for a clean light scientific observatory look."""
    st.markdown(
        """
        <style>
        .stApp { background-color: #f5f7fa; color: #1a1a1a; }
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e5e7eb;
        }
        h1, h2, h3 { color: #111827 !important; font-weight: 650 !important; letter-spacing: -0.02em; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        div[data-testid="stMetric"] label {
            color: #6b7280 !important;
            font-size: 0.75rem !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #111827 !important;
            font-weight: 650;
        }
        .obs-hero {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1.75rem 2rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .obs-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .state-el-nino { color: #b91c1c; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .state-la-nina { color: #1d4ed8; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .state-neutral { color: #374151; font-weight: 800; font-size: 2rem; letter-spacing: -0.03em; }
        .intensity-label { color: #4b5563; font-size: 1.05rem; margin-top: 0.15rem; }
        .badge {
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 650;
            letter-spacing: 0.03em;
        }
        .badge-ok { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
        .badge-warn { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
        .badge-err { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-info { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .badge-hot { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-cold { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .badge-neu { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
        .flow-step {
            display: inline-block;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.35rem 0.7rem;
            margin: 0.2rem;
            font-size: 0.85rem;
            color: #374151;
        }
        .section-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6b7280;
            margin-bottom: 0.35rem;
        }
        .block-container { padding-top: 1.25rem; max-width: 1100px; }
        hr { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def status_badge(status: str) -> str:
    mapping = {
        "Connected": "badge-ok",
        "Updated": "badge-ok",
        "Warning": "badge-warn",
        "Error": "badge-err",
        "Unavailable": "badge-err",
    }
    cls = mapping.get(status, "badge-info")
    return f'<span class="badge {cls}">{status}</span>'


def data_unavailable_message(source: str = "NOAA", detail: Optional[str] = None) -> None:
    msg = f"**{source} data unavailable.** Please try again later."
    if detail:
        msg += f"\n\n_{detail}_"
    st.warning(msg)


def enso_state_class(state: str) -> str:
    return {
        "El Niño": "state-el-nino",
        "La Niña": "state-la-nina",
        "Neutral": "state-neutral",
    }.get(state, "state-neutral")


def state_emoji(state: str) -> str:
    return {"El Niño": "🔴", "La Niña": "🔵", "Neutral": "⚪"}.get(state, "⚪")
