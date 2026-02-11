"""
Phase 1 tests — PDF ingestion engine.

Run: python -m pytest tests/test_pdf_engine.py -v
Or:  python tests/test_pdf_engine.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import BASE_DIR, DB_PATH
from config.csi_divisions import CSI_DIVISIONS, get_section_name, find_division_for_section
from config.sheet_patterns import SHEET_PREFIX_PATTERNS, TITLE_BLOCK_KEYWORDS
from utils.helpers import normalize_sheet_id, extract_page_number, sanitize_filename, human_size
from utils.db import get_conn


def test_config_loads():
    """Settings module loads without error."""
    assert BASE_DIR.exists(), f"BASE_DIR does not exist: {BASE_DIR}"
    print(f"  BASE_DIR: {BASE_DIR}")
    print(f"  DB_PATH:  {DB_PATH}")


def test_csi_divisions():
    """All 16 CSI divisions present with sections."""
    assert len(CSI_DIVISIONS) == 16, f"Expected 16 divisions, got {len(CSI_DIVISIONS)}"
    for code, div in CSI_DIVISIONS.items():
        assert "name" in div, f"Division {code} missing name"
        assert "sections" in div, f"Division {code} missing sections"
        assert len(div["sections"]) > 0, f"Division {code} has no sections"
    print(f"  16 divisions, {sum(len(d['sections']) for d in CSI_DIVISIONS.values())} total sections")


def test_csi_lookup():
    """Section lookup functions work."""
    name = get_section_name("03 30 00")
    assert name == "Cast-in-Place Concrete", f"Got: {name}"

    div = find_division_for_section("26 24 16")
    assert div == "16", f"Got: {div}"
    print(f"  03 30 00 -> {name}")
    print(f"  26 24 16 -> Division {div}")


def test_sheet_patterns():
    """Sheet prefix patterns are well-formed."""
    assert len(SHEET_PREFIX_PATTERNS) > 20
    assert len(TITLE_BLOCK_KEYWORDS) > 15
    print(f"  {len(SHEET_PREFIX_PATTERNS)} prefix patterns")
    print(f"  {len(TITLE_BLOCK_KEYWORDS)} title block keywords")


def test_normalize_sheet_id():
    """Sheet ID normalization handles common formats."""
    cases = [
        ("A-101", "A-101"),
        ("a-101", "A-101"),
        ("A 101", "A-101"),
        ("A101", "A-101"),
        ("S - 201", "S-201"),
        ("M001", "M-001"),
        ("E-101", "E-101"),
    ]
    for raw, expected in cases:
        result = normalize_sheet_id(raw)
        assert result == expected, f"normalize_sheet_id({raw!r}) = {result!r}, expected {expected!r}"
    print(f"  {len(cases)} normalization cases passed")


def test_extract_page_number():
    """Page number extraction from text headers."""
    text = "BAKER CONSTRUCTION\nSheet: A-101\nFLOOR PLAN - LEVEL 1"
    result = extract_page_number(text)
    assert result == "A-101", f"Got: {result}"
    print(f"  Extracted: {result}")


def test_helpers():
    """Miscellaneous helper functions."""
    assert sanitize_filename('test<>:file') == "test___file"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1048576) == "1.0 MB"
    print("  sanitize_filename, human_size OK")


def test_database():
    """Database creates and has expected tables."""
    conn = get_conn()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = sorted(t["name"] for t in tables)
    conn.close()

    expected = ["feedback", "processing_runs", "project_files", "projects", "rule_adjustments", "sheets"]
    for t in expected:
        assert t in table_names, f"Missing table: {t}"
    print(f"  Tables: {table_names}")


def test_pdf_engine_import():
    """PDF engine imports and functions are callable."""
    from ingestion.pdf_engine import extract_pdf, extract_tables, get_page_count
    assert callable(extract_pdf)
    assert callable(extract_tables)
    assert callable(get_page_count)
    print("  pdf_engine functions imported")


def test_file_router_import():
    """File router imports and functions are callable."""
    from ingestion.file_router import route_file, route_files
    assert callable(route_file)
    assert callable(route_files)
    print("  file_router functions imported")


def test_bluebeam_import():
    """Bluebeam module imports."""
    from ingestion.bluebeam import extract_bluebeam_markups, get_markup_summary
    assert callable(extract_bluebeam_markups)
    print("  bluebeam functions imported")


def test_spec_reader_import():
    """Spec reader module imports."""
    from ingestion.spec_reader import read_spec
    assert callable(read_spec)
    print("  spec_reader functions imported")


def test_ocr_import():
    """OCR module imports (Tesseract may not be installed)."""
    from ingestion.image_ocr import ocr_page, is_available
    assert callable(ocr_page)
    available = is_available()
    print(f"  OCR available: {available}")


# ── Run all tests ──────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_config_loads,
        test_csi_divisions,
        test_csi_lookup,
        test_sheet_patterns,
        test_normalize_sheet_id,
        test_extract_page_number,
        test_helpers,
        test_database,
        test_pdf_engine_import,
        test_file_router_import,
        test_bluebeam_import,
        test_spec_reader_import,
        test_ocr_import,
    ]

    print(f"\n{'='*60}")
    print(f"  DABO Phase 1 Tests — {len(tests)} tests")
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
            failed += 1

    print(f"{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)
