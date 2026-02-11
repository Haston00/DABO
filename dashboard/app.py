"""
DABO Streamlit dashboard — main entry point.

Sidebar navigation with project selector and 8 main pages.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Run: pip install streamlit")
    sys.exit(1)

st.set_page_config(
    page_title="DABO -- Plan Review & Scheduling",
    page_icon="\U0001F4D0",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────

st.sidebar.title("DABO")
st.sidebar.caption("Baker Construction / Briegan Concrete")
st.sidebar.divider()

# Page navigation
PAGES = {
    "Project Setup": "p01",
    "PDF Ingestion": "p02",
    "Sheet Index": "p03",
    "Plan Review": "p04",
    "RFI Log": "p05",
    "Schedule": "p06",
    "Export Center": "p07",
    "Feedback": "p08",
}

page_choice = st.sidebar.radio("Navigation", list(PAGES.keys()))

st.sidebar.divider()

# Project selector (shown on all pages except setup)
from dashboard.components.widgets import sidebar_project_selector

active_project = None
if page_choice != "Project Setup":
    active_project = sidebar_project_selector()

# Quick stats in sidebar
from utils.db import get_conn

conn = get_conn()
project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
conn.close()

st.sidebar.divider()
st.sidebar.caption(f"Projects: {project_count}")

# ── Page Routing ─────────────────────────────────────────

if page_choice == "Project Setup":
    from dashboard.views.p01_project_setup import render
    render()

elif page_choice == "PDF Ingestion":
    from dashboard.views.p02_ingestion import render
    render(active_project)

elif page_choice == "Sheet Index":
    from dashboard.views.p03_sheet_index import render
    render(active_project)

elif page_choice == "Plan Review":
    from dashboard.views.p04_plan_review import render
    render(active_project)

elif page_choice == "RFI Log":
    from dashboard.views.p05_rfi_log import render
    render(active_project)

elif page_choice == "Schedule":
    from dashboard.views.p06_schedule import render
    render(active_project)

elif page_choice == "Export Center":
    from dashboard.views.p07_export import render
    render(active_project)

elif page_choice == "Feedback":
    from dashboard.views.p08_feedback import render
    render(active_project)
