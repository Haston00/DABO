"""
Page 07 — Export / Download Center.

Consolidated download point for all project outputs:
RFI logs, schedules, reports, raw data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from config.settings import PROJECTS_DIR


def render(project: dict | None):
    st.header("Export Center")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]
    proj_dir = Path(PROJECTS_DIR) / str(pid)

    if not proj_dir.exists():
        st.info("No outputs generated yet for this project.")
        return

    st.write(f"**Project:** {project['name']}")
    st.divider()

    # Find all exportable files
    exports = {
        "RFI Log (Excel)": list(proj_dir.glob("rfi_log*.xlsx")),
        "Schedule (Excel)": list(proj_dir.glob("*schedule*.xlsx")),
        "Summary Report": list(proj_dir.glob("*report*.txt")) + list(proj_dir.glob("*report*.pdf")),
        "Raw Extraction Data": list(proj_dir.glob("*.json")),
    }

    has_any = False
    for category, files in exports.items():
        if files:
            has_any = True
            st.subheader(category)
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
                size_kb = f.stat().st_size / 1024
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{f.name}** ({size_kb:.1f} KB)")
                with open(f, "rb") as fp:
                    col2.download_button(
                        "Download",
                        fp.read(),
                        file_name=f.name,
                        key=f"dl_{f.name}",
                    )

    if not has_any:
        st.info(
            "No export files found. Generate outputs first:\n\n"
            "- **RFI Log:** Run Plan Review then generate RFIs\n"
            "- **Schedule:** Generate a CPM schedule\n"
        )

    # Generate summary report
    st.divider()
    if st.button("Generate Summary Report"):
        with st.spinner("Building report..."):
            try:
                from datetime import datetime

                # Build a simple text report without requiring full objects
                lines = [
                    "=" * 70,
                    "  DABO Plan Review Report",
                    f"  Project: {project['name']}",
                    f"  Type: {project['building_type']} | SF: {project['square_feet']:,}",
                    f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "=" * 70,
                    "",
                    "Export generated from dashboard. Run full Plan Review",
                    "and Schedule for detailed results.",
                    "",
                    "=" * 70,
                    "  End of Report",
                    "=" * 70,
                ]
                report_text = "\n".join(lines)

                out_path = proj_dir / "summary_report.txt"
                out_path.write_text(report_text, encoding="utf-8")
                st.success("Report generated!")
                st.rerun()

            except Exception as e:
                st.error(f"Report generation failed: {e}")
