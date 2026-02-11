"""
150+ cross-discipline conflict detection rules for commercial construction.

Each rule defines:
  - ID: CR-XXX
  - Name and description
  - Disciplines involved (which sheet types to compare)
  - Severity: CRITICAL / MAJOR / MINOR / INFO
  - Detection method: what to look for in extracted entities
  - Auto-detectable: whether regex/logic can catch it or needs AI assist

Rules organized by CSI MasterFormat divisions and coordination categories.
A senior PM on a $50M+ commercial job would check every one of these.
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


# ── Rule Registry ─────────────────────────────────────────

CONFLICT_RULES: dict[str, ConflictRule] = {}

def _r(rule_id, name, desc, cat, discs, sev, det, auto=True, kw=None):
    """Shorthand to register a rule."""
    CONFLICT_RULES[rule_id] = ConflictRule(
        rule_id=rule_id, name=name, description=desc,
        category=cat, disciplines=discs, severity=sev,
        detection_type=det, auto_detectable=auto,
        keywords=kw or [], check_fn_name=f"check_{rule_id.lower().replace('-', '_')}",
    )


# ═══════════════════════════════════════════════════════════
#  STRUCTURAL / ARCHITECTURAL (CSI Divs 03-05)
# ═══════════════════════════════════════════════════════════

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

_r("CR-035", "Column grid mismatch between arch and structural",
   "Column grid lines on architectural plans don't align with structural foundation/framing plans.",
   "STR-ARCH", ["STR", "ARCH"], "CRITICAL", "dimension",
   kw=["GRID", "COLUMN", "GRID LINE", "OFFSET"])

_r("CR-036", "Slab edge condition missing at curtain wall",
   "No detail shown for slab edge/pour-back at curtain wall or storefront system.",
   "STR-ARCH", ["STR", "ARCH"], "MAJOR", "cross_ref",
   kw=["SLAB EDGE", "CURTAIN WALL", "STOREFRONT", "POUR-BACK"])

_r("CR-037", "Floor-to-floor height mismatch",
   "Architectural sections show different floor-to-floor height than structural framing plans.",
   "STR-ARCH", ["STR", "ARCH"], "CRITICAL", "dimension",
   kw=["FLOOR TO FLOOR", "FTF", "STORY HEIGHT"])

_r("CR-038", "Expansion joint not continuous",
   "Structural expansion joint not carried through architectural finishes, MEP systems, or roof.",
   "STR-ARCH", ["STR", "ARCH", "MECH"], "MAJOR", "cross_ref",
   kw=["EXPANSION JOINT", "SEISMIC", "CONTROL JOINT"])

_r("CR-039", "Steel connection detail not provided",
   "Structural plan shows connection that has no corresponding detail on detail sheets.",
   "STR", ["STR"], "MAJOR", "cross_ref",
   kw=["CONNECTION", "DETAIL", "MOMENT", "SHEAR TAB", "CLIP ANGLE"])

_r("CR-040", "Embed plate missing from foundation plan",
   "Steel column base plate shown on framing plan but no corresponding embed on foundation plan.",
   "STR", ["STR"], "CRITICAL", "cross_ref",
   kw=["EMBED", "BASE PLATE", "ANCHOR BOLT", "FOUNDATION"])

_r("CR-041", "Slab depression not on structural",
   "Architectural finish schedule shows depressed slab for tile but structural plan shows flat slab.",
   "STR-ARCH", ["STR", "ARCH"], "MAJOR", "cross_ref",
   kw=["DEPRESSION", "DEPRESSED SLAB", "TILE", "RECESS"])

_r("CR-042", "Roof slope direction conflicts with drain location",
   "Structural roof framing slope doesn't direct water toward roof drain locations shown on plumbing.",
   "STR-PLMB", ["STR", "PLMB"], "MAJOR", "cross_ref",
   kw=["ROOF DRAIN", "SLOPE", "CRICKET", "TAPERED"])

_r("CR-043", "Bearing wall removed by architectural revision",
   "Architectural revision removed or relocated a wall that is a bearing wall on structural plans.",
   "STR-ARCH", ["STR", "ARCH"], "CRITICAL", "cross_ref",
   kw=["BEARING WALL", "LOAD BEARING", "REVISION"])

_r("CR-044", "Concrete mix design not specified",
   "Structural notes reference concrete strength but no mix design spec section is listed.",
   "STR", ["STR"], "MINOR", "cross_ref",
   kw=["CONCRETE", "PSI", "MIX DESIGN", "03 30 00"])

_r("CR-045", "CMU reinforcement schedule missing",
   "CMU walls shown on architectural but no reinforcement schedule on structural drawings.",
   "STR-ARCH", ["STR", "ARCH"], "MAJOR", "cross_ref",
   kw=["CMU", "MASONRY", "REINFORCEMENT", "GROUT"])


# ═══════════════════════════════════════════════════════════
#  MEP CROSS-DISCIPLINE (CSI Divs 21-28)
# ═══════════════════════════════════════════════════════════

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

_r("CR-046", "Ceiling space stacking order not coordinated",
   "No ceiling coordination drawing showing vertical stacking of ducts, pipes, cable trays, sprinkler.",
   "MEP-ARCH", ["MECH", "PLMB", "ELEC", "FP", "ARCH"], "MAJOR", "cross_ref",
   kw=["CEILING", "COORDINATION", "STACKING", "PLENUM", "SECTION"])

_r("CR-047", "Hydronic pipe insulation clearance",
   "Insulated chilled water or hot water pipe shown with no allowance for insulation thickness.",
   "MECH", ["MECH"], "MAJOR", "dimension",
   kw=["INSULATION", "CHILLED WATER", "HOT WATER", "CLEARANCE"])

_r("CR-048", "Equipment access clearance insufficient",
   "Mechanical equipment doesn't have required service access clearance per manufacturer data.",
   "MECH-ARCH", ["MECH", "ARCH"], "MAJOR", "dimension",
   kw=["ACCESS", "SERVICE", "CLEARANCE", "FILTER", "COIL"])

_r("CR-049", "Exhaust duct termination near intake",
   "Exhaust air discharge within minimum separation distance from outdoor air intake.",
   "MECH", ["MECH"], "CRITICAL", "code",
   kw=["EXHAUST", "INTAKE", "LOUVER", "SEPARATION", "IMC"])

_r("CR-050", "Kitchen hood makeup air not shown",
   "Commercial kitchen exhaust hood shown but no dedicated makeup air unit or path indicated.",
   "MECH-ARCH", ["MECH", "ARCH"], "CRITICAL", "cross_ref",
   kw=["KITCHEN HOOD", "MAKEUP AIR", "EXHAUST", "MAU"])

_r("CR-051", "Duct liner vs exposed ductwork conflict",
   "Ductwork shown as exposed/architectural but also specified with internal liner.",
   "MECH-ARCH", ["MECH", "ARCH"], "MINOR", "cross_ref",
   kw=["DUCT LINER", "EXPOSED", "ARCHITECTURAL DUCT"])

_r("CR-052", "VAV box above inaccessible ceiling",
   "VAV box or control device located above hard/inaccessible ceiling with no access panel shown.",
   "MECH-ARCH", ["MECH", "ARCH"], "MAJOR", "cross_ref",
   kw=["VAV", "ACCESS PANEL", "HARD CEILING", "GWB CEILING"])

_r("CR-053", "Refrigerant line set routing not shown",
   "Split system or VRF outdoor unit shown but no refrigerant piping route to indoor units.",
   "MECH", ["MECH"], "MAJOR", "cross_ref",
   kw=["REFRIGERANT", "LINE SET", "VRF", "SPLIT SYSTEM"])

_r("CR-054", "Condensate drain routing missing",
   "HVAC equipment with condensate drain shown but no routing to nearest plumbing connection.",
   "MECH-PLMB", ["MECH", "PLMB"], "MINOR", "cross_ref",
   kw=["CONDENSATE", "DRAIN", "P-TRAP", "AIR GAP"])

_r("CR-055", "Return air path through rated wall",
   "Return air plenum path crosses fire-rated wall without fire/smoke damper indicated.",
   "MECH-ARCH", ["MECH", "ARCH"], "CRITICAL", "cross_ref",
   kw=["RETURN AIR", "RATED WALL", "FIRE DAMPER", "SMOKE DAMPER"])

_r("CR-056", "Mechanical screen not on structural",
   "Rooftop mechanical screen wall shown on architectural but no structural support indicated.",
   "MECH-STR", ["MECH", "STR", "ARCH"], "MAJOR", "cross_ref",
   kw=["SCREEN", "MECHANICAL SCREEN", "ROOFTOP", "DUNNAGE"])


# ═══════════════════════════════════════════════════════════
#  PLUMBING (CSI Div 22)
# ═══════════════════════════════════════════════════════════

_r("CR-016", "Interior plumbing vs site utilities",
   "Interior plumbing waste/storm connections don't align with site utility stub locations.",
   "PLMB-CIV", ["PLMB", "CIV"], "MAJOR", "cross_ref",
   kw=["INVERT", "STUB", "CONNECTION", "SANITARY", "STORM"])

_r("CR-019", "Fixture count vs code requirements",
   "Plumbing fixture count doesn't meet code minimum for the building occupancy and occupant load.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "CRITICAL", "code",
   kw=["FIXTURE", "COUNT", "OCCUPANCY", "IBC", "IPC", "WATER CLOSET", "LAVATORY"])

_r("CR-057", "Water heater sizing vs fixture count",
   "Water heater capacity doesn't match calculated demand from fixture unit count.",
   "PLMB", ["PLMB"], "MAJOR", "equipment",
   kw=["WATER HEATER", "GPM", "BTU", "FIXTURE UNIT", "DEMAND"])

_r("CR-058", "Grease trap sizing not shown",
   "Food service area shown but no grease interceptor sizing calculation or detail.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "CRITICAL", "code",
   kw=["GREASE TRAP", "GREASE INTERCEPTOR", "FOOD SERVICE", "KITCHEN"])

_r("CR-059", "Backflow preventer location conflicts",
   "Backflow preventer in utility room but no floor drain within 2' per code.",
   "PLMB", ["PLMB"], "MAJOR", "code",
   kw=["BACKFLOW", "RPZ", "FLOOR DRAIN", "DCVA"])

_r("CR-060", "Plumbing cleanout access blocked",
   "Plumbing cleanout shown behind fixed casework or in inaccessible location.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "MINOR", "cross_ref",
   kw=["CLEANOUT", "ACCESS", "CASEWORK"])

_r("CR-061", "Roof drain size vs drainage area",
   "Roof drain size doesn't match calculated drainage area per plumbing code.",
   "PLMB", ["PLMB"], "MAJOR", "equipment",
   kw=["ROOF DRAIN", "DRAINAGE AREA", "LEADER", "DOWNSPOUT"])

_r("CR-062", "Gas piping near ignition sources",
   "Natural gas piping routed near or through spaces with ignition sources without protection.",
   "PLMB-MECH", ["PLMB", "MECH"], "CRITICAL", "code",
   kw=["GAS PIPE", "NATURAL GAS", "IGNITION", "IFGC"])

_r("CR-063", "Waste pipe slope insufficient",
   "Horizontal waste pipe shown without adequate slope (1/4\" per foot for 3\" and smaller).",
   "PLMB", ["PLMB"], "MAJOR", "dimension",
   kw=["SLOPE", "WASTE", "GRADE", "INVERT", "1/4"])

_r("CR-064", "ADA lavatory clearance not shown",
   "Accessible lavatory shown but no insulation kit or pipe protection detail per ADA.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "MAJOR", "code",
   kw=["ADA", "LAVATORY", "INSULATION KIT", "KNEE CLEARANCE"])

_r("CR-065", "Water hammer arrestor locations missing",
   "Quick-closing valves (flush valves, solenoids) shown without water hammer arrestors.",
   "PLMB", ["PLMB"], "MINOR", "code",
   kw=["WATER HAMMER", "ARRESTOR", "FLUSH VALVE", "SOLENOID"])


# ═══════════════════════════════════════════════════════════
#  ELECTRICAL (CSI Divs 26-27)
# ═══════════════════════════════════════════════════════════

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

_r("CR-031", "Lighting fixture type vs spec section",
   "Lighting fixture type on drawings doesn't match fixture schedule or spec section description.",
   "ELEC", ["ELEC"], "MINOR", "cross_ref",
   kw=["FIXTURE", "TYPE", "SCHEDULE", "LIGHTING"])

_r("CR-032", "Receptacle count vs NEC minimums",
   "Receptacle count in a space falls below NEC minimum requirements for the occupancy type.",
   "ELEC", ["ELEC", "ARCH"], "MAJOR", "code",
   kw=["RECEPTACLE", "NEC", "MINIMUM", "COUNT", "SPACING"])

_r("CR-066", "Wire size vs circuit length",
   "Conductor size may not handle voltage drop over the circuit run length (max 3% branch, 5% total).",
   "ELEC", ["ELEC"], "MAJOR", "dimension",
   kw=["WIRE SIZE", "VOLTAGE DROP", "AWG", "CIRCUIT LENGTH"])

_r("CR-067", "Conduit fill exceeds NEC 40%",
   "Conduit shown with conductor count that exceeds NEC Chapter 9 conduit fill limits.",
   "ELEC", ["ELEC"], "MAJOR", "code",
   kw=["CONDUIT FILL", "NEC", "CHAPTER 9", "RACEWAY"])

_r("CR-068", "Working clearance at electrical equipment",
   "Electrical equipment doesn't have required NEC 110.26 working clearance (36\" min depth).",
   "ELEC-ARCH", ["ELEC", "ARCH"], "CRITICAL", "code",
   kw=["WORKING CLEARANCE", "NEC 110.26", "36 INCH", "PANEL"])

_r("CR-069", "Emergency lighting coverage gaps",
   "Emergency/egress lighting doesn't provide 1 fc average along exit path per IBC/NFPA 101.",
   "ELEC-ARCH", ["ELEC", "ARCH"], "CRITICAL", "code",
   kw=["EMERGENCY LIGHTING", "EGRESS", "1 FC", "EXIT"])

_r("CR-070", "Exit sign location vs code",
   "Exit signs not shown at required locations per IBC (changes of direction, exit doors, corridors).",
   "ELEC-ARCH", ["ELEC", "ARCH"], "CRITICAL", "code",
   kw=["EXIT SIGN", "IBC", "EGRESS", "DIRECTION"])

_r("CR-071", "Transformer vault ventilation",
   "Indoor transformer room doesn't show required ventilation per NEC 450.45.",
   "ELEC-MECH", ["ELEC", "MECH"], "MAJOR", "code",
   kw=["TRANSFORMER", "VAULT", "VENTILATION", "NEC 450"])

_r("CR-072", "Electrical room door swing direction",
   "Electrical room door swings into room instead of outward per NEC 110.26(C)(2).",
   "ELEC-ARCH", ["ELEC", "ARCH"], "MAJOR", "code",
   kw=["ELECTRICAL ROOM", "DOOR SWING", "NEC 110.26", "OUTWARD"])

_r("CR-073", "Dedicated circuit for mechanical equipment",
   "Mechanical equipment shown without dedicated disconnect or circuit on panel schedule.",
   "ELEC-MECH", ["ELEC", "MECH"], "MAJOR", "cross_ref",
   kw=["DISCONNECT", "DEDICATED", "CIRCUIT", "EQUIPMENT"])

_r("CR-074", "Outdoor receptacle GFCI protection",
   "Outdoor or wet location receptacles shown without GFCI protection per NEC.",
   "ELEC", ["ELEC"], "MAJOR", "code",
   kw=["GFCI", "OUTDOOR", "WET LOCATION", "WEATHER PROOF"])

_r("CR-075", "Lightning protection not coordinated",
   "Lightning protection system shown on architectural roof plan but not on electrical.",
   "ELEC-ARCH", ["ELEC", "ARCH"], "MINOR", "cross_ref",
   kw=["LIGHTNING", "PROTECTION", "GROUND", "AIR TERMINAL"])

_r("CR-076", "Feeder size vs distance to panel",
   "Sub-panel feeder conductor size may be undersized for the distance from distribution panel.",
   "ELEC", ["ELEC"], "MAJOR", "dimension",
   kw=["FEEDER", "SUB-PANEL", "DISTANCE", "CONDUCTOR", "AMPACITY"])


# ═══════════════════════════════════════════════════════════
#  FIRE PROTECTION (CSI Div 21)
# ═══════════════════════════════════════════════════════════

_r("CR-005", "Sprinkler head vs ceiling type",
   "Sprinkler head type (pendent/upright/concealed) doesn't match ceiling type at that location.",
   "FP-ARCH", ["FP", "ARCH"], "MAJOR", "cross_ref",
   kw=["SPRINKLER", "HEAD", "CEILING", "CONCEALED", "PENDENT", "UPRIGHT"])

_r("CR-011", "Door swing vs sprinkler coverage",
   "Door swing arc interferes with sprinkler head coverage pattern or head location.",
   "FP-ARCH", ["FP", "ARCH"], "MINOR", "cross_ref",
   kw=["DOOR", "SWING", "SPRINKLER", "HEAD", "COVERAGE"])

_r("CR-021", "Penetration through rated assembly",
   "MEP penetration through fire-rated wall or floor assembly without noted firestopping.",
   "FP-ARCH", ["MECH", "PLMB", "ELEC", "ARCH"], "CRITICAL", "cross_ref",
   kw=["PENETRATION", "RATED", "FIRESTOP", "FIRE WALL", "RATED ASSEMBLY"])

_r("CR-077", "Sprinkler head spacing exceeds NFPA 13",
   "Sprinkler head spacing exceeds maximum per NFPA 13 for the hazard classification.",
   "FP", ["FP"], "CRITICAL", "code",
   kw=["SPACING", "NFPA 13", "LIGHT HAZARD", "ORDINARY HAZARD"])

_r("CR-078", "Sprinkler riser room size",
   "Fire sprinkler riser room undersized for the equipment and required working clearance.",
   "FP-ARCH", ["FP", "ARCH"], "MAJOR", "dimension",
   kw=["RISER ROOM", "SPRINKLER", "CLEARANCE"])

_r("CR-079", "Standpipe hose connection location",
   "Standpipe hose connections not within required travel distance in stairwells.",
   "FP-ARCH", ["FP", "ARCH"], "CRITICAL", "code",
   kw=["STANDPIPE", "HOSE CONNECTION", "STAIRWELL", "NFPA 14"])

_r("CR-080", "Fire pump room requirements",
   "Fire pump room missing required features (drain, ventilation, lighting, 2-hour rated enclosure).",
   "FP-ARCH", ["FP", "ARCH", "MECH", "ELEC"], "CRITICAL", "code",
   kw=["FIRE PUMP", "RATED", "DRAIN", "VENTILATION"])

_r("CR-081", "Sprinkler coverage in concealed spaces",
   "Concealed space above ceiling not addressed for sprinkler protection per NFPA 13.",
   "FP-ARCH", ["FP", "ARCH"], "CRITICAL", "code",
   kw=["CONCEALED SPACE", "ABOVE CEILING", "NFPA 13", "COMBUSTIBLE"])

_r("CR-082", "Kitchen hood suppression system",
   "Commercial kitchen hood shown without dedicated fire suppression system (NFPA 96/UL 300).",
   "FP-ARCH", ["FP", "ARCH", "MECH"], "CRITICAL", "code",
   kw=["KITCHEN HOOD", "SUPPRESSION", "NFPA 96", "ANSUL", "UL 300"])

_r("CR-083", "Fire department connection location",
   "FDC not located within required distance from fire hydrant or not accessible from fire lane.",
   "FP-CIV", ["FP", "CIV"], "CRITICAL", "code",
   kw=["FDC", "FIRE DEPARTMENT", "CONNECTION", "HYDRANT", "FIRE LANE"])


# ═══════════════════════════════════════════════════════════
#  FIRE ALARM (CSI Div 28)
# ═══════════════════════════════════════════════════════════

_r("CR-030", "Fire alarm device spacing vs NFPA 72",
   "Fire alarm notification or detection device spacing exceeds NFPA 72 maximums.",
   "FA", ["FA"], "CRITICAL", "code",
   kw=["NFPA 72", "SPACING", "DETECTOR", "HORN", "STROBE", "NOTIFICATION"])

_r("CR-084", "Duct detector locations missing",
   "Supply ducts over 2000 CFM have no duct smoke detector shown per IMC/NFPA.",
   "FA-MECH", ["FA", "MECH"], "CRITICAL", "code",
   kw=["DUCT DETECTOR", "SMOKE DETECTOR", "2000 CFM", "IMC"])

_r("CR-085", "ADA-compliant notification devices",
   "Notification appliances in public/common areas don't include visual (strobe) per ADA/NFPA 72.",
   "FA", ["FA"], "MAJOR", "code",
   kw=["ADA", "STROBE", "VISUAL", "NOTIFICATION", "NFPA 72"])

_r("CR-086", "Elevator recall interface not shown",
   "No fire alarm interface shown for elevator recall (Phase I/Phase II) per ASME/NFPA.",
   "FA-ELEC", ["FA", "ELEC"], "CRITICAL", "code",
   kw=["ELEVATOR", "RECALL", "PHASE I", "PHASE II", "SHUNT TRIP"])

_r("CR-087", "Smoke detector in elevator lobby",
   "Elevator lobby doesn't show required smoke detector for elevator recall.",
   "FA-ARCH", ["FA", "ARCH"], "CRITICAL", "code",
   kw=["ELEVATOR LOBBY", "SMOKE DETECTOR", "RECALL"])

_r("CR-088", "FACP location and annunciator",
   "Fire alarm control panel not at main entrance or remote annunciator not shown.",
   "FA-ARCH", ["FA", "ARCH"], "MAJOR", "code",
   kw=["FACP", "ANNUNCIATOR", "MAIN ENTRANCE", "PANEL"])

_r("CR-089", "Addressable device count vs loop capacity",
   "Number of addressable devices on a single SLC loop exceeds panel capacity.",
   "FA", ["FA"], "MAJOR", "equipment",
   kw=["ADDRESSABLE", "SLC", "LOOP", "CAPACITY", "DEVICE COUNT"])


# ═══════════════════════════════════════════════════════════
#  TELECOM / LOW VOLTAGE (CSI Div 27)
# ═══════════════════════════════════════════════════════════

_r("CR-033", "Data outlet count vs furniture plan",
   "Data/telecom outlet locations don't align with furniture plan workstation locations.",
   "TECH-ARCH", ["TECH", "ARCH"], "MINOR", "cross_ref",
   kw=["DATA", "OUTLET", "FURNITURE", "WORKSTATION"])

_r("CR-034", "Low-voltage pathway sizing",
   "Cable tray or conduit fill exceeds 40% for low-voltage cabling per pathway standards.",
   "TECH", ["TECH"], "MAJOR", "dimension",
   kw=["CABLE TRAY", "FILL", "J-HOOK", "PATHWAY", "CONDUIT"])

_r("CR-090", "Telecom room size per TIA-569",
   "Telecom/data room undersized per TIA-569 standard for the floor area served.",
   "TECH-ARCH", ["TECH", "ARCH"], "MAJOR", "code",
   kw=["TELECOM ROOM", "MDF", "IDF", "TIA-569"])

_r("CR-091", "Backbone pathway between telecom rooms",
   "No conduit or pathway shown between MDF and IDF rooms for backbone cabling.",
   "TECH", ["TECH"], "MAJOR", "cross_ref",
   kw=["BACKBONE", "MDF", "IDF", "CONDUIT", "PATHWAY"])

_r("CR-092", "Wireless AP locations vs coverage",
   "Wireless access point locations don't provide adequate coverage for the floor area.",
   "TECH-ARCH", ["TECH", "ARCH"], "MINOR", "equipment",
   kw=["WIRELESS", "AP", "ACCESS POINT", "WIFI", "COVERAGE"])

_r("CR-093", "Security camera coverage gaps",
   "Security camera locations have blind spots at building entries, parking, or critical areas.",
   "TECH-ARCH", ["TECH", "ARCH"], "MINOR", "cross_ref",
   kw=["CAMERA", "CCTV", "SECURITY", "COVERAGE", "BLIND SPOT"])

_r("CR-094", "AV conduit to conference rooms",
   "Conference rooms don't show conduit for AV connectivity (display, camera, ceiling mic).",
   "TECH-ARCH", ["TECH", "ARCH"], "MINOR", "cross_ref",
   kw=["AV", "CONFERENCE", "DISPLAY", "CONDUIT"])


# ═══════════════════════════════════════════════════════════
#  ENVELOPE / WATERPROOFING (CSI Div 07)
# ═══════════════════════════════════════════════════════════

_r("CR-095", "Window flashing detail missing",
   "Window installation shown but no head/sill/jamb flashing detail provided.",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["FLASHING", "WINDOW", "HEAD", "SILL", "JAMB"])

_r("CR-096", "Roof penetration waterproofing detail",
   "Roof penetration (mechanical curb, pipe, conduit) shown without waterproofing detail.",
   "ARCH-MECH", ["ARCH", "MECH", "PLMB", "ELEC"], "MAJOR", "cross_ref",
   kw=["ROOF PENETRATION", "FLASHING", "CURB", "PITCH POCKET"])

_r("CR-097", "Below-grade waterproofing not shown",
   "Below-grade wall or slab has no waterproofing membrane or drainage detail.",
   "ARCH-STR", ["ARCH", "STR"], "CRITICAL", "cross_ref",
   kw=["WATERPROOFING", "BELOW GRADE", "MEMBRANE", "FOUNDATION"])

_r("CR-098", "Exterior wall air/vapor barrier continuity",
   "Air barrier or vapor retarder not continuous at transitions (wall to roof, wall to slab, window).",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["AIR BARRIER", "VAPOR BARRIER", "CONTINUITY", "TRANSITION"])

_r("CR-099", "Expansion joint cover at roof",
   "Building expansion joint at roof level has no cover or counter-flashing detail.",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["EXPANSION JOINT", "ROOF", "COVER", "COUNTER-FLASHING"])

_r("CR-100", "Parapet cap flashing",
   "Parapet shown without cap flashing or coping detail to prevent water entry.",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["PARAPET", "CAP FLASHING", "COPING"])


# ═══════════════════════════════════════════════════════════
#  CIVIL / SITE (CSI Divs 31-33)
# ═══════════════════════════════════════════════════════════

_r("CR-009", "Foundation vs utility conflict",
   "Building foundation or footing conflicts with underground utility routing.",
   "STR-CIV", ["STR", "CIV"], "CRITICAL", "cross_ref",
   kw=["FOUNDATION", "FOOTING", "UTILITY", "UNDERGROUND", "PIPE"])

_r("CR-015", "Finish floor vs site grade",
   "Interior finish floor elevation doesn't maintain required relationship to exterior site grade.",
   "ARCH-CIV", ["ARCH", "CIV"], "MAJOR", "dimension",
   kw=["FFE", "GRADE", "ELEVATION", "FLOOR", "SITE"])

_r("CR-101", "ADA parking count and access route",
   "Accessible parking count doesn't meet code or accessible route to building entry not shown.",
   "CIV-ARCH", ["CIV", "ARCH"], "CRITICAL", "code",
   kw=["ADA", "PARKING", "ACCESSIBLE", "RAMP", "VAN"])

_r("CR-102", "Fire lane width and access",
   "Fire lane width less than 20' or turning radius insufficient for fire apparatus per IFC.",
   "CIV", ["CIV"], "CRITICAL", "code",
   kw=["FIRE LANE", "20 FEET", "TURNING RADIUS", "IFC", "ACCESS"])

_r("CR-103", "Stormwater detention calculation",
   "Stormwater detention/retention volume doesn't match required calculation for impervious area.",
   "CIV", ["CIV"], "MAJOR", "equipment",
   kw=["DETENTION", "RETENTION", "STORMWATER", "IMPERVIOUS", "BMP"])

_r("CR-104", "Utility easement conflict with building",
   "Building footprint or foundation encroaches on recorded utility or drainage easement.",
   "CIV-ARCH", ["CIV", "ARCH"], "CRITICAL", "cross_ref",
   kw=["EASEMENT", "SETBACK", "ENCROACH", "UTILITY"])

_r("CR-105", "Sanitary sewer capacity at connection",
   "Building sewer connection point doesn't have capacity at the municipal main per utility letter.",
   "CIV-PLMB", ["CIV", "PLMB"], "CRITICAL", "equipment",
   kw=["SANITARY", "SEWER", "CAPACITY", "CONNECTION", "MUNICIPAL"])

_r("CR-106", "Water main size for fire flow",
   "Water main size at building connection may not provide required fire flow per ISO calculation.",
   "CIV-FP", ["CIV", "FP"], "CRITICAL", "equipment",
   kw=["WATER MAIN", "FIRE FLOW", "GPM", "PSI", "HYDRANT"])

_r("CR-107", "Grading direction at building perimeter",
   "Site grading doesn't slope away from building at minimum 5% for first 10 feet per IBC.",
   "CIV-ARCH", ["CIV", "ARCH"], "MAJOR", "code",
   kw=["GRADING", "SLOPE", "PERIMETER", "5 PERCENT", "DRAINAGE"])

_r("CR-108", "Dumpster pad location vs building",
   "Dumpster enclosure location conflicts with building windows, intakes, or minimum setbacks.",
   "CIV-ARCH", ["CIV", "ARCH"], "MINOR", "cross_ref",
   kw=["DUMPSTER", "ENCLOSURE", "SETBACK", "SCREEN"])

_r("CR-109", "Loading dock turning radius",
   "Loading dock approach angle or turning radius insufficient for WB-67 truck per AASHTO.",
   "CIV-ARCH", ["CIV", "ARCH"], "MAJOR", "dimension",
   kw=["LOADING DOCK", "TURNING RADIUS", "WB-67", "TRUCK"])

_r("CR-110", "Transformer pad location vs building",
   "Pad-mounted transformer too close to building openings or in area without utility access.",
   "CIV-ELEC", ["CIV", "ELEC"], "MAJOR", "cross_ref",
   kw=["TRANSFORMER", "PAD MOUNT", "CLEARANCE", "UTILITY ACCESS"])


# ═══════════════════════════════════════════════════════════
#  ARCHITECTURE / CODE (CSI Divs 06-12)
# ═══════════════════════════════════════════════════════════

_r("CR-025", "Egress width vs code",
   "Exit corridor or stair width falls below code-required minimum for the occupant load.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["EGRESS", "EXIT", "CORRIDOR", "WIDTH", "OCCUPANT", "IBC"])

_r("CR-006", "Diffuser location vs ceiling layout",
   "HVAC diffuser or return grille location conflicts with ceiling grid, light fixture, or cloud.",
   "MECH-ARCH", ["MECH", "ARCH"], "MINOR", "cross_ref",
   kw=["DIFFUSER", "GRILLE", "CEILING", "GRID", "LIGHT"])

_r("CR-013", "Spec section missing from drawings",
   "Drawing references a CSI spec section that is not included in the project manual.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB", "FP"], "MAJOR", "cross_ref")

_r("CR-111", "Dead-end corridor exceeds 20 feet",
   "Dead-end corridor length exceeds 20' maximum per IBC 1020.4.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["DEAD END", "CORRIDOR", "20 FEET", "IBC 1020"])

_r("CR-112", "Two exits required but only one shown",
   "Occupant load exceeds 49 (or area > 75' common path) but only one exit provided.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["TWO EXITS", "OCCUPANT LOAD", "COMMON PATH", "IBC 1006"])

_r("CR-113", "Travel distance exceeds maximum",
   "Travel distance to nearest exit exceeds IBC maximum for the occupancy type (200'/250'/300').",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["TRAVEL DISTANCE", "EXIT", "MAXIMUM", "IBC 1017"])

_r("CR-114", "Exit separation less than 1/2 diagonal",
   "Two required exits are less than 1/2 the diagonal distance apart per IBC 1007.1.1.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["EXIT SEPARATION", "DIAGONAL", "1/2", "IBC 1007"])

_r("CR-115", "ADA door clearance at hardware side",
   "Accessible door doesn't have 18\" maneuvering clearance at pull side of door per ICC A117.1.",
   "ARCH", ["ARCH"], "MAJOR", "code",
   kw=["ADA", "MANEUVERING", "CLEARANCE", "18 INCH", "PULL SIDE"])

_r("CR-116", "ADA restroom layout non-compliant",
   "Accessible restroom doesn't meet turning radius, grab bar, or fixture clearance per ADA.",
   "ARCH-PLMB", ["ARCH", "PLMB"], "CRITICAL", "code",
   kw=["ADA", "RESTROOM", "TURNING RADIUS", "GRAB BAR", "60 INCH"])

_r("CR-117", "Stair riser/tread non-uniform",
   "Stair riser height or tread depth varies or exceeds IBC maximums (7\" riser, 11\" tread).",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["STAIR", "RISER", "TREAD", "7 INCH", "11 INCH", "IBC 1011"])

_r("CR-118", "Handrail extension missing",
   "Handrail at stairs doesn't extend 12\" beyond top riser and one tread depth beyond bottom.",
   "ARCH", ["ARCH"], "MAJOR", "code",
   kw=["HANDRAIL", "EXTENSION", "12 INCH", "IBC 1014"])

_r("CR-119", "Guard rail height at elevated surface",
   "Guard rail at balcony, mezzanine, or open floor less than 42\" per IBC 1015.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["GUARD", "RAIL", "42 INCH", "BALCONY", "MEZZANINE", "IBC 1015"])

_r("CR-120", "Rated wall not shown to deck",
   "Fire-rated wall partition shown but not indicated as extending to underside of structure above.",
   "ARCH", ["ARCH"], "CRITICAL", "cross_ref",
   kw=["RATED WALL", "DECK", "STRUCTURE", "SLAB", "CONTINUOUS"])

_r("CR-121", "Smoke compartment size exceeds 22,500 SF",
   "Smoke compartment in I-2 or I-3 occupancy exceeds 22,500 SF per IBC 407/408.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["SMOKE COMPARTMENT", "22500", "I-2", "HEALTHCARE"])

_r("CR-122", "Occupancy separation not provided",
   "Mixed occupancies without required fire separation per IBC Table 508.4.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["OCCUPANCY SEPARATION", "MIXED USE", "IBC 508", "FIRE BARRIER"])

_r("CR-123", "Elevator shaft rated enclosure",
   "Elevator shaft not shown with required rated enclosure per IBC 713.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["ELEVATOR SHAFT", "RATED", "ENCLOSURE", "IBC 713", "HOISTWAY"])

_r("CR-124", "Corridor rating vs construction type",
   "Corridor fire rating doesn't match requirement for the occupancy and construction type.",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["CORRIDOR", "RATED", "1 HOUR", "0 HOUR", "IBC 1020"])

_r("CR-125", "Room number mismatch between plan and schedule",
   "Room numbers on floor plan don't match room finish schedule or door schedule entries.",
   "ARCH", ["ARCH"], "MINOR", "cross_ref",
   kw=["ROOM NUMBER", "SCHEDULE", "FINISH", "DOOR"])

_r("CR-126", "Ceiling height less than 7'-6\" minimum",
   "Room shown with finished ceiling height below IBC minimum 7'-6\" (or 7'-0\" for bathrooms).",
   "ARCH", ["ARCH"], "MAJOR", "code",
   kw=["CEILING HEIGHT", "7'-6\"", "MINIMUM", "IBC 1208"])

_r("CR-127", "Window area less than 8% for natural light",
   "Habitable room window area less than 8% of floor area per IBC 1205 (if no mechanical ventilation).",
   "ARCH", ["ARCH"], "MINOR", "code",
   kw=["NATURAL LIGHT", "WINDOW", "8 PERCENT", "IBC 1205"])

_r("CR-128", "Door schedule conflicts with plan",
   "Door on plan shows different size, type, or hardware than what's listed in door schedule.",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["DOOR SCHEDULE", "HARDWARE", "SIZE", "TYPE"])

_r("CR-129", "Finish schedule references missing material",
   "Room finish schedule lists a finish code that has no corresponding specification section.",
   "ARCH", ["ARCH"], "MINOR", "cross_ref",
   kw=["FINISH SCHEDULE", "SPECIFICATION", "MATERIAL"])

_r("CR-130", "Acoustical rating at wall not specified",
   "Wall between noise-sensitive spaces has no STC rating indicated per occupancy requirements.",
   "ARCH", ["ARCH"], "MAJOR", "cross_ref",
   kw=["STC", "ACOUSTICAL", "SOUND", "WALL RATING"])


# ═══════════════════════════════════════════════════════════
#  GENERAL COORDINATION
# ═══════════════════════════════════════════════════════════

_r("CR-131", "Drawing scale mismatch between sheets",
   "Same area shown at different scales on different sheets without clear notation.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB"], "MINOR", "cross_ref",
   kw=["SCALE", "MISMATCH", "ENLARGED"])

_r("CR-132", "Revision cloud without revision number",
   "Revision cloud on drawing with no corresponding revision number, date, or description in block.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB", "FP", "FA"], "MINOR", "cross_ref",
   kw=["REVISION", "CLOUD", "DELTA", "REVISION BLOCK"])

_r("CR-133", "North arrow inconsistent between sheets",
   "North arrow orientation varies between sheets for the same building.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB"], "MINOR", "cross_ref",
   kw=["NORTH ARROW", "ORIENTATION"])

_r("CR-134", "Drawing not at listed scale when printed",
   "Sheet note says 'Do Not Scale' but bar scale doesn't match listed scale on title block.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB"], "INFO", "cross_ref",
   kw=["BAR SCALE", "DO NOT SCALE", "TITLE BLOCK"])

_r("CR-135", "Abbreviation used but not in legend",
   "Abbreviation or symbol appears on drawings but isn't defined in the abbreviation legend.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB"], "INFO", "cross_ref",
   kw=["ABBREVIATION", "LEGEND", "SYMBOL"])

_r("CR-136", "General note conflicts with detail",
   "General note on first sheet contradicts specific detail or dimension elsewhere in set.",
   "COORDINATION", ["ARCH", "STR", "MECH", "ELEC", "PLMB"], "MAJOR", "cross_ref",
   kw=["GENERAL NOTE", "CONFLICT", "CONTRADICTION"])


# ═══════════════════════════════════════════════════════════
#  ELEVATOR / CONVEYING SYSTEMS (CSI Div 14)
# ═══════════════════════════════════════════════════════════

_r("CR-137", "Elevator pit depth insufficient",
   "Elevator pit depth shown doesn't match manufacturer requirements for the elevator type.",
   "ARCH-STR", ["ARCH", "STR"], "CRITICAL", "dimension",
   kw=["ELEVATOR PIT", "DEPTH", "HYDRAULIC", "TRACTION"])

_r("CR-138", "Machine room ventilation missing",
   "Elevator machine room has no ventilation or cooling shown to maintain temperature limits.",
   "ARCH-MECH", ["ARCH", "MECH"], "MAJOR", "cross_ref",
   kw=["MACHINE ROOM", "VENTILATION", "ELEVATOR", "TEMPERATURE"])

_r("CR-139", "Elevator electrical requirements",
   "Elevator feeder size or disconnect doesn't match manufacturer's electrical requirements.",
   "ELEC", ["ELEC"], "MAJOR", "equipment",
   kw=["ELEVATOR", "FEEDER", "DISCONNECT", "CONTROLLER"])

_r("CR-140", "Cab interior dimensions vs ADA",
   "Elevator cab interior dimensions don't meet ADA/A117.1 minimum (80\" depth, 68\" width).",
   "ARCH", ["ARCH"], "CRITICAL", "code",
   kw=["ELEVATOR CAB", "ADA", "DIMENSION", "80 INCH", "68 INCH"])


# ═══════════════════════════════════════════════════════════
#  SPECIALTIES / MISCELLANEOUS
# ═══════════════════════════════════════════════════════════

_r("CR-141", "Loading capacity at mezzanine/storage",
   "Floor loading shown on arch plans doesn't match structural design load at mezzanine or storage.",
   "STR-ARCH", ["STR", "ARCH"], "CRITICAL", "dimension",
   kw=["FLOOR LOAD", "MEZZANINE", "STORAGE", "PSF", "LIVE LOAD"])

_r("CR-142", "Toilet partition type vs wet area",
   "Toilet partitions in wet area specified as standard instead of moisture-resistant type.",
   "ARCH", ["ARCH"], "MINOR", "cross_ref",
   kw=["TOILET PARTITION", "WET AREA", "MOISTURE", "PHENOLIC"])

_r("CR-143", "Fire extinguisher cabinet locations",
   "Fire extinguisher cabinets not within required travel distance per IFC (75' max).",
   "ARCH", ["ARCH"], "MAJOR", "code",
   kw=["FIRE EXTINGUISHER", "CABINET", "75 FEET", "TRAVEL DISTANCE", "IFC"])

_r("CR-144", "Signage plan not coordinated",
   "Room signage locations on architectural don't match ADA tactile/braille sign requirements.",
   "ARCH", ["ARCH"], "MINOR", "code",
   kw=["SIGNAGE", "ADA", "TACTILE", "BRAILLE", "LATCH SIDE"])

_r("CR-145", "Roof access requirements",
   "Rooftop equipment shown but no permanent roof access (hatch, ships ladder, or stair) provided.",
   "ARCH-MECH", ["ARCH", "MECH"], "MAJOR", "code",
   kw=["ROOF ACCESS", "HATCH", "LADDER", "OSHA"])

_r("CR-146", "Fall protection at roof edge",
   "Rooftop equipment within 6' of roof edge with no parapet or fall protection system shown.",
   "ARCH-MECH", ["ARCH", "MECH"], "CRITICAL", "code",
   kw=["FALL PROTECTION", "ROOF EDGE", "PARAPET", "OSHA", "GUARDRAIL"])

_r("CR-147", "Seismic bracing for MEP systems",
   "MEP systems in seismic design category D or higher without noted seismic bracing details.",
   "MEP-STR", ["MECH", "PLMB", "ELEC", "FP", "STR"], "CRITICAL", "code",
   kw=["SEISMIC", "BRACING", "SDC", "ASCE 7", "IBC 1613"])

_r("CR-148", "Emergency eyewash/shower locations",
   "Hazardous material storage or battery room shown without emergency eyewash/shower per OSHA.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "CRITICAL", "code",
   kw=["EYEWASH", "SHOWER", "HAZARDOUS", "BATTERY ROOM", "OSHA"])

_r("CR-149", "Generator fuel storage not shown",
   "Emergency generator shown but no fuel storage tank, day tank, or fuel piping indicated.",
   "ELEC-MECH", ["ELEC", "MECH"], "MAJOR", "cross_ref",
   kw=["GENERATOR", "FUEL", "DIESEL", "DAY TANK", "STORAGE"])

_r("CR-150", "Photovoltaic system structural loading",
   "Rooftop solar array shown but structural loading not addressed on roof framing plan.",
   "STR-ELEC", ["STR", "ELEC"], "MAJOR", "cross_ref",
   kw=["SOLAR", "PHOTOVOLTAIC", "PV", "ROOF LOAD", "BALLAST"])

_r("CR-151", "EV charging infrastructure",
   "Parking shown with EV-ready spaces but no conduit, panel capacity, or transformer sizing.",
   "ELEC-CIV", ["ELEC", "CIV"], "MAJOR", "code",
   kw=["EV CHARGING", "ELECTRIC VEHICLE", "CONDUIT", "LEVEL 2"])

_r("CR-152", "Energy code compliance path",
   "Building envelope, lighting, or HVAC doesn't clearly show compliance path per IECC/ASHRAE 90.1.",
   "ARCH-MECH-ELEC", ["ARCH", "MECH", "ELEC"], "MAJOR", "code",
   kw=["ENERGY CODE", "IECC", "ASHRAE 90.1", "COMcheck", "COMPLIANCE"])

_r("CR-153", "Plumbing fixture accessibility",
   "Not all required accessible plumbing fixtures shown (drinking fountain hi-lo, accessible urinal).",
   "PLMB-ARCH", ["PLMB", "ARCH"], "MAJOR", "code",
   kw=["ACCESSIBLE", "DRINKING FOUNTAIN", "HI-LO", "ADA"])

_r("CR-154", "Mechanical vibration isolation",
   "Large mechanical equipment (AHU, chiller, pump) shown without vibration isolation details.",
   "MECH-STR", ["MECH", "STR"], "MAJOR", "cross_ref",
   kw=["VIBRATION", "ISOLATION", "SPRING", "INERTIA BASE", "AHU"])

_r("CR-155", "Daylighting controls required",
   "Spaces with qualifying sidelighting/toplighting don't show required automatic daylighting controls.",
   "ELEC-ARCH", ["ELEC", "ARCH"], "MINOR", "code",
   kw=["DAYLIGHTING", "CONTROLS", "PHOTOSENSOR", "ASHRAE 90.1"])

_r("CR-156", "Plumbing vent termination location",
   "Plumbing vent termination within 10' of air intake, operable window, or adjacent building.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "MAJOR", "code",
   kw=["VENT", "TERMINATION", "10 FEET", "AIR INTAKE"])

_r("CR-157", "Roof drain overflow/scupper sizing",
   "Primary roof drainage system has no overflow drain or scupper sized per IPC/IBC.",
   "PLMB-ARCH", ["PLMB", "ARCH"], "CRITICAL", "code",
   kw=["OVERFLOW", "SCUPPER", "ROOF DRAIN", "SECONDARY", "IPC"])

_r("CR-158", "Medical gas zone valve locations",
   "Healthcare facility has no medical gas zone valves shown at each floor/zone per NFPA 99.",
   "MECH-ARCH", ["MECH", "ARCH"], "CRITICAL", "code",
   kw=["MEDICAL GAS", "ZONE VALVE", "NFPA 99", "O2", "VACUUM"])

_r("CR-159", "Clean agent suppression for IT rooms",
   "Server room or data center without clean agent fire suppression per NFPA 75/76.",
   "FP-TECH", ["FP", "TECH"], "CRITICAL", "code",
   kw=["CLEAN AGENT", "SERVER ROOM", "DATA CENTER", "NFPA 75", "FM-200"])

_r("CR-160", "Smoke control system not coordinated",
   "High-rise or atrium requiring smoke control but system not shown or coordinated between MECH/FA.",
   "MECH-FA", ["MECH", "FA"], "CRITICAL", "code",
   kw=["SMOKE CONTROL", "PRESSURIZATION", "ATRIUM", "HIGH RISE"])


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

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
