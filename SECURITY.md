# Sicherheit

## Lücke melden

Melden Sie Schwachstellen **nicht** über öffentliche Issues.

Weg: im Reiter **Security → Report a vulnerability** dieses Repositories
(Private Vulnerability Reporting). Alternativ per E-Mail an den Betreiber.

Wir bestätigen den Eingang innerhalb von **5 Werktagen** und nennen dabei,
ob wir die Meldung als Schwachstelle einordnen.

## Was wir erwarten

- Keine Tests gegen Produktionsdaten Dritter.
- Keine Dienstunterbrechung, keine Lasttests.
- Keine Weitergabe, bis ein Fix veröffentlicht ist.

## Geltungsbereich

Der Code dieses Repositories. Fremde Dienste und Abhängigkeiten melden Sie
bitte direkt beim jeweiligen Anbieter.

## Geheimnisse

Echte Werte liegen ausschließlich in `.env` (nie im Repository) oder im
Schlüsselbund. Finden Sie ein Secret in der Historie, melden Sie es auf dem
oben genannten Weg — nicht im Issue-Tracker.
