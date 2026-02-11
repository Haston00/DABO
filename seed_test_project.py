"""
Seed demo projects for McCrory Construction.
Run once: python seed_test_project.py

Creates 3 projects with sheets, files, processing runs, and feedback
so every dashboard tool has data to play with.
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.db import get_conn
from config.settings import PROJECTS_DIR


def seed():
    conn = get_conn()

    # Check if already seeded
    existing = conn.execute("SELECT id FROM projects WHERE name = 'McCrory Office Tower'").fetchone()
    if existing:
        print(f"Test project already exists (ID #{existing['id']}). Skipping.")
        conn.close()
        return

    # ── Project 1: McCrory Office Tower (original) ────────
    pid1 = _seed_office_tower(conn)

    # ── Project 2: Southpark Medical Center ────────────────
    pid2 = _seed_medical_center(conn)

    # ── Project 3: Ballantyne Mixed-Use ────────────────────
    pid3 = _seed_mixed_use(conn)

    conn.commit()
    conn.close()

    print(f"\nDemo data seeded:")
    print(f"  1. McCrory Office Tower (ID #{pid1}) — 47 sheets, 10 disciplines")
    print(f"  2. Southpark Medical Center (ID #{pid2}) — 62 sheets, 10 disciplines")
    print(f"  3. Ballantyne Mixed-Use (ID #{pid3}) — 38 sheets, 9 disciplines")
    print(f"  Total: 147 sheets across 3 projects")
    print(f"  Plus: mock files, processing runs, feedback history\n")


def _seed_office_tower(conn):
    """Original 47-sheet commercial office project."""
    cursor = conn.execute(
        """INSERT INTO projects (name, building_type, square_feet, stories, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            "McCrory Office Tower",
            "office",
            85000,
            4,
            "4-story Class A office, structural steel frame, curtain wall envelope. "
            "PM: Timmy McClure. McCrory Construction — Charlotte, NC.",
        ),
    )
    pid = cursor.lastrowid
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    sheets = [
        ("G-001", "Cover Sheet & Drawing Index", "GEN", 1),
        ("G-002", "General Notes & Abbreviations", "GEN", 2),
        ("C-101", "Site Plan & Grading", "CIV", 3),
        ("C-102", "Utility Plan", "CIV", 4),
        ("A-101", "Floor Plan — Level 1", "ARCH", 5),
        ("A-102", "Floor Plan — Level 2", "ARCH", 6),
        ("A-103", "Floor Plan — Level 3", "ARCH", 7),
        ("A-104", "Floor Plan — Level 4", "ARCH", 8),
        ("A-201", "Building Elevations", "ARCH", 9),
        ("A-301", "Building Sections", "ARCH", 10),
        ("A-401", "Wall Sections & Details", "ARCH", 11),
        ("A-501", "Enlarged Plans — Lobby & Restrooms", "ARCH", 12),
        ("A-601", "Door & Window Schedules", "ARCH", 13),
        ("A-701", "Finish Schedule & Interior Elevations", "ARCH", 14),
        ("S-101", "Foundation Plan", "STR", 15),
        ("S-102", "Framing Plan — Level 2", "STR", 16),
        ("S-103", "Framing Plan — Level 3", "STR", 17),
        ("S-104", "Framing Plan — Level 4", "STR", 18),
        ("S-105", "Roof Framing Plan", "STR", 19),
        ("S-201", "Structural Sections", "STR", 20),
        ("S-301", "Structural Details", "STR", 21),
        ("S-401", "Steel Connection Details", "STR", 22),
        ("M-101", "HVAC Floor Plan — Level 1", "MECH", 23),
        ("M-102", "HVAC Floor Plan — Level 2", "MECH", 24),
        ("M-103", "HVAC Floor Plan — Levels 3-4", "MECH", 25),
        ("M-201", "HVAC Roof Plan", "MECH", 26),
        ("M-301", "HVAC Details & Schedules", "MECH", 27),
        ("M-401", "Controls Diagrams", "MECH", 28),
        ("P-101", "Plumbing Floor Plan — Level 1", "PLMB", 29),
        ("P-102", "Plumbing Floor Plans — Levels 2-4", "PLMB", 30),
        ("P-201", "Plumbing Riser Diagrams", "PLMB", 31),
        ("P-301", "Plumbing Details & Schedules", "PLMB", 32),
        ("E-101", "Electrical Power Plan — Level 1", "ELEC", 33),
        ("E-102", "Electrical Power Plan — Level 2", "ELEC", 34),
        ("E-103", "Electrical Power Plan — Levels 3-4", "ELEC", 35),
        ("E-201", "Electrical Lighting Plan — Level 1", "ELEC", 36),
        ("E-301", "One-Line Diagram", "ELEC", 37),
        ("E-401", "Panel Schedules", "ELEC", 38),
        ("E-501", "Electrical Details", "ELEC", 39),
        ("FP-101", "Fire Protection Plan — Level 1", "FP", 40),
        ("FP-102", "Fire Protection Plans — Levels 2-4", "FP", 41),
        ("FP-201", "Fire Protection Riser & Details", "FP", 42),
        ("FA-101", "Fire Alarm Plan — Level 1", "FA", 43),
        ("FA-102", "Fire Alarm Plans — Levels 2-4", "FA", 44),
        ("FA-201", "Fire Alarm Riser & Details", "FA", 45),
        ("T-101", "Telecom/Data Plan — Level 1", "TECH", 46),
        ("T-102", "Telecom/Data Plans — Levels 2-4", "TECH", 47),
    ]

    _insert_sheets(conn, pid, sheets, conf_range=(0.88, 0.99))

    # Mock uploaded files
    _insert_files(conn, pid, [
        ("McCrory_Office_Tower_Arch.pdf", "drawing", 14, "processed"),
        ("McCrory_Office_Tower_Struct.pdf", "drawing", 8, "processed"),
        ("McCrory_Office_Tower_MEP.pdf", "drawing", 17, "processed"),
        ("McCrory_Office_Tower_FP_FA.pdf", "drawing", 6, "processed"),
        ("McCrory_Office_Tower_Civil.pdf", "drawing", 2, "processed"),
    ])

    # Processing runs
    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, "ingestion", 5, 47, "complete",
         "Full 47-sheet commercial office drawing set — 5 PDF packages"),
    )
    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, conflicts_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pid, "review", 5, 47, 12, "complete",
         "Cross-discipline review — 12 conflicts detected across 8 rule categories"),
    )

    # Feedback history (makes the feedback/metrics page interesting)
    _insert_feedback(conn, pid, [
        ("CR-001", "confirm", "CRITICAL", "CRITICAL", "Beam depth conflict confirmed — 24\" W-beam vs 10' ceiling"),
        ("CR-005", "downgrade", "MAJOR", "MINOR", "Duct routing has clearance, just tight. Not a real conflict."),
        ("CR-008", "dismiss", "MINOR", "INFO", "Panel location works fine — field verified"),
        ("CR-012", "confirm", "MAJOR", "MAJOR", "Fire rating mismatch is real — need architect response"),
        ("CR-003", "confirm", "CRITICAL", "CRITICAL", "Column grid offset confirmed between S-101 and A-101"),
        ("CR-015", "downgrade", "MAJOR", "MINOR", "Plumbing chase size adequate per plumber"),
        ("CR-022", "dismiss", "MINOR", "INFO", "Telecom pathway cleared with IT consultant"),
    ])

    # Bluebeam markups — what Timmy would add during plan review
    _insert_markups(conn, pid, [
        ("A-101", "callout", "RFI", "Door 101A swings into corridor — verify clearance with ADA path of travel", "Timmy McClure", "#ff0000", 5),
        ("A-101", "cloud", "VERIFY", "Column grid line offset 2\" between A-101 and S-101 — coordinate with structural", "Timmy McClure", "#ff6600", 5),
        ("A-102", "measurement", "DIM", "Ceiling height 9'-6\" — confirm plenum depth for 24\" ductwork + sprinkler main", "Timmy McClure", "#0066ff", 6),
        ("S-101", "callout", "HOLD", "Foundation step at grid C — waiting on geotech boring log confirmation", "Jake Reynolds", "#ffcc00", 15),
        ("S-102", "stamp", "APPROVED", "Framing layout approved — steel order can proceed", "Timmy McClure", "#00cc00", 16),
        ("M-101", "callout", "CLASH", "30x24 supply duct conflicts with W18x35 beam at grid B-3. Need 6\" clearance min.", "Timmy McClure", "#ff0000", 23),
        ("M-101", "cloud", "REROUTE", "Return air path blocked by plumbing chase — reroute through corridor soffit?", "Timmy McClure", "#ff6600", 23),
        ("E-101", "callout", "RFI", "Panel LP-1 location conflicts with fire extinguisher cabinet — move 3' east?", "Timmy McClure", "#ff0000", 33),
        ("E-301", "callout", "VERIFY", "Main breaker rated 1200A but load calc shows 1150A — too close, verify with EE", "Jake Reynolds", "#ff6600", 37),
        ("P-101", "measurement", "DIM", "Sanitary line invert at -4'-2\" — confirm slope to site manhole per C-102", "Timmy McClure", "#0066ff", 29),
        ("FP-101", "callout", "CODE", "Sprinkler head spacing 14' — max is 13' per NFPA 13 for light hazard. Fix.", "Timmy McClure", "#ff0000", 40),
        ("A-301", "cloud", "DETAIL", "Wall section at curtain wall base — no detail showing slab edge condition", "Timmy McClure", "#9933ff", 10),
        ("A-601", "callout", "RFI", "Door schedule shows HM frame for 101B but elevation shows aluminum storefront", "Timmy McClure", "#ff0000", 13),
        ("S-201", "stamp", "REVISE", "Connection detail SD-4 needs revision per steel fabricator RFI response", "Jake Reynolds", "#ff6600", 20),
        ("M-301", "callout", "SPEC", "VAV box schedule calls for Trane but spec section 23 36 00 says Carrier — which?", "Timmy McClure", "#ff0000", 27),
    ])

    return pid


def _seed_medical_center(conn):
    """62-sheet medical/healthcare project — more MEP-heavy."""
    cursor = conn.execute(
        """INSERT INTO projects (name, building_type, square_feet, stories, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            "Southpark Medical Center",
            "healthcare",
            120000,
            3,
            "3-story medical office building with outpatient surgery center. "
            "Heavy MEP coordination. PM: Jake Reynolds. "
            "McCrory Construction — Charlotte, NC.",
        ),
    )
    pid = cursor.lastrowid
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    sheets = [
        ("G-001", "Cover Sheet & Index", "GEN", 1),
        ("G-002", "General Notes", "GEN", 2),
        ("G-003", "Code Analysis & Life Safety", "GEN", 3),
        ("C-101", "Site Plan", "CIV", 4),
        ("C-102", "Grading & Drainage Plan", "CIV", 5),
        ("C-103", "Utility Plan", "CIV", 6),
        ("A-101", "Floor Plan — Level 1", "ARCH", 7),
        ("A-102", "Floor Plan — Level 2", "ARCH", 8),
        ("A-103", "Floor Plan — Level 3", "ARCH", 9),
        ("A-201", "Exterior Elevations", "ARCH", 10),
        ("A-202", "Interior Elevations — Surgery", "ARCH", 11),
        ("A-301", "Building Sections", "ARCH", 12),
        ("A-401", "Wall Sections", "ARCH", 13),
        ("A-501", "Enlarged Plans — OR Suite", "ARCH", 14),
        ("A-502", "Enlarged Plans — Imaging", "ARCH", 15),
        ("A-601", "Door Schedule", "ARCH", 16),
        ("A-701", "Finish Schedule", "ARCH", 17),
        ("A-801", "Reflected Ceiling Plans", "ARCH", 18),
        ("S-101", "Foundation Plan", "STR", 19),
        ("S-102", "Framing Plan — Level 2", "STR", 20),
        ("S-103", "Framing Plan — Level 3", "STR", 21),
        ("S-104", "Roof Framing", "STR", 22),
        ("S-201", "Structural Details", "STR", 23),
        ("S-301", "Vibration Isolation Details", "STR", 24),
        ("M-101", "HVAC Plan — Level 1", "MECH", 25),
        ("M-102", "HVAC Plan — Level 2", "MECH", 26),
        ("M-103", "HVAC Plan — Level 3", "MECH", 27),
        ("M-201", "HVAC Roof Plan", "MECH", 28),
        ("M-301", "HVAC Details", "MECH", 29),
        ("M-401", "Medical Gas Piping — Level 1", "MECH", 30),
        ("M-402", "Medical Gas Piping — Levels 2-3", "MECH", 31),
        ("M-501", "Controls Diagrams", "MECH", 32),
        ("M-601", "Equipment Schedules", "MECH", 33),
        ("P-101", "Plumbing Plan — Level 1", "PLMB", 34),
        ("P-102", "Plumbing Plan — Level 2", "PLMB", 35),
        ("P-103", "Plumbing Plan — Level 3", "PLMB", 36),
        ("P-201", "Plumbing Riser Diagrams", "PLMB", 37),
        ("P-301", "Medical Gas Riser", "PLMB", 38),
        ("P-401", "Plumbing Details", "PLMB", 39),
        ("E-101", "Power Plan — Level 1", "ELEC", 40),
        ("E-102", "Power Plan — Level 2", "ELEC", 41),
        ("E-103", "Power Plan — Level 3", "ELEC", 42),
        ("E-201", "Lighting Plan — Level 1", "ELEC", 43),
        ("E-202", "Lighting Plan — Levels 2-3", "ELEC", 44),
        ("E-301", "One-Line Diagram — Normal", "ELEC", 45),
        ("E-302", "One-Line Diagram — Emergency", "ELEC", 46),
        ("E-401", "Panel Schedules", "ELEC", 47),
        ("E-501", "Generator & Transfer Switch", "ELEC", 48),
        ("E-601", "Electrical Details", "ELEC", 49),
        ("FP-101", "Fire Sprinkler — Level 1", "FP", 50),
        ("FP-102", "Fire Sprinkler — Level 2", "FP", 51),
        ("FP-103", "Fire Sprinkler — Level 3", "FP", 52),
        ("FP-201", "Sprinkler Riser & Details", "FP", 53),
        ("FA-101", "Fire Alarm Plan — Level 1", "FA", 54),
        ("FA-102", "Fire Alarm Plans — Levels 2-3", "FA", 55),
        ("FA-201", "Fire Alarm Riser", "FA", 56),
        ("FA-301", "Nurse Call & Code Blue Layout", "FA", 57),
        ("T-101", "Telecom Plan — Level 1", "TECH", 58),
        ("T-102", "Telecom Plans — Levels 2-3", "TECH", 59),
        ("T-201", "Server Room Layout", "TECH", 60),
        ("T-301", "AV Systems — OR & Conference", "TECH", 61),
        ("T-401", "Security Camera Layout", "TECH", 62),
    ]

    _insert_sheets(conn, pid, sheets, conf_range=(0.82, 0.98))

    _insert_files(conn, pid, [
        ("Southpark_Medical_Arch.pdf", "drawing", 12, "processed"),
        ("Southpark_Medical_Struct.pdf", "drawing", 6, "processed"),
        ("Southpark_Medical_Mech.pdf", "drawing", 9, "processed"),
        ("Southpark_Medical_Plumb.pdf", "drawing", 6, "processed"),
        ("Southpark_Medical_Elec.pdf", "drawing", 10, "processed"),
        ("Southpark_Medical_FP_FA.pdf", "drawing", 8, "processed"),
        ("Southpark_Medical_Tech.pdf", "drawing", 5, "processed"),
        ("Southpark_Medical_Civil.pdf", "drawing", 3, "processed"),
        ("Southpark_Geotech_Report.pdf", "report", 45, "processed"),
    ])

    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, "ingestion", 9, 62, "complete",
         "62-sheet medical office — 9 PDF packages including geotech report"),
    )
    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, conflicts_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pid, "review", 9, 62, 18, "complete",
         "Heavy MEP coordination — 18 conflicts, mostly mechanical/plumbing clashes"),
    )

    _insert_feedback(conn, pid, [
        ("CR-001", "confirm", "CRITICAL", "CRITICAL", "Beam vs ceiling in OR suite — must resolve before steel order"),
        ("CR-005", "confirm", "MAJOR", "MAJOR", "Duct clash with sprinkler main at Level 2 corridor"),
        ("CR-009", "downgrade", "MAJOR", "MINOR", "Medical gas routing workable with minor reroute"),
        ("CR-014", "confirm", "CRITICAL", "CRITICAL", "Emergency generator transfer sequence incomplete"),
        ("CR-019", "dismiss", "MINOR", "INFO", "Nurse call wiring path OK per low-voltage sub"),
    ])

    _insert_markups(conn, pid, [
        ("A-501", "callout", "RFI", "OR suite door width 3'-0\" — code requires 4'-0\" min for hospital gurney access", "Jake Reynolds", "#ff0000", 14),
        ("A-502", "cloud", "VERIFY", "MRI room shielding wall shown 6\" — confirm RF shielding spec with equipment vendor", "Jake Reynolds", "#ff6600", 15),
        ("M-401", "callout", "CODE", "Medical gas zone valve location not shown — required per NFPA 99 at each floor", "Jake Reynolds", "#ff0000", 30),
        ("M-102", "callout", "CLASH", "48x36 supply main conflicts with 8\" sprinkler main at corridor ceiling grid D-2", "Jake Reynolds", "#ff0000", 26),
        ("E-501", "callout", "CRITICAL", "Emergency generator ATS does not show life safety branch separation per NEC 700", "Jake Reynolds", "#ff0000", 48),
        ("E-302", "cloud", "VERIFY", "Emergency one-line missing equipment branch — MRI and CT need dedicated circuits", "Jake Reynolds", "#ff6600", 46),
        ("S-301", "callout", "VIBRATION", "MRI room requires vibration isolation to 125 µin/sec — no detail shown for slab", "Jake Reynolds", "#9933ff", 24),
        ("P-301", "measurement", "DIM", "Medical gas riser size 1-1/4\" — verify capacity for 3 floors of O2/N2O/vacuum", "Jake Reynolds", "#0066ff", 38),
        ("FP-102", "callout", "CODE", "Clean agent suppression required in server room per NFPA 75 — not shown", "Jake Reynolds", "#ff0000", 51),
        ("FA-301", "callout", "RFI", "Nurse call head-end location not coordinated with IT server room layout on T-201", "Jake Reynolds", "#ff0000", 57),
    ])

    return pid


def _seed_mixed_use(conn):
    """38-sheet mixed-use retail/residential — smaller, tighter set."""
    cursor = conn.execute(
        """INSERT INTO projects (name, building_type, square_feet, stories, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            "Ballantyne Mixed-Use",
            "mixed_use",
            52000,
            5,
            "5-story mixed-use: ground-floor retail, 4 floors residential above. "
            "Wood-frame over podium slab. PM: Sarah Chen. "
            "McCrory Construction — Charlotte, NC.",
        ),
    )
    pid = cursor.lastrowid
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    sheets = [
        ("G-001", "Cover Sheet & Index", "GEN", 1),
        ("C-101", "Site Plan", "CIV", 2),
        ("C-102", "Utility & Grading Plan", "CIV", 3),
        ("A-101", "Floor Plan — Retail Level", "ARCH", 4),
        ("A-102", "Floor Plan — Typical Residential", "ARCH", 5),
        ("A-103", "Floor Plan — Level 5 & Roof", "ARCH", 6),
        ("A-201", "Exterior Elevations", "ARCH", 7),
        ("A-301", "Building Sections", "ARCH", 8),
        ("A-401", "Wall Sections & Details", "ARCH", 9),
        ("A-501", "Unit Plans — Type A, B, C", "ARCH", 10),
        ("A-601", "Door & Window Schedules", "ARCH", 11),
        ("A-701", "Finish Schedule", "ARCH", 12),
        ("S-101", "Foundation & Podium Slab Plan", "STR", 13),
        ("S-102", "Framing Plans — Levels 2-5", "STR", 14),
        ("S-201", "Structural Details", "STR", 15),
        ("M-101", "HVAC Plan — Retail", "MECH", 16),
        ("M-102", "HVAC Plan — Typical Residential", "MECH", 17),
        ("M-201", "Roof Mechanical Plan", "MECH", 18),
        ("M-301", "HVAC Details & Schedules", "MECH", 19),
        ("P-101", "Plumbing Plan — Retail", "PLMB", 20),
        ("P-102", "Plumbing Plan — Typical Residential", "PLMB", 21),
        ("P-201", "Plumbing Riser & Details", "PLMB", 22),
        ("E-101", "Electrical Plan — Retail", "ELEC", 23),
        ("E-102", "Electrical Plan — Typical Residential", "ELEC", 24),
        ("E-201", "Lighting Plans", "ELEC", 25),
        ("E-301", "One-Line Diagram", "ELEC", 26),
        ("E-401", "Panel Schedules", "ELEC", 27),
        ("FP-101", "Fire Sprinkler — Retail", "FP", 28),
        ("FP-102", "Fire Sprinkler — Residential", "FP", 29),
        ("FP-201", "Sprinkler Riser", "FP", 30),
        ("FA-101", "Fire Alarm Plans", "FA", 31),
        ("FA-201", "Fire Alarm Riser & Details", "FA", 32),
        ("T-101", "Telecom & Data Plans", "TECH", 33),
        ("L-101", "Landscape Plan", "CIV", 34),
        ("L-201", "Landscape Details & Planting Schedule", "CIV", 35),
        ("A-801", "Amenity Deck Plan — Level 2", "ARCH", 36),
        ("A-901", "Parking Garage Plan", "ARCH", 37),
        ("E-501", "EV Charging Station Layout", "ELEC", 38),
    ]

    _insert_sheets(conn, pid, sheets, conf_range=(0.85, 0.97))

    _insert_files(conn, pid, [
        ("Ballantyne_MixedUse_Full_Set.pdf", "drawing", 38, "processed"),
        ("Ballantyne_Landscape.pdf", "drawing", 2, "processed"),
        ("Ballantyne_Soils_Report.pdf", "report", 28, "processed"),
    ])

    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, "ingestion", 3, 38, "complete",
         "38-sheet mixed-use set — full drawing package + landscape + soils"),
    )

    _insert_feedback(conn, pid, [
        ("CR-002", "confirm", "MAJOR", "MAJOR", "Podium slab penetrations not coordinated with plumbing"),
        ("CR-010", "downgrade", "MAJOR", "MINOR", "EV charging conduit path works — just needs sleeve in podium"),
    ])

    _insert_markups(conn, pid, [
        ("A-101", "callout", "RFI", "Retail storefront height 12' on elevation but 10' on plan — which is correct?", "Sarah Chen", "#ff0000", 4),
        ("S-101", "cloud", "VERIFY", "Podium slab pour-back at column C-3 — no rebar splice detail for wood-to-concrete", "Sarah Chen", "#ff6600", 13),
        ("M-101", "callout", "SPEC", "Retail HVAC shows split system but spec says VRF — confirm system type", "Sarah Chen", "#ff0000", 16),
        ("E-501", "callout", "CODE", "EV charging stations need dedicated 50A circuits — panel LP-R1 has no spare slots", "Sarah Chen", "#ff0000", 38),
        ("P-102", "callout", "CLASH", "Residential waste stack at unit B conflicts with shear wall on S-102", "Sarah Chen", "#ff0000", 21),
        ("A-801", "callout", "RFI", "Amenity deck waterproofing — no detail at planter drain penetration through slab", "Sarah Chen", "#ff6600", 36),
    ])

    return pid


def _insert_sheets(conn, pid, sheets, conf_range=(0.85, 0.99)):
    """Insert sheets with varied confidence scores."""
    random.seed(42)  # Deterministic but varied
    for sheet_id, sheet_name, discipline, page_num in sheets:
        conf = round(random.uniform(*conf_range), 3)
        conn.execute(
            """INSERT INTO sheets
               (project_id, page_number, sheet_id, sheet_name, discipline, confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pid, page_num, sheet_id, sheet_name, discipline, conf),
        )


def _insert_files(conn, pid, files):
    """Insert mock uploaded file records."""
    for filename, file_type, page_count, status in files:
        conn.execute(
            """INSERT OR IGNORE INTO project_files
               (project_id, filename, file_type, page_count, status)
               VALUES (?, ?, ?, ?, ?)""",
            (pid, filename, file_type, page_count, status),
        )


def _insert_feedback(conn, pid, feedback_items):
    """Insert feedback history records."""
    for conflict_id, action, orig_sev, adj_sev, note in feedback_items:
        conn.execute(
            """INSERT INTO feedback
               (project_id, conflict_id, action, original_severity, adjusted_severity, user_note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pid, conflict_id, action, orig_sev, adj_sev, note),
        )


def _insert_markups(conn, pid, markups):
    """Insert mock Bluebeam markup records."""
    for sheet_id, markup_type, label, content, author, color, page in markups:
        conn.execute(
            """INSERT INTO markups
               (project_id, sheet_id, markup_type, label, content, author, color, page_number)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, sheet_id, markup_type, label, content, author, color, page),
        )


if __name__ == "__main__":
    seed()
