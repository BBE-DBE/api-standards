# Changelog — BBE-STD-002

## v1.0.0 — 2026-05-13 (RATIFIED)

Ratification of BBE-STD-002 v1.0-RC2 as v1.0.0 under operator mandate
`[OPERATOR · BBE-STD-002 · GO-A4-RATIFICATION-EXECUTE]` 2026-05-10.
No technical changes vs. RC2; this release flips frontmatter Version +
Status + Effective per the A4 commit plan. The standard is
runtime-agnostic; the BBE-deployment runtime binding lands separately
in `bbe-server-config/`.

### Ratified

- Status flipped: RELEASE-CANDIDATE-2 → RATIFIED.
- Version flipped: v1.0-RC2 → v1.0.0.
- Effective date set: 2026-05-13 (Phase D 14-day warning window starts).
- All 5 residuals (R1–R5) confirmed per `RATIFICATION-NOTE-R1-R5.md`.
- 91/91 mandatory tests pass via `scripts/test-std-002.sh`.
- Codex final-gate review: PASS_WITH_WARNINGS, no blocking issues.

### Carried unchanged from v1.0-RC2

- Spec text, schema, examples, templates, ADRs, tooling — identical.
- The PR (#2) review-surface artefacts (`RATIFICATION-NOTE-R1-R5.md`,
  `docs/PR-DRAFT-BBE-STD-002-v1.0.0.md`) remain in place as historical
  record.

### Phase D rollout

- 2026-05-13 → 2026-05-27: 14-day warning window. Linter findings emit;
  AGUARD reference binding (after `bbe-server-config` runtime PR lands)
  emits warning audits. No hard blocks.
- From 2026-05-28: hard floors take effect — L2 required for formal
  reports (`@type ∈ {agent_result, audit_record}` with
  `@status: complete`); L4 required for privileged workflows (any tool
  action under §7.3 scope vocabulary).

## v1.0-RC2 — 2026-05-09 (later same day)

Hardening pass under operator mandate `[OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]`. Applies 8 explicit operator decisions plus a major tooling refactor and a self-optimization learning loop.

### Changed (operator decisions)

- **Canonical repo home** = `api-standards/standards/` (post-rename); runtime integration home = `bbe-server-config/`. RC2 staging dir is non-canonical.
- **L5 redefined** — HMAC alone is L4 (authorization-safe); L5 reserved for hash-linked / signed / ledger-backed / externally-auditable anchors via `@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest`. Mechanism deferred to STD-003. (ADR-0002)
- **Runtime-agnostic posture** — AGUARD is reference binding, not prerequisite. Conformance to STD-002 does not require AGUARD; alternative runtimes are conformant if they enforce §7's normative rules. (ADR-0003)
- **Rollout cadence** — Phase D 14-day warning window 2026-05-13 → 2026-05-27. From 2026-05-28: L2 hard-required for formal reports; L4 hard-required for privileged workflows.
- **Multi-scope semantics** — AND default; OR opt-in via `@scope_mode: any`. New reserved field, new linter check BBE-COMM-026, claim-id grouping in the runtime hook patch. (ADR-0004)
- **Incident regression test** — full end-to-end replay (detail-rich prompt + repeated GO + no auth → blocked). 26 new Python tests + 2 new bash e2e steps.
- **External analyses** — documented as evidence gap (non-blocking) in spec frontmatter.
- **Charter** — out of STD-002 scope; charter committee owns any cross-reference.

### Added (new capabilities)

- `tools/bbe-comm/` — modular Python package (12 modules, 13 subcommands): `lint`, `score`, `trace`, `explain`, `repair-suggest`, `normalize`, `emit`, `verify-hmac`, `incident-test`, `auth-check`, `integrate-guard`, `learn observe`, `learn suggest`. Plus `report` and `adapt` as roadmap-stubs with defined interfaces.
- `tools/bbe-comm/bbe_comm/learning.py` — append-only event log with redaction policy, pattern-based suggestion synthesis, rate-limited.
- `tools/bbe-comm/bbe_comm/schemas/result.schema.json` — stable JSON wire format for tool output.
- `tools/bbe-comm/bbe_comm/schemas/learning-event.schema.json` — event log shape.
- `tools/bbe-comm/bbe_comm/schemas/aguard-decision-envelope.schema.json` — AGUARD-bound decision envelope.
- `tools/bbe-comm/bbe_comm/integrations/aguard.py` — decision envelope output.
- `tools/bbe-comm/bbe_comm/normalize.py` — Welle-3 / Welt-A → RC2 mechanical converter.
- `tools/bbe-comm/bbe_comm/repair.py` — per-finding suggestion generator.
- `tools/bbe-comm/bbe_comm/incident.py` — prose-only auth-inference detector with phrase-pattern library.
- `tools/bbe-comm/bbe_comm/trace.py` — lineage / correlation graph analysis with cycle detection.
- `examples/incident-replay/` — sanitised incident corpus (3 files).
- `tests/test_incident_replay.py` — 26 regression tests (RC2 layers 1–5 + L4/L5 + multi-scope + runtime-agnostic).
- `tools/bbe-comm/tests/test_learning_loop.py` — 14 safety tests (append-only, redaction, rate-limit, no-mutation).
- `docs/adr/0001-self-optimization-learning-loop.md`, `0002-l5-redefinition.md`, `0003-runtime-agnostic-posture.md`, `0004-multi-scope-semantics.md`.
- `RC2-DELTA.md` — surgical change report from RC1 → RC2.
- `OPEN_ISSUES-RC2.md` — closes most RC1 issues; 5 residuals named.
- `patches/api-standards/` and `patches/bbe-server-config/` — review-ready file fragments and diffs (NOT committed; operator integrates).

### Modified

- `BBE-STD-002-v1.0-RC2.md` — frontmatter, §1, §1.1, §5.1 (added `@scope_mode`, L5 markers), §5.2, §7.2, §7.3 (multi-scope), §7.5, §8 (L5 redefinition), §11, §12, §13, §14, §16 (3-layer architecture diagram), §17. New §16.1 (self-optimization).
- `lint/bbe_comm_lint.py` — converted to a thin backward-compat shim that re-exports from `tools/bbe-comm/bbe_comm/`. Existing `tests/test_bbe_comm_lint.py` (45 tests) continues to pass without modification.
- `tests/test_e2e_hmac.sh` — added incident-replay step (zero log entries, zero tokens) + bbe-comm incident-test exit-4 check + RC2 L4/L5 score check. 16 bash e2e tests now (was 13).

### Test coverage (final)

| Suite | Count | Status |
|---|---|---|
| RC1 Python unit (legacy shim) | 45 | 45/45 pass |
| RC2 incident-replay | 26 | 26/26 pass |
| RC2 learning-loop safety | 14 | 14/14 pass |
| Bash e2e (incl. AGUARD round-trip) | 16 | 16/16 pass |
| **Total** | **101** | **101/101 pass** |

### Self-rating

9.7 / 10 — see CONSOLIDATION-REPORT.md §6 (RC1) and RC2-DELTA.md §6.

---

## v1.0-RC1 — 2026-05-09

Consolidation of two parallel implementations under operator mandate
`[OPERATOR · BBE-STD-002 · KONSOLIDIERUNG-RC1]`.

### Source artifacts

- **Welt A:** `api-standards/protocols/BBE-STD-002-COMMUNICATION-PROTOCOL.md`
  (RATIFIED-CANDIDATE 2026-05-09) + `bbe-server-config/configs/bbe-guard/lib/`
  (production AGUARD coupling) + `api-standards/scripts/validate-blocks.sh`
  + 8 valid + 8 invalid examples + 8/8 e2e test.
- **Welt B:** `bbe-std-002-draft/standards/BBE-STD-002.md` (DRAFT v0.1.0) +
  538-line Python linter with 20 named checks + 6 valid + 15 invalid
  examples + 40+ unit tests + 16-section spec with L0–L5 ladder.

### Added (RC1-original)

- 5 new linter checks (BBE-COMM-021..025): same-type nesting,
  auth-only-fields-anti-inference, compliance-overclaim, scope-vocabulary,
  ttl-policy-max.
- Hybrid ID format: `<type-slug>_<YYYY-MM-DDTHH-MM-SSZ>_<hex8>` (filename-safe
  + type-debuggable).
- `@correlation_id` reserved for workflow grouping (was B-only).
- `@refs` reserved for many-to-many references (was A-only).
- Repo-pivot rule R3 codified at format level (was A-only as agent rule).
- Self-validating dogfood RESULT block in CONSOLIDATION-REPORT.md.

### Adopted from Welt A

- HMAC-SHA256 mechanism (canonical body, op-secret, replay protection).
- AGUARD UserPromptSubmit hook integration (Annex A).
- `bbe-block` operator CLI (sign auth/deny, verify, rotate-secret, scopes).
- Scope vocabulary (10 enum values bound to AGUARD scope classes).
- Structured `@agent: <type>@<version>@<host>` format.
- Directional type registry (12 types: operator_*, agent_*, guard_*, audit_*).
- ISO 27001/42001 compliance mappings.
- Per-type templates (`templates/blocks/*.tmpl`).
- 6-phase rollout model (Phase A author → Phase F charter amend).

### Adopted from Welt B

- `@`-prefixed contiguous header syntax (replaces A's `key: value`).
- Mutable Label semantics (semantic identity in `@type`+`@id`, not Label).
- L0–L5 compliance ladder + privileged-operation gate.
- 20-named-check linter architecture (per-check error IDs BBE-COMM-NNN).
- Anti-inference field-name rule (BBE-COMM-016 forbids `@authorize` etc.).
- Vendor extension namespace (`@x-<vendor>-<field>`, `x-<vendor>-<type>`).
- `@parent_id` and `@correlation_id` clearer naming.
- Filename-safe ID timestamps (`-` instead of `:`).
- 14-day soft-rollout cadence.
- Self-validating dogfood pattern.

### Discarded with justification

From Welt A:
- `key: value` body syntax (collides with prose); replaced by B's `@key:`.
- Tag-embedded version `[<TYPE> v1.0]` (redundant once `@bbe-comm:` is mandatory).
- YAML folded scalar `note: >` multi-line (parser complexity for rare use).
- Implicit type-as-Label coupling (replaced by mutable Label).
- Closed-registry types (replaced by extension namespace).

From Welt B:
- No-HMAC `authorization_grant` (replaced by HMAC-anchored `operator_auth`).
- Generic registry (replaced by directional types).
- `@scope` ambiguity (resolved as JSON array string canonical).
- Free-string `@agent` (replaced by structured form).
- `error` type at registry level (folded into `agent_abort` + `agent_warning`).

### Hardening (incident I-2026-05-09-01 response)

The 2026-05-09 incident is now blocked at four independent layers:

1. **Anti-inference** (BBE-COMM-016 + BBE-COMM-022): forbidden auth-shaped
   field names cannot appear outside `operator_auth` / `operator_deny`.
2. **Type discipline** (R1, R2 in spec §7.1, §7.2): only `@type: operator_auth`
   authorizes.
3. **HMAC anchor** (§5, §7.2): textual content alone cannot authorize without
   a server-derived signature.
4. **Repo-pivot rule R3** (§7.5): target shifts force re-ask even with valid
   HMAC for prior target.

### Test coverage

- 45 Python unit tests pass (B's 40 + 5 new for BBE-COMM-021..025).
- 13 Bash e2e tests pass (A's 8 + 5 new: lint clean, deny revokes,
  ttl-policy linter, multi-target tokens, prose-only rejection).
- 14 valid examples + 20 invalid examples in golden corpus.
- All examples named NNN-... where NNN matches the BBE-COMM-NNN check
  they're expected to fire (or pass clean).

### Known gaps (RC1 → v1.0.0 ratification blockers)

See `OPEN_ISSUES-RC1.md` for 8 operator-decision items (7 carried from
B's 15; 1 new exposed by RC1; 7 of B's items closed).

### Self-rating

9.6 / 10 — see CONSOLIDATION-REPORT.md §6 for breakdown.

---

## Pre-RC1 history (for context)

### Welt A — RATIFIED-CANDIDATE 2026-05-09

Authored under operator mandate `[OPERATOR · BBE-STD-002 · COMMUNICATION-PROTOCOL]`.
- `protocols/BBE-STD-002-COMMUNICATION-PROTOCOL.md` v1.0
- `protocols/BBE-STD-002.schema.json` (JSON Schema 2020-12)
- `protocols/BBE-STD-002-block-types.yaml`
- `scripts/validate-blocks.sh` (Bash dual-mode validator)
- `examples/std-002/{valid,invalid}/`
- Companion in `bbe-server-config/`: `userprompt-hook.sh`, `hmac.sh`,
  `bbe-block-cli.sh`, e2e test.

### Welt B — DRAFT v0.1.0 — 2026-05-09

Authored under operator mandate `[OPERATOR · BBE-STD-002]`.
- `standards/BBE-STD-002.md` (16 sections, NORMATIVE)
- `lint/bbe_comm_lint.py` (538 lines, 20 checks)
- `schema/bbe-comm-v1.0.json` (strict JSON Schema)
- `tests/test_bbe_comm_lint.py` (40+ tests)
- `examples/{valid,invalid}/`
- 15 OPEN_ISSUES.md, MIGRATION.md, CHANGELOG.md
