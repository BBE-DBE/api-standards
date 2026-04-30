# Standards — __SERVICE_NAME__

This service inherits the BBE-DBE ecosystem standards. Cross-cuts:

- ISO 27001 controls: see
  [`api-standards/iso-mappings/27001-controls.md`](https://github.com/BBE-DBE/api-standards/blob/main/iso-mappings/27001-controls.md)
- Cross-service contracts:
  - audit events: `api-standards/protocols/audit-event-schema.yaml`
  - error codes:  `api-standards/protocols/error-codes.yaml`
  - health:       `api-standards/protocols/health-response-schema.yaml`
  - secrets:      `api-standards/protocols/secrets-vault.md`

## Hard rules (every service)

1. **127.0.0.1 only.** Never bind to a non-loopback address. TLS via
   Caddy in front; service-to-service via loopback.
2. **`.env` carries real credentials.** `.env` is gitignored;
   `.env.example` documents every key with safe placeholders.
3. **Migrations are immutable.** `scripts/migrate.sh` aborts if a
   previously-applied file changed (SHA-256 drift detection).
4. **Schema-per-service.** No service touches another's schema
   without a documented contract.
5. **Audit-log is append-only.** A trigger on the `events` table
   rejects UPDATE/DELETE.
6. **Idempotency-Key on every mutation.** Replays return the cached
   response; mismatched bodies return 409 idempotency_mismatch.

## ISO 42001

This service is **out of scope** of ISO 42001 unless it embeds an AI
system as defined in §3.1. If it does, follow
`api-standards/iso-mappings/42001-controls.md` (when added) and
record the model inventory + risk assessment in `docs/ai-system.md`.

## Service-specific

(replace this section with anything unique to __SERVICE_NAME__)
