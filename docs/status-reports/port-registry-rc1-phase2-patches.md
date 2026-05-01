# port-registry rc1 — Phase 2 Plan-Patches

> Operator-Brief 2026-05-01 spezifizierte Phase 2 (Schema + Migrations
> + Seed). Während Implementation traten **vier Plan-Anpassungen**
> auf, die hier dokumentiert sind, damit zukünftige Audits
> nachvollziehen können, *warum* der finale Service-Stand vom Brief
> abweicht. Keine dieser Patches ist ein Skeleton-Bug — sie betreffen
> ausschliesslich den port-registry-Brief.

Erfasst: 2026-05-01 · Service: port-registry · Phase: 2 · Validator: Claude Opus 4.7 (1M)

---

## P1 — Migrations-Numbering 003/004 statt 002/003

**Brief:** `002_port_registry.sql`, `003_health_checks.sql`.
**Patch:** `003_port_registry.sql`, `004_health_checks.sql`.
**Grund:** Skeleton-Bootstrap mit `--with-auth` legt bereits
`002_auth.sql` an. Migrations sind immutable + alphabetisch geordnet;
Brief-Numbering hätte zu Drift-Conflict geführt. Auth-Migration ist
authoritativ vor Service-Migrations (api_keys-Tabelle muss vor
business-Tables stehen für FK-Optionen in späteren Migrations).
**Entscheid-Pfad:** Korrektheit (immutable migrations) > Brief-Wortlaut.

---

## P2 — `update_updated_at()` als `port_registry.update_updated_at()`

**Brief:** `EXECUTE FUNCTION update_updated_at()` (ohne Schema-Prefix).
**Patch:** `EXECUTE FUNCTION port_registry.update_updated_at()`.
**Grund:** Skeleton-`001_init.sql` legt die Funktion bereits
schema-prefixed an. Brief-Wortlaut hätte zu *function does not exist*
geführt, da Service-User keinen `search_path`-Eintrag auf
`port_registry` hat (default ist `"$user", public`). Das Fixing
auf den Schema-Prefix ist Skeleton-konform.
**Entscheid-Pfad:** Konsistenz mit Skeleton-Konvention > Brief-Wortlaut.

---

## P3 — Trigger-Naming `trg_<table>_updated_at`

**Brief:** `<table>_updated_at` (z.B. `hosts_updated_at`).
**Patch:** `trg_<table>_updated_at` (z.B. `trg_hosts_updated_at`).
**Grund:** Skeleton-`001_init.sql` Zeile 70-72 dokumentiert die
Konvention `trg_<table>_updated_at`. Brief verwendet kürzere Form,
ist aber im Konflikt mit Skeleton-Empfehlung.
**Entscheid-Pfad:** Skeleton-Konvention > Brief-Wortlaut. Niedriger
Blast-Radius — Trigger-Namen sind referentiell nur in `\d <table>`
sichtbar.

---

## P4 — Service-Port `5300` → `5099`

**Brief:** Bootstrap-Step 1.2: `--port=5300`.
**Brief:** Phase-4-Watermark: `meta-range = 5000–5099` (100 ports).
**Brief:** Phase-2-Seed: `port-registry@5300 (meta)`.

**Konflikt:** Port `5300` liegt **nicht** in der meta-Range
`5000–5099` — er fällt in die services-Range `5100–5999`. Der
Brief widerspricht sich selbst. Der initiale `pnpm migrate` in
Phase 2 schlug auf der `bpap_port_in_range`-CHECK-Constraint mit
exit 3 fehl.

**Drei Optionen wurden geprüft:**

| Option | Pro | Con |
|---|---|---|
| A — Port-Migration auf `5099` | BPAP-Spec scharf, port-registry "top-of-meta" semantisch passend, null Downtime (nichts läuft) | 5 Files patchen (.env, .env.example, src/config.ts default, src/plugins/openapi.ts loopback URL, 005_seed.sql) |
| B — `range_class='services'` für port-registry | minimaler Diff (1 String) | port-registry IS meta-meta-app; eigenregistrierung in services verzerrt die services-Watermark |
| C — meta-Range erweitern (5000–5399) | Bootstrap-Port + meta-tag bleiben | BPAP-Spec-Änderung + Watermark-Capacity (100→400) |

**Patch:** Option A — Port `5099` ("top-of-meta"). 5 Files
patched, `005_seed.sql` re-run idempotent (`hosts` ON CONFLICT DO
NOTHING, `ports` re-INSERT mit korrekter Range).
**Entscheid-Pfad:** Korrektheit (BPAP-Konvention) > Brief-Wortlaut > DX.

---

## O1 — Operations-Befund: PGPASSWORD-Leak via system-reminder

**Befund:** Während Phase-2-Edits hat `Read` auf `.env` den
inhaltlichen `PGPASSWORD`-Wert in das Conversation-Transcript
geschrieben. Anschliessende **Rotation via `add-service-schema.sh`**
+ `sed -i` auf `.env` triggerte einen automatischen Linter-/Hook-
`<system-reminder>` der wiederum den **frisch rotierten Wert** ins
Transcript zurückgab. Erneutes Rotieren würde den Hook erneut
auslösen — die Plattform-Charakteristik im Claude-Code-Workflow.

**Risiko:** Das Conversation-Transcript ist persistent (Anthropic-
Server-side, plus mögliche lokale Logs unter `~/.claude/projects/`).
Beide PGPASSWORD-Werte (initial + rotiert) sind dort einsehbar.
Aktueller Wert ist der DB-source-of-truth.

**Mitigation aktuell:** Service-User hat *nur* USAGE+CREATE auf
`port_registry`-Schema (Phase-1 Negativ-Test bestätigt: CREATE in
`ip_pool` blocked). Der Schaden eines Leaks ist auf den
port_registry-Schema-Inhalt begrenzt — keine Cross-Service-
Eskalation möglich.

**Empfehlung für zukünftige Services / api-standards-Skeleton:**
- Secret-Pointer-Pattern: `.env` enthält `PGPASSWORD_FILE=/run/secrets/port_registry_pgpassword` statt Inline-Wert. Service-Code liest die Datei at runtime.
- Alternative: dotenv via vault-CLI on demand (`vault kv get …` durch ein wrapper-script).
- Rotation als operator-side workflow (außerhalb Claude-Code-Sessions), nicht im Agent-Pfad.

Diese Empfehlung wird **nicht** in Phase 2-5 umgesetzt — Tech-Debt
für rc2.

**Entscheid-Pfad:** Sicherheit (Schaden begrenzen via Schema-
Isolation) > Korrektheit > Operations-Convenience. Da das Risiko
durch Schema-Isolation kontainiert ist, gilt der Befund als
*akzeptiert mit dokumentierter Mitigation*.

---

## Phase-2-Validierung Snapshot

```
hosts             | 3
ports             | 2  (port-registry@5099 meta, ip-pool-api@5107 services)
port_history      | 0  (gefüllt ab Phase 3)
health_sweeps     | 0  (gefüllt ab Phase 4)
health_results    | 0  (gefüllt ab Phase 4)
schema_migrations | 5
```

BPAP CHECK-Negativtest: `INSERT (port=5108, range_class='workers')`
→ `ERROR: bpap_port_in_range`. ✅
