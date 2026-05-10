"""Validator orchestrator: parse + run all rule modules.

Public API:
    lint(text, filename) -> (blocks, findings)

Backward-compat: same signature/return as the legacy bbe_comm_lint module.
"""

from __future__ import annotations

from .parser import parse_blocks
from .model import Block, Finding
from .rules import ALL_PER_BLOCK_CHECKS, CROSS_BLOCK_CHECKS


def lint(text: str, filename: str = "<input>") -> tuple[list[Block], list[Finding]]:
    """Parse `text`, run all rules, return (blocks, findings).

    Findings are sorted by (line, check_id) for stable output.
    """
    blocks, findings = parse_blocks(text)
    for f in findings:
        f.file = filename
    for b in blocks:
        for check in ALL_PER_BLOCK_CHECKS:
            for finding in check(b):
                finding.file = filename
                findings.append(finding)
        for cross_check in CROSS_BLOCK_CHECKS:
            for finding in cross_check(b, blocks):
                finding.file = filename
                findings.append(finding)
    findings.sort(key=lambda f: (f.line, f.check_id))
    return blocks, findings
