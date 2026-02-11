"""
Activity builder — generate schedule activities from project scope.

Takes project parameters (type, SF, stories, disciplines) and generates
a standard commercial construction activity list with durations and
predecessor logic.
"""
from __future__ import annotations

from config.production_rates import get_duration
from scheduling.cpm_engine import Activity
from utils.logger import get_logger

log = get_logger(__name__)


# Standard activity sequence for commercial construction
# (wbs, activity_code, name, predecessors as (code, rel, lag))
_ACTIVITY_TEMPLATE = [
    # ── Preconstruction ───────────────────────────────────
    ("01", "A0010", "Notice to Proceed",       [],                                      True),
    ("01", "A0020", "Permits & Approvals",      [("A0010", "FS", 0)],                   True),
    ("01", "A0030", "Shop Drawing Submittals",  [("A0010", "FS", 0)],                   False),
    ("01", "A0040", "Material Procurement",     [("A0030", "FS", 5)],                   False),

    # ── Sitework ──────────────────────────────────────────
    ("02", "A0100", "Mobilization",             [("A0020", "FS", 0)],                   False),
    ("02", "A0110", "Earthwork & Grading",      [("A0100", "FS", 0)],                   False),
    ("02", "A0120", "Underground Utilities",    [("A0110", "FS", 0)],                   False),

    # ── Foundations ────────────────────────────────────────
    ("03", "A0200", "Foundations",              [("A0120", "FS", 0)],                   False),
    ("03", "A0210", "Slab on Grade",           [("A0200", "FS", 0)],                   False),

    # ── Structure ─────────────────────────────────────────
    ("05", "A0300", "Structural Steel Erection", [("A0200", "FS", 0), ("A0040", "FS", 0)], False),
    ("05", "A0310", "Metal Deck & Shear Studs", [("A0300", "SS", 5)],                  False),
    ("03", "A0320", "Elevated Concrete Decks",  [("A0310", "FS", 0)],                   False),

    # ── Envelope ──────────────────────────────────────────
    ("07", "A0400", "Roofing",                  [("A0310", "FS", 5)],                   False),
    ("07", "A0410", "Exterior Wall System",     [("A0300", "SS", 10)],                  False),
    ("08", "A0420", "Windows & Storefront",     [("A0410", "SS", 10)],                  False),
    ("07", "A0430", "Waterproofing & Sealants", [("A0410", "SS", 15)],                  False),

    # ── MEP Rough-In ──────────────────────────────────────
    ("15", "A0500", "HVAC Rough-In",            [("A0320", "FS", 0)],                   False),
    ("15", "A0510", "Plumbing Rough-In",        [("A0210", "FS", 0)],                   False),
    ("16", "A0520", "Electrical Rough-In",      [("A0320", "FS", 0)],                   False),
    ("15", "A0530", "Fire Protection",          [("A0320", "FS", 0)],                   False),
    ("16", "A0540", "Fire Alarm Rough-In",      [("A0520", "SS", 5)],                   False),
    ("16", "A0550", "Low Voltage Rough-In",     [("A0520", "SS", 5)],                   False),

    # ── Interior Finishes ─────────────────────────────────
    ("09", "A0600", "Metal Framing & Drywall",  [("A0500", "SS", 10), ("A0520", "SS", 10)], False),
    ("08", "A0610", "Doors & Hardware",         [("A0600", "SS", 15)],                  False),
    ("09", "A0620", "Ceiling Grid & Tile",      [("A0600", "FS", 0), ("A0500", "FS", -5)], False),
    ("09", "A0630", "Flooring",                 [("A0600", "FS", 0)],                   False),
    ("09", "A0640", "Painting",                 [("A0600", "FS", 0)],                   False),
    ("10", "A0650", "Specialties & Accessories", [("A0640", "FS", 0)],                  False),

    # ── MEP Trim ──────────────────────────────────────────
    ("15", "A0700", "HVAC Trim & Startup",      [("A0620", "FS", 0)],                   False),
    ("15", "A0710", "Plumbing Trim & Fixtures",  [("A0630", "FS", 0)],                  False),
    ("16", "A0720", "Electrical Trim & Devices", [("A0640", "FS", 0)],                  False),
    ("16", "A0730", "Fire Alarm Trim & Test",    [("A0620", "FS", 0)],                  False),
    ("16", "A0740", "Low Voltage Trim & Test",   [("A0620", "FS", 0)],                  False),

    # ── Commissioning & Closeout ──────────────────────────
    ("01", "A0800", "Test & Balance",            [("A0700", "FS", 0)],                  False),
    ("01", "A0810", "Commissioning",             [("A0800", "FS", 0)],                  False),
    ("01", "A0820", "Punch List",                [("A0810", "FS", 0), ("A0710", "FS", 0), ("A0720", "FS", 0)], False),
    ("01", "A0830", "Final Inspections",         [("A0820", "FS", 0)],                  True),
    ("01", "A0840", "Certificate of Occupancy",  [("A0830", "FS", 0)],                  True),
    ("01", "A0850", "Substantial Completion",    [("A0840", "FS", 0)],                  True),
]

# Activity code → production rate code mapping
_RATE_MAP = {
    "A0100": "SITE_MOBILIZATION",
    "A0110": "EARTHWORK",
    "A0120": "UNDERGROUND_UTIL",
    "A0200": "FOUNDATIONS",
    "A0210": "SLAB_ON_GRADE",
    "A0300": "STRUCTURAL_STEEL",
    "A0310": "METAL_DECK",
    "A0320": "CONCRETE_STRUCTURE",
    "A0400": "ROOFING",
    "A0410": "EXTERIOR_WALL",
    "A0420": "WINDOWS_STOREFRONT",
    "A0430": "WATERPROOFING",
    "A0500": "HVAC_ROUGH",
    "A0510": "PLUMBING_ROUGH",
    "A0520": "ELECTRICAL_ROUGH",
    "A0530": "FIRE_PROTECTION",
    "A0540": "FIRE_ALARM",
    "A0550": "LOW_VOLTAGE",
    "A0600": "FRAMING_DRYWALL",
    "A0610": "DOORS_HARDWARE",
    "A0620": "CEILING",
    "A0630": "FLOORING",
    "A0640": "PAINTING",
    "A0650": "SPECIALTIES",
    "A0700": "HVAC_TRIM",
    "A0710": "PLUMBING_TRIM",
    "A0720": "ELECTRICAL_TRIM",
    "A0730": "FIRE_ALARM",
    "A0740": "LOW_VOLTAGE",
    "A0800": "TAB",
    "A0810": "COMMISSIONING",
    "A0820": "PUNCH_LIST",
    "A0830": "FINAL_INSPECTION",
    "A0840": "CO_PROCESS",
}

# Milestone activity codes (duration = 0)
_MILESTONES = {"A0010", "A0020", "A0830", "A0840", "A0850"}


def build_activities(
    building_type: str = "office",
    square_feet: int = 50000,
    stories: int = 2,
) -> list[Activity]:
    """
    Generate a complete activity list with durations and predecessors.
    """
    activities = []

    for wbs, code, name, pred_defs, is_ms in _ACTIVITY_TEMPLATE:
        # Calculate duration
        if code in _MILESTONES or is_ms:
            if code in _RATE_MAP:
                duration = get_duration(_RATE_MAP[code], building_type, square_feet)
            else:
                duration = 0
        elif code in _RATE_MAP:
            duration = get_duration(_RATE_MAP[code], building_type, square_feet)
            # Scale by stories for structure and MEP
            if stories > 1 and code in ("A0300", "A0310", "A0320", "A0500", "A0520", "A0600"):
                duration = int(duration * (1 + 0.4 * (stories - 1)))
        else:
            duration = 5  # default

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
        "Built %d activities for %s, %d SF, %d stories",
        len(activities), building_type, square_feet, stories,
    )
    return activities
