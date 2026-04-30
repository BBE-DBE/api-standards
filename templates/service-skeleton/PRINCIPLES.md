# Principles — __SERVICE_NAME__

These principles are inherited from
`BBE-DBE/api-standards/workflows/agent-prompt-prefix.md` and apply to
every service in the ecosystem. Service-specific exceptions are
documented below; if there are none, leave that section empty.

## Inherited

1. **Agent-First.** All endpoints work without UI. Idempotency-Key on
   every mutation. Stable error codes (see
   `api-standards/protocols/error-codes.yaml`).
2. **API-First.** OpenAPI 3.1 generated from zod schemas — single
   source of truth.
3. **Headless.** No UI in the service. Operator dashboards live
   elsewhere and consume the same API.
4. **Plugin-ready.** If the service exposes extensions, they are
   gated by an explicit allowlist in `.env`.
5. **Environment secrets only.** `.env` is gitignored; secrets via
   the vault pattern in `api-standards/protocols/secrets-vault.md`.
6. **Reusable contracts.** External actors (providers, downstream
   services) implement an interface; the service does not embed
   provider-specific logic.
7. **State of the Art.** Strict TypeScript; versioned migrations with
   SHA-256 drift detection; structured pino logging; UUIDv7 for
   external ids; graceful shutdown; Prometheus metrics.

## Service-specific

(none — fill in if this service deviates from any of the above)
