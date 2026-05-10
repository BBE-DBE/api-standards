"""Data model for bbe-comm.

Pure dataclasses; no dependencies on parser, validator, rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Finding:
    """A single linter finding (one rule firing on one block)."""
    check_id: str            # e.g. "BBE-COMM-016"
    severity: str            # "error" | "warning"
    section: str             # spec section, e.g. "§7.4"
    message: str             # human-readable
    line: int                # 1-based
    block_label: str | None = None
    file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Block:
    """A parsed STD-002 block (one [LABEL]…[/LABEL] region)."""
    label: str
    open_line: int
    close_line: int
    headers: dict[str, str] = field(default_factory=dict)
    header_lines: dict[str, int] = field(default_factory=dict)
    body_text: str = ""
    body_start_line: int = 0
    parent_label: str | None = None  # for BBE-COMM-021 same-type nesting

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "open_line": self.open_line,
            "close_line": self.close_line,
            "headers": dict(self.headers),
            "body_chars": len(self.body_text),
            "parent_label": self.parent_label,
        }


@dataclass
class ScoreResult:
    """Per-block compliance level (L0..L5) — computed, not declared."""
    block_label: str
    block_id: str | None
    block_type: str | None
    declared_level: int | None    # None if not self-declared
    computed_level: int           # 0..5
    over_claim: bool              # True if declared > computed
    rationale: str                # what features pushed the level up/capped

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TraceEdge:
    """One link in a lineage / correlation graph."""
    src: str       # block id
    dst: str       # parent_id or correlation_id
    kind: str      # "parent" | "correlation" | "ref"


@dataclass
class TraceResult:
    """Lineage / correlation analysis result."""
    nodes: list[str]              # block ids encountered
    edges: list[TraceEdge]
    cycles: list[list[str]]       # any cycles detected
    orphans: list[str]            # parent_ids not in the graph
    correlation_groups: dict[str, list[str]]  # correlation_id → block ids
    ok: bool                      # True if no broken refs / cycles

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": list(self.nodes),
            "edges": [asdict(e) for e in self.edges],
            "cycles": [list(c) for c in self.cycles],
            "orphans": list(self.orphans),
            "correlation_groups": {k: list(v) for k, v in self.correlation_groups.items()},
            "ok": self.ok,
        }


@dataclass
class AuthCheckResult:
    """Result of an authorization audit on a text region."""
    has_operator_auth_block: bool
    operator_auth_count: int
    prose_auth_inference_detected: bool
    inference_evidence: list[str]    # matched prose phrases (with line numbers)
    auth_block_ids: list[str]
    verdict: str                     # "valid-auth" | "invalid-auth" | "no-auth" | "prose-only-inference"
    exit_code: int                   # 0 valid, 4 prose-only-inference, etc.

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IncidentResult:
    """Result of an incident-pattern detection (RC2 §17.1)."""
    pattern_detected: bool
    matches: list[dict[str, Any]]    # [{phrase, line, in_block_label}]
    has_authorizing_block: bool
    verdict: str                     # "no-pattern" | "pattern-with-auth" | "pattern-without-auth"
    exit_code: int                   # 0 ok, 4 inference attempt detected

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairSuggestion:
    """A proposed minimal fix for a finding."""
    finding: Finding
    fix_kind: str            # "add-field" | "rename-field" | "fix-value" | "add-block" | "split-block"
    description: str         # human-readable
    patch_hint: str          # rough text hint (e.g. "add line: @parent_id: <upstream-id>")
    confidence: str          # "high" | "medium" | "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding": self.finding.to_dict(),
            "fix_kind": self.fix_kind,
            "description": self.description,
            "patch_hint": self.patch_hint,
            "confidence": self.confidence,
        }


@dataclass
class Result:
    """The top-level result envelope returned by every bbe-comm subcommand.

    Stable wire format documented in schemas/result.schema.json.
    """
    schema_version: str           # JSON-schema $id version (this contract)
    bbe_comm_version: str
    subcommand: str               # "lint" | "score" | "trace" | ...
    file: str | None
    blocks: int
    findings: list[Finding] = field(default_factory=list)
    scores: list[ScoreResult] = field(default_factory=list)
    trace: TraceResult | None = None
    auth: AuthCheckResult | None = None
    incident: IncidentResult | None = None
    suggestions: list[RepairSuggestion] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bbe_comm_version": self.bbe_comm_version,
            "subcommand": self.subcommand,
            "file": self.file,
            "blocks": self.blocks,
            "findings": [f.to_dict() for f in self.findings],
            "scores": [s.to_dict() for s in self.scores],
            "trace": self.trace.to_dict() if self.trace else None,
            "auth": self.auth.to_dict() if self.auth else None,
            "incident": self.incident.to_dict() if self.incident else None,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "extra": dict(self.extra),
            "exit_code": self.exit_code,
        }
