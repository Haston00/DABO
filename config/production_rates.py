"""
Standard production rates and durations by building type and activity.

Durations are in working days per unit (1000 SF, floor, or each).
These are GC-level durations for commercial construction.
"""

# Duration per 1000 SF unless noted otherwise
# Format: {activity_code: {building_type: days_per_1000sf}}
PRODUCTION_RATES = {
    # ── Sitework & Foundations ─────────────────────────────
    "SITE_MOBILIZATION":        {"office": 5, "retail": 5, "warehouse": 5, "medical": 5, "education": 5},
    "EARTHWORK":                {"office": 0.5, "retail": 0.4, "warehouse": 0.3, "medical": 0.5, "education": 0.5},
    "UNDERGROUND_UTIL":         {"office": 0.8, "retail": 0.6, "warehouse": 0.4, "medical": 1.0, "education": 0.8},
    "FOUNDATIONS":              {"office": 0.6, "retail": 0.5, "warehouse": 0.3, "medical": 0.7, "education": 0.6},
    "SLAB_ON_GRADE":            {"office": 0.3, "retail": 0.3, "warehouse": 0.2, "medical": 0.4, "education": 0.3},

    # ── Structure ─────────────────────────────────────────
    "STRUCTURAL_STEEL":         {"office": 0.8, "retail": 0.6, "warehouse": 0.4, "medical": 0.9, "education": 0.7},
    "METAL_DECK":               {"office": 0.2, "retail": 0.2, "warehouse": 0.15, "medical": 0.25, "education": 0.2},
    "CONCRETE_STRUCTURE":       {"office": 0.5, "retail": 0.4, "warehouse": 0.2, "medical": 0.6, "education": 0.5},
    "MASONRY":                  {"office": 0.4, "retail": 0.5, "warehouse": 0.3, "medical": 0.5, "education": 0.5},

    # ── Envelope ──────────────────────────────────────────
    "ROOFING":                  {"office": 0.3, "retail": 0.3, "warehouse": 0.2, "medical": 0.35, "education": 0.3},
    "EXTERIOR_WALL":            {"office": 0.5, "retail": 0.4, "warehouse": 0.3, "medical": 0.6, "education": 0.5},
    "WINDOWS_STOREFRONT":       {"office": 0.3, "retail": 0.4, "warehouse": 0.1, "medical": 0.3, "education": 0.3},
    "WATERPROOFING":            {"office": 0.15, "retail": 0.15, "warehouse": 0.1, "medical": 0.2, "education": 0.15},

    # ── Interior ──────────────────────────────────────────
    "FRAMING_DRYWALL":          {"office": 0.6, "retail": 0.5, "warehouse": 0.2, "medical": 0.8, "education": 0.7},
    "DOORS_HARDWARE":           {"office": 0.15, "retail": 0.12, "warehouse": 0.05, "medical": 0.2, "education": 0.15},
    "CEILING":                  {"office": 0.2, "retail": 0.2, "warehouse": 0.05, "medical": 0.25, "education": 0.2},
    "FLOORING":                 {"office": 0.2, "retail": 0.25, "warehouse": 0.1, "medical": 0.3, "education": 0.25},
    "PAINTING":                 {"office": 0.15, "retail": 0.15, "warehouse": 0.05, "medical": 0.2, "education": 0.15},
    "SPECIALTIES":              {"office": 0.1, "retail": 0.1, "warehouse": 0.02, "medical": 0.15, "education": 0.12},

    # ── MEP ───────────────────────────────────────────────
    "HVAC_ROUGH":               {"office": 0.5, "retail": 0.4, "warehouse": 0.15, "medical": 0.7, "education": 0.5},
    "HVAC_TRIM":                {"office": 0.2, "retail": 0.15, "warehouse": 0.05, "medical": 0.25, "education": 0.2},
    "PLUMBING_ROUGH":           {"office": 0.3, "retail": 0.2, "warehouse": 0.08, "medical": 0.5, "education": 0.3},
    "PLUMBING_TRIM":            {"office": 0.1, "retail": 0.08, "warehouse": 0.02, "medical": 0.15, "education": 0.1},
    "ELECTRICAL_ROUGH":         {"office": 0.4, "retail": 0.3, "warehouse": 0.1, "medical": 0.5, "education": 0.4},
    "ELECTRICAL_TRIM":          {"office": 0.15, "retail": 0.12, "warehouse": 0.04, "medical": 0.2, "education": 0.15},
    "FIRE_PROTECTION":          {"office": 0.15, "retail": 0.12, "warehouse": 0.08, "medical": 0.2, "education": 0.15},
    "FIRE_ALARM":               {"office": 0.1, "retail": 0.08, "warehouse": 0.04, "medical": 0.15, "education": 0.1},
    "LOW_VOLTAGE":              {"office": 0.15, "retail": 0.1, "warehouse": 0.03, "medical": 0.2, "education": 0.15},

    # ── Closeout ──────────────────────────────────────────
    "COMMISSIONING":            {"office": 0.1, "retail": 0.08, "warehouse": 0.04, "medical": 0.15, "education": 0.1},
    "PUNCH_LIST":               {"office": 0.1, "retail": 0.1, "warehouse": 0.05, "medical": 0.15, "education": 0.1},
}

# Fixed durations (not per-SF)
FIXED_DURATIONS = {
    "PERMIT":           30,   # calendar days typically
    "SHOP_DRAWINGS":    20,
    "MATERIAL_LEAD":    60,   # long lead items
    "ELEVATOR":         90,   # per cab
    "GENERATOR":        15,
    "SWITCHGEAR":       10,
    "AHU_STARTUP":      5,    # per unit
    "TAB":              15,   # test & balance
    "FINAL_INSPECTION": 5,
    "CO_PROCESS":       15,   # certificate of occupancy
}


def get_duration(activity_code: str, building_type: str, square_feet: int) -> int:
    """
    Calculate activity duration in working days.

    For per-SF rates: duration = rate * (SF / 1000), min 1 day.
    For fixed durations: returns the fixed value.
    """
    if activity_code in FIXED_DURATIONS:
        return FIXED_DURATIONS[activity_code]

    rates = PRODUCTION_RATES.get(activity_code, {})
    rate = rates.get(building_type, rates.get("office", 0.3))
    days = max(1, round(rate * (square_feet / 1000)))
    return days
