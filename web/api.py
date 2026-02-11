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

api_bp = Blueprint("api", __name__, url_prefix="/api")


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

        # Build synthetic entities from DB sheets (same as Streamlit dashboard)
        entities_list = []
        disc_present = {}
        for s in sheets:
            sid = s["sheet_id"]
            disc = s["discipline"]
            entities_list.append(SheetEntities(
                sheet_id=sid,
                page=0,
                discipline_code=disc,
                discipline_name=disc,
            ))
            if disc not in disc_present:
                disc_present[disc] = []
            disc_present[disc].append(sid)

        # Build cross-reference map
        xref = CrossReferenceMap(
            disciplines_present=disc_present,
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
        rfi_log = gen_rfis(conflicts, project["name"])
        rfi_list = [
            {
                "number": r.number,
                "subject": r.subject,
                "question": r.question,
                "severity": r.severity,
                "priority": r.priority,
                "discipline": r.discipline,
                "sheets": r.sheets,
                "status": "Open",
            }
            for r in rfi_log.entries
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
