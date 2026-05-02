# 14-Dimensionen-Selbstcheck

Pflicht nach jedem Build. Status: ✅ · 🟡 (Lücke benannt) · ❌ · ➖ (nicht zutreffend).

## 1. Sicherheit
- [ ] Secrets nie im Code, nie in Logs, nie in Git, nie im Chat
- [ ] Auth-Scopes minimal (least privilege)
- [ ] SQL-Injection / Path-Traversal ausgeschlossen
- [ ] Audit-Log unveränderlich (Trigger-erzwungen)
- [ ] Container-Images per SHA256 gepinnt
- [ ] Dependencies auf bekannte CVEs geprüft (`pnpm audit`)
- [ ] Rate-Limiting + Brute-Force-Schutz aktiv
- [ ] Error-Messages leaken keine internen Details
- [ ] Cache-Invalidation bei Revoke/Rotation

## 2. Korrektheit
- [ ] Idempotenz auf jeder Mutation (Idempotency-Key + persistenter Store)
- [ ] Race-Conditions ausgeschlossen (FOR UPDATE SKIP LOCKED, Outbox)
- [ ] State-Machine in DB erzwungen (Trigger), nicht nur im Code
- [ ] Validation server-seitig (zod o.ä.), nie nur client-seitig
- [ ] Fehlerpfade getestet, nicht nur happy path
- [ ] Idempotency-Replay mit anderem Body → 422

## 3. Performance
- [ ] Hot-Path-Queries haben passende Indizes (EXPLAIN ANALYZE in docs/)
- [ ] N+1-Queries vermieden (Batch-Operations wo möglich)
- [ ] Connection-Pooling konfiguriert (max, min, timeouts)
- [ ] statement_timeout per Connection gesetzt
- [ ] Caching mit klaren Invalidation-Regeln dokumentiert
- [ ] Async statt sync (Outbox, Background-Worker)

## 4. Effizienz
- [ ] Minimale Dependencies, jede begründet
- [ ] Build-Zeit gemessen (sekundengenau im Status-Report)
- [ ] Container-Image-Größe minimal (alpine, multi-stage)
- [ ] Sweeper/Worker skippen leere Arbeit (Pre-Check)
- [ ] Logs nicht bei Idle-Heartbeats spammen

## 5. Modularität
- [ ] Plugin-System mit explizitem Allowlist-Mechanismus
- [ ] Provider-Adapter über Interface, austauschbar (siehe `protocols/provider-adapter-interface.md`)
- [ ] Service-Boundaries klar (DB-Schema pro Service)
- [ ] Keine zirkulären Dependencies
- [ ] Eine Verantwortung pro Komponente (max ~200 LoC pro File)
- [ ] **Service-Reuse verifiziert vor neuer Implementierung** (Lookup in `SERVICES.yaml` dokumentiert; bei Treffer mit niedrigerem `reuse_priority` MUSS das bestehende Service konsumiert werden, nicht reimplementiert)

## 6. Kompatibilität
- [ ] OpenAPI 3.1 als Single Source of Truth
- [ ] /v1/ versioniert, additive Changes only innerhalb Major
- [ ] Strukturierte Error-Codes (nicht Strings parsen)
- [ ] ISO-Timestamps in UTC
- [ ] UUIDv7 extern, BIGSERIAL nur intern
- [ ] Standard HTTP-Status-Codes

## 7. Skalierbarkeit
- [ ] Stateless Services (State nur in DB / Redis)
- [ ] Horizontale Skalierung möglich ohne Refactor
- [ ] Keine kritischen In-Memory-Caches
- [ ] Datenbankschema verträgt 100x aktuelle Last
- [ ] Hardcoded-Limits in config.ts, nicht im Code
- [ ] Sweeper/Worker mit Leader-Election (advisory lock)

## 8. Observability
- [ ] Strukturierte JSON-Logs mit request_id, actor_id, run_id
- [ ] Authorization-Header redacted in allen Logs
- [ ] Prometheus /metrics: Counter + Histogram + Gauge
- [ ] Health-Split: /health, /health/live, /health/ready
- [ ] Audit-Events tragen build_version + git_commit
- [ ] X-Request-Id Cross-Service-Propagation

## 9. Code-Qualität
- [ ] TypeScript strict mode
- [ ] Keine `any` ohne Begründung im Kommentar
- [ ] Unit-Tests für kritische Pfade
- [ ] Integration-Tests für Routes (fastify.inject)
- [ ] Smoke-Test als Akzeptanz-Kriterium
- [ ] Keine TODO/FIXME ohne Issue-Verweis
- [ ] Code-Kommentare erklären WARUM

## 10. Compliance
- [ ] ISO 27001 Mapping aktuell (in STANDARDS.md)
- [ ] ISO 42001 nur claimen wenn ernsthaft adressiert
- [ ] DSGVO Art. 30 Verzeichnis vorhanden (docs/data-processing.md)
- [ ] EU CRA / SBOM (CycloneDX) per Release
- [ ] Author-Tracking auf jeder Migration

## 11. Operations
- [ ] Backup-Skript existiert + Restore-Test grün
- [ ] Backup-Cron via systemd-timer dokumentiert
- [ ] Container-Pinning per SHA256-Digest
- [ ] Graceful Shutdown (SIGTERM → drain → exit)
- [ ] Restart-Survival getestet
- [ ] DR-Runbook dokumentiert (RTO/RPO)
- [ ] Resource-Limits gesetzt (memory, CPU, FDs)
- [ ] Log-Rotation aktiv

## 12. Dokumentation
- [ ] README.md (Zweck, Setup, Konventionen)
- [ ] PRINCIPLES.md (Architektur-Begründung)
- [ ] STANDARDS.md (Compliance-Mapping)
- [ ] CHANGELOG.md (Keep-a-Changelog)
- [ ] OpenAPI-Spec committed
- [ ] Trade-offs als Code-Kommentare

## 13. Agent-Tauglichkeit
- [ ] Alle Endpoints headless nutzbar
- [ ] Maschinenlesbare Error-Codes (stable `code`-Feld)
- [ ] Idempotency-Key + run_id Pflicht für Mutations
- [ ] **Idempotency akzeptiert beide Header** (`Idempotency-Key` und `X-Idempotency-Key`, siehe `protocols/idempotency-header-compat.md`)
- [ ] Bootstrap headless möglich
- [ ] Plugin-Allowlist via config
- [ ] **`/service-manifest` Endpoint** liefert maschinenlesbares Capability-Manifest (siehe `protocols/service-manifest.md`)
- [ ] **Service-Self-Registration** bei `port-registry` beim Boot (siehe `protocols/service-self-registration.md`)
- [ ] **`SERVICES.yaml`-Lookup** dokumentiert: vor jeder neuen Capability geprüft, ob bestehendes Service bereits passt

## 14. Lebenszyklus
- [ ] Migrations immutable (SHA-256-Drift-Check)
- [ ] Niemals löschen, nur retire
- [ ] Soft-Delete via Status-Spalte
- [ ] Bootstrap-Secrets max 30 Tage rotieren
- [ ] Reproducible Build (clean tree beim Tag)
