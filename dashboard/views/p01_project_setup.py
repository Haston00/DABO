"""
Page 01 — Project Setup.

Create new projects, configure building type/SF/stories,
upload drawing files.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from utils.db import get_conn
from config.settings import PROJECTS_DIR


def render():
    st.header("Project Setup")

    tab_new, tab_existing = st.tabs(["New Project", "Existing Projects"])

    with tab_new:
        _new_project_form()

    with tab_existing:
        _existing_projects()


def _new_project_form():
    with st.form("new_project"):
        name = st.text_input("Project Name", placeholder="Baker Office Tower")
        building_type = st.selectbox(
            "Building Type",
            ["office", "retail", "warehouse", "medical", "education", "mixed_use"],
        )
        col1, col2 = st.columns(2)
        square_feet = col1.number_input("Square Feet", min_value=1000, max_value=5_000_000, value=50000, step=1000)
        stories = col2.number_input("Stories", min_value=1, max_value=100, value=2)

        submitted = st.form_submit_button("Create Project")

    if submitted and name.strip():
        conn = get_conn()
        cursor = conn.execute(
            "INSERT INTO projects (name, building_type, square_feet, stories) VALUES (?, ?, ?, ?)",
            (name.strip(), building_type, square_feet, stories),
        )
        conn.commit()
        pid = cursor.lastrowid
        conn.close()

        # Create project directory
        proj_dir = Path(PROJECTS_DIR) / str(pid)
        proj_dir.mkdir(parents=True, exist_ok=True)

        st.success(f"Project **{name}** created (ID #{pid})")
        st.rerun()
    elif submitted:
        st.error("Project name is required.")


def _existing_projects():
    conn = get_conn()
    projects = conn.execute(
        "SELECT id, name, building_type, square_feet, stories, created_at FROM projects ORDER BY id DESC"
    ).fetchall()
    conn.close()

    if not projects:
        st.info("No projects yet. Create one above.")
        return

    for p in projects:
        with st.expander(f"#{p['id']} — {p['name']}"):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Type:** {p['building_type']}")
            c2.write(f"**SF:** {p['square_feet']:,}")
            c3.write(f"**Stories:** {p['stories']}")
            st.caption(f"Created: {p['created_at']}")
