# Model-Provider Adapter

**Status:** Required for every service that calls an LLM.
**Anchor:** PRINCIPLES.md §6 ("Reusable contracts") + §8 (Reuse-First) +
14-dim §5 ("Provider-Adapter über Interface, austauschbar").
**Normative home:** [`standards/BBE-STD-004/`](../standards/BBE-STD-004/BBE-STD-004.md) — this
page is the cross-service pointer; the standard carries the detail.
**Sibling:** [`provider-adapter-interface.md`](provider-adapter-interface.md)
(infrastructure providers: Netcup, Hetzner, …).

## The problem this exists for

A service that imports a vendor SDK and calls it from business logic has made
that vendor a hard dependency of the product. When the vendor goes away,
changes price, deprecates a model, or becomes legally unusable, the cost of
moving is a rewrite — and nobody knows in advance whether the replacement is
good enough, because nothing has ever been measured.

The expensive part of that dependency is never the model. Models are
substitutable; five vendors sell one. What is not substitutable is the layer
above: prompts, agent loops, tool definitions, and the evaluation set that
says whether a swap is safe. BBE-STD-004 exists to keep that layer
provider-shaped instead of vendor-shaped.

## What a service must do

1. **Route every LLM call through a `ModelProviderAdapter`** (BBE-STD-004 §4.2).
   No vendor SDK types above the adapter boundary — same rule as the
   infrastructure adapter interface.
2. **Ship a provider manifest per configured model** — JSON, validated against
   `standards/BBE-STD-004/schema/model-provider-manifest.schema.json`.
   Manifests carry references to credentials (`vault://…` or `env:VAR`), never
   credentials. The linter fails closed on anything that looks like a key.
3. **Keep a golden corpus** of real tasks with mechanical checks, and store a
   portability report for the primary provider.
4. **Qualify at least one non-primary provider** and re-measure at most every
   90 days (conformance level P4).
5. **Publish two numbers** in the service's own `STANDARDS.md`: RTO-model
   (minutes to switch) and QLO (the measured score of the qualified fallback).
   Independence without those two numbers is a claim, not a control.

## Inherited obligations

Everything in `provider-adapter-interface.md` under "Mandatory cross-cutting
behaviours" applies unchanged: retries with backoff, rate-limit awareness, no
vendor types above the adapter, logging redaction, error mapping to
[`error-codes.yaml`](error-codes.yaml), and append-only audit of every
outbound call. BBE-STD-004 does not restate them, and a model adapter that
skips them is non-conformant to both documents.

## Error codes

Model-specific codes live in [`error-codes.yaml`](error-codes.yaml):
`not_supported_by_provider`, `context_length_exceeded`, `model_unavailable`,
`provider_rate_limited`, `content_filtered`. A vendor error that maps to none
of them maps to `internal` and gets a PR to the registry.

## Running the gate

```sh
# lint manifests + corpus
standards/BBE-STD-004/tools/bbe-port/bbe-port validate path/to/*.json
standards/BBE-STD-004/tools/bbe-port/bbe-port corpus path/to/corpus/

# what breaks if we switch?
standards/BBE-STD-004/tools/bbe-port/bbe-port swap \
  --from manifests/primary.json --to manifests/fallback.json --corpus corpus/

# measure the fallback (live endpoint)
standards/BBE-STD-004/tools/bbe-port/bbe-port eval \
  --manifest manifests/fallback.json --corpus corpus/ \
  --transport openai_chat --policy policy.json --out reports/fallback.json
```

Exit codes: `0` pass, `1` gate failure, `2` the measurement did not happen
(usage or transport error — never scored as a quality result).

CI gate for the standard itself: `scripts/test-std-004.sh` (offline, no
credentials).

## What this protocol does NOT do

- It does not pick a vendor, and it does not prefer self-hosting. Where
  inference runs is a cost, latency and jurisdiction decision; the contract is
  identical for `saas`, `self_hosted` and `on_prem`.
- It does not evaluate model quality in general. The corpus is a **regression**
  instrument over your own work, not a benchmark.
- It does not cover prompt or agent-loop portability beyond the call surface.
  That gap is real and currently carried by each service.
