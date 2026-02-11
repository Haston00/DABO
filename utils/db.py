"""
SQLite connection manager + schema bootstrap.

Usage:
    from utils.db import get_conn
    with get_conn() as conn:
        conn.execute("INSERT INTO projects ...")
"""
import sqlite3
from pathlib import Path

from config.settings import DB_PATH

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    building_type   TEXT,
    square_feet     INTEGER,
    stories         INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS project_files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id),
    filename    TEXT NOT NULL,
    filepath    TEXT,
    file_hash   TEXT,
    file_type   TEXT,
    file_size   INTEGER,
    page_count  INTEGER,
    status      TEXT DEFAULT 'pending',
    uploaded_at TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, filename)
);

CREATE TABLE IF NOT EXISTS sheets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    file_id         INTEGER REFERENCES project_files(id),
    page_number     INTEGER,
    sheet_id        TEXT,
    sheet_name      TEXT,
    discipline      TEXT,
    discipline_code TEXT,
    discipline_name TEXT,
    title           TEXT,
    confidence      REAL,
    text_length     INTEGER,
    ocr_used        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS processing_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    run_type        TEXT NOT NULL,
    started_at      TEXT DEFAULT (datetime('now')),
    finished_at     TEXT,
    files_processed INTEGER DEFAULT 0,
    sheets_found    INTEGER DEFAULT 0,
    conflicts_found INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'running',
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    conflict_id     TEXT,
    action          TEXT NOT NULL,
    original_severity TEXT,
    adjusted_severity TEXT,
    user_note       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rule_adjustments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER,
    rule_id         TEXT NOT NULL,
    adjustment_type TEXT NOT NULL,
    value           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    """
    Return a SQLite connection with WAL mode and foreign keys enabled.
    Creates the database and tables on first call.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    return conn


def init_db():
    """Explicitly bootstrap the database (called at startup)."""
    with get_conn() as conn:
        conn.execute("SELECT 1")
