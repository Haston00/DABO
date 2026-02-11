"""
Cross-reference map builder for commercial drawing sets.

Takes extracted entities from all sheets and builds a bidirectional map:
  - Which sheets reference which other sheets
  - Which spec sections are referenced and by whom
  - Which equipment tags appear on which sheets
  - Broken references (sheet X references Y but Y doesn't exist)

The cross-reference map is the foundation for conflict detection.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from classification.entity_extractor import SheetEntities
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class BrokenReference:
    source_sheet: str
    ref_type: str           # "drawing_ref", "callout", "spec_ref"
    target: str             # What was referenced
    description: str


@dataclass
class CrossReferenceMap:
    """Complete cross-reference map for a drawing set."""
    # Forward refs: {target: [source_sheets]}
    drawing_refs: dict[str, list[str]] = field(default_factory=dict)
    spec_refs: dict[str, list[str]] = field(default_factory=dict)
    callouts: dict[str, list[str]] = field(default_factory=dict)
    equipment_refs: dict[str, list[str]] = field(default_factory=dict)

    # Reverse refs: {source_sheet: [targets]}
    sheet_references_out: dict[str, list[str]] = field(default_factory=dict)
    sheet_referenced_by: dict[str, list[str]] = field(default_factory=dict)

    # All sheet IDs in the set
    all_sheet_ids: set[str] = field(default_factory=set)
    all_spec_refs: set[str] = field(default_factory=set)
    all_equipment: set[str] = field(default_factory=set)

    # Broken references
    broken_refs: list[BrokenReference] = field(default_factory=list)

    # Discipline coverage
    disciplines_present: dict[str, list[str]] = field(default_factory=dict)  # {code: [sheet_ids]}

    def to_dict(self) -> dict:
        return {
            "total_sheets": len(self.all_sheet_ids),
            "drawing_refs": len(self.drawing_refs),
            "spec_refs": len(self.spec_refs),
            "equipment_tags": len(self.all_equipment),
            "broken_refs": len(self.broken_refs),
            "disciplines": {k: len(v) for k, v in self.disciplines_present.items()},
        }


def build_cross_reference_map(entities_list: list[SheetEntities]) -> CrossReferenceMap:
    """
    Build a complete cross-reference map from all extracted entities.
    """
    xref = CrossReferenceMap()

    # Collect all sheet IDs and disciplines
    for ent in entities_list:
        xref.all_sheet_ids.add(ent.sheet_id)
        xref.disciplines_present.setdefault(ent.discipline_code, []).append(ent.sheet_id)

    # Build forward references
    for ent in entities_list:
        sid = ent.sheet_id

        # Drawing cross-references
        for ref in ent.parsed.drawing_refs:
            xref.drawing_refs.setdefault(ref.value, []).append(sid)
            xref.sheet_references_out.setdefault(sid, []).append(ref.value)
            xref.sheet_referenced_by.setdefault(ref.value, []).append(sid)

        # Spec section references
        for ref in ent.parsed.spec_refs:
            xref.spec_refs.setdefault(ref.value, []).append(sid)
            xref.all_spec_refs.add(ref.value)

        # Detail/section callouts (extract target sheet from callout)
        for ref in ent.parsed.callouts:
            xref.callouts.setdefault(ref.value, []).append(sid)
            # Extract target sheet from callout (e.g., "3/A-501" → "A-501")
            parts = ref.value.split("/")
            if len(parts) == 2:
                target_sheet = parts[1]
                xref.sheet_references_out.setdefault(sid, []).append(target_sheet)
                xref.sheet_referenced_by.setdefault(target_sheet, []).append(sid)

        # Equipment tags
        for ref in ent.parsed.equipment_tags:
            xref.equipment_refs.setdefault(ref.value, []).append(sid)
            xref.all_equipment.add(ref.value)

    # Deduplicate
    for d in [xref.drawing_refs, xref.spec_refs, xref.callouts, xref.equipment_refs,
              xref.sheet_references_out, xref.sheet_referenced_by]:
        for key in d:
            d[key] = sorted(set(d[key]))

    # Find broken references
    xref.broken_refs = _find_broken_refs(xref)

    _log_summary(xref)
    return xref


def _find_broken_refs(xref: CrossReferenceMap) -> list[BrokenReference]:
    """Identify references to sheets that don't exist in the set."""
    broken = []

    # Drawing references to nonexistent sheets
    for target, sources in xref.drawing_refs.items():
        if target not in xref.all_sheet_ids:
            for src in sources:
                broken.append(BrokenReference(
                    source_sheet=src,
                    ref_type="drawing_ref",
                    target=target,
                    description=f"Sheet {src} references {target}, but {target} is not in the drawing set.",
                ))

    # Callout references to nonexistent sheets
    for callout, sources in xref.callouts.items():
        parts = callout.split("/")
        if len(parts) == 2:
            target_sheet = parts[1]
            if target_sheet not in xref.all_sheet_ids:
                for src in sources:
                    broken.append(BrokenReference(
                        source_sheet=src,
                        ref_type="callout",
                        target=callout,
                        description=f"Sheet {src} has callout {callout}, but target sheet {target_sheet} is not in the set.",
                    ))

    return broken


def get_shared_equipment(xref: CrossReferenceMap) -> dict[str, list[str]]:
    """
    Find equipment tags that appear on multiple discipline sheets.
    These are coordination points (e.g., AHU-1 on M-101 and E-201).
    """
    shared = {}
    for tag, sheets in xref.equipment_refs.items():
        if len(sheets) > 1:
            shared[tag] = sheets
    return shared


def get_discipline_interfaces(xref: CrossReferenceMap) -> list[tuple[str, str, int]]:
    """
    Find which disciplines reference each other and how many times.
    Returns list of (disc_A, disc_B, ref_count).
    """
    # Build sheet→discipline lookup
    sheet_to_disc = {}
    for code, sheets in xref.disciplines_present.items():
        for s in sheets:
            sheet_to_disc[s] = code

    interface_count: dict[tuple[str, str], int] = {}
    for target, sources in xref.drawing_refs.items():
        target_disc = sheet_to_disc.get(target)
        for src in sources:
            src_disc = sheet_to_disc.get(src)
            if src_disc and target_disc and src_disc != target_disc:
                pair = tuple(sorted([src_disc, target_disc]))
                interface_count[pair] = interface_count.get(pair, 0) + 1

    return [(a, b, count) for (a, b), count in sorted(interface_count.items(), key=lambda x: -x[1])]


def _log_summary(xref: CrossReferenceMap):
    log.info(
        "Cross-reference map: %d sheets, %d drawing refs, %d spec refs, %d equipment tags, %d broken refs",
        len(xref.all_sheet_ids), len(xref.drawing_refs), len(xref.all_spec_refs),
        len(xref.all_equipment), len(xref.broken_refs),
    )
    if xref.broken_refs:
        for br in xref.broken_refs[:5]:
            log.warning("  Broken ref: %s", br.description)
        if len(xref.broken_refs) > 5:
            log.warning("  ... and %d more broken refs", len(xref.broken_refs) - 5)
