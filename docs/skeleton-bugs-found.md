# Skeleton-Bugs — Befunde aus port-registry-Bootstrap

> Dieses Dokument trackt **Bugs und Lücken**, die beim ersten echten
> Bootstrap eines Services aus `templates/service-skeleton/` gefunden
> wurden. Jede Zeile ist ein **Action-Item**, kein Eintrag im Tagebuch.
>
> Status-Konvention:
> - **fixed-in <calver>**: behoben in genannter calver-Version
> - **action**: noch offen, Verantwortlicher + ETA
> - **wontfix**: bewusst nicht behoben, Begründung
>
> Erfasst: 2026-05-01 · Validierender Service: port-registry · Validator: Claude Opus 4.7 (1M)

---

## B1 — Leere YAML/SQL-Stubs unter `templates/`

**Befund:** `templates/audit-event-schema.yaml`, `error-codes.yaml`,
`health-response-schema.yaml`, `migration-header.sql`,
`openapi-skeleton.yaml` sind **0 Bytes**. Die echten Inhalte leben unter
`protocols/` (für YAMLs). `migration-header.sql` und
`openapi-skeleton.yaml` haben **keinen** kanonischen Ort sonst.

**Risiko:** Agenten, die einem Pointer auf `templates/audit-event-schema.yaml`
folgen, finden eine leere Datei und verlieren Zeit. SHA-Drift-Prüfungen
auf leere Templates schlagen Alarm.

**Action:** fixed-in 2026.05.02 — leere Stubs werden mit Pointer-Kommentar
auf die kanonische Quelle gefüllt; `migration-header.sql` und
`openapi-skeleton.yaml` werden mit minimalem brauchbaren Inhalt befüllt
(Migration-Header-Konvention; OpenAPI-3.1-Stub).

## B2 — Leere `PRINCIPLES.md` + `STANDARDS.md` im Root

**Befund:** Beide Dateien sind 0 Bytes auf Root-Ebene des api-standards-Repos.
Die ausgefüllten Versionen sind im **Skeleton** (für Services). Inkonsistenz.

**Risiko:** Repo wirkt unfertig; Cross-Refs aus Service-`STANDARDS.md`
(`see ../api-standards/STANDARDS.md`) zeigen ins Leere.

**Action:** fixed-in 2026.05.02 — Root-Versionen werden mit Pointer auf
`workflows/agent-prompt-prefix.md`, `checklists/14-dimensions.md` und
`iso-mappings/27001-controls.md` befüllt.

## B3 — `docs/`-Verzeichnis fehlt

**Befund:** Brief erwartet `~/projects/api-standards/docs/skeleton-bugs-found.md`
und `docs/status-reports/`. Beide Verzeichnisse existieren nicht.

**Risiko:** keine; Pfad wird beim ersten Schreiben angelegt.

**Action:** fixed-in 2026.05.02 — `docs/` und `docs/status-reports/`
werden mit Inhalt angelegt (diese Datei + erste Status-Reports).

## B4 — `update_updated_at()`-Trigger-Funktion fehlt im Skeleton

**Befund:** Skeleton-`db/migrations/001_init.sql` legt Schema, Events,
Idempotency-Keys an, aber **keine** generische `update_updated_at()`-
Trigger-Funktion. Jede Folge-Migration mit `updated_at`-Spalte muss die
Funktion entweder selbst definieren oder sie aus einem nicht-existenten
Skeleton-Helper importieren.

**Risiko:** mittel — jeder Service kopiert/dupliziert die Funktion
oder vergisst sie. State-Drift.

**Action:** fixed-in 2026.05.02 — Funktion wird in
`db/migrations/001_init.sql` ergänzt:

```sql
CREATE OR REPLACE FUNCTION __DB_SCHEMA__.update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END $$;
```

**Drift-Hinweis:** Der Patch ändert den SHA-256 von `001_init.sql`. Services,
die das alte 001 schon angewandt haben (z.B. ip-pool-api), sind **nicht
betroffen**, weil ihr eigenes 001 anders aussieht. Nur Services, die nach
2026.05.01 mit dem **leeren** 001-Template gestartet sind, müssten die
Funktion nachpatchen — bislang gibt es keine.

## B5 — `__SERVICE_DESC__`-Default suboptimal

**Befund:** Wenn der Operator `bash new-service.sh foo bar 5300` (ohne
4. Arg) aufruft, wird die description zu `foo (description pending)`,
und dieser Text landet in `package.json.description`,
`openapi.info.description`, `README.md`-Quickstart usw.

**Risiko:** klein — kosmetisch.

**Action:** fixed-in 2026.05.02 — Default ist leer; Skript warnt
"description nicht gesetzt — Operator muss README/PRINCIPLES selbst
befüllen".

## B6 — Doppeltes `AGENTS.md`-Pointer-Layer

**Befund:** Skeleton-`AGENTS.md` zeigt auf
`~/projects/api-standards/workflows/agent-prompt-prefix.md`. Die
Existenz dieser Datei ist OK, aber der absolute Pfad (`~/projects/...`)
ist host-spezifisch.

**Risiko:** klein — auf nicht-BBE-Hosts (CI?) bricht der Pointer.

**Action:** wontfix für 2026.05.02 — agent-first Konvention; CI nutzt
`gh repo clone BBE-DBE/api-standards` als Fallback (siehe Skeleton-AGENTS-Schritt 1).

## B7 — Tote Skeleton-Dependencies

**Befund:** `package.json` listet `prom-client`, `@fastify/swagger`,
`@fastify/swagger-ui`, `argon2`, `yaml` — aber `app.ts` importiert
keinen davon. Bootstrap-Service ohne Wiring ist ein leerer Health-Server.

**Risiko:** klein — verwirrend; "warum ist das im lockfile?"-Frage.
Build-Zeit + Bundle-Footprint leicht aufgeblasen.

**Action (open):** `templates/service-skeleton/_optional/wiring-snippets/`
mit fertigen Code-Bausteinen (metrics.ts, swagger.ts, auth.sql, auth.ts),
die per `--with-metrics`, `--with-swagger`, `--with-auth` in
`new-service.sh` opt-in sind. **Geplant für nächste calver, nicht
2026.05.02.** Begründung: erste Generalisierung erfordert mind. zwei
Service-Bootstraps, um Snippets von port-registry-spezifischer Logik
zu trennen. port-registry baut Auth/Metrics/Swagger zunächst direkt im
Service-Repo (auf Basis ip-pool-api), und der `_optional/`-Folder kommt
in calver `2026.05.0X`, sobald ein zweiter Service mit derselben
Anforderung auftaucht.

## B8 — `scripts/migrate.sh` Container-Name hardcoded

**Befund:** `scripts/migrate.sh:14` setzt `CONTAINER="infra-postgres"`.
Wenn der Operator den Container umbenennt, schlägt jede Migration fehl.

**Risiko:** klein — bislang heißt der Container überall so.

**Action:** fixed-in 2026.05.02 — `CONTAINER="${POSTGRES_CONTAINER:-infra-postgres}"`.

## B9 — `new-service.sh` macht weder GitHub-Repo, noch Schema, noch PM2

**Befund:** Der Brief des port-registry-Bootstraps fragte explizit "Wird
Repo auf GitHub angelegt? Wird Postgres-Schema angelegt? Wird PM2-Eintrag
generiert?". Antwort laut Skript-Kommentar `new-service.sh:17`: NEIN. Die
drei Schritte sind **operator-TODOs** im Output.

**Risiko:** mittel — der Skript-Auftrag "bootstrappe einen Service" wird
nur halbherzig erfüllt; jeder Operator muss drei Folge-Befehle manuell
ausführen, fehleranfällig.

**Action:** Teil-fixed-in 2026.05.02 —
- `infra-postgres/scripts/add-service-schema.sh` (companion-change in
  infra-postgres v0.1.3): idempotent, schafft Schema + Service-User in
  einem Schritt. Password via `SVC_PASSWORD` env / stdin / interactive
  silent prompt — niemals als CLI-Arg, sonst Shell-History-Leak.
  Re-Run rotiert deliberat das Passwort.
- `new-service.sh` Operator-TODO-Block referenziert `add-service-schema.sh`
  jetzt explizit als Schritt 1; Schritt 3 (GitHub-Repo) und 4 (PM2-Start)
  zeigen den **fertigen Befehl** zum Copy-Paste.
- GitHub-Repo + PM2 bleiben **bewusst** Operator-Schritte (Auth/Sicherheit:
  ein Skript darf nicht autonom `gh repo create` für ein Konto laufen
  lassen, wenn der Operator den Namen oder die Sichtbarkeit ändern will).

## B13 — `__SERVICE_NAME__` in Prometheus-Metric-Name verletzt Spec

**Befund:** Erste Version von `templates/service-skeleton/src/plugins/metrics.ts`
nutzte `__SERVICE_NAME___http_request_*` als Metric-Name. Prometheus
fordert `[a-zA-Z_:][a-zA-Z0-9_:]*` — also keine Hyphens. Bei einem
Service-Namen wie `test-foundation` ergäbe die Substitution
`test-foundation_http_request_*` und Prometheus würde den Namen
ablehnen (oder schlimmer: das prom-client-Lib akzeptiert ihn lokal,
aber Server-side-Scraper brechen ein).

**Risiko:** mittel — die Library prom-client validiert Namen erst beim
Registrieren; lokaler Build wirft, aber wer den Skeleton ohne erste
Test-Registrierung deployt, sieht das Problem erst in Prod.

**Action:** fixed-in 2026.05.02 — Metric-Name-Prefix verwendet
`__DB_SCHEMA__` (per Validation snake_case) statt `__SERVICE_NAME__`.
Konventions-Kommentar im File ergänzt.

## B11 — Schema-Suffix `_svc` kollidiert mit PGUSER-Konvention

**Befund:** `.env.example` setzt `PGUSER=__DB_SCHEMA___svc`. Sed
substituiert `__DB_SCHEMA__` global. Wenn das Schema selbst auf `_svc`
endet (z.B. `foo_svc`), wird PGUSER zu `foo_svc_svc` — doppelter Suffix.

Bei den real verwendeten Schemas (`ip_pool`, `port_registry`, `netcup`,
`adam_eve`) tritt das **nicht** auf. Trotzdem defensiv abfangen.

**Risiko:** klein — nur bei pathologischer Schema-Wahl.

**Action:** fixed-in 2026.05.02 — `new-service.sh` lehnt Schemas ab,
die auf `_svc` enden. Fehlermeldung erklärt die Kollision.

## B10 — `--prefix=`-Flag im Brief, aber nicht im Skript

**Befund:** Brief des port-registry-Bootstraps:
`bash new-service.sh port-registry --port=5300 --schema=port_registry --prefix=prr`.
Skript akzeptiert nur positional-Args, kein `--`-Flag, kein `--prefix`.
Würde mit "usage" fehlschlagen.

**Action:** fixed-in 2026.05.02 — Flag-Parser unterstützt jetzt **beide**
Formen:

```bash
# alt (positional, bleibt funktional):
bash new-service.sh netcup-api netcup 5360 "Netcup adapter"

# neu (Flags, optional):
bash new-service.sh port-registry \
  --schema=port_registry --port=5300 \
  --token-prefix=prr --with-auth --with-metrics --with-swagger \
  --desc="Single Source of Truth für Server-Ports"
```

Token-Prefix-Validierung: `^[a-z]{2,4}$` (analog `iplk`, `prr`).

---

## B14 — `pnpm tsc --noEmit` schlägt standalone fehl (gitignored generated import)

**Befund:** `src/lib/build-version.ts` macht
`await import('./git-sha.js')`. Die Datei `src/lib/git-sha.ts` ist
**gitignored** und wird erst von `scripts/build.sh` zur Build-Zeit
generiert. Folge: ein frisch geclontes Repo kann `pnpm tsc --noEmit`
nicht ausführen — der TypeScript-Modulauflöser findet `./git-sha.js`
nicht und bricht mit `TS2307` ab. `pnpm build` (das build.sh aufruft)
funktioniert, ist aber kein reiner Typecheck mehr.

Reproduktion (am 2026-05-01 in port-registry):
```
$ pnpm tsc --noEmit
src/lib/build-version.ts(27,30): error TS2307:
  Cannot find module './git-sha.js' or its corresponding type declarations.
```

**Risiko:** CI-Jobs, die `tsc --noEmit` als Quality-Gate fahren (typischer
Lint-Step), schlagen vor dem ersten `pnpm build` immer fehl. Agenten
folgen dem Plan-Validation-Step "tsc --noEmit grün" und müssen ad-hoc
auf `pnpm build` ausweichen.

**Action:** `build-version.ts` umbauen so, dass `git-sha.ts` rein
runtime-conditional gelesen wird (z.B. via `process.env.GIT_SHA` als
Primärquelle und `fs.readFileSync('./git-sha.json')` JSON-Datei statt
TS-Modul). Alternative: ein `src/lib/git-sha.ts.template` mit
`export const GIT_SHA = 'unknown';` als Fallback ins Repo einchecken
(nicht gitignored), das build.sh überschreibt. ETA 2026.05.0X.

---

## B15 — `AGENTS.md`-Pin-Floor wird beim Bootstrap nicht auf aktuellen calver substituiert

**Befund:** Frisch gebootstraptes `port-registry/AGENTS.md` enthält
*literal*: "Pinned standards version: **>= 2026.04.30** (or whatever the
current calver is on the day this skeleton was generated)." — der
Klammer-Hinweis bestätigt, dass die Substitution gewollt ist, aber
`new-service.sh` führt sie nicht durch. Der Wert `2026.04.30` ist im
Skeleton-Source hartkodiert und altert.

Reproduktion: Bootstrap am 2026-05-01 (api-standards-Tag `2026.05.02` aktiv) ⇒
AGENTS.md zeigt weiterhin `>= 2026.04.30`. Erwartet wäre `>= 2026.05.02`
(höchster im Source-Repo erreichbarer Tag) oder `>= <current calver>`.

**Risiko:** Reproduzierbarkeit-Lücke. Ein Agent, der den Pin liest,
glaubt der Service sei kompatibel mit allem ab 2026.04.30, obwohl die
Foundation bei der Generierung bereits einen jüngeren, schärferen Tag
verlangt hätte. Drift zwischen Pin-Floor und tatsächlich genutzter
Foundation-Version.

**Action:** `new-service.sh` substituiert `__STANDARDS_PIN_FLOOR__` o.ä.
gegen `git -C <skeleton-source> describe --tags --abbrev=0` zur
Bootstrap-Zeit. Optional zusätzlich eine Datei
`.api-standards-version` mit dem exakten Tag schreiben (für
Drift-Checks). ETA 2026.05.0X.

---

## Tooling-Beobachtung (kein Skeleton-Bug, infra-postgres) — Naming-Drift in `add-service-schema.sh`

**Befund:** `infra-postgres@v0.1.3 scripts/add-service-schema.sh`
liest `POSTGRES_USER` und `POSTGRES_PASSWORD` aus `.env`, aber das
gepflegte `~/projects/infra-postgres/.env` (Stand 2026-05-01) definiert
**stattdessen** `POSTGRES_SUPER_USER` / `POSTGRES_SUPER_PASSWORD`.
Folge: ohne explizite Subshell-Umbenennung exit 1 mit
*"POSTGRES_PASSWORD not in env or .env — cannot connect as superuser"*.

Workaround beim port-registry-Bootstrap (2026-05-01):
```
( cd ~/projects/infra-postgres
  set -a; . ./.env; set +a
  export POSTGRES_USER="$POSTGRES_SUPER_USER"
  export POSTGRES_PASSWORD="$POSTGRES_SUPER_PASSWORD"
  SVC_PASSWORD=... bash scripts/add-service-schema.sh ... )
```

**Action (infra-postgres-Repo, nicht api-standards):** Naming
vereinheitlichen — entweder Script auf `POSTGRES_SUPER_*` umstellen
oder `.env` auf `POSTGRES_USER`/`POSTGRES_PASSWORD` umbenennen. Der
zweite Weg kollidiert weniger mit Postgres-Container-Defaults. Kein
api-standards-Fix nötig; nur hier dokumentiert weil's die nächste
Bootstrap-Welle blockiert hätte.

---

## Zukünftige Bug-Klassen, die wir hier tracken

Wenn beim Bootstrap eines neuen Service **weitere** Lücken auffallen:

1. Eintrag mit nächster B-Nummer hier ergänzen.
2. Action-Item ins nächste calver-Tag.
3. Bug-Reproduktion in `examples/`-Snapshot, falls nicht-trivial.

**Validierungs-Pflicht:** Jeder neue Service muss mind. einmal vom
Skeleton aus generiert werden, **bevor** er in PR/Tag-Pipeline geht.
Wenn der Bootstrap eine "echte" Skeleton-Lücke offenlegt, landet sie hier.
