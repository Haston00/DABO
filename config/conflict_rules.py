"""
34 cross-discipline conflict detection rules for commercial construction.

Each rule defines:
  - ID: CR-XXX
  - Name and description
  - Disciplines involved (which sheet types to compare)
  - Severity: CRITICAL / MAJOR / MINOR / INFO
  - Detection method: what to look for in extracted entities
  - Auto-detectable: whether regex/logic can catch it or needs AI assist

Rules are organized by conflict category.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConflictRule:
    rule_id: str
    name: str
    description: str
    category: str
    disciplines: list[str]        # Which discipline codes are involved
    severity: str                  # CRITICAL, MAJOR, MINOR, INFO
    detection_type: str            # "cross_ref", "dimension", "equipment", "code", "ai_only"
    auto_detectable: bool = True   # Can be caught by rule engine alone
    enabled: bool = True
    keywords: list[str] = field(default_factory=list)  # Signal keywords
    check_fn_name: str = ""        # Name of the check function in conflict_detector


# ── All 34 Rules ─────────────────────────────────────────

CONFLICT_RULES: dict[str, ConflictRule] = {}

def _r(rule_id, name, desc, cat, discs, sev, det, auto=True, kw=None):
    """Shorthand to register a rule."""
    CONFLICT_RULES[rule_id] = ConflictRule(
        rule_id=rule_id, name=name, description=desc,
        category=cat, disciplines=discs, severity=sev,
        detection_type=det, auto_detectable=auto,
        keywords=kw or [], check_fn_name=f"check_{rule_id.lower().replace('-', '_')}",
    )

# ── Structural / Architectural (Divs 03-05 vs 06-09) ─────

_r("CR-001", "Beam depth vs ceiling height",
   "Structural beam depth plus deck thickness exceeds available plenum space below finished ceiling.",
   "STR-ARCH", ["STR", "ARCH", "MECH"], "CRITICAL", "dimension",
   kw=["BEAM", "CEILING", "PLENUM", "T.O.S.", "CLG HT"])

_r("CR-017", "Opening in shear wall not coordinated",
   "Architectural door or window shown in a wall identified as shear wall on structural drawings.",
   "STR-ARCH", ["STR", "ARCH"], "CRITICAL", "cross_ref",
   kw=["SHEAR WALL", "OPENING", "DOOR", "WINDOW"])

_r("CR-024", "Dimension strings don't add up",
   "Partial dimensions on a plan don't sum to the overall dimension string.",
   "COORDINATION", ["ARCH", "STR"], "MAJOR", "dimension",
   kw=["DIM", "OVERALL"])

_r("CR-023", "Callout references missing detail",
   "A detail or section callout on one sheet references a detail number that doesn't exist on the target sheet.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB", "FP"], "MAJOR", "cross_ref")

# ── MEP Cross-Discipline (Divs 15-16) ─────────────────────

_r("CR-002", "Duct route vs beam location",
   "HVAC ductwork shown routing through or conflicting with structural beam at same elevation.",
   "MEP-STR", ["MECH", "STR"], "CRITICAL", "dimension",
   kw=["DUCT", "BEAM", "ROUTE", "ELEVATION"])

_r("CR-003", "Conduit vs ductwork routing",
   "Electrical conduit routing conflicts with HVAC ductwork in shared chase or ceiling space.",
   "MEP-MEP", ["ELEC", "MECH"], "MAJOR", "cross_ref",
   kw=["CONDUIT", "DUCT", "CHASE", "ROUTING"])

_r("CR-004", "Pipe penetration through structure",
   "Plumbing or mechanical pipe penetrates structural element without noted sleeve or opening.",
   "MEP-STR", ["PLMB", "MECH", "STR"], "CRITICAL", "cross_ref",
   kw=["PENETRATION", "SLEEVE", "OPENING", "BEAM", "SLAB"])

_r("CR-008", "Piping vs ductwork chase conflict",
   "Plumbing risers and HVAC ductwork compete for the same shaft or chase space.",
   "MEP-MEP", ["PLMB", "MECH"], "MAJOR", "cross_ref",
   kw=["CHASE", "SHAFT", "RISER", "DUCT"])

_r("CR-012", "HVAC duct vs sprinkler main",
   "HVAC ductwork and fire sprinkler main are shown at conflicting elevations in corridor.",
   "MEP-FP", ["MECH", "FP"], "CRITICAL", "dimension",
   kw=["DUCT", "SPRINKLER", "MAIN", "ELEVATION", "CORRIDOR"])

_r("CR-014", "Equipment load vs structural capacity",
   "Mechanical equipment weight/vibration exceeds structural design at the support location.",
   "MEP-STR", ["MECH", "STR"], "CRITICAL", "equipment",
   kw=["AHU", "RTU", "CHILLER", "WEIGHT", "LOAD", "DUNNAGE"])

_r("CR-020", "HVAC MCA/MOCP vs panel schedule",
   "Mechanical equipment electrical requirements don't match panel schedule circuit allocation.",
   "MEP-ELEC", ["MECH", "ELEC"], "MAJOR", "equipment",
   kw=["MCA", "MOCP", "PANEL", "CIRCUIT", "BREAKER", "AMP"])

# ── Electrical-Specific (Div 16) ──────────────────────────

_r("CR-007", "Panel location vs wall type/depth",
   "Electrical panel shown on a wall that's too thin or is a fire-rated assembly requiring special mounting.",
   "ELEC-ARCH", ["ELEC", "ARCH"], "MAJOR", "cross_ref",
   kw=["PANEL", "WALL", "PARTITION", "RATED", "DEPTH"])

_r("CR-010", "Electrical near water sources",
   "Electrical panels, receptacles, or equipment within NEC-prohibited distance from water sources.",
   "ELEC-PLMB", ["ELEC", "PLMB"], "CRITICAL", "cross_ref",
   kw=["PANEL", "RECEPTACLE", "WATER", "SINK", "FOUNTAIN", "NEC"])

_r("CR-018", "Electrical service vs underground utilities",
   "Electrical service entrance conflicts with underground utility routing shown on civil drawings.",
   "ELEC-CIV", ["ELEC", "CIV"], "MAJOR", "cross_ref",
   kw=["SERVICE", "UNDERGROUND", "UTILITY", "TRANSFORMER", "PAD"])

_r("CR-022", "Receptacle height vs casework",
   "Receptacle or switch mounting height conflicts with casework or equipment at same wall location.",
   "ELEC-ARCH", ["ELEC", "ARCH"], "MINOR", "dimension",
   kw=["RECEPTACLE", "SWITCH", "CASEWORK", "COUNTER", "AFF"])

_r("CR-026", "Panel schedule load calc",
   "Panel schedule connected load doesn't match demand load calculation or exceeds panel rating.",
   "ELEC", ["ELEC"], "CRITICAL", "equipment",
   kw=["PANEL", "LOAD", "CONNECTED", "DEMAND", "AMPERE", "RATING"])

_r("CR-027", "Voltage/phase mismatch",
   "Equipment nameplate voltage/phase doesn't match the panel or circuit feeding it.",
   "ELEC-MEP", ["ELEC", "MECH"], "CRITICAL", "equipment",
   kw=["VOLTAGE", "PHASE", "277", "480", "208", "120", "3PH", "1PH"])

_r("CR-028", "Short circuit/coordination",
   "Available fault current at a panel or device exceeds its AIC (interrupting) rating.",
   "ELEC", ["ELEC"], "CRITICAL", "equipment",
   kw=["AIC", "KAIC", "FAULT", "SHORT CIRCUIT", "COORDINATION"])

_r("CR-029", "Generator load vs ATS capacity",
   "Generator connected load or ATS rating doesn't match standby load requirements.",
   "ELEC", ["ELEC"], "CRITICAL", "equipment",
   kw=["GENERATOR", "ATS", "STANDBY", "EMERGENCY", "KW", "TRANSFER"])

_r("CR-030", "Fire alarm device spacing vs NFPA 72",
   "Fire alarm notification or detection device spacing exceeds NFPA 72 maximums.",
   "FA", ["FA"], "CRITICAL", "code",
   kw=["NFPA 72", "SPACING", "DETECTOR", "HORN", "STROBE", "NOTIFICATION"])

_r("CR-031", "Lighting fixture type vs spec section",
   "Lighting fixture type on drawings doesn't match fixture schedule or spec section description.",
   "ELEC", ["ELEC"], "MINOR", "cross_ref",
   kw=["FIXTURE", "TYPE", "SCHEDULE", "LIGHTING"])

_r("CR-032", "Receptacle count vs NEC minimums",
   "Receptacle count in a space falls below NEC minimum requirements for the occupancy type.",
   "ELEC", ["ELEC", "ARCH"], "MAJOR", "code",
   kw=["RECEPTACLE", "NEC", "MINIMUM", "COUNT", "SPACING"])

_r("CR-033", "Data outlet count vs furniture plan",
   "Data/telecom outlet locations don't align with furniture plan workstation locations.",
   "TECH-ARCH", ["TECH", "ARCH"], "MINOR", "cross_ref",
   kw=["DATA", "OUTLET", "FURNITURE", "WORKSTATION"])

_r("CR-034", "Low-voltage pathway sizing",
   "Cable tray or conduit fill exceeds 40% for low-voltage cabling per pathway standards.",
   "TECH", ["TECH"], "MAJOR", "dimension",
   kw=["CABLE TRAY", "FILL", "J-HOOK", "PATHWAY", "CONDUIT"])

# ── Envelope / Waterproofing (Div 07) ─────────────────────

_r("CR-005", "Sprinkler head vs ceiling type",
   "Sprinkler head type (pendent/upright/concealed) doesn't match ceiling type at that location.",
   "FP-ARCH", ["FP", "ARCH"], "MAJOR", "cross_ref",
   kw=["SPRINKLER", "HEAD", "CEILING", "CONCEALED", "PENDENT", "UPRIGHT"])

_r("CR-015", "Finish floor vs site grade",
   "Interior finish floor elevation doesn't maintain required relationship to exterior site grade.",
   "ARCH-CIV", ["ARCH", "CIV"], "MAJOR", "dimension",
   kw=["FFE", "GRADE", "ELEVATION", "FLOOR", "SITE"])

_r("CR-021", "Penetration through rated assembly",
   "MEP penetration through fire-rated wall or floor assembly without noted firestopping.",
   "FP-ARCH", ["MECH", "PLMB", "ELEC", "ARCH"], "CRITICAL", "cross_ref",
   kw=["PENETRATION", "RATED", "FIRESTOP", "FIRE WALL", "RATED ASSEMBLY"])

# ── Civil / Site (Divs 02, 31-33) ─────────────────────────

_r("CR-009", "Foundation vs utility conflict",
   "Building foundation or footing conflicts with underground utility routing.",
   "STR-CIV", ["STR", "CIV"], "CRITICAL", "cross_ref",
   kw=["FOUNDATION", "FOOTING", "UTILITY", "UNDERGROUND", "PIPE"])

_r("CR-016", "Interior plumbing vs site utilities",
   "Interior plumbing waste/storm connections don't align with site utility stub locations.",
   "PLMB-CIV", ["PLMB", "CIV"], "MAJOR", "cross_ref",
   kw=["INVERT", "STUB", "CONNECTION", "SANITARY", "STORM"])

_r("CR-025", "Egress width vs code",
   "Exit corridor or stair width falls below code-required minimum for the occupant load.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["EGRESS", "EXIT", "CORRIDOR", "WIDTH", "OCCUPANT", "IBC"])

# ── Architecture / Coordination (Divs 08-10) ─────────────

_r("CR-006", "Diffuser location vs ceiling layout",
   "HVAC diffuser or return grille location conflicts with ceiling grid, light fixture, or cloud.",
   "MECH-ARCH", ["MECH", "ARCH"], "MINOR", "cross_ref",
   kw=["DIFFUSER", "GRILLE", "CEILING", "GRID", "LIGHT"])

_r("CR-011", "Door swing vs sprinkler coverage",
   "Door swing arc interferes with sprinkler head coverage pattern or head location.",
   "FP-ARCH", ["FP", "ARCH"], "MINOR", "cross_ref",
   kw=["DOOR", "SWING", "SPRINKLER", "HEAD", "COVERAGE"])

_r("CR-013", "Spec section missing from drawings",
   "Drawing references a CSI spec section that is not included in the project manual.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB", "FP"], "MAJOR", "cross_ref")

_r("CR-019", "Fixture count vs code requirements",
   "Plumbing fixture count doesn't meet code minimum for the building occupancy and occupant load.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "CRITICAL", "code",
   kw=["FIXTURE", "COUNT", "OCCUPANCY", "IBC", "IPC", "WATER CLOSET", "LAVATORY"])


def get_rules_for_disciplines(disc_codes: set[str]) -> list[ConflictRule]:
    """Return rules that apply to the given set of disciplines present in the drawing set."""
    applicable = []
    for rule in CONFLICT_RULES.values():
        if not rule.enabled:
            continue
        # Rule applies if at least 2 of its disciplines are present (for cross-disc rules)
        # or if it's a single-discipline rule and that discipline is present
        overlap = set(rule.disciplines) & disc_codes
        if len(rule.disciplines) == 1 and overlap:
            applicable.append(rule)
        elif len(overlap) >= 2:
            applicable.append(rule)
        elif len(overlap) >= 1 and rule.detection_type == "code":
            applicable.append(rule)
    return applicable


def get_rule(rule_id: str) -> ConflictRule | None:
    return CONFLICT_RULES.get(rule_id)
