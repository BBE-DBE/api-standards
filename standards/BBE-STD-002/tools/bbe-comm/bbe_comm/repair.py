"""Repair-suggestion generator.

For each finding, propose a minimal fix as text. The generator NEVER applies
fixes; it only emits suggestions for human/operator review. Pattern: every
finding maps to one suggestion (or none — some findings are advisory only).

Suggestions are deterministic functions of the finding; they don't read the
file content again. This keeps the repair flow side-effect-free.
"""

from __future__ import annotations

from .model import Block, Finding, RepairSuggestion


def _suggest_for_finding(f: Finding) -> RepairSuggestion | None:
    cid = f.check_id
    if cid == "BBE-COMM-005":
        return RepairSuggestion(f, "add-field",
            "Add the protocol-version header.",
            "Add line near top of header: `@bbe-comm: 1.0`",
            "high")
    if cid == "BBE-COMM-006":
        return RepairSuggestion(f, "add-field",
            "Add the @type header.",
            "Add line: `@type: <one-of: operator_prompt | agent_result | …>` (see RC2 §5.4)",
            "medium")
    if cid == "BBE-COMM-007":
        return RepairSuggestion(f, "fix-value",
            "@bbe-comm value must be semver MAJOR.MINOR[.PATCH].",
            "Replace value with `1.0` (drop any leading 'v').",
            "high")
    if cid == "BBE-COMM-008":
        return RepairSuggestion(f, "fix-value",
            "Major version unsupported by this parser; downgrade to 1.x.",
            "Replace value with `1.0`.",
            "medium")
    if cid == "BBE-COMM-009":
        return RepairSuggestion(f, "fix-value",
            "@type must be in the canonical registry or use x-<vendor>-<type> form.",
            "Pick from RC2 §5.4 (operator_prompt / operator_auth / operator_deny / "
            "operator_context / operator_query / agent_result / agent_progress / "
            "agent_query / agent_warning / agent_abort / guard_decision / audit_record).",
            "high")
    if cid == "BBE-COMM-011":
        return RepairSuggestion(f, "fix-value",
            "@id must match canonical or interop form.",
            "Use canonical form: `<type-slug>_<YYYY-MM-DDTHH-MM-SSZ>_<hex8>` "
            "(e.g. `op_auth_2026-05-09T19-30-00Z_7f3e1234`). Note: `-` between time "
            "components, NOT `:` (filename safety).",
            "high")
    if cid == "BBE-COMM-012":
        return RepairSuggestion(f, "fix-value",
            "@id type-slug should match @type.",
            "Either change the @id type-slug to match @type's expected slug "
            "(see RC2 §6.2), or use `msg_` for foreign / interop IDs.",
            "low")
    if cid == "BBE-COMM-013":
        return RepairSuggestion(f, "add-field",
            "Non-root non-prompt blocks need @parent_id at L4+.",
            "Add line: `@parent_id: <id of the upstream block this responds to>`. "
            "If this block IS a root, change @type to `operator_prompt` (the only "
            "registered root type).",
            "high")
    if cid == "BBE-COMM-014":
        return RepairSuggestion(f, "fix-value",
            "@parent_id must follow the same ID pattern as @id.",
            "See RC2 §6.4 — canonical or interop form. Foreign/interop IDs are "
            "accepted with prefix in {msg_, task_, sess_, conv_, welle_}.",
            "high")
    if cid == "BBE-COMM-015":
        return RepairSuggestion(f, "add-field",
            "operator_auth requires @scope, @target, @ttl, @nonce, @hmac, @issued_by, @id.",
            "Sign via `bbe-block sign auth --scope <s> --target <t> --ttl <d> "
            "--correlation <id>` — emits a fully-formed block.",
            "high")
    if cid == "BBE-COMM-016":
        return RepairSuggestion(f, "rename-field",
            "Auth-shaped field names (@authorize / @authorized / @authorization / "
            "@authority) are forbidden outside operator_auth (anti-inference rule, RC2 §7.4).",
            "Rename to a non-reserved name OR move the entire block to "
            "@type: operator_auth and add the required auth fields.",
            "high")
    if cid == "BBE-COMM-017":
        return RepairSuggestion(f, "rename-field",
            "Custom headers must use the @x-<vendor>-<field> form.",
            "Rename to `@x-<your-vendor>-<your-field>` (e.g. `@x-bbe-trace_id`).",
            "high")
    if cid == "BBE-COMM-018":
        return RepairSuggestion(f, "rename-field",
            "@x- extension fields should follow @x-<vendor>-<field>.",
            "Add a vendor prefix: `@x-<vendor>-<field>`. Vendor token must be "
            "2..32 lowercase chars.",
            "medium")
    if cid == "BBE-COMM-019":
        return RepairSuggestion(f, "fix-value",
            "@compliance_level must be one of L0..L5.",
            "Replace value with `L4` (typical) or `L2` (formal-report minimum, post-rollout).",
            "high")
    if cid == "BBE-COMM-020":
        return RepairSuggestion(f, "split-block",
            "Header-shaped line in body — header must be contiguous.",
            "Either move the line up into the header block, or escape the leading "
            "@ in the body line, or split the block.",
            "medium")
    if cid == "BBE-COMM-021":
        return RepairSuggestion(f, "split-block",
            "Same-type nesting forbidden (lineage ambiguity).",
            "Close the inner block before opening another of the same @type, OR "
            "change the inner block's @type, OR replace nesting with @parent_id.",
            "high")
    if cid == "BBE-COMM-022":
        return RepairSuggestion(f, "rename-field",
            "Auth-only field used outside its allowed type.",
            "Either remove the field, OR change @type to one of the allowed types "
            "for that field (see RC2 §5.2).",
            "high")
    if cid == "BBE-COMM-023":
        return RepairSuggestion(f, "fix-value",
            "Declared @compliance_level exceeds computed level. RC2: HMAC alone is L4, NOT L5.",
            "Lower @compliance_level to the computed level — usually L4 for HMAC-anchored "
            "auth blocks. L5 requires @x-bbe-sig / @x-bbe-ledger / @x-bbe-attest.",
            "high")
    if cid == "BBE-COMM-024":
        return RepairSuggestion(f, "fix-value",
            "Scope token outside canonical vocabulary (RC2 §7.3).",
            "Replace with one of: pm2-mutate, git-push, git-remote-change, "
            "systemctl-mutate, docker-mutate, gh-mutate, http-mutate, db-mutate, "
            "fs-mutate-system, secret-rotate.",
            "high")
    if cid == "BBE-COMM-025":
        return RepairSuggestion(f, "fix-value",
            "@ttl exceeds policy max (1h).",
            "Reduce to 1h or less (e.g. `1h`, `30m`, `5m`).",
            "high")
    if cid == "BBE-COMM-026":
        return RepairSuggestion(f, "fix-value",
            "@scope_mode must be 'all' or 'any' (RC2 §7.3 multi-scope).",
            "Either remove the field (default 'all') or set to `any` for OR semantics.",
            "high")
    return None


def repair_suggestions(findings: list[Finding]) -> list[RepairSuggestion]:
    out: list[RepairSuggestion] = []
    for f in findings:
        s = _suggest_for_finding(f)
        if s is not None:
            out.append(s)
    return out
