# Standards — api-standards (root)

The cross-cutting standards every BBE-DBE service inherits. Service-
specific deviations live in each service's own `STANDARDS.md`.

## Cross-service contracts

| Contract             | Location                                                                                |
|----------------------|-----------------------------------------------------------------------------------------|
| Audit-event schema   | [`protocols/audit-event-schema.yaml`](protocols/audit-event-schema.yaml)                |
| Error-code registry  | [`protocols/error-codes.yaml`](protocols/error-codes.yaml)                              |
| Health response shapes | [`protocols/health-response-schema.yaml`](protocols/health-response-schema.yaml)      |
| Secrets vault        | [`protocols/secrets-vault.md`](protocols/secrets-vault.md)                              |

## Hard rules (every service)

1. **127.0.0.1 only.** Service binds loopback. TLS via Caddy in front;
   service-to-service via loopback.
2. **`.env` carries real credentials.** `.env` is gitignored.
   `.env.example` documents every key with safe placeholders.
3. **Migrations are immutable.** `scripts/migrate.sh` aborts on SHA-256
   drift.
4. **Schema-per-service.** No service touches another's schema without
   a documented contract.
5. **Audit-log is append-only.** A trigger on `events` rejects
   UPDATE/DELETE.
6. **Idempotency-Key on every mutation.** Replays return the cached
   response; mismatched bodies return 409 idempotency_mismatch.

## ISO mappings

- ISO 27001 controls implemented:
  [`iso-mappings/27001-controls.md`](iso-mappings/27001-controls.md)
- ISO 42001: out-of-scope unless the service embeds an AI system
  (Art. 3.1).
- DSGVO: each service ships `docs/data-processing.md` (Art. 30
  Verzeichnis).
- EU Cyber Resilience Act: SBOM (CycloneDX) per release.

## Versioning

Calendar versioning: `YYYY.MM.DD`. Tags are immutable. Services pin a
**minimum version** they were last validated against, in their own
`STANDARDS.md`. New controls land here first; services migrate at
their next release.

## Self-check

After every build, run
[`checklists/14-dimensions.md`](checklists/14-dimensions.md). The
status report follows
[`templates/status-report.md`](templates/status-report.md).
