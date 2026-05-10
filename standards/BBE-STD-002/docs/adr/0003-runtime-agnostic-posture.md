# ADR-0003 — Runtime-agnostic posture; AGUARD is reference, not prerequisite

**Status:** Accepted (operator decision 3 in RC2 mandate)
**Date:** 2026-05-09

## Context

RC1 designed AGUARD as Annex A (informative) but threaded AGUARD-specific language through several normative sections (e.g. §7.2 said *"the agent MUST NOT take the authorized action until ... the AGUARD GO-token is consumed at PreToolUse time"*).

This had two problems:

1. **External adopters can't use STD-002 unless they install AGUARD.** The standard reads as if AGUARD is a prerequisite, not a reference.
2. **The standard couples to a BBE-specific runtime implementation.** Future BBE deployments using a different enforcement mechanism (a different hook, a different operating system, a tool-call gateway, etc.) cannot claim STD-002 conformance without the linguistic gymnastics of "Annex A is informative."

## Decision

STD-002 is **runtime-agnostic**. Conformance is determined by:

- The textual **format** (block syntax, header rules, ID pattern, type registry).
- The **agent rules** (R1–R7) which are normative and runtime-agnostic.
- The **HMAC anchor** as a *format requirement* — the block carries the field; verification is the runtime's job.

AGUARD is a **reference binding** for BBE deployments. Other deployments are conformant if they implement equivalent enforcement of §7's normative rules. The standard does not prescribe HOW.

## Consequences

### Spec changes

- §1 (Purpose): question 4 (enforcement) is now framed as runtime-specific.
- §1.1 (incident layers table): each layer carries a "Runtime-agnostic?" column. Layers 1–3 are agnostic; layer 4 splits into 4a (agent rule, agnostic) and 4b (runtime enforcement, BBE-specific).
- §7.2 (valid authorization): "AGUARD GO-token consumed at PreToolUse" → "a runtime-equivalent enforcement token (in the BBE reference binding: an AGUARD GO-token consumed at PreToolUse, see Annex A.2)."
- §7.5 (R3 repo-pivot): split into 4a (agent rule) and 4b (AGUARD enforcement).
- §16 (tooling architecture): three-layer diagram with author-side (universal), operator-side (universal), runtime-side (BBE-specific).
- §17 (incident response): layers table updated to mark which are runtime-agnostic.
- Annex A: opens with "INFORMATIVE, BBE-deployment-specific. Conformance to BBE-STD-002 does not require AGUARD."

### Tool changes

- `bbe-comm` core (lint/score/trace/etc.) has zero AGUARD coupling.
- `bbe-comm integrate-guard` is opt-in; the AGUARD-decision-envelope is one possible output.
- `bbe-comm verify-hmac` delegates to the operator-side `bbe-block-cli.sh` which itself is universal (any deployment with bash + openssl + the op-secret).

### Compliance changes

- ISO 27001 A.5.15 mapping language now reads: "every privileged operation textually anchored in a verifiable `operator_auth`. Runtime bindings (e.g. AGUARD) provide the cryptographically anchored GO-token leg; conformant deployments without runtime binding rely on operator-attended action plus structural validation."
- Repos can claim STD-002 conformance without AGUARD as long as they enforce R1–R7 in some other manner (e.g. a different hook, code review, manual operator gate).

## Consequences

### Positive

- The standard is portable. Codex / GPT / future LLMs can adopt it.
- BBE deployments that don't run AGUARD (e.g. CI-only environments) can still be compliant.
- The mental model is clean: format spec is universal, runtime binding is per-deployment.

### Negative

- A future operator might build a runtime that claims STD-002 conformance without actually enforcing the agent rules. Mitigation: the agent rules R1–R7 are normative; a runtime that does not enforce them is not conformant. The standard cannot prevent fake claims, but it can be honest about what it requires.

## Cross-references

- RC2 spec §1, §1.1, §7.2, §7.5, §16, §17, Annex A
- `tools/bbe-comm/bbe_comm/integrations/aguard.py` (envelope schema explicitly notes runtime is decision-maker)
- `tests/test_incident_replay.py::test_runtime_agnostic_no_aguard_required`
