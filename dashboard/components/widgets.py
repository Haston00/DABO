"""
Reusable Streamlit UI components for DABO dashboard.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from utils.db import get_conn


def sidebar_project_selector() -> dict | None:
    """Render project selector in sidebar. Returns selected project dict or None."""
    conn = get_conn()
    projects = conn.execute(
        "SELECT id, name, building_type, square_feet FROM projects ORDER BY id DESC"
    ).fetchall()
    conn.close()

    if not projects:
        st.sidebar.warning("No projects yet. Create one in Project Setup.")
        return None

    options = {f"{p['name']} (#{p['id']})": dict(p) for p in projects}
    choice = st.sidebar.selectbox("Active Project", list(options.keys()))
    return options[choice] if choice else None


def severity_badge(severity: str) -> str:
    """Return colored markdown badge for severity level."""
    colors = {
        "CRITICAL": "red",
        "MAJOR": "orange",
        "MINOR": "gold",
        "INFO": "blue",
    }
    color = colors.get(severity.upper(), "gray")
    return f":{color}[**{severity.upper()}**]"


def status_badge(status: str) -> str:
    """Return colored badge for processing status."""
    colors = {
        "complete": "green",
        "processing": "blue",
        "error": "red",
        "pending": "gray",
    }
    color = colors.get(status.lower(), "gray")
    return f":{color}[{status}]"


def metric_row(metrics: dict):
    """Render a row of metric cards from a dict."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)


def file_upload_area(label: str = "Upload Construction Drawings", types: list | None = None):
    """Standard file upload widget for construction documents."""
    if types is None:
        types = ["pdf"]
    return st.file_uploader(
        label,
        type=types,
        accept_multiple_files=True,
        help="Upload Bluebeam PDFs or spec documents",
    )


def confirm_action(key: str, label: str = "Confirm") -> bool:
    """Two-step confirmation button."""
    if st.button(label, key=f"{key}_btn"):
        st.session_state[f"{key}_confirm"] = True
    if st.session_state.get(f"{key}_confirm"):
        col1, col2 = st.columns(2)
        if col1.button("Yes, proceed", key=f"{key}_yes"):
            st.session_state[f"{key}_confirm"] = False
            return True
        if col2.button("Cancel", key=f"{key}_no"):
            st.session_state[f"{key}_confirm"] = False
    return False


def empty_state(icon: str, title: str, message: str):
    """Show empty state placeholder."""
    st.markdown(f"### {icon} {title}")
    st.caption(message)
