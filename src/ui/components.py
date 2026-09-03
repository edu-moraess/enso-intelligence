"""Reusable Streamlit UI components for ENSO Intelligence.

Keep presentation helpers small and dependency-light so every Streamlit page can
import them safely in Streamlit Community Cloud.
"""

from __future__ import annotations

import html

import streamlit as st


def apply_light_theme() -> None:
    """Apply the project's light scientific visual theme."""
    st.markdown(
        """
        <style>
        :root {
            --enso-text: #111827;
            --enso-muted: #6b7280;
            --enso-border: #e5e7eb;
            --enso-surface: #ffffff;
        }
        .stApp {
            background: #f8fafc;
            color: var(--enso-text);
        }
        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.92);
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--enso-border);
        }
        .enso-card {
            background: var(--enso-surface);
            border: 1px solid var(--enso-border);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }
        .enso-section-title {
            color: var(--enso-text);
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0;
        }
        .enso-section-caption {
            color: var(--enso-muted);
            font-size: 0.9rem;
            margin-top: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, delta: str | None = None) -> None:
    """Render a compact metric card."""
    delta_html = ""
    if delta is not None:
        delta_html = (
            f'<div style="margin-top:.35rem;color:#6b7280;font-size:.8rem;">'
            f"{html.escape(str(delta))}</div>"
        )
    st.markdown(
        f"""
        <div class="enso-card">
            <div style="font-size:.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:.04em;">
                {html.escape(str(label))}
            </div>
            <div style="font-size:1.45rem;font-weight:700;color:#111827;margin-top:.2rem;">
                {html.escape(str(value))}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(label: str, state: str | None = None) -> str:
    """Return a semantic HTML status badge."""
    text = state or label
    normalized = str(text).lower()
    if "el niño" in normalized or "el nino" in normalized:
        background, foreground = "#fee2e2", "#991b1b"
    elif "la niña" in normalized or "la nina" in normalized:
        background, foreground = "#dbeafe", "#1e40af"
    else:
        background, foreground = "#dcfce7", "#166534"
    return (
        f'<span style="display:inline-block;padding:.3rem .65rem;border-radius:999px;'
        f'background:{background};color:{foreground};font-weight:700;font-size:.82rem;">'
        f"{html.escape(str(text))}</span>"
    )


def enso_state_html(state: str) -> str:
    """Return a large semantic ENSO state indicator as HTML."""
    normalized = str(state).lower()
    if "el niño" in normalized or "el nino" in normalized:
        symbol, background, foreground = "🔴", "#fee2e2", "#991b1b"
    elif "la niña" in normalized or "la nina" in normalized:
        symbol, background, foreground = "🔵", "#dbeafe", "#1e40af"
    else:
        symbol, background, foreground = "🟢", "#dcfce7", "#166534"
    return (
        f'<div style="display:inline-flex;align-items:center;gap:.5rem;margin-top:.35rem;'
        f'padding:.45rem .75rem;border-radius:10px;background:{background};color:{foreground};'
        f'font-size:1.25rem;font-weight:800;">{symbol} {html.escape(str(state))}</div>'
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    """Render a consistent section heading."""
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="enso-section-caption">{html.escape(str(subtitle))}</div>'
    st.markdown(
        f'<div class="enso-section-title">{html.escape(str(title))}</div>{subtitle_html}',
        unsafe_allow_html=True,
    )


def data_unavailable_message(source: str, message: str | None = None) -> None:
    """Explain a data-source outage without substituting synthetic data."""
    detail = message or "The source did not return usable data."
    st.warning(f"Data unavailable from {source}. {detail}")
