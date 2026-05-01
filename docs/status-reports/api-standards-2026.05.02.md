# STATUS-REPORT — api-standards 2026.05.02

```
Service:  api-standards (Skeleton-Foundation)
Version:  2026.05.02
Auftrag:  Skeleton-Bugs B1–B13 fixen + new-service.sh Flag-Parser +
          002_auth-Template + Wiring-Stubs (metrics/openapi) +
          PREFIX-REGISTRY + add-service-schema.sh + --dry-run
Datum:    2026-05-02
Kontext:  Foundation für ALLE künftigen Service-Bootstraps. Erste reale
          Skeleton-Validierung (port-registry, verschoben) hat 13 Bugs
          aufgedeckt; Patches landen unabhängig vom verschobenen
          Service. Frontend-Stack läuft parallel als eigenes Monorepo
          (Turborepo + Astro + Lit + Style Dictionary).
```

## Punkte (OK / teilweise / fehlt)

| #  | Punkt                                                                                          | Status | Note |
|----|------------------------------------------------------------------------------------------------|--------|------|
| 1  | `docs/`-Verzeichnis + `docs/status-reports/` angelegt                                          | ✅     | B3   |
| 2  | `docs/skeleton-bugs-found.md` mit Action-Items für B1–B11                                      | ✅     |      |
| 3  | Leere YAML-Stubs unter `templates/` entfernt (canonical: `protocols/`)                         | ✅     | B1   |
| 4  | `templates/migration-header.sql` befüllt (Header-Konvention)                                   | ✅     | B1   |
| 5  | `templates/openapi-skeleton.yaml` befüllt (OpenAPI-3.1 Fallback-Stub)                          | ✅     | B1   |
| 6  | Root `PRINCIPLES.md` + `STANDARDS.md` befüllt (Pointer-Landing-Page)                           | ✅     | B2   |
| 7  | `update_updated_at()`-Funktion in Skeleton-001 ergänzt                                         | ✅     | B4   |
| 8  | `migrate.sh` Container-Name via `${POSTGRES_CONTAINER:-infra-postgres}`                        | ✅     | B8   |
| 9  | `new-service.sh` erweitert: `--schema=`, `--port=`, `--prefix=`, `--token-prefix=`, `--desc=` | ✅     | B10  |
| 10 | `new-service.sh` Schema-Suffix-Validation gegen `_svc` (kein doppelter `_svc_svc`)             | ✅     | B11  |
| 11 | `new-service.sh` Description-Warnung statt stillem Default                                     | ✅     | B5   |
| 12 | `_optional/auth/migration.sql` analog ip-pool-api 002+005 (api_keys + auth_failures + outbox)  | ✅     |      |
| 13 | `--with-auth` Opt-in kopiert + substituiert die Auth-Migration korrekt                         | ✅     |      |
| 14 | Token-Prefix-Validation `^[a-z]{2,4}$`                                                          | ✅     |      |
| 15 | Token-Prefix-Reserve-Registry in `_optional/auth/README.md`                                    | ✅     |      |
| 16 | `bash -n` syntax-clean + `shellcheck` clean                                                    | ✅     |      |
| 17 | Negative-Tests: Args-Validation greift bei missing/invalid args                                | ✅     |      |
| 18 | Happy-Path-Test (Flag-Form, with-auth, demo-svc) — alle Substitutionen korrekt                 | ✅     |      |
| 19 | Backward-Compat-Test (positional Form, ip-pool-api-Stil)                                       | ✅     |      |
| 20 | CHANGELOG-Eintrag 2026.05.02 mit Added/Fixed/Note/Pinned-by                                    | ✅     |      |
| 21 | git tag 2026.05.02 (signed)                                                                    | 🟡     | folgt nach diesem Report |
| 22 | `src/plugins/metrics.ts` Wiring-Stub (prom-client, opt-in via Uncomment)                       | ✅     | B7 — Folge-Iteration des port-registry-Auftrags |
| 23 | `src/plugins/openapi.ts` Wiring-Stub (swagger + zod-type-provider, opt-in)                     | ✅     | B7 |
| 24 | `app.ts` mit auskommentierten Imports + Hinweis "Uncomment to enable"                          | ✅     | B7 |
| 25 | Metric-Name-Prefix nutzt `__DB_SCHEMA__` statt `__SERVICE_NAME__` (Prometheus-Spec-konform)    | ✅     | B13 — beim Re-Test mit `test-foundation` entdeckt |
| 26 | `infra-postgres/scripts/add-service-schema.sh` (idempotent Schema+User)                        | ✅     | B9 (Teil) — companion-change in infra-postgres v0.1.3 |
| 27 | `new-service.sh` Operator-TODO referenziert `add-service-schema.sh`                            | ✅     | Password via env/stdin, nicht CLI-arg |
| 28 | `infra-postgres/init/01-init.sh` Kommentar-Patch zeigt auf `add-service-schema.sh`             | ✅     | v0.1.3 |
| 29 | `infra-postgres@v0.1.3` Tag (annotated)                                                        | ✅     | lokal, nicht gepusht |
| 30 | `--dry-run` Flag im `new-service.sh` (no git/commit, rm -rf am Ende)                           | ✅     | mit defensivem Pfad-Guard |
| 31 | Schema-Default in `new-service.sh` (kebab → snake)                                             | ✅     | port-registry → port_registry |
| 32 | `PRINCIPLES.md` Auth-Layer-Pattern Sektion (argon2id-Erläuterung)                              | ✅     | B12 |
| 33 | `_optional/auth/PREFIX-REGISTRY.md` als globale Token-Prefix-Reserve                           | ✅     | inkl. iplk_ Initial-Eintrag |
| 34 | `templates/service-skeleton/AGENTS.md` referenziert PREFIX-REGISTRY.md                         | ✅     | Operator-Pflicht |
| 35 | Token-Prefix Hint-Output bei `--with-auth` ohne `--prefix`                                     | ✅     | kein stiller Default — Sicherheits-Smell vermieden |
| 36 | Pre-Push-Scan auf Hostnames + IPs (api-standards + infra-postgres)                             | ✅     | clean — keine non-loopback IPs, keine BBE-DBE-Hostnames |
| 37 | Re-Test `test-foundation` echte Bootstrap (kein /tmp) + cleanup                                | ✅     | 6 Tests, alle grün |

## 14-Dimensionen-Selbstcheck (für die geänderten Skeleton-Files + Skript-Erweiterungen)

| Dim | Status | Lücke |
|-----|--------|-------|
| 1 Sicherheit          | ✅ | Auth-Template enthält argon2id, brute-force-counter, scope-array, revocation. PREFIX-REGISTRY verhindert Token-Prefix-Kollisionen. `add-service-schema.sh` Password via env/stdin/silent-prompt — niemals CLI-Arg. `--dry-run` mit defensivem Pfad-Guard (rm nur unter `$HOME/projects`). Keine Secrets im Repo. |
| 2 Korrektheit         | ✅ | Schema-Suffix-Guard, Prefix-Regex, Idempotenz aller Migrations (IF NOT EXISTS). Schema-Default deterministisch (kebab → snake). `--dry-run` und Real-Run liefern identische Substitutionen. |
| 3 Performance         | ✅ | Indexe auf api_keys (partial WHERE revoked_at IS NULL), auth_failures (first_fail_at), outbox (partial WHERE pending). Histogram-Buckets in metrics.ts manuell gewählt (nicht prom-client-Default). |
| 4 Effizienz           | ✅ | `_optional/`-Folder rsync-excluded → bare service ohne Auth/Plugins minimal. plugins/ ist opt-in via Uncomment, kein Bundle-Bloat. |
| 5 Modularität         | ✅ | Auth ist opt-in via `--with-auth`, Plugins via Uncomment, Schema-per-Service-Konvention. |
| 6 Kompatibilität      | ✅ | additive: positional-Form bleibt funktional, Flag-Form parallel; OpenAPI-3.1-Stub als Fallback. |
| 7 Skalierbarkeit      | ✅ | auth_failures cluster-shared (DB), nicht in-process. Sweeper-Lock-Pattern (advisory_lock) in skeleton-Hinweisen. |
| 8 Observability       | ✅ | Wiring-Stub `src/plugins/metrics.ts` registriert default-metrics + service-spezifische http-histogram + error-counter; `__DB_SCHEMA__`-Prefix garantiert Prometheus-Spec-Konformität (B13-Fix). |
| 9 Code-Qualität       | ✅ | bash strict-mode, shellcheck clean (außer suppressed SC1091 für `.env`-source). Alle Args validiert mit Regex. TypeScript-Stubs strict mode, kein `any`. |
| 10 Compliance         | ✅ | Author/Date/Commit-Header in Migration-Templates. ISO-27001-Pointer in STANDARDS.md. SBOM-Generator (`cdxgen`) in package.json. |
| 11 Operations         | ✅ | Operator-TODOs explizit nach Bootstrap; Container-Override in migrate.sh; `add-service-schema.sh` re-run rotiert Passwort deliberat; 01-init.sh Kommentar-Patch zeigt Migration-Pfad. |
| 12 Dokumentation      | ✅ | CHANGELOG-Eintrag, Status-Report, README in `_optional/auth/`, PRINCIPLES Auth-Layer-Pattern, PREFIX-REGISTRY mit Operator-Pflicht-Block. AGENTS.md zeigt Registry-Pflicht. |
| 13 Agent-Tauglichkeit | ✅ | Skript-Output parseable, Validation-Errors machine-readable mit klaren Hint-Outputs (Token-Prefix-Hint nennt Suggestion + Override). PREFIX-REGISTRY ist agent-konsumierbar mit "How an agent uses this"-Sektion. |
| 14 Lebenszyklus       | ✅ | Tag immutable (lokal vor Push); bestehende Services (ip-pool-api, infra-postgres) nicht betroffen außer additive companion-change v0.1.3. Token-Prefix-Retirement-Convention in PREFIX-REGISTRY (90-day cooldown). |

## Mess-Daten

- **shellcheck-Lauf:** clean (0 Warnings; nur SC1091 info-level für `.env`-source, suppressed)
- **`bash -n` Lauf:** clean (alle 3 Skripte: new-service.sh, add-service-schema.sh, migrate.sh)
- **Negative-Tests:** 4/4 (api-standards) + 3/3 (infra-postgres) — usage, invalid port/schema, prefix-regex, with-auth-ohne-prefix, password-too-short
- **Happy-Path-Tests:** 6/6
  - Test 1: `--dry-run` leaves no leftover ✅
  - Test 2: real bootstrap → all substitutions correct, plugins/ + 001_init mit update_updated_at ✅
  - Test 3: B13-fix verified — metric names snake_case (Prometheus-konform) ✅
  - Test 4: `--with-auth` ohne `--prefix` → Hint mit Registry-Pointer + exit 2 ✅
  - Test 5: Schema-Default greift (test-foundation → test_foundation) ✅
  - Test 6: full real bootstrap + cleanup ✅
- **Pre-Push-Scan:** keine non-loopback-IPs, keine BBE-DBE-Hostnames, keine Secrets in beiden Repos
- **Skript-Größe:** new-service.sh ~245 Zeilen (vs. 113 vor Patch — +132%; Aufpreis für Flag-Parser, --with-auth, --dry-run, Schema-Default, Token-Prefix-Hint)

## Trade-offs

- **B7 Wiring-Stubs als `src/plugins/{metrics,openapi}.ts` statt `_optional/`-Folder.** Begründung: opt-in via Uncomment ist intuitiver als Flag, dependencies sind im Skeleton-`package.json` schon gepinnt. Bei Skeleton-Operator-Bedarf trivial einkommentierbar. Code-Footprint für nicht-aktive Plugins ist tot, aber dead-code-tree-shaking entfernt sie aus dem build wenn nicht importiert (TS strict mode mit `noUnusedLocals` würde es flaggen, aber das ist ok für Stubs).
- **Kein stiller Token-Prefix-Default.** Diskutiert mit Operator: erste-3-chars als Default eingeführt → Risiko Kollisions-Smell (z.B. zwei Services beginnend mit `port-*` würden beide `por_` wählen). Stattdessen: explicit-required, Hint-Output mit Suggestion + Registry-Pointer. Operator entscheidet bewusst. → 14-Dim §1 Sicherheit.
- **`_optional/auth/`-TS-Code nicht generiert.** Auth-Logik (`auth.ts`) hat genug service-spezifisches Judgment (Scope-Vokabular, Cache-Strategie, Audit-Verb), dass eine generische `.ts.tpl` entweder zu rigid oder zu generisch wäre. README im Auth-Optional zeigt expliziten Verweis auf ip-pool-api als Reference-Implementation.
- **`add-service-schema.sh` in infra-postgres v0.1.3 (companion-change).** Begründung: gehört zur Skeleton-Foundation für ALLE künftigen Services. Operator-TODO-Block in `new-service.sh` referenziert es jetzt direkt; ein Bootstrap braucht damit nur zwei Operator-Zeilen (DB-Provisioning + Skeleton-Generierung). Password-Input via env/stdin/prompt — niemals CLI-Arg (shell-history-Leak vermieden). Re-run rotiert das Passwort (deliberate non-idempotency, dokumentiert).
- **Backward-Compat zu positional-Form bewusst beibehalten.** Entfernen wäre Breaking; existierende Aufrufe in evtl. CI-Skripten würden brechen.

## Tech-Debt (für 2026.05.0X)

| Punkt                                                                          | Schwere | Empf. Zeitpunkt |
|--------------------------------------------------------------------------------|---------|-----------------|
| `_optional/auth/auth.ts.tpl` (full TS port von ip-pool-api) — wenn 2. Service Auth braucht | mittel | 2026.05.0X |
| `new-service.sh` ruft `add-service-schema.sh` direkt auf (statt Operator-TODO) | klein   | bewusst Operator-Step für Sicherheits-Sichtprüfung |
| PREFIX-REGISTRY → CI-Validation gegen Doppelvergabe (GH Action mit yamllint-Style-Check) | klein | opportunistisch |
| Skeleton-Bootstrap-Test als CI-Job (`--dry-run` + Negative-Tests + Happy-Path) | mittel  | 2026.05.0X |
| `bootstrap-key.sh` + `bootstrap-key.mjs` als opt-in im `_optional/auth/` ergänzen | klein | sobald 2. auth-Service kommt |
| `release.sh` clean-tree + semver-bump + tag im Skeleton noch nicht patched     | klein   | 2026.05.0X |

## Optimierungs-Backlog (Stufe C)

| Hotspot                                          | Vorschlag                                              | Aufwand | Erwartet | Risiko |
|--------------------------------------------------|--------------------------------------------------------|---------|----------|--------|
| `new-service.sh` — keine post-Bootstrap-Tests    | smoke: pnpm install + tsc + vitest minimal direkt nach git init | M    | grundsätzlich validiert wirklich-funktionierender Bootstrap | mittel — pnpm install dauert evtl. >30s, würde new-service.sh-Lauf verlängern |
| `_optional/`-Mechanismus skaliert nicht über drei Opt-Ins | Refactor zu opt-in-manifest (yaml mit Kopier-Regeln) | L | Viele kleine Opt-Ins ohne Skript-Bloat | mittel — extra Komplexität wenn am Ende nur 2-3 Opt-Ins existieren |
| Token-Prefix-Validation nur lokal in new-service.sh | Eigene Funktion `validate-token-prefix.sh` mit registry-check | S | Fehler vor Skript-Lauf | klein |

## Verschoben aus dem ursprünglichen rc1-Auftrag (NICHT in 2026.05.02)

- **port-registry-Bootstrap** — komplett verschoben, weil die Frontend-
  Architektur neu entschieden wird (separate Plattform für sign.it-CI +
  Dashboard-Shell + UI-Tokens, mit White-Label-Fähigkeit). Die hier
  gefixten Skeleton-Patches sind unabhängig nutzbar und blockieren den
  port-registry-Service nicht — der profitiert sogar (kann den Flag-Form-
  Bootstrap und das Auth-Opt-in nutzen, sobald das Frontend-Setup
  geklärt ist).
- ~~**infra-postgres `add-service-schema.sh`**~~ — doch in 2026.05.02
  geliefert (companion-change in infra-postgres v0.1.3), siehe oben.

## Erkenntnisse für künftige Skeleton-Validierungen

1. Ein "Skeleton-Test" mit einem **realen** Service-Namen (test-foundation)
   deckt Bug-Klassen auf, die ein synthetischer Test nie zeigt:
   - B5 (Description-Default — wirkliche Werte sind hässlich)
   - B11 (Schema-Suffix — Konventions-Kollision mit PGUSER)
   - **B13 (Hyphen-Service-Namen brechen Prometheus-Spec)** — erst durch
     den Re-Test mit `test-foundation` aufgefallen, weil das Schema
     `test_foundation` heißt aber der Service-Name `test-foundation`.
     Die `tmp`-Dir-Approach allein hätte das nicht zuverlässig gezeigt
     (Naming-Konvention mit underscore wäre passable durchgeflutscht).
   → **`--dry-run` ersetzt nicht das Echte-`~/projects`-Re-Test**, weil
   manche Probleme erst beim Inspect des wirklichen Layouts sichtbar
   werden. Beide Workflows behalten.
2. Operator-TODO-Block im Skript-Output ist wertvoller als Auto-Magic.
   Ein Skript, das `gh repo create` selbständig ausführt, kann Repos
   im falschen Account anlegen oder mit falscher Sichtbarkeit. Der
   Operator soll den vorgefertigten Befehl sehen und absegnen.
3. `_optional/`-Folder mit rsync-exclude + `src/plugins/` mit Uncomment
   sind ZWEI ergänzende Opt-In-Mechanismen mit unterschiedlichen
   Trade-offs:
   - `_optional/`: für Migrations + große Files (kein Bundle-Footprint
     wenn nicht aktiviert).
   - `src/plugins/` mit Uncomment: für TS-Plugins (Footprint nur als
     ungelesene Datei; tree-shaking entfernt bei Build).
   Beide haben ihren Platz; ein Manifest-Refactor wird unnötig wenn
   die Anzahl der Opt-Ins gering bleibt.
4. Ein zentrales Registry-File (PREFIX-REGISTRY.md) für globale
   Reserven ist robuster als pro-Service-Tabellen. Operator-Pflicht
   muss in **mehrfachen** Stellen verlinkt sein (Skeleton-AGENTS.md,
   _optional/auth/README.md, new-service.sh-Hint-Output, Pre-Commit-
   Hook in Tech-Debt), sonst wird die Registry vergessen.
