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
  `--desc=`, `--with-auth`, `--dry-run`. Positional-Form bleibt
  funktional. `--schema` ist optional und wird aus dem Service-Namen
  abgeleitet (kebab → snake, `port-registry` → `port_registry`).
- `--dry-run` Flag: führt alle Substitutionen + Validations durch,
  überspringt git-init, löscht das Target-Verzeichnis am Ende
  (defensiver Pfad-Guard: nur unter `$HOME/projects/`).
- `templates/service-skeleton/_optional/auth/migration.sql` — opt-in
  Auth-Layer-Migration (api_keys + auth_failures + outbox), per
  `--with-auth` ins neue Service-Repo gespielt mit voll
  substituiertem `__TOKEN_PREFIX__`.
- `templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md` —
  globale Single Source of Truth für reservierte Bearer-Token-Prefixe
  (Initial-Eintrag: `iplk_` → ip-pool-api v0.3.0). Operator-Pflicht:
  vor neuer Vergabe konsultieren. Referenziert vom Skeleton-AGENTS.md
  und vom `new-service.sh`-Hint-Output.
- `templates/service-skeleton/src/plugins/metrics.ts` — opt-in
  Wiring-Stub für prom-client. `app.ts` enthält den Aufruf
  auskommentiert mit "Uncomment to enable". Metric-Name-Prefix nutzt
  `__DB_SCHEMA__` (nicht `__SERVICE_NAME__`), um Prometheus-Spec
  (`[a-zA-Z_:][a-zA-Z0-9_:]*`) bei kebab-case-Service-Namen
  einzuhalten — siehe B13 in `docs/skeleton-bugs-found.md`.
- `templates/service-skeleton/src/plugins/openapi.ts` — opt-in
  Wiring-Stub für `@fastify/swagger` + `swagger-ui` +
  `fastify-type-provider-zod`.
- `PRINCIPLES.md` Sektion "Auth-Layer-Pattern" — argon2id-Begründung,
  Token-Format, Reference-Implementation-Pointer (B12).
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
  Skeleton-Lücken, die bei realen Bootstraps auffallen. B1–B13
  dokumentiert. B7 jetzt ✅ (Wiring-Stubs als `src/plugins/`).
  Reste von B9 (auto-`gh repo create`/PM2) bleiben bewusst offen
  (Operator-Sichtprüfung).
- `docs/status-reports/api-standards-2026.05.02.md` — Status-Report
  mit 14-Dimensionen-Selbstcheck und Mess-Daten. Re-Test mit
  echtem `test-foundation`-Bootstrap (6/6 grün).

#### Architecture-Completion (2026-05-02 evening, branch `feat/architecture-completion-2026-05-02`)
- `SERVICES.yaml` — root-level service catalog. Single source of truth
  for "which BBE-DBE services exist, what can they do, in what order
  do agents reuse them?". 11 services indexed (foundation, service,
  frontend, bridge tiers) with port, openapi_url, manifest_url,
  capabilities, reuse_priority. Anchored from PRINCIPLES.md §8.
- `PRINCIPLES.md` §8 **Reuse-First / Lookup-before-Build** — new
  inherited principle that mandates `SERVICES.yaml` consultation
  before any new capability. Violations are compliance bugs.
- `PRINCIPLES.md` §9 **Self-Registration** — new inherited principle
  that mandates port-registry registration on startup and
  `/service-manifest` exposure.
- `protocols/service-self-registration.md` — registration / heartbeat
  / deregistration contract for port-registry. Contract-only, no
  implementation here.
- `protocols/service-manifest.md` — `/service-manifest` endpoint
  schema (name, version, capabilities, dependencies, openapi_url,
  auth, idempotency, health, metrics_url, compliance, links).
- `protocols/idempotency-header-compat.md` — both `Idempotency-Key`
  AND `X-Idempotency-Key` MUST be accepted as aliases; conflict on
  divergent values rejected with `idempotency_header_conflict`.
- `protocols/provider-adapter-interface.md` — minimal `ProviderAdapter`
  TypeScript surface and cross-cutting obligations (retries,
  rate-limit, error mapping, audit, multi-base). Initial consumers:
  netcup-api, hetzner-api.
- `checklists/14-dimensions.md` §5 + §13 extended with: service-reuse
  verification, dual-header idempotency, /service-manifest, self-
  registration, SERVICES.yaml lookup.
- `docs/status-reports/hetzner-api-gaps.md` — gap snapshot for
  hetzner-api at branch `release/v1.0.0` tip `adab95d`. **No code
  changes to hetzner-api**; this is documentation only.

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
