"""Extension rules — checks 017 (custom field needs @x- prefix), 018
(@x- vendor namespace shape).
"""

from __future__ import annotations

from ..constants import (
    ALL_RESERVED_FIELDS, FORBIDDEN_AUTH_INFERENCE_FIELDS, EXTENSION_FIELD_RE,
)
from ..model import Block, Finding


def check_017_extension_field_naming(b: Block) -> list[Finding]:
    findings: list[Finding] = []
    for key in b.headers:
        if key in ALL_RESERVED_FIELDS:
            continue
        if key in FORBIDDEN_AUTH_INFERENCE_FIELDS:
            continue  # 016 handles these
        if not key.startswith("x-"):
            findings.append(Finding(
                "BBE-COMM-017", "error", "§5.6",
                f"Custom header @{key} is not in reserved set and lacks @x- extension prefix",
                b.header_lines.get(key, b.open_line), b.label,
            ))
    return findings


def check_018_extension_vendor_namespace(b: Block) -> list[Finding]:
    findings: list[Finding] = []
    for key in b.headers:
        if not key.startswith("x-"):
            continue
        if key in ALL_RESERVED_FIELDS:
            continue  # x-bbe-sig etc. are explicitly reserved
        if not EXTENSION_FIELD_RE.match(key):
            findings.append(Finding(
                "BBE-COMM-018", "warning", "§5.6",
                f"Extension @{key} should follow @x-<vendor>-<field> form "
                f"(vendor 2-32 lowercase chars, then dash, then field)",
                b.header_lines.get(key, b.open_line), b.label,
            ))
    return findings


ALL = [check_017_extension_field_naming, check_018_extension_vendor_namespace]
