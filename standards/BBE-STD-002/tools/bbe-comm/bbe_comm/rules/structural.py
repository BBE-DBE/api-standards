"""Structural rules — checks 004 (label pattern), 020 (header contiguity),
021 (same-type nesting). Checks 001..003 fire during parse.
"""

from __future__ import annotations

from ..constants import LABEL_RE, HEADER_RE
from ..model import Block, Finding


def check_004_label_pattern(b: Block) -> list[Finding]:
    if not LABEL_RE.match(b.label):
        return [Finding("BBE-COMM-004", "error", "§4.2",
                        f"Label '{b.label}' violates pattern ^[A-Z][A-Z0-9_-]*$",
                        b.open_line, b.label)]
    return []


def check_020_header_contiguous(b: Block) -> list[Finding]:
    """Detect header-shaped lines in body (header should be contiguous at top)."""
    findings: list[Finding] = []
    body_lines = b.body_text.split("\n") if b.body_text else []
    for i, line in enumerate(body_lines):
        if HEADER_RE.match(line):
            findings.append(Finding(
                "BBE-COMM-020", "warning", "§4.2",
                f"Header-shaped line '{line.strip()[:60]}' appears in body — "
                f"headers must be contiguous at top of body",
                b.body_start_line + i, b.label,
            ))
    return findings


def check_021_same_type_nesting(b: Block, all_blocks: list[Block]) -> list[Finding]:
    """A block of type T MUST NOT nest within another block of type T."""
    if not b.parent_label:
        return []
    my_type = b.headers.get("type")
    if not my_type:
        return []
    for other in all_blocks:
        if other is b:
            continue
        if other.label != b.parent_label:
            continue
        if other.open_line < b.open_line and other.close_line > b.close_line:
            other_type = other.headers.get("type")
            if other_type == my_type:
                return [Finding("BBE-COMM-021", "error", "§4.2",
                                f"Block of @type '{my_type}' is nested inside another "
                                f"block of @type '{my_type}' (same-type nesting forbidden — "
                                f"prevents lineage ambiguity)",
                                b.open_line, b.label)]
            break
    return []


ALL = [check_004_label_pattern, check_020_header_contiguous]
CROSS_BLOCK = [check_021_same_type_nesting]
