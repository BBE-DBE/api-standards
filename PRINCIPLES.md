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

## Why this file is short

The detailed reasoning for each principle lives in
[`workflows/agent-prompt-prefix.md`](workflows/agent-prompt-prefix.md)
and the cross-cutting protocols under
[`protocols/`](protocols/). This page is a **landing point**, not the
manual.
