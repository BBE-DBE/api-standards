"""AGUARD decision-envelope output.

Renders bbe-comm verdicts into a JSON shape that an AGUARD-equivalent
runtime (or the future ENG-001 Decision Engine) can consume directly.

This is OUTBOUND only. bbe-comm never reads from AGUARD's tokens dir or
audit log; the runtime is the source of truth for issued tokens and
consumed nonces. The envelope here is bbe-comm's contribution to the
runtime's decision input.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from ..model import Block, Finding, Result


ENVELOPE_SCHEMA_VERSION = "1.0"


def _summarize_findings(findings: list[Finding]) -> dict[str, Any]:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    by_check: dict[str, int] = {}
    for f in findings:
        by_check[f.check_id] = by_check.get(f.check_id, 0) + 1
    return {
        "errors": len(errors),
        "warnings": len(warnings),
        "by_check_id": by_check,
        "load_bearing_failures": [
            f.check_id for f in errors
            if f.check_id in ("BBE-COMM-015", "BBE-COMM-016", "BBE-COMM-022",
                              "BBE-COMM-024", "BBE-COMM-025")
        ],
    }


def _content_hash(blocks: list[Block]) -> str:
    """Stable hash over (label, type, id) of every block. Content-free."""
    h = hashlib.sha256()
    for b in blocks:
        h.update((b.label + "|").encode())
        h.update((b.headers.get("type", "") + "|").encode())
        h.update((b.headers.get("id", "") + "|").encode())
    return h.hexdigest()[:16]


def build_envelope(blocks: list[Block], findings: list[Finding],
                   *, file: str | None = None,
                   correlation_id: str | None = None,
                   subcommand: str = "lint") -> dict[str, Any]:
    """Build an AGUARD-decision envelope.

    Schema documented in tools/bbe-comm/bbe_comm/schemas/aguard-decision-envelope.schema.json.
    """
    summary = _summarize_findings(findings)
    decision: str
    reason: str
    if summary["load_bearing_failures"]:
        decision = "deny"
        reason = "load-bearing-lint-error: " + ",".join(summary["load_bearing_failures"])
    elif summary["errors"] > 0:
        decision = "warn"
        reason = f"non-load-bearing lint errors: {summary['errors']}"
    elif summary["warnings"] > 0:
        decision = "allow-with-warnings"
        reason = f"warnings only: {summary['warnings']}"
    else:
        decision = "allow"
        reason = "lint clean"

    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "issued_at":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "subcommand":     subcommand,
        "decision":       decision,           # allow | allow-with-warnings | warn | deny
        "reason":         reason,
        "block_count":    len(blocks),
        "content_hash":   _content_hash(blocks),
        "correlation_id": correlation_id,
        "file":           file,
        "lint_summary":   summary,
        "advisory":       (
            "This envelope is bbe-comm's structural verdict. Runtime token "
            "issuance / consumption / repo-pivot detection remain the runtime's "
            "responsibility. The runtime SHOULD consume this envelope as one "
            "input to its decision but MUST NOT treat it as authorization on "
            "its own."
        ),
    }
