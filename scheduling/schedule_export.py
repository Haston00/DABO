"""
Schedule export coordinator — ties together activity builder, CPM engine,
and Excel writer to produce a complete P6-compatible schedule.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scheduling.activity_builder import build_activities
from scheduling.cpm_engine import compute_cpm, activities_to_export, get_critical_path
from scheduling.predecessor_logic import validate_predecessors, detect_cycles
from scheduling.wbs_builder import build_wbs, wbs_to_text
from output.schedule_excel import write_schedule_excel
from utils.logger import get_logger

log = get_logger(__name__)


def generate_schedule(
    project_name: str = "Commercial Project",
    building_type: str = "office",
    square_feet: int = 50000,
    stories: int = 2,
    start_date: datetime | None = None,
    output_dir: Path | str = ".",
    scope: str = "new_construction",
) -> dict:
    """
    Generate a complete CPM schedule and export to Excel.

    Returns a summary dict with schedule stats and file path.
    """
    start_date = start_date or datetime.now()
    output_dir = Path(output_dir)

    # 1. Build activities
    activities = build_activities(building_type, square_feet, stories, scope=scope)

    # 2. Validate
    errors = validate_predecessors(activities)
    if errors:
        for e in errors:
            log.error("Predecessor error: %s", e)
        return {"error": "Predecessor validation failed", "errors": errors}

    has_cycle = detect_cycles(activities)
    if has_cycle:
        log.error("Circular dependency detected in schedule")
        return {"error": "Circular dependency detected"}

    # 3. Run CPM
    activities = compute_cpm(activities)

    # 4. Get critical path
    critical = get_critical_path(activities)
    project_duration = max(a.early_finish for a in activities) if activities else 0

    # 5. Build WBS
    wbs = build_wbs(activities, project_name)

    # 6. Export to Excel
    export_data = activities_to_export(activities, start_date)
    excel_path = output_dir / f"{project_name.replace(' ', '_')}_Schedule.xlsx"
    write_schedule_excel(export_data, project_name, excel_path)

    milestones = [a for a in activities if a.is_milestone]

    summary = {
        "project_name": project_name,
        "building_type": building_type,
        "square_feet": square_feet,
        "stories": stories,
        "total_activities": len(activities),
        "critical_activities": len(critical),
        "milestones": len(milestones),
        "project_duration_days": project_duration,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "excel_path": str(excel_path),
        "wbs_text": wbs_to_text(wbs),
        "activities_data": activities,
        "critical_path": [
            {"id": a.activity_id, "name": a.activity_name, "duration": a.duration}
            for a in critical
        ],
    }

    log.info(
        "Schedule generated: %d activities, %d days, %d critical path activities",
        len(activities), project_duration, len(critical),
    )

    return summary
