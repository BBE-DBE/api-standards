# Changelog

Calendar versioning: **YYYY.MM.DD**. Tags are immutable; new policies
land as a new tag, services pin a minimum version they were last
validated against.

## [2026.05.02] - 2026-05-02

Skeleton-Validierungs-Patch. Bugs aus dem ersten echten Bootstrap-Versuch
(siehe `docs/skeleton-bugs-found.md`) sind gefixt; das Skeleton ist jetzt
reproduzierbar von einem Skript-Aufruf aus generierbar.

### Added
- `scripts/new-service.sh` — Flag-Parser für reproduzierbare Bootstraps:
  `--schema=`, `--port=`, `--prefix=` (alias `--token-prefix=`),
  `--desc=`, `--with-auth`. Positional-Form bleibt funktional.
- `templates/service-skeleton/_optional/auth/migration.sql` — opt-in
  Auth-Layer-Migration (api_keys + auth_failures + outbox), per
  `--with-auth` ins neue Service-Repo gespielt mit voll
  substituiertem `__TOKEN_PREFIX__`. Reserve-Registry der Prefixe in
  `_optional/auth/README.md`.
- `templates/service-skeleton/db/migrations/001_init.sql` —
  `update_updated_at()`-Trigger-Funktion ergänzt; Folge-Migrations können
  sie ohne Re-Definition referenzieren.
- `templates/openapi-skeleton.yaml` — OpenAPI-3.1-Stub als Fallback,
  wenn ein Service den zod→OpenAPI-Generator noch nicht verdrahtet hat.
- `templates/migration-header.sql` — Konventions-Datei für
  Author/Date/Commit-Header.
- `PRINCIPLES.md` und `STANDARDS.md` (root) — vorher 0 Bytes; jetzt
  Landing-Page für Cross-Cuts (Pointer auf Workflows, Protocols, Mappings).
- `docs/skeleton-bugs-found.md` — fortgesetzte Sammelstelle aller
  Skeleton-Lücken, die bei realen Bootstraps auffallen. B1–B11
  dokumentiert; B7 (`_optional/`-Wiring-Snippets für metrics/swagger) und
  Teile von B9 (Auto-Repo-Erstellung) bleiben offen.
- `docs/status-reports/skeleton-patches-2026.05.02.md` — Status-Report
  zu diesem Patch (Trade-offs, 14-Dimensionen-Selbstcheck-Auszug).

### Fixed
- `templates/{audit-event-schema,error-codes,health-response-schema}.yaml`
  (0-Byte-Stubs) entfernt — Quelle der Wahrheit ist `protocols/`.
- `templates/service-skeleton/scripts/migrate.sh` — Container-Name jetzt
  via `${POSTGRES_CONTAINER:-infra-postgres}` überschreibbar (B8).
- `scripts/new-service.sh` — Schema-Suffix `_svc` wird jetzt abgelehnt
  (B11), sonst doppelter `_svc_svc`-User. Fehlende Description gibt
  jetzt eine sichtbare Warnung statt stiller Default-Substitution (B5).

### Note (additive only)
Bestehende Services (ip-pool-api, infra-postgres) sind nicht betroffen.
Die Skeleton-Patches wirken nur auf Services, die **nach** 2026.05.02
generiert werden. Pinning-Migration auf 2026.05.02 ist optional und
empfehlenswert beim nächsten Service-Release.

### Companion changes (separate repos)
- `BBE-DBE/infra-postgres` v0.1.3 ships
  `scripts/add-service-schema.sh` — referenced from
  `new-service.sh`'s operator-TODO block. Together the two scripts
  reduce a service bootstrap to two operator lines (provision +
  service-`new-service.sh` invocation).

### Pinned by
- BBE-DBE/ip-pool-api ≥ 2026.04.30 (unverändert).
- BBE-DBE/infra-postgres ≥ 2026.05.02 (since v0.1.3).

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
