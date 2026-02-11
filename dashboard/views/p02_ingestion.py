"""
Page 02 — PDF Ingestion.

Upload files, trigger processing, view extraction status.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from utils.db import get_conn
from config.settings import PROJECTS_DIR
from dashboard.components.widgets import severity_badge, status_badge


def render(project: dict | None):
    st.header("PDF Ingestion")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]

    tab_upload, tab_status = st.tabs(["Upload Files", "Processing Status"])

    with tab_upload:
        _upload_section(pid)

    with tab_status:
        _status_section(pid)


def _upload_section(pid: int):
    uploaded = st.file_uploader(
        "Upload Construction Drawings",
        type=["pdf"],
        accept_multiple_files=True,
        help="Bluebeam PDFs or plain drawing PDFs",
    )

    if uploaded and st.button("Process Uploads"):
        proj_dir = Path(PROJECTS_DIR) / str(pid)
        proj_dir.mkdir(parents=True, exist_ok=True)

        progress = st.progress(0, text="Starting...")
        total = len(uploaded)

        for i, f in enumerate(uploaded):
            progress.progress((i + 1) / total, text=f"Processing {f.name}...")

            # Save uploaded file
            dest = proj_dir / f.name
            dest.write_bytes(f.getbuffer())

            # Record in DB
            conn = get_conn()
            from utils.helpers import file_hash
            fhash = file_hash(str(dest))
            conn.execute(
                "INSERT OR IGNORE INTO project_files (project_id, filename, filepath, file_hash, file_type) "
                "VALUES (?, ?, ?, ?, ?)",
                (pid, f.name, str(dest), fhash, "drawing"),
            )
            conn.commit()

            # Run extraction
            try:
                from ingestion.file_router import process_file
                result = process_file(str(dest))
                page_count = result.get("page_count", 0)
                method = result.get("method", "unknown")

                conn.execute(
                    "UPDATE project_files SET page_count = ?, status = 'processed' "
                    "WHERE project_id = ? AND filename = ?",
                    (page_count, pid, f.name),
                )
                conn.commit()
            except Exception as e:
                conn.execute(
                    "UPDATE project_files SET status = 'error' "
                    "WHERE project_id = ? AND filename = ?",
                    (pid, f.name),
                )
                conn.commit()
                st.error(f"Error processing {f.name}: {e}")
            finally:
                conn.close()

        progress.progress(1.0, text="Done!")
        st.success(f"Processed {total} file(s)")
        st.rerun()


def _status_section(pid: int):
    conn = get_conn()
    files = conn.execute(
        "SELECT filename, file_type, page_count, status, uploaded_at "
        "FROM project_files WHERE project_id = ? ORDER BY uploaded_at DESC",
        (pid,),
    ).fetchall()
    conn.close()

    if not files:
        st.info("No files uploaded yet.")
        return

    st.write(f"**{len(files)} file(s)**")

    for f in files:
        status = f["status"] or "pending"
        cols = st.columns([3, 1, 1, 1])
        cols[0].write(f["filename"])
        cols[1].write(f["file_type"] or "—")
        cols[2].write(f"{f['page_count'] or 0} pages")
        cols[3].markdown(status_badge(status))
