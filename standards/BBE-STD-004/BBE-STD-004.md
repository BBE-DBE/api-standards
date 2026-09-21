# BBE-STD-004 — Model Provider Portability

| Field | Value |
|---|---|
| Standard ID | BBE-STD-004 |
| Title | Model Provider Portability |
| Version | **0.1.0** |
| Status | DRAFT |
| Effective | — (draft; no service is bound until RATIFIED) |
| Owner | `api-standards/standards/BBE-STD-004/` |
| Pairs with | `protocols/model-provider-adapter.md` (cross-service contract pointer) · `schema/*.schema.json` · `tools/bbe-port/` (reference CLI) · `examples/` (golden corpus) |
| Cross-refs | `protocols/provider-adapter-interface.md` (parent pattern) · `protocols/error-codes.yaml` · `protocols/secrets-vault.md` · `PRINCIPLES.md` §6, §8 · `checklists/14-dimensions.md` §5 |
| ID note | `BBE-STD-003` is reserved for Audit-Store & Message Persistence (see `STANDARDS.md`). This standard takes the next free ID. |

---

## §1 Purpose

BBE-STD-004 answers one operational question:

> **If our current model provider disappears, is degraded, changes price, or
> becomes legally unusable — how long until we are running again, and how do
> we know the replacement is good enough?**

The answer must be a *measured number*, not a belief. This standard defines
the two mechanisms that produce that number:

1. **A model-provider adapter contract** (§4) so that switching providers is
   a configuration change, not a code change.
2. **A portability gate** (§5–§7) — a golden task corpus plus a scoring run
   that produces a machine-readable verdict on whether a candidate provider
   qualifies as a fallback.

Mechanism 1 without mechanism 2 is unverified. An abstraction layer nobody has
ever switched is a hypothesis, not insurance.

### §1.1 What this standard explicitly does NOT claim

- It does not make BBE independent of *model vendors*. It makes BBE
  independent of any **single** vendor.
- Running open weights on own hardware is one deployment option (§4.3), not a
  goal in itself. The standard is indifferent to where inference happens as
  long as the contract and the gate hold.
- It does not define prompt engineering, agent architecture, or evaluation
  science. The corpus is a **regression** instrument, not a benchmark.

---

## §2 Scope

### §2.1 In scope

- The `ModelProviderAdapter` surface every BBE service MUST use to reach an
  LLM (§4).
- The **provider manifest**: a machine-readable capability descriptor per
  provider/model pair (§4.2, `schema/model-provider-manifest.schema.json`).
- The **swap check**: mechanical comparison of incumbent vs. candidate that
  names exactly which capabilities are lost (§6).
- The **golden corpus** format and the scoring/verdict rules (§5, §7).
- A reference implementation (`tools/bbe-port/`) and a CI gate
  (`scripts/test-std-004.sh`) that run **offline, without credentials**.

### §2.2 Out of scope

- Choosing a specific vendor. The registry in §8 is descriptive.
- Model hosting, GPU procurement, quantization. Out of band.
- Streaming transport framing (SSE vs. chunked) — adapter-internal.
- Training or fine-tuning of any model.

---

## §3 Conformance levels

| Level | Name | Requirement |
|---|---|---|
| **P0** | Coupled | Provider SDK called directly from service code. **Non-conformant.** |
| **P1** | Abstracted | All LLM calls go through a `ModelProviderAdapter` (§4). No vendor types above the adapter. |
| **P2** | Declared | P1 + a valid provider manifest per configured model (§4.2), secrets by reference only. |
| **P3** | Measured | P2 + a golden corpus of ≥ 20 tasks and a stored portability report for the primary provider (§7). |
| **P4** | Proven | P3 + at least one **non-primary** provider with verdict `QUALIFIED` or `QUALIFIED_DEGRADED`, re-measured at most 90 days ago. |

A service claiming "provider independent" in its `STANDARDS.md` MUST state its
level. Claiming a level without the stored report is a compliance bug, not a
style preference (mirrors `PRINCIPLES.md` §8 enforcement posture).

**Target for BBE-DBE services that embed an AI system: P4.**

---

## §4 The adapter contract

### §4.1 Relationship to `protocols/provider-adapter-interface.md`

The existing provider-adapter interface governs **infrastructure** providers
(Netcup, Hetzner) and is CRUD-shaped (`list/get/create/update/delete`). Model
providers are not CRUD-shaped, so this standard defines a sibling surface —
but it **inherits the cross-cutting obligations verbatim** and does not
restate them: retries and backoff, rate-limit awareness, no vendor types above
the adapter, logging redaction, error mapping to `protocols/error-codes.yaml`,
and append-only audit of every outbound call.

Anything §4 does not mention follows the parent document.

### §4.2 Surface (normative)

```ts
export interface ModelProviderAdapter {
  /** Stable id, MUST equal the manifest `id`: "<vendor>/<model>". */
  readonly id: string;

  /** Parsed provider manifest — see model-provider-manifest.schema.json. */
  readonly manifest: ProviderManifest;

  /** Probe credentials + reachability. Same contract as the parent
   *  interface's init(): never throws on a reachable-but-unauthorized
   *  provider, returns ok:false instead. */
  init(): Promise<{ ok: boolean; latency_ms: number; details?: string }>;

  /** Single completion. MUST reject with `not_supported_by_provider`
   *  when `req` uses a capability the manifest declares false. */
  complete(req: ModelRequest, ctx: CallContext): Promise<ModelResponse>;

  /** Token-by-token. OPTIONAL — omit when manifest.capabilities.streaming
   *  is false. */
  stream?(req: ModelRequest, ctx: CallContext): AsyncIterable<ModelChunk>;

  /** Vendor-error → BBE error-code mapping. Pure function. */
  mapError(vendorErr: unknown): { code: string; status: number; message: string };

  /** Per-call audit hook. MUST fire for every attempt, success or failure. */
  onCall(event: ModelCallEvent): void;
}

export interface ModelRequest {
  system?:      string;
  messages:     ReadonlyArray<{ role: 'user'|'assistant'; content: string }>;
  tools?:       ReadonlyArray<ToolDef>;   // requires capabilities.tools
  json_schema?: unknown;                  // requires capabilities.json_mode
  max_output_tokens?: number;
  temperature?: number;
  /** Task id from the golden corpus when this call is part of a gate run. */
  eval_task_id?: string;
}

export interface ModelResponse {
  text:        string;
  tool_calls?: ReadonlyArray<{ name: string; arguments: unknown }>;
  stop_reason: 'end'|'max_tokens'|'tool_use'|'filtered';
  usage:       { input_tokens: number; output_tokens: number };
  /** Which adapter actually served this — set by the router on fallback. */
  served_by:   string;
}

export interface ModelCallEvent {
  adapter_id:    string;
  request_id:    string;
  attempt:       number;
  outcome:       'ok'|'retried'|'failed'|'rate_limited'|'fell_back';
  latency_ms:    number;
  input_tokens:  number;
  output_tokens: number;
  cost_micro_eur?: number;
  error_code?:   string;
  /** sha256 of the canonical request. Never the prompt itself. */
  request_hash:  string;
}
```

`CallContext` is the one from `protocols/provider-adapter-interface.md`,
unchanged.

### §4.3 Deployment neutrality

`manifest.deployment` is one of `saas`, `self_hosted`, `on_prem`. The adapter
surface is identical for all three. A self-hosted open-weights model behind an
OpenAI-compatible endpoint is an ordinary adapter, not a special case. This is
what makes "we can move inference in-house" a configuration decision rather
than a rewrite.

### §4.4 Secrets

A manifest MUST NOT contain credential material. `credential_ref` MUST be
either `vault://<path>` (see `protocols/secrets-vault.md`) or `env:<VAR_NAME>`.
The reference linter fails closed on anything resembling an inline key
(`BBE-PORT-004`) — this is a §1-tier concern under `PRINCIPLES.md` conflict
order and outranks convenience.

---

## §5 The golden corpus

A corpus is a directory of task files (`schema/eval-task.schema.json`). A task
is a **deterministic, machine-checkable** unit of real work:

```json
{
  "task_version": "1",
  "id": "extract-invoice-total",
  "category": "extraction",
  "weight": 2,
  "requires": ["json_mode"],
  "system": "You extract structured data. Answer with JSON only.",
  "prompt": "Rechnung ...",
  "checks": [
    { "type": "json_has_keys", "keys": ["total_eur", "invoice_no"] },
    { "type": "contains_all",  "values": ["1190.00"] },
    { "type": "not_contains",  "values": ["I cannot"] }
  ]
}
```

Rules:

1. **Tasks come from production.** A corpus of puzzle questions measures
   nothing about your business. Tasks SHOULD be derived from real traffic with
   PII removed.
2. **Checks are mechanical.** No "model-as-judge" in the gate. If a capability
   cannot be checked mechanically, it does not belong in the gate; it belongs
   in a human review that is not on the blocking path.
3. **`requires` is load-bearing.** It names manifest capability flags the task
   depends on. A provider lacking one gets the task scored `blocked`, never
   `failed` — a missing capability is a *known* limitation, not a quality
   signal (§7.2).
4. **Minimum size for P3 is 20 tasks.** Below that the score is noise.
5. **Corpus changes are versioned.** A report is only comparable to another
   report over the same `corpus_hash` (§7.3).

Check types (v0.1.0): `contains_all`, `contains_any`, `not_contains`,
`regex`, `json_has_keys`, `equals_normalized`.

---

## §6 The swap check

`bbe-port swap --from <manifest> --to <manifest> [--corpus <dir>]` compares
two manifests and emits:

- **capability_lost** — flags true on incumbent, false on candidate.
- **capability_gained** — informational.
- **context_delta** — candidate context window minus incumbent's.
- **corpus_impact** — when `--corpus` is given: how many tasks (and how much
  weight) would become `blocked` on the candidate.

Verdict:

| Verdict | Condition |
|---|---|
| `compatible` | no capability lost, context not reduced below corpus need |
| `degraded` | capabilities lost, but no corpus task depends on them |
| `incompatible` | a corpus task's `requires` flag is lost, or context window falls below the largest corpus task |

`incompatible` means the swap breaks known work. It is a blocking finding.

---

## §7 Scoring and verdict

### §7.1 Score

For each non-blocked task: all checks pass → task passes. Score is
weight-weighted:

```
score = Σ weight(passed tasks) / Σ weight(non-blocked tasks)
```

Blocked tasks are excluded from the denominator and reported separately. A
provider cannot improve its score by being incapable.

### §7.2 Verdict

| Verdict | Condition | Exit code |
|---|---|---|
| `QUALIFIED` | `score >= floor` AND `blocked_weight == 0` | 0 |
| `QUALIFIED_DEGRADED` | `score >= floor` AND `blocked_weight > 0` | 0 |
| `NOT_QUALIFIED` | `score < floor` | 1 |

Default floor is `0.80` and is set per corpus in `policy.json`. The floor is a
**business** decision (what quality loss is survivable for a week), not a
technical one, and MUST be signed off by the operator.

### §7.3 Report

Reports conform to `schema/portability-report.schema.json` and carry
`corpus_hash` (sha256 over sorted task ids + their canonical bodies). Two
reports are comparable only at equal `corpus_hash`. Stale reports (> 90 days)
do not satisfy P4.

Reports MUST NOT contain model output verbatim beyond a 200-character excerpt
per failed task — full transcripts go to the service's audit store
(BBE-STD-003 when ratified), not into a repo artifact.

---

## §8 Recovery-time objective

A service at P4 MUST document, in its own `STANDARDS.md`, two numbers:

- **RTO-model** — wall-clock minutes from "primary provider unusable" to
  "fallback serving production traffic". At P4 this is a config change plus a
  deploy, so the honest number is usually minutes, not weeks.
- **QLO** — quality-loss objective: the measured `score` of the qualified
  fallback. This is the number to put in front of a customer, not a promise
  of parity.

Independence claimed without these two numbers is marketing.

---

## §9 Reference implementation

`tools/bbe-port/` — Python 3.11+, standard library only (no `jsonschema`
dependency; the repo CI environment has none). Subcommands:

| Command | Purpose |
|---|---|
| `bbe-port validate <manifest…>` | manifest lint (BBE-PORT-001…008) |
| `bbe-port swap --from A --to B [--corpus D]` | §6 |
| `bbe-port eval --manifest M --corpus D [--transport …]` | §5/§7 run |
| `bbe-port report <report.json>` | re-print verdict, exit per §7.2 |

Transports are pluggable. `mock` replays a fixture file and is what the CI
gate uses, so the gate is deterministic and needs no credentials or network.
`openai_chat` is the live transport for any OpenAI-compatible endpoint
(including self-hosted vLLM/llama.cpp servers).

CI gate: `scripts/test-std-004.sh` (mirrors `scripts/test-std-002.sh`).

---

## §10 Open issues (DRAFT)

| # | Issue | Disposition |
|---|---|---|
| D1 | Streaming is in the surface but not exercised by the gate | v0.2 — needs a deterministic chunk-level check type |
| D2 | Cost is recorded per call but not part of the verdict | intentional: cost is an operator decision, not a gate |
| D3 | `model-as-judge` check type for non-mechanical tasks | rejected for the blocking path (§5.2); revisit as advisory-only |
| D4 | Binding to the audit store | blocked on BBE-STD-003 |
| D5 | Live-transport conformance suite (real vendor endpoints) | out of CI; operator-run, credentials required |

Ratification requires: D1 closed or explicitly deferred, one service at P3 with
a stored report, and an operator mandate per the STD-002 precedent.
