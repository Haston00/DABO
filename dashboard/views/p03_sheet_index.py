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


# McCrory discipline color mapping
_DISC_COLORS = {
    "GEN": "#666666", "CIV": "#8B4513", "ARCH": "#1976D2",
    "STR": "#D32F2F", "MECH": "#388E3C", "PLMB": "#0097A7",
    "ELEC": "#F9A825", "FP": "#E53935", "FA": "#C62828",
    "TECH": "#7B1FA2", "FS": "#FF6F00", "CONV": "#455A64",
}


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
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #999;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">&#128196;</div>
            <div style="font-size: 1.1rem; font-weight: 500; color: #666;">No sheets classified yet</div>
            <div style="font-size: 0.9rem;">Upload and process files in the Ingestion tab.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    sheet_dicts = [dict(s) for s in sheets]

    # Summary metrics
    disciplines = sorted(set(s["discipline"] for s in sheet_dicts if s["discipline"]))
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sheets", len(sheet_dicts))
    col2.metric("Disciplines", len(disciplines))
    avg_conf = sum(s.get("confidence", 0) or 0 for s in sheet_dicts) / max(len(sheet_dicts), 1)
    col3.metric("Avg Confidence", f"{avg_conf:.0%}")

    # Discipline summary cards
    st.markdown("### Discipline Breakdown")
    disc_counts = {}
    for s in sheet_dicts:
        d = s.get("discipline", "?")
        disc_counts[d] = disc_counts.get(d, 0) + 1

    # Render as colored badges
    badge_html = ""
    for disc in sorted(disc_counts.keys()):
        color = _DISC_COLORS.get(disc, "#888")
        count = disc_counts[disc]
        badge_html += (
            f'<span style="display:inline-block; background:{color}; color:white; '
            f'padding:0.35rem 0.75rem; border-radius:4px; margin:0.25rem; '
            f'font-weight:600; font-size:0.85rem;">'
            f'{disc} &middot; {count}</span>'
        )
    st.markdown(badge_html, unsafe_allow_html=True)

    st.markdown("")

    # Chart
    chart = discipline_bar(sheet_dicts)
    if chart:
        chart.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(color="#00263A"),
        )
        chart.update_traces(marker_color="#FF5A19")
        st.plotly_chart(chart, use_container_width=True)

    # Filter
    disc_filter = st.multiselect(
        "Filter by Discipline",
        disciplines,
        default=disciplines,
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
                "confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0, max_value=1, format="%.0%%",
                ),
            },
            use_container_width=True,
            hide_index=True,
            height=min(600, len(filtered) * 38 + 50),
        )
    else:
        st.info("No sheets match the selected filters.")
