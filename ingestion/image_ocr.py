"""
OCR fallback for scanned/image-based PDF pages.

Used when PyMuPDF and pdfplumber both return insufficient text.
Rasterizes the page to an image, then runs Tesseract OCR.

Requires Tesseract to be installed on the system.
If Tesseract is not available, logs a warning and returns empty text.
"""
from __future__ import annotations

import fitz
from pathlib import Path

from config.settings import TESSERACT_CMD, OCR_DPI
from utils.logger import get_logger

log = get_logger(__name__)

_TESSERACT_AVAILABLE = None


def _check_tesseract() -> bool:
    """Check if Tesseract is installed and accessible."""
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
        log.info("Tesseract OCR available")
    except Exception:
        _TESSERACT_AVAILABLE = False
        log.warning("Tesseract OCR not available — scanned pages will have no text")

    return _TESSERACT_AVAILABLE


def ocr_page(file_path: Path | str, page_num: int) -> str:
    """
    OCR a single page of a PDF.

    Args:
        file_path: Path to the PDF
        page_num: 1-based page number

    Returns:
        Extracted text, or empty string if OCR is unavailable.
    """
    if not _check_tesseract():
        return ""

    import pytesseract
    from PIL import Image
    import io

    file_path = Path(file_path)
    doc = fitz.open(str(file_path))

    if page_num < 1 or page_num > len(doc):
        doc.close()
        return ""

    page = doc[page_num - 1]
    log.debug("OCR page %d of %s at %d DPI", page_num, file_path.name, OCR_DPI)

    # Rasterize page to image
    mat = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()

    # Run OCR
    img = Image.open(io.BytesIO(img_bytes))
    try:
        text = pytesseract.image_to_string(img, lang="eng")
        log.debug("OCR extracted %d chars from page %d", len(text), page_num)
        return text.strip()
    except Exception as e:
        log.warning("OCR failed on page %d: %s", page_num, e)
        return ""


def ocr_pages(file_path: Path | str, page_nums: list[int]) -> dict[int, str]:
    """
    OCR multiple pages. Returns {page_num: text}.
    """
    results = {}
    for pn in page_nums:
        results[pn] = ocr_page(file_path, pn)
    return results


def is_available() -> bool:
    """Check if OCR capability is available."""
    return _check_tesseract()
