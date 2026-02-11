"""
Page 06 — Schedule.

CPM schedule generation, Gantt chart, critical path view,
and P6-compatible Excel export.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from dashboard.components.charts import build_gantt_data, gantt_chart


def render(project: dict | None):
    st.header("Schedule")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]
    sched_key = f"schedule_{pid}"

    tab_gen, tab_view = st.tabs(["Generate", "View Schedule"])

    with tab_gen:
        _generate_schedule(project, sched_key)

    with tab_view:
        _view_schedule(project, sched_key)


def _generate_schedule(project: dict, sched_key: str):
    st.write("Generate a CPM schedule based on project parameters.")

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Project Start Date", value=datetime(2026, 4, 1))
    col2.write(f"**Type:** {project['building_type']}")
    col2.write(f"**SF:** {project['square_feet']:,}")

    if st.button("Generate Schedule", type="primary"):
        with st.spinner("Building activities and computing CPM..."):
            try:
                from scheduling.schedule_export import generate_schedule
                from config.settings import PROJECTS_DIR

                output_dir = Path(PROJECTS_DIR) / str(project["id"])
                output_dir.mkdir(parents=True, exist_ok=True)

                result = generate_schedule(
                    project_name=project["name"],
                    building_type=project["building_type"],
                    square_feet=project["square_feet"],
                    stories=project.get("stories", 1),
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    output_dir=output_dir,
                )

                if "error" in result:
                    st.error(f"Schedule error: {result['error']}")
                    return

                st.session_state[sched_key] = result
                st.success(
                    f"Schedule generated: {result['total_activities']} activities, "
                    f"{result['project_duration_days']} working days, "
                    f"{result['critical_activities']} critical"
                )
                st.rerun()

            except Exception as e:
                st.error(f"Schedule generation failed: {e}")


def _view_schedule(project: dict, sched_key: str):
    result = st.session_state.get(sched_key)

    if not result:
        st.info("No schedule generated yet.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Activities", result["total_activities"])
    col2.metric("Duration (days)", result["project_duration_days"])
    col3.metric("Critical Path", result["critical_activities"])
    col4.metric("Milestones", result.get("milestones", 0))

    # Gantt chart
    st.subheader("Gantt Chart")
    activities = result.get("activities_data")
    if activities:
        start_date = result.get("start_date", datetime(2026, 4, 1))
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        gantt_data = build_gantt_data(activities, start_date)
        fig = gantt_chart(gantt_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Install plotly for Gantt chart: pip install plotly")
    else:
        st.info("Activity detail data not available for chart.")

    # Critical path table
    st.subheader("Critical Path")
    critical = result.get("critical_path", [])
    if critical:
        for act in critical:
            st.write(f"- **{act['id']}**: {act['name']} ({act['duration']}d)")

    # WBS
    wbs_text = result.get("wbs_text")
    if wbs_text:
        with st.expander("WBS Structure"):
            st.code(wbs_text, language=None)

    # Export
    st.divider()
    excel_path = result.get("excel_path")
    if excel_path and Path(excel_path).exists():
        with open(excel_path, "rb") as fp:
            st.download_button(
                "Download P6-Compatible Excel",
                fp.read(),
                file_name=f"{project['name']}_schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
