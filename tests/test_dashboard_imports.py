"""
Phase 7 test — verify all dashboard modules import correctly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_widgets():
    from dashboard.components.widgets import (
        sidebar_project_selector, severity_badge, status_badge, metric_row,
        file_upload_area, confirm_action, empty_state,
    )
    assert severity_badge("CRITICAL") == ":red[**CRITICAL**]"
    assert severity_badge("MAJOR") == ":orange[**MAJOR**]"
    assert status_badge("complete") == ":green[complete]"
    print("  widgets: 7 functions imported, badge tests pass")

def test_charts():
    from dashboard.components.charts import (
        build_gantt_data, gantt_chart, severity_pie, discipline_bar, accuracy_trend,
    )
    print("  charts: 5 functions imported")

def test_views():
    from dashboard.views.p01_project_setup import render as r1
    from dashboard.views.p02_ingestion import render as r2
    from dashboard.views.p03_sheet_index import render as r3
    from dashboard.views.p04_plan_review import render as r4
    from dashboard.views.p05_rfi_log import render as r5
    from dashboard.views.p06_schedule import render as r6
    from dashboard.views.p07_export import render as r7
    from dashboard.views.p08_feedback import render as r8
    print("  views: 8 pages imported (p01-p08)")

def test_rfi_excel_dict_mode():
    from output.rfi_excel import write_rfi_excel_from_dicts
    import tempfile
    out = Path(tempfile.mkdtemp()) / "test_rfi.xlsx"
    rfis = [
        {"number": 1, "priority": "URGENT", "severity": "CRITICAL",
         "subject": "Test", "question": "Test?", "sheets": "A-101",
         "discipline": "ARCH", "status": "Open"},
    ]
    result = write_rfi_excel_from_dicts(rfis, out, "Test Project")
    assert result.exists()
    print(f"  rfi_excel dict mode: {result.name} ({result.stat().st_size / 1024:.1f} KB)")

def test_file_count():
    """Verify total file count matches plan."""
    dabo_root = Path(__file__).resolve().parent.parent
    py_files = list(dabo_root.rglob("*.py"))
    # Exclude __pycache__
    py_files = [f for f in py_files if "__pycache__" not in str(f)]
    print(f"  Total Python files: {len(py_files)}")
    assert len(py_files) >= 50, f"Expected 50+ files, got {len(py_files)}"

    # Count by package
    packages = {}
    for f in py_files:
        rel = f.relative_to(dabo_root)
        pkg = rel.parts[0] if len(rel.parts) > 1 else "root"
        packages.setdefault(pkg, 0)
        packages[pkg] += 1

    for pkg in sorted(packages):
        print(f"    {pkg}: {packages[pkg]} files")


if __name__ == "__main__":
    tests = [
        test_widgets,
        test_charts,
        test_views,
        test_rfi_excel_dict_mode,
        test_file_count,
    ]

    print(f"\n{'='*60}")
    print(f"  DABO Phase 7 Tests - {len(tests)} tests")
    print(f"  Dashboard + Polish")
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
