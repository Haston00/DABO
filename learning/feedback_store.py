"""
Feedback store — SQLite-backed storage for user corrections.

Tracks:
  - False positives (conflicts marked as incorrect)
  - Severity adjustments (user says MAJOR, system said CRITICAL)
  - User notes explaining why something was wrong
  - Rule adjustments (suppress a rule for a project or globally)
"""
from __future__ import annotations

from datetime import datetime

from utils.db import get_conn
from utils.logger import get_logger

log = get_logger(__name__)


def record_feedback(
    project_id: int,
    conflict_id: str,
    action: str,           # "false_positive", "severity_change", "accepted", "note"
    original_severity: str = "",
    adjusted_severity: str = "",
    user_note: str = "",
) -> int:
    """Record user feedback on a conflict. Returns feedback row ID."""
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO feedback
           (project_id, conflict_id, action, original_severity, adjusted_severity, user_note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (project_id, conflict_id, action, original_severity, adjusted_severity, user_note),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    log.info("Feedback recorded: %s on %s (ID=%d)", action, conflict_id, row_id)
    return row_id


def get_feedback(project_id: int) -> list[dict]:
    """Get all feedback for a project."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM feedback WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_false_positives(project_id: int) -> set[str]:
    """Get conflict IDs marked as false positives."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT conflict_id FROM feedback WHERE project_id = ? AND action = 'false_positive'",
        (project_id,),
    ).fetchall()
    conn.close()
    return {r["conflict_id"] for r in rows}


def record_rule_adjustment(
    rule_id: str,
    adjustment_type: str,  # "suppress", "severity_override", "custom_threshold"
    value: str = "",
    project_id: int | None = None,
) -> int:
    """Record a rule adjustment. project_id=None means global."""
    conn = get_conn()
    cursor = conn.execute(
        """INSERT INTO rule_adjustments (project_id, rule_id, adjustment_type, value)
           VALUES (?, ?, ?, ?)""",
        (project_id, rule_id, adjustment_type, value),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    scope = f"project {project_id}" if project_id else "global"
    log.info("Rule adjustment: %s %s (%s, ID=%d)", adjustment_type, rule_id, scope, row_id)
    return row_id


def get_suppressed_rules(project_id: int | None = None) -> set[str]:
    """Get rule IDs that are suppressed (project-specific + global)."""
    conn = get_conn()
    # Global suppressions
    rows = conn.execute(
        "SELECT rule_id FROM rule_adjustments WHERE adjustment_type = 'suppress' AND project_id IS NULL",
    ).fetchall()
    suppressed = {r["rule_id"] for r in rows}

    # Project-specific suppressions
    if project_id:
        rows = conn.execute(
            "SELECT rule_id FROM rule_adjustments WHERE adjustment_type = 'suppress' AND project_id = ?",
            (project_id,),
        ).fetchall()
        suppressed.update(r["rule_id"] for r in rows)

    conn.close()
    return suppressed
