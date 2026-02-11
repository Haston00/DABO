"""
Activity builder — generate schedule activities from project scope.

Supports three project modes:
  - new_construction: Ground-up commercial (foundations → CO)
  - renovation: Gut renovation of existing building (demo → finishes → CO)
  - tenant_improvement: Interior fit-out within existing shell (demo → finishes → punch)

Takes project parameters (type, SF, stories, scope) and generates
a standard activity list with durations and predecessor logic.
"""
from __future__ import annotations

from config.production_rates import get_duration, FIXED_DURATIONS
from scheduling.cpm_engine import Activity
from utils.logger import get_logger

log = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# TEMPLATE: NEW CONSTRUCTION
# Full ground-up commercial build
# (wbs, code, name, predecessors as (code, rel, lag), is_milestone)
# ═══════════════════════════════════════════════════════════════
_NEW_CONSTRUCTION = [
    # ── Preconstruction ───────────────────────────────────
    ("01", "A0010", "Notice to Proceed",            [],                                        True),
    ("01", "A0020", "Permits & Approvals",           [("A0010", "FS", 0)],                     True),
    ("01", "A0030", "Shop Drawing Submittals",       [("A0010", "FS", 0)],                     False),
    ("01", "A0040", "Material Procurement",          [("A0030", "FS", 5)],                     False),

    # ── Sitework ──────────────────────────────────────────
    ("02", "A0100", "Mobilization",                  [("A0020", "FS", 0)],                     False),
    ("02", "A0110", "Earthwork & Grading",           [("A0100", "FS", 0)],                     False),
    ("02", "A0120", "Underground Utilities",         [("A0110", "FS", 0)],                     False),

    # ── Foundations ────────────────────────────────────────
    ("03", "A0200", "Foundations",                   [("A0120", "FS", 0)],                     False),
    ("03", "A0210", "Slab on Grade",                 [("A0200", "FS", 0)],                     False),

    # ── Structure ─────────────────────────────────────────
    ("05", "A0300", "Structural Steel Erection",     [("A0200", "FS", 0), ("A0040", "FS", 0)], False),
    ("05", "A0310", "Metal Deck & Shear Studs",      [("A0300", "SS", 5)],                     False),
    ("03", "A0320", "Elevated Concrete Decks",       [("A0310", "FS", 0)],                     False),

    # ── Envelope ──────────────────────────────────────────
    ("07", "A0400", "Roofing",                       [("A0310", "FS", 5)],                     False),
    ("07", "A0410", "Exterior Wall System",          [("A0300", "SS", 10)],                    False),
    ("08", "A0420", "Windows & Storefront",          [("A0410", "SS", 10)],                    False),
    ("07", "A0430", "Waterproofing & Sealants",      [("A0410", "SS", 15)],                    False),

    # ── MEP Rough-In ──────────────────────────────────────
    ("15", "A0500", "HVAC Rough-In",                 [("A0320", "FS", 0)],                     False),
    ("15", "A0510", "Plumbing Rough-In",             [("A0210", "FS", 0)],                     False),
    ("16", "A0520", "Electrical Rough-In",           [("A0320", "FS", 0)],                     False),
    ("15", "A0530", "Fire Protection",               [("A0320", "FS", 0)],                     False),
    ("16", "A0540", "Fire Alarm Rough-In",           [("A0520", "SS", 5)],                     False),
    ("16", "A0550", "Low Voltage Rough-In",          [("A0520", "SS", 5)],                     False),

    # ── Interior Finishes ─────────────────────────────────
    ("09", "A0600", "Metal Framing & Drywall",       [("A0500", "SS", 10), ("A0520", "SS", 10)], False),
    ("08", "A0610", "Doors & Hardware",              [("A0600", "SS", 15)],                    False),
    ("09", "A0620", "Ceiling Grid & Tile",           [("A0600", "FS", 0), ("A0500", "FS", -5)], False),
    ("09", "A0630", "Flooring",                      [("A0600", "FS", 0)],                     False),
    ("09", "A0640", "Painting",                      [("A0600", "FS", 0)],                     False),
    ("10", "A0650", "Specialties & Accessories",     [("A0640", "FS", 0)],                     False),

    # ── MEP Trim ──────────────────────────────────────────
    ("15", "A0700", "HVAC Trim & Startup",           [("A0620", "FS", 0)],                     False),
    ("15", "A0710", "Plumbing Trim & Fixtures",      [("A0630", "FS", 0)],                     False),
    ("16", "A0720", "Electrical Trim & Devices",     [("A0640", "FS", 0)],                     False),
    ("16", "A0730", "Fire Alarm Trim & Test",        [("A0620", "FS", 0)],                     False),
    ("16", "A0740", "Low Voltage Trim & Test",       [("A0620", "FS", 0)],                     False),

    # ── Commissioning & Closeout ──────────────────────────
    ("01", "A0800", "Test & Balance",                [("A0700", "FS", 0)],                     False),
    ("01", "A0810", "Commissioning",                 [("A0800", "FS", 0)],                     False),
    ("01", "A0820", "Punch List",                    [("A0810", "FS", 0), ("A0710", "FS", 0), ("A0720", "FS", 0)], False),
    ("01", "A0830", "Final Inspections",             [("A0820", "FS", 0)],                     True),
    ("01", "A0840", "Certificate of Occupancy",      [("A0830", "FS", 0)],                     True),
    ("01", "A0850", "Substantial Completion",        [("A0840", "FS", 0)],                     True),
]


# ═══════════════════════════════════════════════════════════════
# TEMPLATE: RENOVATION / REMODEL
# Gut renovation of existing building — no foundations, no steel
# Demo → Abatement → Structure mods → MEP → Finishes → Closeout
# ═══════════════════════════════════════════════════════════════
_RENOVATION = [
    # ── Preconstruction ───────────────────────────────────
    ("01", "R0010", "Notice to Proceed",             [],                                        True),
    ("01", "R0020", "Permits & Approvals",           [("R0010", "FS", 0)],                     True),
    ("01", "R0030", "Shop Drawing Submittals",       [("R0010", "FS", 0)],                     False),
    ("01", "R0040", "Material Procurement",          [("R0030", "FS", 5)],                     False),
    ("01", "R0050", "Existing Conditions Survey",    [("R0010", "FS", 0)],                     False),

    # ── Mobilization & Protection ─────────────────────────
    ("02", "R0100", "Mobilization",                  [("R0020", "FS", 0)],                     False),
    ("02", "R0110", "Temp Barriers & Dust Control",  [("R0100", "FS", 0)],                     False),
    ("02", "R0120", "Tenant Protection / Phasing",   [("R0100", "FS", 0)],                     False),

    # ── Abatement & Demolition ────────────────────────────
    ("02", "R0200", "Hazmat Abatement",              [("R0110", "FS", 0)],                     False),
    ("02", "R0210", "Selective Interior Demo",       [("R0200", "FS", 0)],                     False),
    ("02", "R0220", "MEP Demo & Cap-Off",            [("R0200", "FS", 0)],                     False),
    ("02", "R0230", "Demo Debris Removal",           [("R0210", "SS", 3)],                     False),

    # ── Structural Modifications ──────────────────────────
    ("05", "R0300", "Structural Modifications",      [("R0210", "FS", 0), ("R0050", "FS", 0)], False),
    ("03", "R0310", "Concrete Repairs & Patching",   [("R0300", "FS", 0)],                     False),

    # ── Envelope Repairs (if needed) ──────────────────────
    ("07", "R0400", "Roof Repairs / Replacement",    [("R0210", "FS", 0)],                     False),
    ("07", "R0410", "Exterior Wall Repairs",         [("R0210", "FS", 0)],                     False),
    ("08", "R0420", "Window Replacement",            [("R0410", "SS", 5)],                     False),
    ("07", "R0430", "Waterproofing Repairs",         [("R0410", "SS", 10)],                    False),

    # ── MEP Rough-In ──────────────────────────────────────
    ("15", "R0500", "HVAC Rough-In",                 [("R0310", "FS", 0), ("R0220", "FS", 0)], False),
    ("15", "R0510", "Plumbing Rough-In",             [("R0220", "FS", 0)],                     False),
    ("16", "R0520", "Electrical Rough-In",           [("R0310", "FS", 0), ("R0220", "FS", 0)], False),
    ("15", "R0530", "Fire Protection",               [("R0310", "FS", 0)],                     False),
    ("16", "R0540", "Fire Alarm Rough-In",           [("R0520", "SS", 5)],                     False),
    ("16", "R0550", "Low Voltage Rough-In",          [("R0520", "SS", 5)],                     False),

    # ── Interior Finishes ─────────────────────────────────
    ("09", "R0600", "Metal Framing & Drywall",       [("R0500", "SS", 10), ("R0520", "SS", 10)], False),
    ("08", "R0610", "Doors & Hardware",              [("R0600", "SS", 15)],                    False),
    ("09", "R0620", "Ceiling Grid & Tile",           [("R0600", "FS", 0)],                     False),
    ("09", "R0630", "Flooring",                      [("R0600", "FS", 0)],                     False),
    ("09", "R0640", "Painting",                      [("R0600", "FS", 0)],                     False),
    ("10", "R0650", "Specialties & Accessories",     [("R0640", "FS", 0)],                     False),

    # ── MEP Trim ──────────────────────────────────────────
    ("15", "R0700", "HVAC Trim & Startup",           [("R0620", "FS", 0)],                     False),
    ("15", "R0710", "Plumbing Trim & Fixtures",      [("R0630", "FS", 0)],                     False),
    ("16", "R0720", "Electrical Trim & Devices",     [("R0640", "FS", 0)],                     False),
    ("16", "R0730", "Fire Alarm Trim & Test",        [("R0620", "FS", 0)],                     False),
    ("16", "R0740", "Low Voltage Trim & Test",       [("R0620", "FS", 0)],                     False),

    # ── Closeout ──────────────────────────────────────────
    ("01", "R0800", "Test & Balance",                [("R0700", "FS", 0)],                     False),
    ("01", "R0810", "Commissioning",                 [("R0800", "FS", 0)],                     False),
    ("01", "R0820", "Punch List",                    [("R0810", "FS", 0), ("R0710", "FS", 0), ("R0720", "FS", 0)], False),
    ("01", "R0830", "Final Inspections",             [("R0820", "FS", 0)],                     True),
    ("01", "R0840", "Certificate of Occupancy",      [("R0830", "FS", 0)],                     True),
    ("01", "R0850", "Substantial Completion",        [("R0840", "FS", 0)],                     True),
]


# ═══════════════════════════════════════════════════════════════
# TEMPLATE: TENANT IMPROVEMENT (TI)
# Interior fit-out within existing shell — no exterior, no structure
# Demo → MEP → Finishes → Punch
# ═══════════════════════════════════════════════════════════════
_TENANT_IMPROVEMENT = [
    # ── Preconstruction ───────────────────────────────────
    ("01", "T0010", "Notice to Proceed",             [],                                        True),
    ("01", "T0020", "Permits & Approvals",           [("T0010", "FS", 0)],                     True),
    ("01", "T0030", "Shop Drawing Submittals",       [("T0010", "FS", 0)],                     False),
    ("01", "T0040", "Material Procurement",          [("T0030", "FS", 5)],                     False),

    # ── Mobilization & Demo ───────────────────────────────
    ("02", "T0100", "Mobilization & Protection",     [("T0020", "FS", 0)],                     False),
    ("02", "T0110", "Selective Demo",                [("T0100", "FS", 0)],                     False),
    ("02", "T0120", "Demo Debris Removal",           [("T0110", "SS", 2)],                     False),

    # ── MEP Rough-In ──────────────────────────────────────
    ("15", "T0200", "HVAC Rough-In",                 [("T0110", "FS", 0)],                     False),
    ("15", "T0210", "Plumbing Rough-In",             [("T0110", "FS", 0)],                     False),
    ("16", "T0220", "Electrical Rough-In",           [("T0110", "FS", 0)],                     False),
    ("15", "T0230", "Fire Protection Mods",          [("T0110", "FS", 0)],                     False),
    ("16", "T0240", "Fire Alarm Rough-In",           [("T0220", "SS", 3)],                     False),
    ("16", "T0250", "Low Voltage Rough-In",          [("T0220", "SS", 3)],                     False),

    # ── Interior Finishes ─────────────────────────────────
    ("09", "T0300", "Metal Framing & Drywall",       [("T0200", "SS", 5), ("T0220", "SS", 5)], False),
    ("08", "T0310", "Doors & Hardware",              [("T0300", "SS", 10)],                    False),
    ("09", "T0320", "Ceiling Grid & Tile",           [("T0300", "FS", 0)],                     False),
    ("09", "T0330", "Flooring",                      [("T0300", "FS", 0)],                     False),
    ("09", "T0340", "Painting",                      [("T0300", "FS", 0)],                     False),
    ("10", "T0350", "Millwork & Casework",           [("T0340", "FS", 0)],                     False),
    ("10", "T0360", "Specialties & Accessories",     [("T0340", "FS", 0)],                     False),

    # ── MEP Trim ──────────────────────────────────────────
    ("15", "T0400", "HVAC Trim & Startup",           [("T0320", "FS", 0)],                     False),
    ("15", "T0410", "Plumbing Trim & Fixtures",      [("T0330", "FS", 0)],                     False),
    ("16", "T0420", "Electrical Trim & Devices",     [("T0340", "FS", 0)],                     False),
    ("16", "T0430", "Fire Alarm Trim & Test",        [("T0320", "FS", 0)],                     False),
    ("16", "T0440", "Low Voltage Trim & Test",       [("T0320", "FS", 0)],                     False),

    # ── Closeout ──────────────────────────────────────────
    ("01", "T0500", "Test & Balance",                [("T0400", "FS", 0)],                     False),
    ("01", "T0510", "Punch List",                    [("T0500", "FS", 0), ("T0410", "FS", 0), ("T0420", "FS", 0)], False),
    ("01", "T0520", "Final Inspection",              [("T0510", "FS", 0)],                     True),
    ("01", "T0530", "Tenant Move-In Ready",          [("T0520", "FS", 0)],                     True),
]


# ═══════════════════════════════════════════════════════════════
# Activity code → production rate code mapping
# (shared across all templates)
# ═══════════════════════════════════════════════════════════════
_RATE_MAP = {
    # New construction
    "A0100": "SITE_MOBILIZATION", "A0110": "EARTHWORK", "A0120": "UNDERGROUND_UTIL",
    "A0200": "FOUNDATIONS", "A0210": "SLAB_ON_GRADE",
    "A0300": "STRUCTURAL_STEEL", "A0310": "METAL_DECK", "A0320": "CONCRETE_STRUCTURE",
    "A0400": "ROOFING", "A0410": "EXTERIOR_WALL", "A0420": "WINDOWS_STOREFRONT", "A0430": "WATERPROOFING",
    "A0500": "HVAC_ROUGH", "A0510": "PLUMBING_ROUGH", "A0520": "ELECTRICAL_ROUGH",
    "A0530": "FIRE_PROTECTION", "A0540": "FIRE_ALARM", "A0550": "LOW_VOLTAGE",
    "A0600": "FRAMING_DRYWALL", "A0610": "DOORS_HARDWARE", "A0620": "CEILING",
    "A0630": "FLOORING", "A0640": "PAINTING", "A0650": "SPECIALTIES",
    "A0700": "HVAC_TRIM", "A0710": "PLUMBING_TRIM", "A0720": "ELECTRICAL_TRIM",
    "A0730": "FIRE_ALARM", "A0740": "LOW_VOLTAGE",
    "A0800": "TAB", "A0810": "COMMISSIONING", "A0820": "PUNCH_LIST",
    "A0830": "FINAL_INSPECTION", "A0840": "CO_PROCESS",

    # Renovation (same rate codes, different activity IDs)
    "R0100": "SITE_MOBILIZATION",
    "R0110": "TEMP_BARRIERS", "R0120": "TENANT_PROTECTION",
    "R0200": "HAZMAT_ABATEMENT", "R0210": "SELECTIVE_DEMO", "R0220": "MEP_DEMO", "R0230": "DEMO_REMOVAL",
    "R0300": "STRUCTURAL_MODS", "R0310": "CONCRETE_REPAIRS",
    "R0400": "ROOFING", "R0410": "EXTERIOR_WALL", "R0420": "WINDOWS_STOREFRONT", "R0430": "WATERPROOFING",
    "R0500": "HVAC_ROUGH", "R0510": "PLUMBING_ROUGH", "R0520": "ELECTRICAL_ROUGH",
    "R0530": "FIRE_PROTECTION", "R0540": "FIRE_ALARM", "R0550": "LOW_VOLTAGE",
    "R0600": "FRAMING_DRYWALL", "R0610": "DOORS_HARDWARE", "R0620": "CEILING",
    "R0630": "FLOORING", "R0640": "PAINTING", "R0650": "SPECIALTIES",
    "R0700": "HVAC_TRIM", "R0710": "PLUMBING_TRIM", "R0720": "ELECTRICAL_TRIM",
    "R0730": "FIRE_ALARM", "R0740": "LOW_VOLTAGE",
    "R0800": "TAB", "R0810": "COMMISSIONING", "R0820": "PUNCH_LIST",
    "R0830": "FINAL_INSPECTION", "R0840": "CO_PROCESS",

    # Tenant Improvement
    "T0100": "SITE_MOBILIZATION",
    "T0110": "SELECTIVE_DEMO", "T0120": "DEMO_REMOVAL",
    "T0200": "HVAC_ROUGH", "T0210": "PLUMBING_ROUGH", "T0220": "ELECTRICAL_ROUGH",
    "T0230": "FIRE_PROTECTION", "T0240": "FIRE_ALARM", "T0250": "LOW_VOLTAGE",
    "T0300": "FRAMING_DRYWALL", "T0310": "DOORS_HARDWARE", "T0320": "CEILING",
    "T0330": "FLOORING", "T0340": "PAINTING", "T0350": "SPECIALTIES", "T0360": "SPECIALTIES",
    "T0400": "HVAC_TRIM", "T0410": "PLUMBING_TRIM", "T0420": "ELECTRICAL_TRIM",
    "T0430": "FIRE_ALARM", "T0440": "LOW_VOLTAGE",
    "T0500": "TAB", "T0510": "PUNCH_LIST", "T0520": "FINAL_INSPECTION",
}


# Renovation-specific fixed durations
_RENO_FIXED = {
    "TEMP_BARRIERS":      5,
    "TENANT_PROTECTION":  3,
    "HAZMAT_ABATEMENT":  15,
    "SELECTIVE_DEMO":    None,   # scaled by SF (see PRODUCTION_RATES below)
    "MEP_DEMO":          None,
    "DEMO_REMOVAL":       5,
    "STRUCTURAL_MODS":   10,
    "CONCRETE_REPAIRS":   8,
    "EXISTING_SURVEY":    5,
}

# Per-SF rates for demo/reno-specific activities
_RENO_RATES = {
    "SELECTIVE_DEMO":     0.12,   # days per 1000 SF
    "MEP_DEMO":           0.08,
}


# Which template activity codes are milestones (duration = 0)
_MILESTONES = {
    "A0010", "A0020", "A0830", "A0840", "A0850",
    "R0010", "R0020", "R0830", "R0840", "R0850",
    "T0010", "T0020", "T0520", "T0530",
}

# Structure/MEP activities that scale with stories
_STORY_SCALE = {
    "A0300", "A0310", "A0320", "A0500", "A0520", "A0600",
    "R0500", "R0520", "R0600",
    "T0200", "T0220", "T0300",
}

# Renovation activities get a 15% productivity penalty (existing conditions)
_RENO_PENALTY_CODES = {
    "R0500", "R0510", "R0520", "R0530", "R0540", "R0550",
    "R0600", "R0610", "R0620", "R0630", "R0640",
    "R0700", "R0710", "R0720", "R0730", "R0740",
}

# Valid project scope values
VALID_SCOPES = ["new_construction", "renovation", "tenant_improvement"]


def _get_template(scope: str) -> list:
    """Return the activity template for the given scope."""
    if scope == "renovation":
        return _RENOVATION
    elif scope == "tenant_improvement":
        return _TENANT_IMPROVEMENT
    else:
        return _NEW_CONSTRUCTION


def _calc_duration(code: str, building_type: str, square_feet: int, scope: str) -> int:
    """Calculate duration for a single activity."""
    # Check milestones first
    if code in _MILESTONES:
        rate_code = _RATE_MAP.get(code)
        if rate_code and rate_code in FIXED_DURATIONS:
            return FIXED_DURATIONS[rate_code]
        return 0

    # Reno-specific fixed durations
    rate_code = _RATE_MAP.get(code, "")
    if rate_code in _RENO_FIXED and _RENO_FIXED[rate_code] is not None:
        return _RENO_FIXED[rate_code]

    # Reno-specific per-SF rates
    if rate_code in _RENO_RATES:
        return max(2, round(_RENO_RATES[rate_code] * (square_feet / 1000)))

    # Existing conditions survey
    if code == "R0050":
        return 5

    # Standard rate lookup
    if rate_code:
        dur = get_duration(rate_code, building_type, square_feet)

        # TI work is faster — 80% of new construction duration
        if scope == "tenant_improvement" and dur > 2:
            dur = max(2, round(dur * 0.80))

        # Renovation penalty — 15% slower for MEP/finishes in existing building
        if scope == "renovation" and code in _RENO_PENALTY_CODES:
            dur = round(dur * 1.15)

        return dur

    return 5  # fallback


def build_activities(
    building_type: str = "office",
    square_feet: int = 50000,
    stories: int = 2,
    scope: str = "new_construction",
) -> list[Activity]:
    """
    Generate a complete activity list with durations and predecessors.

    Args:
        building_type: office, retail, warehouse, medical, education, mixed_use
        square_feet: Gross building area
        stories: Number of floors
        scope: new_construction, renovation, or tenant_improvement
    """
    if scope not in VALID_SCOPES:
        scope = "new_construction"

    template = _get_template(scope)
    activities = []

    for wbs, code, name, pred_defs, is_ms in template:
        duration = _calc_duration(code, building_type, square_feet, scope)

        # Scale by stories for structure and MEP
        if stories > 1 and code in _STORY_SCALE:
            duration = int(duration * (1 + 0.4 * (stories - 1)))

        # Build predecessor list
        preds = []
        for pred_code, rel_type, lag in pred_defs:
            preds.append({
                "activity_id": pred_code,
                "rel_type": rel_type,
                "lag": lag,
            })

        act = Activity(
            activity_id=code,
            activity_name=name,
            wbs=wbs,
            duration=duration,
            predecessors=preds,
            is_milestone=code in _MILESTONES or (is_ms and duration == 0),
        )
        activities.append(act)

    log.info(
        "Built %d activities for %s %s, %d SF, %d stories",
        len(activities), scope, building_type, square_feet, stories,
    )
    return activities
