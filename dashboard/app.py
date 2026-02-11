"""
DABO Streamlit dashboard — main entry point.

Premium enterprise UI with McCrory Construction branding.
"""
import sys
from pathlib import Path

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

# ── Premium CSS ──────────────────────────────────────────

st.markdown("""
<style>
    /* ═══ IMPORTS ═══ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ═══ ROOT VARIABLES ═══ */
    :root {
        --navy: #00263A;
        --navy-light: #003854;
        --navy-dark: #001B2B;
        --orange: #FF5A19;
        --orange-hover: #E04E10;
        --orange-glow: rgba(255, 90, 25, 0.15);
        --cream: #EFEAE2;
        --cream-light: #F7F5F0;
        --white: #FFFFFF;
        --gray-50: #FAFBFC;
        --gray-100: #F0F2F5;
        --gray-200: #E4E7EB;
        --gray-300: #D1D5DB;
        --gray-500: #6B7280;
        --gray-700: #374151;
        --gray-900: #111827;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
        --shadow-lg: 0 10px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.03);
        --shadow-orange: 0 4px 14px rgba(255, 90, 25, 0.25);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
    }

    /* ═══ GLOBAL ═══ */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ═══ SIDEBAR ═══ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--navy-dark) 0%, var(--navy) 40%, var(--navy-light) 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: rgba(239, 234, 226, 0.85) !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 2px;
    }
    [data-testid="stSidebar"] .stRadio > div > label {
        padding: 0.6rem 1rem !important;
        border-radius: var(--radius-sm) !important;
        transition: all 0.2s ease !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(255, 90, 25, 0.1) !important;
        color: var(--orange) !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div {
        background: rgba(255, 90, 25, 0.15) !important;
        color: var(--orange) !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08) !important;
        margin: 0.75rem 0 !important;
    }

    /* ═══ BRANDED HERO HEADER ═══ */
    .hero-header {
        background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 50%, var(--navy-light) 100%);
        padding: 1.75rem 2.25rem;
        border-radius: var(--radius-lg);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,90,25,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--orange) 0%, transparent 100%);
    }
    .hero-left h1 {
        color: var(--white);
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1px;
        line-height: 1.1;
    }
    .hero-left .hero-tagline {
        color: var(--orange);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-top: 0.4rem;
    }
    .hero-right {
        text-align: right;
        color: rgba(239,234,226,0.7);
        font-size: 0.85rem;
        line-height: 1.6;
        position: relative;
        z-index: 1;
    }
    .hero-right .hero-company {
        font-weight: 600;
        color: var(--cream);
        font-size: 1rem;
        letter-spacing: 0.5px;
    }
    .hero-right .hero-pm {
        color: var(--orange);
        font-weight: 700;
        font-size: 0.9rem;
    }

    /* ═══ METRIC CARDS ═══ */
    [data-testid="stMetric"] {
        background: var(--white);
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-md);
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        box-shadow: var(--shadow-md);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--orange) 0%, #FF8A50 100%);
        border-radius: 4px 0 0 4px;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
        border-color: rgba(255,90,25,0.2);
    }
    [data-testid="stMetric"] label {
        color: var(--gray-500) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        letter-spacing: 0.8px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--navy) !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    /* ═══ BUTTONS ═══ */
    .stButton > button {
        background: linear-gradient(135deg, var(--orange) 0%, #FF7A40 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--orange-hover) 0%, var(--orange) 100%) !important;
        box-shadow: var(--shadow-orange) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ═══ TABS ═══ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--gray-50);
        border-radius: var(--radius-md) var(--radius-md) 0 0;
        padding: 0.25rem 0.25rem 0;
        border-bottom: 2px solid var(--gray-200);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.75rem;
        font-weight: 500;
        color: var(--gray-500);
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--navy);
        background: rgba(0,38,58,0.04);
    }
    .stTabs [aria-selected="true"] {
        color: var(--navy) !important;
        background: var(--white) !important;
        font-weight: 700 !important;
        border-bottom: 3px solid var(--orange) !important;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
    }

    /* ═══ EXPANDERS ═══ */
    .streamlit-expanderHeader {
        background: var(--gray-50) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--navy) !important;
        padding: 0.85rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover {
        background: var(--white) !important;
        border-color: var(--orange) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ═══ HEADINGS ═══ */
    h1, h2 {
        color: var(--navy) !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    h2 {
        font-size: 1.5rem !important;
        border-bottom: 3px solid var(--orange);
        padding-bottom: 0.6rem;
        margin-bottom: 1.25rem;
    }
    h3 {
        color: var(--navy) !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
    }

    /* ═══ DATA TABLES ═══ */
    [data-testid="stDataFrame"] {
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--gray-200);
    }

    /* ═══ FILE UPLOADER ═══ */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        padding: 2rem 1rem !important;
        background: var(--gray-50) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--orange) !important;
        background: var(--orange-glow) !important;
    }

    /* ═══ FORMS ═══ */
    [data-testid="stForm"] {
        background: var(--white);
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
    }

    /* ═══ SELECT BOXES & INPUTS ═══ */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: var(--radius-sm) !important;
        border-color: var(--gray-300) !important;
        transition: all 0.2s ease !important;
    }
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--orange) !important;
        box-shadow: 0 0 0 3px var(--orange-glow) !important;
    }

    /* ═══ ALERTS ═══ */
    .stAlert {
        border-radius: var(--radius-md) !important;
        border-left: 4px solid !important;
    }

    /* ═══ PROGRESS BAR ═══ */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--orange) 0%, #FF8A50 100%) !important;
        border-radius: 10px;
    }

    /* ═══ CUSTOM COMPONENTS ═══ */
    .stat-card {
        background: var(--white);
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        text-align: center;
    }
    .stat-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-3px);
    }
    .stat-card .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--navy);
        line-height: 1;
    }
    .stat-card .stat-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--gray-500);
        margin-top: 0.5rem;
    }
    .stat-card .stat-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .info-banner {
        background: linear-gradient(135deg, var(--cream-light) 0%, var(--cream) 100%);
        border: 1px solid rgba(0,38,58,0.08);
        border-left: 4px solid var(--orange);
        border-radius: var(--radius-md);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .info-banner strong {
        color: var(--navy);
        font-size: 1rem;
    }
    .info-banner p {
        color: var(--gray-700);
        font-size: 0.9rem;
        margin: 0.25rem 0 0 0;
    }

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--gray-500);
    }
    .empty-state .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    .empty-state .empty-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--gray-700);
        margin-bottom: 0.5rem;
    }
    .empty-state .empty-desc {
        font-size: 0.95rem;
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.5;
    }

    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, var(--orange) 0%, transparent 50%);
        border: none;
        margin: 2rem 0;
        border-radius: 3px;
    }

    /* ═══ SCROLLBAR ═══ */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--gray-100);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--gray-300);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--orange);
    }
</style>
""", unsafe_allow_html=True)

# ── Hero Header ──────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div class="hero-left">
        <h1>DABO</h1>
        <div class="hero-tagline">AI-Powered Plan Review & Scheduling</div>
    </div>
    <div class="hero-right">
        <div class="hero-company">McCrory Construction</div>
        <div class="hero-pm">PM: Timmy McClure</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────

st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem 0 0.5rem 0;">
    <div style="font-size: 2.2rem; font-weight: 900; color: #FF5A19;
                letter-spacing: -2px; line-height: 1;">DABO</div>
    <div style="font-size: 0.6rem; color: rgba(239,234,226,0.5);
                letter-spacing: 3px; text-transform: uppercase;
                margin-top: 0.3rem;">PLAN REVIEW ENGINE</div>
    <div style="width: 40px; height: 2px; background: #FF5A19;
                margin: 0.75rem auto 0; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

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

from dashboard.components.widgets import sidebar_project_selector

active_project = None
if page_choice != "Project Setup":
    active_project = sidebar_project_selector()

from utils.db import get_conn

conn = get_conn()
project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
sheet_count = conn.execute("SELECT COUNT(*) FROM sheets").fetchone()[0]
conn.close()

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="padding: 0.5rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;
                padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
        <span style="font-size: 0.7rem; color: rgba(239,234,226,0.4);
                     text-transform: uppercase; letter-spacing: 1px;">Projects</span>
        <span style="font-size: 1rem; font-weight: 700; color: #FF5A19;">{project_count}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center;
                padding: 0.4rem 0;">
        <span style="font-size: 0.7rem; color: rgba(239,234,226,0.4);
                     text-transform: uppercase; letter-spacing: 1px;">Sheets</span>
        <span style="font-size: 1rem; font-weight: 700; color: #FF5A19;">{sheet_count}</span>
    </div>
    <div style="margin-top: 1rem; padding-top: 0.75rem;
                border-top: 1px solid rgba(255,255,255,0.05);
                text-align: center;">
        <span style="font-size: 0.6rem; color: rgba(239,234,226,0.25);
                     letter-spacing: 1px;">DABO v1.0</span>
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
