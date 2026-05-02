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

`POST {PORT_REGISTRY_URL}/v1/register` with body:

```json
{
  "name": "<service short-name from SERVICES.yaml>",
  "version": "<semver from package.json>",
  "host": "<hostname or routable IP>",
  "port": <integer>,
  "manifest_url": "http://<host>:<port>/service-manifest",
  "openapi_url":  "http://<host>:<port>/openapi.json",
  "build_version": "<git short SHA>",
  "started_at":    "<ISO-8601 UTC>",
  "process_id":    <int>,
  "registration_ttl_seconds": 60
}
```

Headers:
- `Authorization: Bearer <port-registry-token>` (issued by port-registry,
  stored in service's `.env` as `PORT_REGISTRY_TOKEN`).
- `Idempotency-Key: <uuid-v7>` (so a registration retry is safe).

### Heartbeat

`POST {PORT_REGISTRY_URL}/v1/heartbeat/{run_id}` every
`registration_ttl_seconds / 3` (default: 20 s).
Body: `{}`. The registry treats a missed heartbeat after
`registration_ttl_seconds` as deregistration.

### Graceful shutdown

`POST {PORT_REGISTRY_URL}/v1/deregister/{run_id}` on SIGTERM, before
draining. Best-effort — registry tolerates missing deregistration via
the heartbeat-TTL fallback.

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
