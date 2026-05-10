"""Lineage rule — check 013 (non-root non-prompt missing @parent_id at L4+)."""

from __future__ import annotations

import re

from ..constants import ROOT_TYPES
from ..model import Block, Finding

_LEVEL_RE = re.compile(r"^L([0-5])$")


def _parse_level(s: str | None) -> int:
    if not s:
        return 4  # default enforcement floor
    m = _LEVEL_RE.match(s)
    return int(m.group(1)) if m else 4


def check_013_lineage_parent_id(b: Block) -> list[Finding]:
    """Non-root blocks at L4+ must have @parent_id."""
    t = b.headers.get("type")
    if t is None:
        return []
    if t in ROOT_TYPES:
        return []
    declared_level = _parse_level(b.headers.get("compliance_level"))
    enforced_level = max(declared_level, 4)  # L4 default enforcement
    if enforced_level >= 4 and "parent_id" not in b.headers:
        return [Finding("BBE-COMM-013", "error", "§5.1",
                        f"L{enforced_level} non-root @type '{t}' is missing @parent_id "
                        f"(lineage integrity required for authorization-safe operations)",
                        b.open_line, b.label)]
    return []


ALL = [check_013_lineage_parent_id]
