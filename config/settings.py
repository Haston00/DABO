"""
DABO global settings — paths, API keys, parameters.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dabo.db"
PROJECTS_DIR = DATA_DIR / "projects"
TEMPLATES_DIR = DATA_DIR / "templates"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "dabo.log"

# ── Claude API ─────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_ENABLED = bool(ANTHROPIC_API_KEY)

# ── PDF Engine ─────────────────────────────────────────
# Minimum characters on a page before falling back to OCR
OCR_FALLBACK_THRESHOLD = 50
# Tesseract path (Windows default)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# DPI for rasterizing pages to images (OCR fallback)
OCR_DPI = 300

# ── Processing ─────────────────────────────────────────
# Max file size in MB for upload
MAX_UPLOAD_MB = 500
# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

# ── Scheduling ─────────────────────────────────────────
DEFAULT_WORKDAYS_PER_WEEK = 5
DEFAULT_HOURS_PER_DAY = 8

# ── Database ───────────────────────────────────────────
DB_SCHEMA_VERSION = 1
