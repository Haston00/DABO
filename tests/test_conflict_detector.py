"""
Phase 3 tests — Cross-Reference + Conflict Detection.

Uses synthetic commercial construction data.
Tests the full pipeline: entities -> xref map -> conflict rules -> RFI generation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.pdf_engine import PageResult
from classification.sheet_classifier import classify_sheets
from classification.entity_extractor import extract_all_entities
from analysis.cross_reference import (
    build_cross_reference_map, get_shared_equipment, get_discipline_interfaces,
)
from analysis.conflict_detector import detect_conflicts
from analysis.rfi_generator import generate_rfis
from analysis.ai_reviewer import is_available as ai_available
from config.conflict_rules import CONFLICT_RULES, get_rules_for_disciplines


# ── Reuse synthetic data from Phase 2 tests ───────────────
from tests.test_classification import (
    ARCH_FLOOR_PLAN_TEXT, STRUCTURAL_PLAN_TEXT, MECHANICAL_PLAN_TEXT,
    ELECTRICAL_PLAN_TEXT, PLUMBING_PLAN_TEXT, FIRE_PROTECTION_TEXT,
    _make_page,
)


def _build_test_set():
    """Build a complete test drawing set through the full pipeline."""
    pages = [
        _make_page(ARCH_FLOOR_PLAN_TEXT, 1),
        _make_page(STRUCTURAL_PLAN_TEXT, 2),
        _make_page(MECHANICAL_PLAN_TEXT, 3),
        _make_page(ELECTRICAL_PLAN_TEXT, 4),
        _make_page(PLUMBING_PLAN_TEXT, 5),
        _make_page(FIRE_PROTECTION_TEXT, 6),
    ]
    classifications = classify_sheets(pages)
    entities = extract_all_entities(pages, classifications)
    return entities


# ── Tests ─────────────────────────────────────────────────

def test_conflict_rules_loaded():
    """All 34 conflict rules loaded."""
    assert len(CONFLICT_RULES) == 34, f"Expected 34 rules, got {len(CONFLICT_RULES)}"
    for rule_id, rule in CONFLICT_RULES.items():
        assert rule.rule_id == rule_id
        assert rule.severity in ("CRITICAL", "MAJOR", "MINOR", "INFO")
        assert len(rule.disciplines) > 0
    print(f"  {len(CONFLICT_RULES)} conflict rules loaded")
    sev_counts = {}
    for r in CONFLICT_RULES.values():
        sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
    print(f"  By severity: {sev_counts}")


def test_rules_for_disciplines():
    """Rule filtering by discipline works."""
    # Full commercial set — should get most rules
    all_discs = {"ARCH", "STR", "MECH", "ELEC", "PLMB", "FP", "FA", "CIV", "TECH"}
    rules = get_rules_for_disciplines(all_discs)
    assert len(rules) >= 25, f"Expected 25+ applicable rules, got {len(rules)}"
    print(f"  Full set ({len(all_discs)} disciplines): {len(rules)} rules applicable")

    # Small set — fewer rules
    small = {"ARCH", "STR"}
    rules_small = get_rules_for_disciplines(small)
    print(f"  ARCH+STR only: {len(rules_small)} rules applicable")
    assert len(rules_small) < len(rules)


def test_cross_reference_map():
    """Cross-reference map builds correctly."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)

    assert len(xref.all_sheet_ids) == 6
    assert len(xref.drawing_refs) > 0, "No drawing refs found"
    assert len(xref.spec_refs) > 0, "No spec refs found"
    assert len(xref.all_equipment) > 0, "No equipment found"
    print(f"  Sheets: {len(xref.all_sheet_ids)}")
    print(f"  Drawing refs: {len(xref.drawing_refs)} unique targets")
    print(f"  Spec refs: {len(xref.all_spec_refs)} unique sections")
    print(f"  Equipment: {len(xref.all_equipment)} unique tags")
    print(f"  Broken refs: {len(xref.broken_refs)}")


def test_broken_references():
    """Broken references detected correctly."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)

    # Several refs should be broken since we only have 6 sheets
    # but they reference sheets like A-501, S-501, M-501, etc.
    assert len(xref.broken_refs) > 0, "Expected broken refs (target sheets not in set)"
    print(f"  Found {len(xref.broken_refs)} broken references:")
    for br in xref.broken_refs[:5]:
        print(f"    {br.source_sheet} -> {br.target} ({br.ref_type})")


def test_shared_equipment():
    """Equipment shared across disciplines is identified."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)
    shared = get_shared_equipment(xref)
    print(f"  Shared equipment: {len(shared)} tags")
    for tag, sheets in shared.items():
        print(f"    {tag}: {sheets}")


def test_discipline_interfaces():
    """Discipline interface mapping works."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)
    interfaces = get_discipline_interfaces(xref)
    assert len(interfaces) > 0, "No discipline interfaces found"
    print(f"  Discipline interfaces:")
    for a, b, count in interfaces:
        print(f"    {a} <-> {b}: {count} references")


def test_conflict_detection():
    """Full conflict detection runs and finds issues."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)
    result = detect_conflicts(entities, xref)

    assert result.rules_checked > 0, "No rules were checked"
    assert len(result.conflicts) > 0, "No conflicts detected"
    print(f"  Rules checked: {result.rules_checked}")
    print(f"  Rules triggered: {result.rules_triggered}")
    print(f"  Total conflicts: {len(result.conflicts)}")
    print(f"  CRITICAL: {result.critical_count}")
    print(f"  MAJOR: {result.major_count}")
    print(f"  MINOR: {result.minor_count}")

    # Show first few conflicts
    for c in result.conflicts[:5]:
        print(f"    [{c.severity}] {c.rule_id}: {c.rule_name} -> {c.sheets_involved}")


def test_conflict_suppression():
    """Suppressed rules are skipped."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)

    # Run without suppression
    result1 = detect_conflicts(entities, xref)
    # Run with all rules suppressed
    all_ids = set(CONFLICT_RULES.keys())
    result2 = detect_conflicts(entities, xref, suppressed_rules=all_ids)

    # Suppressed should have fewer conflicts (still has broken refs + division checks)
    assert len(result2.conflicts) <= len(result1.conflicts)
    print(f"  Without suppression: {len(result1.conflicts)} conflicts")
    print(f"  With all rules suppressed: {len(result2.conflicts)} conflicts")


def test_rfi_generation():
    """RFI log generates from conflicts."""
    entities = _build_test_set()
    xref = build_cross_reference_map(entities)
    result = detect_conflicts(entities, xref)

    rfi_log = generate_rfis(result, project_name="Test Commercial Project", use_ai=False)

    assert rfi_log.total > 0, "No RFIs generated"
    assert rfi_log.project_name == "Test Commercial Project"
    print(f"  Generated {rfi_log.total} RFIs")
    print(f"  CRITICAL: {rfi_log.critical_count}")
    print(f"  MAJOR: {rfi_log.major_count}")

    # Check RFI structure
    for rfi in rfi_log.rfis[:3]:
        assert rfi.rfi_number > 0
        assert rfi.subject
        assert rfi.question
        assert rfi.severity
        print(f"    RFI-{rfi.rfi_number:03d} [{rfi.priority}]: {rfi.subject[:60]}")


def test_ai_reviewer_status():
    """AI reviewer reports availability correctly."""
    available = ai_available()
    print(f"  Claude AI available: {available}")
    # Not a failure either way — system works without it


# ── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_conflict_rules_loaded,
        test_rules_for_disciplines,
        test_cross_reference_map,
        test_broken_references,
        test_shared_equipment,
        test_discipline_interfaces,
        test_conflict_detection,
        test_conflict_suppression,
        test_rfi_generation,
        test_ai_reviewer_status,
    ]

    print(f"\n{'='*60}")
    print(f"  DABO Phase 3 Tests - {len(tests)} tests")
    print(f"  Cross-Reference + Conflict Detection")
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
