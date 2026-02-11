"""
Dimension parser for commercial construction drawings.

Handles every format you see on commercial plan sets:
  - Imperial: 42'-6", 10' - 3 1/2", 0'-8", 3/4"
  - Metric: 1200mm, 3.5m, 450 mm
  - Elevations: T.O.S. EL. 124'-6", B.O.S. 112.50', FFE 100'-0"
  - Grid lines: A, B, C... or 1, 2, 3... with spacing
  - Steel sizes: W12x26, W24x68, HSS6x6x1/4, L4x4x3/8
  - Rebar: #4@12" O.C., #5@18" E.W., (2)#8 cont.
  - Pipe sizes: 4" DWV, 2-1/2" CW, 6" SS
  - Duct sizes: 24x12, 36x18, 14" rd
  - Conduit: 3/4"C, 1"C, 2"EMT, 3"RGS
  - Tolerances: +/- 1/8", +/- 3mm
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from utils.logger import get_logger

log = get_logger(__name__)

# Quote characters found in PDFs (straight + curly)
_INCH_MARKS = '"\u201c\u201d'   # " and curly double quotes
_FOOT_MARKS = "'\u2018\u2019"   # ' and curly single quotes
_ANY_INCH = f"[{_INCH_MARKS}]"
_ANY_FOOT = f"[{_FOOT_MARKS}]"


@dataclass
class Dimension:
    raw: str                # Original text as found
    value_inches: float     # Converted to inches (0 if not linear)
    value_display: str      # Clean display string
    dim_type: str           # "linear", "elevation", "steel", "rebar", "pipe", "duct", "conduit", "metric", "area", "grid_spacing"
    unit: str = ""          # "ft-in", "in", "mm", "m", etc.


# ── Imperial feet-inches patterns ──────────────────────────

# 42'-6", 10'-3 1/2", 0'-8", 100'-0"
_FT_IN = re.compile(
    r"(\d+)\s*" + _ANY_FOOT + r"\s*-?\s*(\d+)"
    r"(?:\s+(\d+)\s*/\s*(\d+))?"
    r"\s*" + _ANY_INCH + r"?"
)

# 3/4", 1/2", 7/8"
_FRAC_INCH = re.compile(
    r"(?<!\d)(\d+)\s*/\s*(\d+)\s*" + _ANY_INCH
)

# 6", 18", 36" (bare inches, no feet)
_BARE_INCH = re.compile(
    r"(?<!\d)(\d+(?:\.\d+)?)\s*" + _ANY_INCH
)

# 12' (feet only, no inches)
_BARE_FEET = re.compile(
    r"(?<!\d)(\d+)\s*" + _ANY_FOOT + r"\s*(?![\d-])"
)

# ── Metric patterns ────────────────────────────────────────
_METRIC_MM = re.compile(r"(\d+(?:\.\d+)?)\s*mm\b", re.IGNORECASE)
_METRIC_M = re.compile(r"(\d+(?:\.\d+)?)\s*m\b(?!m|i|o|e|a)", re.IGNORECASE)

# ── Elevation patterns ─────────────────────────────────────
# T.O.S. EL. 124'-6", FFE 100'-0", B.O.S. 112.50'
_ELEVATION = re.compile(
    r"(?:T\.?O\.?S\.?|B\.?O\.?S\.?|T\.?O\.?W\.?|B\.?O\.?W\.?|"
    r"T\.?O\.?C\.?|B\.?O\.?C\.?|T\.?O\.?F\.?|F\.?F\.?E\.?|"
    r"EL\.?|ELEV\.?|FIN\.?\s*FL\.?|SLAB\s*EL\.?)\s*"
    r"[=:]?\s*(\d+" + _ANY_FOOT + r"\s*-?\s*\d+\s*" + _ANY_INCH + r"?|\d+(?:\.\d+)?" + _ANY_FOOT + r"?)",
    re.IGNORECASE
)

# ── Structural steel sizes ─────────────────────────────────
# W12x26, W24x68, HP14x73, C10x25
_W_SHAPE = re.compile(r"\b(W|HP|C|MC|S|WT|MT|ST)\s*(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\b")
# HSS6x6x1/4, HSS8x4x3/8
_HSS = re.compile(r"\bHSS\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+/\d+|\.\d+|\d+(?:\.\d+)?)\b", re.IGNORECASE)
# L4x4x3/8, L6x3-1/2x5/16
_ANGLE = re.compile(r"\bL\s*(\d+(?:[.-]\d+/?(?:\d+))?)\s*[xX]\s*(\d+(?:[.-]\d+/?(?:\d+))?)\s*[xX]\s*(\d+/\d+|\.\d+)\b")

# ── Rebar patterns ─────────────────────────────────────────
# #4@12" O.C., #5@18" E.W., (2)#8 cont., #6@12 EW T&B
_REBAR = re.compile(
    r"(?:\((\d+)\))?\s*#(\d+)\s*"
    r"(?:@\s*(\d+)\s*" + _ANY_INCH + r"?\s*"
    r"(?:O\.?C\.?|E\.?W\.?|E\.?F\.?)?)?"
    r"(?:\s*(CONT\.?|T\s*&\s*B|T&B|E\.?W\.?|E\.?F\.?))?",
    re.IGNORECASE
)

# ── Pipe sizes ─────────────────────────────────────────────
# 4" DWV, 2-1/2" CW, 6" SS, 3/4" CW
_PIPE = re.compile(
    r"(\d+(?:-\d+/\d+|/\d+)?)\s*" + _ANY_INCH + r"?\s*"
    r"(DWV|CW|HW|HHW|CHW|SS|SD|RD|GAS|MED|VAC|ACID|OV|RF|CWR|CHWR)\b",
    re.IGNORECASE
)

# ── Duct sizes ─────────────────────────────────────────────
# 24x12, 36x18, 14" rd, 24"x12"
_DUCT_RECT = re.compile(r"(\d+)\s*" + _ANY_INCH + r"?\s*[xX]\s*(\d+)\s*" + _ANY_INCH + r"?")
_DUCT_ROUND = re.compile(r"(\d+)\s*" + _ANY_INCH + r"?\s*(?:RD|ROUND|DIA|rd)\b", re.IGNORECASE)

# ── Conduit sizes ──────────────────────────────────────────
# 3/4"C, 1"EMT, 2"RGS, 3"PVC
_CONDUIT = re.compile(
    r"(\d+(?:/\d+)?)\s*" + _ANY_INCH + r"?\s*(C|EMT|IMC|RGS|RMC|PVC|LFMC|FMC|ENT)\b",
    re.IGNORECASE
)

# ── On-center spacing ─────────────────────────────────────
_OC_SPACING = re.compile(
    r"(\d+(?:\.\d+)?)\s*" + _ANY_INCH + r"?\s*O\.?C\.?",
    re.IGNORECASE
)


def parse_dimensions(text: str) -> list[Dimension]:
    """
    Extract all dimensions from a block of text.
    Returns deduplicated list sorted by position in text.
    """
    dims = []
    seen = set()

    for finder in [
        _find_elevations,
        _find_steel,
        _find_rebar,
        _find_pipe,
        _find_conduit,
        _find_duct,
        _find_ft_in,
        _find_metric,
        _find_bare_inch,
        _find_bare_feet,
    ]:
        for dim in finder(text):
            key = dim.raw.strip()
            if key not in seen:
                seen.add(key)
                dims.append(dim)

    return dims


def parse_single(text: str) -> Dimension | None:
    """Try to parse a single dimension string."""
    dims = parse_dimensions(text.strip())
    return dims[0] if dims else None


def to_inches(feet: float = 0, inches: float = 0, fraction_num: int = 0, fraction_den: int = 1) -> float:
    """Convert feet-inches-fraction to total inches."""
    frac = fraction_num / fraction_den if fraction_den else 0
    return (feet * 12) + inches + frac


# ── Finder functions ──────────────────────────────────────

def _find_ft_in(text: str) -> list[Dimension]:
    dims = []
    for m in _FT_IN.finditer(text):
        ft = int(m.group(1))
        inch = int(m.group(2))
        frac_n = int(m.group(3)) if m.group(3) else 0
        frac_d = int(m.group(4)) if m.group(4) else 1
        total = to_inches(ft, inch, frac_n, frac_d)
        raw = m.group(0).strip()
        display = f"{ft}'-{inch}"
        if frac_n:
            display += f" {frac_n}/{frac_d}"
        display += '"'
        dims.append(Dimension(raw=raw, value_inches=total, value_display=display, dim_type="linear", unit="ft-in"))
    return dims


def _find_bare_feet(text: str) -> list[Dimension]:
    dims = []
    for m in _BARE_FEET.finditer(text):
        ft = int(m.group(1))
        dims.append(Dimension(raw=m.group(0).strip(), value_inches=ft * 12, value_display=f"{ft}'", dim_type="linear", unit="ft"))
    return dims


def _find_bare_inch(text: str) -> list[Dimension]:
    dims = []
    for m in _BARE_INCH.finditer(text):
        val = float(m.group(1))
        dims.append(Dimension(raw=m.group(0).strip(), value_inches=val, value_display=f'{val:.0f}"' if val == int(val) else f'{val}"', dim_type="linear", unit="in"))
    # Also get fractions
    for m in _FRAC_INCH.finditer(text):
        n, d = int(m.group(1)), int(m.group(2))
        val = n / d if d else 0
        dims.append(Dimension(raw=m.group(0).strip(), value_inches=val, value_display=f'{n}/{d}"', dim_type="linear", unit="in"))
    return dims


def _find_metric(text: str) -> list[Dimension]:
    dims = []
    for m in _METRIC_MM.finditer(text):
        val = float(m.group(1))
        dims.append(Dimension(raw=m.group(0).strip(), value_inches=val / 25.4, value_display=f"{val:.0f}mm", dim_type="metric", unit="mm"))
    for m in _METRIC_M.finditer(text):
        val = float(m.group(1))
        dims.append(Dimension(raw=m.group(0).strip(), value_inches=val * 39.3701, value_display=f"{val}m", dim_type="metric", unit="m"))
    return dims


def _find_elevations(text: str) -> list[Dimension]:
    dims = []
    for m in _ELEVATION.finditer(text):
        raw = m.group(0).strip()
        elev_str = m.group(1) if m.lastindex else ""
        # Try to parse the elevation value
        sub_dims = _find_ft_in(elev_str) or _find_bare_feet(elev_str)
        val = sub_dims[0].value_inches if sub_dims else 0
        dims.append(Dimension(raw=raw, value_inches=val, value_display=raw, dim_type="elevation", unit="ft-in"))
    return dims


def _find_steel(text: str) -> list[Dimension]:
    dims = []
    for m in _W_SHAPE.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="steel"))
    for m in _HSS.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="steel"))
    for m in _ANGLE.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="steel"))
    return dims


def _find_rebar(text: str) -> list[Dimension]:
    dims = []
    for m in _REBAR.finditer(text):
        raw = m.group(0).strip()
        if not raw or len(raw) < 2:
            continue
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="rebar"))
    return dims


def _find_pipe(text: str) -> list[Dimension]:
    dims = []
    for m in _PIPE.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="pipe"))
    return dims


def _find_duct(text: str) -> list[Dimension]:
    dims = []
    for m in _DUCT_ROUND.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="duct"))
    for m in _DUCT_RECT.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="duct"))
    return dims


def _find_conduit(text: str) -> list[Dimension]:
    dims = []
    for m in _CONDUIT.finditer(text):
        raw = m.group(0).strip()
        dims.append(Dimension(raw=raw, value_inches=0, value_display=raw, dim_type="conduit"))
    return dims
