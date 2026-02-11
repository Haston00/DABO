"""
Common conflict patterns in commercial construction.

This is the knowledge base that tells the conflict detector what to look for
beyond the formal rules. Each pattern describes a common coordination issue
with the disciplines involved and typical resolution.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConflictPattern:
    pattern_id: str
    name: str
    description: str
    disciplines: list[str]
    typical_resolution: str
    frequency: str          # "common", "occasional", "rare"
    severity: str           # "CRITICAL", "MAJOR", "MINOR"


PATTERNS: list[ConflictPattern] = [
    # ── Structural vs MEP ─────────────────────────────────
    ConflictPattern(
        "PAT-001", "Beam web penetration too large",
        "MEP penetration through structural beam web exceeds 1/3 of beam depth or is in restricted zone.",
        ["STR", "MECH", "PLMB"],
        "Relocate penetration, add reinforcing, or resize beam. Requires structural engineer review.",
        "common", "CRITICAL"
    ),
    ConflictPattern(
        "PAT-002", "Slab depression not coordinated",
        "Architectural finish requiring slab depression (tile, terrazzo) not shown on structural drawings.",
        ["ARCH", "STR"],
        "Add slab depression to structural drawings. Verify rebar coverage and edge conditions.",
        "common", "MAJOR"
    ),
    ConflictPattern(
        "PAT-003", "Roof drain vs structure",
        "Roof drain location conflicts with structural beam or joist below, preventing proper slope.",
        ["PLMB", "STR"],
        "Relocate drain to clear span area or add framing opening with header.",
        "occasional", "MAJOR"
    ),

    # ── MEP Coordination ──────────────────────────────────
    ConflictPattern(
        "PAT-004", "Ceiling plenum space insufficient",
        "Combined depth of structure, ductwork, piping, sprinkler mains, and lighting exceeds available plenum.",
        ["MECH", "PLMB", "ELEC", "FP", "STR", "ARCH"],
        "Resequence MEP routing priorities. May need to lower ceiling or raise structure.",
        "common", "CRITICAL"
    ),
    ConflictPattern(
        "PAT-005", "Mechanical room too small",
        "Equipment clearance requirements, service access, and code clearances exceed room dimensions.",
        ["MECH", "ARCH"],
        "Enlarge room, reconfigure equipment layout, or select different equipment.",
        "common", "MAJOR"
    ),
    ConflictPattern(
        "PAT-006", "Electrical room clearance",
        "NEC working clearance in front of panels/switchgear not maintained due to room size or obstructions.",
        ["ELEC", "ARCH"],
        "Enlarge room or relocate equipment. NEC requires 36\" min clearance at 277V, 48\" at 480V.",
        "common", "CRITICAL"
    ),

    # ── Fire Protection ───────────────────────────────────
    ConflictPattern(
        "PAT-007", "Sprinkler head in wrong ceiling type",
        "Concealed head specified where there's no hard ceiling, or pendent head where ceiling is too high.",
        ["FP", "ARCH"],
        "Match head type to ceiling type. Concealed needs hard ceiling. Pendent max 12' for standard.",
        "occasional", "MAJOR"
    ),
    ConflictPattern(
        "PAT-008", "Sprinkler branch vs light fixture",
        "Sprinkler branch line routing conflicts with recessed light fixture locations.",
        ["FP", "ELEC", "ARCH"],
        "Coordinate head layout with ceiling reflected plan. Adjust head or fixture locations.",
        "common", "MINOR"
    ),

    # ── Envelope / Waterproofing ──────────────────────────
    ConflictPattern(
        "PAT-009", "Through-wall flashing not detailed",
        "Masonry veneer or curtain wall lacks through-wall flashing detail at shelf angles and penetrations.",
        ["ARCH"],
        "Add flashing details. Coordinate with structural shelf angle locations.",
        "occasional", "MAJOR"
    ),
    ConflictPattern(
        "PAT-010", "Roof penetration waterproofing",
        "MEP equipment curb or pipe penetration through roof membrane lacks proper detail.",
        ["MECH", "ELEC", "ARCH"],
        "Add roof penetration details showing curb height, flashing, and counter-flashing.",
        "common", "MAJOR"
    ),

    # ── Code Compliance ───────────────────────────────────
    ConflictPattern(
        "PAT-011", "Accessible route not continuous",
        "ADA accessible route is interrupted by steps, thresholds, or missing ramps.",
        ["ARCH"],
        "Verify continuous accessible route from parking through all public spaces. Add ramps as needed.",
        "occasional", "CRITICAL"
    ),
    ConflictPattern(
        "PAT-012", "Exit sign visibility",
        "Exit signs not visible from required locations or not on emergency power.",
        ["ELEC", "ARCH"],
        "Add exit signs per IBC. Verify all on emergency circuit per NEC.",
        "occasional", "MAJOR"
    ),

    # ── Site / Civil ──────────────────────────────────────
    ConflictPattern(
        "PAT-013", "Utility crossing conflicts",
        "Underground utility crossings not properly separated or sequenced (storm, sanitary, water, gas, electric).",
        ["CIV", "PLMB", "ELEC"],
        "Verify horizontal and vertical separation per local utility standards. May need redesign.",
        "occasional", "CRITICAL"
    ),
    ConflictPattern(
        "PAT-014", "Loading dock clearance",
        "Overhead door height, dock leveler travel, and truck bed height don't work together.",
        ["ARCH", "STR"],
        "Verify 14' min clear for standard trailers. Check leveler pit vs slab depression.",
        "occasional", "MAJOR"
    ),
]


def get_patterns_for_disciplines(disc_codes: set[str]) -> list[ConflictPattern]:
    """Return patterns that involve the given disciplines."""
    return [
        p for p in PATTERNS
        if set(p.disciplines) & disc_codes
    ]
