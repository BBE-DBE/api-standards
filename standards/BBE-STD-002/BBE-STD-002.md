# BBE-STD-002 — Agent Communication Protocol

| Field | Value |
|---|---|
| Standard ID | BBE-STD-002 |
| Title | Agent Communication Protocol |
| Version | **1.0-RC2** |
| Status | RELEASE-CANDIDATE-2 (8 RC1-open-issues resolved per operator mandate 2026-05-09; pending final ratification per OPEN_ISSUES-RC2.md) |
| Effective | upon Phase B acceptance per §13 |
| Owner | `api-standards/standards/` (canonical home, post-rename); `bbe-server-config/` is runtime integration home; `/home/dev/bbe-std-002-rc1/` is staging (non-canonical) |
| Author | claude_integrator_21 (RC2 hardening under OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION; consolidates Welt-A + Welt-B and applies 8 operator decisions) |
| Supersedes | BBE-STD-002 v1.0-RC1 (this repo, 2026-05-09) and its predecessors (Welt A `RATIFIED-CANDIDATE`; Welt B v0.1.0-draft) |
| Pairs with | `schema/BBE-STD-002.schema.json` · `tools/bbe-comm/` (Python CLI package) · `tools/bbe-block-cli.sh` (operator HMAC CLI) · `tools/userprompt-hook.sh` (AGUARD reference binding) · `examples/` golden corpus · `templates/blocks/` · `docs/adr/` |
| Cross-refs | `BBE-STD-001-FINAL-ACCEPTANCE.md` · `BBE-POL-008-AGENT-AUTONOMY.md` · `BBE-STD-AGUARD-001` (REFERENCE binding, ADR-0005; **not a STD-002 prerequisite**) · `iso-mappings/27001-controls.md` |
| Companion specs (deferred — NOT authored here) | POL-009 Authorization Decision Policy · BBE-STD-003 Audit-Store & Message Persistence · ENG-001 Decision-Engine Interface |
| Known evidence gap | Two external analyses referenced in original mandates were not visible to the authoring sessions or the RC2 integrator. Ratification proceeds without them; deltas land in RC2.1 if they surface. |
| Runtime posture | **Runtime-agnostic.** Conformance does not require AGUARD, BBE infrastructure, or any specific runtime. Annex A describes the BBE reference binding only. |

---

## §1 Purpose

BBE-STD-002 defines the **structural communication protocol** between **operator** and **agent** (and between agents) on every BBE host, in every project, across every agent vendor (Claude, Codex, GPT, future).

The standard answers four load-bearing questions that the previous ad-hoc `[TAG]…[/TAG]` convention left implicit, and that incident **I-2026-05-09-01** exposed as schema-level requirements:

1. **What carries authorization?** Exactly one block type (`operator_auth`) carries authorization. Detail-rich prompts do not. (§4, §7)
2. **How is authorization verifiable?** Every `operator_auth` carries an HMAC-SHA256 over its canonical body, computed against a server-stored secret. No HMAC ⇒ no authorization, even if the textual content is convincing. (§5)
3. **How are blocks correlated across turns / sessions / hosts / agents?** Every block has a globally unique `@id`, an optional `@parent_id`, an optional `@correlation_id` (workflow group), an optional `@refs` array (many-to-many), a required `@correlation_id` ON privileged messages, and a structured `@agent` identifier. (§6)
4. **How does this couple to enforcement?** This is **runtime-specific**. The standard itself defines the format and the agent rules (§7); the binding to a specific runtime is informative. The BBE reference binding (Annex A) shows how AGUARD converts valid `operator_auth` blocks to GO-tokens via a UserPromptSubmit hook, and how PreToolUse consumption keeps chat-text and server-state in lock-step. Other runtimes are conformant if they implement equivalent enforcement of §7's normative agent rules.

### §1.1 Incident I-2026-05-09-01

> Operator pasted a detail-rich, well-structured prompt for project A into a chat about project B. The agent treated the detail as authorization, pivoted repos, executed `pm2 reload`, and made 6 commits.

This standard makes that failure a **schema violation, not a judgment call**, in four independent layers. **Layers 1–3 are runtime-agnostic** (every conformant deployment has them). **Layer 4 is split**: 4a is the agent rule (runtime-agnostic), 4b is one possible runtime enforcement (the BBE reference binding via AGUARD; informative, see Annex A).

| # | Layer | Mechanism | Source | Runtime-agnostic? |
|---|---|---|---|---|
| 1 | Anti-inference (field-level) | `@authorize`/`@authorized`/`@authorization`/`@authority` forbidden outside `operator_auth`; auth-only fields forbidden outside `operator_auth`/`operator_deny` | §7.4 (BBE-COMM-016, BBE-COMM-022) | yes |
| 2 | Type discipline | Only `@type: operator_auth` authorizes; any other type rejected at the gate | §4.1 (R1, R2) | yes |
| 3 | Cryptographic anchor | HMAC-SHA256 over canonical body; no HMAC ⇒ no authorization. **HMAC is L4 — see §8 for the L4/L5 distinction.** | §5 | yes (the *format* of HMAC is universal; *who holds the key* is runtime-specific) |
| 4a | Repo-pivot rule (agent) | Target shift forces fresh `operator_auth` even with valid HMAC for prior target | §7.5 (R3) | yes (normative agent rule) |
| 4b | Repo-pivot enforcement (runtime) | AGUARD's PreToolUse hook detects target shift and emits `[GUARD-DECISION decision:deny reason:repo-pivot-without-auth]` | Annex A.4 | **no** — BBE-deployment-specific reference binding |

Adoption of BBE-STD-002 makes I-2026-05-09-01 a detectable, audit-emittable schema violation in any conformant deployment, and a machine-blocked event in deployments using a runtime binding equivalent to AGUARD.

---

## §2 Scope and non-goals

### §2.1 In scope

- **Wire format** for operator↔agent and agent↔agent textual communication.
- **Required and optional fields** per block type (§5).
- **Authorization mechanics** (HMAC, scope vocabulary, replay protection, repo-pivot) (§7).
- **Compliance levels** (L0–L5) and the privileged-operation gate (§8).
- **Validation reference implementation**: a Python linter + a JSON Schema, plus a Bash adapter for the AGUARD UserPromptSubmit hook (§9).

### §2.2 Out of scope (deferred)

- POL-009 Authorization Decision Policy — *who* may grant *what scope* to *whom*.
- BBE-STD-003 Audit-Store & Persistence — append-only message log.
- ENG-001 Decision-Engine Interface — runtime go/no-go.
- L5 asymmetric-signature mechanism (multi-operator) — reserved for v2.0.
- Transport-layer security — blocks travel as chat text; HMAC anchors integrity but does not encrypt.
- Live key-rotation protocol — manual via `bbe-block rotate-secret` (§5.6).

---

## §3 Terminology

| Term | Meaning |
|---|---|
| Block (= Message) | A single tagged communication unit — `[<LABEL>] @<header>… <body> [/<LABEL>]` |
| Label | The descriptor inside `[…]` and `[/…]`. Mutable, human-friendly. Semantic identity lives in `@type` and `@id`, not the Label. |
| Header | Lines at the top of the body that begin with `@`. Contiguous from the first non-blank line. |
| Body | Free-form content after the header. Markdown, prose, code-fences allowed. Ignored by the parser except for malformed-header heuristics (§9.1 BBE-COMM-020). |
| Type | The semantic kind of a block, carried in `@type:`. From the registry §5.4. |
| ID | Stable, globally-unique block identifier (§6). |
| Lineage | Chain of `@parent_id` references from a block back to the root request. |
| Correlation | Workflow group tag in `@correlation_id`, joining many lineage trees. |
| Compliance Level | Self-declared L0–L5; computed by the linter. (§8) |
| Principal | The producing operator or agent. |
| Scope | An authorized action / capability token, JSON-array form (§7.3). |
| Op-secret | 32-byte file at `/var/lib/bbe-guard/op-secret`, root-owned `0600`, used as HMAC key. |
| Canonical body | Deterministic LF-separated concatenation of fields, used as HMAC input (§5.1). |

---

## §4 Block format (NORMATIVE)

### §4.1 Syntax

A block is a UTF-8 text region delimited by:

```
[<LABEL>]
@bbe-comm: <protocol-version>
@type: <type>
@id: <id>
@parent_id: <id>           # required for L4+ non-root, see §8
@<reserved-field>: <value>
@x-<vendor>-<field>: <value>
…

<body content — markdown, prose, code-fences, anything not header-shaped>
[/<LABEL>]
```

### §4.2 Structural rules

| Rule | Specification |
|---|---|
| Opening tag pattern | `^\[[A-Z][A-Z0-9_-]*\]$` on its own line |
| Closing tag pattern | `^\[/[A-Z][A-Z0-9_-]*\]$` on its own line |
| Label match | The Label between opening and closing tag MUST be byte-identical |
| Label nature | Label is **human-friendly only**. Semantic identity lives in `@type:` and `@id:`. Renaming a Label MUST NOT change message semantics. RECOMMENDED Label = uppercase form of `@type:` value (e.g. `@type: operator_auth` ↔ `[OPERATOR-AUTH]`). |
| Header layout | Header lines start with `@`. They MUST be contiguous from the first non-blank line of the body. The first non-`@` line ends the header. |
| Header parse | Pattern `^@([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$`. Value is everything after the first `:`, trimmed. |
| Header values | Single-line. Multi-line content goes into the body, not into a header value. |
| Same-type nesting | A block of type `T` MUST NOT contain a nested block of type `T` (prevents lineage ambiguity). Cross-type nesting is allowed. |
| Blank lines in body | Allowed and ignored. |
| Multi-block stream | Multiple blocks may appear in sequence; each is parsed independently. |

**Rationale for `@`-prefix:** A's prior `key: value` form (without `@`) collided with body prose — a `note: …` line in body could not be distinguished from a header in markdown contexts. The `@`-prefix is unambiguous and survives every transport (chat, log files, code fences).

---

## §5 Reserved header fields

### §5.1 Common reserved fields

| Field | Required when | Type | Purpose |
|---|---|---|---|
| `@bbe-comm` | always (L2+) | semver `MAJOR.MINOR[.PATCH]` | Protocol version; e.g. `1.0` |
| `@type` | always (L2+) | enum (§5.4) or `x-<vendor>-<type>` | Block semantic |
| `@id` | L3+ | ID pattern (§6) | Stable globally-unique id |
| `@parent_id` | L4+ on non-root | ID pattern | Direct parent block |
| `@correlation_id` | optional (REQUIRED on privileged operations — §7) | ID-shaped string | Workflow group |
| `@refs` | optional | JSON array of IDs, ≤32 entries | Many-to-many cross-references |
| `@agent` | REQUIRED on `agent_*` and `guard_*` types; optional on `operator_*` | `<type>@<version>@<host>` | Emitter identification |
| `@timestamp` | optional | ISO-8601 UTC | Emission time; defaults to ID-embedded ts |
| `@host` | optional | hostname or `local` | Where emitted |
| `@status` | type-dependent | enum per type (§5.4) | Lifecycle marker |
| `@compliance_level` | optional | `L0`..`L5` | Self-declared level |
| `@x-bbe-sig` | optional (reserved for L5) | opaque (STD-003) | Cryptographic signature with externally-verifiable public key |
| `@x-bbe-ledger` | optional (reserved for L5) | opaque (STD-003) | Append-only ledger receipt id |
| `@x-bbe-attest` | optional (reserved for L5) | opaque (STD-003) | External attestation reference |

### §5.2 Authorization-specific reserved fields

These fields are reserved for `operator_auth` and `operator_deny` ONLY. The linter rejects them on any other `@type` (BBE-COMM-016 / BBE-COMM-022 anti-inference rules).

| Field | Required when | Type | Purpose |
|---|---|---|---|
| `@scope` | `operator_auth` | JSON array of scope tokens (§7.3) | Authorized actions |
| `@target` | `operator_auth` | string ≤240 chars | Scope-specific target (process name, repo, unit, hostname) |
| `@ttl` | `operator_auth` | `<int>[smh]`, max `1h` | Authorization lifetime |
| `@nonce` | `operator_auth`, `operator_deny` | 4–16 hex chars, single-use | Replay protection |
| `@hmac` | `operator_auth`, `operator_deny` | `sha256:<64-hex>` | HMAC-SHA256 over canonical body |
| `@issued_by` | `operator_auth` | string ≤80 chars | Granting principal name |
| `@not_after` | optional on `operator_auth` | ISO-8601 UTC | Hard expiry; takes precedence over `@ttl` if present |
| `@revokes` | `operator_deny` | block-id of `operator_auth` to revoke | Target of revocation |
| `@reason` | optional on `operator_deny`, `agent_abort`, `guard_decision` | string ≤240 chars | Why |
| `@scope_mode` | optional on `operator_auth` | enum `{all, any}`, default `all` | Multi-scope semantic (§7.3): AND vs OR |

### §5.3 Anti-inference: forbidden fields

The following field names MUST NOT appear in any block whose `@type` is not `operator_auth`. The linter (BBE-COMM-016) rejects these as errors. Rationale: these names look like authorization; restricting them to the explicit authorization type prevents accidental "authorization by field name" — the structural analogue of the prose-inference incident.

`@authorize`, `@authorized`, `@authorization`, `@authority`

In addition, `@hmac`, `@scope`, `@target`, `@ttl`, `@nonce`, `@issued_by`, `@not_after`, `@revokes` MUST NOT appear outside `operator_auth` / `operator_deny`. The linter (BBE-COMM-022) rejects these as errors.

### §5.4 Type registry (canonical, v1.0)

Type names are snake_case. The registry is **append-only across minor versions**; removal or semantic change requires a major version bump.

| `@type` value | Direction | Recommended Label | Authorizes? | Required fields (beyond common) |
|---|---|---|---|---|
| `operator_prompt` | op→agent | `OPERATOR-PROMPT` | No | — |
| `operator_auth` | op→agent | `OPERATOR-AUTH` | **Yes** (HMAC-anchored) | `@scope`, `@target`, `@ttl`, `@nonce`, `@hmac`, `@issued_by` |
| `operator_deny` | op→agent | `OPERATOR-DENY` | n/a (revokes) | `@revokes`, `@nonce`, `@hmac` |
| `operator_context` | op→agent | `OPERATOR-CONTEXT` | No | — |
| `operator_query` | op→agent | `OPERATOR-QUERY` | No | `@ask` (string ≤1000) |
| `agent_result` | agent→op | `AGENT-RESULT` | n/a | `@status` (`complete`/`partial`/`blocked`/`failed`) |
| `agent_progress` | agent→op | `AGENT-PROGRESS` | n/a | — |
| `agent_query` | agent→op | `AGENT-QUERY` | No (request only) | `@ask` (string ≤1000) |
| `agent_warning` | agent→op | `AGENT-WARNING` | n/a | `@severity` (`info`/`warn`/`error`) |
| `agent_abort` | agent→op | `AGENT-ABORT` | n/a | `@reason` (string ≤240) |
| `guard_decision` | system→audit | `GUARD-DECISION` | n/a (machine-only) | `@layer` (`L1`..`L5`), `@tool`, `@decision` (`allow`/`deny`/`warn`/`break-glass-allow`), `@reason` |
| `audit_record` | system→audit | `AUDIT-RECORD` | n/a (machine-only) | `@subject`, `@action` |

Vendor extensions: `@type: x-<vendor>-<type>`, where `<vendor>` is 2–32 lowercase chars and `<type>` is any header-legal name. Interoperability is not guaranteed across vendors; the linter accepts but does not type-check vendor types.

### §5.5 Status registry per type

For type-restricted lifecycle values, the linter (BBE-COMM-010) warns on out-of-set status:

| `@type` | Allowed `@status` |
|---|---|
| `agent_result` | `complete`, `partial`, `blocked`, `failed` |
| `agent_progress` | `starting`, `running`, `paused` |
| `operator_auth` | `active`, `expired`, `revoked`, `consumed` |
| `agent_warning` | (no status; uses `@severity` instead) |

### §5.6 Extension fields

New header fields not in §5.1 / §5.2 MUST use the namespaced form `@x-<vendor>-<field>` where `<vendor>` is 2–32 lowercase chars + dash + field-legal name. Examples:

- `@x-bbe-trace_id: trace_a1b2c3d4`
- `@x-stripe-customer_ref: cus_…`
- `@x-bbe-sig` (reserved for future asymmetric signatures, mechanism in STD-003)

A v1.0 parser:

- MUST accept unknown `@x-…` header fields (pass-through).
- MUST reject unknown non-`@x-…` header fields not in the reserved set (BBE-COMM-017).
- MUST reject unknown non-`x-…`-prefixed `@type` values (BBE-COMM-009).
- MUST treat `@bbe-comm` MAJOR > supported as a hard error (BBE-COMM-008).
- MAY warn on `@bbe-comm` MINOR > supported within same MAJOR (forward-compat).

---

## §6 ID format (NORMATIVE)

### §6.1 Canonical pattern

```
<type-slug>_<YYYY-MM-DDTHH-MM-SSZ>_<hex8>
```

Regex: `^[a-z][a-z0-9_]{1,16}_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[a-f0-9]{8}$`

Examples:

- `op_auth_2026-05-09T19-30-00Z_7f3e1234`
- `agent_result_2026-05-09T19-31-15Z_8e9f0123`
- `guard_dec_2026-05-09T19-30-14Z_f1a30000`
- `msg_2026-05-09T18-30-00Z_a1b2c3d4` (generic, when type-slug is unknown — interop import)

**Note:** `:` in the time portion is replaced by `-` (filename + log + URL safety). The trailing 8 hex characters are random (≥ 32 bits entropy).

### §6.2 Type-slug convention

| `@type` | type-slug prefix |
|---|---|
| `operator_prompt` | `op_prompt` |
| `operator_auth` | `op_auth` |
| `operator_deny` | `op_deny` |
| `operator_context` | `op_ctx` |
| `operator_query` | `op_query` |
| `agent_result` | `agent_result` |
| `agent_progress` | `agent_progress` |
| `agent_query` | `agent_query` |
| `agent_warning` | `agent_warn` |
| `agent_abort` | `agent_abort` |
| `guard_decision` | `guard_dec` |
| `audit_record` | `audit` |
| (foreign / interop) | `msg` |

The type-slug is parser convenience; the IDs remain unique even with the slug truncated.

### §6.3 Required properties (recap)

| Property | Satisfied by |
|---|---|
| Stable after creation | ID is immutable; never regenerated |
| Globally unique enough | Second-precision timestamp + 32-bit random ⇒ collision rate < 1 in 4 billion per same-second emissions |
| Human-debuggable | Type-slug + ISO timestamp visible at a glance |
| Filename + log + URL safe | No `:`, `/`, spaces, or shell metacharacters |
| Independent of mutable Label | Label changes never affect ID |
| Suitable for `@parent_id` / `@correlation_id` / `@refs` | Plain string, opaque to consumer |

### §6.4 Foreign / interop IDs

`@parent_id`, `@correlation_id`, and entries in `@refs` MAY use foreign-system IDs. The relaxed pattern is:

```
^[a-z]{3,16}_[A-Za-z0-9_-]{8,64}$
```

Reserved interop prefixes (linter does not error, may warn):

| Prefix | Source |
|---|---|
| `op_*` / `agent_*` / `guard_*` / `audit` / `msg_` | Canonical (this standard) |
| `task_` | Task tracker IDs |
| `sess_` | Session IDs |
| `conv_` | Conversation IDs |
| `welle_` | bbe-coord welle identifiers |

The reference linter generates only canonical forms.

---

## §7 Authorization (NORMATIVE — INCIDENT RESPONSE)

This section is the load-bearing reason BBE-STD-002 exists. The format spec is universal; the HMAC mechanism is BBE-deployment-specific. See Annex A for the AGUARD coupling.

### §7.1 Anti-inference rule (HARD)

**Authorization MUST NEVER be inferred.** The following are explicitly NOT authorization:

- Detail level or length of an operator prompt
- Autonomous-mode wording in a prompt
- Repeated `GO` in unrelated context
- Body text, headings, prose, or task-detail
- Intent-interpretation by the agent
- Default permissions inherited from a session or role
- Past authorizations for similar-looking actions

### §7.2 Valid authorization (only form)

Authorization is valid **only** when transported as a block satisfying ALL of:

| Constraint | Source |
|---|---|
| `@type: operator_auth` | §5.4 |
| `@id` present, canonical pattern | §6.1 |
| `@scope` present, JSON array of tokens from the §7.3 vocabulary | §7.3 |
| `@target` present (string, ≤240 chars) | §5.2 |
| `@ttl` present, `<int>[smh]`, max `1h` | §5.2 |
| `@nonce` present, 4–16 hex chars | §5.2 |
| `@hmac` present, `sha256:<64-hex>`, recomputable from canonical body against deployment op-secret | §5.2 + §5.4 |
| `@issued_by` present | §5.2 |
| Nonce not previously consumed | §5.5 (server-side) |
| Block not yet expired (ttl from emission time, or `@not_after`) | §5.2 |
| `@correlation_id` REQUIRED for any privileged operation | §5.1 |

The agent MUST NOT take the authorized action until **both** (a) the block is structurally valid AND (b) a runtime-equivalent enforcement token (in the BBE reference binding: an AGUARD GO-token consumed at PreToolUse, see Annex A.2) is in place. Failure of either condition: agent emits `[AGENT-QUERY]` and waits. Deployments that do not implement a runtime binding satisfy condition (b) by structural validation plus operator-attended action.

### §7.3 Scope vocabulary

`@scope` is a JSON array string of tokens from the canonical scope vocabulary (originally AGUARD-derived; in RC2 the vocabulary is part of the standard, not the runtime). The vocabulary is enumerated below; additions are MINOR-bump.

```
@scope: ["pm2-mutate"]
@scope: ["git-push", "gh-mutate"]
```

Single-token shorthand is accepted by the linter but canonicalised to JSON array on emission:

```
@scope: pm2-mutate           # accepted, canonicalises to ["pm2-mutate"]
```

**Multi-scope semantics (NORMATIVE):**

When `@scope` carries more than one token, the default semantic is **AND** — the granted authorization permits actions matching **ALL** listed scopes against the same `@target`. To grant any-of (OR) semantics, the block carries the optional `@scope_mode: any` field.

```
@scope: ["pm2-mutate", "git-push"]
                                  # AND — agent may do BOTH against @target
@scope: ["pm2-mutate", "git-push"]
@scope_mode: any                  # OR — agent may do EITHER against @target
```

`@scope_mode` is reserved (§5.1). Allowed values: `all` (default if absent) and `any`. The linter (BBE-COMM-026) rejects other values.

Runtime bindings (§16, Annex A) consume `@scope_mode`:

- Under `all` (default), the runtime requires every scope to be satisfied (AGUARD reference: one go-token per scope, all must be in flight at action time).
- Under `any`, the runtime issues N tokens grouped by a shared `claim-id`; the agent's first consume retires the entire group.

Canonical vocabulary (v1.0):

| Scope | Action class |
|---|---|
| `pm2-mutate` | `pm2 reload` / `pm2 restart` / `pm2 stop` / `pm2 start` |
| `git-push` | `git push` to any remote |
| `git-remote-change` | `git remote set-url` / clone-pivot |
| `systemctl-mutate` | `systemctl restart` / `start` / `stop` / `enable` / `disable` |
| `docker-mutate` | `docker run` / `docker stop` / `docker rm` / `docker compose up\|down` |
| `gh-mutate` | `gh pr merge` / `gh release create` / write-side `gh` commands |
| `http-mutate` | Mutating HTTP requests to BBE-internal services |
| `db-mutate` | `psql` / `mysql` write queries; migration apply |
| `fs-mutate-system` | Writes outside the working tree (`/etc`, `/var`, `/usr`) |
| `secret-rotate` | `bbe-block rotate-secret` / vault rotations |

Vocabulary additions are MINOR-bump (forward-compatible).

### §7.4 Forbidden field-name discipline

The linter (BBE-COMM-016, BBE-COMM-022) enforces that:

- `@authorize`, `@authorized`, `@authorization`, `@authority` MUST NOT appear on any block whose `@type` is not `operator_auth`.
- `@hmac`, `@scope`, `@target`, `@ttl`, `@nonce`, `@issued_by`, `@not_after`, `@revokes` MUST NOT appear on any block whose `@type` is not `operator_auth` / `operator_deny` (as applicable).

This is the structural analogue of the prose-inference rule: authorization-shaped fields are restricted to the authorization-shaped block.

### §7.5 Repo-pivot rule (R3, NORMATIVE)

If a request would change the **operating repository** (different `origin` URL, different working directory, different active project), the agent MUST emit `[AGENT-QUERY]` asking for explicit re-authorization, **even if a matching `operator_auth` exists**. Repo-pivots are a separate authorization category; ambiguity defaults to ASK.

A repo-pivot is detected by:

- Different `git remote get-url origin` from the previously-active session.
- Different working tree root.
- Different `@target` named in the active `operator_prompt`.

The AGUARD L3 hook (Annex A.4) also flags repo-pivots and emits `[GUARD-DECISION decision: deny reason: repo-pivot-without-auth]` when an agent attempts to act past a target shift.

### §7.6 Detail-vs-Auth examples

A long, specific operator prompt asking for a netcup-API deploy is an `operator_prompt`, not an `operator_auth`. The agent reads it, plans the work, then emits `[AGENT-QUERY]` for each scope-gated step. The operator responds with `[OPERATOR-AUTH]` blocks signed by `bbe-block sign auth …`. Only then does the agent proceed.

The 5-line response *"Yes, please go ahead"* is an `operator_context` unless it is wrapped in an `operator_auth` block with valid HMAC. The agent that treats the casual reply as authorization is non-conformant per §7.1.

---

## §8 Compliance Levels (NORMATIVE)

| Level | Name | Required features | Use case |
|---|---|---|---|
| **L0** | Unstructured | None — plain text | Legacy free-text, not a block |
| **L1** | Tagged | `[LABEL]…[/LABEL]` syntactic wrapping only | Visual bracketing, no machine parse expected |
| **L2** | Headered | + `@bbe-comm`, `@type` | Type known, minimally parseable. **Minimum for formal reports** (§13). |
| **L3** | Identified | + `@id` (canonical or interop pattern) | Auditable individual block |
| **L4** | Linked + authorization-safe | + `@parent_id` for non-root (lineage integrity); + `@hmac` valid against deployment op-secret WHEN `@type ∈ {operator_auth, operator_deny}`. **Minimum for privileged operations** (§13). | Workflow correlation; HMAC-anchored authorization. |
| **L5** | Hash-linked / signed / ledger-backed / externally auditable | + at least one of: (a) `@x-bbe-sig` — cryptographic signature with externally-verifiable public key (e.g. Ed25519, X.509), (b) `@x-bbe-ledger` — entry into an append-only / hash-linked ledger (Merkle, transparent log) with a referenceable receipt id, (c) `@x-bbe-attest` — external attestation (notary, witness co-sign) | Externally auditable; tamper-evident beyond the runtime's own secret store. **NOT required for v1.0 conformance**; reserved for STD-003. |

**HMAC IS L4, NOT L5.** The runtime authorization anchor (HMAC-SHA256 against a server-stored op-secret) is sufficient for the privileged-operation gate but is **NOT** an external audit anchor — an external auditor cannot verify HMAC without the server's secret, and the secret cannot be shared without breaking the security model. L5 reserves space for *external* verifiability, which v1.0 does not require but v1.x can add additively (MINOR-bump) once STD-003 specifies the algorithm.

The L5 marker fields (`@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest`) are reserved at the format level in v1.0; their **values** are opaque to the v1.0 linter (shape-checked only). STD-003 will specify value formats and verification protocols.

### §8.1 Privileged-operation gate (HARD)

Privileged workflows (production deploys, fund transfers, repo merges, live infrastructure changes, secret reads, sudo commands, push/merge) MUST require:

1. The triggering block at minimum **L4** (lineage-complete).
2. A matching `operator_auth` at **L4** (HMAC-verified against deployment op-secret) within the same `@correlation_id`.
3. A runtime-equivalent enforcement (in the BBE reference binding: AGUARD PreToolUse GO-token consume, §A.3). Deployments without a runtime binding rely on operator-attended action plus structural validation.

A block below L4 is treated as having no authority to request privileged work, regardless of body content. A block at L4 but referencing an `operator_auth` whose HMAC fails verification is treated as unauthorized.

L5 is **desired but not required** for v1.0. It marks the path to external auditability (STD-003).

### §8.2 Self-declaration vs computed

Agents MAY declare their compliance level via `@compliance_level: L4`. The declaration is advisory. The linter computes the actual level from features present and fires:

- `BBE-COMM-019` error if `@compliance_level` value is not `L0..L5`.
- `BBE-COMM-023` error if declared > computed (over-claiming). The check honours the L4/L5 distinction: a block with `@hmac` valid-shape reaches L4, not L5; a block reaches L5 only with a shape-valid `@x-bbe-sig` / `@x-bbe-ledger` / `@x-bbe-attest`.
- silent if declared ≤ computed (under-claiming is harmless).

---

## §9 Validation reference implementation

### §9.1 Linter check inventory (26 checks)

The reference linter ships 26 checks across 9 categories. Checks 1–20 inherited from Welt B; 21–25 introduced in RC1; 26 introduced in RC2 for `@scope_mode`.

The reference implementation is the modular Python package `tools/bbe-comm/` (RC2). The legacy `lint/bbe_comm_lint.py` from RC1 remains as a thin compatibility shim that re-exports `lint()` from the package; existing test suites continue to work without modification.

| ID | Severity | Section | Category | What it catches |
|---|---|---|---|---|
| BBE-COMM-001 | error | §4.2 | Structural | Closing tag without opening |
| BBE-COMM-002 | error | §4.2 | Structural | Label mismatch open/close |
| BBE-COMM-003 | error | §4.2 | Structural | Opening tag without closing |
| BBE-COMM-004 | error | §4.2 | Structural | Label pattern violation |
| BBE-COMM-005 | error | §5.1 | Header | `@bbe-comm` missing |
| BBE-COMM-006 | error | §5.1 | Header | `@type` missing |
| BBE-COMM-007 | error | §11   | Versioning | `@bbe-comm` not semver |
| BBE-COMM-008 | error | §11   | Versioning | Major version unsupported |
| BBE-COMM-009 | error | §5.4 | Type whitelist | Unregistered `@type` |
| BBE-COMM-010 | warning | §5.5 | Status whitelist | Unregistered `@status` for `@type` |
| BBE-COMM-011 | error | §6 | ID | Pattern violation |
| BBE-COMM-012 | warning | §6.2 | ID | type-slug prefix mismatch with `@type` |
| BBE-COMM-013 | error | §5.1 | Lineage | Non-root non-`*_prompt` missing `@parent_id` at L4+ |
| BBE-COMM-014 | error | §6.4 | Lineage | `@parent_id` pattern violation |
| BBE-COMM-015 | error | §7.2 | Auth | `operator_auth` missing required fields |
| BBE-COMM-016 | error | §7.4 | Auth (anti-inference) | Forbidden auth-shaped field outside `operator_auth` |
| BBE-COMM-017 | error | §5.6 | Extension | Non-reserved field without `@x-` prefix |
| BBE-COMM-018 | warning | §5.6 | Extension | `@x-` field without vendor namespace |
| BBE-COMM-019 | error | §8.2 | Compliance | `@compliance_level` not in `L0..L5` |
| BBE-COMM-020 | warning | §4.2 | Layout | Header-shaped line in body |
| **BBE-COMM-021** | error | §4.2 | Structural | Same-type nesting (B's open-issue #12 closed) |
| **BBE-COMM-022** | error | §7.4 | Auth (anti-inference) | Auth-only fields (`@hmac`, `@scope`, etc.) on non-auth blocks |
| **BBE-COMM-023** | error | §8.2 | Compliance | Declared `@compliance_level` exceeds computed level |
| **BBE-COMM-024** | error | §7.3 | Auth (scope) | Scope token outside canonical vocabulary |
| **BBE-COMM-025** | error | §5.2 | Auth | `operator_auth` `@ttl` exceeds policy max (`1h`) |
| **BBE-COMM-026** | error | §7.3 | Auth (scope) | `@scope_mode` value not in `{all, any}` |

### §9.2 CLI

The RC2 reference CLI is `bbe-comm` (Python package, `tools/bbe-comm/`). It exposes subcommands beyond raw lint:

```
bbe-comm lint <file>...                # validate (exit 0/1/2)
bbe-comm score <file>                  # compute L0..L5 per block
bbe-comm trace <file>...               # check parent_id / correlation_id chains
bbe-comm explain <CHECK-ID>            # human-readable explanation of a finding
bbe-comm repair-suggest <file>         # propose minimal fixes
bbe-comm normalize <file>              # Welle-3 / Welt-A → RC2 mechanical convert
bbe-comm emit <type>                   # print template
bbe-comm verify-hmac <file>            # check HMAC against op-secret (delegates)
bbe-comm incident-test <file>          # detect prose-only auth-inference attempt
bbe-comm auth-check <file>             # prose-vs-block authorization audit
bbe-comm integrate-guard <file>        # AGUARD-decision-envelope JSON output
bbe-comm learn observe <event-json>    # append a learning event
bbe-comm learn suggest                 # synthesise process-improvement suggestions
```

Universal flags: `--json` (machine-readable result), `--quiet` (suppress clean files).

Exit codes (universal):

| Code | Meaning |
|---|---|
| 0 | success / valid / clean |
| 1 | invalid / lint errors present |
| 2 | security violation (auth-inference of unusual severity) |
| 3 | lineage error (broken `@parent_id` / `@correlation_id` chain) |
| 4 | auth inference attempt detected (prose-only "go ahead" without `operator_auth`) |
| 5 | tool / runtime error (file not found, parse crash, etc.) |

### §9.3 Schema mode

The Python linter performs **structural** + **schema** validation. The companion `schema/BBE-STD-002.schema.json` (JSON Schema 2020-12) gives a cross-tool contract. External validators (ajv-cli, Go json-schema, etc.) consume the same schema.

### §9.4 Server-side validation (AGUARD hook)

The AGUARD `UserPromptSubmit` hook (`tools/userprompt-hook.sh`) extracts `operator_auth` / `operator_deny` blocks via Bash regex, verifies HMAC + nonce, and issues / revokes GO-tokens. It does NOT perform full Python-linter validation per prompt (avoid fork-exec on hot path); on parse anomalies, it falls back to invoking `bbe-comm-lint`. See Annex A.

### §9.5 Golden corpus

`examples/valid/*.txt` — at least one example per `@type`, with all required and many optional fields populated. Linter MUST pass all of these clean.

`examples/invalid/*.txt` — labelled `NNN-<reason>.txt` where `NNN` matches `BBE-COMM-NNN`. Linter MUST fire the named check on each.

---

## §10 Examples

See `examples/valid/` for the full corpus. Below are inline canonical examples.

### §10.1 Operator authorizes a PM2 reload (the headline example)

```
[OPERATOR-PROMPT]
@bbe-comm: 1.0
@type: operator_prompt
@id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: routine-netcup-api-deploy-2026-05-09

netcup-api: rebase feat/auth onto main, run tests, if green ask for
pm2 reload authorization.
[/OPERATOR-PROMPT]
```

```
[AGENT-PROGRESS]
@bbe-comm: 1.0
@type: agent_progress
@id: agent_progress_2026-05-09T19-28-30Z_3c4d5e6f
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: routine-netcup-api-deploy-2026-05-09
@agent: claude-opus-4-7@2.1.138@v2202.bbe.internal
@status: running
@compliance_level: L4

Rebase clean, tests green (24/24). Requesting pm2-mutate auth.
[/AGENT-PROGRESS]
```

```
[AGENT-QUERY]
@bbe-comm: 1.0
@type: agent_query
@id: agent_query_2026-05-09T19-29-45Z_5e6f7890
@parent_id: agent_progress_2026-05-09T19-28-30Z_3c4d5e6f
@correlation_id: routine-netcup-api-deploy-2026-05-09
@agent: claude-opus-4-7@2.1.138@v2202.bbe.internal
@ask: pm2-mutate authorization for netcup-api after green test run
@compliance_level: L4
[/AGENT-QUERY]
```

```
[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: agent_query_2026-05-09T19-29-45Z_5e6f7890
@correlation_id: routine-netcup-api-deploy-2026-05-09
@scope: ["pm2-mutate"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2

Authorize PM2 reload after netcup adapter v0.2.0 verification.
[/OPERATOR-AUTH]
```

### §10.2 Operator INFO that is NOT auth

```
[OPERATOR-CONTEXT]
@bbe-comm: 1.0
@type: operator_context
@id: op_ctx_2026-05-09T19-32-00Z_a1b2c3d4
@correlation_id: routine-netcup-api-deploy-2026-05-09

FYI — netcup adapter v0.2.0 is the version we shipped on Tuesday.
[/OPERATOR-CONTEXT]
```

This block contains content that *sounds* operationally relevant. It authorizes nothing.

### §10.3 Agent self-aborts on detected pivot (R3)

```
[AGENT-ABORT]
@bbe-comm: 1.0
@type: agent_abort
@id: agent_abort_2026-05-09T19-33-11Z_c3d4e5f6
@parent_id: op_prompt_2026-05-09T19-32-55Z_b2c1d3e4
@correlation_id: routine-hetzner-storagebox
@agent: claude-opus-4-7@2.1.138@v2202.bbe.internal
@reason: repo-pivot-detected
@compliance_level: L4

Active session targets hetzner-api. Operator's last prompt mentions
netcup-api (different origin remote, different scope target). Rule R3
(BBE-STD-002 §7.5) requires fresh operator_auth for new target.
Halting.
[/AGENT-ABORT]
```

This is the incident-fix in literal form: the agent recognises the target shift and refuses to proceed.

### §10.4 Guard decision (system-emitted)

```
[GUARD-DECISION]
@bbe-comm: 1.0
@type: guard_decision
@id: guard_dec_2026-05-09T19-30-14Z_f1a30000
@correlation_id: routine-netcup-api-deploy-2026-05-09
@agent: bbe-guard@0.1.0@v2202.bbe.internal
@layer: L3
@tool: Bash
@decision: allow
@reason: go-token-consumed

Token op_auth_2026-05-09T19-30-00Z_7f3e1234 consumed.
scope=pm2-mutate target=netcup-api
cmd_hash=sha256:e8d7c6aa…
[/GUARD-DECISION]
```

These are auto-emitted into the conversation when `BBE_GUARD_EMIT_DECISIONS=1` (default off; on for incident-response or compliance audit).

---

## §11 Versioning + evolution

| Item | Versioning |
|---|---|
| Standard document | semver — `BBE-STD-002 v1.0-RC1` → `v1.0.0` on ratification |
| Protocol identifier in `@bbe-comm` | `MAJOR.MINOR[.PATCH]` — agents emit at minimum `MAJOR.MINOR` |
| Breaking change | MAJOR bump (e.g., removing a registered `@type`, changing ID format, retiring HMAC for asymmetric signatures) |
| Backward-compatible addition | MINOR bump (new `@type`, new optional `@`-field, new scope token) |
| Editorial / clarification | PATCH bump |

Future versions:

- **v1.x (MINOR-bumps)** may add: `operator_delegate` (multi-operator handoff), `agent_handoff` (cross-agent), `audit_record` field expansions, **L5 marker-field algorithm bindings** (`@x-bbe-sig`, `@x-bbe-ledger`, `@x-bbe-attest` value formats — owned by STD-003 when it lands). All forward-compatible: old parsers warn but accept.
- **v2.0** is reserved for breaking changes — at minimum, retirement of HMAC-symmetric authorization in favour of asymmetric signatures (Ed25519 / X.509) at L4. Multi-operator workflows become first-class. All v1.x HMAC-based authorizations become invalid at the v2.0 boundary.

Parsers MUST reject blocks with `@bbe-comm MAJOR > supported`. Parsers SHOULD warn but accept blocks with `MINOR > supported`.

---

## §12 What this standard does NOT do

1. **No prompt-injection defense for the OPERATOR.** If a malicious actor takes over the operator's terminal, they can run `bbe-block sign auth …` and emit valid HMACs. Trust boundary is the operator account, not the chat content.
2. **No semantic check on block content.** A valid `operator_auth` for `scope: ["pm2-mutate"], target: prod-payments-api` is parsed as a valid grant. The standard does not encode "is this scope safe for this target" — that is policy (POL-009).
3. **No transport-layer security.** Blocks travel in chat (plain text). The HMAC anchors integrity; it does not encrypt. Sensitive content should not appear in block bodies or `@reason` fields.
4. **No retroactive authorization.** A block emitted *after* an action does not retroactively authorize the action. Runtime audit logs (in BBE: AGUARD's `audit.jsonl`) make the time-order verifiable.
5. **No coverage of non-textual channels.** Function-call APIs (e.g. tool-use schemas in LLM SDKs) operate at a different layer; STD-002 describes the textual layer humans read and audit. Tool-call metadata MAY embed STD-002 blocks in argument fields, but is not itself an STD-002 block.
6. **No live-key-rotation protocol** in v1.0. Key rotation is a manual operator action: `sudo bbe-block rotate-secret`. All in-flight tokens become invalid.
7. **No multi-operator support at L4.** Single op-secret = single operator at the HMAC layer. Multi-operator at L4 requires asymmetric signatures (v2.0). At L5, multi-operator is enabled by `@x-bbe-attest` (witness co-signing), pending STD-003.
8. **No external auditability at L4.** HMAC against a server-stored secret is not externally verifiable (the auditor would need the secret). External audit requires L5 (signature, ledger, or attestation). HMAC is intentionally L4, not L5; STD-003 provides the external-audit path.
9. **No requirement to use AGUARD or any specific runtime.** AGUARD is one reference binding; the standard is runtime-agnostic. Conformant deployments may bind to other runtimes (or to no runtime, with operator-attended action) and still be STD-002-compliant.

---

## §13 Migration

### §13.1 Phased rollout

| Phase | Description | Owner | Target |
|---|---|---|---|
| **A** | Author RC1 → RC2 (this document) | claude_integrator_21 | 2026-05-09 |
| **B** | Operator review + ratification → v1.0.0; canonical home = `api-standards/standards/`; runtime integration home = `bbe-server-config/` | BBE-DBE | 2026-05-12 (Tag 4) |
| **C** | Install on `<BBE_PRIMARY_HOST>` (Netcup): seed `op-secret`, deploy `bbe-block` CLI to `/usr/local/sbin/`, wire `userprompt-hook.sh` into `managed-settings.json`. Multipass-bridge hard-gate update. | BBE-DBE + bbe-server-config | 2026-05-13 |
| **D** | Broadcast: every BBE-DBE service repo gets a 1-line `STANDARDS.md` reference; agent prompts (CLAUDE.md / AGENTS.md) cite STD-002 R1–R7 as hard rules. **14-day warning mode: 2026-05-13 → 2026-05-27.** From 2026-05-28: **L2 hard-required for formal reports** (`@type ∈ {agent_result, audit_record}` with `@status: complete`); **L4 hard-required for privileged workflows** (any tool action under §7.3 scope vocabulary). | bbe-coord welle-04 | 2026-05-13 → 2026-05-28+ |
| **E** | Cross-vendor: validator + signing CLI ported / wrapped for Codex, GPT, future. Operator decides wrapper-in-spawner (T-AM-002 area) vs. allowlist-downgrade (OPEN_ISSUES-RC2 #2). | bbe-coord welle-05+ | ongoing |

**Note:** Charter cross-reference, if pursued, is the charter committee's PR — not a STD-002 phase. RC2 does not modify Charter.

### §13.2 Welle-3 → STD-002 mechanical conversion

Welle-3 patterns are non-normative inputs to this design. They convert mechanically:

| Welle-3 pattern | RC1 conversion |
|---|---|
| `[RESULT-<TASK-NAME>]…[/RESULT-<TASK-NAME>]` | Label preserved. Add `@bbe-comm: 1.0`, `@type: agent_result`, `@id`, `@parent_id`, `@agent`, `@status`. |
| `[BLOCKER-<TOPIC>]…[/BLOCKER-<TOPIC>]` | Label preserved. `@type: agent_warning`, `@severity: warn`, `@status: open`. |
| `[QUESTION-<TOPIC>]…[/QUESTION-<TOPIC>]` | Label preserved. `@type: agent_query`, `@ask: <topic>`. |
| `[OPERATOR · <TASK> · <PHASE>]` | Label preserved (re-cased to `OPERATOR-<TASK>-<PHASE>`). `@type: operator_prompt`. |
| Free-form `status:` line in body | Move to `@status:` header. |
| Implicit "this is a response to X" by adjacency | Make explicit via `@parent_id`. |
| Mixed-case tag names (`[Result-…]`) | Re-case to `^[A-Z][A-Z0-9_-]*$`. Linter rejects mixed-case tags. |
| Authorization implied by emphatic body text (`"GO"`, `"yes proceed"`) | **REJECTED** — direct violation of §7.1 anti-inference rule. Operator MUST emit signed `operator_auth`. |

### §13.3 Compliance gate per repo

A repo is **STD-002-compliant** when:

1. `STANDARDS.md` cites BBE-STD-002 v1.0.
2. Agent-facing prompt files (`AGENTS.md`, `CLAUDE.md`) state R1–R7 (§7).
3. `tests/` includes a harness emitting an `agent_result` block at the end of CI runs at minimum **L2** (post 2026-05-28 hard-rollout) — machine-discoverable pass/fail signal.
4. Privileged operations in CI emit `operator_auth` blocks at **L4** (HMAC-anchored) within the active `@correlation_id`. L5 is desired but not v1.0-required.

Phase D rolls compliance per repo. During the 14-day warning window, non-compliant repos receive lint warnings only. After 2026-05-28, non-compliant repos do not block their own builds, but their agent operations on a BBE host with the AGUARD reference binding are subject to that runtime's stricter mode (`STATUS` instead of `GUIDED`). Deployments without a runtime binding rely on the lint warnings + operator review for enforcement.

---

## §14 Compliance mappings

- **ISO 27001 A.5.15** (Access Control): every privileged operation textually anchored in a verifiable `operator_auth`. Runtime bindings (e.g. AGUARD) provide the cryptographically anchored GO-token leg; conformant deployments without runtime binding rely on operator-attended action plus structural validation.
- **ISO 27001 A.8.15** (Logging): structured logs joinable by `@nonce` / `@correlation_id` / `cmd_hash`. The BBE reference binding produces `incoming.jsonl` + `issued.jsonl` + `audit.jsonl`; other deployments produce equivalent logs.
- **ISO 27001 A.8.32** (Change Management): repo-pivots become textually announced events (R3, agent rule). Runtime detection (e.g. AGUARD L3 hook) is supplementary.
- **ISO 42001** (AI Management System): the standard is the substantive technical control implementing the AI-system access-control requirement.
- **DSGVO Art. 30**: not applicable (no personal data processed by the protocol itself; operators MUST NOT include PII in block bodies or `@reason` fields).

---

## §15 Integration points (deferred specs)

| Spec | Consumes from STD-002 | Produces | Status |
|---|---|---|---|
| **POL-009** Authorization Decision | `operator_auth` blocks, principal identity | grant/deny verdicts | DEFERRED |
| **BBE-STD-003** Audit-Store | All L3+ blocks | persisted append-only log | DEFERRED |
| **ENG-001** Decision-Engine | All blocks, computed compliance level, lineage | runtime go/no-go for action | DEFERRED |

This standard publishes the **transport contract**. Each deferred spec is responsible for its own ratification cycle.

---

## §16 Tooling architecture (informative)

The reference implementations sit at three layers — author-side (universal), operator-side (universal), runtime-side (BBE-deployment-specific reference, see Annex A):

```
┌─────────────────────────────────────────────────────────────────┐
│  Author-side    (developer machine, CI, agent during emission)  │
│  Universal — runs anywhere Python runs                          │
│                                                                 │
│   bbe-comm CLI (Python package, 13+ subcommands)                │
│     ├── lint             (26 checks, exit 0/1/2)                │
│     ├── score            (compute L0..L5 per block)             │
│     ├── trace            (parent_id / correlation_id chains)    │
│     ├── explain          (human-readable check explanations)    │
│     ├── repair-suggest   (minimal-fix proposals)                │
│     ├── normalize        (Welle-3 / Welt-A → RC2 mechanical)    │
│     ├── emit             (template-based block generation)      │
│     ├── verify-hmac      (delegates to hmac.sh + op-secret)     │
│     ├── incident-test    (auth-inference detector, exit 4)      │
│     ├── auth-check       (prose-vs-block authorization audit)   │
│     ├── integrate-guard  (AGUARD-decision-envelope JSON)        │
│     ├── learn observe    (append learning event)                │
│     └── learn suggest    (synthesize process improvements)      │
│       │                                                         │
│       ├─→ schema/BBE-STD-002.schema.json (block schema)         │
│       ├─→ schemas/result.schema.json (CLI output contract)      │
│       └─→ schemas/learning-event.schema.json (event log shape)  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Operator-side  (terminal, when emitting OPERATOR-AUTH)         │
│  Universal — wherever bash + openssl + the op-secret live       │
│                                                                 │
│   bbe-block sign auth   (Bash, root-required for op-secret)     │
│   bbe-block sign deny                                           │
│   bbe-block verify                                              │
│   bbe-block template <type>                                     │
│   bbe-block rotate-secret                                       │
│       │                                                         │
│       └─→ shared lib hmac.sh (canonical body, HMAC-SHA256)      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Runtime-side   (BBE deployment — INFORMATIVE; see Annex A)     │
│  BBE-specific reference binding via AGUARD                      │
│                                                                 │
│   userprompt-hook.sh   (Bash, fast path, no Python)             │
│       │                                                         │
│       ├─→ extract OPERATOR-AUTH/DENY blocks (regex)             │
│       ├─→ HMAC verify (shared hmac.sh)                          │
│       ├─→ nonce replay check                                    │
│       ├─→ issue/revoke GO-token via go-token.sh                 │
│       └─→ audit to incoming.jsonl + audit.jsonl                 │
│                                                                 │
│   On parse anomaly: fall back to invoking bbe-comm lint         │
└─────────────────────────────────────────────────────────────────┘
```

**Why two languages?** The runtime hook is on a hot path (every operator prompt fires it); fork-exec to Python is wasteful and the existing Bash regex extractor is proven. The author-side `bbe-comm` benefits from Python's per-check named errors, structured output, modular rule organisation, and learning-loop machinery. The shared `hmac.sh` library means HMAC computation is byte-identical between operator-side signing and runtime-side verification.

**Why three layers separated?** Author-side and operator-side are universal (any conformant deployment runs them). Runtime-side is informative — alternative runtimes are conformant if they enforce §7 equivalently.

### §16.1 Self-optimization (informative)

The `bbe-comm learn` subcommands enable a closed feedback loop: every lint failure, every successful repair, every auth-inference attempt is appended as an event to `tools/bbe-comm/data/learning-events.jsonl`. Pattern detection (frequency thresholds) generates **review-only** suggestion files in `tools/bbe-comm/suggestions/`. The learning loop NEVER mutates the standard, the schema, the linter rules, or any policy. It only proposes; operators dispose. See `docs/adr/0001-self-optimization-learning-loop.md`.

**Redaction policy:** the event log never stores raw block bodies, raw operator prompts, `@hmac` values, `@nonce` values, or any auth-only field value. Content is reduced to SHA-256 hashes plus structured metadata (check IDs, type counts, block-level summary).

---

## §17 References to incident I-2026-05-09-01

The incident pattern was:

> Operator pasted a *detail-rich, well-structured prompt* for project A into a chat about project B. Agent treated the detail as authorization, pivoted repos, executed a service mutation, made commits.

BBE-STD-002 v1.0-RC2 closes this in **four** independent layers (three runtime-agnostic, one runtime-specific):

1. **Block-type discipline** (R1, R2 in §7.1, §7.2): only `operator_auth` authorizes. **Runtime-agnostic.**
2. **Anti-inference field discipline** (BBE-COMM-016, BBE-COMM-022 in §7.4): authorization-shaped field names outside `operator_auth` (and auth-only fields outside `operator_auth`/`operator_deny`) are rejected at format level. **Runtime-agnostic.**
3. **HMAC anchor** (§5, §7.2): textual content alone, no matter how detailed, cannot authorize without a deployment-derived HMAC. The HMAC anchor places the block at L4 (authorization-safe); L5 is reserved for external auditability (STD-003). **Runtime-agnostic** *as a format requirement*; runtime-specific in *who holds the key*.
4. **Repo-pivot rule R3** (§7.5): even with valid HMAC for prior target, target shifts force re-ask. **Runtime-agnostic as an agent rule** (4a); BBE deployments add runtime enforcement via the AGUARD PreToolUse hook (4b, see Annex A.4).

Adoption of this standard makes I-2026-05-09-01 a **schema violation** in any conformant deployment, and a machine-blocked event in deployments using a runtime binding equivalent to AGUARD.

### §17.1 Incident-replay regression test

The `tests/test_incident_replay.py` and the `tests/test_e2e_hmac.sh` step "incident-replay" feed the canonical incident pattern (a 2KB operator_prompt with detail, repeated `GO`, `please proceed`, `you are authorized`) through the parser, the linter, the `bbe-comm incident-test` subcommand, and the AGUARD reference hook. Expected results:

1. Zero `operator_auth` blocks parsed (because the prose has none).
2. `bbe-comm score` returns L0/L1 only — no block reaches L4 because nothing is structurally an `operator_auth`.
3. `bbe-comm auth-check` returns FAIL with exit code 4.
4. `bbe-comm incident-test` returns exit code 4 (`auth_inference_attempt`).
5. The AGUARD reference hook issues zero tokens and writes zero new entries to `incoming.jsonl`.

These are the **load-bearing tests** for the standard's incident-fix claim. They are run on every change to the linter or the runtime hook.

---

## Annex A: AGUARD reference binding (informative, BBE-deployment-specific)

This annex describes one possible runtime binding of BBE-STD-002 — the BBE deployment using AGUARD. **It is informative, not normative.** Conformance to BBE-STD-002 does not require AGUARD; it requires equivalent enforcement of §7's normative agent rules. Other runtimes are conformant if they:

- Reject `operator_auth` blocks whose `@hmac` does not verify against the deployment's authorization key (whatever that key is).
- Track nonce consumption to prevent replay.
- Detect repo-pivots (or equivalent target shifts) and require fresh authorization.
- Maintain an append-only audit log with `@nonce` / `@correlation_id` join keys.

The remainder of this annex is the BBE reference implementation.

---

### §A.1 Component layout

| Path | Owner | Purpose |
|---|---|---|
| `/var/lib/bbe-guard/op-secret` | root:root 0600 | 32-byte raw secret used as HMAC key |
| `/var/lib/bbe-guard/consumed-nonces/` | root:bbe-guard 0750 | One empty file per consumed `@nonce` (replay protection) |
| `/var/lib/bbe-guard/tokens/` | root:bbe-guard 0750 | One YAML file per active GO-token |
| `/var/log/bbe-blocks/incoming.jsonl` | root:bbe-guard 0640 | Every parsed block (valid or not) — append-only |
| `/var/log/bbe-blocks/issued.jsonl` | root:bbe-guard 0640 | Every block emitted by `bbe-block sign` — append-only |
| `/var/log/bbe-guard/audit.jsonl` | root:bbe-guard 0640 | AGUARD audit log — append-only |
| `/usr/local/sbin/bbe-block` | root:root 0750 | Operator CLI (root-required for op-secret access) |
| `/usr/local/bbe-guard/lib/userprompt-hook.sh` | root:root 0755 | UserPromptSubmit hook |
| `/usr/local/bbe-guard/lib/pretool-hook.sh` | root:root 0755 | PreToolUse hook (token consume) |

### §A.2 UserPromptSubmit hook flow

```
operator pastes block
       │
       ▼
Claude Code UserPromptSubmit hook (bash)
       │
       ├── extract [OPERATOR-AUTH] / [OPERATOR-DENY] blocks via regex
       │
       ├── for each block:
       │     ├── check required fields (§7.2)
       │     ├── check nonce not in consumed-nonces/ (replay)
       │     ├── recompute HMAC over canonical body (§5.1)
       │     ├── compare with @hmac (§5.2)
       │     │
       │     ├── on auth-valid: write GO-token to /var/lib/bbe-guard/tokens/<uuid>.yaml
       │     │     mark nonce consumed
       │     │     audit: incoming.jsonl + audit.jsonl
       │     │     emit additionalContext to agent: "[bbe-guard] OPERATOR-AUTH … ACCEPTED → token <uuid>"
       │     │
       │     └── on deny-valid: rm /var/lib/bbe-guard/tokens/* matching from-block:<id>
       │           mark nonce consumed
       │           audit
       │           emit additionalContext
```

### §A.3 PreToolUse hook flow

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

### §A.4 Repo-pivot detection

The PreToolUse hook also inspects:

- `git remote get-url origin` from the working tree at action-time
- The `@target` of the most recent `operator_auth` token
- The `@correlation_id` of the originating `operator_prompt`

If any of these shifts mid-session, the hook emits `[GUARD-DECISION decision:deny reason:repo-pivot-without-auth]` and refuses the tool call until a fresh `operator_auth` arrives.

### §A.5 Audit join keys

| Field | In `incoming.jsonl` | In `audit.jsonl` | In agent transcripts |
|---|---|---|---|
| `@id` | yes | yes (as `block-auth-id`) | yes (in additionalContext) |
| `@nonce` | yes | yes | no |
| `@correlation_id` | yes | yes | yes |
| `cmd_hash` | no | yes | yes (in `[GUARD-DECISION]`) |
| GO-token `uuid` | yes (`valid-token-issued` verdict) | yes (`block-auth-token-issued` action) | yes |

A complete audit trail for "what authorized X?" joins on `@nonce` (block→token issuance) and on `uuid` (token issuance→token consume).

### §A.6 Mode awareness

| AGUARD mode | UserPromptSubmit hook | PreToolUse hook |
|---|---|---|
| `OFF` | Hook not loaded | Hook not loaded |
| `STATUS` | Logs only; no token issuance | Logs only; allows everything |
| `GUIDED` | Issues tokens for valid `operator_auth`; rejects invalid | Allows w/ token; warns w/o token |
| `DEPLOY` | Same as GUIDED | Allows w/ token; **denies** w/o token |
| `BREAK-GLASS` | Issues tokens; logs everything | Allows everything; logs at audit-WARN |

The mode is a single-line file at `/var/lib/bbe-guard/mode`.

---

*— RC2 hardened under operator mandate `[OPERATOR · BBE-STD-002 · AUTONOMOUS-TOOLING-SELF-OPTIMIZATION]` 2026-05-09. Author: claude_integrator_21@claude-opus-4-7@v2202.bbe.internal. Builds on RC1 (consolidation of Welt A + Welt B) by applying 8 operator decisions (see RC2-DELTA.md): canonical repo home, L5/HMAC separation, runtime-agnostic posture, 14-day rollout cadence, multi-scope AND-default + `@scope_mode: any`, incident-replay regression test, evidence-gap documentation, charter scope-out. Server-side policy priority observed throughout: no live actions, no policy mutations, no implicit approvals, no root, no push.*
