"""
Page 08 — Feedback / Corrections.

Interface for marking false positives, adjusting severities,
suppressing rules, and viewing accuracy metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from dashboard.components.widgets import severity_badge
from dashboard.components.charts import accuracy_trend


def render(project: dict | None):
    st.header("Feedback & Corrections")

    if not project:
        st.warning("Select a project in the sidebar first.")
        return

    pid = project["id"]

    tab_feedback, tab_rules, tab_metrics = st.tabs(["Conflict Feedback", "Rule Management", "Accuracy Metrics"])

    with tab_feedback:
        _conflict_feedback(pid)

    with tab_rules:
        _rule_management(pid)

    with tab_metrics:
        _accuracy_metrics(pid)


def _conflict_feedback(pid: int):
    st.write("Review detected conflicts and provide feedback to improve future accuracy.")

    # Load review results from session
    results_key = f"review_results_{pid}"
    results = st.session_state.get(results_key)

    if not results or not results.get("conflicts"):
        st.info("No review results available. Run a Plan Review first.")
        return

    conflicts = results["conflicts"]

    for i, c in enumerate(conflicts):
        sev = c.get("severity", "INFO")
        with st.expander(f"{severity_badge(sev)} {c.get('rule_id', '')} — {c.get('description', '')}"):
            st.write(f"**Sheets:** {', '.join(c.get('sheets', []))}")

            action = st.radio(
                "Your assessment:",
                ["Accept (correct finding)", "False Positive", "Change Severity", "Add Note"],
                key=f"fb_action_{i}",
                horizontal=True,
            )

            new_sev = None
            note = ""

            if action == "Change Severity":
                new_sev = st.selectbox(
                    "Correct severity:",
                    ["CRITICAL", "MAJOR", "MINOR"],
                    key=f"fb_sev_{i}",
                )

            if action == "Add Note":
                note = st.text_area("Note:", key=f"fb_note_{i}")

            if st.button("Submit Feedback", key=f"fb_submit_{i}"):
                try:
                    from learning.feedback_store import record_feedback

                    action_map = {
                        "Accept (correct finding)": "accepted",
                        "False Positive": "false_positive",
                        "Change Severity": "severity_change",
                        "Add Note": "note",
                    }

                    record_feedback(
                        project_id=pid,
                        conflict_id=c.get("conflict_id", f"C-{i}"),
                        action=action_map[action],
                        original_severity=sev,
                        adjusted_severity=new_sev or "",
                        user_note=note,
                    )
                    st.success("Feedback recorded!")
                except Exception as e:
                    st.error(f"Failed to record feedback: {e}")


def _rule_management(pid: int):
    st.write("Manage rule suppressions and overrides for this project.")

    from learning.feedback_store import get_suppressed_rules

    suppressed = get_suppressed_rules(pid)

    if suppressed:
        st.write(f"**{len(suppressed)} suppressed rule(s):**")
        for rule_id in sorted(suppressed):
            col1, col2 = st.columns([3, 1])
            col1.code(rule_id)
            if col2.button("Restore", key=f"restore_{rule_id}"):
                st.info(f"Rule {rule_id} restored (remove from rule_adjustments table)")
    else:
        st.info("No rules currently suppressed.")

    st.divider()
    st.subheader("Suppress a Rule")

    from config.conflict_rules import CONFLICT_RULES
    rule_options = {f"{r.rule_id} — {r.name}": r.rule_id for r in CONFLICT_RULES}

    selected = st.selectbox("Select rule to suppress:", list(rule_options.keys()))
    scope = st.radio("Scope:", ["This project only", "Global (all projects)"], horizontal=True)

    if st.button("Suppress Rule"):
        from learning.feedback_store import record_rule_adjustment
        proj_id = pid if scope == "This project only" else None
        record_rule_adjustment(
            rule_id=rule_options[selected],
            adjustment_type="suppress",
            project_id=proj_id,
        )
        st.success(f"Rule {rule_options[selected]} suppressed ({scope.lower()})")
        st.rerun()


def _accuracy_metrics(pid: int):
    st.write("Accuracy metrics based on your feedback history.")

    from learning.metrics import calculate_metrics

    metrics = calculate_metrics(pid)
    md = metrics.to_dict()

    if md["total_conflicts"] == 0:
        st.info("No feedback recorded yet. Submit feedback on conflicts to build accuracy data.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reviewed", md["total_conflicts"])
    col2.metric("True Positive Rate", f"{md['true_positive_rate']:.1%}")
    col3.metric("False Positive Rate", f"{md['false_positive_rate']:.1%}")
    col4.metric("Severity Changes", md["severity_changes"])

    st.divider()
    st.write(f"**Accepted:** {md['accepted']}")
    st.write(f"**False Positives:** {md['false_positives']}")
    st.write(f"**Notes:** {md['notes']}")
