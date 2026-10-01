# Startplatz-Finder Südtirol

Statische Website, die auf einer Karte mögliche Startplätze für Gleitschirmflieger in Südtirol zeigt.

**Hinweis:** Die Ergebnisse sind Kandidaten, keine geprüften oder erlaubten Startplätze.

Die ausführliche Projektbeschreibung steht in [CLAUDE.md](CLAUDE.md).

## Ordner

| Ordner | Inhalt |
|---|---|
| `einstellungen/` | alle einstellbaren Werte (Neigung, Fläche, Gleitzahl …) |
| `analyse/` | Python-Skripte der Berechnung |
| `rohdaten/` | heruntergeladene Höhenmodelle (nur lokal, nicht auf GitHub) |
| `daten/` | kleine Eingangsdaten (OSM, bekannte Startplätze) und [QUELLEN.md](daten/QUELLEN.md) |
| `ergebnisse/` | kompakte Ergebnisse (z. B. GeoJSON) |
| `docs/` | die Website (GitHub Pages) |
| `docs/vorschau/` | Testseiten zum Prüfen von Zwischenergebnissen |
| `.github/workflows/` | Anleitungen für GitHub Actions |
