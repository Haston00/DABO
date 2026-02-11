"""
AI-assisted schedule logic generation.

Uses Claude API to refine schedule logic based on project-specific
conditions extracted from the drawing set.
"""
from __future__ import annotations

from analysis.ai_reviewer import generate_schedule_logic, is_available
from utils.logger import get_logger

log = get_logger(__name__)


def get_ai_schedule_suggestions(
    building_type: str,
    square_feet: int,
    stories: int,
    disciplines: list[str],
) -> dict:
    """
    Get AI-generated schedule suggestions.

    Returns a dict with suggestions or empty if AI is unavailable.
    """
    if not is_available():
        return {"available": False, "message": "Claude API not configured"}

    result = generate_schedule_logic(building_type, square_feet, stories, disciplines)

    if result.success:
        return {
            "available": True,
            "suggestions": result.content,
            "tokens_used": result.tokens_used,
        }
    else:
        return {
            "available": False,
            "error": result.error,
        }
