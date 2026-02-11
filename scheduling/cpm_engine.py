"""
CPM (Critical Path Method) forward/backward pass engine.

Takes a list of activities with durations and predecessors,
computes:
  - Early Start / Early Finish (forward pass)
  - Late Start / Late Finish (backward pass)
  - Total Float
  - Critical Path

Supports relationship types: FS, SS, FF with lags.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class Activity:
    activity_id: str
    activity_name: str
    wbs: str = ""
    duration: int = 0          # working days
    predecessors: list[dict] = field(default_factory=list)  # [{activity_id, rel_type, lag}]
    successors: list[str] = field(default_factory=list)
    early_start: int = 0       # day number
    early_finish: int = 0
    late_start: int = 0
    late_finish: int = 0
    total_float: int = 0
    is_critical: bool = False
    is_milestone: bool = False

    def to_dict(self) -> dict:
        return {
            "activity_id": self.activity_id,
            "activity_name": self.activity_name,
            "wbs": self.wbs,
            "duration": self.duration,
            "predecessors": self.predecessors,
            "early_start": self.early_start,
            "early_finish": self.early_finish,
            "late_start": self.late_start,
            "late_finish": self.late_finish,
            "total_float": self.total_float,
            "is_critical": self.is_critical,
            "is_milestone": self.is_milestone,
        }


def compute_cpm(activities: list[Activity]) -> list[Activity]:
    """
    Run CPM forward and backward pass on a list of activities.

    Activities must have activity_id, duration, and predecessors set.
    Modifies activities in place and returns them.
    """
    if not activities:
        return activities

    # Build lookup
    act_map = {a.activity_id: a for a in activities}

    # Build successor lists
    for act in activities:
        for pred in act.predecessors:
            pred_act = act_map.get(pred["activity_id"])
            if pred_act and act.activity_id not in pred_act.successors:
                pred_act.successors.append(act.activity_id)

    # ── Forward Pass ──────────────────────────────────────
    # Topological sort
    order = _topological_sort(activities, act_map)

    for act_id in order:
        act = act_map[act_id]

        if not act.predecessors:
            act.early_start = 0
        else:
            max_es = 0
            for pred in act.predecessors:
                pred_act = act_map.get(pred["activity_id"])
                if not pred_act:
                    continue
                rel = pred.get("rel_type", "FS")
                lag = pred.get("lag", 0)

                if rel == "FS":
                    es = pred_act.early_finish + lag
                elif rel == "SS":
                    es = pred_act.early_start + lag
                elif rel == "FF":
                    es = pred_act.early_finish + lag - act.duration
                else:
                    es = pred_act.early_finish + lag

                max_es = max(max_es, es)

            act.early_start = max_es

        act.early_finish = act.early_start + act.duration

    # ── Backward Pass ─────────────────────────────────────
    project_finish = max(a.early_finish for a in activities)

    for act_id in reversed(order):
        act = act_map[act_id]

        if not act.successors:
            act.late_finish = project_finish
        else:
            min_lf = project_finish
            for succ_id in act.successors:
                succ = act_map.get(succ_id)
                if not succ:
                    continue

                # Find the predecessor entry in successor that references this activity
                for pred in succ.predecessors:
                    if pred["activity_id"] == act.activity_id:
                        rel = pred.get("rel_type", "FS")
                        lag = pred.get("lag", 0)

                        if rel == "FS":
                            lf = succ.late_start - lag
                        elif rel == "SS":
                            lf = succ.late_start - lag + act.duration
                        elif rel == "FF":
                            lf = succ.late_finish - lag
                        else:
                            lf = succ.late_start - lag

                        min_lf = min(min_lf, lf)
                        break

            act.late_finish = min_lf

        act.late_start = act.late_finish - act.duration
        act.total_float = act.late_start - act.early_start
        act.is_critical = act.total_float == 0

    critical_count = sum(1 for a in activities if a.is_critical)
    log.info(
        "CPM complete: %d activities, project duration %d days, %d critical",
        len(activities), project_finish, critical_count,
    )

    return activities


def get_critical_path(activities: list[Activity]) -> list[Activity]:
    """Return activities on the critical path, in order."""
    return [a for a in activities if a.is_critical]


def day_to_date(day_number: int, start_date: datetime, skip_weekends: bool = True) -> datetime:
    """Convert a working-day number to a calendar date."""
    current = start_date
    days_added = 0
    while days_added < day_number:
        current += timedelta(days=1)
        if skip_weekends and current.weekday() >= 5:
            continue
        days_added += 1
    return current


def activities_to_export(
    activities: list[Activity],
    start_date: datetime | None = None,
) -> list[dict]:
    """Convert activities to export-ready dicts with calendar dates."""
    start_date = start_date or datetime.now()
    result = []
    for act in activities:
        d = act.to_dict()
        d["early_start"] = day_to_date(act.early_start, start_date).strftime("%Y-%m-%d")
        d["early_finish"] = day_to_date(act.early_finish, start_date).strftime("%Y-%m-%d")
        d["late_start"] = day_to_date(act.late_start, start_date).strftime("%Y-%m-%d")
        d["late_finish"] = day_to_date(act.late_finish, start_date).strftime("%Y-%m-%d")
        result.append(d)
    return result


def _topological_sort(activities: list[Activity], act_map: dict[str, Activity]) -> list[str]:
    """Topological sort of activities by predecessor dependencies."""
    in_degree = {a.activity_id: 0 for a in activities}
    for act in activities:
        for pred in act.predecessors:
            if pred["activity_id"] in act_map:
                in_degree[act.activity_id] = in_degree.get(act.activity_id, 0) + 1

    queue = [aid for aid, deg in in_degree.items() if deg == 0]
    order = []

    while queue:
        current = queue.pop(0)
        order.append(current)
        act = act_map[current]
        for succ_id in act.successors:
            in_degree[succ_id] -= 1
            if in_degree[succ_id] == 0:
                queue.append(succ_id)

    # Add any activities not reached (disconnected)
    for act in activities:
        if act.activity_id not in order:
            order.append(act.activity_id)

    return order
