# AGENT-WORKFLOW

Pflicht-Workflow für jede Code-Änderung in einem BBE-DBE-Service durch einen
agentischen Code-Generator (Claude Code, Codex, etc.).

Drei Teile: **VORHER** (Trade-off), **NACHHER** (Selbstcheck), **OPTIMIERUNG**
(Iteration). Der Agent durchläuft alle drei ohne weitere Aufforderung.
Verstöße werden im Status-Report genannt, nicht stillschweigend übergangen.

---

## TEIL 1 — VORHER: Trade-off-Analyse

Vor jedem Schreibvorgang liefert der Agent diesen Block:

### (a) Was ich übernehme wie vorgeschlagen
Listenform. Pro Punkt: Auftrags-Zeile + "ok".

### (b) Was ich anders mache und warum
Pro Punkt: Auftrags-Zeile + alternative Lösung + Begründung. Wenn die
Begründung mit einer Prüf-Dimension aus Teil 2 zusammenhängt, Dimension
benennen.

### (c) Welche Annahmen ich treffe
Wo der Auftrag mehrdeutig ist:
- Annahme klar formulieren
- Begründung warum das die plausibelste Lesart ist
- "Wenn das falsch ist: Stop-Wort 'falsch' im Chat, ich warte"

### (d) Welche Risiken bleiben
Tech-Debt-Items für nach diesem Auftrag. Format:
- Punkt
- Schweregrad (kritisch / mittel / klein)
- Empfohlener Zeitpunkt (v0.3 / vor-skale / opportunistisch)

### Konflikt-Reihenfolge
1. **Sicherheit** (Secrets, Auth, Audit, SQL-Injection)
2. **Korrektheit** (Idempotenz, Race-Conditions, State-Machine)
3. **Compliance** (DSGVO, ISO 27001, Audit-Trail)
4. **Observability** (Logs, Metrics, Tracing)
5. **Performance** (Latency, Throughput)
6. **DX** (Build-Zeit, Code-Schönheit)

Niedrigere Stufen weichen höheren. Begründung im Code-Kommentar.

---

## TEIL 2 — NACHHER: Selbstcheck nach Build

Pflicht nach `pnpm build` + `pnpm test`. Vollständige Checkliste in
[`../checklists/14-dimensions.md`](../checklists/14-dimensions.md).

Status-Symbole: ✅ OK · 🟡 teilweise · ❌ fehlt · ➖ n/a

---

## TEIL 3 — OPTIMIERUNG: Iteration nach grünem Build

### Stufe A — Mess-Daten erheben
- reserve/release p50, p99 (über 100 Iterations)
- Throughput unter Rate-Limit-Decke
- Build-Zeit (sekundengenau)
- Coverage pro File (nicht nur Mittel)
- /health-Antwortzeit
- Sweeper-Tick-Dauer (idle vs. work)

Werte in `docs/performance.md` ergänzen mit Datum + Git-SHA.

### Stufe B — Hotspots identifizieren
Vergleich gegen die letzten Werte:
- Latency-Regression > 10 % → analysieren, melden
- Coverage-Drop in einer Datei → Test-Lücke benennen
- Build-Zeit-Anstieg > 20 % → Dependency-Analyse

### Stufe C — Vorschläge formulieren
Pro Hotspot: was ändern, Aufwand (XS/S/M/L), erwartete Verbesserung, Risiko.
**NICHT umsetzen ohne neuen Auftrag.** Liste am Ende des Status-Reports als
"Optimierungs-Backlog".

### Stufe D — Tech-Debt aufräumen
Wenn ein CHANGELOG-Tech-Debt-Item < 15 Min zusätzlich kostet: erledigen +
notieren. Sonst dokumentieren, weiterziehen.

---

Vorlage für den Abschluss-Bericht: [`../templates/status-report.md`](../templates/status-report.md).
