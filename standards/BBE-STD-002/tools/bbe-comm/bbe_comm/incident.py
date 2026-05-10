"""Incident-pattern detection (RC2 §17.1).

Detects the I-2026-05-09-01 pattern:
  detail-rich operator prompt with prose-only auth-inference cues,
  but NO `[OPERATOR-AUTH]` block carrying valid HMAC.

This is a defensive belt-and-braces check on top of the structural
anti-inference rules (BBE-COMM-016, BBE-COMM-022). The structural rules
catch field-level inference; this module catches *prose*-level inference
by scanning for canonical incident phrases.

Exit codes (returned in IncidentResult and AuthCheckResult):
  0 — no inference attempt (or inference is correctly accompanied by valid auth)
  4 — inference attempt detected without an authorizing block
"""

from __future__ import annotations

import re

from .constants import INCIDENT_PROSE_PATTERNS, INCIDENT_FIRES_ON_CONTEXT
from .model import Block, AuthCheckResult, IncidentResult
from .validator import lint


_PHRASE_REGEXES = [re.compile(p, re.IGNORECASE) for p in INCIDENT_PROSE_PATTERNS]


def _find_phrase_matches(text: str) -> list[dict]:
    """Return per-line matches of any incident phrase."""
    matches: list[dict] = []
    for ln, line in enumerate(text.split("\n"), start=1):
        for rx in _PHRASE_REGEXES:
            m = rx.search(line)
            if m:
                matches.append({
                    "phrase": m.group(0),
                    "line": ln,
                    "context": line.strip()[:120],
                })
                break  # one match per line is sufficient
    return matches


def _which_block_contains_line(line: int, blocks: list[Block]) -> str | None:
    for b in blocks:
        if b.open_line <= line <= b.close_line:
            return b.label
    return None


def auth_check(text: str) -> AuthCheckResult:
    """Audit a text region for prose-only authorization-inference."""
    blocks, findings = lint(text)
    auth_blocks = [b for b in blocks if b.headers.get("type") == "operator_auth"]
    auth_labels = {b.label for b in auth_blocks}
    auth_blocking_errors = [
        f for f in findings
        if f.severity == "error" and (f.block_label in auth_labels or f.block_label is None)
    ]
    valid_auth_blocks = [] if auth_blocking_errors else auth_blocks
    has_valid_auth = len(valid_auth_blocks) > 0
    auth_ids = [b.headers.get("id", "") for b in auth_blocks if b.headers.get("id")]

    raw_matches = _find_phrase_matches(text)
    # Filter: matches in operator_auth bodies are fine (the auth block can
    # discuss the action). Matches outside any block (free prose) are
    # always significant. Matches in operator_context can be configured
    # via INCIDENT_FIRES_ON_CONTEXT (default True — context that LOOKS
    # like authorization is the literal incident).
    filtered: list[dict] = []
    for m in raw_matches:
        in_label = _which_block_contains_line(m["line"], blocks)
        in_block = next((b for b in blocks if b.label == in_label), None)
        in_type = in_block.headers.get("type") if in_block else None
        if in_type == "operator_auth":
            continue  # auth block prose is fine
        if in_type == "operator_context" and not INCIDENT_FIRES_ON_CONTEXT:
            continue
        m["in_block_label"] = in_label
        m["in_type"] = in_type
        filtered.append(m)

    inference_detected = len(filtered) > 0 and not has_valid_auth

    if has_valid_auth and not filtered:
        verdict = "valid-auth"
        exit_code = 0
    elif has_valid_auth and filtered:
        # Auth block IS present; prose inference cues are noise but not a violation
        verdict = "valid-auth"
        exit_code = 0
    elif filtered and not has_valid_auth:
        verdict = "prose-only-inference"
        exit_code = 4
    elif auth_blocks and not has_valid_auth:
        verdict = "invalid-auth"
        exit_code = 1
    else:
        verdict = "no-auth"
        exit_code = 0

    evidence = [f"L{m['line']}: '{m['phrase']}' (in {m.get('in_type') or 'free-prose'})"
                for m in filtered]

    return AuthCheckResult(
        has_operator_auth_block=has_valid_auth,
        operator_auth_count=len(auth_blocks),
        prose_auth_inference_detected=inference_detected,
        inference_evidence=evidence,
        auth_block_ids=auth_ids,
        verdict=verdict,
        exit_code=exit_code,
    )


def incident_test(text: str) -> IncidentResult:
    """Specifically detect the I-2026-05-09-01 pattern."""
    blocks, findings = lint(text)
    auth_blocks = [b for b in blocks if b.headers.get("type") == "operator_auth"]
    auth_labels = {b.label for b in auth_blocks}
    auth_blocking_errors = [
        f for f in findings
        if f.severity == "error" and (f.block_label in auth_labels or f.block_label is None)
    ]
    has_valid_auth = bool(auth_blocks) and not auth_blocking_errors

    raw_matches = _find_phrase_matches(text)
    filtered: list[dict] = []
    for m in raw_matches:
        in_label = _which_block_contains_line(m["line"], blocks)
        in_block = next((b for b in blocks if b.label == in_label), None)
        in_type = in_block.headers.get("type") if in_block else None
        if in_type == "operator_auth":
            continue
        if in_type == "operator_context" and not INCIDENT_FIRES_ON_CONTEXT:
            continue
        m["in_block_label"] = in_label
        m["in_type"] = in_type
        filtered.append(m)

    pattern_detected = len(filtered) > 0

    if not pattern_detected:
        verdict = "no-pattern"
        exit_code = 0
    elif has_valid_auth:
        verdict = "pattern-with-auth"
        exit_code = 0
    else:
        verdict = "pattern-without-auth"
        exit_code = 4

    return IncidentResult(
        pattern_detected=pattern_detected,
        matches=filtered,
        has_authorizing_block=has_valid_auth,
        verdict=verdict,
        exit_code=exit_code,
    )
