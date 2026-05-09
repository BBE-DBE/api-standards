"""Authorization rules — checks 015, 016, 022, 024, 025, 026.

These are the load-bearing checks for the incident-fix:
- 015: operator_auth required fields
- 016: anti-inference (forbidden auth-shaped fields outside operator_auth)
- 022: auth-only fields (@hmac etc.) outside their allowed types
- 024: scope vocabulary
- 025: TTL policy max (1h)
- 026: @scope_mode value (RC2 §7.3 multi-scope semantics)
"""

from __future__ import annotations

import json
import re

from ..constants import (
    AUTH_ONLY_FIELDS, FORBIDDEN_AUTH_INFERENCE_FIELDS,
    CANONICAL_SCOPES, SCOPE_MODE_VALUES,
    TTL_RE, TTL_MAX_SECONDS,
)
from ..model import Block, Finding


def check_015_operator_auth_required_fields(b: Block) -> list[Finding]:
    if b.headers.get("type") != "operator_auth":
        return []
    missing = []
    for f in ("scope", "target", "ttl", "nonce", "hmac", "issued_by", "id"):
        if f not in b.headers:
            missing.append(f"@{f}")
    if missing:
        return [Finding("BBE-COMM-015", "error", "§7.2",
                        f"operator_auth missing required field(s): {missing}",
                        b.open_line, b.label)]
    return []


def check_016_no_authorization_inference(b: Block) -> list[Finding]:
    """Anti-inference: forbidden auth-shaped field names outside operator_auth."""
    t = b.headers.get("type")
    findings: list[Finding] = []
    for forbidden in FORBIDDEN_AUTH_INFERENCE_FIELDS:
        if forbidden in b.headers and t != "operator_auth":
            findings.append(Finding(
                "BBE-COMM-016", "error", "§7.4",
                f"Field @{forbidden} is forbidden outside @type: operator_auth "
                f"(anti-inference rule). Got @type: '{t}'. "
                f"Authorization MUST be transported as an operator_auth block.",
                b.header_lines.get(forbidden, b.open_line), b.label,
            ))
    return findings


def check_022_auth_only_fields_outside_auth(b: Block) -> list[Finding]:
    """Auth-only fields on non-allowed types (e.g. @hmac on operator_prompt)."""
    t = b.headers.get("type")
    findings: list[Finding] = []
    for field_name, allowed_types in AUTH_ONLY_FIELDS.items():
        if field_name in b.headers and t not in allowed_types:
            findings.append(Finding(
                "BBE-COMM-022", "error", "§7.4",
                f"Field @{field_name} is reserved for @type in {sorted(allowed_types)} "
                f"but appears on @type '{t}' (auth-only-fields anti-inference rule).",
                b.header_lines.get(field_name, b.open_line), b.label,
            ))
    return findings


def _parse_scope(raw: str) -> list[str] | None:
    """Parse @scope value. Accepts JSON array or single-token shorthand."""
    raw = raw.strip()
    if raw.startswith("["):
        try:
            arr = json.loads(raw)
            if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
                return arr
        except json.JSONDecodeError:
            return None
        return None
    if "," in raw:
        return [x.strip().strip('"').strip("'") for x in raw.split(",") if x.strip()]
    return [raw]


def check_024_scope_vocabulary(b: Block) -> list[Finding]:
    if b.headers.get("type") != "operator_auth":
        return []
    if "scope" not in b.headers:
        return []  # 015 handles missing
    raw = b.headers["scope"]
    tokens = _parse_scope(raw)
    if tokens is None:
        return [Finding("BBE-COMM-024", "error", "§7.3",
                        f"@scope value '{raw}' is not parseable as JSON array or "
                        f"single-token shorthand",
                        b.header_lines.get("scope", b.open_line), b.label)]
    bad = [t for t in tokens if t not in CANONICAL_SCOPES]
    if bad:
        return [Finding("BBE-COMM-024", "error", "§7.3",
                        f"@scope contains token(s) outside canonical vocabulary: {bad}. "
                        f"Allowed: {sorted(CANONICAL_SCOPES)}",
                        b.header_lines.get("scope", b.open_line), b.label)]
    return []


def _ttl_to_seconds(raw: str) -> int | None:
    m = TTL_RE.match(raw)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    return {"s": n, "m": n * 60, "h": n * 3600}[unit]


def check_025_ttl_policy_max(b: Block) -> list[Finding]:
    if b.headers.get("type") != "operator_auth":
        return []
    if "ttl" not in b.headers:
        return []
    raw = b.headers["ttl"]
    secs = _ttl_to_seconds(raw)
    if secs is None:
        return [Finding("BBE-COMM-025", "error", "§5.2",
                        f"@ttl '{raw}' must match <int>[smh]",
                        b.header_lines.get("ttl", b.open_line), b.label)]
    if secs > TTL_MAX_SECONDS:
        return [Finding("BBE-COMM-025", "error", "§5.2",
                        f"@ttl '{raw}' exceeds policy maximum of 1h ({TTL_MAX_SECONDS}s)",
                        b.header_lines.get("ttl", b.open_line), b.label)]
    return []


def check_026_scope_mode_value(b: Block) -> list[Finding]:
    """RC2 §7.3: @scope_mode value must be 'all' or 'any' if present."""
    if "scope_mode" not in b.headers:
        return []
    v = b.headers["scope_mode"]
    if v not in SCOPE_MODE_VALUES:
        return [Finding("BBE-COMM-026", "error", "§7.3",
                        f"@scope_mode '{v}' must be one of {sorted(SCOPE_MODE_VALUES)} "
                        f"(default 'all' if absent)",
                        b.header_lines.get("scope_mode", b.open_line), b.label)]
    return []


ALL = [
    check_015_operator_auth_required_fields,
    check_016_no_authorization_inference,
    check_022_auth_only_fields_outside_auth,
    check_024_scope_vocabulary,
    check_025_ttl_policy_max,
    check_026_scope_mode_value,
]
