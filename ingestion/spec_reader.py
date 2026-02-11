"""
Specification document reader — handles PDF specs and Word (.docx) files.

Construction specs are typically organized by CSI division/section.
This module extracts text and identifies spec section boundaries
so the conflict detector can cross-reference drawings against specs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from utils.logger import get_logger

log = get_logger(__name__)

# Pattern for CSI section headers like "SECTION 03 30 00 - CAST-IN-PLACE CONCRETE"
_SECTION_HEADER = re.compile(
    r"SECTION\s+(\d{2}\s?\d{2}\s?\d{2})\s*[-–—]\s*(.+)",
    re.IGNORECASE
)

# Pattern for spec part headers (PART 1, PART 2, PART 3)
_PART_HEADER = re.compile(
    r"PART\s+(\d)\s*[-–—]\s*(.+)",
    re.IGNORECASE
)


@dataclass
class SpecSection:
    section_code: str      # "03 30 00"
    section_name: str      # "CAST-IN-PLACE CONCRETE"
    text: str = ""
    parts: dict[int, str] = field(default_factory=dict)  # {1: "GENERAL", 2: "PRODUCTS", 3: "EXECUTION"}
    page_start: int = 0


def read_spec_pdf(file_path: Path | str) -> list[SpecSection]:
    """
    Extract spec sections from a PDF specification document.
    """
    file_path = Path(file_path)
    log.info("Reading spec PDF: %s", file_path.name)

    import fitz
    doc = fitz.open(str(file_path))

    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()

    return _parse_spec_text(full_text)


def read_spec_docx(file_path: Path | str) -> list[SpecSection]:
    """
    Extract spec sections from a Word document.
    """
    file_path = Path(file_path)
    log.info("Reading spec DOCX: %s", file_path.name)

    try:
        from docx import Document
    except ImportError:
        log.warning("python-docx not installed — cannot read .docx specs")
        return []

    doc = Document(str(file_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    return _parse_spec_text(full_text)


def read_spec(file_path: Path | str) -> list[SpecSection]:
    """Route to the correct reader based on file extension."""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return read_spec_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return read_spec_docx(file_path)
    else:
        log.warning("Unsupported spec format: %s", ext)
        return []


def _parse_spec_text(text: str) -> list[SpecSection]:
    """
    Parse raw spec text into structured sections.
    Splits on CSI section headers, then identifies Part 1/2/3 within each.
    """
    sections = []
    lines = text.split("\n")
    current_section = None
    current_part = 0
    part_text = []

    for line in lines:
        # Check for new CSI section
        sec_match = _SECTION_HEADER.match(line.strip())
        if sec_match:
            # Save previous section
            if current_section:
                if current_part and part_text:
                    current_section.parts[current_part] = "\n".join(part_text)
                current_section.text = text  # full text for search
                sections.append(current_section)

            code = sec_match.group(1).strip()
            name = sec_match.group(2).strip()
            current_section = SpecSection(section_code=code, section_name=name)
            current_part = 0
            part_text = []
            continue

        # Check for Part header within a section
        part_match = _PART_HEADER.match(line.strip())
        if part_match and current_section:
            if current_part and part_text:
                current_section.parts[current_part] = "\n".join(part_text)
            current_part = int(part_match.group(1))
            part_text = []
            continue

        part_text.append(line)

    # Save last section
    if current_section:
        if current_part and part_text:
            current_section.parts[current_part] = "\n".join(part_text)
        sections.append(current_section)

    log.info("Parsed %d spec sections", len(sections))
    return sections
