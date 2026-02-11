"""
File router — takes uploaded files and sends them to the right extractor.

Determines file type, validates size, and dispatches to:
  - pdf_engine for drawing PDFs
  - bluebeam for Bluebeam-annotated PDFs
  - spec_reader for specification documents
  - image_ocr for image-only pages
"""
from __future__ import annotations

import fitz
from dataclasses import dataclass, field
from pathlib import Path

from config.settings import MAX_UPLOAD_MB, SUPPORTED_EXTENSIONS
from ingestion.pdf_engine import extract_pdf, PageResult
from ingestion.bluebeam import extract_bluebeam_markups, BluebeamMarkup
from ingestion.image_ocr import ocr_page
from ingestion.spec_reader import read_spec, SpecSection
from utils.helpers import file_hash
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class FileIngestionResult:
    filename: str
    file_path: str
    file_type: str          # "drawing", "spec", "unknown"
    file_hash: str = ""
    file_size_mb: float = 0.0
    page_count: int = 0
    pages: list[PageResult] = field(default_factory=list)
    bluebeam_markups: list[BluebeamMarkup] = field(default_factory=list)
    spec_sections: list[SpecSection] = field(default_factory=list)
    ocr_pages_processed: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size_mb": self.file_size_mb,
            "page_count": self.page_count,
            "pages_extracted": len(self.pages),
            "bluebeam_markups": len(self.bluebeam_markups),
            "spec_sections": len(self.spec_sections),
            "ocr_pages_processed": self.ocr_pages_processed,
            "errors": self.errors,
        }


def route_file(file_path: Path | str, run_ocr: bool = True) -> FileIngestionResult:
    """
    Process a single file through the ingestion pipeline.

    1. Validate file type and size
    2. Detect if it's a drawing set or spec document
    3. Extract text + annotations
    4. Run OCR on pages that need it (if enabled)
    5. Return structured result
    """
    file_path = Path(file_path)
    result = FileIngestionResult(
        filename=file_path.name,
        file_path=str(file_path),
        file_type="unknown",
    )

    # ── Validate ──────────────────────────────────────
    if not file_path.exists():
        result.errors.append(f"File not found: {file_path}")
        return result

    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        result.errors.append(f"Unsupported file type: {ext}")
        return result

    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        result.errors.append(f"File too large: {size_mb:.1f} MB (max {MAX_UPLOAD_MB} MB)")
        return result

    result.file_size_mb = round(size_mb, 2)
    result.file_hash = file_hash(file_path)

    # ── Route by type ─────────────────────────────────
    if ext == ".pdf":
        result = _process_pdf(file_path, result, run_ocr)
    elif ext in (".docx", ".doc"):
        result.file_type = "spec"
        result.spec_sections = read_spec(file_path)

    return result


def route_files(file_paths: list[Path | str], run_ocr: bool = True) -> list[FileIngestionResult]:
    """Process multiple files."""
    results = []
    for fp in file_paths:
        results.append(route_file(fp, run_ocr))
    return results


def _process_pdf(file_path: Path, result: FileIngestionResult, run_ocr: bool) -> FileIngestionResult:
    """Handle PDF files — could be drawings or specs."""
    try:
        # Get page count
        doc = fitz.open(str(file_path))
        result.page_count = len(doc)
        doc.close()

        # Classify: drawing vs spec
        result.file_type = _classify_pdf_type(file_path)
        log.info("Classified %s as: %s", file_path.name, result.file_type)

        if result.file_type == "spec":
            result.spec_sections = read_spec(file_path)
        else:
            # Extract as drawing set
            result.pages = extract_pdf(file_path)

            # Extract Bluebeam markups
            result.bluebeam_markups = extract_bluebeam_markups(file_path)

            # OCR pages that need it
            if run_ocr:
                ocr_count = 0
                for page in result.pages:
                    if page.method == "needs_ocr":
                        text = ocr_page(file_path, page.page)
                        if text:
                            page.text = text
                            page.text_length = len(text)
                            page.method = "ocr"
                            ocr_count += 1
                result.ocr_pages_processed = ocr_count

    except Exception as e:
        log.error("Failed to process PDF %s: %s", file_path.name, e)
        result.errors.append(str(e))

    return result


def _classify_pdf_type(file_path: Path) -> str:
    """
    Determine if a PDF is a drawing set or a specification document.

    Heuristics:
    - Specs tend to have lots of text, small page sizes (letter/legal)
    - Drawings have less text, large page sizes (ARCH D, E, etc.)
    - Specs have CSI section headers ("SECTION 03 30 00")
    """
    doc = fitz.open(str(file_path))
    if len(doc) == 0:
        doc.close()
        return "unknown"

    # Sample first few pages
    sample_size = min(5, len(doc))
    total_text = 0
    large_pages = 0
    has_section_header = False

    for i in range(sample_size):
        page = doc[i]
        text = page.get_text("text")
        total_text += len(text)

        # ARCH D = 24x36 = ~1728x2592 pts; letter = 612x792 pts
        if page.rect.width > 1000 or page.rect.height > 1000:
            large_pages += 1

        if "SECTION" in text.upper() and any(
            c.isdigit() for c in text[:500]
        ):
            import re
            if re.search(r"SECTION\s+\d{2}\s?\d{2}\s?\d{2}", text, re.IGNORECASE):
                has_section_header = True

    doc.close()

    # Decision logic
    avg_text = total_text / sample_size if sample_size else 0

    if has_section_header and avg_text > 2000:
        return "spec"
    if large_pages > sample_size / 2:
        return "drawing"
    if avg_text > 3000:
        return "spec"

    return "drawing"
