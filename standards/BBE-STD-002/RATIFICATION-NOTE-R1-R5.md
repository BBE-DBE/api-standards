# Ratification Note — Residuals R1–R5 (final)

**Status:** Operator-confirmed in mandate `[OPERATOR · BBE-STD-002 · PR-RATIFICATION-READINESS]` 2026-05-09.
**Effect:** these decisions are binding for v1.0.0 and supersede the
weaker recommendations in `OPEN_ISSUES-RC2.md`.

| # | Topic | v1.0.0 decision (final) | v1.1+ deferral |
|---|---|---|---|
| **R1** | Cross-vendor compliance enforcement | **Allowlist fallback for non-privileged messages only.** Privileged operations (`@type: operator_auth`, anything reaching scope-gated tools) ALWAYS require L4 regardless of agent vendor. The allowlist downgrade applies only to `operator_prompt` / `agent_progress` / `agent_result` / `agent_query` / `agent_warning` from non-Claude agents, capping their declared compliance level at L2. | Full wrapper-in-spawner (T-AM-002 area) — converts vendor output into RC2-form before AGUARD sees it. |
| **R2** | External analyses (operator-referenced "two analyses") | **Evidence gap, non-blocking.** Documented in spec frontmatter. Ratification proceeds without them. If the analyses surface and conflict with RC2, an RC2.1 or v1.0.1 amendment absorbs deltas; no blocker for v1.0.0. | RC2.1 amendment surface kept open. |
| **R3** | Suggestion-file review cadence | **Weekly default.** Operator scans `bbe-comm learn suggest --json` weekly during ops review. **Immediate review threshold:** any `authorization_inference_attempt` or `guard_denial` event triggers same-day review (these are security-grade signals; they MUST NOT wait 7 days). The threshold is operator-discipline, not tool-enforced in v1.0.0. | Tool-enforced threshold via `bbe-comm learn suggest --since 24h --severity security` flag combination (deferred). |
| **R4** | bbe-comm shipping path | **Repo-local CLI for v1.0.0.** Tool runs from the canonical location (`api-standards/standards/BBE-STD-002/tools/bbe-comm/bbe-comm`). No `/usr/local/bin/` symlink, no PyPI package, no install module in v1.0.0. CI gate (`scripts/test-std-002.sh`) invokes via the canonical path. Operators run from a local checkout. | (v1.1) PyPI / pipx / internal release; install-module symlink in `bbe-server-config/scripts/install-modules/`. |
| **R5** | Trace orphans semantics | **Warning by default; strict mode may error.** `bbe-comm trace` reports orphan parent_ids as advisory output (exit 0). A future `--strict` flag (not in v1.0.0) will exit 3 on orphans. Cycles always exit 3 regardless of mode. | (v1.1) `--strict` flag implementation + e2e test. |

---

## Why these are final

- **R1:** the security boundary is "what can be authorized" (privileged operations). Cross-vendor agents emitting `operator_prompt`-grade messages do not breach the security boundary even at L2; they merely lose lineage richness. Cross-vendor agents attempting `operator_auth` MUST hit full L4 (HMAC valid against deployment op-secret) — the standard has no "vendor exception" for authorization. This is the strongest possible read of the runtime-agnostic posture (ADR-0003).

- **R2:** withholding ratification because of unverifiable referenced documents is theatre, not security. Documented gap is honest; if real conflicts surface we fix in v1.0.1 without touching the v1.0.0 ABI.

- **R3:** discipline > tooling for v1.0.0. The operator is a single human-in-the-loop; weekly cadence + same-day-on-security is operationally clear. v1.1 tightens with flags once we have data on real volume.

- **R4:** repo-local execution removes shipping friction during the initial 14-day Phase D warning window. Operators on `<BBE_PRIMARY_HOST>` can run `cd /path/to/api-standards && scripts/test-std-002.sh` without root, without install hooks. PyPI/install-module is a v1.1 enhancement once the standard is rolled out.

- **R5:** false positives on multi-file tracing (parent_id refers to a block in a sibling file) are common; defaulting to error would be operator-hostile. Strict mode is opt-in for CI of self-contained block files (e.g. audit log replays).

---

## What this note is NOT

This note does not change any spec text, schema, or rule. The spec already permits all five decisions:

- R1 allowlist is a runtime-binding concern (Annex A territory; AGUARD-specific in BBE deployments). Spec §7.2 already says authorization requires L4 for any deployment.
- R2 evidence-gap line is already in the spec frontmatter.
- R3 cadence is operator discipline, not spec.
- R4 distribution path is implementation, not spec.
- R5 trace semantics live in `bbe-comm` tool docs, not spec.

So this note is **operator policy**, not standard amendment.

---

*— Ratification note authored under operator mandate `[OPERATOR · BBE-STD-002 · PR-RATIFICATION-READINESS]` 2026-05-09. Author: claude_integrator_21@claude-opus-4-7@v2202.bbe.internal.*
