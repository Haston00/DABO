"""
Phase 5 tests — CPM Scheduling Engine.

Tests activity generation, CPM forward/backward pass, critical path,
and Excel export for a synthetic commercial project.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from scheduling.activity_builder import build_activities
from scheduling.cpm_engine import compute_cpm, get_critical_path, activities_to_export
from scheduling.predecessor_logic import validate_predecessors, detect_cycles
from scheduling.wbs_builder import build_wbs, wbs_to_text
from scheduling.schedule_export import generate_schedule
from config.production_rates import get_duration, PRODUCTION_RATES, FIXED_DURATIONS


def test_production_rates():
    """Production rates load for all building types."""
    assert len(PRODUCTION_RATES) > 20
    assert len(FIXED_DURATIONS) > 5

    # Test specific lookups
    dur = get_duration("STRUCTURAL_STEEL", "office", 50000)
    assert dur > 0, f"Expected positive duration, got {dur}"
    print(f"  Structural steel, 50K SF office: {dur} days")

    dur2 = get_duration("STRUCTURAL_STEEL", "warehouse", 100000)
    print(f"  Structural steel, 100K SF warehouse: {dur2} days")

    dur_fixed = get_duration("PERMIT", "office", 50000)
    assert dur_fixed == 30
    print(f"  Permit (fixed): {dur_fixed} days")


def test_activity_builder():
    """Activity builder generates complete list."""
    activities = build_activities("office", 50000, 2)
    assert len(activities) > 30, f"Expected 30+ activities, got {len(activities)}"

    # Check all have IDs and names
    for act in activities:
        assert act.activity_id, f"Activity missing ID"
        assert act.activity_name, f"Activity {act.activity_id} missing name"

    print(f"  Generated {len(activities)} activities")
    milestones = [a for a in activities if a.is_milestone]
    print(f"  Milestones: {len(milestones)}")

    # Check different building types produce different durations
    office = build_activities("office", 50000, 2)
    warehouse = build_activities("warehouse", 100000, 1)
    print(f"  Office 50K/2-story: {len(office)} activities")
    print(f"  Warehouse 100K/1-story: {len(warehouse)} activities")


def test_predecessor_validation():
    """Predecessor validation catches errors."""
    activities = build_activities("office", 50000, 2)
    errors = validate_predecessors(activities)
    assert len(errors) == 0, f"Unexpected errors: {errors}"
    print(f"  Validation passed: 0 errors")

    # Check no cycles
    has_cycle = detect_cycles(activities)
    assert not has_cycle, "Unexpected cycle detected"
    print(f"  No circular dependencies")


def test_cpm_forward_backward():
    """CPM engine computes correct ES/EF/LS/LF and float."""
    activities = build_activities("office", 50000, 2)
    activities = compute_cpm(activities)

    # Project should have positive duration
    project_dur = max(a.early_finish for a in activities)
    assert project_dur > 100, f"Project duration too short: {project_dur} days"
    print(f"  Project duration: {project_dur} working days")

    # All activities should have ES <= EF
    for act in activities:
        assert act.early_start <= act.early_finish, f"{act.activity_id}: ES > EF"
        assert act.late_start <= act.late_finish, f"{act.activity_id}: LS > LF"
        assert act.total_float >= 0, f"{act.activity_id}: negative float"

    # Float should be non-negative
    neg_float = [a for a in activities if a.total_float < 0]
    assert len(neg_float) == 0, f"{len(neg_float)} activities have negative float"
    print(f"  All float values non-negative")


def test_critical_path():
    """Critical path identified correctly."""
    activities = build_activities("office", 50000, 2)
    activities = compute_cpm(activities)
    critical = get_critical_path(activities)

    assert len(critical) > 5, f"Expected 5+ critical activities, got {len(critical)}"
    print(f"  Critical path: {len(critical)} activities")
    for act in critical:
        assert act.total_float == 0, f"Critical activity {act.activity_id} has non-zero float"
        print(f"    {act.activity_id}: {act.activity_name} ({act.duration}d)")


def test_wbs_structure():
    """WBS tree builds correctly."""
    activities = build_activities("office", 50000, 2)
    wbs = build_wbs(activities, "Test Office Building")

    assert wbs.activity_count == len(activities)
    assert len(wbs.children) > 0
    print(f"  WBS root: {wbs.activity_count} activities across {len(wbs.children)} divisions")

    text = wbs_to_text(wbs)
    assert len(text) > 100
    # Print first 500 chars
    print(f"  WBS Tree (truncated):")
    for line in text.split("\n")[:10]:
        print(f"    {line}")


def test_schedule_export():
    """Full schedule generation with Excel export."""
    output_dir = Path(__file__).resolve().parent / "sample_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    result = generate_schedule(
        project_name="Test Office Building",
        building_type="office",
        square_feet=50000,
        stories=2,
        start_date=datetime(2026, 3, 1),
        output_dir=output_dir,
    )

    assert "error" not in result, f"Schedule generation error: {result.get('error')}"
    assert result["total_activities"] > 30
    assert result["project_duration_days"] > 100
    assert result["critical_activities"] > 5

    excel_path = Path(result["excel_path"])
    assert excel_path.exists(), f"Excel file not created: {excel_path}"

    print(f"  Project: {result['project_name']}")
    print(f"  Activities: {result['total_activities']}")
    print(f"  Duration: {result['project_duration_days']} working days")
    print(f"  Critical: {result['critical_activities']} activities")
    print(f"  Excel: {excel_path.name} ({excel_path.stat().st_size / 1024:.1f} KB)")


def test_date_conversion():
    """Working day to calendar date conversion."""
    from scheduling.cpm_engine import day_to_date
    start = datetime(2026, 3, 2)  # Monday

    # Day 5 from Monday: Tue, Wed, Thu, Fri, Mon = Monday (5 working days)
    d5 = day_to_date(5, start)
    assert d5.weekday() == 0, f"Day 5 should be Monday, got {d5.strftime('%A')}"
    print(f"  Day 0: {start.strftime('%A %Y-%m-%d')}")
    print(f"  Day 5: {d5.strftime('%A %Y-%m-%d')}")

    # Day 10 should skip another weekend
    d10 = day_to_date(10, start)
    assert d10.weekday() < 5, f"Day 10 landed on weekend: {d10.strftime('%A')}"
    print(f"  Day 10: {d10.strftime('%A %Y-%m-%d')}")


# ── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_production_rates,
        test_activity_builder,
        test_predecessor_validation,
        test_cpm_forward_backward,
        test_critical_path,
        test_wbs_structure,
        test_schedule_export,
        test_date_conversion,
    ]

    print(f"\n{'='*60}")
    print(f"  DABO Phase 5 Tests - {len(tests)} tests")
    print(f"  CPM Scheduling Engine")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            print(f"[RUN]  {name}")
            test()
            print(f"[PASS] {name}\n")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)
