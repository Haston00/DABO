"""
Combined summary report builder.

Generates a single report with:
  - Project info
  - Sheet index with classifications
  - Cross-reference summary
  - Conflict summary
  - RFI stats
"""
from __future__ import annotations

from pathlib import Path

from classification.sheet_classifier import ClassifiedSheet
from analysis.cross_reference import CrossReferenceMap
from analysis.conflict_detector import DetectionResult
from analysis.rfi_generator import RFILog
from utils.logger import get_logger

log = get_logger(__name__)


def build_text_report(
    project_name: str,
    sheets: list[ClassifiedSheet],
    xref: CrossReferenceMap,
    detection: DetectionResult,
    rfi_log: RFILog,
) -> str:
    """Build a plain-text summary report."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  DABO Plan Review Report")
    lines.append(f"  Project: {project_name}")
    lines.append(f"  Generated: {rfi_log.generated_date}")
    lines.append("=" * 70)

    # ── Sheet Index ────────────────────────────────────────
    lines.append(f"\nSHEET INDEX ({len(sheets)} sheets)")
    lines.append("-" * 50)
    for s in sorted(sheets, key=lambda x: x.sheet_id):
        lines.append(f"  {s.sheet_id:10s} | {s.discipline_code:5s} | {s.discipline_name:25s} | {s.title[:30]}")

    # ── Discipline Summary ─────────────────────────────────
    lines.append(f"\nDISCIPLINE COVERAGE")
    lines.append("-" * 50)
    for code, sheet_ids in sorted(xref.disciplines_present.items()):
        lines.append(f"  {code:5s}: {len(sheet_ids)} sheets ({', '.join(sheet_ids)})")

    # ── Cross-Reference Summary ────────────────────────────
    lines.append(f"\nCROSS-REFERENCE SUMMARY")
    lines.append("-" * 50)
    lines.append(f"  Drawing references: {len(xref.drawing_refs)} unique targets")
    lines.append(f"  Spec sections:     {len(xref.all_spec_refs)} unique")
    lines.append(f"  Equipment tags:    {len(xref.all_equipment)} unique")
    lines.append(f"  Broken references: {len(xref.broken_refs)}")

    if xref.broken_refs:
        lines.append(f"\n  Broken References:")
        for br in xref.broken_refs:
            lines.append(f"    {br.source_sheet} -> {br.target} ({br.ref_type})")

    # ── Conflict Summary ───────────────────────────────────
    lines.append(f"\nCONFLICT DETECTION RESULTS")
    lines.append("-" * 50)
    lines.append(f"  Rules checked:     {detection.rules_checked}")
    lines.append(f"  Rules triggered:   {detection.rules_triggered}")
    lines.append(f"  Total conflicts:   {len(detection.conflicts)}")
    lines.append(f"    CRITICAL:        {detection.critical_count}")
    lines.append(f"    MAJOR:           {detection.major_count}")
    lines.append(f"    MINOR:           {detection.minor_count}")

    # ── RFI Summary ────────────────────────────────────────
    lines.append(f"\nRFI LOG SUMMARY")
    lines.append("-" * 50)
    lines.append(f"  Total RFIs:   {rfi_log.total}")
    lines.append(f"  CRITICAL:     {rfi_log.critical_count}")
    lines.append(f"  MAJOR:        {rfi_log.major_count}")

    lines.append("\n" + "=" * 70)
    lines.append("  End of Report")
    lines.append("=" * 70)

    return "\n".join(lines)


def write_report(report_text: str, output_path: Path | str) -> Path:
    """Write report to a text file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    log.info("Report written: %s", output_path.name)
    return output_path
