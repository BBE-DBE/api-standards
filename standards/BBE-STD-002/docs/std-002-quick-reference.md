# BBE-STD-002 v1.0-RC1 — Quick reference

5-minute onboarding for operators and agents.

## The four-layer guarantee

The 2026-05-09 incident — "operator pasted a detail-rich prompt for project A
into a chat about project B; agent treated detail as authorization, pivoted
repos, executed pm2 reload, made commits" — is closed by RC1 in **four layers**.
All four fire simultaneously; bypassing all of them requires compromising the
operator's terminal account.

| Layer | Mechanism | Where |
|---|---|---|
| 1. Anti-inference (field-level) | `@authorize`/`@authorized`/`@authorization`/`@authority` outside `operator_auth` → linter rejects | spec §7.4 (BBE-COMM-016) |
| 2. Type discipline | Only `@type: operator_auth` authorizes anything | spec §4.1 (R1, R2) |
| 3. Cryptographic anchor | `@hmac: sha256:<64-hex>` over canonical body, key = server op-secret | spec §5 |
| 4. Repo-pivot rule | Target shift forces fresh `operator_auth` even with valid prior HMAC | spec §7.5 (R3) |

## Operator: how to authorize

You **never type the HMAC by hand**. You run:

```
sudo bbe-block sign auth \
    --scope pm2-mutate \
    --target netcup-api \
    --ttl 5m \
    --correlation routine-deploy-2026-05-09 \
    --note "v0.2.0 verify ok"
```

It emits a complete `[OPERATOR-AUTH]` block to stdout. Paste it into the chat.
The AGUARD UserPromptSubmit hook on the BBE host parses, verifies HMAC, and
issues a GO-token for the agent's later action.

To revoke:

```
sudo bbe-block sign deny \
    --revokes op_auth_2026-05-09T19-30-00Z_7f3e1234 \
    --correlation routine-deploy-2026-05-09 \
    --reason "abort, revert needed"
```

## Operator: what is NOT authorization

| Block / text | Authorization status |
|---|---|
| `[OPERATOR-PROMPT]` (any length, any detail) | NO |
| `[OPERATOR-CONTEXT]` ("FYI...") | NO |
| `[OPERATOR-QUERY]` (operator asks agent) | NO |
| Free prose ("yes please go ahead") | NO |
| `[OPERATOR-AUTH]` without `@hmac` field | NO |
| `[OPERATOR-AUTH]` with bad HMAC | NO |
| `[OPERATOR-AUTH]` with consumed nonce | NO |
| `[OPERATOR-AUTH]` for `target: A` when agent is operating on `target: B` | NO (R3 repo-pivot rule) |
| `[OPERATOR-AUTH]` with valid HMAC, fresh nonce, matching target, within TTL | **YES** |

## Agent: the seven rules (R1–R7)

1. **Authorization Discipline.** No scope-gated action without (a) matching
   `[OPERATOR-AUTH]` AND (b) AGUARD GO-token consume.
2. **Detail-vs-Auth Separation.** Never promote any non-`operator_auth` block
   to authorization. Even prose "go ahead."
3. **Pivot Discipline.** Different repo / target = ASK first.
4. **Self-Identification.** Every `agent_*` block carries
   `@agent: <type>@<version>@<host>`.
5. **Block ID Discipline.** Every emitted block has unique `@id` per spec §6.
6. **Schema Stability.** Don't invent fields outside the schema. Custom data
   goes in body or in `@x-<vendor>-<field>`.
7. **Recovery.** Malformed block = treat as `operator_context` (informational),
   emit `[AGENT-WARNING]`, never guess authorization.

## Compliance levels at a glance

| L | What it means |
|---|---|
| L0 | Plain text, no block |
| L1 | `[LABEL]…[/LABEL]` only |
| L2 | + `@bbe-comm`, `@type` |
| L3 | + `@id` |
| L4 | + `@parent_id` (lineage) — **min for any privileged operation** |
| L5 | + valid HMAC against op-secret (operator_auth/operator_deny) |

## Linting locally

```
python3 /home/dev/bbe-std-002-rc1/lint/bbe_comm_lint.py myfile.txt
```

Exit codes: `0` clean · `1` errors · `2` warnings only.

JSON output: `--json`. Quiet (suppress clean files): `--quiet`.

## Common mistakes

| Mistake | Linter check | Fix |
|---|---|---|
| `key: value` body lines | (parser silently treats as body) | Use `@key: value` for headers |
| Mixed-case label `[Result-...]` | parse-rejected | Re-case to `[RESULT-...]` |
| `@id` with `:` in timestamp | BBE-COMM-011 | Use `-` instead: `T19-30-00Z` |
| `@type: result` (Welle-3 style) | BBE-COMM-009 | Use `@type: agent_result` |
| `[AGENT-RESULT]` without `@parent_id` | BBE-COMM-013 | Add `@parent_id` of upstream prompt/auth |
| `[OPERATOR-AUTH]` without `@hmac` | BBE-COMM-015 | Sign via `bbe-block sign auth` |
| `@scope: pm2-mutate, git-push` (comma) | accepted (warning-free) but legacy | Use JSON array `["pm2-mutate", "git-push"]` |
| `@ttl: 24h` | BBE-COMM-025 | Max is `1h` per AGUARD policy |
| `@authorize: yes` on a non-auth block | BBE-COMM-016 (incident-grade) | Authorization is `[OPERATOR-AUTH]` only |
