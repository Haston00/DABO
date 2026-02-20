"""
Database connection manager + schema bootstrap.

Uses Supabase Postgres when DATABASE_URL is set (production on Render),
falls back to local SQLite for development.

Usage:
    from utils.db import get_conn
    conn = get_conn()
    conn.execute("INSERT INTO projects ...")
    conn.commit()
    conn.close()
"""
import os
import sqlite3
from pathlib import Path

from config.settings import DB_PATH
from utils.logger import get_logger

log = get_logger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ── Postgres schema (Supabase) ─────────────────────────────

_PG_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    building_type   TEXT,
    square_feet     INTEGER,
    stories         INTEGER,
    scope           TEXT DEFAULT 'new_construction',
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS project_files (
    id          SERIAL PRIMARY KEY,
    project_id  INTEGER NOT NULL REFERENCES projects(id),
    filename    TEXT NOT NULL,
    filepath    TEXT,
    file_hash   TEXT,
    file_type   TEXT,
    file_size   INTEGER,
    page_count  INTEGER,
    status      TEXT DEFAULT 'pending',
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, filename)
);

CREATE TABLE IF NOT EXISTS sheets (
    id              SERIAL PRIMARY KEY,
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
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    run_type        TEXT NOT NULL,
    started_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMPTZ,
    files_processed INTEGER DEFAULT 0,
    sheets_found    INTEGER DEFAULT 0,
    conflicts_found INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'running',
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    conflict_id     TEXT,
    action          TEXT NOT NULL,
    original_severity TEXT,
    adjusted_severity TEXT,
    user_note       TEXT,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_adjustments (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER,
    rule_id         TEXT NOT NULL,
    adjustment_type TEXT NOT NULL,
    value           TEXT,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS markups (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    sheet_id        TEXT,
    markup_type     TEXT NOT NULL,
    label           TEXT,
    content         TEXT,
    author          TEXT,
    color           TEXT,
    page_number     INTEGER,
    x               REAL,
    y               REAL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

# ── SQLite schema (local dev fallback) ──────────────────────

_SQLITE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    building_type   TEXT,
    square_feet     INTEGER,
    stories         INTEGER,
    scope           TEXT DEFAULT 'new_construction',
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

CREATE TABLE IF NOT EXISTS markups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    sheet_id        TEXT,
    markup_type     TEXT NOT NULL,
    label           TEXT,
    content         TEXT,
    author          TEXT,
    color           TEXT,
    page_number     INTEGER,
    x               REAL,
    y               REAL,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""


def _use_postgres() -> bool:
    return bool(DATABASE_URL)


# ── Postgres connection (dict-like rows) ────────────────────

class _PgDictRow:
    """Wrap psycopg2 row to support both dict(row) and row[key] and row[0]."""
    def __init__(self, cursor, row):
        self._data = {}
        self._values = list(row)
        if cursor.description:
            self._data = {desc[0]: val for desc, val in zip(cursor.description, row)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __iter__(self):
        return iter(self._data)


class _PgCursorWrapper:
    """Wraps psycopg2 cursor to translate ? -> %s and return dict-like rows."""
    def __init__(self, real_cursor):
        self._cur = real_cursor
        self.lastrowid = None
        self.description = None

    def execute(self, sql, params=None):
        # Track if this was originally an INSERT OR IGNORE
        was_ignore = "INSERT OR IGNORE" in sql.upper()
        sql = sql.replace("?", "%s")
        sql = sql.replace("INSERT OR IGNORE", "INSERT")
        sql = sql.replace("insert or ignore", "INSERT")
        # Convert INSERT OR IGNORE → INSERT ... ON CONFLICT DO NOTHING
        if was_ignore and "ON CONFLICT" not in sql.upper():
            # Strip any trailing RETURNING that _PgConnWrapper added, re-add after
            returning_clause = ""
            if "RETURNING" in sql.upper():
                idx = sql.upper().rfind("RETURNING")
                returning_clause = " " + sql[idx:]
                sql = sql[:idx].rstrip()
            sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING" + returning_clause
        self._cur.execute(sql, params)
        self.description = self._cur.description
        # Get lastrowid for INSERT via RETURNING or cursor attribute
        if sql.strip().upper().startswith("INSERT"):
            try:
                # Try to get the inserted ID
                if self._cur.description and self._cur.rowcount > 0:
                    row = self._cur.fetchone()
                    if row:
                        self.lastrowid = row[0]
                        return self
            except Exception:
                pass
            self.lastrowid = 0
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _PgDictRow(self._cur, row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [_PgDictRow(self._cur, r) for r in rows]

    def close(self):
        self._cur.close()


class _PgConnWrapper:
    """Wraps psycopg2 connection to behave like sqlite3 connection."""
    def __init__(self, real_conn):
        self._conn = real_conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        wrapper = _PgCursorWrapper(cur)
        # For INSERTs, add RETURNING id to get lastrowid
        stripped = sql.strip()
        if stripped.upper().startswith("INSERT") and "RETURNING" not in stripped.upper():
            sql = stripped.rstrip(";") + " RETURNING id"
        wrapper.execute(sql, params)
        return wrapper

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(sql)
        self._conn.commit()
        cur.close()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._conn.close()


def _get_pg_conn() -> _PgConnWrapper:
    """Get a Postgres connection via psycopg2."""
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return _PgConnWrapper(conn)


# ── SQLite connection (local dev) ───────────────────────────

def _sqlite_migrate(conn: sqlite3.Connection):
    """Add columns that may be missing from older databases."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()}
    if "scope" not in cols:
        conn.execute("ALTER TABLE projects ADD COLUMN scope TEXT DEFAULT 'new_construction'")
        conn.commit()


def _get_sqlite_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SQLITE_SCHEMA_SQL)
    _sqlite_migrate(conn)
    return conn


# ── Public API ──────────────────────────────────────────────

def get_conn():
    """
    Return a database connection.

    Uses Supabase Postgres when DATABASE_URL is set,
    otherwise falls back to local SQLite.
    """
    if _use_postgres():
        return _get_pg_conn()
    return _get_sqlite_conn()


def init_db():
    """Bootstrap the database schema (called at startup)."""
    if _use_postgres():
        log.info("Using Supabase Postgres: %s", DATABASE_URL[:40] + "...")
        conn = _get_pg_conn()
        conn.executescript(_PG_SCHEMA_SQL)
        conn.close()
    else:
        log.info("Using local SQLite: %s", DB_PATH)
        conn = _get_sqlite_conn()
        conn.execute("SELECT 1")
        conn.close()
