# Arbeitsanweisung für GitHub Copilot

Diese Datei gilt für dieses Repository. Copilot liest sie bei jeder Chat-Anfrage,
jedem Coding-Agent-Auftrag und jedem Code-Review automatisch.

## Sprache

Antworten, Commit-Nachrichten, Pull-Request-Beschreibungen und Code-Kommentare:
**Deutsch**. Fachbegriffe bleiben in der etablierten Form (Pull Request, Branch,
Rollback) — keine erfundenen Eindeutschungen.

## Maßgeblicher Standard

Verbindlich ist `SSR-AII/ssr-engineering-standard` → `STANDARD.md`. Bei Widerspruch
zwischen dieser Datei und dem Standard gilt der Standard. Kurzfassung:

1. **Conventional Commits**, deutsch: `feat: …`, `fix: …`, `chore: …`, `docs: …`,
   `refactor: …`, `test: …`. Kopfzeile sagt *was*, Body sagt *warum*.
2. **SemVer-Tags**, `CHANGELOG.md` nach Keep a Changelog.
3. **Pflichtdateien:** `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `README.md`,
   `CHANGELOG.md`, `docs/adr/` (MADR), `SECURITY.md`, `CODEOWNERS`, CI-Workflow.
4. **Trunk-based:** kurzlebige Branches `feat/…` `fix/…` `chore/…` `docs/…`,
   niemals direkt auf dem Standard-Branch. Branch nach dem Merge löschen.
5. `main` bleibt jederzeit grün. Rote Tests = kein Merge.

## Was du bei JEDEM Auftrag prüfst

Vor dem ersten Vorschlag:

- [ ] Gibt es die Funktion schon? Erst suchen, dann bauen. Keine Parallel-Implementierung.
- [ ] Welcher Stil herrscht in den Nachbardateien (Namen, Kommentardichte, Idiome)?
      Dem folgen, nicht den eigenen mitbringen.
- [ ] Welche Tests deckt die Änderung ab? Fehlt einer, schreib ihn mit.

## Was du NIE tust

- Secrets, Tokens, Passwörter, private Keys oder `.env`-Inhalte in Code, Tests,
  Beispiele, Logs, Kommentare oder PR-Texte schreiben. Platzhalter: `<WERT_AUS_ENV>`.
- `dist/`, `build/`, `node_modules/`, Build-Artefakte oder Fremdcode committen.
- Force-Push auf geteilte Branches.
- Produktions-Deploys, Releases, Datenbank-Migrationen auf Produktionsdaten oder
  `rm -rf` ausführen.
- Abhängigkeiten neu einziehen, nur um ein paar Zeilen zu sparen. Standardbibliothek
  zuerst; neue Abhängigkeit im PR-Text begründen.

## Als Code-Reviewer

Wenn du einen Pull Request prüfst, arbeite diese Reihenfolge ab und melde
**Fundstelle + konkreten Fix**, nicht nur die Beobachtung:

1. **Korrektheit** — Grenzfälle, `null`/`undefined`, Off-by-one, Fehlerpfade,
   Nebenläufigkeit, nicht behandelte Promise-Rejections.
2. **Sicherheit** — Injection (SQL, Shell, Pfad), fehlende Eingabeprüfung, kaputte
   Autorisierung, Secret im Diff, unsichere Deserialisierung, offene Weiterleitung.
3. **Abhängigkeiten** — neu hinzugefügte Pakete: Zweck, Lizenz, bekannte Lücken.
4. **Tests** — deckt der Diff sich selbst ab? Negativfälle vorhanden?
5. **Standard** — Commit-Format, Pflichtdateien, CHANGELOG-Eintrag, ADR bei
   Architekturentscheidungen.
6. **Vereinfachung** — Doppelung, toter Code, überflüssige Abstraktion.

Keine Stilkommentare, die ein Formatierer erledigt. Keine Lobhudelei.
Wenn nichts zu melden ist: „Keine Befunde" und Begründung in einem Satz.

## Geheimnisse und Umgebung

Echte Werte stehen ausschließlich in `.env` (immer `.gitignore`) oder im
Schlüsselbund. Jedes Repository hat `.env.example` mit allen Variablennamen und
leeren Werten. Brauchst du eine neue Variable, trag sie dort ein — nie den Wert.
