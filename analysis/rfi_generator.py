"""
RFI generator — convert detected conflicts into structured RFI entries.

Each RFI entry contains:
  - Sequential RFI number
  - Subject line
  - Description with sheet references
  - Question to A/E
  - Severity / priority
  - Status tracking fields

Can optionally use Claude AI to draft professional RFI language.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from analysis.conflict_detector import Conflict, DetectionResult
from analysis.ai_reviewer import draft_rfi_question, is_available as ai_available
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class RFIEntry:
    rfi_number: int
    subject: str
    description: str
    question: str
    sheets_referenced: list[str] = field(default_factory=list)
    spec_sections: list[str] = field(default_factory=list)
    discipline: str = ""
    severity: str = ""           # CRITICAL, MAJOR, MINOR
    priority: str = ""           # URGENT, HIGH, NORMAL, LOW
    status: str = "OPEN"
    conflict_id: str = ""
    rule_id: str = ""
    ai_drafted: bool = False
    created_date: str = ""
    response: str = ""
    response_date: str = ""

    def to_dict(self) -> dict:
        return {
            "rfi_number": self.rfi_number,
            "subject": self.subject,
            "description": self.description,
            "question": self.question,
            "sheets_referenced": self.sheets_referenced,
            "spec_sections": self.spec_sections,
            "discipline": self.discipline,
            "severity": self.severity,
            "priority": self.priority,
            "status": self.status,
            "conflict_id": self.conflict_id,
            "rule_id": self.rule_id,
            "ai_drafted": self.ai_drafted,
            "created_date": self.created_date,
        }


@dataclass
class RFILog:
    """Complete RFI log for a project."""
    project_name: str
    rfis: list[RFIEntry] = field(default_factory=list)
    generated_date: str = ""

    @property
    def total(self) -> int:
        return len(self.rfis)

    @property
    def critical_count(self) -> int:
        return sum(1 for r in self.rfis if r.severity == "CRITICAL")

    @property
    def major_count(self) -> int:
        return sum(1 for r in self.rfis if r.severity == "MAJOR")

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "total_rfis": self.total,
            "critical": self.critical_count,
            "major": self.major_count,
            "generated_date": self.generated_date,
            "rfis": [r.to_dict() for r in self.rfis],
        }


_SEVERITY_TO_PRIORITY = {
    "CRITICAL": "URGENT",
    "MAJOR": "HIGH",
    "MINOR": "NORMAL",
    "INFO": "LOW",
}


def generate_rfis(
    detection_result: DetectionResult,
    project_name: str = "Untitled Project",
    use_ai: bool = True,
) -> RFILog:
    """
    Generate an RFI log from conflict detection results.

    Args:
        detection_result: Output from conflict_detector
        project_name: Project name for the log
        use_ai: Whether to use Claude API for RFI drafting
    """
    rfi_log = RFILog(
        project_name=project_name,
        generated_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    rfi_number = 0
    use_claude = use_ai and ai_available()

    for conflict in detection_result.conflicts:
        if conflict.suppressed:
            continue

        rfi_number += 1
        rfi = _conflict_to_rfi(conflict, rfi_number)

        # Optionally enhance with AI-drafted language
        if use_claude and conflict.severity in ("CRITICAL", "MAJOR"):
            ai_result = draft_rfi_question(
                conflict.description,
                conflict.sheets_involved,
                conflict.evidence,
            )
            if ai_result.success and ai_result.content:
                _apply_ai_draft(rfi, ai_result.content)
                rfi.ai_drafted = True

        rfi_log.rfis.append(rfi)

    log.info(
        "Generated %d RFIs: %d CRITICAL, %d MAJOR, %d MINOR",
        rfi_log.total, rfi_log.critical_count, rfi_log.major_count,
        sum(1 for r in rfi_log.rfis if r.severity == "MINOR"),
    )
    return rfi_log


def _conflict_to_rfi(conflict: Conflict, rfi_number: int) -> RFIEntry:
    """Convert a single conflict into an RFI entry."""
    # Build question from conflict data
    sheets_str = ", ".join(conflict.sheets_involved) if conflict.sheets_involved else "N/A"
    evidence_str = "; ".join(conflict.evidence) if conflict.evidence else ""

    question = (
        f"Please clarify the following coordination issue "
        f"identified on sheet(s) {sheets_str}: {conflict.description}"
    )
    if conflict.suggested_action:
        question += f" Suggested resolution: {conflict.suggested_action}"

    return RFIEntry(
        rfi_number=rfi_number,
        subject=f"{conflict.rule_name} — {sheets_str}",
        description=conflict.description,
        question=question,
        sheets_referenced=conflict.sheets_involved,
        discipline=", ".join(conflict.disciplines),
        severity=conflict.severity,
        priority=_SEVERITY_TO_PRIORITY.get(conflict.severity, "NORMAL"),
        conflict_id=conflict.conflict_id,
        rule_id=conflict.rule_id,
        created_date=datetime.now().strftime("%Y-%m-%d"),
    )


def _apply_ai_draft(rfi: RFIEntry, ai_content: str) -> None:
    """Replace RFI fields with AI-drafted content if it looks good."""
    lines = ai_content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.lower().startswith("subject"):
            rfi.subject = line.split(":", 1)[-1].strip() if ":" in line else rfi.subject
        elif line.lower().startswith("description") or line.lower().startswith("issue"):
            rfi.description = line.split(":", 1)[-1].strip() if ":" in line else rfi.description
        elif line.lower().startswith("question"):
            rfi.question = line.split(":", 1)[-1].strip() if ":" in line else rfi.question
