"""
Page 05 — RFI Log.

View, filter, and edit generated RFI entries.
Export to Excel.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from dashboard.components.widgets import severity_badge


def render(project: dict | None):
    st.header("RFI Log")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]
    rfi_key = f"rfi_log_{pid}"

    # Check for RFIs in session
    rfis = st.session_state.get(rfi_key, [])

    if not rfis:
        st.info("No RFIs generated yet. Run a Plan Review first, then generate RFIs.")

        if st.button("Generate RFIs from Review Results"):
            review_key = f"review_results_{pid}"
            results = st.session_state.get(review_key)
            if not results or not results.get("conflicts"):
                st.error("No review results with conflicts found. Run Plan Review first.")
                return

            with st.spinner("Generating RFI entries..."):
                try:
                    from analysis.rfi_generator import generate_rfis
                    conflicts = results["conflicts"]
                    rfi_log = generate_rfis(conflicts, project["name"])
                    st.session_state[rfi_key] = [
                        {
                            "number": r.number,
                            "subject": r.subject,
                            "question": r.question,
                            "severity": r.severity,
                            "priority": r.priority,
                            "discipline": r.discipline,
                            "sheets": r.sheets,
                            "status": "Open",
                        }
                        for r in rfi_log.entries
                    ]
                    st.success(f"Generated {len(rfi_log.entries)} RFIs")
                    st.rerun()
                except Exception as e:
                    st.error(f"RFI generation failed: {e}")
        return

    # Summary row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total RFIs", len(rfis))
    critical = sum(1 for r in rfis if r.get("severity") == "CRITICAL")
    major = sum(1 for r in rfis if r.get("severity") == "MAJOR")
    col2.metric("Critical", critical)
    col3.metric("Major", major)
    col4.metric("Open", sum(1 for r in rfis if r.get("status") == "Open"))

    # Filter
    sev_filter = st.multiselect(
        "Filter by Severity",
        ["CRITICAL", "MAJOR", "MINOR"],
        default=["CRITICAL", "MAJOR", "MINOR"],
    )
    filtered = [r for r in rfis if r.get("severity") in sev_filter]

    # RFI cards
    for rfi in filtered:
        sev = rfi.get("severity", "INFO")
        with st.expander(f"RFI-{rfi['number']:03d} | {severity_badge(sev)} | {rfi['subject']}"):
            st.write(f"**Question:** {rfi.get('question', 'N/A')}")
            st.write(f"**Priority:** {rfi.get('priority', 'N/A')}")
            st.write(f"**Discipline:** {rfi.get('discipline', 'N/A')}")
            st.write(f"**Sheets:** {rfi.get('sheets', 'N/A')}")

            new_status = st.selectbox(
                "Status",
                ["Open", "Submitted", "Answered", "Closed"],
                index=["Open", "Submitted", "Answered", "Closed"].index(rfi.get("status", "Open")),
                key=f"rfi_status_{rfi['number']}",
            )
            rfi["status"] = new_status

    # Export
    st.divider()
    if st.button("Export RFI Log to Excel"):
        with st.spinner("Building Excel..."):
            try:
                from output.rfi_excel import write_rfi_excel_from_dicts
                from config.settings import PROJECTS_DIR

                output_dir = Path(PROJECTS_DIR) / str(pid)
                output_dir.mkdir(parents=True, exist_ok=True)
                out_path = output_dir / "rfi_log.xlsx"

                write_rfi_excel_from_dicts(rfis, out_path, project["name"])

                with open(out_path, "rb") as fp:
                    st.download_button(
                        "Download RFI Excel",
                        fp.read(),
                        file_name="rfi_log.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            except Exception as e:
                st.error(f"Export failed: {e}")
