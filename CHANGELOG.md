# Changelog

Calendar versioning: **YYYY.MM.DD**. Tags are immutable; new policies
land as a new tag, services pin a minimum version they were last
validated against.

## [2026.05.01] - 2026-05-01

Tier-0-Fundament. Cross-service contracts, forkbares Service-Skeleton,
secrets-vault pattern.

### Added
- `templates/service-skeleton/` — komplett forkbares Service-Skeleton
  mit `__SERVICE_NAME__/__DB_SCHEMA__/__DEFAULT_PORT__/__SERVICE_DESC__`
  Platzhaltern, eigener config/db/lib/audit/idempotency/errors,
  health-routes, vitest-setup, ecosystem.config.cjs, gitleaks,
  Dependabot, Test-CI mit `pnpm audit --audit-level=high`.
- `scripts/new-service.sh` — bootstrapped neue Services aus dem
  Skeleton, inklusive Substitution + git init + Operator-Next-Steps.
- `protocols/audit-event-schema.yaml` — verbindliches Audit-Event-Format
  (JSON-Schema 2020-12). Additive Evolution; Felder werden nie umbenannt.
- `protocols/error-codes.yaml` — cross-service Error-Code-Registry.
  Adding/removing codes ist ein versionierter Vorgang.
- `protocols/health-response-schema.yaml` — Schema-Definitionen für
  /health, /health/live, /health/ready.
- `protocols/secrets-vault.md` — `.env`-Tresor-Pattern (vault contents,
  GPG-master-key setup, restore drill cadence).

### Note (additive only)

Alle bestehenden Services bleiben gültig unter 2026.04.30. Neue Tier-0-
Anforderungen treten in Kraft, sobald ein Service auf 2026.05.01 pinnt.

### Pinned by

- BBE-DBE/ip-pool-api ≥ 2026.04.30 (unverändert; Migration auf
  2026.05.01 separat geplant — Tier-0 ändert ip-pool-api nicht).
- BBE-DBE/infra-postgres ≥ 2026.04.30 (unverändert).

## [2026.04.30] - 2026-04-30

### Added
- `workflows/agent-prompt-prefix.md` — three-part workflow (Trade-off →
  14-Dimension-Selbstcheck → Optimierungs-Schleife).
- `checklists/14-dimensions.md` — full checklist used by the post-build
  self-check.
- `checklists/new-service-bootstrap.md` — what every new BBE-DBE
  service must ship with on day one.
- `iso-mappings/27001-controls.md` — ISO 27001 controls actually
  implemented across the ecosystem (with per-service evidence pointers).
- `templates/status-report.md` — final-status-report layout used at the
  end of every agent task.

### Pinned by

- BBE-DBE/ip-pool-api ≥ 2026.04.30 (since v0.3.0)
- BBE-DBE/infra-postgres ≥ 2026.04.30 (since v0.1.1)
