"""
Bluebeam / PDF annotation markup extractor.

Reads the annotation layer from PDF files (including Bluebeam .bfx exports)
and extracts callouts, measurements, text boxes, stamps, clouds, and other
markups that field teams add during plan review.

This data feeds into conflict detection and RFI generation — catching things
that plain text extraction from the drawing itself would miss.

Requires PyMuPDF (fitz). Gracefully returns empty list if not installed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Markup:
    sheet_id: str
    markup_type: str       # callout, measurement, text, cloud, highlight, stamp, polyline
    label: str             # short label (e.g. "RFI", "HOLD", "VERIFY")
    content: str           # full text content of the markup
    author: str            # who created it in Bluebeam
    color: str             # hex color
    page_number: int
    x: float = 0.0
    y: float = 0.0

    def to_dict(self):
        return asdict(self)


# Map PDF annotation type codes to human-readable names
_ANNOT_TYPE_MAP = {
    0: "text",          # Text note / sticky
    1: "highlight",     # Highlight
    4: "stamp",         # Stamp (Bluebeam custom stamps)
    5: "strikeout",     # Strikeout
    6: "underline",     # Underline
    8: "callout",       # Free text / callout (Bluebeam callouts)
    9: "polyline",      # Polyline / cloud markup
    12: "cloud",        # Polygon / cloud
    15: "measurement",  # Bluebeam measurements show as polyline annotations
    19: "text",         # Widget (form fields)
}


def extract_markups(pdf_path: str, sheet_id: str = "") -> list[Markup]:
    """
    Extract all annotations/markups from a PDF file.

    Works with:
    - Standard PDF annotations
    - Bluebeam Revu markups (saved as PDF annotations)
    - Bluebeam .bfx files (internally PDF format)

    Returns list of Markup objects.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []

    markups = []

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return []

    for page_num, page in enumerate(doc):
        for annot in page.annots() or []:
            annot_type = annot.type[0]
            type_name = _ANNOT_TYPE_MAP.get(annot_type, "other")

            # Get the text content
            content = (annot.info.get("content", "") or "").strip()

            # Get subject/label — Bluebeam puts markup type here
            label = (annot.info.get("subject", "") or "").strip()
            if not label:
                label = type_name.upper()

            # Author
            author = (annot.info.get("title", "") or "").strip()

            # Color
            color_tuple = annot.colors.get("stroke") or annot.colors.get("fill")
            if color_tuple:
                r, g, b = [int(c * 255) for c in color_tuple[:3]]
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#ff0000"

            # Position
            rect = annot.rect
            x = round(rect.x0, 1)
            y = round(rect.y0, 1)

            # Skip empty annotations
            if not content and type_name in ("text", "highlight", "underline", "strikeout"):
                continue

            markups.append(Markup(
                sheet_id=sheet_id,
                markup_type=type_name,
                label=label,
                content=content,
                author=author,
                color=color,
                page_number=page_num + 1,
                x=x,
                y=y,
            ))

    doc.close()
    return markups


def extract_markups_from_bluebeam(pdf_path: str, sheet_id: str = "") -> list[Markup]:
    """
    Alias for extract_markups — Bluebeam .bfx files are PDFs internally.
    This function exists for clarity in the API.
    """
    return extract_markups(pdf_path, sheet_id)
