"""
Sheet naming conventions by discipline.

Construction drawing sets follow predictable sheet numbering:
  A-101 = Architectural sheet 101
  S-201 = Structural sheet 201
  M-001 = Mechanical sheet 1
  E-101 = Electrical sheet 101

This module maps sheet prefix patterns to CSI disciplines
so the classifier can route sheets before reading content.
"""

# Map: regex pattern → (discipline_code, discipline_name, csi_divisions)
# Patterns are checked in order; first match wins.
SHEET_PREFIX_PATTERNS = [
    # ── General / Cover ────────────────────────────────
    (r"^G[-\s]?\d",       "GEN",  "General",                   ["01"]),
    (r"^T[-\s]?\d",       "GEN",  "Title / Cover",             ["01"]),

    # ── Civil / Site ───────────────────────────────────
    (r"^C[-\s]?\d",       "CIV",  "Civil / Site",              ["02", "31", "32", "33"]),
    (r"^L[-\s]?\d",       "CIV",  "Landscape",                 ["32"]),

    # ── Architectural ──────────────────────────────────
    (r"^A[-\s]?\d",       "ARCH", "Architectural",             ["06", "07", "08", "09", "10"]),
    (r"^AD[-\s]?\d",      "ARCH", "Architectural Demo",        ["02"]),
    (r"^AI[-\s]?\d",      "ARCH", "Architectural Interiors",   ["09", "10", "12"]),
    (r"^ID[-\s]?\d",      "ARCH", "Interior Design",           ["09", "10", "12"]),

    # ── Structural ─────────────────────────────────────
    (r"^S[-\s]?\d",       "STR",  "Structural",                ["03", "04", "05"]),
    (r"^SF[-\s]?\d",      "STR",  "Structural Foundation",     ["03"]),

    # ── Mechanical / HVAC ──────────────────────────────
    (r"^M[-\s]?\d",       "MECH", "Mechanical / HVAC",         ["15", "23"]),
    (r"^H[-\s]?\d",       "MECH", "HVAC",                      ["23"]),

    # ── Plumbing ───────────────────────────────────────
    (r"^P[-\s]?\d",       "PLMB", "Plumbing",                  ["22"]),

    # ── Electrical ─────────────────────────────────────
    (r"^E[-\s]?\d",       "ELEC", "Electrical",                ["26"]),
    (r"^EL[-\s]?\d",      "ELEC", "Electrical Lighting",       ["26"]),
    (r"^EP[-\s]?\d",      "ELEC", "Electrical Power",          ["26"]),

    # ── Fire Protection ────────────────────────────────
    (r"^FP[-\s]?\d",      "FP",   "Fire Protection",           ["21"]),
    (r"^FS[-\s]?\d",      "FP",   "Fire Suppression",          ["21"]),
    (r"^FA[-\s]?\d",      "FA",   "Fire Alarm",                ["28"]),

    # ── Technology / Low Voltage ───────────────────────
    (r"^T[-\s]?[A-Z]",    "TECH", "Technology",                ["27", "28"]),
    (r"^D[-\s]?\d",       "TECH", "Data / Communications",     ["27"]),
    (r"^IT[-\s]?\d",      "TECH", "IT / Technology",           ["27"]),

    # ── Food Service ───────────────────────────────────
    (r"^FK[-\s]?\d",      "FS",   "Food Service",              ["11"]),
    (r"^K[-\s]?\d",       "FS",   "Kitchen Equipment",         ["11"]),

    # ── Conveying ──────────────────────────────────────
    (r"^EV[-\s]?\d",      "CONV", "Elevator / Conveying",      ["14"]),
]

# Fallback keywords found in title blocks when prefix doesn't match
TITLE_BLOCK_KEYWORDS = {
    "FLOOR PLAN":       "ARCH",
    "ROOF PLAN":        "ARCH",
    "ELEVATION":        "ARCH",
    "SECTION":          "ARCH",  # can be structural too — needs context
    "DETAIL":           "ARCH",
    "REFLECTED CEILING": "ARCH",
    "FOUNDATION":       "STR",
    "FRAMING":          "STR",
    "COLUMN SCHEDULE":  "STR",
    "BEAM SCHEDULE":    "STR",
    "MECHANICAL":       "MECH",
    "HVAC":             "MECH",
    "DUCTWORK":         "MECH",
    "PLUMBING":         "PLMB",
    "PIPING":           "PLMB",
    "ELECTRICAL":       "ELEC",
    "LIGHTING":         "ELEC",
    "POWER PLAN":       "ELEC",
    "PANEL SCHEDULE":   "ELEC",
    "ONE-LINE":         "ELEC",
    "SINGLE LINE":      "ELEC",
    "FIRE ALARM":       "FA",
    "FIRE PROTECTION":  "FP",
    "SPRINKLER":        "FP",
    "SITE PLAN":        "CIV",
    "GRADING":          "CIV",
    "UTILITY":          "CIV",
    "DEMOLITION":       "ARCH",
}
