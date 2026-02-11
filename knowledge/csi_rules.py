"""
Division-specific review rules for commercial construction plan review.

Each division has a checklist of items DABO verifies when that discipline
is present in the drawing set. These drive the automated checks beyond
cross-discipline conflicts.
"""
from __future__ import annotations


# Format: {discipline_code: [list of check items]}
# Each check item: (check_id, description, severity, what_to_look_for)
DIVISION_CHECKS: dict[str, list[tuple[str, str, str, list[str]]]] = {
    "STR": [
        ("STR-01", "Foundation type matches geotech report", "MAJOR", ["FOUNDATION", "GEOTECH", "BORING", "SOIL"]),
        ("STR-02", "Concrete strength specified on drawings", "MAJOR", ["PSI", "F'C", "MIX DESIGN"]),
        ("STR-03", "Steel connection details provided", "MAJOR", ["CONNECTION", "DETAIL", "MOMENT", "SHEAR"]),
        ("STR-04", "Slab on grade thickness and reinforcing noted", "MAJOR", ["SOG", "SLAB", "REINFORCING", "MESH"]),
        ("STR-05", "Expansion/control joints shown", "MINOR", ["EXPANSION", "CONTROL JOINT", "ISOLATION"]),
        ("STR-06", "Structural steel schedule complete", "MAJOR", ["SCHEDULE", "BEAM", "COLUMN"]),
        ("STR-07", "Live load assumptions noted", "MAJOR", ["LIVE LOAD", "PSF", "DESIGN LOAD"]),
    ],
    "ARCH": [
        ("ARCH-01", "Door schedule complete with hardware", "MAJOR", ["DOOR SCHEDULE", "HARDWARE", "CLOSER"]),
        ("ARCH-02", "Finish schedule per room", "MINOR", ["FINISH SCHEDULE", "FLOOR", "WALL", "CEILING"]),
        ("ARCH-03", "Partition types defined", "MAJOR", ["PARTITION", "TYPE", "STC", "RATED"]),
        ("ARCH-04", "Ceiling heights noted", "MINOR", ["CEILING", "HEIGHT", "CLG"]),
        ("ARCH-05", "ADA compliance checked", "CRITICAL", ["ADA", "ACCESSIBLE", "CLEARANCE", "GRAB BAR"]),
        ("ARCH-06", "Code-required signage shown", "MAJOR", ["EXIT", "SIGNAGE", "ADA", "ROOM"]),
        ("ARCH-07", "Reflected ceiling plan matches floor plan", "MAJOR", ["RCP", "REFLECTED", "CEILING"]),
    ],
    "MECH": [
        ("MECH-01", "Equipment schedule with capacities", "MAJOR", ["SCHEDULE", "CFM", "TON", "BTU", "MBH"]),
        ("MECH-02", "Duct sizes noted on plan", "MAJOR", ["DUCT", "SIZE", "SUPPLY", "RETURN"]),
        ("MECH-03", "Outdoor air requirements met", "CRITICAL", ["OUTDOOR AIR", "OA", "ASHRAE", "VENTILATION"]),
        ("MECH-04", "Controls sequence provided", "MAJOR", ["SEQUENCE", "CONTROL", "BAS", "DDC"]),
        ("MECH-05", "Refrigerant piping sized", "MINOR", ["REFRIGERANT", "LINE SET", "SUCTION", "LIQUID"]),
        ("MECH-06", "Test and balance requirements noted", "MINOR", ["TAB", "TEST", "BALANCE"]),
    ],
    "ELEC": [
        ("ELEC-01", "Panel schedules complete", "CRITICAL", ["PANEL SCHEDULE", "CIRCUIT", "LOAD"]),
        ("ELEC-02", "One-line diagram provided", "CRITICAL", ["ONE-LINE", "SINGLE LINE", "RISER"]),
        ("ELEC-03", "Short circuit and coordination study noted", "MAJOR", ["SHORT CIRCUIT", "COORDINATION", "AIC"]),
        ("ELEC-04", "Emergency/standby power scope defined", "CRITICAL", ["EMERGENCY", "STANDBY", "GENERATOR", "ATS"]),
        ("ELEC-05", "Lighting controls per energy code", "MAJOR", ["OCCUPANCY", "DAYLIGHT", "DIMMING", "ENERGY CODE"]),
        ("ELEC-06", "Voltage drop calculations", "MINOR", ["VOLTAGE DROP", "FEEDER", "WIRE SIZE"]),
    ],
    "PLMB": [
        ("PLMB-01", "Plumbing fixture schedule", "MAJOR", ["FIXTURE SCHEDULE", "WC", "LAV", "URINAL"]),
        ("PLMB-02", "Water heater sizing", "MAJOR", ["WATER HEATER", "GALLON", "BTU", "RECOVERY"]),
        ("PLMB-03", "Backflow prevention", "CRITICAL", ["BACKFLOW", "RPZA", "DC", "PREVENTER"]),
        ("PLMB-04", "Roof drain locations and sizing", "MAJOR", ["ROOF DRAIN", "OVERFLOW", "LEADER"]),
        ("PLMB-05", "Gas piping sized and routed", "MAJOR", ["GAS", "NATURAL GAS", "BTU", "CFH"]),
    ],
    "FP": [
        ("FP-01", "Sprinkler hydraulic design area noted", "CRITICAL", ["HYDRAULIC", "DESIGN AREA", "DENSITY", "HAZARD"]),
        ("FP-02", "Sprinkler head types per area", "MAJOR", ["HEAD", "PENDENT", "UPRIGHT", "CONCEALED", "SIDEWALL"]),
        ("FP-03", "Fire pump sizing", "CRITICAL", ["FIRE PUMP", "GPM", "PSI", "JOCKEY"]),
        ("FP-04", "FDC location and type", "MAJOR", ["FDC", "FIRE DEPARTMENT", "SIAMESE", "STORZ"]),
    ],
    "FA": [
        ("FA-01", "FACP location and type", "CRITICAL", ["FACP", "FIRE ALARM", "CONTROL PANEL"]),
        ("FA-02", "Initiating device coverage", "CRITICAL", ["DETECTOR", "SMOKE", "HEAT", "PULL STATION"]),
        ("FA-03", "Notification device coverage", "CRITICAL", ["HORN", "STROBE", "NOTIFICATION", "NFPA 72"]),
        ("FA-04", "Fire alarm monitoring", "MAJOR", ["MONITORING", "SUPERVISE", "ANNUNCIATOR"]),
    ],
    "CIV": [
        ("CIV-01", "Utility connections shown", "CRITICAL", ["WATER", "SEWER", "STORM", "GAS", "ELECTRIC", "TELECOM"]),
        ("CIV-02", "Grading and drainage plan", "MAJOR", ["GRADING", "DRAINAGE", "CONTOUR", "SLOPE"]),
        ("CIV-03", "Parking count per code", "MAJOR", ["PARKING", "SPACE", "ADA", "COUNT"]),
        ("CIV-04", "Fire lane access", "CRITICAL", ["FIRE LANE", "ACCESS", "TURNING RADIUS"]),
    ],
}


def get_checks(discipline_code: str) -> list[tuple[str, str, str, list[str]]]:
    """Return division-specific checks for a discipline."""
    return DIVISION_CHECKS.get(discipline_code, [])


def get_all_checks_for_project(disc_codes: set[str]) -> dict[str, list]:
    """Return all applicable checks for the disciplines in a project."""
    return {code: DIVISION_CHECKS.get(code, []) for code in disc_codes if code in DIVISION_CHECKS}
