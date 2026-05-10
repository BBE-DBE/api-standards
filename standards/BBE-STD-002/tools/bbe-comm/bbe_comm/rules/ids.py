"""ID rules — checks 011 (id pattern), 012 (canonical type-slug match),
014 (parent_id pattern). Check 013 (lineage) lives in lineage.py.
"""

from __future__ import annotations

import re

from ..constants import CANONICAL_ID_RE, INTEROP_ID_RE, TYPE_TO_SLUG
from ..model import Block, Finding

_SLUG_PREFIX_RE = re.compile(r"^([a-z][a-z0-9_]*?)_(\d{4}-\d{2}-\d{2}T)")


def check_011_id_pattern(b: Block) -> list[Finding]:
    if "id" not in b.headers:
        return []
    v = b.headers["id"]
    if CANONICAL_ID_RE.match(v) or INTEROP_ID_RE.match(v):
        return []
    return [Finding("BBE-COMM-011", "error", "§6",
                    f"@id '{v}' violates ID pattern. "
                    f"Canonical form: <type-slug>_<YYYY-MM-DDTHH-MM-SSZ>_<hex8>; "
                    f"interop form: ^[a-z]{{3,16}}_[A-Za-z0-9_-]{{8,64}}$",
                    b.header_lines.get("id", b.open_line), b.label)]


def check_012_canonical_slug_match(b: Block) -> list[Finding]:
    """Warn if @id type-slug does not match @type per RC2 §6.2."""
    if "id" not in b.headers or "type" not in b.headers:
        return []
    v = b.headers["id"]
    if not CANONICAL_ID_RE.match(v):
        return []
    m = _SLUG_PREFIX_RE.match(v)
    if not m:
        return []
    actual_slug = m.group(1)
    expected_slug = TYPE_TO_SLUG.get(b.headers["type"])
    if expected_slug and actual_slug != expected_slug:
        return [Finding("BBE-COMM-012", "warning", "§6.2",
                        f"@id type-slug '{actual_slug}' does not match @type '{b.headers['type']}' "
                        f"(expected slug: '{expected_slug}')",
                        b.header_lines.get("id", b.open_line), b.label)]
    return []


def check_014_parent_id_pattern(b: Block) -> list[Finding]:
    if "parent_id" not in b.headers:
        return []
    v = b.headers["parent_id"]
    if CANONICAL_ID_RE.match(v) or INTEROP_ID_RE.match(v):
        return []
    return [Finding("BBE-COMM-014", "error", "§6.4",
                    f"@parent_id '{v}' violates id pattern",
                    b.header_lines.get("parent_id", b.open_line), b.label)]


ALL = [check_011_id_pattern, check_012_canonical_slug_match, check_014_parent_id_pattern]
