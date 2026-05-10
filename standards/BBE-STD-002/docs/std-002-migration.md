# BBE-STD-002 v1.0-RC1 — Migration guide

How to convert legacy patterns to RC1.

## Welle-3 → RC1 mechanical conversion

| Welle-3 pattern | RC1 conversion |
|---|---|
| `[RESULT-<TASK-NAME>]…[/RESULT-<TASK-NAME>]` | Label preserved; add `@bbe-comm: 1.0`, `@type: agent_result`, `@id`, `@parent_id`, `@agent`, `@status`. |
| `[BLOCKER-<TOPIC>]…[/BLOCKER-<TOPIC>]` | Label preserved; `@type: agent_warning`, `@severity: warn`, `@status: open`. |
| `[QUESTION-<TOPIC>]…[/QUESTION-<TOPIC>]` | Label preserved; `@type: agent_query`, `@ask: <topic>`. |
| `[OPERATOR · <TASK> · <PHASE>]` | Label re-cased to `OPERATOR-<TASK>-<PHASE>`; `@type: operator_prompt`. |
| Free-form `status:` line in body | Move to `@status:` header. |
| Implicit "this is a response to X" by adjacency | Make explicit via `@parent_id`. |
| Mixed-case tag names (`[Result-…]`) | Re-case to `^[A-Z][A-Z0-9_-]*$`. Linter rejects mixed-case tags. |
| Authorization implied by emphatic body text (`"GO"`, `"yes proceed"`) | **REJECTED** — direct violation of §7.1 anti-inference rule. |

## Welt A `key: value` → RC1 `@key: value`

If you have existing Welt A blocks like:

```
[OPERATOR-AUTH v1.0]
id: op_auth-2026-05-09T19:30:00Z-7f3e
session: routine-netcup-api-deploy-2026-05-09
scope: pm2-mutate
target: netcup-api
ttl: 5m
issued_by: BBE-DBE
nonce: 9c8f2a1b
hmac: sha256:b1d4f7c8...
[/OPERATOR-AUTH]
```

Convert to RC1:

```
[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@correlation_id: routine-netcup-api-deploy-2026-05-09
@scope: ["pm2-mutate"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8...
[/OPERATOR-AUTH]
```

Mechanical changes:

1. Remove ` v1.0` from the opening tag.
2. Add `@bbe-comm: 1.0` as the first header line.
3. Add `@type: operator_auth` as the second header line.
4. Prepend `@` to every header key.
5. Rename `session` → `correlation_id`.
6. Convert `:` in `@id` time portion to `-` (filename safety).
7. Pad random-suffix to exactly 8 hex chars (was 4-8 in Welt A).
8. Convert `scope` value to JSON array: `pm2-mutate` → `["pm2-mutate"]` (or
   leave shorthand — linter accepts both).
9. **The HMAC stays valid** if you regenerate the canonical body using the
   RC1 `tools/hmac.sh::canonical_auth_body` (which uses the new field order:
   id, correlation_id, scope, target, ttl, issued_by, nonce, [not_after]).
   If you only renamed fields without re-signing, **HMAC will mismatch**.
   Re-sign with `bbe-block sign auth` against the same op-secret.

## Welt B `authorization_grant` → RC1 `operator_auth`

Welt B blocks like:

```
[GRANT-DEPLOY-PROD]
@bbe-comm: 1.0
@type: authorization_grant
@id: msg_2026-05-09T19-00-00Z_c3d4e5f6
@parent_id: msg_2026-05-09T18-55-00Z_d4e5f6a7
@agent: operator
@scope: ["deploy:bbe-coord:prod"]
@one_shot: true
@compliance_level: L4
[/GRANT-DEPLOY-PROD]
```

**These do not carry HMAC.** Under RC1, they are only valid as:

- a generic `x-<vendor>-grant` extension type (vendor namespace, no
  AGUARD interop), OR
- (preferred) re-emit as `operator_auth` with HMAC via `bbe-block sign auth`.

`@one_shot: true` is no longer needed on `operator_auth` — the nonce
mechanism enforces single-use. For non-AGUARD-bound grants in vendor
extensions, `@one_shot: true` may still be carried under `@x-<vendor>-…`
extensions.

## Backward compatibility

RC1 is **forward-only**. There is no automatic backward-compat shim.
Welle-3 logs and Welt-A/-B blocks are not retroactively re-parsed.
Per OPEN_ISSUES-RC1.md (B's #13 forwarded), backfill is BBE-STD-003's
domain when it lands.

Existing audit logs remain readable as plain text. They simply do not
participate in the RC1 compliance ladder.
