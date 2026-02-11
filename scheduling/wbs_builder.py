"""
WBS (Work Breakdown Structure) hierarchy generation.

Builds a WBS tree from activities organized by CSI division.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from scheduling.cpm_engine import Activity


@dataclass
class WBSNode:
    code: str
    name: str
    level: int = 0
    activities: list[Activity] = field(default_factory=list)
    children: list["WBSNode"] = field(default_factory=list)

    @property
    def total_duration(self) -> int:
        own = sum(a.duration for a in self.activities)
        child = sum(c.total_duration for c in self.children)
        return own + child

    @property
    def activity_count(self) -> int:
        own = len(self.activities)
        child = sum(c.activity_count for c in self.children)
        return own + child


# Division code → name mapping for WBS
_DIV_NAMES = {
    "01": "General Requirements",
    "02": "Site Construction",
    "03": "Concrete",
    "04": "Masonry",
    "05": "Metals / Structural Steel",
    "06": "Wood & Plastics",
    "07": "Thermal & Moisture Protection",
    "08": "Openings",
    "09": "Finishes",
    "10": "Specialties",
    "11": "Equipment",
    "12": "Furnishings",
    "13": "Special Construction",
    "14": "Conveying Equipment",
    "15": "Mechanical",
    "16": "Electrical",
}


def build_wbs(activities: list[Activity], project_name: str = "Project") -> WBSNode:
    """Build a WBS tree from activities grouped by their WBS code (CSI division)."""
    root = WBSNode(code="00", name=project_name, level=0)

    # Group activities by WBS division
    by_div: dict[str, list[Activity]] = {}
    for act in activities:
        div = act.wbs if act.wbs else "01"
        by_div.setdefault(div, []).append(act)

    # Create division nodes
    for div_code in sorted(by_div.keys()):
        div_name = _DIV_NAMES.get(div_code, f"Division {div_code}")
        node = WBSNode(
            code=div_code,
            name=div_name,
            level=1,
            activities=by_div[div_code],
        )
        root.children.append(node)

    return root


def wbs_to_text(node: WBSNode, indent: int = 0) -> str:
    """Format WBS tree as indented text."""
    lines = []
    prefix = "  " * indent
    count = node.activity_count
    dur = node.total_duration
    lines.append(f"{prefix}{node.code} {node.name} ({count} activities, {dur} days)")
    for act in node.activities:
        lines.append(f"{prefix}  {act.activity_id} {act.activity_name} ({act.duration}d)")
    for child in node.children:
        lines.append(wbs_to_text(child, indent + 1))
    return "\n".join(lines)
