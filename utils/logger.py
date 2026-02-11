"""
Structured logging for DABO.

Every module calls:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Processing sheet %s", sheet_id)

Logs go to both console (INFO+) and file (DEBUG+).
"""
import logging
import sys
from pathlib import Path

from config.settings import LOG_FILE

_INITIALIZED = False


def _init_logging():
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("dabo")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — DEBUG and above
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'dabo' namespace."""
    _init_logging()
    return logging.getLogger(f"dabo.{name}")
