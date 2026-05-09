# Open Issues — BBE-STD-002 v1.0-RC2

**Status:** RC2 ready for ratification. Most RC1 open issues were resolved by the RC2 operator decisions; the residual list below is shorter and named explicitly.

**Timeline anchor (operator-set, RC2 mandate):**

- 2026-05-09: RC2 produced (this artifact).
- 2026-05-10: Operator review.
- 2026-05-11..12: Ratification → v1.0.0; canonical home becomes `api-standards/standards/`.
- 2026-05-13: Phase B/C install on `<BBE_PRIMARY_HOST>`.
- 2026-05-13 → 2026-05-27: Phase D 14-day warning window.
- 2026-05-28: Hard-required floors take effect (L2 for formal reports, L4 for privileged ops).

---

## Resolved by RC2 mandate (closed)

| RC1 # | Topic | RC2 status |
|---|---|---|
| 1 | Repo home | **CLOSED** — `api-standards/` is canonical home; `bbe-server-config/` is runtime integration home; staging dir non-canonical |
| 2 | Two external analyses | **CLOSED-AS-EVIDENCE-GAP** — documented in spec frontmatter; non-blocking |
| 3 | Soft-rollout schedule | **CLOSED** — 14-day warning, hard-rollout 2026-05-28 |
| 6 | Charter v1.2 amendment | **CLOSED** — out of STD-002 scope; charter committee owns |
| RC1-8 | Multi-scope AND vs OR | **CLOSED** — AND default; `@scope_mode: any` for OR (ADR-0004) |

## Resolved by RC2 architectural decisions (closed)

| Topic | RC2 closure |
|---|---|
| L4/L5 separation | **CLOSED** — ADR-0002. HMAC is L4, not L5; L5 reserved for STD-003 (signature/ledger/attestation) |
| Runtime-agnostic posture | **CLOSED** — ADR-0003. AGUARD is reference binding, not prerequisite |
| Self-optimization safety | **CLOSED** — ADR-0001. Append-only, redacted, review-only suggestions; no silent mutations |
| JSON output contract | **CLOSED** — `schemas/result.schema.json`, `schemas/learning-event.schema.json`, `schemas/aguard-decision-envelope.schema.json` |
| Incident regression test | **CLOSED** — `tests/test_incident_replay.py` (26 tests) + bash e2e step (steps 12–13) |
| Linter language | **CLOSED** — Python primary (modular package), Bash hook adapter (BBE-deployment-specific) |
| Tool architecture | **CLOSED** — `tools/bbe-comm/bbe_comm/` 12-module package + 13 subcommands |

---

## RC2 residual issues — operator decisions still required

### Issue R1 (carried from RC1 #7): Cross-vendor compliance enforcement strategy

**Question:** Codex / GPT / future LLMs often emit free-form. RC1 surfaced two paths; neither was chosen. RC2 still defers.

| Path | Pros | Cons |
|---|---|---|
| (a) Wrapper in spawner (T-AM-002 area) | Universal compliance; no permanent allowlist debt | Adds spawner complexity; latency cost |
| (b) Allowlist-downgrade | Simple; immediate | Permanent two-tier system; allowlist drift |

**Integrator weak-recommendation:** (a) wrapper-in-spawner. The runtime-agnostic posture (ADR-0003) makes (a) cleaner: the wrapper's job is purely textual normalization (call `bbe-comm normalize` on vendor output, then validate). Operator decides at v1.0.0 ratification or in v1.1 follow-up.

---

### Issue R2 (carried from RC1 #15): POL-009 / STD-003 / ENG-001 sequencing

**Status:** still deferred. RC2 makes the dependency clearer:

- **STD-003** (audit-store) blocks: L5 mechanisms, Welle-3 audit re-parse, the bbe-comm `report` subcommand.
- **POL-009** (authorization decision policy) blocks: multi-operator authorization, principal-proof for non-operator grants.
- **ENG-001** (decision-engine interface) blocks: replacing the AGUARD reference binding with a standardised decision-engine contract.

**Integrator recommendation (unchanged):** POL-009 next. Highest leverage; closes the incident loop end-to-end. STD-003 next-but-one; ENG-001 last (it consumes the previous two).

---

### Issue R3 (NEW, surfaced by RC2 review): Suggestion-file repository placement

**Question:** When the learning loop emits suggestions in `tools/bbe-comm/data/suggestions/`, who reads them?

- Option (a): Operator manually scans `bbe-comm learn suggest` output during weekly ops review.
- Option (b): A scheduled job (per `/schedule` skill) runs `bbe-comm learn suggest --json` and emits a Slack/email digest.
- Option (c): The suggestions live on a separate review repo (e.g. `bbe-coord/suggestions/std-002/`) for operator triage.

**Integrator weak-recommendation:** (a) for v1.0; (b) for v1.1 once the suggestion volume is known. (c) is over-engineering until volume justifies it.

---

### Issue R4 (NEW, surfaced by RC2 implementation): bbe-comm distribution path

**Question:** How is `bbe-comm` shipped to BBE hosts?

- Option (a): Copy into `/usr/local/bin/bbe-comm` via `bbe-server-config` install module 71-bbe-std-002.
- Option (b): Ship as PyPI package `bbe-comm` and pip-install during provisioning.
- Option (c): Run from `/home/dev/projects/api-standards/tools/bbe-comm/` as a sibling repo.

**Integrator weak-recommendation:** (a) — minimum churn, aligned with how `bbe-block` and `userprompt-hook.sh` are already shipped. (b) can wait for v1.1 and external adopters.

---

### Issue R5 (NEW, exposed by `bbe-comm trace`): Cross-conversation lineage

**Question:** When tracing a single file, parent_id refs to blocks in an earlier conversation turn (different file) are flagged as "orphans." Should they be?

**RC2 implementation:** orphans are reported but DO NOT fail the trace (exit 0). Cycles still fail (exit 3). This is the right default for single-file usage; for whole-conversation audit, operators concatenate files before passing to `bbe-comm trace`.

**Operator decision pending:** confirm this default; or specify a `--strict-orphans` flag for stricter checks. RC2 leaves it as warn-only.

---

## Items NOT addressed in RC2 (intentionally)

- POL-009 spec content (separate workstream).
- STD-003 spec content (separate workstream — owns L5 algorithm).
- ENG-001 spec content (separate workstream).
- Welle-3 audit backfill (STD-003).
- Charter v1.2 amendment text (charter committee).
- Live install on `<BBE_PRIMARY_HOST>` (operator action — Phase B in spec §13).

---

## How to ratify RC2 → v1.0.0

1. Operator reviews this document, RC2-DELTA.md, and the four ADRs (0001–0004).
2. Decisions on Issues R1, R2, R3, R4, R5.
3. (Optional) any RC3 amendments based on operator feedback.
4. Tag `v1.0.0` in the chosen repo home (`api-standards/`).
5. Apply patches:
   - `patches/api-standards/` files land in `api-standards/standards/`.
   - `patches/bbe-server-config/` files land in `bbe-server-config/configs/bbe-guard/lib/` (multi-scope hook update).
6. Phase B install on `<BBE_PRIMARY_HOST>` per spec §13.1. Operator-attended; integrator does not run live commands.
7. Phase D broadcast: every BBE-DBE service repo gets a 1-line `STANDARDS.md` reference; `AGENTS.md`/`CLAUDE.md` cite R1–R7.

---

*— Compiled by claude_integrator_21 (claude-opus-4-7@2.1.138) under operator mandate `[OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]` 2026-05-09. Server-side policy priority observed: no live actions, no policy mutations, no implicit approvals, no root, no push.*
