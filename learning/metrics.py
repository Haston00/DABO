"""
Accuracy metrics tracking for DABO's detection performance.

Tracks:
  - True positive rate (accepted conflicts / total conflicts)
  - False positive rate (rejected / total)
  - Severity accuracy (how often severity matched user expectation)
  - Improvement over time
"""
from __future__ import annotations

from dataclasses import dataclass

from learning.feedback_store import get_feedback
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AccuracyMetrics:
    total_conflicts: int = 0
    accepted: int = 0
    false_positives: int = 0
    severity_changes: int = 0
    notes: int = 0
    true_positive_rate: float = 0.0
    false_positive_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_conflicts": self.total_conflicts,
            "accepted": self.accepted,
            "false_positives": self.false_positives,
            "severity_changes": self.severity_changes,
            "notes": self.notes,
            "true_positive_rate": round(self.true_positive_rate, 3),
            "false_positive_rate": round(self.false_positive_rate, 3),
        }


def calculate_metrics(project_id: int) -> AccuracyMetrics:
    """Calculate accuracy metrics from feedback for a project."""
    feedback = get_feedback(project_id)
    metrics = AccuracyMetrics()

    for fb in feedback:
        metrics.total_conflicts += 1
        action = fb.get("action", "")
        if action == "accepted":
            metrics.accepted += 1
        elif action == "false_positive":
            metrics.false_positives += 1
        elif action == "severity_change":
            metrics.severity_changes += 1
        elif action == "note":
            metrics.notes += 1

    if metrics.total_conflicts > 0:
        metrics.true_positive_rate = metrics.accepted / metrics.total_conflicts
        metrics.false_positive_rate = metrics.false_positives / metrics.total_conflicts

    return metrics
