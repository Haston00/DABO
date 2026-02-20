"""
DABO API blueprint — all JSON endpoints for the Flask dashboard.
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file

from config.settings import PROJECTS_DIR
from utils.db import get_conn
from utils.helpers import file_hash
from utils import storage as cloud
from classification.text_parser import ParsedSheet, ParsedToken

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── Demo ParsedSheet builder ─────────────────────────────
# Populates discipline-appropriate notes, spec refs, equipment tags,
# callouts, and code refs so the conflict detector finds real issues.

def _tok(ttype, raw, value="", ctx=""):
    return ParsedToken(token_type=ttype, raw=raw, value=value or raw, context=ctx)


_DEMO_PARSED: dict[str, callable] = {}


def _build_demo_parsed(discipline: str) -> ParsedSheet:
    builder = _DEMO_PARSED.get(discipline)
    if builder:
        return builder()
    return ParsedSheet()


def _arch_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "CEILING HEIGHT IN LOBBY SHALL BE 12'-0\" AFF. VERIFY PLENUM SPACE WITH MECHANICAL FOR DUCTWORK CLEARANCE."),
            _tok("note", "DOOR D-101 HARDWARE GROUP 4 WITH CLOSER. SEE DOOR SCHEDULE FOR RATING. VERIFY WALL DEPTH WITH STRUCTURAL."),
            _tok("note", "PROVIDE DEPRESSED SLAB AT TILE AREAS PER FINISH SCHEDULE. COORDINATE RECESS DEPTH WITH STRUCTURAL."),
            _tok("note", "SHEAR WALL SW-1 SHOWN ON STRUCTURAL. NO OPENINGS PERMITTED WITHOUT STRUCTURAL ENGINEER APPROVAL."),
            _tok("note", "CURTAIN WALL SYSTEM AT SOUTH ELEVATION. VERIFY SLAB EDGE POUR-BACK CONDITION WITH STRUCTURAL."),
            _tok("note", "RATED WALL TYPE RW-2 EXTENDS TO UNDERSIDE OF DECK ABOVE. FIRESTOP ALL PENETRATIONS PER SPEC."),
            _tok("note", "PROVIDE FLASHING AT WINDOW HEAD, SILL, AND JAMB CONDITIONS. SEE DETAIL 3/A-501."),
            _tok("note", "EGRESS CORRIDOR WIDTH 6'-0\" MINIMUM. EXIT SIGNS AT EACH CHANGE OF DIRECTION PER IBC."),
            _tok("note", "ADA RESTROOM LAYOUT PER ICC A117.1. PROVIDE GRAB BAR AND 60 INCH TURNING RADIUS."),
            _tok("note", "PARAPET CAP FLASHING AND COPING PER DETAIL. COORDINATE EXPANSION JOINT COVER AT ROOF."),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 09 29 00", "09 29 00"),
            _tok("spec_ref", "SECTION 08 44 13", "08 44 13"),
            _tok("spec_ref", "SECTION 07 92 00", "07 92 00"),
            _tok("spec_ref", "SECTION 09 51 00", "09 51 00"),
        ],
        callouts=[
            _tok("callout", "3/A-501", "3/A-501"),
            _tok("callout", "1/A-301", "1/A-301"),
            _tok("callout", "A/A-601", "A/A-601"),
        ],
        door_marks=[
            _tok("door", "D-101", "D-101"),
            _tok("door", "D-102", "D-102"),
            _tok("door", "D-201", "D-201"),
        ],
        room_refs=[
            _tok("room", "ROOM 101", "101"),
            _tok("room", "ROOM 201", "201"),
            _tok("room", "ROOM 105", "105"),
        ],
        drawing_refs=[
            _tok("drawing_ref", "SEE S-101", "S-101"),
            _tok("drawing_ref", "SEE M-101", "M-101"),
        ],
        code_refs=[
            _tok("code_ref", "IBC 2021", "IBC 2021"),
            _tok("code_ref", "ICC A117.1", "ICC A117.1"),
        ],
        grid_refs=[
            _tok("grid", "GRID A", "A"),
            _tok("grid", "GRID 3", "3"),
        ],
    )


def _str_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "CONCRETE 4000 PSI F'C AT 28 DAYS. MIX DESIGN PER SECTION 03 30 00. VERIFY ALL BEAM SIZES WITH SCHEDULE."),
            _tok("note", "MOMENT FRAME CONNECTION AT GRID L-10. PROVIDE SHEAR TAB AND CLIP ANGLE PER DETAIL 2/S-301."),
            _tok("note", "EMBED PLATE AND ANCHOR BOLT LAYOUT AT COLUMN BASE PLATE. COORDINATE WITH FOUNDATION PLAN."),
            _tok("note", "SHEAR WALL SW-1 AT GRID A-3. NO OPENINGS WITHOUT ENGINEER REVIEW. COORDINATE WITH ARCHITECTURAL."),
            _tok("note", "SLAB ON GRADE 5\" THICK WITH #4 REINFORCING MESH AT 12\" O.C. EACH WAY. CONTROL JOINT LAYOUT PER PLAN."),
            _tok("note", "STRUCTURAL OPENING REQUIRED FOR MECHANICAL DUCT PENETRATION AT BEAM B-12. PROVIDE SLEEVE."),
            _tok("note", "EXPANSION JOINT AT GRID J. CONTINUOUS THROUGH ALL LEVELS. COORDINATE WITH ARCHITECTURAL FINISHES."),
            _tok("note", "LIVE LOAD DESIGN: OFFICE 80 PSF, CORRIDOR 100 PSF, MEZZANINE STORAGE 125 PSF."),
            _tok("note", "BELOW GRADE FOUNDATION WALL. WATERPROOFING MEMBRANE BY ARCHITECTURAL. VERIFY FOOTING DEPTH."),
            _tok("note", "ROOF FRAMING SLOPE 1/4\" PER FOOT TO DRAIN LOCATIONS. VERIFY WITH PLUMBING ROOF DRAIN LAYOUT."),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 03 30 00", "03 30 00"),
            _tok("spec_ref", "SECTION 05 12 00", "05 12 00"),
            _tok("spec_ref", "SECTION 03 20 00", "03 20 00"),
        ],
        callouts=[
            _tok("callout", "2/S-301", "2/S-301"),
            _tok("callout", "1/S-401", "1/S-401"),
        ],
        drawing_refs=[
            _tok("drawing_ref", "SEE A-101", "A-101"),
        ],
        grid_refs=[
            _tok("grid", "GRID A", "A"),
            _tok("grid", "GRID L", "L"),
            _tok("grid", "GRID J", "J"),
        ],
    )


def _mech_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "AHU-1 SUPPLY DUCT 24x12 ROUTED BELOW BEAM B-12. VERIFY PLENUM CLEARANCE WITH STRUCTURAL. CEILING HEIGHT 9'-6\"."),
            _tok("note", "RTU-2 ON STRUCTURAL DUNNAGE. WEIGHT 2800 LBS. VIBRATION ISOLATION WITH SPRING INERTIA BASE PER DETAIL."),
            _tok("note", "EXHAUST AIR LOUVER MIN 10'-0\" SEPARATION FROM OUTDOOR AIR INTAKE PER IMC. VERIFY ON ROOF PLAN."),
            _tok("note", "CHILLED WATER PIPE INSULATION 1.5\" THICK. ALLOW CLEARANCE FOR INSULATION IN CEILING SPACE."),
            _tok("note", "KITCHEN HOOD MAKEUP AIR UNIT MAU-1 PROVIDES 100% REPLACEMENT AIR. COORDINATE DUCT ROUTING WITH STRUCTURAL."),
            _tok("note", "RETURN AIR PLENUM CROSSES FIRE-RATED WALL RW-2. PROVIDE FIRE DAMPER AND SMOKE DAMPER AT PENETRATION."),
            _tok("note", "VAV-201 ABOVE GWB CEILING. PROVIDE ACCESS PANEL 24\"x24\" IN CEILING BELOW FOR SERVICE."),
            _tok("note", "CONDENSATE DRAIN FROM AHU-1 TO NEAREST PLUMBING CONNECTION. PROVIDE P-TRAP AND AIR GAP."),
            _tok("note", "REFRIGERANT LINE SET FROM CU-1 TO INDOOR UNITS. VRF SYSTEM PIPING PER MANUFACTURER."),
            _tok("note", "OUTDOOR AIR VENTILATION PER ASHRAE 62.1. MINIMUM OA CFM SHOWN ON SCHEDULE."),
        ],
        equipment_tags=[
            _tok("equipment", "AHU-1", "AHU-1"),
            _tok("equipment", "RTU-2", "RTU-2"),
            _tok("equipment", "MAU-1", "MAU-1"),
            _tok("equipment", "VAV-201", "VAV-201"),
            _tok("equipment", "CU-1", "CU-1"),
            _tok("equipment", "EF-1", "EF-1"),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 23 05 00", "23 05 00"),
            _tok("spec_ref", "SECTION 23 73 00", "23 73 00"),
        ],
        callouts=[
            _tok("callout", "1/M-301", "1/M-301"),
        ],
        drawing_refs=[
            _tok("drawing_ref", "SEE S-101", "S-101"),
            _tok("drawing_ref", "SEE A-101", "A-101"),
        ],
        code_refs=[
            _tok("code_ref", "IMC 2021", "IMC 2021"),
            _tok("code_ref", "ASHRAE 62.1", "ASHRAE 62.1"),
        ],
    )


def _elec_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "MDP PANEL SCHEDULE: 480V 3PH. CONNECTED LOAD 350A. DEMAND LOAD 280A. AIC RATING 65 KAIC."),
            _tok("note", "PANEL LP-1A: 208/120V 1PH. CIRCUIT 1-20 LIGHTING. VERIFY VOLTAGE WITH MECHANICAL EQUIPMENT NAMEPLATE."),
            _tok("note", "GENERATOR 150KW DIESEL WITH ATS TRANSFER SWITCH. STANDBY POWER FOR EMERGENCY LIGHTING AND FIRE PUMP."),
            _tok("note", "CONDUIT ROUTING IN CEILING PLENUM. COORDINATE WITH DUCTWORK ROUTING ON MECHANICAL DRAWINGS."),
            _tok("note", "NEC 110.26 WORKING CLEARANCE 36 INCH MINIMUM AT ALL ELECTRICAL PANELS. VERIFY WALL DEPTH WITH ARCHITECTURAL."),
            _tok("note", "EMERGENCY LIGHTING AND EXIT SIGNS PER EGRESS PLAN. 1 FC MINIMUM AT EXIT PATH PER IBC."),
            _tok("note", "TRANSFORMER VAULT VENTILATION PER NEC 450.45. COORDINATE WITH MECHANICAL FOR EXHAUST FAN."),
            _tok("note", "DEDICATED DISCONNECT FOR AHU-1 AND RTU-2. CIRCUIT AND WIRE SIZE PER PANEL SCHEDULE."),
            _tok("note", "GFCI PROTECTION AT ALL OUTDOOR AND WET LOCATION RECEPTACLES PER NEC."),
            _tok("note", "FEEDER TO SUB-PANEL LP-2A: CONDUCTOR SIZE #2 AWG. VERIFY VOLTAGE DROP FOR CIRCUIT LENGTH."),
        ],
        equipment_tags=[
            _tok("equipment", "MDP", "MDP-1"),
            _tok("equipment", "LP-1A", "LP-1A"),
            _tok("equipment", "LP-2A", "LP-2A"),
            _tok("equipment", "ATS-1", "ATS-1"),
            _tok("equipment", "GEN-1", "GEN-1"),
            _tok("equipment", "AHU-1", "AHU-1"),
            _tok("equipment", "RTU-2", "RTU-2"),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 26 24 16", "26 24 16"),
            _tok("spec_ref", "SECTION 26 05 00", "26 05 00"),
        ],
        drawing_refs=[
            _tok("drawing_ref", "SEE M-101", "M-101"),
        ],
        code_refs=[
            _tok("code_ref", "NEC 2020", "NEC 2020"),
            _tok("code_ref", "NEC 110.26", "NEC 110.26"),
            _tok("code_ref", "NEC 450", "NEC 450"),
        ],
    )


def _plmb_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "WATER HEATER WH-1: 80 GALLON, 199000 BTU NATURAL GAS. FIXTURE UNIT DEMAND CALCULATION ON SCHEDULE."),
            _tok("note", "ROOF DRAIN RD-1 THROUGH RD-4 WITH OVERFLOW SCUPPER. DRAINAGE AREA PER IPC CALCULATION. LEADER SIZE 4\"."),
            _tok("note", "BACKFLOW PREVENTER RPZ IN UTILITY ROOM. PROVIDE FLOOR DRAIN WITHIN 2 FEET PER CODE."),
            _tok("note", "GREASE INTERCEPTOR AT KITCHEN. FOOD SERVICE WASTE LINE SEPARATE FROM SANITARY. SIZE PER IPC."),
            _tok("note", "WASTE PIPE SLOPE 1/4 INCH PER FOOT FOR 3\" AND SMALLER. GRADE AND INVERT ELEVATIONS ON PLAN."),
            _tok("note", "ADA LAVATORY WITH INSULATION KIT. KNEE CLEARANCE PER ICC A117.1. COORDINATE WITH ARCHITECTURAL."),
            _tok("note", "NATURAL GAS PIPING SIZED PER DEMAND. ROUTE AWAY FROM IGNITION SOURCES PER IFGC."),
            _tok("note", "SANITARY SEWER CONNECTION AT NORTH PROPERTY LINE. VERIFY INVERT AND CAPACITY WITH CIVIL."),
            _tok("note", "WATER HAMMER ARRESTOR AT FLUSH VALVE AND SOLENOID LOCATIONS. SIZE PER FIXTURE UNIT."),
            _tok("note", "PLUMBING VENT TERMINATION 10 FEET FROM AIR INTAKE AND OPERABLE WINDOWS."),
        ],
        equipment_tags=[
            _tok("equipment", "WH-1", "WH-1"),
            _tok("equipment", "BFP-1", "BFP-1"),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 22 10 00", "22 10 00"),
            _tok("spec_ref", "SECTION 22 40 00", "22 40 00"),
        ],
        code_refs=[
            _tok("code_ref", "IPC 2021", "IPC 2021"),
            _tok("code_ref", "IFGC 2021", "IFGC 2021"),
        ],
    )


def _fp_parsed() -> ParsedSheet:
    return ParsedSheet(
        notes=[
            _tok("note", "FIRE SPRINKLER SYSTEM PER NFPA 13. LIGHT HAZARD SPACING 15'-0\" MAX. HYDRAULIC DESIGN AREA ON PLAN."),
            _tok("note", "SPRINKLER HEAD PENDENT TYPE IN FINISHED CEILING. CONCEALED HEAD IN LOBBY. UPRIGHT IN MECHANICAL ROOM."),
            _tok("note", "FIRE PUMP 500 GPM AT 100 PSI. JOCKEY PUMP INCLUDED. RATED ENCLOSURE 2-HOUR WITH DRAIN AND VENTILATION."),
            _tok("note", "FDC LOCATION AT SOUTH ENTRY NEAR FIRE HYDRANT. VERIFY FIRE LANE ACCESS WITH CIVIL."),
            _tok("note", "STANDPIPE HOSE CONNECTION IN EACH STAIRWELL PER NFPA 14. VERIFY TRAVEL DISTANCE."),
            _tok("note", "CONCEALED SPACE ABOVE CEILING REQUIRES SPRINKLER PROTECTION WHERE COMBUSTIBLE PER NFPA 13."),
            _tok("note", "KITCHEN HOOD SUPPRESSION SYSTEM PER NFPA 96. ANSUL R-102 OR UL 300 LISTED SYSTEM."),
            _tok("note", "SPRINKLER RISER ROOM 6'-0\" x 8'-0\" MINIMUM. PROVIDE CLEARANCE FOR VALVES AND GAUGES."),
            _tok("note", "DUCT VS SPRINKLER MAIN ELEVATION CONFLICT AT CORRIDOR. SPRINKLER MAIN BELOW DUCT PER COORDINATION."),
            _tok("note", "WATER MAIN FIRE FLOW 1500 GPM AT 20 PSI RESIDUAL. VERIFY WITH CIVIL HYDRANT FLOW TEST."),
        ],
        spec_refs=[
            _tok("spec_ref", "SECTION 21 13 13", "21 13 13"),
        ],
        code_refs=[
            _tok("code_ref", "NFPA 13", "NFPA 13"),
            _tok("code_ref", "NFPA 14", "NFPA 14"),
            _tok("code_ref", "NFPA 96", "NFPA 96"),
        ],
        drawing_refs=[
            _tok("drawing_ref", "SEE A-101", "A-101"),
        ],
    )


_DEMO_PARSED["ARCH"] = _arch_parsed
_DEMO_PARSED["STR"] = _str_parsed
_DEMO_PARSED["MECH"] = _mech_parsed
_DEMO_PARSED["ELEC"] = _elec_parsed
_DEMO_PARSED["PLMB"] = _plmb_parsed
_DEMO_PARSED["FP"] = _fp_parsed


# ── Projects ────────────────────────────────────────────────

@api_bp.route("/projects", methods=["GET"])
def list_projects():
    conn = get_conn()
    rows = conn.execute(
        "SELECT p.id, p.name, p.building_type, p.square_feet, p.stories, p.scope, "
        "       p.notes, p.created_at, "
        "       (SELECT COUNT(*) FROM sheets WHERE project_id = p.id) as sheet_count, "
        "       (SELECT COUNT(*) FROM project_files WHERE project_id = p.id) as file_count "
        "FROM projects p ORDER BY p.id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@api_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Project name is required"}), 400

    building_type = data.get("building_type", "office")
    square_feet = data.get("square_feet", 50000)
    stories = data.get("stories", 2)
    scope = data.get("scope", "new_construction")
    notes = (data.get("notes") or "").strip()

    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO projects (name, building_type, square_feet, stories, scope, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (name, building_type, int(square_feet), int(stories), scope, notes),
    )
    conn.commit()
    pid = cursor.lastrowid
    conn.close()

    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    return jsonify({"id": pid, "name": name}), 201


@api_bp.route("/projects/<int:pid>", methods=["GET"])
def get_project(pid):
    conn = get_conn()
    row = conn.execute(
        "SELECT p.*, "
        "       (SELECT COUNT(*) FROM sheets WHERE project_id = p.id) as sheet_count, "
        "       (SELECT COUNT(*) FROM project_files WHERE project_id = p.id) as file_count "
        "FROM projects p WHERE p.id = ?",
        (pid,),
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(dict(row))


# ── File Upload & Ingestion ─────────────────────────────────

@api_bp.route("/projects/<int:pid>/upload", methods=["POST"])
def upload_files(pid):
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for f in files:
        if not f.filename:
            continue

        dest = proj_dir / f.filename
        f.save(str(dest))

        # Persist to Supabase so files survive Render restarts
        cloud.upload_file(dest, pid, f.filename)

        fhash = file_hash(str(dest))
        conn = get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO project_files (project_id, filename, filepath, file_hash, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (pid, f.filename, str(dest), fhash, "drawing"),
        )
        conn.commit()

        # Run extraction (requires PyMuPDF — gracefully skip if not installed)
        status = "processed"
        page_count = 0
        error_msg = None
        try:
            import fitz  # noqa: F401 — check if PyMuPDF available
            from ingestion.file_router import route_file
            result = route_file(str(dest))
            page_count = result.page_count

            # Classify sheets from extracted pages
            if result.pages:
                from classification.sheet_classifier import classify_sheets
                classified = classify_sheets(result.pages)
                for sheet in classified:
                    conn.execute(
                        "INSERT OR IGNORE INTO sheets "
                        "(project_id, file_id, page_number, sheet_id, discipline, confidence) "
                        "VALUES (?, (SELECT id FROM project_files WHERE project_id=? AND filename=?), ?, ?, ?, ?)",
                        (pid, pid, f.filename, sheet.get("page", 0),
                         sheet.get("sheet_id", ""), sheet.get("discipline", ""),
                         sheet.get("confidence", 0)),
                    )
                    conn.commit()

        except Exception as e:
            status = "error"
            error_msg = str(e)

        conn.execute(
            "UPDATE project_files SET page_count = ?, status = ? "
            "WHERE project_id = ? AND filename = ?",
            (page_count, status, pid, f.filename),
        )
        conn.commit()
        conn.close()

        results.append({
            "filename": f.filename,
            "status": status,
            "page_count": page_count,
            "error": error_msg,
        })

    return jsonify({"uploaded": len(results), "results": results})


@api_bp.route("/projects/<int:pid>/files", methods=["GET"])
def list_files(pid):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, file_type, page_count, status, uploaded_at "
        "FROM project_files WHERE project_id = ? ORDER BY uploaded_at DESC",
        (pid,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── Sheets ──────────────────────────────────────────────────

@api_bp.route("/projects/<int:pid>/sheets", methods=["GET"])
def list_sheets(pid):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, sheet_id, sheet_name, discipline, page_number, confidence "
        "FROM sheets WHERE project_id = ? ORDER BY sheet_id",
        (pid,),
    ).fetchall()
    conn.close()

    sheets = [dict(r) for r in rows]

    # Build discipline summary
    disc_counts = {}
    for s in sheets:
        d = s.get("discipline") or "?"
        disc_counts[d] = disc_counts.get(d, 0) + 1

    avg_conf = 0
    if sheets:
        avg_conf = sum(s.get("confidence") or 0 for s in sheets) / len(sheets)

    return jsonify({
        "sheets": sheets,
        "total": len(sheets),
        "disciplines": disc_counts,
        "avg_confidence": round(avg_conf, 3),
    })


# ── Plan Review / Conflicts ────────────────────────────────

@api_bp.route("/projects/<int:pid>/review", methods=["POST"])
def run_review(pid):
    conn = get_conn()
    sheets = conn.execute(
        "SELECT sheet_id, discipline FROM sheets WHERE project_id = ?",
        (pid,),
    ).fetchall()
    conn.close()

    if not sheets:
        return jsonify({"error": "No classified sheets found. Process files first."}), 400

    try:
        from analysis.conflict_detector import detect_conflicts
        from analysis.cross_reference import CrossReferenceMap
        from classification.entity_extractor import SheetEntities

        # Build synthetic entities from DB sheets with realistic parsed data
        entities_list = []
        disc_present = {}
        for s in sheets:
            sid = s["sheet_id"]
            disc = s["discipline"]
            ent = SheetEntities(
                sheet_id=sid,
                page=0,
                discipline_code=disc,
                discipline_name=disc,
            )
            ent.parsed = _build_demo_parsed(disc)
            entities_list.append(ent)
            if disc not in disc_present:
                disc_present[disc] = []
            disc_present[disc].append(sid)

        # Build cross-reference map with equipment refs from parsed data
        equip_refs = {}
        for ent in entities_list:
            for tag in ent.parsed.equipment_tags:
                equip_refs.setdefault(tag.value, []).append(ent.sheet_id)
        xref = CrossReferenceMap(
            disciplines_present=disc_present,
            equipment_refs=equip_refs,
            all_equipment=set(equip_refs.keys()),
        )

        # Get suppressed rules
        from learning.feedback_store import get_suppressed_rules as get_suppressed
        suppressed = get_suppressed(pid)

        # Run detection
        result = detect_conflicts(entities_list, xref, suppressed)

        conflict_list = [c.to_dict() for c in result.conflicts]

        return jsonify({
            "sheets_analyzed": len(sheets),
            "disciplines": len(disc_present),
            "conflicts": conflict_list,
            "total_conflicts": len(conflict_list),
            "rules_checked": result.rules_checked,
            "rules_triggered": result.rules_triggered,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/projects/<int:pid>/conflicts", methods=["GET"])
def get_conflicts(pid):
    # Conflicts are computed on-demand via /review POST
    # This returns stored results if available
    return jsonify({"conflicts": [], "note": "Run POST /review to generate conflicts"})


# ── RFIs ────────────────────────────────────────────────────

@api_bp.route("/projects/<int:pid>/rfis", methods=["POST"])
def generate_rfis(pid):
    data = request.get_json() or {}
    conflicts = data.get("conflicts", [])

    if not conflicts:
        return jsonify({"error": "No conflicts provided. Run plan review first."}), 400

    conn = get_conn()
    project = conn.execute("SELECT name FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()

    if not project:
        return jsonify({"error": "Project not found"}), 404

    try:
        from analysis.rfi_generator import generate_rfis as gen_rfis
        from analysis.conflict_detector import Conflict, DetectionResult

        # Rebuild Conflict objects from the JSON dicts
        conflict_objs = []
        for c in conflicts:
            conflict_objs.append(Conflict(
                conflict_id=c.get("conflict_id", ""),
                rule_id=c.get("rule_id", ""),
                rule_name=c.get("rule_name", ""),
                severity=c.get("severity", "INFO"),
                category=c.get("category", ""),
                description=c.get("description", ""),
                sheets_involved=c.get("sheets_involved", []),
                disciplines=c.get("disciplines", []),
                evidence=c.get("evidence", []),
                location=c.get("location", ""),
                suggested_action=c.get("suggested_action", ""),
            ))

        det_result = DetectionResult(conflicts=conflict_objs)
        rfi_log = gen_rfis(det_result, project["name"])
        rfi_list = [
            {
                "number": r.rfi_number,
                "subject": r.subject,
                "question": r.question,
                "severity": r.severity,
                "priority": r.priority,
                "discipline": r.discipline,
                "sheets": ", ".join(r.sheets_referenced),
                "status": "Open",
            }
            for r in rfi_log.rfis
        ]
        return jsonify({"rfis": rfi_list, "total": len(rfi_list)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/projects/<int:pid>/rfis", methods=["GET"])
def list_rfis(pid):
    return jsonify({"rfis": [], "note": "RFIs are generated via POST"})


@api_bp.route("/projects/<int:pid>/rfis/export", methods=["POST"])
def export_rfis(pid):
    data = request.get_json() or {}
    rfis = data.get("rfis", [])

    conn = get_conn()
    project = conn.execute("SELECT name FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()

    if not project:
        return jsonify({"error": "Project not found"}), 404

    try:
        from output.rfi_excel import write_rfi_excel_from_dicts

        output_dir = Path(PROJECTS_DIR) / str(pid)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "rfi_log.xlsx"

        write_rfi_excel_from_dicts(rfis, out_path, project["name"])
        return send_file(str(out_path), as_attachment=True, download_name="rfi_log.xlsx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Schedule ────────────────────────────────────────────────

@api_bp.route("/projects/<int:pid>/schedule", methods=["POST"])
def generate_schedule(pid):
    data = request.get_json() or {}
    start_date_str = data.get("start_date", "2026-04-01")

    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Project not found"}), 404

    project = dict(row)

    try:
        from scheduling.schedule_export import generate_schedule as gen_sched

        output_dir = Path(PROJECTS_DIR) / str(pid)
        output_dir.mkdir(parents=True, exist_ok=True)

        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")

        scope = project.get("scope", "new_construction") or "new_construction"

        result = gen_sched(
            project_name=project["name"],
            building_type=project["building_type"],
            square_feet=project["square_feet"],
            stories=project.get("stories", 1) or 1,
            start_date=start_dt,
            output_dir=output_dir,
            scope=scope,
        )

        if "error" in result:
            return jsonify(result), 400

        # WBS division names for Gantt grouping (CSI MasterFormat)
        _WBS_NAMES = {
            "01": "General Requirements",
            "02": "Site Construction / Demo",
            "03": "Concrete",
            "05": "Metals / Structural Steel",
            "07": "Thermal & Moisture Protection",
            "08": "Openings",
            "09": "Finishes",
            "10": "Specialties",
            "15": "Mechanical",
            "16": "Electrical",
        }

        # Serialize activities for Gantt chart
        gantt_data = []
        activities = result.get("activities_data", [])
        if activities:
            from scheduling.cpm_engine import day_to_date
            from datetime import timedelta
            for act in activities:
                s = day_to_date(act.early_start, start_dt)
                f = day_to_date(act.early_finish, start_dt)
                if f <= s:
                    f = s + timedelta(days=1)
                wbs_code = act.wbs.split(".")[0] if act.wbs else "01"
                gantt_data.append({
                    "id": act.activity_id,
                    "task": act.activity_name,
                    "start": s.strftime("%Y-%m-%d"),
                    "end": f.strftime("%Y-%m-%d"),
                    "duration": act.duration,
                    "wbs": wbs_code,
                    "wbs_name": _WBS_NAMES.get(wbs_code, "General"),
                    "critical": act.total_float == 0,
                    "float": act.total_float,
                    "milestone": act.is_milestone,
                    "predecessors": [
                        {"id": p["activity_id"], "type": p.get("rel_type", "FS"), "lag": p.get("lag", 0)}
                        for p in act.predecessors
                    ],
                })

        return jsonify({
            "total_activities": result["total_activities"],
            "project_duration_days": result["project_duration_days"],
            "critical_activities": result["critical_activities"],
            "milestones": result.get("milestones", 0),
            "start_date": start_date_str,
            "excel_path": result.get("excel_path", ""),
            "wbs_text": result.get("wbs_text", ""),
            "critical_path": result.get("critical_path", []),
            "gantt_data": gantt_data,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/projects/<int:pid>/schedule", methods=["GET"])
def get_schedule(pid):
    return jsonify({"note": "Generate schedule via POST first"})


# ── Exports ─────────────────────────────────────────────────

@api_bp.route("/projects/<int:pid>/exports", methods=["GET"])
def list_exports(pid):
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    if not proj_dir.exists():
        return jsonify({"files": []})

    files = []
    patterns = {
        "RFI Log": "rfi_log*.xlsx",
        "Schedule": "*schedule*.xlsx",
        "Report": "*report*.txt",
        "Data": "*.json",
    }
    for category, pattern in patterns.items():
        for f in proj_dir.glob(pattern):
            files.append({
                "filename": f.name,
                "category": category,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    files.sort(key=lambda x: x["modified"], reverse=True)
    return jsonify({"files": files})


@api_bp.route("/projects/<int:pid>/exports/<filename>", methods=["GET"])
def download_export(pid, filename):
    proj_dir = Path(PROJECTS_DIR) / str(pid)
    file_path = proj_dir / filename

    if not file_path.exists() or not file_path.is_relative_to(proj_dir):
        return jsonify({"error": "File not found"}), 404

    return send_file(str(file_path), as_attachment=True, download_name=filename)


@api_bp.route("/projects/<int:pid>/report", methods=["POST"])
def generate_report(pid):
    conn = get_conn()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()

    if not project:
        return jsonify({"error": "Project not found"}), 404

    proj_dir = Path(PROJECTS_DIR) / str(pid)
    proj_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "=" * 70,
        "  DABO Plan Review Report",
        f"  Project: {project['name']}",
        f"  Type: {project['building_type']} | SF: {project['square_feet']:,}",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 70,
        "",
        "Export generated from dashboard. Run full Plan Review",
        "and Schedule for detailed results.",
        "",
        "=" * 70,
        "  End of Report",
        "=" * 70,
    ]
    out_path = proj_dir / "summary_report.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")

    return jsonify({"message": "Report generated", "filename": "summary_report.txt"})


# ── Feedback ────────────────────────────────────────────────

@api_bp.route("/projects/<int:pid>/feedback", methods=["POST"])
def record_feedback(pid):
    data = request.get_json() or {}

    try:
        from learning.feedback_store import record_feedback as store_fb
        row_id = store_fb(
            project_id=pid,
            conflict_id=data.get("conflict_id", ""),
            action=data.get("action", "note"),
            original_severity=data.get("original_severity", ""),
            adjusted_severity=data.get("adjusted_severity", ""),
            user_note=data.get("user_note", ""),
        )
        return jsonify({"id": row_id, "message": "Feedback recorded"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/projects/<int:pid>/metrics", methods=["GET"])
def get_metrics(pid):
    try:
        from learning.metrics import calculate_metrics
        metrics = calculate_metrics(pid)
        return jsonify(metrics.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Rules ───────────────────────────────────────────────────

@api_bp.route("/rules/suppress", methods=["POST"])
def suppress_rule():
    data = request.get_json() or {}
    rule_id = data.get("rule_id")
    project_id = data.get("project_id")

    if not rule_id:
        return jsonify({"error": "rule_id is required"}), 400

    try:
        from learning.feedback_store import record_rule_adjustment
        row_id = record_rule_adjustment(
            rule_id=rule_id,
            adjustment_type="suppress",
            project_id=project_id,
        )
        return jsonify({"id": row_id, "message": f"Rule {rule_id} suppressed"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/rules/suppressed/<int:pid>", methods=["GET"])
def get_suppressed_rules(pid):
    from learning.feedback_store import get_suppressed_rules as get_suppressed
    rules = get_suppressed(pid)
    return jsonify({"suppressed": sorted(rules)})


@api_bp.route("/rules/all", methods=["GET"])
def list_all_rules():
    from config.conflict_rules import CONFLICT_RULES
    rules = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "severity": r.severity,
            "disciplines": r.disciplines,
        }
        for r in CONFLICT_RULES.values()
    ]
    return jsonify({"rules": rules})


# ── Markups (Bluebeam / PDF Annotations) ──────────────────

@api_bp.route("/projects/<int:pid>/markups", methods=["GET"])
def list_markups(pid):
    sheet_filter = request.args.get("sheet_id", "")
    conn = get_conn()
    if sheet_filter:
        rows = conn.execute(
            "SELECT * FROM markups WHERE project_id = ? AND sheet_id = ? ORDER BY page_number, id",
            (pid, sheet_filter),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM markups WHERE project_id = ? ORDER BY sheet_id, page_number, id",
            (pid,),
        ).fetchall()
    conn.close()

    markups = [dict(r) for r in rows]

    # Summary stats
    by_type = {}
    by_author = {}
    for m in markups:
        t = m.get("markup_type", "other")
        by_type[t] = by_type.get(t, 0) + 1
        a = m.get("author", "Unknown")
        by_author[a] = by_author.get(a, 0) + 1

    return jsonify({
        "markups": markups,
        "total": len(markups),
        "by_type": by_type,
        "by_author": by_author,
    })
