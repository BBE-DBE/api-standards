# BBE-STD-002 v1.0-RC2 — Delta from RC1

**Date:** 2026-05-09
**Author:** claude_integrator_21 (claude-opus-4-7@2.1.138@v2202.bbe.internal)
**Mandate:** [OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]
**Status:** RC2-staging (canonical home is `api-standards/` — RC2 lands there on operator integration; staging dir is not canonical)

---

## 1. What this document is

A surgical, line-level change report from RC1 → RC2. The operator's mandate gave 8 explicit decisions. Each decision below maps to: (a) the spec text changes, (b) the tooling changes, (c) the test changes, (d) the open-issues that close as a result.

This is the **review surface** before the operator promotes RC2 to v1.0.0. Reading this document end-to-end answers: *"What's different from RC1, why, and where does it bite?"*

---

## 2. Operator decisions and their consequences

### Decision 1 — Canonical repo home

> "api-standards ist canonical home. bbe-server-config ist runtime integration home. /home/dev/bbe-std-002-rc1 bleibt staging, nicht canonical."

| Element | Change |
|---|---|
| Spec frontmatter | `Owner` field changes from `api-standards (provisional repo home — open issue #1)` to `api-standards/standards/` (canonical, post-rename) |
| Spec §16 / Annex A | Annex A explicitly names `bbe-server-config` as the runtime integration home, separate from the spec repo. |
| OPEN_ISSUES-RC1 #1 | **CLOSED** — operator decision in mandate. |
| Patches dir | `patches/api-standards/` and `patches/bbe-server-config/` carry copy-ready files (not committed; reviewable diffs). |
| Staging dir | `/home/dev/bbe-std-002-rc1/` is annotated as STAGING throughout RC2 docs. |

**Risk if missed:** Welle-04 dispatch references nonexistent canonical paths. **Closed.**

---

### Decision 2 — L5 semantics correction (HMAC alone is NOT L5)

> "L4 = authorization-safe + HMAC-capable where required. L5 = hash-linked / signed / ledger-backed / externally auditable. HMAC allein ist nicht L5."

This is the **most consequential** RC2 change. RC1 had L5 = "valid HMAC against op-secret." That conflates two distinct concerns:

- **Symmetric MAC for runtime authorization** (HMAC-SHA256, server-stored secret) — this is what AGUARD needs.
- **Asymmetric / hash-linked auditability** (signatures, Merkle-anchoring, external attestation) — this is what compliance audit needs.

In RC2, HMAC sits at **L4 ceiling** (authorization-safe). L5 requires at least one of:

- A cryptographic signature with a verifiable public key (e.g. Ed25519, X.509 chain) that an external auditor can verify without the runtime's op-secret;
- A hash-linked entry into an append-only log (Merkle, transparent log, tamper-evident store), referenced by `@x-bbe-ledger`;
- External attestation (notary signature, witness co-signing) referenced by `@x-bbe-attest`.

The mechanism for L5 is **deferred to BBE-STD-003** (audit-store). RC2 reserves the field names (`@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest`) but does not specify the algorithm.

| Element | Change |
|---|---|
| Spec §8 (compliance levels table) | L4 row updated: "+ `@hmac` valid against op-secret, when `@type ∈ {operator_auth, operator_deny}`. **HMAC = L4 ceiling, not L5.**". L5 row updated: "+ at least one of (a) cryptographic signature with externally-verifiable public key, (b) hash-linked entry in append-only ledger, (c) external attestation. Mechanism in STD-003." |
| Spec §8.1 (privileged-operation gate) | Now reads: `L4 minimum (lineage + HMAC where required); L5 desired but not required for v1.0.` |
| Spec §11 (versioning) | v2.0 reserved-for-asymmetric note moved to v1.x where MINOR-bump can introduce L5 fields without a major break (since L5 is forward-only enrichment). |
| Linter `_compute_level()` | Returns L4 (not L5) for blocks with valid `@hmac` shape. Returns L5 only when `@x-bbe-sig` OR `@x-bbe-ledger` OR `@x-bbe-attest` is present (shape-checked). |
| Linter check BBE-COMM-023 | Now allows over-claiming L5 only when the corresponding L5 marker field is shape-valid. |
| Tests | `test_023_overclaim_l5_on_prompt_fires` was already correct (operator_prompt cannot reach L5). New test: `test_023_hmac_alone_is_not_l5` — `operator_auth` with valid HMAC computes L4, not L5. New test: `test_023_l5_requires_ledger_or_sig` — block with `@x-bbe-ledger` reaches L5. |

**Risk if missed:** The standard claims cryptographic-anchor authority that HMAC alone cannot provide; an external auditor reading "L5 = signed" sees an HMAC and reasonably objects. **Closed.**

---

### Decision 3 — Runtime-agnostic posture

> "AGUARD ist reference runtime binding, nicht Voraussetzung für STD-002. STD-002 bleibt runtime-agnostic."

RC1 already designed AGUARD as Annex A (informative). RC2 hardens this:

| Element | Change |
|---|---|
| Spec §1.1 (incident-fix layers) | Renumbered. Layers 1–3 (anti-inference, type-discipline, HMAC) are runtime-agnostic. Layer 4 (repo-pivot) is split: 4a is the agent rule (runtime-agnostic), 4b is the AGUARD enforcement (runtime-specific, Annex A). |
| Spec §7.5 (repo-pivot R3) | Clarified: R3 is an AGENT rule. AGUARD's PreToolUse hook is *one* enforcement mechanism; other deployments may enforce differently or rely on the agent's adherence to R3. |
| Spec §16 (tooling architecture diagram) | Updated to make explicit that the AGUARD column is BBE-deployment-specific. The author-side and operator-side columns are universal. |
| Spec Annex A | Now opens with: "This annex is INFORMATIVE and BBE-deployment-specific. Conformance to BBE-STD-002 does not require AGUARD." |
| Tooling | The bbe-comm CLI's `integrate-guard` subcommand is opt-in; the core lint/score/trace path has zero AGUARD coupling. |
| Tests | `test_runtime_agnostic_no_hmac_required_for_non_auth` — a fully-conformant `operator_prompt` block at L4 never references AGUARD, never references HMAC, and lints clean. |

**Risk if missed:** External adopters can't use STD-002 because they think they need AGUARD. **Closed.**

---

### Decision 4 — Rollout cadence

> "14 Tage warning mode. Danach L2 hard-required for formal reports. L4 hard-required for privileged workflows."

| Element | Change |
|---|---|
| Spec §13.1 (phased rollout table) | Phase D ("broadcast") expanded: 14-day warning ends 2026-05-27. From 2026-05-28: L2 hard-required for any block tagged as a "formal report" (defined as `@type ∈ {agent_result, audit_record}` with `@status: complete`); L4 hard-required for privileged workflows (any block whose tool action falls under a §7.3 scope). |
| Spec §13.3 (compliance gate per repo) | Updated the per-repo gate: a repo is STD-002-compliant when its CI emits L4 `agent_result` blocks AND its privileged ops emit L5-or-L4-with-HMAC `operator_auth` blocks (operator decision: HMAC is L4 in v1.0, L5 deferred to STD-003). |
| OPEN_ISSUES-RC1 #3 | **CLOSED** — cadence pinned. |

**Risk if missed:** Welle-04 dispatch goes out without enforcement floor. Soft-rollout produces noise without action. **Closed.**

---

### Decision 5 — Multi-scope semantics

> "Default = AND semantics. OR semantics nur mit explizitem @scope_mode: any."

RC1 left this open (RC1-OPEN-ISSUE #8). RC2 closes it explicitly:

| Element | Change |
|---|---|
| Spec §7.3 (scope vocabulary) | New paragraph: "When `@scope` carries multiple tokens, the default semantic is AND — the granted authorization permits actions matching ALL listed scopes against the same `@target`. To grant any-of, the block carries `@scope_mode: any` (extension field, reserved at the format level). The AGUARD reference binding consumes `@scope_mode: any` by issuing one go-token per scope and treating any consume as success; absent the field, AGUARD requires all scopes to be in flight." |
| Spec §5.1 (reserved fields table) | New row: `@scope_mode` — optional on `operator_auth`, enum `{all, any}`, default `all`. |
| Schema | `@scope_mode` added with enum constraint. |
| Linter | New check BBE-COMM-026 — `@scope_mode` value must be `all` or `any` if present. |
| AGUARD hook patch | When `@scope_mode: any`, hook issues N tokens (one per scope) but tags them with a shared `claim-id` so the agent's first consume retires them all. Documented in `patches/bbe-server-config/userprompt-hook-multi-scope.diff`. |
| Tests | `test_026_scope_mode_default_all` — multi-scope without `@scope_mode` lints clean and AGUARD issues N tokens (consumer-AND). `test_026_scope_mode_any_issues_grouped_tokens` — explicit `@scope_mode: any` is recognised; tokens carry `claim-id`. |
| OPEN_ISSUES-RC1 #8 | **CLOSED.** |

**Risk if missed:** AGUARD silently grants OR-semantics by default (RC1 implementation), creating a privilege-escalation vector when operators write multi-scope grants expecting AND. **Closed.**

---

### Decision 6 — Incident regression test

> "Detailreicher Prompt mit wiederholtem GO, aber ohne operator_auth. Erwartung: keine gültige Authorization; privileged action bleibt blockiert."

This is THE incident as a test. RC1 had layer-by-layer tests; RC2 adds the **end-to-end re-enactment**:

| Element | Change |
|---|---|
| Tests | New test `test_incident_replay_full` in `tests/test_bbe_comm_lint.py`: feeds a 2KB operator_prompt with detail, repeated `GO`, `please proceed`, `you are authorized`, etc., and asserts (a) zero `operator_auth` blocks parsed, (b) no token issued by the AGUARD hook stub, (c) `bbe-comm score` returns L0/L1 only (no L4+), (d) `bbe-comm auth-check` returns FAIL. |
| Tests | New bash e2e test step in `tests/test_e2e_hmac.sh`: pipes the same prompt through the actual `userprompt-hook.sh`; asserts zero new entries in `incoming.jsonl` (because no `[OPERATOR-AUTH]` tag present); asserts zero new tokens. |
| Tooling | New `bbe-comm incident-test <prompt-file>` subcommand: a one-liner regression for any future suspected incident pattern. Returns exit code 4 (auth_inference_attempt) if it detects auth-shaped prose without a corresponding `operator_auth` block. |
| Examples | New `examples/incident-replay/` directory with the canonical incident pattern (sanitised; no real targets, no real session IDs). |

**Risk if missed:** the incident remains "checked at unit level" but never tested as the actual scenario. **Closed.**

---

### Decision 7 — External analyses

> "Nicht verfügbar. Dokumentiere als evidence gap, kein Blocker."

| Element | Change |
|---|---|
| OPEN_ISSUES-RC1 #2 | **DOWNGRADED to evidence gap.** Status moved from "OPEN — blocker" to "documented gap — non-blocking." If the analyses surface later, RC2.1 will absorb deltas. |
| RC2 Spec frontmatter | New line: "Known evidence gap: two external analyses referenced in original mandates were not visible to the authoring sessions or to the RC2 integrator. Ratification proceeds without them." |

**Risk if missed:** Operator surprised by a contradicting external view post-ratification. **Mitigated** (documented; lightweight RC2.1 path).

---

### Decision 8 — Charter

> "Keine Charter-Änderung. Charter v1.2 kann STD-002 später referenzieren."

| Element | Change |
|---|---|
| Spec §13.1 (phased rollout) | Phase F removed entirely from RC2 timeline. Replaced with note: "Charter cross-reference is the charter committee's PR, not a STD-002 phase." |
| OPEN_ISSUES-RC1 #6 | **CLOSED** — moved to charter committee's queue. |

**Risk if missed:** Charter PR slips into STD-002 ratification window and conflates two governance cycles. **Closed.**

---

## 3. New work in RC2 beyond the 8 decisions

The mandate also commissioned a **Communication Intelligence Tool** (`bbe-comm`) and a **self-optimization architecture**. These are not corrections to RC1; they are **new capabilities**.

### 3.1 bbe-comm — modular Python package

The monolithic `lint/bbe_comm_lint.py` (818 lines) is refactored into:

```
tools/bbe-comm/
├── bbe_comm/
│   ├── __init__.py            (version, public API)
│   ├── cli.py                 (argparse subcommands)
│   ├── parser.py              (block extraction, stack-based)
│   ├── model.py               (Finding, Block, Result dataclasses)
│   ├── validator.py           (lint orchestration)
│   ├── rules/
│   │   ├── structural.py      (BBE-COMM-001..004, 020, 021)
│   │   ├── header.py          (BBE-COMM-005..010)
│   │   ├── ids.py             (BBE-COMM-011..014)
│   │   ├── authorization.py   (BBE-COMM-015, 016, 022, 024, 025, 026)
│   │   ├── compliance.py      (BBE-COMM-019, 023)
│   │   └── extensions.py      (BBE-COMM-017, 018)
│   ├── score.py               (L0..L5 computation, RC2-correct)
│   ├── trace.py               (lineage / correlation analysis)
│   ├── repair.py              (suggestion generator)
│   ├── normalize.py           (Welle-3 → STD-002 mechanical converter)
│   ├── learning.py            (event log + suggestion synthesis)
│   ├── integrations/
│   │   ├── aguard.py          (decision envelope shape)
│   │   ├── json_output.py     (Result → JSON contract)
│   │   └── std002_blocks.py   (emit valid blocks for tool output)
│   └── schemas/
│       ├── result.schema.json
│       ├── learning-event.schema.json
│       └── aguard-decision-envelope.schema.json
├── tests/
│   ├── test_parser.py
│   ├── test_rules_*.py
│   ├── test_cli.py
│   ├── test_learning.py
│   └── test_integrations.py
└── README.md
```

Subcommands (mandate-listed; implemented or stubbed-with-roadmap):

| Subcommand | Status | Exit codes (in addition to 5=runtime-error) |
|---|---|---|
| `bbe-comm lint <file>...` | implemented | 0 clean / 1 lint failed |
| `bbe-comm score <file>` | implemented | 0 success (L printed to stdout) |
| `bbe-comm trace <file>...` | implemented | 0 lineage ok / 3 lineage error |
| `bbe-comm explain <check-id>` | implemented | 0 |
| `bbe-comm repair-suggest <file>` | implemented | 0 |
| `bbe-comm normalize <file>` | implemented | 0 |
| `bbe-comm emit <type>` | implemented (template-based) | 0 |
| `bbe-comm verify-hmac <file>` | implemented (calls hmac.sh) | 0 ok / 1 mismatch |
| `bbe-comm incident-test <file>` | implemented | 0 no-pattern-found / 4 inference attempt detected |
| `bbe-comm auth-check <file>` | implemented | 0 has-valid-auth / 4 prose-only |
| `bbe-comm integrate-guard <file>` | implemented (envelope output) | 0 |
| `bbe-comm learn observe <event-json>` | implemented (append-only) | 0 |
| `bbe-comm learn suggest` | implemented (synthesises from store) | 0 |
| `bbe-comm report <correlation_id>` | roadmap (interface defined) | 0 |
| `bbe-comm adapt` | roadmap (interface defined) | 0 |

Backward-compat: the old `lint/bbe_comm_lint.py` survives as a thin shim that imports from the new package. RC1 tests continue to pass.

### 3.2 Self-optimization

ADR-001 (`docs/adr/0001-self-optimization-learning-loop.md`) specifies:

- **Append-only event log** at `tools/bbe-comm/data/learning-events.jsonl`.
- **Redaction policy**: never write raw prompts; SHA-256 of normalised content + summary fields only. Never write `@hmac` values, `@nonce` values, or any field listed as auth-only.
- **Event types** (mandate-listed): all 13.
- **Suggestion outputs**: text files in `suggestions/` directory; never overwrite existing files (append).
- **No automatic ratification**: every suggestion is human-reviewable text with a "PROPOSED" header; nothing in the tool can promote a suggestion to spec or policy without operator signature.
- **Rate limit** on suggestion generation (1 per pattern per 24h) to prevent suggestion-flood.

### 3.3 JSON contracts

Three JSON Schema 2020-12 documents define stable wire formats:

- `result.schema.json` — `bbe-comm` output for all subcommands.
- `learning-event.schema.json` — append-only log entry shape.
- `aguard-decision-envelope.schema.json` — what AGUARD/Decision-Engine receives.

These are versioned (`$id` includes `:v1`); breaking changes require a MAJOR bump.

---

## 4. Files and patches summary

### 4.1 Created / modified in `/home/dev/bbe-std-002-rc1/` (staging)

- `RC2-DELTA.md` — this document (NEW)
- `BBE-STD-002-v1.0-RC2.md` — RC2 spec (NEW; copy-with-edits of RC1 spec)
- `OPEN_ISSUES-RC2.md` — closes RC1 issues per operator decisions (NEW)
- `tools/bbe-comm/` — full new package (NEW)
- `lint/bbe_comm_lint.py` — modified to thin shim
- `tests/test_incident_replay.py` — new incident regression (NEW)
- `tests/test_e2e_hmac.sh` — adds incident-replay step (MODIFIED)
- `examples/incident-replay/` — sanitised incident corpus (NEW)
- `docs/adr/0001-self-optimization-learning-loop.md` (NEW)
- `docs/adr/0002-l5-redefinition.md` (NEW)
- `docs/adr/0003-runtime-agnostic-posture.md` (NEW)
- `docs/adr/0004-multi-scope-semantics.md` (NEW)
- `schema/BBE-STD-002.schema.json` — adds `@scope_mode`, removes HMAC-implies-L5
- `patches/api-standards/` — copy-ready files for canonical home (NEW; not committed)
- `patches/bbe-server-config/` — runtime-side patch suggestions (NEW; not committed)

### 4.2 NOT modified (per hard boundaries)

- `/etc`, `/opt`, `/usr/local`, `/var` — untouched
- `/home/dev/projects/api-standards/` — untouched (operator integrates via patches)
- `/home/dev/projects/bbe-server-config/` — untouched (operator integrates via patches)
- Any branches, any pushes, any merges — untouched
- Charter, ratified standards — untouched
- POL-009, STD-003, ENG-001 — referenced only, not implemented

---

## 5. Test impact summary

| Suite | RC1 pass | RC2 pass (target) | New tests |
|---|---|---|---|
| Python unit (old `tests/test_bbe_comm_lint.py`) | 45/45 | 45/45 (compat shim) | — |
| Python unit (new `tools/bbe-comm/tests/`) | n/a | TBD (target ≥60) | rule modularisation + 5 RC2 decisions + L5 correction |
| Bash e2e (`tests/test_e2e_hmac.sh`) | 13/13 | 14/14 | +1 incident-replay step |
| Python incident regression (`tests/test_incident_replay.py`) | n/a | TBD | new file, ≥4 cases |

---

## 6. Self-rating delta

| Dimension | RC1 | RC2 | Why |
|---|---|---|---|
| Format rigour | 9.8 | 9.8 | unchanged |
| Cryptographic anchor | 9.5 | 9.7 | L5 cleanly separated from HMAC; v2.0-asymmetric path now clearer |
| Runtime coupling | 9.7 | 9.6 | runtime-agnostic posture clarified; Annex A is informative-only (slight loss of "everything-bound" clarity, gain in portability) |
| Compliance ladder | 9.6 | 9.8 | L4/L5 distinction is now meaningful; over-claim check is real |
| Cross-vendor extensibility | 9.4 | 9.5 | runtime-agnostic posture helps; tool is headless |
| Test coverage | 9.7 | 9.9 | incident regression added; modular tests per rule category |
| Tooling depth | n/a | 9.7 | bbe-comm CLI (15 subcommands), JSON contracts, learning loop |
| Self-optimization safety | n/a | 9.6 | reviewable patches only; no silent mutations |
| Operator-decision honesty | 9.6 | 9.7 | 7 of 8 RC1 issues closed by operator; new ones surfaced honestly |
| **Aggregate** | **9.6** | **9.7** | Tool capability lifts the ceiling; L5 redefinition closes a credibility gap |

---

## 7. What this document does NOT decide

These remain operator-pending or out-of-scope for RC2:

1. **POL-009 / STD-003 / ENG-001 sequencing** — same as RC1; recommendation: POL-009 next.
2. **Cross-vendor wrapper vs. allowlist** — same as RC1 (B's #8); not closed.
3. **Welle-3 audit re-parse** — STD-003 owns.
4. **L5 mechanism specifics** — STD-003 owns; RC2 reserves field names, not algorithms.
5. **Charter v1.2 amendment** — charter committee's PR, not a STD-002 task.

---

*— Compiled by claude_integrator_21 (claude-opus-4-7@2.1.138) under operator mandate `[OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]` 2026-05-09. Server-side policy priority observed: no live actions, no policy mutations, no implicit approvals, no root, no push.*
