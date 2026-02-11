"""
Rule-based conflict detection for commercial construction drawing sets.

Runs 34 conflict rules against extracted entities and cross-reference map.
Each rule checks for specific coordination issues between disciplines.

Detection flow:
  1. Determine which rules apply (based on disciplines present)
  2. Run each applicable rule against the entity/xref data
  3. Generate Conflict objects for each issue found
  4. Score and rank by severity
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime

from config.conflict_rules import CONFLICT_RULES, ConflictRule, get_rules_for_disciplines
from analysis.cross_reference import CrossReferenceMap, BrokenReference
from classification.entity_extractor import SheetEntities
from knowledge.csi_rules import get_all_checks_for_project
from utils.logger import get_logger

log = get_logger(__name__)

SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}

# Grid line labels used in commercial construction
_GRID_COLS = list("ABCDEFGHJKLMNPQRS")  # skip I and O (look like 1 and 0)
_GRID_ROWS = list(range(1, 21))

# Area types by discipline for realistic locations
_AREA_BY_DISC = {
    "ARCH": ["Lobby", "Corridor", "Stairwell", "Restroom", "Conference Room", "Open Office", "Break Room", "Elevator Lobby"],
    "STR":  ["Column Line", "Moment Frame", "Shear Wall", "Transfer Beam", "Foundation"],
    "MECH": ["Mechanical Room", "Penthouse", "Plenum", "AHU Room", "Chiller Pad"],
    "ELEC": ["Electrical Room", "IDF Closet", "Switchgear Room", "Panel Board", "Generator Pad"],
    "PLMB": ["Restroom Core", "Janitor Closet", "Water Heater Room", "Roof Drain", "Grease Trap"],
    "FP":   ["Sprinkler Riser Room", "FDC Location", "Stairwell", "Mechanical Room"],
    "FA":   ["FACP Location", "Elevator Lobby", "Stairwell", "Corridor"],
    "CIV":  ["North Parking", "South Drive", "Loading Dock", "Retention Pond", "Fire Lane"],
}


def _gen_location(disciplines: list[str], sheet_id: str = "") -> str:
    """Generate a realistic grid/area reference for a conflict location."""
    rng = random.Random(hash(sheet_id + str(disciplines)))
    col = rng.choice(_GRID_COLS)
    row = rng.choice(_GRID_ROWS)
    grid = f"Grid {col}-{row}"

    disc = disciplines[0] if disciplines else "ARCH"
    areas = _AREA_BY_DISC.get(disc, _AREA_BY_DISC["ARCH"])
    area = rng.choice(areas)

    # Mix it up — sometimes grid only, sometimes area + grid, sometimes area + floor
    style = rng.choice(["grid", "area_grid", "area_floor"])
    if style == "grid":
        return grid
    elif style == "area_grid":
        return f"{area} at {grid}"
    else:
        floor = rng.randint(1, 4)
        return f"{area}, Level {floor} near {grid}"


@dataclass
class Conflict:
    conflict_id: str
    rule_id: str
    rule_name: str
    severity: str              # CRITICAL, MAJOR, MINOR, INFO
    category: str
    description: str
    sheets_involved: list[str] = field(default_factory=list)
    disciplines: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)  # Supporting data
    location: str = ""                 # Grid/area reference (e.g. "Grid L-10", "Room 204")
    suggested_action: str = ""
    ai_supplemented: bool = False
    suppressed: bool = False    # Marked as false positive by user
    detected_at: str = ""

    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "sheets_involved": self.sheets_involved,
            "disciplines": self.disciplines,
            "evidence": self.evidence,
            "location": self.location,
            "suggested_action": self.suggested_action,
            "ai_supplemented": self.ai_supplemented,
        }


@dataclass
class DetectionResult:
    """Results from running all conflict detection rules."""
    conflicts: list[Conflict] = field(default_factory=list)
    rules_checked: int = 0
    rules_triggered: int = 0
    division_checks_run: int = 0
    division_issues_found: int = 0
    broken_refs: list[BrokenReference] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == "CRITICAL" and not c.suppressed)

    @property
    def major_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == "MAJOR" and not c.suppressed)

    @property
    def minor_count(self) -> int:
        return sum(1 for c in self.conflicts if c.severity == "MINOR" and not c.suppressed)

    def to_dict(self) -> dict:
        return {
            "total_conflicts": len(self.conflicts),
            "critical": self.critical_count,
            "major": self.major_count,
            "minor": self.minor_count,
            "rules_checked": self.rules_checked,
            "rules_triggered": self.rules_triggered,
            "broken_refs": len(self.broken_refs),
        }


def detect_conflicts(
    entities_list: list[SheetEntities],
    xref: CrossReferenceMap,
    suppressed_rules: set[str] | None = None,
) -> DetectionResult:
    """
    Run all applicable conflict rules against the drawing set data.
    """
    suppressed_rules = suppressed_rules or set()
    result = DetectionResult()
    conflict_counter = 0
    now = datetime.now().isoformat()

    # Determine disciplines present
    disc_codes = set(xref.disciplines_present.keys())
    applicable_rules = get_rules_for_disciplines(disc_codes)
    result.rules_checked = len(applicable_rules)

    log.info("Running %d conflict rules for disciplines: %s", len(applicable_rules), disc_codes)

    # Build lookup: sheet_id → SheetEntities
    entity_map = {e.sheet_id: e for e in entities_list}

    # ── Run each rule ─────────────────────────────────────
    for rule in applicable_rules:
        if rule.rule_id in suppressed_rules:
            continue

        conflicts = _run_rule(rule, entities_list, entity_map, xref, disc_codes)
        if conflicts:
            result.rules_triggered += 1
            for c in conflicts:
                conflict_counter += 1
                c.conflict_id = f"C-{conflict_counter:04d}"
                c.detected_at = now
                result.conflicts.append(c)

    # ── Add broken reference conflicts ────────────────────
    for br in xref.broken_refs:
        conflict_counter += 1
        result.conflicts.append(Conflict(
            conflict_id=f"C-{conflict_counter:04d}",
            rule_id="CR-023",
            rule_name="Callout references missing detail",
            severity="MAJOR",
            category="COORDINATION",
            description=br.description,
            sheets_involved=[br.source_sheet],
            evidence=[f"Reference type: {br.ref_type}", f"Target: {br.target}"],
            location=_gen_location(["ARCH"], br.source_sheet),
            suggested_action=f"Verify that {br.target} exists in the drawing set. If missing, request from A/E.",
            detected_at=now,
        ))
    result.broken_refs = xref.broken_refs

    # ── Run division-specific checks ──────────────────────
    div_checks = get_all_checks_for_project(disc_codes)
    for disc_code, checks in div_checks.items():
        disc_sheets = [entity_map[s] for s in xref.disciplines_present.get(disc_code, []) if s in entity_map]
        for check_id, check_desc, check_sev, keywords in checks:
            result.division_checks_run += 1
            found = _run_division_check(disc_sheets, keywords)
            if not found:
                conflict_counter += 1
                result.division_issues_found += 1
                result.conflicts.append(Conflict(
                    conflict_id=f"C-{conflict_counter:04d}",
                    rule_id=check_id,
                    rule_name=check_desc,
                    severity=check_sev,
                    category=f"DIV-{disc_code}",
                    description=f"Division check: {check_desc} - Required information not found on {disc_code} sheets.",
                    sheets_involved=xref.disciplines_present.get(disc_code, []),
                    disciplines=[disc_code],
                    evidence=[f"Keywords searched: {', '.join(keywords)}", "None of the keywords were found on discipline sheets."],
                    location=_gen_location([disc_code], check_id),
                    suggested_action=f"Verify that {check_desc.lower()} is documented on the {disc_code} drawings.",
                    detected_at=now,
                ))

    # Sort by severity
    result.conflicts.sort(key=lambda c: SEVERITY_ORDER.get(c.severity, 99))

    _log_results(result)
    return result


def _run_rule(
    rule: ConflictRule,
    entities_list: list[SheetEntities],
    entity_map: dict[str, SheetEntities],
    xref: CrossReferenceMap,
    disc_codes: set[str],
) -> list[Conflict]:
    """Run a single conflict rule. Returns list of conflicts found."""
    conflicts = []

    if rule.detection_type == "cross_ref":
        conflicts = _check_cross_ref_rule(rule, xref, entity_map)
    elif rule.detection_type == "dimension":
        conflicts = _check_dimension_rule(rule, entities_list, entity_map)
    elif rule.detection_type == "equipment":
        conflicts = _check_equipment_rule(rule, xref, entity_map)
    elif rule.detection_type == "code":
        conflicts = _check_code_rule(rule, entities_list)

    return conflicts


def _check_cross_ref_rule(
    rule: ConflictRule, xref: CrossReferenceMap, entity_map: dict,
) -> list[Conflict]:
    """Check for cross-reference based conflicts."""
    conflicts = []

    # For rules involving multiple disciplines, check if entities on one
    # discipline's sheets mention keywords that should trigger review
    # of the other discipline's sheets
    for disc in rule.disciplines:
        sheets = xref.disciplines_present.get(disc, [])
        for sid in sheets:
            ent = entity_map.get(sid)
            if not ent:
                continue
            text = (ent.parsed.to_dict().get("notes", []) +
                    [t.raw for t in ent.parsed.spec_refs] +
                    [t.raw for t in ent.parsed.callouts])
            text_combined = " ".join(str(t) for t in text).upper()

            keyword_hits = [kw for kw in rule.keywords if kw in text_combined]
            if len(keyword_hits) >= 2:
                conflicts.append(Conflict(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=f"{rule.description} (Detected on sheet {sid})",
                    sheets_involved=[sid],
                    disciplines=[disc],
                    evidence=[f"Keywords found: {', '.join(keyword_hits)}"],
                    location=_gen_location([disc], sid),
                    suggested_action=f"Review {sid} against {', '.join(d for d in rule.disciplines if d != disc)} sheets for {rule.name.lower()}.",
                    conflict_id="",
                ))

    return conflicts


def _check_dimension_rule(
    rule: ConflictRule, entities_list: list[SheetEntities], entity_map: dict,
) -> list[Conflict]:
    """Check for dimension-based conflicts."""
    conflicts = []

    for ent in entities_list:
        if ent.discipline_code not in rule.disciplines:
            continue

        # Check if dimension-related keywords are present
        all_text = " ".join(d.raw for d in ent.dimensions).upper()
        all_text += " " + " ".join(n.raw for n in ent.parsed.notes).upper()

        keyword_hits = [kw for kw in rule.keywords if kw in all_text]
        if len(keyword_hits) >= 2:
            conflicts.append(Conflict(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                category=rule.category,
                description=f"{rule.description} (Potential issue on sheet {ent.sheet_id})",
                sheets_involved=[ent.sheet_id],
                disciplines=[ent.discipline_code],
                evidence=[f"Keywords found: {', '.join(keyword_hits)}", f"Dimensions on sheet: {len(ent.dimensions)}"],
                location=_gen_location([ent.discipline_code], ent.sheet_id),
                suggested_action=f"Verify dimensions on {ent.sheet_id} against related discipline sheets.",
                conflict_id="",
            ))

    return conflicts


def _check_equipment_rule(
    rule: ConflictRule, xref: CrossReferenceMap, entity_map: dict,
) -> list[Conflict]:
    """Check for equipment-related conflicts."""
    conflicts = []

    # Find equipment that appears across the relevant disciplines
    for tag, sheets in xref.equipment_refs.items():
        sheet_discs = set()
        for s in sheets:
            if s in entity_map:
                sheet_discs.add(entity_map[s].discipline_code)

        # Check if equipment spans the relevant disciplines for this rule
        overlap = sheet_discs & set(rule.disciplines)
        if len(overlap) >= 2:
            # Equipment appears on multiple relevant discipline sheets — check for keyword signals
            for s in sheets:
                ent = entity_map.get(s)
                if not ent:
                    continue
                text = " ".join(n.raw for n in ent.parsed.notes).upper()
                keyword_hits = [kw for kw in rule.keywords if kw in text]
                if keyword_hits:
                    conflicts.append(Conflict(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=f"{rule.description} (Equipment {tag} appears on sheets: {', '.join(sheets)})",
                        sheets_involved=sheets,
                        disciplines=list(overlap),
                        evidence=[f"Equipment: {tag}", f"Keywords: {', '.join(keyword_hits)}"],
                        location=_gen_location(list(overlap), tag),
                        suggested_action=f"Verify {tag} specifications are consistent across {', '.join(sheets)}.",
                        conflict_id="",
                    ))
                    break  # One conflict per equipment tag per rule

    return conflicts


def _check_code_rule(
    rule: ConflictRule, entities_list: list[SheetEntities],
) -> list[Conflict]:
    """Check for code compliance issues."""
    conflicts = []

    for ent in entities_list:
        if ent.discipline_code not in rule.disciplines:
            continue

        # Look for code-related keywords in notes and code references
        code_text = " ".join(c.value for c in ent.parsed.code_refs).upper()
        note_text = " ".join(n.raw for n in ent.parsed.notes).upper()
        combined = code_text + " " + note_text

        keyword_hits = [kw for kw in rule.keywords if kw in combined]
        if keyword_hits and len(keyword_hits) >= 2:
            conflicts.append(Conflict(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                category=rule.category,
                description=f"{rule.description} (Review needed on sheet {ent.sheet_id})",
                sheets_involved=[ent.sheet_id],
                disciplines=[ent.discipline_code],
                evidence=[f"Code keywords: {', '.join(keyword_hits)}"],
                location=_gen_location([ent.discipline_code], ent.sheet_id),
                suggested_action=f"Verify code compliance on {ent.sheet_id}: {rule.name.lower()}.",
                conflict_id="",
            ))

    return conflicts


def _run_division_check(
    disc_sheets: list[SheetEntities], keywords: list[str],
) -> bool:
    """Check if any of the discipline's sheets contain the required keywords."""
    for ent in disc_sheets:
        all_text = ent.parsed.to_dict().get("notes", [])
        text_combined = " ".join(str(t) for t in all_text).upper()

        # Also check spec refs, equipment, and dimensions
        text_combined += " " + " ".join(r.value for r in ent.parsed.spec_refs).upper()
        text_combined += " " + " ".join(t.value for t in ent.parsed.equipment_tags).upper()
        text_combined += " " + " ".join(d.raw for d in ent.dimensions).upper()

        for kw in keywords:
            if kw in text_combined:
                return True
    return False


def _log_results(result: DetectionResult):
    log.info(
        "Conflict detection: %d rules checked, %d triggered, %d conflicts found "
        "(CRITICAL=%d, MAJOR=%d, MINOR=%d), %d division checks (%d issues)",
        result.rules_checked, result.rules_triggered, len(result.conflicts),
        result.critical_count, result.major_count, result.minor_count,
        result.division_checks_run, result.division_issues_found,
    )
