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
| Model-provider adapter | [`protocols/model-provider-adapter.md`](protocols/model-provider-adapter.md)          |

## Ratified standards registry

| Standard ID  | Title                            | Version    | Status                          | Location                                                                  |
|--------------|----------------------------------|------------|---------------------------------|---------------------------------------------------------------------------|
| BBE-STD-002  | Agent Communication Protocol     | v1.0.0     | RATIFIED                                                              | [`standards/BBE-STD-002/`](standards/BBE-STD-002/) |
| BBE-STD-004  | Model Provider Portability       | v0.1.0     | DRAFT                                                                 | [`standards/BBE-STD-004/`](standards/BBE-STD-004/) |

**BBE-STD-002 notes:**
- Runtime-agnostic per [ADR-0003](standards/BBE-STD-002/docs/adr/0003-runtime-agnostic-posture.md). The BBE deployment runtime binding lives in `bbe-server-config/configs/bbe-guard/`.
- HMAC-anchored authorization sits at L4. L5 (signature/ledger/attestation) reserved for the deferred BBE-STD-003.
- Reference linter + CLI: `standards/BBE-STD-002/tools/bbe-comm/`. Run `scripts/test-std-002.sh` for the ratification gate.
- Phase D rollout: 14-day warning window 2026-05-13 → 2026-05-27; hard floors take effect 2026-05-28.

**BBE-STD-004 notes:**
- **DRAFT — binds no service yet.** Reserved ID note: `BBE-STD-003` stays
  reserved for Audit-Store & Message Persistence; portability took the next
  free ID.
- Answers "what happens when our model provider is switched off" with two
  numbers per service: **RTO-model** (minutes to switch) and **QLO** (measured
  score of the qualified fallback). A claim of provider independence without
  both is marketing, not a control.
- Conformance levels P0–P4 (§3). Target for services that embed an AI system:
  **P4** — at least one non-primary provider measured `QUALIFIED` within 90 days.
- Reference CLI: `standards/BBE-STD-004/tools/bbe-port/`. Run
  `scripts/test-std-004.sh` for the gate (offline, no credentials, stdlib only).
- Cross-service pointer: [`protocols/model-provider-adapter.md`](protocols/model-provider-adapter.md).
  Inherits the cross-cutting obligations of
  [`protocols/provider-adapter-interface.md`](protocols/provider-adapter-interface.md)
  rather than restating them (ADR-0001).
- Ratification blockers: one service at P3 with a stored report, §10 D1, and an
  operator mandate.

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
