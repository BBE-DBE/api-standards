# port-registry rc1 — Final Status Report

**Service:** `port-registry`
**Version:** `v0.1.0-rc1` (annotated tag, **lokal**, nicht gepusht)
**Repo:** `BBE-DBE/port-registry` (private, remote=origin, no commits pushed)
**Validator:** Claude Opus 4.7 (1M context)
**Date:** 2026-05-01

## Resultat

`v0.1.0-rc1` ist build-grün, tag-bereit, push-pending auf
Operator-Entscheid (siehe `docs/operator-todo.md` im Service-Repo).
47 vitest-specs grün, TSC strict 0 errors, pnpm audit 0 high+,
SBOM 408 components (CycloneDX 1.6). NOTIFY/LISTEN end-to-end
live verifiziert (Phase 4 smoke).

## Phasen-Trail

| Phase | Commit | Was               | Validierung                     |
|-------|--------|-------------------|---------------------------------|
| 1     | `c082009` + `0542a08` | Bootstrap from skeleton + lockfile | install + tsc + vitest + audit; gh repo create (no push) |
| 2     | `94780a0`     | Schema/migrations/seed + 5099 alignment | counts(3 hosts, 2 ports), BPAP CHECK negative-test |
| 3     | `dc1c9bf`     | Auth + 9 v1-routes + zod + OpenAPI 3.1 + inline watermark | server smoke (3 routes + 3 auth-cases) |
| 4     | `ebe9ea6`     | LISTEN/NOTIFY watermark cache + cluster-safe sweeper | live UPDATE → trigger → invalidate captured; sweep_id=3 with mixed ok/fail |
| 5     | `3e4d706`     | 47 vitest specs + docs + CHANGELOG + SBOM | full suite green, TSC, audit clean |

Tag-Snapshot:
```
3e4d706 feat(phase-5): 47 vitest specs, docs, CHANGELOG rc1     ← v0.1.0-rc1
ebe9ea6 feat(phase-4): watermark LISTEN/NOTIFY + sweeper
dc1c9bf feat(phase-3): auth, 9 v1-routes, zod, OpenAPI 3.1
94780a0 feat(phase-2): schema + migrations + seed + 5099
0542a08 chore(phase-1): commit lockfile
c082009 feat: initialise from skeleton
```

## 14-Dim-Selfcheck (final, post-Phase-5)

| # | Dimension | Status | Notiz |
|---|-----------|:-:|-------|
| 1  | Sicherheit         | ✅ | argon2id verify + brute-force-counter (5 in 60 s) cluster-shared via `auth_failures`; secret-sha256 cache (no plaintext); X-Request-Id propagation; schema-isolation enforced (Phase-1 negative-test); BPAP CHECK at DB-layer; advisory-lock 7099 documented; pnpm audit 0 high+; **O1** documented (PGPASSWORD-leak via Read+system-reminder; mitigation via schema-isolation; rc2: secret-pointer-pattern) |
| 2  | Korrektheit        | ✅ | DB CHECK + zod + transactional reserve+release+audit+port_history; idempotency-Key inline (test verified); 3-fail-streak only emits once; LISTEN/NOTIFY end-to-end live; resetDb safety-assertion (NODE_ENV=test ∧ PGDATABASE=ecosystem) |
| 3  | Performance        | ✅ | watermark cache (push: NOTIFY, pull: 30 s TTL); keyset audit pagination via `events_subject_id_at` index; sweeper fan-out parallel via Promise.all; AbortSignal 5 s timeout; partial indexes on `status='live'` and `status IN ('reserved','running')` |
| 4  | Effizienz          | ✅ | LISTEN on dedicated `pg.Client` (pool not blocked); skip-on-lock-busy in sweeper; pre-computed argon2 hash in tests (~ms per `mintTestKey`); HEALTH_SWEEP_DISABLED short-circuits the loop |
| 5  | Modularität        | ✅ | schemas/routes/lib/plugins separate; auth-prefix shared via PREFIX-REGISTRY; Migrations 001..006 each ≤100 lines; routes ≤350 lines |
| 6  | Kompatibilität     | ✅ | OpenAPI 3.1.0 (post-rewrite — `@fastify/swagger` v9 issue documented); /v1/* versioned; structured error-codes; ISO timestamps; UUIDv7 external + BIGSERIAL internal |
| 7  | Skalierbarkeit     | ✅ | Stateless app, DB is source of truth; in-process verify-cache OK at single-instance scale; cluster-safe sweeper via `pg_try_advisory_lock(7099)`; auth_failures cluster-shared |
| 8  | Observability      | ✅ | structured pino logs with request_id, sweep metrics (sweep_id, ok/fail/unknown, latency); cache-invalidate log captures payload; reconnect log with delay_ms; audit events tag build_version + git_commit |
| 9  | Code-Qualität      | ✅ | TSC strict 0; vitest 47/47; commits explain WHY (not what); trade-offs in commit messages; no TODO/FIXME without follow-up |
| 10 | Compliance         | 🟡 | author-tracking on every migration (sha-drift-checked); SBOM via cdxgen 1.6; ISO-mappings remain skeleton-stubs (rc2) |
| 11 | Operations         | ✅ | shutdown order: sweeper → listener → app → db; SIGTERM/SIGINT handled; PM2 ecosystem.config.cjs from skeleton; HEALTH_SWEEP_DISABLED maintenance toggle; operator-todo runbook for post-tag steps |
| 12 | Dokumentation      | ✅ | README + BPAP-v1.0 + API + operator-todo + CHANGELOG; OpenAPI auto-gen as live spec; Plan-Patches doc-trail in api-standards |
| 13 | Agent-Tauglichkeit | ✅ | headless JSON, stable error-codes, Idempotency-Key + X-Run-Id honored, headless bootstrap (skeleton + add-service-schema.sh + bootstrap-key.sh), all auth via bearer |
| 14 | Lebenszyklus       | ✅ | Migrations immutable, sha-256-drift-checked, author-tracked; soft-delete via `status='released'`; tag annotated; reproducible build via `GIT_SHA` stamp + clean-tree gate |

**13 ✅ + 1 🟡** — Compliance bleibt yellow weil ISO-Mapping (27001 + 42001) als
Skeleton-Stubs unverändert sind. Das ist Plan-erwartet (rc1 ist
Code-/Tests-/Docs-Cut, ISO-Sweep folgt orthogonal).

## Trade-offs (kompakt)

Die wichtigsten Trade-offs aus den Phase-spezifischen Reports
(siehe `port-registry-rc1-phase{2,4}-patches.md`):

| Wo | Entscheidung | Wahl | Begründung |
|----|--------------|------|------------|
| Phase 2 | Service-Port `5300` vs `5099` | **5099** | Brief widersprach BPAP-meta-Range; Korrektheit > Brief-Wortlaut |
| Phase 2 | Migrations `002/003` vs `003/004` | **003/004** | Skeleton belegt 002_auth |
| Phase 3 | Auth from-scratch vs ip-pool-clone | **clone** | Konsistenz zwischen BBE-DBE-Services |
| Phase 3 | OpenAPI hand-written vs zod-auto | **zod-auto** | single source of truth, no drift |
| Phase 3 | Bootstrap-Token persistieren? | **discard** | O1-mitigation: token nicht in transcript |
| Phase 4 | Cache invalidation: TTL vs LISTEN | **LISTEN + TTL fallback** | belt-and-suspenders, defense-in-depth |
| Phase 4 | NOTIFY trigger location | **DB trigger** | catches direct SQL too |
| Phase 4 | Cluster lock | **pg_advisory_lock** | no extra infra |
| Phase 4 | Conflict-detection scope | **DB-half only** | rc2: Application-half braucht uniforme `/health` shape |
| Phase 5 | Test-DB-Strategie | **shared schema + TRUNCATE+seed** | testcontainers wäre Overkill; safety-assertion |
| Phase 5 | Test-Auth | **echtes argon2-mint** | kein Mock-Drift |
| Phase 5 | Test-Pool-Mode | **single fork + sequential files** | TRUNCATE-Race-Vermeidung |

**Konflikt-Reihenfolge** wurde durchgängig angewandt:
Sicherheit > Korrektheit > Compliance > Observability > Performance > DX.

## Tech-Debt für rc2

1. **O1 — secret-pointer pattern.** `.env`-edits leak PGPASSWORD ins
   Conversation-Transcript via Read + Claude-Code system-reminder.
   rc1-Mitigation: schema-isolation begrenzt blast-radius. rc2-Plan:
   `PGPASSWORD_FILE=/run/secrets/...` + service-side file-read at
   startup.
2. **P5 — Application-side conflict-detection.** Sweeper soll `/health`
   (full) statt `/health/live` probieren und `service.name` mit
   `port.service_name` vergleichen. Setzt voraus, dass alle BBE-DBE-
   Services `/health.service = { name, version }` exposen → api-
   standards-Protokoll-Commit + sweep-PR durch alle Services.
3. **Advisory-Lock-Registry** in api-standards (analog zu
   `PREFIX-REGISTRY.md`). Konvention: 4-digit, erste 2 = service-port-
   prefix, letzte 2 = subsystem (`xx99` = sweeper). port-registry hält
   `7099`.
4. **B14 / B15 (skeleton bugs).** `pnpm tsc --noEmit` standalone fail
   wegen gitignored generated `git-sha.ts`; `AGENTS.md` Pin-Floor wird
   nicht beim Bootstrap auf aktuellen calver-Tag substituiert. Beide
   in `skeleton-bugs-found.md` als action items für `2026.05.0X`.
5. **`@fastify/swagger` v9 OpenAPI 3.1 native emission** — heute
   workaround per `/openapi.yaml`-route post-rewrite. Sobald upstream
   3.1 nativ emittiert, post-rewrite entfernen.
6. **HEALTH_SWEEP_INTERVAL** ist global — eine Operator-overridebare
   per-port `health_check_interval_ms`-Spalte könnte langsamere
   Services entlasten. Niedrige Priorität.
7. **OpenAPI Schema-Examples** — Plan-Brief erwähnte sie, rc1 lieferte
   nur Schemas. examples via zod `.describe()` + transformer-extension
   sind ein 1-day-job.

## Operator-Pflicht-TODO vor Push

Aus `port-registry/docs/operator-todo.md` (Auszug):

1. Phase-3 bootstrap-Token revoken (plaintext wurde discarded), via
   `bash scripts/bootstrap-key.sh` neu minten → landet in `.env` als
   `PRR_ADMIN_TOKEN`.
2. PM2: `pm2 start ecosystem.config.cjs && pm2 save`.
3. Live-Smoke gegen alle 8 v1-Routes (curl-Recipes im operator-todo).
4. Restart-survival: `pm2 restart && /health/live` muss innerhalb 5 s
   antworten; Logs müssen `watermark LISTEN active` + `health sweeper
   started` zeigen.
5. **Wenn alles grün:** `git push origin main && git push origin v0.1.0-rc1`.
   Sonst: follow-up commit + `v0.1.0-rc2`.

## Downstream-Implikationen

- `bbe-frontend` Phase 4 (per memory `bbe_frontend_state.md`) ist
  blockiert auf rc1-push. Frontend liest `GET /v1/ports` + `GET /v1/hosts`.
- Neue BBE-DBE-Services rufen während ihres Bootstraps (nach
  `add-service-schema.sh`, vor PM2-start) `POST /v1/ports/reserve` auf.
  Operator-Convention: token aus `BBE-DBE/port-registry`-Vault holen,
  niemals als CLI-arg.
