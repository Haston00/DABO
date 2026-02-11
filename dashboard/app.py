"""
DABO Streamlit dashboard — main entry point.

Professional UI with McCrory Construction branding.
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
    page_title="DABO | McCrory Construction",
    page_icon="\U0001F3D7",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────

st.markdown("""
<style>
    /* McCrory brand: Navy #00263A, Orange #FF5A19, Cream #EFEAE2 */

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #00263A 0%, #003854 100%);
    }
    [data-testid="stSidebar"] * {
        color: #EFEAE2 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #EFEAE2 !important;
        font-weight: 400;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #FF5A19 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #EFEAE2 !important;
    }

    /* Top branded header bar */
    .brand-header {
        background: linear-gradient(90deg, #00263A 0%, #004D6E 100%);
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .brand-header h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-header .brand-sub {
        color: #FF5A19;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 4px solid #FF5A19;
        padding: 1rem;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    [data-testid="stMetric"] label {
        color: #00263A !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00263A !important;
        font-weight: 700 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #FF5A19;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #E04E10;
        box-shadow: 0 2px 8px rgba(255,90,25,0.3);
    }
    .stButton > button[kind="primary"] {
        background-color: #FF5A19;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: #F8F9FA;
        border-radius: 4px;
        font-weight: 500;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid #E0E0E0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #666;
    }
    .stTabs [aria-selected="true"] {
        color: #00263A !important;
        border-bottom: 3px solid #FF5A19 !important;
        font-weight: 600;
    }

    /* Data tables */
    .stDataFrame {
        border-radius: 6px;
        overflow: hidden;
    }

    /* Page section headers */
    h2 {
        color: #00263A;
        font-weight: 700;
        border-bottom: 2px solid #FF5A19;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: #00263A;
        font-weight: 600;
    }

    /* Info/warning/success boxes */
    .stAlert {
        border-radius: 6px;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #CCC;
        border-radius: 8px;
        padding: 1rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #FF5A19;
    }
</style>
""", unsafe_allow_html=True)

# ── Branded Header ───────────────────────────────────────

st.markdown("""
<div class="brand-header">
    <div>
        <h1>DABO</h1>
        <div class="brand-sub">AI-Powered Plan Review & Scheduling</div>
    </div>
    <div style="text-align: right; color: #EFEAE2; font-size: 0.85rem;">
        McCrory Construction<br/>
        <span style="color: #FF5A19; font-weight: 600;">PM: Timmy McClure</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────

# Logo area
st.sidebar.markdown("""
<div style="text-align: center; padding: 0.5rem 0 1rem 0;">
    <div style="font-size: 2rem; font-weight: 800; color: #FF5A19; letter-spacing: -1px;">DABO</div>
    <div style="font-size: 0.7rem; color: #EFEAE2; letter-spacing: 2px; text-transform: uppercase;">
        McCrory Construction
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Page navigation with icons
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

page_choice = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
    label_visibility="collapsed",
)

st.sidebar.markdown("---")

# Project selector (shown on all pages except setup)
from dashboard.components.widgets import sidebar_project_selector

active_project = None
if page_choice != "Project Setup":
    active_project = sidebar_project_selector()

# Quick stats in sidebar footer
from utils.db import get_conn

conn = get_conn()
project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
sheet_count = conn.execute("SELECT COUNT(*) FROM sheets").fetchone()[0]
conn.close()

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="font-size: 0.75rem; color: #8899AA; padding: 0.5rem 0;">
    <div>Projects: <strong style="color:#FF5A19;">{project_count}</strong></div>
    <div>Sheets indexed: <strong style="color:#FF5A19;">{sheet_count}</strong></div>
    <div style="margin-top: 0.5rem; font-size: 0.65rem; color: #667788;">
        DABO v1.0
    </div>
</div>
""", unsafe_allow_html=True)

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
