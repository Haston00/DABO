"""
Claude API integration for supplementary plan review.

Four use cases:
  1. Ambiguous callout interpretation
  2. RFI question drafting (professional GC language)
  3. Non-obvious conflict identification
  4. Schedule logic generation

System works without API — if ANTHROPIC_API_KEY is not set, these
functions return gracefully with a flag indicating AI was not used.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_ENABLED
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AIReviewResult:
    success: bool
    content: str = ""
    model: str = ""
    tokens_used: int = 0
    error: str = ""


def _get_client():
    """Lazy-load the Anthropic client."""
    if not CLAUDE_ENABLED:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        log.warning("anthropic package not installed")
        return None
    except Exception as e:
        log.warning("Failed to create Anthropic client: %s", e)
        return None


def _call_claude(system_prompt: str, user_prompt: str) -> AIReviewResult:
    """Make a single Claude API call."""
    client = _get_client()
    if not client:
        return AIReviewResult(success=False, error="Claude API not available")

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text if response.content else ""
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return AIReviewResult(
            success=True,
            content=content,
            model=CLAUDE_MODEL,
            tokens_used=tokens,
        )
    except Exception as e:
        log.error("Claude API call failed: %s", e)
        return AIReviewResult(success=False, error=str(e))


# ── Use Case 1: Ambiguous Callout Interpretation ─────────

CALLOUT_SYSTEM = """You are a commercial construction plan reviewer.
You interpret ambiguous callouts, notes, and abbreviations found on construction drawings.
Give a clear interpretation with a confidence score (HIGH/MEDIUM/LOW).
If you can't determine the meaning, say so and suggest what the GC should ask in an RFI."""


def interpret_callout(callout_text: str, sheet_context: str = "") -> AIReviewResult:
    """Interpret an ambiguous callout or notation."""
    prompt = f"""Interpret this callout from a commercial construction drawing:

Callout: {callout_text}
Sheet context: {sheet_context}

Provide:
1. Most likely interpretation
2. Confidence (HIGH/MEDIUM/LOW)
3. If LOW confidence, draft an RFI question"""

    return _call_claude(CALLOUT_SYSTEM, prompt)


# ── Use Case 2: RFI Question Drafting ─────────────────────

RFI_SYSTEM = """You are a senior project manager at a commercial general contractor.
You draft RFIs (Requests for Information) to architects and engineers.
Your tone is professional, specific, and references exact sheet numbers and details.
Each RFI should clearly state the issue, reference the specific drawing/spec location,
and ask a pointed question that gets a definitive answer."""


def draft_rfi_question(conflict_description: str, sheets: list[str], evidence: list[str]) -> AIReviewResult:
    """Draft a professional RFI question from a detected conflict."""
    prompt = f"""Draft an RFI for the following coordination issue:

Issue: {conflict_description}
Sheets involved: {', '.join(sheets)}
Evidence: {'; '.join(evidence)}

Format:
- Subject line (brief)
- Description of the issue with specific references
- Question to A/E (clear, answerable)
- Suggested resolution (if you have one)"""

    return _call_claude(RFI_SYSTEM, prompt)


# ── Use Case 3: Non-Obvious Conflict Identification ──────

CONFLICT_SYSTEM = """You are an expert MEP coordinator for commercial construction.
You review summaries of drawing set entities looking for coordination issues
that automated rules might miss. Focus on:
- Spatial conflicts between disciplines
- Missing information that should be present
- Inconsistencies between sheets
- Code compliance concerns
Be specific. Reference sheet numbers and entity types."""


def supplementary_review(sheet_summaries: list[dict]) -> AIReviewResult:
    """Run AI review on sheet summaries to find issues rules missed."""
    # Truncate to keep within token limits
    summary_text = ""
    for s in sheet_summaries[:20]:  # Max 20 sheets
        summary_text += f"\nSheet {s.get('sheet_id', '?')} ({s.get('discipline', '?')}):\n"
        summary_text += f"  Spec refs: {s.get('spec_refs', [])}\n"
        summary_text += f"  Equipment: {s.get('equipment', [])}\n"
        summary_text += f"  Drawing refs: {s.get('drawing_refs', [])}\n"
        summary_text += f"  Notes (first 3): {s.get('notes', [])[:3]}\n"

    prompt = f"""Review these sheet summaries from a commercial construction drawing set.
Identify any coordination issues, missing information, or potential conflicts
that automated rules might miss.

{summary_text}

List each issue with:
1. Issue description
2. Sheets involved
3. Severity (CRITICAL/MAJOR/MINOR)
4. Recommended action"""

    return _call_claude(CONFLICT_SYSTEM, prompt)


# ── Use Case 4: Schedule Logic Generation ─────────────────

SCHEDULE_SYSTEM = """You are a CPM scheduling expert for commercial construction.
You generate activity lists with predecessor logic based on project scope.
Use standard CSI division sequencing. All activities should have:
- WBS code
- Activity name
- Duration (working days)
- Predecessors (FS, SS, FF with lags where appropriate)
Format as structured data."""


def generate_schedule_logic(
    building_type: str, square_feet: int, stories: int,
    disciplines_present: list[str],
) -> AIReviewResult:
    """Generate preliminary schedule logic from project parameters."""
    prompt = f"""Generate a CPM schedule activity list for:

Building type: {building_type}
Square footage: {square_feet:,} SF
Stories: {stories}
Disciplines present: {', '.join(disciplines_present)}

Provide activities organized by CSI division with:
- WBS code (XX.XX format)
- Activity name
- Duration (working days)
- Predecessors (activity code, relationship type FS/SS/FF, lag days)

Focus on the critical path. Include milestones for permits, inspections, and substantial completion."""

    return _call_claude(SCHEDULE_SYSTEM, prompt)


def is_available() -> bool:
    """Check if Claude API is configured and accessible."""
    return CLAUDE_ENABLED
