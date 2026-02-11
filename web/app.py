"""
DABO Flask web app — main entry point.

Serves the splash screen, dashboard, and API routes.
Run locally:  python web/app.py
Cloud deploy:  gunicorn web.app:app
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, redirect, url_for

from utils.db import init_db


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB
    app.secret_key = os.environ.get("SECRET_KEY", "dabo-mccrory-2026")

    # Bootstrap database
    init_db()

    # Auto-seed the demo project if DB is empty
    _seed_if_empty()

    # Register API blueprint
    from web.api import api_bp
    app.register_blueprint(api_bp)

    # ── Page routes ─────────────────────────────────────

    @app.route("/")
    def splash():
        return render_template("splash.html")

    @app.route("/dashboard")
    @app.route("/dashboard/<page>")
    def dashboard(page="projects"):
        valid_pages = [
            "projects", "ingestion", "sheets", "review",
            "rfis", "schedule", "exports", "feedback",
        ]
        if page not in valid_pages:
            page = "projects"

        # Get sidebar data
        from utils.db import get_conn
        conn = get_conn()
        projects = conn.execute(
            "SELECT id, name, building_type, square_feet, stories FROM projects ORDER BY id DESC"
        ).fetchall()
        project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        sheet_count = conn.execute("SELECT COUNT(*) FROM sheets").fetchone()[0]
        conn.close()

        return render_template(
            "dashboard.html",
            page=page,
            projects=[dict(p) for p in projects],
            project_count=project_count,
            sheet_count=sheet_count,
        )

    return app


def _seed_if_empty():
    """Auto-seed demo projects on first run or if missing."""
    from utils.db import get_conn
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    conn.close()
    if count < 3:
        # Wipe and re-seed to get all 3 demo projects
        conn = get_conn()
        for table in ["feedback", "rule_adjustments", "processing_runs",
                       "sheets", "project_files", "projects"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        from seed_test_project import seed
        seed()


# Module-level app for gunicorn: `gunicorn web.app:app`
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"\n  DABO Web Dashboard")
    print(f"  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
