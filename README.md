# Startplatz-Finder Südtirol

Statische Website, die auf einer Karte mögliche Startplätze für Gleitschirmflieger in Südtirol zeigt.
Man wählt eine Startrichtung (16 Sektoren, z. B. S–SSW), die Karte zeigt passende Kandidatenflächen.

> **Hinweis:** Die Ergebnisse sind **Kandidaten, keine geprüften oder erlaubten Startplätze.**

Die ausführliche Projektbeschreibung steht in [CLAUDE.md](CLAUDE.md).

## Stand

| Phase | Inhalt | Stand |
|---|---|---|
| 1 | Prüfen, ob die Daten der Provinz automatisch ladbar sind | erledigt (04.10.2026) |
| 2 | Berechnung für das Testgebiet Rittner Horn (6 × 6 km), Karte auf GitHub Pages | offen |
| 3 | Ausweitung auf ganz Südtirol (erst nach Freigabe) | offen |

## Datenquellen und Lizenzen

Alle Einzelheiten (Adressen, Layernamen, Aufnahmejahre) stehen in [daten/QUELLEN.md](daten/QUELLEN.md).

| Daten | Quelle | Lizenz | Stand |
|---|---|---|---|
| Geländemodell DGM 2,5 m | Autonome Provinz Bozen, WCS-Dienst | CC0 (gemeinfrei) | Befliegung 2004/2005 |
| Oberflächenmodell DOM 2,5 m | Autonome Provinz Bozen, WCS-Dienst | CC0 (gemeinfrei) | Befliegung 2004/2005 |
| Orthofoto (Hintergrund) | Autonome Provinz Bozen, WMS | CC BY 4.0 | 2023 |
| Wege, Seilbahnen, Stromleitungen, Wald, Fels | OpenStreetMap (Overpass) | ODbL 1.0 | Abrufdatum in jeder Datei |
| Bekannte Startplätze | paraglidingearth.com | CC BY-SA 3.0 | Abrufdatum in der Datei |

**Achtung:** Der Waldstand im DOM ist rund 20 Jahre alt (Zuwachs, Schlägerungen, Sturm Vaia 2018).

## Eignungskriterien

Grundlage ist die Masterarbeit von Elisabeth Egger („Investigation of routing possibilities for
Hike and Fly within paragliding“, TU Graz 2022). Alle Schwellenwerte stehen in
[einstellungen/einstellungen.toml](einstellungen/einstellungen.toml) und können dort geändert werden.

- Hangneigung 7°–30°
- Hangausrichtung innerhalb ±45° der Startrichtung (stufenlos gespeichert, Filter in 16 Sektoren)
- Untergrund: nur Wiese, Weide, offener Boden
- Mindestfläche 112 m²
- Startbahn: in einem 90°-Kreisbogen mit 30 m Radius muss die Mehrheit der Zellen geeignet sein
- Hindernisse im Abflug (Dreieck 500 m lang, 40° Öffnung, Gleitzahl 7): Gelände, Bäume
  (DOM minus DGM), Gebäude, Seilbahnen und Stromleitungen (OSM)
- Abstand zum nächsten Weg, Nationalpark, Luftraum: als Eigenschaft gespeichert, nicht ausgeschlossen

## Berechnung neu starten

Die Berechnung läuft auf GitHub (GitHub Actions), nicht auf dem eigenen Computer.

1. Im Repository oben auf den Reiter **Actions** klicken.
2. Links den gewünschten Ablauf wählen (zurzeit nur **Datenprüfung**).
3. Rechts auf **Run workflow** → **Run workflow** klicken.
4. Nach einigen Minuten erscheint ein grüner Haken (geklappt) oder ein rotes Kreuz (Fehler).
   Ein Klick auf den Lauf zeigt den Bericht.

## Ordner

| Ordner | Inhalt |
|---|---|
| `einstellungen/` | alle einstellbaren Werte (Neigung, Fläche, Gleitzahl …) |
| `analyse/` | Python-Skripte der Berechnung, nummeriert nach Reihenfolge |
| `rohdaten/` | heruntergeladene Höhenmodelle (nur lokal, nicht auf GitHub) |
| `daten/` | kleine Eingangsdaten (OSM, bekannte Startplätze) und [QUELLEN.md](daten/QUELLEN.md) |
| `ergebnisse/` | kompakte Ergebnisse (z. B. GeoJSON) |
| `docs/` | die Website (GitHub Pages) |
| `docs/vorschau/` | Testseiten zum Prüfen von Zwischenergebnissen |
| `.github/workflows/` | Abläufe für GitHub Actions |
