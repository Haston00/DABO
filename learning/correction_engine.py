"""
Correction engine — apply learned corrections to future reviews.

Uses feedback history to:
  - Suppress known false-positive rules for a project
  - Adjust severity levels based on user feedback patterns
  - Track accuracy improvement over time
"""
from __future__ import annotations

from analysis.conflict_detector import DetectionResult, Conflict
from learning.feedback_store import get_suppressed_rules, get_false_positives, get_feedback
from utils.logger import get_logger

log = get_logger(__name__)


def apply_corrections(
    result: DetectionResult,
    project_id: int,
) -> DetectionResult:
    """
    Apply learned corrections to a detection result.

    - Marks conflicts as suppressed if the rule was suppressed by feedback
    - Adjusts severity based on historical patterns
    """
    # Get suppressed rules
    suppressed = get_suppressed_rules(project_id)

    # Get specific false positive conflict IDs
    false_pos = get_false_positives(project_id)

    # Get feedback history for severity patterns
    feedback = get_feedback(project_id)
    severity_overrides = _build_severity_map(feedback)

    corrections_applied = 0

    for conflict in result.conflicts:
        # Suppress by rule
        if conflict.rule_id in suppressed:
            conflict.suppressed = True
            corrections_applied += 1
            continue

        # Suppress by specific conflict
        if conflict.conflict_id in false_pos:
            conflict.suppressed = True
            corrections_applied += 1
            continue

        # Adjust severity
        if conflict.rule_id in severity_overrides:
            old = conflict.severity
            conflict.severity = severity_overrides[conflict.rule_id]
            if old != conflict.severity:
                corrections_applied += 1

    if corrections_applied:
        log.info("Applied %d corrections from feedback history", corrections_applied)

    return result


def _build_severity_map(feedback: list[dict]) -> dict[str, str]:
    """
    Build a severity override map from feedback history.

    If a user has consistently changed the severity of a rule,
    apply that override automatically.
    """
    # Count severity changes per rule
    changes: dict[str, dict[str, int]] = {}
    for fb in feedback:
        if fb["action"] == "severity_change" and fb.get("adjusted_severity"):
            rule_key = fb.get("conflict_id", "").split("-")[0] if fb.get("conflict_id") else ""
            if rule_key:
                changes.setdefault(rule_key, {})
                adj = fb["adjusted_severity"]
                changes[rule_key][adj] = changes[rule_key].get(adj, 0) + 1

    # Only override if user has made 3+ consistent changes
    overrides = {}
    for rule_id, sev_counts in changes.items():
        if sev_counts:
            top_sev = max(sev_counts, key=sev_counts.get)
            if sev_counts[top_sev] >= 3:
                overrides[rule_id] = top_sev

    return overrides
