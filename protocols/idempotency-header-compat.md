# Idempotency Header Compatibility

**Status:** Required for every BBE-DBE service that exposes mutation routes.
**Anchor:** 14-dimensions.md §13 ("Idempotency akzeptiert beide Header").

## Rule

Every mutation endpoint (POST / PUT / PATCH / DELETE that changes state)
MUST accept the idempotency key under **both** of the following request
headers:

- `Idempotency-Key`     (canonical, IETF draft `draft-ietf-httpapi-idempotency-key-header`)
- `X-Idempotency-Key`   (legacy / vendor-prefixed, still common in client SDKs)

The two header names are **aliases** — they MUST resolve to the same
internal value with identical semantics.

## Resolution order

1. If both headers are present and have **the same value** → accept.
2. If both headers are present and values **differ** → reject with
   HTTP 400, error code `idempotency_header_conflict`, message
   "Idempotency-Key and X-Idempotency-Key both present with different
   values". This is a client bug; do not silently pick one.
3. If exactly one is present → use that value.
4. If neither is present and the route requires idempotency → reject
   with HTTP 400, error code `missing_idempotency_key` (already in
   `protocols/error-codes.yaml`).

## Validation

- Length: 8–128 characters.
- Charset: `[A-Za-z0-9_\-:.]` (ASCII printable, no whitespace).
- TTL: implementation-defined, exposed via `/service-manifest →
  idempotency.ttl_seconds`. Default 24 h.

## Storage

Existing pattern from `BBE-DBE/ip-pool-api/src/lib/idempotency.ts`
applies unchanged. The two header names share **one** persistence row
keyed by the resolved value.

## Replay rules (unchanged)

- Same key + same body hash → return the cached response (status +
  body) verbatim.
- Same key + different body hash → 422 with code
  `idempotency_mismatch`.

## Echo-back

The response SHOULD echo the resolved key under the canonical header
`Idempotency-Key` (not the vendor-prefixed alias) so log scrapers and
tracing tools see one canonical name.

## Migration note

Services that previously accepted only `Idempotency-Key`: this is an
**additive** change. Adding `X-Idempotency-Key` does not break existing
clients. No major-version bump required.

## Test obligations

- Integration test: send mutation with `Idempotency-Key` only → 2xx.
- Integration test: send mutation with `X-Idempotency-Key` only → 2xx.
- Integration test: send both with same value → 2xx.
- Integration test: send both with different values → 400
  `idempotency_header_conflict`.

These four tests are minimum bar. Add to
`tests/integration/idempotency.spec.ts`.
