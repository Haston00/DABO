"""
Page 03 — Sheet Index.

Shows classified sheets by discipline, extraction results,
and discipline coverage summary.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from utils.db import get_conn
from dashboard.components.charts import discipline_bar


def render(project: dict | None):
    st.header("Sheet Index")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]

    conn = get_conn()
    sheets = conn.execute(
        "SELECT sheet_id, sheet_name, discipline, page_number, confidence "
        "FROM sheets WHERE project_id = ? ORDER BY sheet_id",
        (pid,),
    ).fetchall()
    conn.close()

    if not sheets:
        st.info("No sheets classified yet. Upload and process files in the Ingestion tab.")
        return

    sheet_dicts = [dict(s) for s in sheets]

    # Summary metrics
    disciplines = set(s["discipline"] for s in sheet_dicts if s["discipline"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sheets", len(sheet_dicts))
    col2.metric("Disciplines", len(disciplines))
    avg_conf = sum(s.get("confidence", 0) or 0 for s in sheet_dicts) / max(len(sheet_dicts), 1)
    col3.metric("Avg Confidence", f"{avg_conf:.0%}")

    # Chart
    chart = discipline_bar(sheet_dicts)
    if chart:
        st.plotly_chart(chart, use_container_width=True)

    # Filter
    disc_filter = st.multiselect(
        "Filter by Discipline",
        sorted(disciplines),
        default=sorted(disciplines),
    )

    # Table
    filtered = [s for s in sheet_dicts if s.get("discipline") in disc_filter]
    if filtered:
        st.dataframe(
            filtered,
            column_config={
                "sheet_id": st.column_config.TextColumn("Sheet ID", width="small"),
                "sheet_name": st.column_config.TextColumn("Sheet Name", width="large"),
                "discipline": st.column_config.TextColumn("Discipline", width="small"),
                "page_number": st.column_config.NumberColumn("Page", width="small"),
                "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No sheets match the selected filters.")
