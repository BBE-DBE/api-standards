# STATUS-REPORT — api-standards 2026.05.02

```
Service:  api-standards (Skeleton-Patch-Subset)
Version:  2026.05.02
Auftrag:  Skeleton-Bugs B1–B11 fixen + new-service.sh erweitern + 002_auth-Template
Datum:    2026-05-02
Kontext:  Subset des port-registry-rc1-Auftrags. Die Service-Implementation
          wurde verschoben (Frontend-Architekturentscheidung); die hier
          gefixten Skeleton-Patches sind aber unabhängig nutzbar.
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
| 22 | `_optional/`-Wiring-Snippets für metrics + swagger                                             | ❌     | B7 — geplant für nächste calver |
| 23 | `infra-postgres/scripts/add-service-schema.sh` (idempotent Schema+User)                        | ✅     | B9 (Teil) — companion-change in infra-postgres v0.1.3 |
| 24 | `new-service.sh` Operator-TODO referenziert `add-service-schema.sh`                            | ✅     | Password via env/stdin, nicht CLI-arg |

## 14-Dimensionen-Selbstcheck (für die geänderten Skeleton-Files)

| Dim | Status | Lücke |
|-----|--------|-------|
| 1 Sicherheit          | ✅ | Auth-Template enthält argon2id, brute-force-counter, scope-array, revocation. Keine Secrets im Repo. |
| 2 Korrektheit         | ✅ | Schema-Suffix-Guard, Prefix-Regex, Idempotenz der Migration (IF NOT EXISTS). |
| 3 Performance         | ✅ | Indexe auf api_keys (key_id, partial WHERE revoked_at IS NULL), auth_failures (first_fail_at), outbox (next_attempt_at, partial WHERE pending). |
| 4 Effizienz           | ✅ | `_optional/`-Folder rsync-excluded → bare service bleibt minimal. |
| 5 Modularität         | ✅ | Auth ist opt-in, Schema-per-Service-Konvention bleibt.  |
| 6 Kompatibilität      | ✅ | additive: alte positional-Form bleibt funktional. |
| 7 Skalierbarkeit      | ✅ | auth_failures ist cluster-shared (DB-Tabelle), nicht in-process. |
| 8 Observability       | ➖ | Skeleton-Patch berührt keine Logging/Metrics-Pfade. |
| 9 Code-Qualität       | ✅ | shellcheck clean, bash-strict-mode, alle Args validiert. |
| 10 Compliance         | ✅ | Author/Date/Commit-Header in Migration-Template. ISO-27001-Pointer in STANDARDS.md. |
| 11 Operations         | ✅ | Operator-TODOs explizit nach Bootstrap; Container-Override in migrate.sh. |
| 12 Dokumentation      | ✅ | CHANGELOG-Eintrag, status-report, README in `_optional/auth/`. |
| 13 Agent-Tauglichkeit | ✅ | Skript-Output ist parseable, Validation-Errors sind machine-readable. |
| 14 Lebenszyklus       | ✅ | Tag immutable; bestehende Services (ip-pool-api) nicht betroffen. |

## Mess-Daten

- **shellcheck-Lauf:** clean (0 Warnings)
- **`bash -n` Lauf:** clean
- **Negative-Tests:** 4/4 — usage, invalid port, invalid prefix, --with-auth ohne --prefix
- **Happy-Path:** demo-svc bootstrappt, 002_auth.sql substituiert mit `demo` + `dem_`, keine `__PLACEHOLDER__`-Reste
- **Skript-Größe:** new-service.sh 188 Zeilen (vs. 113 vor Patch — +66%, Aufpreis für Flag-Parser + opt-in-Logik)

## Trade-offs

- **Kein voller `_optional/`-Folder mit metrics + swagger im Patch.** Begründung: erste Generalisierung erfordert mind. zwei Service-Bootstraps für klares Pattern. Aktuell nur ip-pool-api als Datenpunkt; port-registry verschoben. → action-item B7.
- **`_optional/auth/`-TS-Code nicht generiert.** Auth-Logik (`auth.ts`) hat genug service-spezifisches Judgment (Scope-Vokabular, Cache-Strategie, Audit-Verb), dass eine generische `.ts.tpl` entweder zu rigid oder zu generisch wäre. README im Auth-Optional zeigt expliziten Verweis auf ip-pool-api als Reference-Implementation.
- **`add-service-schema.sh` in infra-postgres v0.1.3 (companion-change).** Begründung: gehört zur Skeleton-Foundation für ALLE künftigen Services. Operator-TODO-Block in `new-service.sh` referenziert es jetzt direkt; ein Bootstrap braucht damit nur zwei Operator-Zeilen (DB-Provisioning + Skeleton-Generierung). Password-Input via env/stdin/prompt — niemals CLI-Arg (shell-history-Leak vermieden). Re-run rotiert das Passwort (deliberate non-idempotency, dokumentiert).
- **Backward-Compat zu positional-Form bewusst beibehalten.** Entfernen wäre Breaking; existierende Aufrufe in evtl. CI-Skripten würden brechen.

## Tech-Debt (für 2026.05.0X)

| Punkt                                                                          | Schwere | Empf. Zeitpunkt |
|--------------------------------------------------------------------------------|---------|-----------------|
| `_optional/metrics/metrics.ts` + `_optional/swagger/register.ts` Templates     | mittel  | 2026.05.0X      |
| `_optional/auth/auth.ts.tpl` (full TS) — wenn 2. Service Auth braucht           | mittel  | 2026.05.0X      |
| `new-service.sh` ruft `add-service-schema.sh` direkt auf (statt Operator-TODO) | klein   | 2026.05.0X — bewusst Operator-Step für Sicherheits-Sichtprüfung |
| Token-Prefix-Reserve-Registry → CI-Validation gegen Doppelvergabe              | klein   | opportunistisch |
| Skeleton-Bootstrap-Test als CI-Job (`tmp`-dir + Negative-Tests + Happy-Path)   | mittel  | 2026.05.0X      |

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

1. Ein "Skeleton-Test" mit einem **realen** Service deckt Bug-Klassen
   auf, die ein synthetischer Test nie zeigt (B5 Description-Default,
   B11 Schema-Suffix). Die `tmp`-Dir-Approach in den negativen Tests
   sollte CI-Standard werden (Tech-Debt #5).
2. Operator-TODO-Block im Skript-Output ist wertvoller als Auto-Magic.
   Ein Skript, das `gh repo create` selbständig ausführt, kann Repos
   im falschen Account anlegen oder mit falscher Sichtbarkeit. Der
   Operator soll den vorgefertigten Befehl sehen und absegnen.
3. `_optional/`-Folder mit rsync-exclude ist eine saubere Lösung für
   Opt-Ins, solange die Anzahl klein bleibt. Bei >3 Opt-Ins braucht es
   ein Manifest (siehe Optimierungs-Backlog).
