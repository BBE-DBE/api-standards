# New-Service-Bootstrap (Checkliste)

Anwenden bei jedem neuen Service unter `~/projects/<name>/`. Kopiert die
Mindest-Standards aus dem ip-pool-api-Schnitt:

## Dateien (alle Pflicht)
- [ ] `README.md`
- [ ] `PRINCIPLES.md`
- [ ] `STANDARDS.md` (verlinkt `api-standards/iso-mappings/27001-controls.md`)
- [ ] `CHANGELOG.md` (Keep-a-Changelog)
- [ ] `AGENTS.md` (Pointer auf api-standards)
- [ ] `.env.example` (Platzhalter, nie echte Werte)
- [ ] `.gitignore` (`node_modules/`, `dist/`, `.env`, `logs/`, `coverage/`,
  `.tsbuildinfo`, `src/lib/git-sha.ts`)
- [ ] `.gitleaks.toml` mit allowlist für `.env.example`
- [ ] `.github/workflows/test.yml` (tsc + vitest + build)
- [ ] `.github/workflows/gitleaks.yml`

## Skripte (Pflicht)
- [ ] `scripts/build.sh` (generiert `src/lib/git-sha.ts`)
- [ ] `scripts/release.sh` (clean-tree, semver-bump, tag)
- [ ] `scripts/migrate.sh` (SHA-256-Drift-Check, Author-Header parse)
- [ ] `scripts/smoke-test.sh`
- [ ] `scripts/install-precommit.sh` (gitleaks)

## Code-Bausteine
- [ ] `src/config.ts` mit zod-validiertem env
- [ ] `src/db.ts` mit `statement_timeout`, search_path, pool min/max/idle
- [ ] `src/lib/logger.ts` (pino, redact paths)
- [ ] `src/lib/uuid7.ts`
- [ ] `src/lib/build-version.ts`
- [ ] `src/lib/idempotency.ts` (DB-backed, request_hash)
- [ ] `src/lib/audit.ts` (Tx-shared event_uuid + outbox)
- [ ] `src/auth.ts` (argon2id, verify-cache, brute-force counter)
- [ ] `src/app.ts` + `src/server.ts` (split — pm2-fork-mode entry-detection)

## Datenbank
- [ ] Eigenes Schema (kein Cross-Schema-Zugriff)
- [ ] Append-only Trigger auf events
- [ ] State-Machine-Trigger wo State-Übergänge existieren
- [ ] Migrations mit `-- Author: / -- Date: / -- Commit:` Header
- [ ] Idempotency-Keys-Tabelle
- [ ] Outbox-Tabelle (wenn Hooks)
- [ ] Api-Keys-Tabelle (wenn eigener Auth-Layer)

## Doku
- [ ] `docs/api-versioning.md`
- [ ] `docs/bootstrap-rotation.md`
- [ ] `docs/data-processing.md` (DSGVO Art. 30)
- [ ] `docs/disaster-recovery.md` (RTO/RPO)
- [ ] `docs/query-plans.md` (EXPLAIN)
- [ ] `docs/release.md` (Release-Procedure)
- [ ] `docs/operations.md` (systemd-Timer, pm2-logrotate, Cron)
