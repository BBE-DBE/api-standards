# Service Self-Registration Protocol

**Status:** Required for every network-bound BBE-DBE service.
**Anchor principle:** PRINCIPLES.md §9 ("Self-Registration").
**Discovery target:** `port-registry` (see `SERVICES.yaml`, port 5099).

## Why

Without runtime registration, agents cannot answer the question "what
services are alive right now and what can they do?" without scanning
disk. PRINCIPLES.md §8 (Reuse-First) requires `SERVICES.yaml` for
**design-time** lookup; this protocol delivers the **runtime** half.

## Contract (no implementation provided here, only the rules)

### When

1. Service starts up and finishes its own internal readiness checks
   (DB connection healthy, migrations at expected SHA, etc.).
2. Before accepting external traffic on the public port.

### What it sends

`POST {PORT_REGISTRY_URL}/v1/services/register` with body:

```json
{
  "name":          "<service short-name from SERVICES.yaml>",
  "version":       "<semver from package.json>",
  "repo":          "BBE-DBE/<repo>",
  "role":          "service",
  "port":          <integer>,
  "base_url":      "http://<host>:<port>",
  "health_url":    "http://<host>:<port>/health",
  "openapi_url":   "http://<host>:<port>/openapi.json",
  "manifest_url":  "http://<host>:<port>/service-manifest",
  "auth_required": true,
  "status":        "active",
  "capabilities":  ["…"],
  "dependencies":  [{ "name": "…", "version": ">=…", "status": "required|optional" }],
  "metadata":      { },
  "ttl_seconds":   60
}
```

Headers:
- `Authorization: Bearer <port-registry-token>` (scope `services:write`,
  stored in service's `.env` as `PORT_REGISTRY_TOKEN`).
- `Idempotency-Key: <uuid-v7>` (so a registration retry is safe). Both
  `Idempotency-Key` and `X-Idempotency-Key` are accepted as aliases per
  [`idempotency-header-compat.md`](idempotency-header-compat.md).

Response: `201 Created` on first registration, `200 OK` on
re-registration of the same `name` (UPSERT semantics).

### Heartbeat

`POST {PORT_REGISTRY_URL}/v1/services/heartbeat` every
`ttl_seconds / 3` (default: 20 s) with body:

```json
{ "name": "<service-name>", "status": "active",
  "health": { /* arbitrary */ }, "metadata": { } }
```

The registry treats a missed heartbeat after `ttl_seconds` as
liveness expiry — `is_live` flips to `false` in `/v1/services` /
`/v1/capabilities` responses, but the row itself stays so historical
audit + capability data remains queryable.

### Graceful shutdown

`POST {PORT_REGISTRY_URL}/v1/services/deregister` on SIGTERM, before
draining, with body `{ "name": "<service-name>" }`. The registry
tombstones the service to `status='retired'` (no DELETE — capability
history stays). Best-effort — registry tolerates missing deregistration
via the heartbeat-TTL fallback.

### Failure mode

If `port-registry` is unreachable at boot:
- Service MUST log `level=warn event=port_registry_unreachable` with
  the URL it tried.
- Service MUST start anyway (registry is not on the critical path for
  user-facing requests, only for discovery).
- Service MUST retry registration on a 30 s exponential backoff up to
  10 attempts, then a 5-minute steady-state retry loop.

This guarantees: a brand-new service does not become unreachable just
because the registry is being restarted.

## What this protocol does NOT mandate

- A specific HTTP client library.
- Where the `PORT_REGISTRY_URL` lives in config — only that it is
  read from `.env` (see `protocols/secrets-vault.md`).
- The shape of `port-registry`'s own response (defined in its own
  `openapi.yaml`).

## Reference

- Catalog entry: `SERVICES.yaml` → `port-registry`.
- Manifest definition: `protocols/service-manifest.md`.
