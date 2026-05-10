# ADR-0004 — Multi-scope semantics: AND default, OR via `@scope_mode: any`

**Status:** Accepted (operator decision 5 in RC2 mandate)
**Date:** 2026-05-09

## Context

RC1 left multi-scope semantics open (RC1-OPEN-ISSUE #8). When `@scope: ["pm2-mutate", "git-push"]` arrives at the AGUARD reference binding, two readings are possible:

- **AND**: the operator authorizes the agent to do BOTH pm2-mutate AND git-push against the same target as part of one privileged operation.
- **OR**: the operator authorizes the agent to do EITHER pm2-mutate OR git-push against the same target as one of two distinct privileged operations.

RC1's reference implementation accidentally implemented OR (the hook issued one go-token per scope token in a list, and any one consume succeeded). Operators writing multi-scope grants expecting AND would discover, after deployment, that the agent could do MORE than they intended.

This is a privilege-escalation vector by ambiguity. Fix in RC2.

## Decision

**Default: AND.** When `@scope` carries multiple tokens and `@scope_mode` is absent or `@scope_mode: all`, the runtime requires every scope token to be satisfied — i.e. all tokens must be in flight at the moment of action. The action is gated on the conjunction.

**OR is opt-in via `@scope_mode: any`.** The operator must explicitly write `@scope_mode: any` to grant any-of semantics. The runtime then issues N tokens grouped by a shared `claim-id`; the agent's first consume retires the entire group.

`@scope_mode` is a new reserved field (RC2 §5.2). Allowed values: `all` (default), `any`. The linter (BBE-COMM-026) rejects other values.

## Consequences

### Spec changes

- §5.2: new row for `@scope_mode` (optional on operator_auth, enum {all, any}, default all).
- §7.3: new paragraph specifying the AND default and the OR opt-in.
- §9.1: new check BBE-COMM-026 (`@scope_mode` value validation).

### Schema changes

- `schema/BBE-STD-002.schema.json`: add `@scope_mode` with enum constraint.

### Tool changes

- `tools/bbe-comm/bbe_comm/rules/authorization.py`: implement `check_026_scope_mode_value`.
- `tools/bbe-comm/bbe_comm/integrations/aguard.py`: envelope includes scope_mode (informative).

### AGUARD reference-binding changes

- `tools/userprompt-hook.sh`: when `@scope_mode: any`, issue N tokens with shared `claim-id`. The patch is documented in `patches/bbe-server-config/userprompt-hook-multi-scope.diff`.
- `pretool-hook.sh` (in bbe-server-config): when consuming, retire all tokens with the same `claim-id` if `@scope_mode: any` was set on the originating block.

### Tests

- `tests/test_incident_replay.py::test_scope_mode_default_is_implicit_all` — multi-scope without field lints clean.
- `tests/test_incident_replay.py::test_scope_mode_any_explicit_passes` — explicit `any` lints clean.
- `tests/test_incident_replay.py::test_scope_mode_invalid_value_fires_026` — bad value fires BBE-COMM-026.

## Consequences

### Positive

- The default is the safer reading (AND is more restrictive than OR).
- Operators get explicit signal when they want OR — no ambiguity.
- The `claim-id` mechanism (in the runtime patch) makes OR semantics atomic at consume time, avoiding double-consume.

### Negative

- Existing RC1 multi-scope grants in the wild (if any) had OR-by-default behaviour. They will now require `@scope_mode: any` to keep working. Mitigation: the rollout's 14-day warning window catches this; AGUARD audit logs flag grants that would change semantic interpretation.

### Migration

- During Phase D (14-day warning), the AGUARD hook emits `[AGENT-WARNING severity:warn]` when it sees a multi-scope grant without `@scope_mode`. After 2026-05-28, the hook silently applies AND-default per the spec.

## Cross-references

- RC2 spec §5.2, §7.3, §9.1 (BBE-COMM-026)
- `tools/bbe-comm/bbe_comm/rules/authorization.py`
- `patches/bbe-server-config/userprompt-hook-multi-scope.diff`
- `tests/test_incident_replay.py` (3 tests)
