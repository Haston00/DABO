"""
Seed a test commercial project for McCrory Construction.
Run once: python seed_test_project.py
"""
import sys
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

    # Create project
    cursor = conn.execute(
        """INSERT INTO projects (name, building_type, square_feet, stories, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            "McCrory Office Tower",
            "office",
            85000,
            4,
            "Test commercial project. PM: Timmy McClure. "
            "4-story Class A office, structural steel frame, curtain wall envelope. "
            "McCrory Construction — Charlotte, NC.",
        ),
    )
    pid = cursor.lastrowid

    # Create project directory
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    # Seed some synthetic classified sheets
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

    for sheet_id, sheet_name, discipline, page_num in sheets:
        conn.execute(
            """INSERT INTO sheets
               (project_id, page_number, sheet_id, sheet_name, discipline, confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pid, page_num, sheet_id, sheet_name, discipline, 0.95),
        )

    # Record a processing run
    conn.execute(
        """INSERT INTO processing_runs
           (project_id, run_type, files_processed, sheets_found, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, "ingestion", 1, len(sheets), "complete",
         "Test data — 47-sheet commercial office drawing set"),
    )

    conn.commit()
    conn.close()

    print(f"Test project created: McCrory Office Tower (ID #{pid})")
    print(f"  Type: office | 85,000 SF | 4 stories")
    print(f"  PM: Timmy McClure")
    print(f"  Sheets: {len(sheets)} across 9 disciplines")
    print(f"  Directory: {proj_dir}")


if __name__ == "__main__":
    seed()
