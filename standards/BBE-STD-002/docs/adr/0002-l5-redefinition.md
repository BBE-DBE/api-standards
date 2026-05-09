# ADR-0002 — L5 redefinition: HMAC is L4, not L5

**Status:** Accepted (operator decision 2 in RC2 mandate)
**Date:** 2026-05-09

## Context

RC1 defined L5 as: *"+ `@hmac` valid against the deployment op-secret (for `operator_auth` / `operator_deny`); for non-privileged blocks, `@x-bbe-sig` reserved (mechanism in STD-003)."*

This conflated two distinct concerns:

1. **Symmetric MAC for runtime authorization** — HMAC-SHA256 against a server-stored 32-byte secret. Used by AGUARD to prove that a block was issued by the operator. Verifiable only by holders of the same secret (the server).
2. **Asymmetric / hash-linked auditability** — signatures with externally-verifiable public keys, hash-linked ledger entries, third-party attestations. Verifiable by external auditors WITHOUT trusting the runtime's secret store.

A compliance auditor reading "L5 = signed" reasonably expects (2). Receiving an HMAC and being told "trust the server" is a credibility gap. The Senior Review correctly flagged this as a load-bearing fix.

## Decision

Redefine the levels:

- **L4** — Linked + authorization-safe. Reachable when:
  - the block has lineage (`@parent_id` for non-root types),
  - AND, for `@type ∈ {operator_auth, operator_deny}`, the block has a shape-valid `@hmac`.
- **L5** — Hash-linked / signed / ledger-backed / externally auditable. Reachable when:
  - L4 is satisfied,
  - AND at least one of `@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest` is present and shape-valid.

The mechanism for L5 marker fields is **deferred to BBE-STD-003**. RC2 reserves the field names and shape-checks them; STD-003 specifies algorithms, key management, and verification protocols.

The privileged-operation gate (RC2 §8.1) requires **L4 minimum**, not L5. L5 is desired but not required for v1.0 conformance. v1.x can additively introduce concrete L5 mechanisms via MINOR-bump.

## Consequences

### Positive

- Compliance / external audit gets a path forward (STD-003) without breaking v1.0.
- v1.0 is shippable today (HMAC is a real, deployed mechanism).
- The credibility gap closes: L5 means what auditors think it means.

### Negative

- Existing RC1 consumers that thought "HMAC = L5" need a migration. The over-claim check (BBE-COMM-023) catches `@compliance_level: L5` declarations on HMAC-only blocks. Operators see the error immediately.
- STD-003 is not yet authored. Until it lands, no block reaches L5 in production. Acceptable: L4 is the privileged-operation gate.

### Mitigations

- The linter prints a helpful repair-suggest message for BBE-COMM-023: *"RC2: HMAC alone is L4, not L5; L5 requires @x-bbe-sig / @x-bbe-ledger / @x-bbe-attest."*
- The `bbe-comm explain BBE-COMM-023` subcommand says the same.
- Migration doc (`docs/std-002-migration.md` — to be updated post-RC2) lists this as a breaking semantic change.

## Cross-references

- RC2 spec §8 (compliance levels)
- RC2 spec §11 (versioning + evolution)
- `tools/bbe-comm/bbe_comm/score.py` (`compute_level` implementation)
- `tools/bbe-comm/bbe_comm/rules/compliance.py` (BBE-COMM-023)
- `tests/test_incident_replay.py::test_l4_l5_hmac_alone_is_l4_not_l5`
- `tests/test_incident_replay.py::test_l5_requires_external_audit_anchor`
- `tests/test_incident_replay.py::test_l5_overclaim_with_only_hmac_fires`
