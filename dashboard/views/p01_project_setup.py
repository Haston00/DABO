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
    st.markdown("""
    <div style="background: #F8F9FA; padding: 1.25rem; border-radius: 8px;
                border-left: 4px solid #FF5A19; margin-bottom: 1.5rem;">
        <strong style="color: #00263A;">Create a new project</strong><br/>
        <span style="color: #666; font-size: 0.9rem;">
            Enter project details below. You can upload drawings on the Ingestion page after creation.
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("new_project"):
        name = st.text_input("Project Name", placeholder="McCrory Office Tower")

        col1, col2, col3 = st.columns(3)
        building_type = col1.selectbox(
            "Building Type",
            ["office", "retail", "warehouse", "medical", "education", "mixed_use"],
        )
        square_feet = col2.number_input(
            "Square Feet", min_value=1000, max_value=5_000_000,
            value=50000, step=1000, format="%d",
        )
        stories = col3.number_input("Stories", min_value=1, max_value=100, value=2)

        notes = st.text_area(
            "Project Notes (optional)",
            placeholder="PM name, address, scope notes...",
            height=80,
        )

        submitted = st.form_submit_button("Create Project")

    if submitted and name.strip():
        conn = get_conn()
        cursor = conn.execute(
            "INSERT INTO projects (name, building_type, square_feet, stories, notes) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), building_type, square_feet, stories, notes.strip()),
        )
        conn.commit()
        pid = cursor.lastrowid
        conn.close()

        proj_dir = Path(PROJECTS_DIR) / str(pid)
        proj_dir.mkdir(parents=True, exist_ok=True)

        st.success(f"Project **{name}** created (ID #{pid})")
        st.rerun()
    elif submitted:
        st.error("Project name is required.")


def _existing_projects():
    conn = get_conn()
    projects = conn.execute(
        "SELECT p.id, p.name, p.building_type, p.square_feet, p.stories, p.notes, p.created_at, "
        "       (SELECT COUNT(*) FROM sheets WHERE project_id = p.id) as sheet_count, "
        "       (SELECT COUNT(*) FROM project_files WHERE project_id = p.id) as file_count "
        "FROM projects p ORDER BY p.id DESC"
    ).fetchall()
    conn.close()

    if not projects:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #999;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">&#128203;</div>
            <div style="font-size: 1.1rem; font-weight: 500; color: #666;">No projects yet</div>
            <div style="font-size: 0.9rem;">Create your first project above to get started.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for p in projects:
        with st.expander(f"#{p['id']} -- {p['name']}", expanded=(len(projects) == 1)):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Type", p["building_type"].title())
            c2.metric("Square Feet", f"{p['square_feet']:,}")
            c3.metric("Stories", p["stories"])
            c4.metric("Files", p["file_count"])
            c5.metric("Sheets", p["sheet_count"])

            if p["notes"]:
                st.caption(p["notes"])
            st.caption(f"Created: {p['created_at']}")
