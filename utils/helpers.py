"""
Small utility functions — dates, file ops, path helpers.
"""
import hashlib
import re
from datetime import datetime
from pathlib import Path


def timestamp_str() -> str:
    """Return current time as a filename-safe string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def file_hash(path: Path, algo: str = "sha256") -> str:
    """Compute hex digest of a file (for dedup / change detection)."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize_filename(name: str) -> str:
    """Strip characters that are illegal in Windows filenames."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it doesn't exist; return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def human_size(nbytes: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def normalize_sheet_id(raw: str) -> str:
    """
    Normalize a sheet identifier for consistent matching.
    'A - 101', 'A101', 'a-101' all become 'A-101'.
    """
    raw = raw.upper().strip()
    # collapse spaces around dashes
    raw = re.sub(r"\s*-\s*", "-", raw)
    # replace space between letters and digits with dash (A 101 → A-101)
    raw = re.sub(r"^([A-Z]+)\s+(\d)", r"\1-\2", raw)
    # insert dash if missing between letter(s) and digits (A101 → A-101)
    raw = re.sub(r"^([A-Z]+)(\d)", r"\1-\2", raw)
    return raw


def extract_page_number(text: str) -> str | None:
    """
    Try to pull a sheet number from the first few lines of page text.
    Looks for patterns like 'A-101', 'S2.01', 'M-001', 'E101'.
    """
    pattern = r"\b([A-Z]{1,3}[-.\s]?\d{1,3}(?:[.\-]\d{1,3})?)\b"
    match = re.search(pattern, text[:500])
    if match:
        return normalize_sheet_id(match.group(1))
    return None
