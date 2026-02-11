"""
Phase 2 tests — Classification + Entity Extraction.

All tests use synthetic commercial construction text.
No external PDF files required.

Run: python tests/test_classification.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.pdf_engine import PageResult
from classification.sheet_classifier import classify_sheets, classify_single, ClassifiedSheet
from classification.text_parser import parse_sheet_text
from classification.dimension_parser import parse_dimensions, parse_single, to_inches
from classification.entity_extractor import extract_entities, extract_all_entities, build_cross_reference_index


# ── Synthetic commercial drawing text ─────────────────────

ARCH_FLOOR_PLAN_TEXT = """
BAKER CONSTRUCTION CO.
FIRST FLOOR PLAN
Sheet: A-101

ROOM 101 - LOBBY                    ROOM 102 - CORRIDOR
ROOM 103 - CONFERENCE               ROOM 104 - OPEN OFFICE
ROOM 105 - BREAK ROOM               ROOM 106 - MECH. RM.
ROOM 107 - ELEC. RM.                ROOM 108 - JANITOR

1. PROVIDE 5/8" TYPE X GYP. BD. ON ALL PARTITION WALLS
2. ALL CEILING HEIGHTS 9'-0" U.N.O.
3. SEE SHEET A-501 FOR WALL SECTIONS
4. SEE SHEET A-301 FOR INTERIOR ELEVATIONS
5. PARTITION TYPE PT-1 AT ALL OFFICES, SEE 3/A-501

DOOR SCHEDULE:
D-101  3'-0" x 7'-0" HM FRAME, SOLID CORE WOOD, 90 MIN RATED
D-102  3'-0" x 7'-0" HM FRAME, HM DOOR, 20 MIN RATED
D-103  6'-0" x 7'-0" PAIR, ALUMINUM STOREFRONT

WINDOW SCHEDULE:
W-101  5'-0" x 4'-0" FIXED ALUMINUM
W-102  3'-0" x 4'-0" OPERABLE ALUMINUM

FINISH SCHEDULE PER SECTION 09 90 00
DOOR HARDWARE PER SECTION 08 70 00
ACT CEILING TYPE: 2x2 TEGULAR, SECTION 09 50 00
"""

STRUCTURAL_PLAN_TEXT = """
RUGGLES ENGINEERING PC
SECOND FLOOR FRAMING PLAN
Sheet: S-201

GRID A        GRID B        GRID C        GRID D
  |    28'-0"   |    32'-0"   |    28'-0"   |

W24x68 (TYP)
W16x40 AT GRID LINE B
W12x26 AT CORRIDOR
HSS6x6x1/4 BRACE AT GRID A

SLAB ON METAL DECK:
3-1/4" NW CONC. ON 2" COMP. DECK (3VLI20)
TOTAL SLAB DEPTH = 5-1/4"
f'c = 4000 PSI @ 28 DAYS
#4@12" O.C. E.W. T&B OVER SUPPORTS

BASE PLATE: 1-1/2" x 18" x 18" A36
ANCHOR BOLTS: (4) 3/4" DIA. x 18" EMBED

SECTION 03 30 00 - CAST-IN-PLACE CONCRETE
SECTION 05 12 00 - STRUCTURAL STEEL
T.O.S. EL. 112'-6"
B.O.S. EL. 109'-2"
SEE S-501 FOR DETAILS
"""

MECHANICAL_PLAN_TEXT = """
BAKER MECHANICAL
FIRST FLOOR HVAC PLAN
Sheet: M-101

AHU-1: 15,000 CFM, CHW COIL, DX BACKUP
RTU-2: 5,000 CFM, GAS/ELECTRIC
VAV-101: 1,200 CFM MAX, 400 CFM MIN
VAV-102: 800 CFM MAX, 300 CFM MIN
EF-1: 2,500 CFM, KITCHEN EXHAUST

SUPPLY DUCTWORK:
  36x18 MAIN TRUNK AT CORRIDOR
  24x12 BRANCH TO OFFICES
  14" RD TO CONFERENCE ROOM
  10" RD FLEX TO DIFFUSERS

CHILLED WATER: 2-1/2" CW SUPPLY, 2-1/2" CW RETURN
HOT WATER: 1-1/2" HW SUPPLY, 1-1/2" HW RETURN

EQUIPMENT SCHEDULE PER SECTION 23 70 00
DUCTWORK PER SECTION 23 30 00
CONTROLS PER SECTION 23 09 00

SEE M-501 FOR DETAILS
SEE E-101 FOR POWER TO MECHANICAL EQUIPMENT

THERMOSTAT: DDC, BAS CONNECTED
ALL DUCTWORK INSULATED PER SECTION 23 07 00
"""

ELECTRICAL_PLAN_TEXT = """
JOHNSON ELECTRICAL ENGINEERS
FIRST FLOOR LIGHTING PLAN
Sheet: E-101

PANEL SCHEDULE: LP-1A (277/480V, 3PH, 42 CKT)
MDP: 2000A, 277/480V, 65 KAIC
XFMR-1: 75 KVA, 480V PRI / 208Y/120V SEC

RECEPTACLE COUNT PER NEC 2020:
  OFFICES: (4) DUPLEX PER ROOM + (2) DEDICATED
  CONFERENCE: (8) FLOOR BOX + (4) WALL
  BREAK ROOM: (6) GFCI + (2) DEDICATED 20A

CONDUIT: 3/4"EMT (TYP), 1"EMT AT RUNS > 100'
HOME RUNS: 1"C TO LP-1A

LIGHTING:
  2x4 LED TROFFER, TYPE A, 40W, 4000K
  2x2 LED, TYPE B, 25W, 4000K
  6" LED DOWNLIGHT, TYPE C, 15W, 3000K
  EXIT SIGNS: LED, BATTERY BACKUP

SECTION 26 24 16 - PANELBOARDS
SECTION 26 51 00 - INTERIOR LIGHTING
SECTION 26 05 33 - RACEWAYS AND BOXES
ATS-1: 800A, 480V, SEE E-401 FOR ONE-LINE

GENERATOR: 500 KW STANDBY, DIESEL
SEE E-401 FOR ONE-LINE DIAGRAM
"""

PLUMBING_PLAN_TEXT = """
FIRST FLOOR PLUMBING PLAN
Sheet: P-101

DOMESTIC WATER:
  2" CW MAIN
  1-1/2" HW SUPPLY FROM MECH RM
  3/4" CW BRANCH TO FIXTURES

SANITARY:
  4" DWV MAIN
  3" DWV AT TOILETS
  2" DWV AT LAVS

STORM DRAIN:
  6" SS LEADER FROM ROOF DRAIN
  4" SD HORIZONTAL

PLUMBING FIXTURE SCHEDULE:
  WC-1: WATER CLOSET, FLOOR MOUNT, 1.28 GPF
  LAV-1: LAVATORY, WALL HUNG, 0.5 GPM
  UR-1: URINAL, WALL MOUNT, 0.125 GPF
  EWC-1: ELEC. WATER COOLER W/ BOTTLE FILLER

WATER HEATER: WH-1, 100 GAL, GAS, 199 MBH
BACKFLOW PREVENTER: BFP-1, 2" RPZA

SECTION 22 10 00 - PLUMBING PIPING
SECTION 22 40 00 - PLUMBING FIXTURES
SECTION 22 30 00 - PLUMBING EQUIPMENT

SEE S-101 FOR FLOOR PENETRATIONS
"""

FIRE_PROTECTION_TEXT = """
FIRE PROTECTION PLAN
Sheet: FP-101

WET PIPE SPRINKLER SYSTEM PER NFPA 13
ORDINARY HAZARD GROUP 2

SPRINKLER MAINS:
  4" MAIN RISER
  2-1/2" CROSS MAIN
  1" ARM-OVER TO HEADS

HEAD TYPES:
  PENDENT, 155F, K=5.6, CHROME, QR
  CONCEALED, 165F, K=5.6, WHITE COVER

FDC: 2-1/2" SIAMESE, STORZ CONNECTION
STANDPIPE: CLASS I, 4" RISER, 2-1/2" HOSE VALVE

FIRE PUMP: FP-1, 750 GPM, 100 PSI, ELECTRIC
JOCKEY PUMP: JP-1, 25 GPM

SECTION 21 13 00 - SPRINKLER SYSTEMS
SECTION 21 30 00 - FIRE PUMPS
SEE E-101 FOR POWER TO FIRE PUMP
"""


# ── Tests ─────────────────────────────────────────────────

def _make_page(text: str, page_num: int = 1) -> PageResult:
    """Create a synthetic PageResult from text."""
    return PageResult(
        page=page_num,
        text=text,
        text_length=len(text),
        method="synthetic",
        width=2592,  # ARCH D size
        height=1728,
    )


def test_dimension_parser_imperial():
    """Parse imperial dimensions from commercial drawings."""
    text = "28'-0\" span, 3'-0\" x 7'-0\" door, 5-1/4\" slab, 3/4\" rebar"
    dims = parse_dimensions(text)
    assert len(dims) > 0, "No dimensions found"

    # Check specific values
    types = {d.dim_type for d in dims}
    print(f"  Found {len(dims)} dimensions, types: {types}")
    for d in dims:
        print(f"    {d.raw:20s} -> {d.value_display:12s} ({d.dim_type})")


def test_dimension_parser_steel():
    """Parse structural steel sizes."""
    text = "W24x68 beam, W12x26 at corridor, HSS6x6x1/4 brace, L4x4x3/8"
    dims = parse_dimensions(text)
    steel = [d for d in dims if d.dim_type == "steel"]
    assert len(steel) >= 3, f"Expected 3+ steel sizes, got {len(steel)}"
    print(f"  Found {len(steel)} steel sizes: {[d.raw for d in steel]}")


def test_dimension_parser_rebar():
    """Parse rebar callouts."""
    text = "#4@12\" O.C. E.W. T&B, (2)#8 cont., #5@18\""
    dims = parse_dimensions(text)
    rebar = [d for d in dims if d.dim_type == "rebar"]
    assert len(rebar) >= 1, f"Expected rebar, got {len(rebar)}"
    print(f"  Found {len(rebar)} rebar: {[d.raw for d in rebar]}")


def test_dimension_parser_pipe():
    """Parse pipe sizes with abbreviations."""
    text = '4" DWV, 2-1/2" CW, 6" SS'
    dims = parse_dimensions(text)
    pipes = [d for d in dims if d.dim_type == "pipe"]
    assert len(pipes) >= 3, f"Expected 3 pipes, got {len(pipes)}"
    print(f"  Found {len(pipes)} pipes: {[d.raw for d in pipes]}")


def test_dimension_parser_elevations():
    """Parse elevation callouts."""
    text = "T.O.S. EL. 112'-6\", B.O.S. EL. 109'-2\""
    dims = parse_dimensions(text)
    elevs = [d for d in dims if d.dim_type == "elevation"]
    assert len(elevs) >= 2, f"Expected 2 elevations, got {len(elevs)}"
    print(f"  Found {len(elevs)} elevations: {[d.raw for d in elevs]}")


def test_dimension_parser_conduit():
    """Parse conduit sizes."""
    text = '3/4"EMT, 1"EMT, 1"C'
    dims = parse_dimensions(text)
    conduits = [d for d in dims if d.dim_type == "conduit"]
    assert len(conduits) >= 2, f"Expected 2+ conduits, got {len(conduits)}"
    print(f"  Found {len(conduits)} conduits: {[d.raw for d in conduits]}")


def test_dimension_parser_duct():
    """Parse duct sizes."""
    text = '36x18 main trunk, 24x12 branch, 14" RD to conference'
    dims = parse_dimensions(text)
    ducts = [d for d in dims if d.dim_type == "duct"]
    assert len(ducts) >= 2, f"Expected 2+ ducts, got {len(ducts)}: {[d.raw for d in ducts]}"
    print(f"  Found {len(ducts)} ducts: {[d.raw for d in ducts]}")


def test_text_parser_spec_refs():
    """Parse CSI spec section references."""
    parsed = parse_sheet_text(ARCH_FLOOR_PLAN_TEXT)
    assert len(parsed.spec_refs) >= 3, f"Expected 3+ spec refs, got {len(parsed.spec_refs)}"
    codes = [r.value for r in parsed.spec_refs]
    assert "09 90 00" in codes, f"Missing 09 90 00 in {codes}"
    assert "08 70 00" in codes, f"Missing 08 70 00 in {codes}"
    print(f"  Spec refs: {codes}")


def test_text_parser_equipment():
    """Parse equipment tags from mechanical plan."""
    parsed = parse_sheet_text(MECHANICAL_PLAN_TEXT)
    tags = [t.value for t in parsed.equipment_tags]
    assert "AHU-1" in tags, f"Missing AHU-1 in {tags}"
    assert "RTU-2" in tags, f"Missing RTU-2 in {tags}"
    assert "EF-1" in tags, f"Missing EF-1 in {tags}"
    print(f"  Equipment: {tags}")


def test_text_parser_drawing_refs():
    """Parse drawing cross-references."""
    parsed = parse_sheet_text(ARCH_FLOOR_PLAN_TEXT)
    refs = [r.value for r in parsed.drawing_refs]
    assert any("A-501" in r for r in refs), f"Missing A-501 ref in {refs}"
    assert any("A-301" in r for r in refs), f"Missing A-301 ref in {refs}"
    print(f"  Drawing refs: {refs}")


def test_text_parser_rooms():
    """Parse room references."""
    parsed = parse_sheet_text(ARCH_FLOOR_PLAN_TEXT)
    rooms = [r.value for r in parsed.room_refs]
    assert "101" in rooms, f"Missing room 101 in {rooms}"
    assert len(rooms) >= 6, f"Expected 6+ rooms, got {len(rooms)}"
    print(f"  Rooms: {rooms}")


def test_text_parser_doors():
    """Parse door marks."""
    parsed = parse_sheet_text(ARCH_FLOOR_PLAN_TEXT)
    doors = [d.value for d in parsed.door_marks]
    assert len(doors) >= 3, f"Expected 3+ doors, got {len(doors)}"
    print(f"  Doors: {doors}")


def test_text_parser_callouts():
    """Parse detail callouts."""
    parsed = parse_sheet_text(ARCH_FLOOR_PLAN_TEXT)
    callouts = [c.value for c in parsed.callouts]
    assert any("A-501" in c for c in callouts), f"Missing callout to A-501 in {callouts}"
    print(f"  Callouts: {callouts}")


def test_text_parser_code_refs():
    """Parse code references."""
    parsed = parse_sheet_text(ELECTRICAL_PLAN_TEXT)
    codes = [c.value for c in parsed.code_refs]
    assert any("NEC" in c for c in codes), f"Missing NEC ref in {codes}"
    print(f"  Code refs: {codes}")


def test_sheet_classifier_prefix():
    """Classify sheets by prefix — commercial disciplines."""
    pages = [
        _make_page(ARCH_FLOOR_PLAN_TEXT, 1),
        _make_page(STRUCTURAL_PLAN_TEXT, 2),
        _make_page(MECHANICAL_PLAN_TEXT, 3),
        _make_page(ELECTRICAL_PLAN_TEXT, 4),
        _make_page(PLUMBING_PLAN_TEXT, 5),
        _make_page(FIRE_PROTECTION_TEXT, 6),
    ]

    classified = classify_sheets(pages)
    assert len(classified) == 6

    # Check each discipline
    codes = {c.sheet_id: c.discipline_code for c in classified}
    print(f"  Classifications: {codes}")

    assert codes.get("A-101") == "ARCH", f"A-101 should be ARCH, got {codes.get('A-101')}"
    assert codes.get("S-201") == "STR", f"S-201 should be STR, got {codes.get('S-201')}"
    assert codes.get("M-101") == "MECH", f"M-101 should be MECH, got {codes.get('M-101')}"
    assert codes.get("E-101") == "ELEC", f"E-101 should be ELEC, got {codes.get('E-101')}"
    assert codes.get("P-101") == "PLMB", f"P-101 should be PLMB, got {codes.get('P-101')}"
    assert codes.get("FP-101") == "FP", f"FP-101 should be FP, got {codes.get('FP-101')}"

    # All should have high confidence from prefix match
    for c in classified:
        assert c.confidence >= 0.90, f"{c.sheet_id} confidence too low: {c.confidence}"


def test_entity_extractor_full():
    """Full extraction pipeline on synthetic commercial data."""
    pages = [
        _make_page(ARCH_FLOOR_PLAN_TEXT, 1),
        _make_page(STRUCTURAL_PLAN_TEXT, 2),
        _make_page(MECHANICAL_PLAN_TEXT, 3),
        _make_page(ELECTRICAL_PLAN_TEXT, 4),
        _make_page(PLUMBING_PLAN_TEXT, 5),
    ]

    classifications = classify_sheets(pages)
    entities = extract_all_entities(pages, classifications)

    assert len(entities) == 5
    total = sum(e.total_entities for e in entities)
    assert total > 30, f"Expected 30+ total entities, got {total}"
    print(f"  Total entities across 5 sheets: {total}")

    for e in entities:
        print(f"    {e.sheet_id} ({e.discipline_code}): {e.total_entities} entities")


def test_cross_reference_index():
    """Build cross-reference index from extracted entities."""
    pages = [
        _make_page(ARCH_FLOOR_PLAN_TEXT, 1),
        _make_page(STRUCTURAL_PLAN_TEXT, 2),
        _make_page(MECHANICAL_PLAN_TEXT, 3),
        _make_page(ELECTRICAL_PLAN_TEXT, 4),
        _make_page(PLUMBING_PLAN_TEXT, 5),
        _make_page(FIRE_PROTECTION_TEXT, 6),
    ]

    classifications = classify_sheets(pages)
    entities = extract_all_entities(pages, classifications)
    xref = build_cross_reference_index(entities)

    # Should have drawing cross-references
    draw_refs = xref.get("drawing_refs", {})
    assert len(draw_refs) > 0, "No drawing cross-references found"
    print(f"  Drawing refs: {dict(draw_refs)}")

    # Should have spec references
    spec_refs = xref.get("spec_refs", {})
    assert len(spec_refs) > 0, "No spec cross-references found"
    print(f"  Spec refs: {len(spec_refs)} unique sections")

    # Should have equipment tags
    equip = xref.get("equipment_tags", {})
    print(f"  Equipment: {dict(equip)}")


# ── Run all tests ─────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_dimension_parser_imperial,
        test_dimension_parser_steel,
        test_dimension_parser_rebar,
        test_dimension_parser_pipe,
        test_dimension_parser_elevations,
        test_dimension_parser_conduit,
        test_dimension_parser_duct,
        test_text_parser_spec_refs,
        test_text_parser_equipment,
        test_text_parser_drawing_refs,
        test_text_parser_rooms,
        test_text_parser_doors,
        test_text_parser_callouts,
        test_text_parser_code_refs,
        test_sheet_classifier_prefix,
        test_entity_extractor_full,
        test_cross_reference_index,
    ]

    print(f"\n{'='*60}")
    print(f"  DABO Phase 2 Tests - {len(tests)} tests")
    print(f"  Using synthetic commercial construction data")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            print(f"[RUN]  {name}")
            test()
            print(f"[PASS] {name}\n")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}\n")
            failed += 1

    print(f"{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)
