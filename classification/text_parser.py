"""
Text parser — tokenize raw PDF text into structured entities.

Takes raw text from a drawing sheet and identifies:
  - Spec section references (03 30 00, Section 07 50 00)
  - General notes and keynotes
  - Detail/section callouts (1/A-501, A/S-201)
  - Equipment tags (AHU-1, RTU-2, MDP, LP-1A)
  - Grid line references (grid A, line 3)
  - Room names and numbers
  - Door/window marks (D-101, W-201)
  - Drawing cross-references (SEE A-301, REF S-201)
  - Code references (IBC 2021, NFPA 13, NEC 2020)

Built for commercial construction — no residential patterns.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ParsedToken:
    token_type: str    # "spec_ref", "note", "callout", "equipment", "grid", "room", "door", "window", "drawing_ref", "code_ref", "keynote"
    raw: str           # Original text
    value: str         # Cleaned/normalized value
    context: str = ""  # Surrounding text for disambiguation
    line_num: int = 0


@dataclass
class ParsedSheet:
    """All tokens extracted from a single sheet."""
    spec_refs: list[ParsedToken] = field(default_factory=list)
    notes: list[ParsedToken] = field(default_factory=list)
    callouts: list[ParsedToken] = field(default_factory=list)
    equipment_tags: list[ParsedToken] = field(default_factory=list)
    grid_refs: list[ParsedToken] = field(default_factory=list)
    room_refs: list[ParsedToken] = field(default_factory=list)
    door_marks: list[ParsedToken] = field(default_factory=list)
    window_marks: list[ParsedToken] = field(default_factory=list)
    drawing_refs: list[ParsedToken] = field(default_factory=list)
    code_refs: list[ParsedToken] = field(default_factory=list)
    keynotes: list[ParsedToken] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(len(getattr(self, f)) for f in self.__dataclass_fields__)

    def to_dict(self) -> dict:
        return {
            "spec_refs": [t.value for t in self.spec_refs],
            "notes": [t.raw for t in self.notes],
            "callouts": [t.value for t in self.callouts],
            "equipment_tags": [t.value for t in self.equipment_tags],
            "grid_refs": [t.value for t in self.grid_refs],
            "room_refs": [t.value for t in self.room_refs],
            "door_marks": [t.value for t in self.door_marks],
            "window_marks": [t.value for t in self.window_marks],
            "drawing_refs": [t.value for t in self.drawing_refs],
            "code_refs": [t.value for t in self.code_refs],
            "keynotes": [t.value for t in self.keynotes],
            "total": self.total_tokens,
        }


# ── Spec section references ────────────────────────────────
# "SECTION 03 30 00", "03 30 00", "SEC. 07 50 00", "SPEC SEC 26 24 16"
_SPEC_REF = re.compile(
    r"""(?:SECTION|SEC\.?|SPEC(?:\s*SEC)?\.?\s*)?\s*"""
    r"""(\d{2})\s+(\d{2})\s+(\d{2})""",
    re.IGNORECASE | re.VERBOSE
)

# ── Detail / section callouts ──────────────────────────────
# "1/A-501", "A/S-201", "3/A501", "DET 5/S-301"
_CALLOUT = re.compile(
    r"""(?:DET(?:AIL)?\.?\s*|SEC(?:TION)?\.?\s*)?"""
    r"""(\w{1,3})\s*/\s*([A-Z]{1,3}[-\s]?\d{1,4}(?:\.\d{1,2})?)""",
    re.IGNORECASE | re.VERBOSE
)

# ── Drawing cross-references ──────────────────────────────
# "SEE A-301", "REF S-201", "SEE SHEET M-001", "REFER TO E-101"
_DRAWING_REF = re.compile(
    r"""(?:SEE|REF(?:ER)?\s*(?:TO)?|REFER\s*TO)\s+"""
    r"""(?:SHEET\s+|DWG\.?\s+)?"""
    r"""([A-Z]{1,3}[-\s]?\d{1,4}(?:\.\d{1,2})?)""",
    re.IGNORECASE | re.VERBOSE
)

# ── Equipment tags (commercial) ────────────────────────────
# AHU-1, RTU-2, FCU-3A, MDP, LP-1A, PP-2, CUH-4, VAV-201, EF-1
_EQUIPMENT = re.compile(
    r"""\b(AHU|RTU|FCU|MAU|ERU|VRF|WSHP|CUH|UH|EF|SF|RF|"""
    r"""MDP|SDP|MSB|LP|DP|PP|MCC|ATS|GEN|UPS|XFMR|"""
    r"""VAV|FPB|CAV|HRU|ERV|CU|CT|"""
    r"""FEC|FACP|"""
    r"""HWH|WH|EWC|BFP|PRV|CP|SP|"""
    r"""CH|B|P|FP|JP)"""
    r"""[-\s]?(\d{1,4}[A-Z]?(?:[-]\d{1,2}[A-Z]?)?)\b""",
    re.VERBOSE
)

# ── Room names and numbers ─────────────────────────────────
# "ROOM 101", "RM 201A", "CORRIDOR 104", "LOBBY", "MECH. RM."
_ROOM = re.compile(
    r"""\b(?:ROOM|RM\.?|SPACE)\s+(\d{1,5}[A-Z]?)\b""",
    re.IGNORECASE | re.VERBOSE
)

# ── Door marks ─────────────────────────────────────────────
# D-101, DR-201, DOOR 103
_DOOR = re.compile(
    r"""\b(?:D|DR|DOOR)[-\s]?(\d{1,5}[A-Z]?)\b""",
    re.IGNORECASE | re.VERBOSE
)

# ── Window marks ───────────────────────────────────────────
# W-101, WIN-201, WINDOW TYPE A
_WINDOW = re.compile(
    r"""\b(?:W|WIN|WINDOW)[-\s]?(\d{1,5}[A-Z]?|TYPE\s+[A-Z])\b""",
    re.IGNORECASE | re.VERBOSE
)

# ── Grid line references ──────────────────────────────────
# "GRID A", "GRID LINE 3", "@ GRID B.2", "BETWEEN GRIDS 1 AND 5"
_GRID = re.compile(
    r"""\bGRID(?:\s*LINE)?\s+([A-Z0-9](?:\.\d)?)\b""",
    re.IGNORECASE | re.VERBOSE
)

# ── Code references ────────────────────────────────────────
# IBC 2021, NFPA 13, NEC 2020, ADA, ASCE 7-22, ACI 318-19
_CODE_REF = re.compile(
    r"""\b(IBC|IRC|NFPA|NEC|ADA|ASCE|ACI|AISC|AWS|ASTM|UL|FM|ASHRAE|ICC|ANSI|OSHA|EPA)"""
    r"""\s*([\d]+(?:[-.][\d]+)?(?:\s*[-]\s*\d{2,4})?)\b""",
    re.VERBOSE
)

# ── Keynotes ───────────────────────────────────────────────
# Numbered keynotes: "1. PROVIDE...", "KN-01:", "KEYNOTE 3:"
_KEYNOTE_NUMBERED = re.compile(
    r"""(?:^|\n)\s*(?:KN[-\s]?)?(\d{1,3})[.):\s]+\s*([A-Z].{10,})""",
    re.MULTILINE | re.VERBOSE
)

# ── General notes ──────────────────────────────────────────
_NOTE_HEADER = re.compile(
    r"""(?:^|\n)\s*(?:GENERAL\s+)?NOTES?\s*:?\s*$""",
    re.IGNORECASE | re.MULTILINE
)
_NOTE_ITEM = re.compile(
    r"""(?:^|\n)\s*(\d{1,3})[.)]\s+(.+)""",
    re.MULTILINE
)


def parse_sheet_text(text: str) -> ParsedSheet:
    """
    Parse all entities from a single sheet's text content.
    """
    result = ParsedSheet()
    if not text or len(text) < 10:
        return result

    # Spec references
    for m in _SPEC_REF.finditer(text):
        code = f"{m.group(1)} {m.group(2)} {m.group(3)}"
        result.spec_refs.append(ParsedToken(
            token_type="spec_ref", raw=m.group(0).strip(), value=code,
        ))

    # Detail/section callouts
    for m in _CALLOUT.finditer(text):
        detail = m.group(1)
        sheet = m.group(2).upper().replace(" ", "")
        result.callouts.append(ParsedToken(
            token_type="callout", raw=m.group(0).strip(), value=f"{detail}/{sheet}",
        ))

    # Drawing cross-references
    for m in _DRAWING_REF.finditer(text):
        ref = m.group(1).upper().strip()
        result.drawing_refs.append(ParsedToken(
            token_type="drawing_ref", raw=m.group(0).strip(), value=ref,
        ))

    # Equipment tags
    for m in _EQUIPMENT.finditer(text):
        tag = f"{m.group(1)}-{m.group(2)}".upper()
        result.equipment_tags.append(ParsedToken(
            token_type="equipment", raw=m.group(0).strip(), value=tag,
        ))

    # Room references
    for m in _ROOM.finditer(text):
        result.room_refs.append(ParsedToken(
            token_type="room", raw=m.group(0).strip(), value=m.group(1).upper(),
        ))

    # Door marks
    for m in _DOOR.finditer(text):
        result.door_marks.append(ParsedToken(
            token_type="door", raw=m.group(0).strip(), value=f"D-{m.group(1).upper()}",
        ))

    # Window marks
    for m in _WINDOW.finditer(text):
        result.window_marks.append(ParsedToken(
            token_type="window", raw=m.group(0).strip(), value=f"W-{m.group(1).upper()}",
        ))

    # Grid references
    for m in _GRID.finditer(text):
        result.grid_refs.append(ParsedToken(
            token_type="grid", raw=m.group(0).strip(), value=m.group(1).upper(),
        ))

    # Code references
    for m in _CODE_REF.finditer(text):
        code_name = m.group(1).upper()
        code_ver = m.group(2).strip()
        result.code_refs.append(ParsedToken(
            token_type="code_ref", raw=m.group(0).strip(), value=f"{code_name} {code_ver}",
        ))

    # Keynotes
    for m in _KEYNOTE_NUMBERED.finditer(text):
        num = m.group(1)
        content = m.group(2).strip()
        result.keynotes.append(ParsedToken(
            token_type="keynote", raw=m.group(0).strip(), value=f"KN-{num}: {content[:120]}",
        ))

    # General notes
    for m in _NOTE_ITEM.finditer(text):
        content = m.group(2).strip()
        if len(content) > 15:  # filter out short junk
            result.notes.append(ParsedToken(
                token_type="note", raw=content, value=content[:200],
            ))

    # Deduplicate
    _dedup(result)

    return result


def _dedup(sheet: ParsedSheet):
    """Remove duplicate tokens within each category."""
    for field_name in sheet.__dataclass_fields__:
        tokens = getattr(sheet, field_name)
        if isinstance(tokens, list):
            seen = set()
            unique = []
            for t in tokens:
                if t.value not in seen:
                    seen.add(t.value)
                    unique.append(t)
            setattr(sheet, field_name, unique)
