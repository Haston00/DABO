"""
Sheet classifier — identify discipline for every sheet in a commercial drawing set.

Three-pass classification:
  1. Sheet prefix matching (A-101 → Architectural, S-201 → Structural)
  2. Title block keyword scan (REFLECTED CEILING → Arch, PANEL SCHEDULE → Elec)
  3. Content-based classification (equipment tags, spec refs, terminology)

Returns classified sheets with confidence scores.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from config.sheet_patterns import SHEET_PREFIX_PATTERNS, TITLE_BLOCK_KEYWORDS
from ingestion.pdf_engine import PageResult
from utils.helpers import normalize_sheet_id, extract_page_number
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ClassifiedSheet:
    page: int
    sheet_id: str              # Normalized: A-101, S-201, M-001
    discipline_code: str       # ARCH, STR, MECH, ELEC, PLMB, FP, FA, CIV, etc.
    discipline_name: str       # "Architectural", "Structural", etc.
    csi_divisions: list[str] = field(default_factory=list)  # ["06","07","08","09"]
    title: str = ""            # Sheet title from title block
    confidence: float = 0.0    # 0.0 – 1.0
    method: str = ""           # "prefix", "keyword", "content", "fallback"
    text_length: int = 0
    extraction_method: str = ""  # "pymupdf", "pdfplumber", "ocr"

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "sheet_id": self.sheet_id,
            "discipline_code": self.discipline_code,
            "discipline_name": self.discipline_name,
            "csi_divisions": self.csi_divisions,
            "title": self.title,
            "confidence": self.confidence,
            "method": self.method,
            "text_length": self.text_length,
        }


# ── Content-based classification keywords ──────────────────
# When prefix and title block fail, scan content for discipline signals.
# These are commercial-specific terms weighted by discipline.
_CONTENT_SIGNALS: dict[str, list[tuple[str, float]]] = {
    "ARCH": [
        ("FLOOR PLAN", 3.0), ("ROOF PLAN", 2.5), ("REFLECTED CEILING", 3.0),
        ("BUILDING SECTION", 2.5), ("WALL SECTION", 2.5), ("EXTERIOR ELEVATION", 3.0),
        ("INTERIOR ELEVATION", 2.5), ("FINISH SCHEDULE", 3.0), ("DOOR SCHEDULE", 3.0),
        ("WINDOW SCHEDULE", 3.0), ("ROOM FINISH", 2.5), ("PARTITION TYPE", 2.5),
        ("ENLARGED PLAN", 2.0), ("RESTROOM", 2.0), ("TOILET", 1.5),
        ("CEILING HEIGHT", 2.0), ("GYP. BD.", 1.5), ("ACT CEILING", 2.0),
    ],
    "STR": [
        ("FOUNDATION PLAN", 3.0), ("FRAMING PLAN", 3.0), ("COLUMN SCHEDULE", 3.0),
        ("BEAM SCHEDULE", 3.0), ("STRUCTURAL NOTES", 3.0), ("SLAB ON GRADE", 2.5),
        ("PILE CAP", 2.5), ("GRADE BEAM", 2.5), ("SHEAR WALL", 2.5),
        ("MOMENT FRAME", 2.5), ("BRACE FRAME", 2.5), ("BASE PLATE", 2.0),
        ("ANCHOR BOLT", 2.0), ("W12X", 1.5), ("W24X", 1.5), ("HSS", 1.5),
        ("EMBED", 2.0), ("FOOTING", 2.5), ("PIER", 2.0), ("PILE", 2.0),
        ("CONCRETE SCHEDULE", 2.5), ("REBAR", 1.5), ("#4@", 1.5), ("#5@", 1.5),
    ],
    "MECH": [
        ("MECHANICAL PLAN", 3.0), ("HVAC PLAN", 3.0), ("DUCTWORK", 2.5),
        ("AIR HANDLING", 2.5), ("AHU", 2.0), ("RTU", 2.0), ("VAV", 2.0),
        ("DIFFUSER", 2.0), ("RETURN AIR", 2.0), ("SUPPLY AIR", 2.0),
        ("EXHAUST FAN", 2.0), ("MECHANICAL SCHEDULE", 3.0), ("EQUIPMENT SCHEDULE", 2.0),
        ("REFRIGERANT", 2.0), ("CHILLED WATER", 2.5), ("HOT WATER", 1.5),
        ("THERMOSTAT", 1.5), ("BAS", 1.5), ("DDC", 1.5), ("DAMPER", 1.5),
        ("CFM", 2.0), ("BTU", 1.5), ("TON", 1.0), ("MBH", 1.5),
    ],
    "PLMB": [
        ("PLUMBING PLAN", 3.0), ("PLUMBING RISER", 3.0), ("FIXTURE SCHEDULE", 2.5),
        ("WATER HEATER", 2.0), ("DOMESTIC WATER", 2.5), ("SANITARY", 2.5),
        ("STORM DRAIN", 2.5), ("ROOF DRAIN", 2.0), ("GREASE TRAP", 2.5),
        ("GREASE INTERCEPTOR", 2.5), ("BACKFLOW", 2.0), ("CLEANOUT", 2.0),
        ("FLOOR DRAIN", 2.0), ("LAVATORY", 2.0), ("WATER CLOSET", 2.0),
        ("URINAL", 2.5), ("DWV", 2.0), ("CW", 1.0), ("HW", 1.0),
    ],
    "ELEC": [
        ("ELECTRICAL PLAN", 3.0), ("LIGHTING PLAN", 3.0), ("POWER PLAN", 3.0),
        ("PANEL SCHEDULE", 3.0), ("ONE-LINE", 3.0), ("SINGLE LINE", 3.0),
        ("RISER DIAGRAM", 2.5), ("SWITCHBOARD", 2.5), ("SWITCHGEAR", 2.5),
        ("TRANSFORMER", 2.0), ("GENERATOR", 2.0), ("ATS", 2.0),
        ("MDP", 2.0), ("DISTRIBUTION", 1.5), ("RECEPTACLE", 2.0),
        ("CIRCUIT", 1.5), ("BREAKER", 1.5), ("CONDUIT", 1.5),
        ("AMPERE", 1.5), ("VOLTAGE", 1.5), ("277V", 2.0), ("480V", 2.5),
        ("120V", 1.5), ("WATT", 1.0),
    ],
    "FP": [
        ("FIRE PROTECTION", 3.0), ("SPRINKLER PLAN", 3.0), ("SPRINKLER RISER", 3.0),
        ("FIRE PUMP", 3.0), ("STANDPIPE", 2.5), ("FDC", 2.5),
        ("WET PIPE", 2.5), ("DRY PIPE", 2.5), ("PRE-ACTION", 2.5),
        ("SPRINKLER HEAD", 2.5), ("HYDRAULIC CALC", 2.5), ("NFPA 13", 3.0),
        ("FIRE SUPPRESSION", 2.5), ("CLEAN AGENT", 2.5),
    ],
    "FA": [
        ("FIRE ALARM PLAN", 3.0), ("FIRE ALARM RISER", 3.0), ("FACP", 3.0),
        ("SMOKE DETECTOR", 2.5), ("PULL STATION", 2.5), ("HORN/STROBE", 2.5),
        ("NOTIFICATION", 2.0), ("INITIATING DEVICE", 2.5), ("NFPA 72", 3.0),
        ("MASS NOTIFICATION", 2.5), ("DUCT DETECTOR", 2.5),
    ],
    "CIV": [
        ("SITE PLAN", 3.0), ("GRADING PLAN", 3.0), ("UTILITY PLAN", 3.0),
        ("PAVING PLAN", 2.5), ("EROSION CONTROL", 2.5), ("STORMWATER", 2.5),
        ("DETENTION", 2.0), ("CURB", 1.5), ("SIDEWALK", 1.5),
        ("PARKING", 2.0), ("FIRE LANE", 2.0), ("CONTOUR", 2.0),
        ("INVERT", 2.0), ("MANHOLE", 2.0), ("CATCH BASIN", 2.0),
    ],
    "TECH": [
        ("TECHNOLOGY PLAN", 3.0), ("DATA PLAN", 3.0), ("TELECOM", 2.5),
        ("STRUCTURED CABLING", 3.0), ("MDF", 2.5), ("IDF", 2.5),
        ("CABLE TRAY", 2.0), ("FIBER OPTIC", 2.5), ("CAT6", 2.5),
        ("WIRELESS AP", 2.0), ("ACCESS CONTROL", 2.5), ("CCTV", 2.5),
        ("SECURITY PLAN", 2.5), ("NURSE CALL", 2.5), ("PAGING", 2.0),
    ],
}


def classify_sheets(pages: list[PageResult]) -> list[ClassifiedSheet]:
    """
    Classify every page in a drawing set by discipline.

    Three-pass approach:
    1. Sheet prefix (highest confidence)
    2. Title block keywords
    3. Content signal scoring
    """
    classified = []

    for page in pages:
        sheet = ClassifiedSheet(
            page=page.page,
            sheet_id="",
            discipline_code="UNK",
            discipline_name="Unknown",
            text_length=page.text_length,
            extraction_method=page.method,
        )

        text_upper = page.text.upper() if page.text else ""

        # Try to extract sheet ID from text
        sheet.sheet_id = extract_page_number(page.text) or f"P-{page.page:03d}"

        # Try to extract title (first substantial line after sheet ID)
        sheet.title = _extract_title(page.text)

        # ── Pass 1: Sheet prefix ─────────────────────
        result = _classify_by_prefix(sheet.sheet_id)
        if result:
            sheet.discipline_code = result[0]
            sheet.discipline_name = result[1]
            sheet.csi_divisions = result[2]
            sheet.confidence = 0.95
            sheet.method = "prefix"
            classified.append(sheet)
            continue

        # ── Pass 2: Title block keywords ─────────────
        result = _classify_by_keywords(text_upper)
        if result:
            sheet.discipline_code = result[0]
            sheet.discipline_name = result[1]
            sheet.confidence = 0.80
            sheet.method = "keyword"
            classified.append(sheet)
            continue

        # ── Pass 3: Content signals ──────────────────
        result = _classify_by_content(text_upper)
        if result:
            sheet.discipline_code = result[0]
            sheet.discipline_name = result[1]
            sheet.confidence = result[2]
            sheet.method = "content"
            classified.append(sheet)
            continue

        # Fallback
        sheet.method = "fallback"
        sheet.confidence = 0.0
        classified.append(sheet)

    _log_summary(classified)
    return classified


def classify_single(page: PageResult) -> ClassifiedSheet:
    """Classify a single page."""
    return classify_sheets([page])[0]


# ── Pass 1: Prefix matching ──────────────────────────────

def _classify_by_prefix(sheet_id: str) -> Optional[tuple[str, str, list[str]]]:
    """Match sheet ID against known discipline prefixes."""
    if not sheet_id:
        return None

    for pattern, code, name, divisions in SHEET_PREFIX_PATTERNS:
        if re.match(pattern, sheet_id, re.IGNORECASE):
            return (code, name, divisions)

    return None


# ── Pass 2: Title block keyword matching ─────────────────

def _classify_by_keywords(text_upper: str) -> Optional[tuple[str, str]]:
    """Scan text for title block keywords."""
    # Check first ~500 chars (title block area) and full text
    search_zones = [text_upper[:500], text_upper]

    for zone in search_zones:
        for keyword, discipline_code in TITLE_BLOCK_KEYWORDS.items():
            if keyword in zone:
                # Map code to name
                name = _CODE_TO_NAME.get(discipline_code, discipline_code)
                return (discipline_code, name)

    return None


# ── Pass 3: Content signal scoring ───────────────────────

def _classify_by_content(text_upper: str) -> Optional[tuple[str, str, float]]:
    """Score text against discipline signal keywords."""
    if not text_upper or len(text_upper) < 50:
        return None

    scores: dict[str, float] = {}
    for discipline, signals in _CONTENT_SIGNALS.items():
        score = 0.0
        for keyword, weight in signals:
            if keyword in text_upper:
                score += weight
        if score > 0:
            scores[discipline] = score

    if not scores:
        return None

    best = max(scores, key=scores.get)
    best_score = scores[best]
    total = sum(scores.values())

    # Confidence based on how dominant the top discipline is
    confidence = min(0.85, (best_score / max(total, 1)) * 0.85)
    name = _CODE_TO_NAME.get(best, best)

    return (best, name, confidence)


# ── Title extraction ──────────────────────────────────────

def _extract_title(text: str) -> str:
    """Try to pull the sheet title from text content."""
    if not text:
        return ""

    lines = text.strip().split("\n")
    # Look for lines that look like titles (all caps, reasonable length)
    for line in lines[:20]:
        clean = line.strip()
        if 10 < len(clean) < 80 and clean.upper() == clean and not clean.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            # Skip lines that are just dimensions or coordinates
            if not re.match(r"^[\d\s'\"-/x.]+$", clean):
                return clean

    return ""


# ── Helpers ────────────────────────────────────────────────

_CODE_TO_NAME = {
    "GEN":  "General",
    "CIV":  "Civil / Site",
    "ARCH": "Architectural",
    "STR":  "Structural",
    "MECH": "Mechanical / HVAC",
    "PLMB": "Plumbing",
    "ELEC": "Electrical",
    "FP":   "Fire Protection",
    "FA":   "Fire Alarm",
    "TECH": "Technology",
    "FS":   "Food Service",
    "CONV": "Conveying",
    "UNK":  "Unknown",
}


def _log_summary(sheets: list[ClassifiedSheet]):
    """Log classification results."""
    by_disc: dict[str, int] = {}
    by_method: dict[str, int] = {}
    for s in sheets:
        by_disc[s.discipline_code] = by_disc.get(s.discipline_code, 0) + 1
        by_method[s.method] = by_method.get(s.method, 0) + 1

    log.info(
        "Classified %d sheets — disciplines: %s — methods: %s",
        len(sheets),
        {k: v for k, v in sorted(by_disc.items(), key=lambda x: -x[1])},
        by_method,
    )
