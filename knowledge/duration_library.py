"""
Activity duration library — stores learned durations from completed projects.

Over time as DABO processes more projects, actual durations can be fed back
to improve production rate estimates.
"""
from __future__ import annotations

from utils.db import get_conn
from utils.logger import get_logger

log = get_logger(__name__)


def get_default_durations() -> dict[str, dict[str, int]]:
    """
    Return default durations from production_rates.
    This is the starting point before any learning happens.
    """
    from config.production_rates import PRODUCTION_RATES, FIXED_DURATIONS
    return {
        "per_sf_rates": {k: v for k, v in PRODUCTION_RATES.items()},
        "fixed_durations": dict(FIXED_DURATIONS),
    }
