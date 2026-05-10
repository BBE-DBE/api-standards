"""Header rules — checks 005..010 (required @bbe-comm/@type, semver,
supported major, type registry, status registry).
"""

from __future__ import annotations

from ..constants import (
    PROTOCOL_VERSION_RE, SUPPORTED_PROTOCOL_MAJOR,
    REGISTERED_TYPES, EXTENSION_TYPE_RE, REGISTERED_STATUSES_BY_TYPE,
)
from ..model import Block, Finding


def check_005_bbe_comm_present(b: Block) -> list[Finding]:
    if "bbe-comm" not in b.headers:
        return [Finding("BBE-COMM-005", "error", "§5.1",
                        "Missing required header @bbe-comm (protocol version)",
                        b.open_line, b.label)]
    return []


def check_006_type_present(b: Block) -> list[Finding]:
    if "type" not in b.headers:
        return [Finding("BBE-COMM-006", "error", "§5.1",
                        "Missing required header @type",
                        b.open_line, b.label)]
    return []


def check_007_protocol_version_format(b: Block) -> list[Finding]:
    v = b.headers.get("bbe-comm")
    if v is None:
        return []
    if not PROTOCOL_VERSION_RE.match(v):
        return [Finding("BBE-COMM-007", "error", "§11",
                        f"@bbe-comm value '{v}' is not semver MAJOR.MINOR[.PATCH]",
                        b.header_lines.get("bbe-comm", b.open_line), b.label)]
    return []


def check_008_protocol_version_supported(b: Block) -> list[Finding]:
    v = b.headers.get("bbe-comm")
    if v is None or not PROTOCOL_VERSION_RE.match(v):
        return []
    major = int(v.split(".")[0])
    if major not in SUPPORTED_PROTOCOL_MAJOR:
        return [Finding("BBE-COMM-008", "error", "§11",
                        f"@bbe-comm major version {major} unsupported "
                        f"(value '{v}', supported majors: {sorted(SUPPORTED_PROTOCOL_MAJOR)})",
                        b.header_lines.get("bbe-comm", b.open_line), b.label)]
    return []


def check_009_type_in_registry(b: Block) -> list[Finding]:
    t = b.headers.get("type")
    if t is None:
        return []
    if t in REGISTERED_TYPES:
        return []
    if EXTENSION_TYPE_RE.match(t):
        return []
    return [Finding("BBE-COMM-009", "error", "§5.4",
                    f"@type '{t}' not in registered types and not in x-<vendor>-<type> form. "
                    f"Registered: {sorted(REGISTERED_TYPES)}",
                    b.header_lines.get("type", b.open_line), b.label)]


def check_010_status_in_registry(b: Block) -> list[Finding]:
    t = b.headers.get("type")
    s = b.headers.get("status")
    if not (t and s):
        return []
    if t not in REGISTERED_STATUSES_BY_TYPE:
        return []
    if s in REGISTERED_STATUSES_BY_TYPE[t]:
        return []
    return [Finding("BBE-COMM-010", "warning", "§5.5",
                    f"@status '{s}' not registered for @type '{t}' "
                    f"(allowed: {sorted(REGISTERED_STATUSES_BY_TYPE[t])})",
                    b.header_lines.get("status", b.open_line), b.label)]


ALL = [
    check_005_bbe_comm_present,
    check_006_type_present,
    check_007_protocol_version_format,
    check_008_protocol_version_supported,
    check_009_type_in_registry,
    check_010_status_in_registry,
]
