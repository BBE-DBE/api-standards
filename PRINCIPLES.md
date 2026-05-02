# Principles — api-standards (root)

This file is the entry point for **agents and humans** that need the
ecosystem-wide architectural principles. Service-specific principles
live in each service's own `PRINCIPLES.md`; the inherited ones are
listed in
[`templates/service-skeleton/PRINCIPLES.md`](templates/service-skeleton/PRINCIPLES.md).

## Inherited (every BBE-DBE service ships with these)

1. **Agent-First.** Every endpoint headless. Idempotency-Key on every
   mutation. Stable, machine-readable error codes
   ([`protocols/error-codes.yaml`](protocols/error-codes.yaml)).
2. **API-First.** OpenAPI 3.1 generated from zod schemas — single source
   of truth.
3. **Headless.** No UI in the service. Operator dashboards consume the
   same API as agents.
4. **Plugin-ready.** Extensions gated by an explicit allowlist in `.env`.
5. **Environment secrets only.** `.env` is gitignored; secrets via
   [`protocols/secrets-vault.md`](protocols/secrets-vault.md).
6. **Reusable contracts.** External actors implement an interface; the
   service does not embed provider-specific logic.
7. **State of the Art.** Strict TypeScript; immutable migrations with
   SHA-256 drift detection; structured pino logging; UUIDv7 externally,
   BIGSERIAL internally; Prometheus metrics; graceful shutdown.
8. **Reuse-First / Lookup-before-Build.** Before any new capability is
   implemented, the catalog at [`SERVICES.yaml`](SERVICES.yaml) MUST be
   consulted. If an existing service already exposes the capability
   (matching `services[*].capabilities`), the new code MUST consume it
   over HTTP — never copy logic, never re-implement. Cross-cutting
   concerns (auth, idempotency, errors, health, metrics, audit) MUST
   reuse the protocols under [`protocols/`](protocols/) and the
   reference implementation in `BBE-DBE/ip-pool-api`. Violations are a
   compliance bug, not a style preference. Workflow enforcement lives in
   [`checklists/14-dimensions.md`](checklists/14-dimensions.md) §5 + §13
   and in the bootstrap checklist.
9. **Self-Registration.** Every network-bound service MUST register
   itself with `port-registry` on startup and expose
   `/service-manifest` (see [`protocols/service-manifest.md`](protocols/service-manifest.md)).
   This is what makes principle 8 mechanically possible: agents discover
   capabilities at runtime, not by reading source code.

## Workflow (mandatory)

Every code change in any service follows
[`workflows/agent-prompt-prefix.md`](workflows/agent-prompt-prefix.md):

1. **Vorher** — Trade-off analysis (a/b/c/d as defined in the workflow).
2. **Nachher** — 14-dimension self-check
   ([`checklists/14-dimensions.md`](checklists/14-dimensions.md)).
3. **Optimierung** — measurement-driven follow-up.

## Conflict order (when principles collide)

1. **Sicherheit** (Secrets, Auth, Audit, SQL-Injection)
2. **Korrektheit** (Idempotenz, Race-Conditions, State-Machine)
3. **Compliance** (DSGVO, ISO 27001, Audit-Trail)
4. **Observability** (Logs, Metrics, Tracing)
5. **Performance** (Latency, Throughput)
6. **DX** (Build-Zeit, Code-Schönheit)

Lower tiers yield to higher tiers. Justification goes in a code comment.

## Auth-Layer-Pattern

Services that authenticate callers themselves (as opposed to inheriting
auth from a sibling service) follow a single pattern, anchored on
**argon2id** for secret hashing and a **prefixed bearer token** for
transport.

### Token format

```
<prefix>_<key_id>_<secret>
```

- `<prefix>` — 2–4 lowercase letters, **reserved per service** in
  [`templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md`](templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md).
  Operator pflicht: vor neuer Vergabe Liste prüfen.
- `<key_id>` — 26-char base32-lower, generated at mint time. Public,
  indexable, **no secret material**.
- `<secret>` — 43-char base64url, generated at mint time. **Never
  persisted in plaintext** — only the argon2id hash lives in
  `<schema>.api_keys.key_hash`.

### Why argon2id and not bcrypt/scrypt/SHA

- argon2id is the OWASP-recommended default since 2021 (memory-hard,
  side-channel-resistant).
- The skeleton ships `argon2` as a build-only dependency
  (`pnpm.onlyBuiltDependencies` in `package.json`); it builds a
  native binding at install time. That is **deliberate, not
  dead-code** — the dep is opt-in via `--with-auth` in
  `scripts/new-service.sh`. Services that don't authenticate
  themselves can safely remove the dep from their own `package.json`.

### Reference implementation

`BBE-DBE/ip-pool-api/src/auth.ts` (~325 LoC). It covers:

- Argon2id verify with in-process verify-cache (60 s TTL, sha256 of
  the verified secret only — never the secret itself).
- Cluster-shared brute-force counter via `<schema>.auth_failures`,
  with a 1 s in-process read-cache to keep the hot path off the DB.
- Two-bucket lock (per-`key_id` AND per-`source-ip`) — either trips
  the 429.
- `requireAuth(scopes)` Fastify pre-handler that throws
  `forbidden` on missing scope, `unauthorized` on bad token,
  `too_many_failed_auth` (429) with `Retry-After` on lock-out.

### Mandatory accompanying assets

When `--with-auth` is set, `new-service.sh` copies the migration
template `_optional/auth/migration.sql` to
`db/migrations/002_auth.sql` (api_keys + auth_failures + outbox).
The TypeScript layer is **not** auto-generated yet — implement based
on ip-pool-api as reference.

## Why this file is short

The detailed reasoning for each principle lives in
[`workflows/agent-prompt-prefix.md`](workflows/agent-prompt-prefix.md)
and the cross-cutting protocols under
[`protocols/`](protocols/). This page is a **landing point**, not the
manual.
