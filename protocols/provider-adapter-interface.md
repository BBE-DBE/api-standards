# Provider-Adapter Interface

**Status:** Required for every service that fronts an external provider.
**Anchor:** PRINCIPLES.md §6 ("Reusable contracts") + 14-dim §5
("Provider-Adapter über Interface, austauschbar").
**Initial consumers:** `netcup-api`, `hetzner-api`.
**Forward consumers:** any future provider (Cloudflare, AWS, Vercel, …).

## Why one shared interface

`netcup-api` and `hetzner-api` both wrap a third-party HTTP API. They
have nearly identical concerns: token-based auth, rate-limit handling,
retries with backoff, mapping vendor errors to BBE error codes, audit
logging of every outbound call. Without a shared contract every new
provider re-invents the same plumbing differently. With this interface
they share one tested core and only the **vendor-specific** parts
diverge.

This document defines the **interface only** (no implementation). Each
service is free to implement it in TypeScript however it wants, as long
as the surface and the externally-observable behaviour match.

## Surface (TypeScript shape, normative)

```ts
export interface ProviderAdapter<TConfig, TResource> {
  /** Stable adapter id, equal to `SERVICES.yaml` short-name. */
  readonly id: string;

  /** SemVer of the adapter implementation. */
  readonly version: string;

  /** Provider-side base URL (may be multiple — see hetzner dual-base). */
  readonly bases: ReadonlyArray<{ name: string; url: string }>;

  /** Bound from .env at boot, never logged. */
  readonly config: TConfig;

  /** One-time at boot: probe credentials and connectivity. */
  init(): Promise<{ ok: boolean; latency_ms: number; details?: string }>;

  /** Provider-resource CRUD. Each method is OPTIONAL — implement the
   *  subset the provider actually supports. Missing methods MUST
   *  throw `not_supported_by_provider` (see error-codes.yaml). */
  list?  (filter?: Record<string, unknown>): Promise<TResource[]>;
  get?   (id: string): Promise<TResource>;
  create?(input: Partial<TResource>, ctx: CallContext): Promise<TResource>;
  update?(id: string, patch: Partial<TResource>, ctx: CallContext): Promise<TResource>;
  delete?(id: string, ctx: CallContext): Promise<void>;

  /** Vendor-error → BBE error-code mapping. Pure function. */
  mapError(vendorErr: unknown): { code: string; status: number; message: string };

  /** Per-call audit hook. MUST be called for every successful or
   *  failed outbound HTTP request. */
  onCall(event: ProviderCallEvent): void;
}

export interface CallContext {
  request_id:       string;     // X-Request-Id, propagated cross-service
  actor_id:         string;     // who is calling (key_id from auth)
  idempotency_key?: string;     // resolved per protocols/idempotency-header-compat.md
  run_id?:          string;     // for long-running batches
}

export interface ProviderCallEvent {
  adapter_id:    string;
  method:        'GET'|'POST'|'PUT'|'PATCH'|'DELETE';
  base:          string;          // which adapter base was used
  path:          string;
  status_code:   number;
  latency_ms:    number;
  request_id:    string;
  attempt:       number;          // 1 = first try, >1 = retry
  outcome:       'ok'|'retried'|'failed'|'rate_limited';
  error_code?:   string;
  request_hash:  string;          // sha256 of canonical request body
}
```

## Mandatory cross-cutting behaviours

These are NOT in the interface signature — they are obligations every
implementation MUST honour.

1. **Retries.** Idempotent methods (GET, PUT, DELETE, plus POSTs that
   carry `idempotency_key`) MUST retry on 429 / 502 / 503 / 504 / network
   errors with exponential backoff (250 ms base, ×2, max 4 attempts).
2. **Rate-limit awareness.** Honour vendor `Retry-After` headers when
   present; fall back to exponential backoff when absent.
3. **No vendor-specific types in service code.** The service layer
   above the adapter MUST only see `TResource` shaped to the BBE
   contract. Vendor JSON stays inside the adapter.
4. **Logging redaction.** `Authorization`, vendor API tokens, and any
   field listed in `protocols/secrets-vault.md` MUST be redacted before
   reaching `onCall` or the structured logger.
5. **Error mapping.** Every vendor error MUST map to a code listed in
   `protocols/error-codes.yaml`. New codes require a PR to that file.
6. **Audit trail.** `onCall` MUST persist into the service's
   `<schema>.audit_provider_calls` table (append-only, see
   `iso-mappings/27001-controls.md`). No in-memory-only audit allowed.

## Multi-base support (hetzner pattern)

Some providers expose related products under different hostnames
(Hetzner: `api.hetzner.cloud` for cloud servers, `api.hetzner.com` for
storage boxes). The `bases` array models this: the resource layer picks
which base to use per resource, the adapter does NOT pick implicitly.

Anti-pattern: a single `base_url` config that requires per-call switch
logic scattered through the codebase.

## What this interface does NOT cover

- HTTP client choice (undici, fetch, axios — service-internal).
- Connection pooling (delegated to `protocols/undici-pool.md` once that
  ADR lands as a protocol).
- Token rotation strategy (`protocols/secrets-vault.md`).

## Evolution

Additions are non-breaking and bump the patch version.
Method removals require a major bump and a migration path for current
consumers (`netcup-api`, `hetzner-api`).
