"""Compliance-level rules — checks 019 (value pattern) and 023 (over-claim).

RC2 update: HMAC alone is L4, NOT L5. L5 requires @x-bbe-sig OR @x-bbe-ledger
OR @x-bbe-attest. The over-claim check honours this.
"""

from __future__ import annotations

from ..constants import COMPLIANCE_LEVEL_RE
from ..model import Block, Finding
from ..score import compute_level


def check_019_compliance_level_value(b: Block) -> list[Finding]:
    if "compliance_level" not in b.headers:
        return []
    v = b.headers["compliance_level"]
    if not COMPLIANCE_LEVEL_RE.match(v):
        return [Finding("BBE-COMM-019", "error", "§8.2",
                        f"@compliance_level '{v}' must be one of L0, L1, L2, L3, L4, L5",
                        b.header_lines.get("compliance_level", b.open_line), b.label)]
    return []


def check_023_compliance_overclaim(b: Block) -> list[Finding]:
    if "compliance_level" not in b.headers:
        return []
    declared_raw = b.headers["compliance_level"]
    if not COMPLIANCE_LEVEL_RE.match(declared_raw):
        return []  # 019 handles bad-format
    declared = int(declared_raw[1])
    computed = compute_level(b)
    if declared > computed:
        return [Finding("BBE-COMM-023", "error", "§8.2",
                        f"@compliance_level declared L{declared} exceeds computed L{computed}. "
                        f"Under-claiming is harmless; over-claiming is rejected. "
                        f"(RC2: HMAC alone is L4, not L5; L5 requires @x-bbe-sig / "
                        f"@x-bbe-ledger / @x-bbe-attest.)",
                        b.header_lines.get("compliance_level", b.open_line), b.label)]
    return []


ALL = [check_019_compliance_level_value, check_023_compliance_overclaim]
