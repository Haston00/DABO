"""
Entity extractor — pull all structured data from classified sheets.

This is the top-level extraction module. For each classified sheet it:
  1. Runs text_parser to get spec refs, callouts, equipment tags, etc.
  2. Runs dimension_parser to get all dimensional data
  3. Combines into a single SheetEntities result
  4. Stores to database for downstream analysis

Built for commercial construction drawing sets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from classification.sheet_classifier import ClassifiedSheet
from classification.text_parser import parse_sheet_text, ParsedSheet
from classification.dimension_parser import parse_dimensions, Dimension
from utils.logger import get_logger

if TYPE_CHECKING:
    from ingestion.pdf_engine import PageResult

log = get_logger(__name__)


@dataclass
class SheetEntities:
    """All extracted entities from a single classified sheet."""
    sheet_id: str
    page: int
    discipline_code: str
    discipline_name: str
    title: str = ""

    # From text_parser
    parsed: ParsedSheet = field(default_factory=ParsedSheet)

    # From dimension_parser
    dimensions: list[Dimension] = field(default_factory=list)

    # Summary stats
    total_entities: int = 0

    def to_dict(self) -> dict:
        dim_summary = {}
        for d in self.dimensions:
            dim_summary[d.dim_type] = dim_summary.get(d.dim_type, 0) + 1

        return {
            "sheet_id": self.sheet_id,
            "page": self.page,
            "discipline_code": self.discipline_code,
            "discipline_name": self.discipline_name,
            "title": self.title,
            "tokens": self.parsed.to_dict(),
            "dimensions": {
                "count": len(self.dimensions),
                "by_type": dim_summary,
                "items": [{"raw": d.raw, "type": d.dim_type, "display": d.value_display} for d in self.dimensions[:50]],
            },
            "total_entities": self.total_entities,
        }


def extract_entities(
    page: PageResult,
    classification: ClassifiedSheet,
) -> SheetEntities:
    """
    Extract all entities from a single classified sheet.
    """
    entities = SheetEntities(
        sheet_id=classification.sheet_id,
        page=classification.page,
        discipline_code=classification.discipline_code,
        discipline_name=classification.discipline_name,
        title=classification.title,
    )

    text = page.text or ""

    if not text:
        return entities

    # Run text parser
    entities.parsed = parse_sheet_text(text)

    # Run dimension parser
    entities.dimensions = parse_dimensions(text)

    # Total count
    entities.total_entities = entities.parsed.total_tokens + len(entities.dimensions)

    log.debug(
        "Sheet %s (%s): %d tokens, %d dimensions",
        entities.sheet_id, entities.discipline_code,
        entities.parsed.total_tokens, len(entities.dimensions),
    )

    return entities


def extract_all_entities(
    pages: list[PageResult],
    classifications: list[ClassifiedSheet],
) -> list[SheetEntities]:
    """
    Extract entities from all sheets in a drawing set.
    Pages and classifications must be aligned (same length, same order).
    """
    if len(pages) != len(classifications):
        log.error(
            "Page count (%d) != classification count (%d)",
            len(pages), len(classifications),
        )
        return []

    results = []
    for page, cls in zip(pages, classifications):
        entities = extract_entities(page, cls)
        results.append(entities)

    _log_extraction_summary(results)
    return results


def build_cross_reference_index(entities_list: list[SheetEntities]) -> dict:
    """
    Build a cross-reference index from all extracted entities.

    Returns a dict mapping reference targets to their source sheets:
    {
        "drawing_refs": {"A-301": ["M-101", "E-201"], ...},
        "spec_refs": {"03 30 00": ["S-101", "S-102"], ...},
        "callouts": {"3/A-501": ["A-101", "A-102"], ...},
        "equipment_tags": {"AHU-1": ["M-101", "M-201"], ...},
        ...
    }
    """
    index = {
        "drawing_refs": {},
        "spec_refs": {},
        "callouts": {},
        "equipment_tags": {},
        "room_refs": {},
        "door_marks": {},
        "window_marks": {},
        "grid_refs": {},
        "code_refs": {},
    }

    for ent in entities_list:
        sid = ent.sheet_id

        for ref in ent.parsed.drawing_refs:
            index["drawing_refs"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.spec_refs:
            index["spec_refs"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.callouts:
            index["callouts"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.equipment_tags:
            index["equipment_tags"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.room_refs:
            index["room_refs"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.door_marks:
            index["door_marks"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.window_marks:
            index["window_marks"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.grid_refs:
            index["grid_refs"].setdefault(ref.value, []).append(sid)
        for ref in ent.parsed.code_refs:
            index["code_refs"].setdefault(ref.value, []).append(sid)

    # Deduplicate source lists
    for category in index.values():
        for key in category:
            category[key] = sorted(set(category[key]))

    _log_xref_summary(index)
    return index


def _log_extraction_summary(results: list[SheetEntities]):
    """Log summary of extraction across all sheets."""
    total_tokens = sum(r.parsed.total_tokens for r in results)
    total_dims = sum(len(r.dimensions) for r in results)
    sheets_with_data = sum(1 for r in results if r.total_entities > 0)

    log.info(
        "Extracted entities from %d/%d sheets: %d tokens, %d dimensions",
        sheets_with_data, len(results), total_tokens, total_dims,
    )

    # Per-discipline breakdown
    by_disc: dict[str, dict] = {}
    for r in results:
        code = r.discipline_code
        if code not in by_disc:
            by_disc[code] = {"sheets": 0, "tokens": 0, "dims": 0}
        by_disc[code]["sheets"] += 1
        by_disc[code]["tokens"] += r.parsed.total_tokens
        by_disc[code]["dims"] += len(r.dimensions)

    for code, stats in sorted(by_disc.items()):
        log.info(
            "  %s: %d sheets, %d tokens, %d dimensions",
            code, stats["sheets"], stats["tokens"], stats["dims"],
        )


def _log_xref_summary(index: dict):
    """Log cross-reference index summary."""
    for category, refs in index.items():
        if refs:
            log.info("  Cross-ref %s: %d unique targets", category, len(refs))
