# PR Draft — Add BBE-STD-002 v1.0-RC2 (ratification candidate)

**Branch:** `feat/std-002-v1.0.0`
**Base:** `main` (`c818320`)
**Commits in this PR:** A1 `844d509` · A2 `18d309b` · A3 `9f9fae3` (3)
**Status at PR open:** RELEASE-CANDIDATE-2 (operator merges A4 ratification commit either before push or after approval)

---

## Summary

Adds the canonical home of **BBE-STD-002 — Agent Communication Protocol v1.0-RC2**, plus its reference implementation (`bbe-comm` Python CLI), golden corpus, ADRs, and a CI ratification gate. Currently RC2 / pending; flips to v1.0.0 / RATIFIED via a separate `docs(std-002): ratify BBE-STD-002 v1.0.0` commit on this same branch (A4 — see `RATIFICATION-NOTE-R1-R5.md`).

This PR ratifies **only the standard** (api-standards). The runtime binding (AGUARD hooks, operator CLI) lands in a separate PR against `bbe-server-config` (B1, B2).

---

## What changed

Three commits, 88 files, 7525 insertions:

### A1 — `docs(std-002): add v1.0-RC2 standard, schema, corpus, ADRs` (53 files)

- `standards/BBE-STD-002/BBE-STD-002.md` — 16-section spec + Annex A (informative AGUARD reference binding)
- `schema/BBE-STD-002.schema.json` — JSON Schema 2020-12, strict (`additionalProperties: false`), 26 conditional rules
- `examples/valid/` (14), `examples/invalid/` (20), `examples/incident-replay/` (3) — golden corpus
- `templates/blocks/` — 5 type-templates (operator-auth/deny, agent-query/result/abort)
- `docs/adr/0001..0004.md` — architectural decision records
- `docs/std-002-{quick-reference,migration}.md` — operator + author docs
- `CHANGELOG.md`, `OPEN_ISSUES-RC2.md`, `docs/RC2-DELTA.md` — review surface

### A2 — `feat(bbe-comm): add STD-002 communication intelligence tool + tests` (32 files)

Modular Python package (no external dependencies):

- `tools/bbe-comm/bbe_comm/` — 12 modules + 7 rule modules + 3 JSON schemas
- 13 subcommands: `lint`, `score`, `trace`, `explain`, `repair-suggest`, `normalize`, `emit`, `verify-hmac`, `incident-test`, `auth-check`, `integrate-guard`, `learn observe`, `learn suggest` (`report`, `adapt` are roadmap-stubs with defined interfaces)
- 85 Python tests:
  - `tests/test_bbe_comm_lint.py` (45) — RC1 compat
  - `tests/test_incident_replay.py` (26) — RC2 incident regression
  - `tools/bbe-comm/tests/test_learning_loop.py` (14) — self-optimization safety
- `.gitignore` — excludes `__pycache__/` and `tools/bbe-comm/data/` (host-local learning store)

### A3 — `test(std-002): add ratification CI gate and standards registry entry` (3 files)

- `scripts/test-std-002.sh` — aggregating CI gate (exit 0 on full pass)
- `STANDARDS.md` — new "Ratified standards registry" section (BBE-STD-002 listed as RC2 / pending)
- `standards/BBE-STD-002/docs/aguard-integration.md` — informative AGUARD reference-binding doc

---

## Why

### Incident addressed

**I-2026-05-09-01:** an operator pasted a detail-rich, well-structured prompt for project A into a chat about project B. The agent treated the detail as authorization, pivoted repos, executed a `pm2 reload`, and made 6 commits.

This standard makes the failure pattern a **schema violation, not a judgment call**, in four independent layers:

1. **Anti-inference (field-level)** — `@authorize`/`@authorized`/`@authorization`/`@authority` forbidden outside `operator_auth` (BBE-COMM-016); auth-only fields (`@hmac`, `@scope`, `@target`, `@ttl`, `@nonce`, `@issued_by`, `@not_after`, `@revokes`) forbidden outside `operator_auth`/`operator_deny` (BBE-COMM-022).
2. **Type discipline** — only `@type: operator_auth` authorizes; any other type is rejected at the gate (R1, R2 in §7.1, §7.2).
3. **Cryptographic anchor** — HMAC-SHA256 over canonical body; no HMAC = no authorization (§5, §7.2). HMAC sits at L4 (authorization-safe). L5 reserved for hash-linked / signed / ledger-backed / externally auditable anchors (mechanism deferred to STD-003 — see ADR-0002).
4. **Repo-pivot rule (R3, agent rule + runtime detection)** — target shifts force fresh `operator_auth` even with valid HMAC for prior target (§7.5).

The incident-replay regression (`tests/test_incident_replay.py`) replays the canonical pattern end-to-end and asserts all four layers fire.

### Architectural posture

- **Runtime-agnostic** — STD-002 conformance does not require AGUARD or any specific runtime (ADR-0003). The standard defines format + agent rules; runtime enforcement is per-deployment. The BBE reference binding (AGUARD) lives in `bbe-server-config/`.
- **Self-optimization is review-only** — the `learn observe`/`learn suggest` loop (ADR-0001) appends events to a redacted JSONL log and synthesises pattern-based suggestions. It NEVER mutates the standard, schema, rules, or any policy. `test_synthesize_does_not_modify_spec_files` enforces this on every CI run by snapshotting `mtime`.
- **Auditability** — every privileged operation is anchored in a verifiable `operator_auth` (ISO 27001 A.5.15), structured log entries are joinable by `@nonce` / `@correlation_id` (A.8.15), repo-pivots are textually announced (A.8.32). Mappings in spec §14.

---

## Tests

| Suite | Tests | Status |
|---|---|---|
| `test_bbe_comm_lint.py` (legacy compat) | 45 | 45/45 |
| `test_incident_replay.py` (incident regression) | 26 | 26/26 |
| `test_learning_loop.py` (self-optimization safety) | 14 | 14/14 |
| **Mandatory total via `scripts/test-std-002.sh`** | **85** | **85/85, exit 0** |
| Bash e2e (`tests/test_e2e_hmac.sh`) | 16 | not in this repo — runtime tests live in `bbe-server-config/tests/` (ADR-0003) |

CI gate: `scripts/test-std-002.sh` (mandatory only). Optional bash e2e via `BBE_SERVER_CONFIG` env when reviewer has the runtime repo checked out.

---

## Non-goals

This PR explicitly does NOT:

- Implement POL-009 (Authorization Decision Policy) — separate workstream.
- Implement BBE-STD-003 (Audit-Store) — separate workstream; owns L5 mechanism.
- Implement ENG-001 (Decision-Engine Interface) — separate workstream.
- Modify Charter v1.x — out of STD-002 scope.
- Modify any ratified standard.
- Modify `bbe-server-config/` — runtime binding is a separate PR (see "Follow-up").
- Implement the `report` or `adapt` subcommands — interfaces defined; deferred to v1.1.
- Ship `bbe-comm` to PyPI — repo-local execution for v1.0.0 (see RATIFICATION-NOTE-R1-R5.md, R4).

---

## Runtime separation

**STD-002 is runtime-agnostic** (ADR-0003). Conformance is determined by the format + agent rules; runtime enforcement is per-deployment. AGUARD is the BBE reference binding, not a prerequisite.

Consequences for review:

- This PR contains **no runtime hooks**, **no runtime tests**, **no `userprompt-hook.sh` / `pretool-hook.sh` / `bbe-block-cli.sh`**.
- `docs/aguard-integration.md` is **informative only** — describes the BBE-deployment binding for documentation purposes; does not prescribe.
- The `bbe-comm verify-hmac` subcommand delegates to a runtime `bbe-block-cli.sh` if available (via `$BBE_BLOCK_CLI`); without the runtime, the subcommand returns exit 5 with a helpful message.

The runtime PR (`bbe-server-config: feat/std-002-runtime-binding`) is a follow-up; review independently.

---

## Operator checklist (pre-merge)

- [ ] Confirm RC2 spec text (`standards/BBE-STD-002/BBE-STD-002.md`) reads as intended.
- [ ] Confirm 4 ADRs (0001–0004) capture the architectural decisions correctly.
- [ ] Confirm `OPEN_ISSUES-RC2.md` residuals R1–R5 match the v1.0.0 decisions in `RATIFICATION-NOTE-R1-R5.md`.
- [ ] Confirm `docs/RC2-DELTA.md` accurately describes the RC1 → RC2 surgical change list.
- [ ] CI gate green on origin (`scripts/test-std-002.sh` exit 0).
- [ ] Decide: ratification flip A4 in this PR (one merge to ratify) OR follow-up commit after approval (two merges).
- [ ] Decide on `Effective:` date in spec frontmatter (Phase D warning window starts at this date).
- [ ] Plan op-secret rotation on `<BBE_PRIMARY_HOST>` (BEFORE deploying B1 runtime PR).
- [ ] Decide whether to clean up the 12 pre-existing untracked Welt-A files (separate operator action; see audit report).
- [ ] Verify Welle-04 dispatch (2026-05-13) timing aligns with merge + Phase B install.

---

## Rollback notes

- A1, A2, A3 are pure additions to a previously-empty `standards/BBE-STD-002/` directory plus a new section in `STANDARDS.md`. **Trivial revert** via `git revert <sha>` for any single commit, or branch rewind to `main`.
- A4 (ratification flip, if pre-merged) is a small text-only commit; revert flips back to RC2.
- **No runtime state change** — this PR creates no files outside the repo, no symlinks, no `op-secret`, no tokens, no audit logs. There is nothing to "undo" outside `git`.
- `bbe-comm learn` writes to `tools/bbe-comm/data/` (gitignored) only when explicitly invoked; rolling back the PR removes the code path automatically.

---

## Follow-up (separate PR, separate repo)

After this PR merges, the runtime binding lands in **`bbe-server-config`** as branch `feat/std-002-runtime-binding`:

| Commit | Files | Purpose |
|---|---|---|
| **B1** | `configs/bbe-guard/lib/{userprompt-hook.sh,pretool-hook.sh,hmac.sh}`, `scripts/bbe-block-cli.sh`, `configs/bbe-guard/agent-allowlist.txt` (R1), `tests/acceptance-bbe-guard.sh`, `STANDARDS.md` | RC2 @-syntax hooks; multi-scope claim-id grouping (ADR-0004); allowlist-downgrade for non-Claude agents on non-privileged messages (R1); canonical-body field-order migration (`session` → `correlation_id`). |
| **B2** | `scripts/install-modules/71-bbe-std-002.sh` (R4 v1.1 enabler — currently a stub), `docs/runbooks/std-002-phase-b-install.md` | Operator runbook for op-secret rotation + Phase B install. |

**Critical pre-deploy step (operator-only):** rotate `op-secret` BEFORE B1 deploy — the canonical-body field order changed in RC2, so all RC1-format tokens become invalid. Documented in spec §11 and the Phase B runbook.

The `bbe-server-config` PR is **NOT blocked** by this PR's merge; they can be reviewed in parallel. Merge order: this PR first (standard exists), then `bbe-server-config` PR (runtime adopts).

---

## Phase D rollout window

- **Day 0** = `Effective:` date in spec frontmatter (operator sets at A4 ratification commit).
- **Days 0–14** = warning window. Linter findings emit; AGUARD hook (after B1 deploys) emits warning audits. No hard blocks.
- **Day 14+** = hard floors:
  - L2 hard-required for formal reports (`@type ∈ {agent_result, audit_record}` with `@status: complete`).
  - L4 hard-required for privileged workflows (any tool action under §7.3 scope vocabulary).

If the `Effective:` date is set to 2026-05-13 (Welle-04 dispatch day), Day-14 hard rollout is 2026-05-28.

---

## Self-validating dogfood

This PR description is itself an STD-002-conformant document — its closing block lints clean against the linter included in this PR:

```
[RESULT-PR-DRAFT-STD-002-V1-0-0]
@bbe-comm: 1.0
@type: agent_result
@id: agent_result_2026-05-10T01-30-00Z_dec9aff0
@parent_id: op_prompt_2026-05-10T01-15-00Z_de50aff0
@correlation_id: bbe-coord-bbe-std-002-pr-readiness
@agent: claude-opus-4-7@2.1.138@v2202.bbe.internal
@status: complete
@compliance_level: L4

PR draft for BBE-STD-002 v1.0.0 ratification.
Branch=feat/std-002-v1.0.0 commits=A1+A2+A3 tests=85/85_pass
ratification_flip_pending=A4_separate_commit
runtime_binding=separate_PR_in_bbe-server-config
[/RESULT-PR-DRAFT-STD-002-V1-0-0]
```
