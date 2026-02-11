"""
Primary PDF text extraction using PyMuPDF (fitz).

This is the workhorse — handles 90%+ of construction drawing sets.
Falls back to pdfplumber for table-heavy pages, then OCR as last resort.

Returns a list of PageResult dicts, one per page:
    {
        "page": 1,
        "text": "...",
        "text_length": 4532,
        "method": "pymupdf",          # or "pdfplumber" or "ocr"
        "annotations": [...],
        "images": [{"bbox": ..., "size": ...}],
        "tables": [...],
    }
"""
from __future__ import annotations

import fitz  # PyMuPDF
import pdfplumber
from dataclasses import dataclass, field
from pathlib import Path

from config.settings import OCR_FALLBACK_THRESHOLD
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class PageResult:
    page: int
    text: str = ""
    text_length: int = 0
    method: str = "pymupdf"
    annotations: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    tables: list[list] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "text": self.text,
            "text_length": self.text_length,
            "method": self.method,
            "annotations": self.annotations,
            "images": self.images,
            "tables": self.tables,
            "width": self.width,
            "height": self.height,
        }


def extract_pdf(file_path: Path | str) -> list[PageResult]:
    """
    Extract text, annotations, and metadata from every page of a PDF.

    Strategy:
    1. PyMuPDF text extraction (fast, preserves layout)
    2. If text is too short → try pdfplumber (better with tables/forms)
    3. If still too short → flag for OCR (handled by image_ocr module)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    log.info("Opening PDF: %s", file_path.name)
    results = []

    doc = fitz.open(str(file_path))
    log.info("PDF has %d pages, size %.1f MB", len(doc), file_path.stat().st_size / 1e6)

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pr = PageResult(
            page=page_idx + 1,
            width=page.rect.width,
            height=page.rect.height,
        )

        # ── Step 1: PyMuPDF text extraction ────────────
        text = page.get_text("text")
        if text:
            pr.text = text.strip()
            pr.text_length = len(pr.text)
            pr.method = "pymupdf"

        # ── Step 2: pdfplumber fallback for sparse pages ─
        if pr.text_length < OCR_FALLBACK_THRESHOLD:
            plumber_text = _pdfplumber_extract(file_path, page_idx)
            if plumber_text and len(plumber_text) > pr.text_length:
                pr.text = plumber_text.strip()
                pr.text_length = len(pr.text)
                pr.method = "pdfplumber"

        # ── Step 3: Mark for OCR if still sparse ─────────
        if pr.text_length < OCR_FALLBACK_THRESHOLD:
            pr.method = "needs_ocr"
            log.debug("Page %d has only %d chars — needs OCR", pr.page, pr.text_length)

        # ── Extract annotations ────────────────────────
        pr.annotations = _extract_annotations(page)

        # ── Extract image info (bounding boxes, not pixels) ─
        pr.images = _extract_image_info(page)

        results.append(pr)

    doc.close()
    log.info(
        "Extracted %d pages: %d pymupdf, %d pdfplumber, %d need OCR",
        len(results),
        sum(1 for r in results if r.method == "pymupdf"),
        sum(1 for r in results if r.method == "pdfplumber"),
        sum(1 for r in results if r.method == "needs_ocr"),
    )
    return results


def extract_tables(file_path: Path | str, page_num: int) -> list[list]:
    """Extract tables from a specific page using pdfplumber."""
    file_path = Path(file_path)
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                return []
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            return tables or []
    except Exception as e:
        log.warning("Table extraction failed on page %d: %s", page_num, e)
        return []


def get_page_count(file_path: Path | str) -> int:
    """Quick page count without full extraction."""
    doc = fitz.open(str(file_path))
    count = len(doc)
    doc.close()
    return count


# ── Private helpers ────────────────────────────────────────

def _pdfplumber_extract(file_path: Path, page_idx: int) -> str:
    """Try pdfplumber on a single page."""
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            if page_idx < len(pdf.pages):
                text = pdf.pages[page_idx].extract_text()
                return text or ""
    except Exception as e:
        log.debug("pdfplumber fallback failed on page %d: %s", page_idx + 1, e)
    return ""


def _extract_annotations(page: fitz.Page) -> list[dict]:
    """Pull all PDF annotations (Bluebeam markups, comments, etc.)."""
    annots = []
    for annot in page.annots() or []:
        info = annot.info
        annots.append({
            "type": annot.type[1],  # e.g., "Text", "Highlight", "FreeText"
            "content": info.get("content", ""),
            "subject": info.get("subject", ""),
            "title": info.get("title", ""),
            "rect": list(annot.rect),
            "color": annot.colors.get("stroke", None),
        })
    return annots


def _extract_image_info(page: fitz.Page) -> list[dict]:
    """Get bounding boxes and sizes of embedded images (not the pixels)."""
    images = []
    for img in page.get_images(full=True):
        xref = img[0]
        try:
            bbox = page.get_image_bbox(img)
            images.append({
                "xref": xref,
                "bbox": list(bbox),
                "width": img[2],
                "height": img[3],
            })
        except Exception:
            pass
    return images
