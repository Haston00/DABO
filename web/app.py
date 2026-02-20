"""
DABO Flask web app — main entry point.

Serves the splash screen, dashboard, and API routes.
Run locally:  python web/app.py
Cloud deploy:  gunicorn web.app:app
"""
import os
import sys
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, redirect, url_for, request

from utils.db import init_db


def _start_keep_alive(url, interval=840):
    """Ping our own healthz endpoint every 14 min to prevent Render free tier sleep."""
    def _ping():
        import urllib.request
        while True:
            time.sleep(interval)
            try:
                urllib.request.urlopen(url, timeout=10)
            except Exception:
                pass
    t = threading.Thread(target=_ping, daemon=True)
    t.start()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400  # Cache static files 24h
    app.secret_key = os.environ.get("SECRET_KEY", "dabo-mccrory-2026")

    # Bootstrap database
    init_db()

    # Auto-seed the demo project if DB is empty
    _seed_if_empty()

    # Register API blueprint
    from web.api import api_bp
    app.register_blueprint(api_bp)

    # Cache headers for static assets
    @app.after_request
    def add_cache_headers(response):
        if 'static' in (response.headers.get('X-Accel-Redirect', '') or request.path):
            response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

    # ── Health check (keeps Render from sleeping) ──────

    @app.route("/healthz")
    def healthz():
        return "ok", 200

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

# Keep Render free tier alive — self-ping every 14 minutes
_RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if _RENDER_URL:
    _start_keep_alive(f"{_RENDER_URL}/healthz")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"\n  DABO Web Dashboard")
    print(f"  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
