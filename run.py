"""
DABO entry point.

Usage:
    python run.py              → Launch Streamlit dashboard
    python run.py --ingest FILE → Quick-ingest a PDF from command line
    python run.py --test        → Run a quick self-test
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser(description="DABO — AI Plan Review & Scheduling Agent")
    parser.add_argument("--ingest", type=str, help="Ingest a PDF file (quick CLI mode)")
    parser.add_argument("--test", action="store_true", help="Run a quick self-test")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard (legacy)")
    parser.add_argument("--web", action="store_true", help="Launch Flask web dashboard (default)")
    args = parser.parse_args()

    # Bootstrap database
    from utils.db import init_db
    init_db()

    if args.test:
        _run_self_test()
    elif args.ingest:
        _run_ingest(args.ingest)
    elif args.dashboard:
        _launch_streamlit()
    else:
        _launch_web()


def _run_self_test():
    """Quick smoke test of core modules."""
    from utils.logger import get_logger
    log = get_logger("selftest")

    log.info("=== DABO Self-Test ===")

    # Test 1: Config loads
    from config.settings import BASE_DIR, DB_PATH
    log.info("[PASS] Config loaded — BASE_DIR: %s", BASE_DIR)

    # Test 2: CSI divisions load
    from config.csi_divisions import CSI_DIVISIONS
    assert len(CSI_DIVISIONS) == 16, f"Expected 16 divisions, got {len(CSI_DIVISIONS)}"
    log.info("[PASS] CSI divisions: %d loaded", len(CSI_DIVISIONS))

    # Test 3: Sheet patterns load
    from config.sheet_patterns import SHEET_PREFIX_PATTERNS
    assert len(SHEET_PREFIX_PATTERNS) > 20, "Expected 20+ sheet patterns"
    log.info("[PASS] Sheet patterns: %d loaded", len(SHEET_PREFIX_PATTERNS))

    # Test 4: Database initializes
    from utils.db import get_conn
    with get_conn() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        log.info("[PASS] Database tables: %s", table_names)

    # Test 5: PDF engine imports
    from ingestion.pdf_engine import extract_pdf
    log.info("[PASS] PDF engine imported")

    # Test 6: File router imports
    from ingestion.file_router import route_file
    log.info("[PASS] File router imported")

    log.info("=== All self-tests passed ===")


def _run_ingest(file_path: str):
    """Quick CLI ingestion of a single file."""
    from utils.logger import get_logger
    from ingestion.file_router import route_file

    log = get_logger("cli")
    path = Path(file_path)

    if not path.exists():
        log.error("File not found: %s", path)
        sys.exit(1)

    log.info("Ingesting: %s", path.name)
    result = route_file(path)

    print(f"\n{'='*60}")
    print(f"File:     {result.filename}")
    print(f"Type:     {result.file_type}")
    print(f"Size:     {result.file_size_mb} MB")
    print(f"Pages:    {result.page_count}")
    print(f"Extracted: {len(result.pages)} pages")
    print(f"Markups:  {len(result.bluebeam_markups)}")
    print(f"OCR'd:    {result.ocr_pages_processed} pages")

    if result.errors:
        print(f"\nErrors:")
        for e in result.errors:
            print(f"  - {e}")

    if result.pages:
        print(f"\nPage Details:")
        for p in result.pages:
            text_preview = p.text[:80].replace("\n", " ") if p.text else "(no text)"
            print(f"  Page {p.page:3d} | {p.method:10s} | {p.text_length:5d} chars | {text_preview}")

    if result.spec_sections:
        print(f"\nSpec Sections: {len(result.spec_sections)}")
        for s in result.spec_sections:
            print(f"  {s.section_code} — {s.section_name}")

    print(f"{'='*60}\n")


def _launch_web():
    """Launch the Flask web dashboard."""
    from web.app import create_app
    app = create_app()
    print("\n  DABO Web Dashboard")
    print("  http://localhost:5000\n")
    app.run(debug=True, port=5000)


def _launch_streamlit():
    """Launch the Streamlit dashboard (legacy)."""
    import subprocess
    dashboard_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    print(f"Launching DABO Streamlit dashboard (legacy)...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])


if __name__ == "__main__":
    main()
