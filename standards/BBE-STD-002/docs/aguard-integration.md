# BBE-STD-002 v1.0-RC1 — AGUARD integration (Annex A standalone)

This document is a re-issue of the spec's Annex A as a standalone reference.
It is **informative**, BBE-deployment-specific. Other deployments may bind
the format spec to their runtime differently or not at all.

## Component layout

| Path | Owner | Purpose |
|---|---|---|
| `/var/lib/bbe-guard/op-secret` | root:root 0600 | 32-byte raw secret used as HMAC key |
| `/var/lib/bbe-guard/consumed-nonces/` | root:bbe-guard 0750 | One empty file per consumed `@nonce` (replay protection) |
| `/var/lib/bbe-guard/tokens/` | root:bbe-guard 0750 | One YAML file per active GO-token |
| `/var/log/bbe-blocks/incoming.jsonl` | root:bbe-guard 0640 | Every parsed block (valid or not) — append-only |
| `/var/log/bbe-blocks/issued.jsonl` | root:bbe-guard 0640 | Every block emitted by `bbe-block sign` — append-only |
| `/var/log/bbe-guard/audit.jsonl` | root:bbe-guard 0640 | AGUARD audit log — append-only |
| `/usr/local/sbin/bbe-block` | root:root 0750 | Operator CLI (root-required) |
| `/usr/local/bbe-guard/lib/userprompt-hook.sh` | root:root 0755 | UserPromptSubmit hook |
| `/usr/local/bbe-guard/lib/pretool-hook.sh` | root:root 0755 | PreToolUse hook (token consume) |

## UserPromptSubmit hook flow

```
operator pastes block
       │
       ▼
Claude Code UserPromptSubmit hook (bash)
       │
       ├── extract [LABEL] blocks via regex (any uppercase label)
       │
       ├── for each block where @type ∈ {operator_auth, operator_deny}:
       │     ├── check required fields (spec §7.2)
       │     ├── check nonce not in consumed-nonces/ (replay)
       │     ├── recompute HMAC over canonical body (spec §5.1)
       │     ├── compare with @hmac (spec §5.2)
       │     │
       │     ├── on auth-valid:
       │     │     for each scope token in @scope (multi-scope grants OK):
       │     │       write GO-token to /var/lib/bbe-guard/tokens/<uuid>.yaml
       │     │     mark nonce consumed
       │     │     audit: incoming.jsonl + audit.jsonl
       │     │     emit additionalContext to agent: "[bbe-guard] OPERATOR-AUTH … ACCEPTED → token <uuid>"
       │     │
       │     └── on deny-valid:
       │           rm /var/lib/bbe-guard/tokens/* matching from-block:<id>
       │           mark nonce consumed
       │           audit
       │           emit additionalContext
```

## PreToolUse hook flow

```
agent attempts a tool call (Bash, Edit, etc.)
       │
       ▼
Claude Code PreToolUse hook (bash)
       │
       ├── classify scope from tool + command (e.g. "pm2 reload" → pm2-mutate)
       ├── classify target from cwd / repo / process name
       │
       ├── search /var/lib/bbe-guard/tokens/ for token matching {scope, target}
       │     ├── match found:
       │     │     ├── consume (move to tokens-used/)
       │     │     ├── audit: GUARD-DECISION layer:L3 decision:allow reason:go-token-consumed
       │     │     └── return {permissionDecision: allow}
       │     │
       │     └── no match:
       │           ├── audit: GUARD-DECISION layer:L3 decision:deny reason:no-matching-token
       │           └── return {permissionDecision: deny}
```

## Repo-pivot detection

The PreToolUse hook also inspects:

- `git remote get-url origin` from the working tree at action-time
- The `@target` of the most recent `operator_auth` token
- The `@correlation_id` of the originating `operator_prompt`

If any of these shifts mid-session, the hook emits
`[GUARD-DECISION decision:deny reason:repo-pivot-without-auth]` and refuses
the tool call until a fresh `operator_auth` arrives.

## Audit join keys

| Field | In `incoming.jsonl` | In `audit.jsonl` | In agent transcripts |
|---|---|---|---|
| `@id` | yes | yes (as `block-auth-id`) | yes (in additionalContext) |
| `@nonce` | yes | yes | no |
| `@correlation_id` | yes | yes | yes |
| `cmd_hash` | no | yes | yes (in `[GUARD-DECISION]`) |
| GO-token `uuid` | yes (`valid-token-issued` verdict) | yes (`block-auth-token-issued` action) | yes |

A complete audit trail for "what authorized X?" joins on `@nonce`
(block→token issuance) and on `uuid` (token issuance→token consume).

## Mode awareness

The mode is a single-line file at `/var/lib/bbe-guard/mode`.

| AGUARD mode | UserPromptSubmit hook | PreToolUse hook |
|---|---|---|
| `OFF` | Hook not loaded | Hook not loaded |
| `STATUS` | Logs only; no token issuance | Logs only; allows everything |
| `GUIDED` | Issues tokens for valid `operator_auth`; rejects invalid | Allows w/ token; warns w/o token |
| `DEPLOY` | Same as GUIDED | Allows w/ token; **denies** w/o token |
| `BREAK-GLASS` | Issues tokens; logs everything | Allows everything; logs at audit-WARN |

## Bash-vs-Python boundary

The hook is in **Bash**, not Python, by design:

- The hook fires on every operator prompt (high frequency).
- Fork-exec to Python adds ~50ms latency per prompt that no operator wants.
- The Bash regex extractor is simple and proven (8/8 of A's e2e tests pass).
- HMAC computation lives in shared `lib/hmac.sh` (used by both
  `bbe-block-cli.sh` and `userprompt-hook.sh`) — byte-identical canonical
  bodies between operator-side signing and server-side verification.
- On parse anomaly, the hook MAY invoke `bbe-comm-lint` (Python) for
  deeper structural validation. This is the slow path.

The Python linter (`lint/bbe_comm_lint.py`) runs:

- author-side (developer, CI) for full 25-check validation;
- in tooling pipelines that need JSON-structured findings (`--json`);
- as the slow-path fallback inside the Bash hook when extraction fails.

## Installation script outline

The `bbe-server-config` repo ships an installer that:

1. Generates `/var/lib/bbe-guard/op-secret` (32 raw bytes from `/dev/urandom`,
   chmod 0600, root:root).
2. Installs `bbe-block` to `/usr/local/sbin/`, `userprompt-hook.sh` and
   `pretool-hook.sh` to `/usr/local/bbe-guard/lib/`.
3. Wires the hooks into the system Claude Code `managed-settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": "/usr/local/bbe-guard/lib/userprompt-hook.sh",
       "PreToolUse": "/usr/local/bbe-guard/lib/pretool-hook.sh"
     }
   }
   ```
4. Creates the audit log directories and rotates them via `logrotate`.
5. Adds `bbe-guard` group; adds the operator user to it.
6. Verifies with the e2e test (`tests/test_e2e_hmac.sh`).

## Key rotation

```
sudo bbe-block rotate-secret
```

Generates a fresh 32-byte op-secret. **All in-flight tokens become invalid
immediately.** Operator must re-issue any active `operator_auth`. The old
op-secret is overwritten in place; no archival (per BBE security policy —
recoverable old secrets are recoverable threats).
