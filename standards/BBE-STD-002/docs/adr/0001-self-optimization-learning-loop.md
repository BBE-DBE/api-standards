# ADR-0001 — Self-optimization learning loop

**Status:** Proposed (RC2-staging)
**Date:** 2026-05-09
**Mandate:** [OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]

## Context

The mandate asked for a tool that "learns from successes/failures, recognises patterns, and suggests process improvements" — but explicitly **without** silent policy mutations or live changes. This ADR specifies the architecture that satisfies both: a closed feedback loop that **observes**, **patterns**, and **proposes**; never **applies**.

## Decision

### Architecture

```
                                    ┌─────────────────────────────┐
   bbe-comm subcommand              │  tools/bbe-comm/data/       │
   (lint / score / trace / etc.)    │    learning-events.jsonl    │  ← append-only
                  │                 │    suggestions/             │
                  │                 │      operator-training.md   │
                  │                 │      new-test-cases.md      │  ← append-only,
                  ▼                 │      new-linter-rules.md    │    review-only
   ┌──────────────────────┐         │      schema-gaps.md         │
   │  learning.observe()  │ ──────► │      process-improvements.md│
   │   (with redaction)   │         │    .suggestion-markers/     │
   └──────────────────────┘         │      <hash>.last (rate-lim) │
                                    └─────────────────────────────┘
                  ▲                                │
                  │                                │
                  │         ┌─ pattern detection ──┘
                  │         ▼
                  │  learning.synthesize_suggestions()
                  └─ (rate-limited, never overwrites)
```

### Event types (mandate-listed)

| Event | When emitted |
|---|---|
| `lint_error` | A linter finding fires (severity error) |
| `repair_suggestion` | bbe-comm repair-suggest emits a suggestion |
| `repeated_invalid_pattern` | Same finding fires N times within a window |
| `authorization_inference_attempt` | bbe-comm incident-test exits 4 |
| `missing_lineage` | BBE-COMM-013 fires |
| `invalid_parent_id` | BBE-COMM-014 fires |
| `legacy_tag_detected` | bbe-comm normalize had work to do |
| `guard_denial` | AGUARD reference hook denied an action |
| `operator_override` | Operator manually accepted a finding (future v1.1) |
| `successful_repair` | A repair-suggest output was applied and re-lint passes |
| `failed_repair` | A repair-suggest output was applied and re-lint still fails |
| `schema_gap_detected` | A valid block fails schema due to missing field name |
| `test_gap_detected` | A new corpus example does not match any check |

### Redaction policy (load-bearing)

The event log MUST NEVER contain:

- Raw block bodies
- Raw operator prompts
- `@hmac` values
- `@nonce` values
- Any auth-only field value (`@scope`, `@target`, `@issued_by`, `@not_after`, `@revokes`)
- L5 marker-field values (`@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest`)
- Raw file paths
- Raw `@correlation_id` values

The store reduces these to:

- SHA-256[:12] hashes (12 hex chars — enough to group, not enough to recover);
- structured metadata (`check_id`, `block_type`, `severity`);
- length-bucketed shape descriptors (`block_label_shape`).

`learning.observe()` enforces a final scrub: any forbidden field-name in `extra` is rewritten to `<REDACTED>` before write. The `tests/test_learning_loop.py::test_redaction_scrubs_forbidden_values` test validates this on every CI run.

### Rate-limiting

Same suggestion (identified by `rate_key`) MUST NOT be re-emitted within 24 hours. Rate-limit markers live in `tools/bbe-comm/data/.suggestion-markers/<hash>.last`. Without this, a frequent pattern could flood the suggestion files with duplicate proposals every minute.

### Append-only invariant

- Events file (`learning-events.jsonl`) MUST be append-only. Reading-then-rewriting is forbidden by code review (the code only opens with mode `"a"`).
- Suggestion files (`suggestions/*.md`) MUST be append-only. Each suggestion is a new section with `## PROPOSED — <title> (<timestamp>)`. Existing content is preserved.
- The store directory MUST be auditable: a future operator running `git log` on the suggestions directory sees every suggestion with timestamp.

### Adaptation rule (load-bearing)

Suggestions are **review-only**. The tool:

- WRITES suggestion files with a `## PROPOSED — …` heading.
- Includes a "**This is a SUGGESTION ONLY. No spec, schema, or rule has been changed. Operator review required.**" disclaimer in every suggestion.
- NEVER modifies `BBE-STD-002-v1.0-RC2.md`, `schema/`, `lint/`, `tools/bbe-comm/bbe_comm/rules/`, or any other policy artifact.
- NEVER auto-applies a suggestion.
- NEVER opens a PR or sends a Slack message or runs `git commit` or any other live action.

The **only** writes a learning-loop tool performs are inside `tools/bbe-comm/data/`. The unit test `test_synthesize_does_not_modify_spec_files` enforces this on every CI run by snapshotting `mtime` of the spec and schema before and after `synthesize_suggestions()`.

### Communication contract

The learning store is also accessible via `bbe-comm learn observe <json>` and `bbe-comm learn suggest`. This means:

- An external orchestrator (bbe-coord, AGUARD audit log shipper, etc.) can pipe events into the learning loop without writing Python.
- The suggest output is JSON-renderable (`--json`) so it can be polled by a dashboard.
- The schema is documented in `tools/bbe-comm/bbe_comm/schemas/learning-event.schema.json`.

### Roadmap (v1.1)

The mandate listed `report` and `adapt` subcommands; RC2 ships them as **stubs with defined interfaces**. v1.1 will:

- Implement `report <correlation_id>`: render a markdown audit of every block in a given correlation group, in lineage order.
- Implement `adapt`: scan the learning store and propose new corpus examples, new linter checks, or schema field additions — STILL as review-only suggestions.

## Consequences

### Positive

- The tool can detect recurring problems without operator intervention.
- Operators get review-grade suggestions backed by counts and timestamps.
- Audit trail of every suggestion is preserved.
- Redaction policy means the learning store is shareable (e.g. across BBE-deployments) without leaking secrets.

### Negative

- An attacker who compromises the bbe-comm host can read the events file and infer some metadata (timestamps, file-path hashes, frequency patterns). Mitigation: the events file lives at `0640` root:bbe-guard, same protections as the audit log.
- Suggestions can become stale if the spec evolves; the rate-limit prevents flood but does not prevent suggestions from referencing old rules. Mitigation: the v1.1 `adapt` subcommand will include staleness detection.
- The rate-limit window (24h) is a heuristic; if BBE-STD-002 evolves rapidly, suggestions may queue up. Operators can manually clear `.suggestion-markers/` to force a fresh synthesis.

## Compliance

- ISO 27001 A.8.15 (Logging): the event log is structured, append-only, and joinable by `correlation_hash`.
- ISO 42001 (AI Management System): the loop is an explicit "monitor → propose → human-decide" pattern with auditable proposals.

## Cross-references

- RC2 spec §16.1 (tooling architecture, self-optimization sub-section)
- `tools/bbe-comm/bbe_comm/learning.py` (implementation)
- `tools/bbe-comm/bbe_comm/schemas/learning-event.schema.json` (event-shape contract)
- `tools/bbe-comm/tests/test_learning_loop.py` (safety tests)
