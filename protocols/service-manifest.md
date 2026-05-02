# Service Manifest Endpoint

**Status:** Required for every network-bound BBE-DBE service.
**Anchor principle:** PRINCIPLES.md §9 + 14-dimensions.md §13.
**Path:** `GET /service-manifest`
**Auth:** none (public, like `/health`).
**Content-Type:** `application/json; charset=utf-8`

## Why

`SERVICES.yaml` is the **static** catalog. `/service-manifest` is the
**live, self-described** counterpart: when an agent talks to a service
it has never seen before, this endpoint tells it everything it needs to
decide "can this service do what I want, and how do I call it?"

The endpoint is the **machine-readable** contract that fulfils
PRINCIPLES.md §1 (Agent-First) and §8 (Reuse-First).

## Response Schema

```json
{
  "name":         "ip-pool-api",
  "version":      "0.3.0",
  "build_version":"a1b2c3d",
  "started_at":   "2026-05-02T14:23:01Z",
  "openapi_url":  "/openapi.json",
  "openapi_path": "/openapi.yaml",
  "capabilities": [
    "ip-reservation",
    "ip-release",
    "ip-import",
    "pool-listing"
  ],
  "dependencies": [
    {
      "name":     "infra-postgres",
      "version":  ">=0.1.3",
      "status":   "required",
      "verified": true
    },
    {
      "name":     "port-registry",
      "version":  ">=0.1.0",
      "status":   "optional",
      "verified": true
    }
  ],
  "auth": {
    "scheme": "bearer-prefixed",
    "prefix": "ipa"
  },
  "idempotency": {
    "headers_accepted": ["Idempotency-Key", "X-Idempotency-Key"],
    "ttl_seconds":      86400
  },
  "health": {
    "live":   "/health/live",
    "ready":  "/health/ready",
    "full":   "/health"
  },
  "metrics_url": "/metrics",
  "compliance": {
    "api_standards_version":  "2026.04.30",
    "iso27001_mapping":       "compliance/iso-27001-mapping.md",
    "principles_pinned":      ["1","2","3","4","5","6","7","8","9"]
  },
  "links": {
    "repo":          "https://github.com/BBE-DBE/ip-pool-api",
    "principles":    "https://github.com/BBE-DBE/ip-pool-api/blob/main/PRINCIPLES.md",
    "changelog":     "https://github.com/BBE-DBE/ip-pool-api/blob/main/CHANGELOG.md"
  }
}
```

## Field rules

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | MUST equal entry key in `SERVICES.yaml`. |
| `version` | semver | yes | From `package.json`. |
| `build_version` | string | yes | Git short SHA at build time. |
| `started_at` | ISO-8601 UTC | yes | Process start. |
| `openapi_url` | path | yes | Live JSON variant of OpenAPI. |
| `openapi_path` | path | yes | Static YAML variant. |
| `capabilities` | string[] | yes | MUST be a superset of `SERVICES.yaml`'s `capabilities` for this service. |
| `dependencies` | object[] | yes | Each item: `name`, `version` (semver range), `status` (`required`\|`optional`), `verified` (bool — was a probe successful at startup?). |
| `auth.scheme` | string | yes | One of: `none`, `bearer-prefixed`, `bbe-internal`. |
| `auth.prefix` | string | iff scheme=`bearer-prefixed` | 2–4 chars from `templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md`. |
| `idempotency.headers_accepted` | string[] | yes if any mutation routes exist | MUST list both `Idempotency-Key` AND `X-Idempotency-Key`. |
| `idempotency.ttl_seconds` | integer | yes if mutations | TTL of the idempotency cache. |
| `health.{live,ready,full}` | path | yes | Three-way split per 14-dim §8. |
| `metrics_url` | path | yes | Prometheus exposition. |
| `compliance.api_standards_version` | string | yes | Pin against the `api-standards` CHANGELOG date-tag. |
| `compliance.principles_pinned` | string[] | yes | Which PRINCIPLES.md inherited principles this service claims to honour. |
| `links` | object | yes | repo / principles / changelog at minimum. |

## Cache headers

- `Cache-Control: public, max-age=10`
- `ETag: <strong etag computed from content>`

A polling discovery service (e.g., port-registry) SHOULD revalidate via
`If-None-Match` rather than re-fetching every time.

## Error response

If the service cannot answer (e.g., DB-outage so dependencies cannot be
verified), still return 200 with `dependencies[].verified=false` and
include a `degraded: true` field at the root. Never 5xx the manifest —
that breaks discovery.

## Why not just OpenAPI?

OpenAPI describes the **endpoint shape** (what JSON goes in and out).
The manifest describes the **service identity and posture** (what
principles, what compliance, what dependencies, what auth-scheme). Both
are needed; both are referenced from `SERVICES.yaml`.
