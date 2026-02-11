"""
Predecessor logic utilities — FS, SS, FF relationships with lags.

Helper functions for building and validating predecessor chains.
"""
from __future__ import annotations

from scheduling.cpm_engine import Activity


def add_predecessor(activity: Activity, pred_id: str, rel_type: str = "FS", lag: int = 0):
    """Add a predecessor relationship to an activity."""
    activity.predecessors.append({
        "activity_id": pred_id,
        "rel_type": rel_type,
        "lag": lag,
    })


def validate_predecessors(activities: list[Activity]) -> list[str]:
    """
    Validate predecessor references. Returns list of error messages.
    """
    errors = []
    act_ids = {a.activity_id for a in activities}

    for act in activities:
        for pred in act.predecessors:
            pid = pred["activity_id"]
            if pid not in act_ids:
                errors.append(f"Activity {act.activity_id} references nonexistent predecessor {pid}")
            if pid == act.activity_id:
                errors.append(f"Activity {act.activity_id} references itself as predecessor")
            if pred.get("rel_type", "FS") not in ("FS", "SS", "FF", "SF"):
                errors.append(f"Activity {act.activity_id}: invalid relationship type '{pred.get('rel_type')}'")

    return errors


def detect_cycles(activities: list[Activity]) -> bool:
    """Check for circular dependencies. Returns True if a cycle exists."""
    act_map = {a.activity_id: a for a in activities}
    visited = set()
    rec_stack = set()

    def dfs(act_id: str) -> bool:
        visited.add(act_id)
        rec_stack.add(act_id)

        act = act_map.get(act_id)
        if act:
            for pred in act.predecessors:
                pid = pred["activity_id"]
                if pid not in visited:
                    if dfs(pid):
                        return True
                elif pid in rec_stack:
                    return True

        rec_stack.discard(act_id)
        return False

    for act in activities:
        if act.activity_id not in visited:
            if dfs(act.activity_id):
                return True
    return False
