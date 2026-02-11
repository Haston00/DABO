"""
Standard production rates and durations by building type and activity.

Durations are in working days per 1000 SF (scaled to project size),
or fixed durations for activities that don't scale with SF.

Based on RS Means, industry benchmarks, and GC scheduling experience
for commercial construction (stick-built, structural steel, tilt-up).
"""

# Duration per 1000 SF — formula: rate * (SF / 1000), min 1 day
# Calibrated for 20,000-150,000 SF commercial buildings
PRODUCTION_RATES = {
    # ── Sitework & Foundations ─────────────────────────────
    "EARTHWORK":                {"office": 0.25, "retail": 0.20, "warehouse": 0.15, "medical": 0.30, "education": 0.25, "mixed_use": 0.25},
    "UNDERGROUND_UTIL":         {"office": 0.30, "retail": 0.25, "warehouse": 0.15, "medical": 0.40, "education": 0.30, "mixed_use": 0.30},
    "FOUNDATIONS":              {"office": 0.35, "retail": 0.30, "warehouse": 0.20, "medical": 0.40, "education": 0.35, "mixed_use": 0.35},
    "SLAB_ON_GRADE":            {"office": 0.15, "retail": 0.15, "warehouse": 0.10, "medical": 0.20, "education": 0.15, "mixed_use": 0.15},

    # ── Structure ─────────────────────────────────────────
    "STRUCTURAL_STEEL":         {"office": 0.40, "retail": 0.30, "warehouse": 0.20, "medical": 0.45, "education": 0.35, "mixed_use": 0.40},
    "METAL_DECK":               {"office": 0.10, "retail": 0.10, "warehouse": 0.08, "medical": 0.12, "education": 0.10, "mixed_use": 0.10},
    "CONCRETE_STRUCTURE":       {"office": 0.25, "retail": 0.20, "warehouse": 0.10, "medical": 0.30, "education": 0.25, "mixed_use": 0.25},
    "MASONRY":                  {"office": 0.20, "retail": 0.25, "warehouse": 0.15, "medical": 0.25, "education": 0.25, "mixed_use": 0.22},

    # ── Envelope ──────────────────────────────────────────
    "ROOFING":                  {"office": 0.15, "retail": 0.15, "warehouse": 0.10, "medical": 0.18, "education": 0.15, "mixed_use": 0.15},
    "EXTERIOR_WALL":            {"office": 0.25, "retail": 0.20, "warehouse": 0.15, "medical": 0.30, "education": 0.25, "mixed_use": 0.25},
    "WINDOWS_STOREFRONT":       {"office": 0.15, "retail": 0.20, "warehouse": 0.05, "medical": 0.15, "education": 0.15, "mixed_use": 0.18},
    "WATERPROOFING":            {"office": 0.08, "retail": 0.08, "warehouse": 0.05, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},

    # ── Interior ──────────────────────────────────────────
    "FRAMING_DRYWALL":          {"office": 0.30, "retail": 0.25, "warehouse": 0.10, "medical": 0.40, "education": 0.35, "mixed_use": 0.32},
    "DOORS_HARDWARE":           {"office": 0.08, "retail": 0.06, "warehouse": 0.03, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},
    "CEILING":                  {"office": 0.10, "retail": 0.10, "warehouse": 0.03, "medical": 0.12, "education": 0.10, "mixed_use": 0.10},
    "FLOORING":                 {"office": 0.10, "retail": 0.12, "warehouse": 0.05, "medical": 0.15, "education": 0.12, "mixed_use": 0.12},
    "PAINTING":                 {"office": 0.08, "retail": 0.08, "warehouse": 0.03, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},
    "SPECIALTIES":              {"office": 0.05, "retail": 0.05, "warehouse": 0.01, "medical": 0.08, "education": 0.06, "mixed_use": 0.05},

    # ── MEP ───────────────────────────────────────────────
    "HVAC_ROUGH":               {"office": 0.25, "retail": 0.20, "warehouse": 0.08, "medical": 0.35, "education": 0.25, "mixed_use": 0.25},
    "HVAC_TRIM":                {"office": 0.10, "retail": 0.08, "warehouse": 0.03, "medical": 0.12, "education": 0.10, "mixed_use": 0.10},
    "PLUMBING_ROUGH":           {"office": 0.15, "retail": 0.10, "warehouse": 0.04, "medical": 0.25, "education": 0.15, "mixed_use": 0.15},
    "PLUMBING_TRIM":            {"office": 0.05, "retail": 0.04, "warehouse": 0.01, "medical": 0.08, "education": 0.05, "mixed_use": 0.05},
    "ELECTRICAL_ROUGH":         {"office": 0.20, "retail": 0.15, "warehouse": 0.05, "medical": 0.25, "education": 0.20, "mixed_use": 0.20},
    "ELECTRICAL_TRIM":          {"office": 0.08, "retail": 0.06, "warehouse": 0.02, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},
    "FIRE_PROTECTION":          {"office": 0.08, "retail": 0.06, "warehouse": 0.04, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},
    "FIRE_ALARM":               {"office": 0.05, "retail": 0.04, "warehouse": 0.02, "medical": 0.08, "education": 0.05, "mixed_use": 0.05},
    "LOW_VOLTAGE":              {"office": 0.08, "retail": 0.05, "warehouse": 0.02, "medical": 0.10, "education": 0.08, "mixed_use": 0.08},
}

# Fixed durations (not scaled by SF) — working days
FIXED_DURATIONS = {
    "SITE_MOBILIZATION":  10,   # mob trailers, fencing, temp utilities
    "PERMIT":             30,   # building permit
    "SHOP_DRAWINGS":      20,   # submittals + review cycles
    "MATERIAL_LEAD":      45,   # long lead procurement
    "ELEVATOR":           90,   # per cab
    "GENERATOR":          15,
    "SWITCHGEAR":         10,
    "AHU_STARTUP":         5,   # per unit
    "TAB":                15,   # test & balance
    "COMMISSIONING":      10,   # Cx agent verification
    "PUNCH_LIST":         15,   # walk-throughs + corrections
    "FINAL_INSPECTION":    5,
    "CO_PROCESS":         10,   # certificate of occupancy
}


def get_duration(activity_code: str, building_type: str, square_feet: int) -> int:
    """
    Calculate activity duration in working days.

    For fixed durations: returns the fixed value.
    For per-SF rates: duration = rate * (SF / 1000), min 2 days.
    """
    if activity_code in FIXED_DURATIONS:
        return FIXED_DURATIONS[activity_code]

    rates = PRODUCTION_RATES.get(activity_code, {})
    rate = rates.get(building_type, rates.get("office", 0.15))
    days = max(2, round(rate * (square_feet / 1000)))
    return days
