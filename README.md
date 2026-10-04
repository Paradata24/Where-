# Startplatz-Finder Südtirol

Statische Website, die auf einer Karte mögliche Startplätze für Gleitschirmflieger in Südtirol zeigt.
Man wählt eine Startrichtung (16 Sektoren, z. B. S–SSW), die Karte zeigt passende Kandidatenflächen.

> **Hinweis:** Die Ergebnisse sind **Kandidaten, keine geprüften oder erlaubten Startplätze.**

Die ausführliche Projektbeschreibung steht in [CLAUDE.md](CLAUDE.md).

## Stand

| Phase | Inhalt | Stand |
|---|---|---|
| 1 | Prüfen, ob die Daten der Provinz automatisch ladbar sind | erledigt (04.10.2026) |
| 2 | Berechnung für Testgebiete (je 6 × 6 km): Rittner Horn, Sarntal – Großer Mittager; Karte auf GitHub Pages | erster Stand (04.10.2026), wartet auf Prüfung |
| 3 | Ausweitung auf ganz Südtirol (erst nach Freigabe) | offen |

## Testgebiete

Die Gebiete stehen in `einstellungen/einstellungen.toml` unter `[[gebiete.liste]]`
(Kürzel, Name, Mittelpunkt). Ein weiteres Gebiet kommt dazu, indem man dort einen
neuen Block mit den gleichen Feldern einfügt; die Berechnung startet dann automatisch.

| Kürzel | Name | Mittelpunkt |
|---|---|---|
| `rittner_horn` | Ritten – Rittner Horn | Gipfel Rittner Horn |
| `grosser_mittager` | Sarntal – Großer Mittager | Gipfel Großer Mittager (2422 m) |

## Website

Die Karte liegt in `docs/index.html` und wird über GitHub Pages veröffentlicht.
Man wählt in der Windrose eine oder mehrere der 16 Startrichtungen; angezeigt werden
die Kandidaten mit freiem Abflug in dieser Richtung. Weitere Filter: Abstand zum Weg,
Hinweis „früher Wald“, Startflächen, bekannte Startplätze zum Vergleich.

**GitHub Pages einschalten (einmalig):** Im Repository oben auf **Settings** → links
**Pages** → bei „Source“ **Deploy from a branch** → bei „Branch“ den Zweig wählen
(zum Testen `claude/startplatz-finder-suedtirol-5fn3yc`, später `main`) und den Ordner
**/docs** → **Save**. Nach 1–2 Minuten steht oben die Adresse der Website,
z. B. `https://paradata24.github.io/Where-/`.

## Datenquellen und Lizenzen

Alle Einzelheiten (Adressen, Layernamen, Aufnahmejahre) stehen in [daten/QUELLEN.md](daten/QUELLEN.md).

| Daten | Quelle | Wofür | Lizenz | Stand |
|---|---|---|---|---|
| Geländemodell DGM 2,5 m | Autonome Provinz Bozen, WCS | Neigung, Ausrichtung, Gleitlinie | CC0 | 2004/2005 |
| Oberflächenmodell DOM 2,5 m | Autonome Provinz Bozen, WCS | Höhe von Bäumen/Gebäuden (DOM − DGM) | CC0 | 2004/2005 |
| Realnutzungskarte 1:10.000 | Autonome Provinz Bozen, WFS | Untergrund (Wiese, Wald, Fels …) | CC0 | 2005 |
| Orthofoto 2023 Infrarot | Autonome Provinz Bozen, WMS | Prüfung: heute Vegetation oder kahl? | CC BY 4.0 | 2023 |
| Orthofoto 2023 Farbe | Autonome Provinz Bozen, WMS | nur Kartenhintergrund | CC BY 4.0 | 2023 |
| Wege, Seilbahnen, Stromleitungen | OpenStreetMap (Overpass) | Abstand zum Weg, Hindernisse | ODbL 1.0 | Abrufdatum in jeder Datei |
| Bekannte Startplätze | paraglidingearth.com | nur zum Vergleich | CC BY-SA 3.0 | Abrufdatum in der Datei |

**Achtung:** Gelände-, Oberflächenmodell und Realnutzungskarte sind rund 20 Jahre alt.
Bäume, die seither gewachsen sind, fehlen als Hindernis. Wo die Karte von 2005 Wald zeigt,
das Luftbild von 2023 aber offene Wiese, wird der Kandidat mit einem Hinweis markiert.

## Eignungskriterien

Grundlage ist die Masterarbeit von Elisabeth Egger („Investigation of routing possibilities for
Hike and Fly within paragliding“, TU Graz 2022, Kap. 2.2 und 8.2; PDF unter `docs/vorschau/`).
Alle Schwellenwerte stehen in [einstellungen/einstellungen.toml](einstellungen/einstellungen.toml)
und können dort geändert werden.

1. **Hangneigung** 7°–30°.
2. **Hangausrichtung** höchstens ±45° von der Startrichtung. Gerechnet wird für 16 Richtungen
   (N, NNO, NO … NNW; Egger: 8).
3. **Untergrund:** Grasland oder Wiese/Weide laut Realnutzungskarte, im Infrarotbild 2023 nicht
   kahl, keine Objekte ab 3 m Höhe.
4. **Startbahn:** In einem 90°-Kreisbogen mit 30 m Radius in Startrichtung muss die Mehrheit
   der Zellen geeignet sein.
5. **Mindestfläche** 112 m².
6. **Freier Abflug:** In einem Dreieck vor dem Startpunkt (500 m lang, 40° Öffnung) muss die
   Gleitlinie mit Gleitzahl 7 überall über Gelände, Bäumen/Gebäuden (DOM − DGM) und Leitungen
   (Seilbahnen 15 m, Stromleitungen 20 m über Grund, aus OSM) bleiben. Geprüft wird jede
   Rasterzelle im Dreieck.
7. **Startpunkt:** Innerhalb jeder Fläche werden Punkte im 10-m-Raster geprüft; Startpunkt ist der
   höchste Punkt mit freiem Abflug. *Abweichung von Egger*, die nur den höchsten Punkt der
   Fläche prüft – der liegt oft auf einer flachen Kuppe, von der kein Abflug frei ist.
8. **Zusammenfassen:** Startpunkte näher als 20 m (auch aus verschiedenen Richtungen) werden
   zu einem Kandidaten.
9. **Nur als Eigenschaft** (kein Ausschluss): Abstand zum nächsten Weg (Egger: max. 50 m).
   Nationalpark und Luftraum: noch offen (betrifft das Testgebiet nicht).

## Berechnung neu starten

Die Berechnung läuft auf GitHub (GitHub Actions), nicht auf dem eigenen Computer.

1. Im Repository oben auf den Reiter **Actions** klicken.
2. Links **Berechnung** wählen.
3. Rechts auf **Run workflow** klicken, den Zweig auswählen und nochmals **Run workflow** klicken.
4. Nach ca. 15 Minuten je Gebiet erscheint ein grüner Haken. Die neuen Ergebnisse werden automatisch
   gespeichert; die Website zeigt sie nach 1–2 Minuten.

Ablauf (Ordner `analyse/`):

| Schritt | Skript | macht |
|---|---|---|
| 0 | `00_datenpruefung.py` | prüft, ob alle Datenquellen erreichbar sind (Workflow „Datenprüfung“) |
| 1 | `01_hoehenmodelle_laden.py` | lädt DGM und DOM |
| 2 | `02_osm_laden.py` | lädt Wege, Seilbahnen, Stromleitungen aus OSM |
| 3 | `03_startplaetze_laden.py` | lädt bekannte Startplätze (ParaglidingEarth) |
| 4 | `04_untergrund_laden.py` | lädt Realnutzungskarte und Infrarot-Orthofoto |
| 5 | `05_objekthoehe.py` | berechnet und prüft die Objekthöhe (DOM − DGM) |
| 6 | `06_kandidaten.py` | berechnet die Kandidaten → `ergebnisse/<gebiet>/` und `docs/daten/<gebiet>/` |

Jedes Skript rechnet alle Gebiete. Mit einem Kürzel dahinter nur dieses, z. B.
`python 06_kandidaten.py grosser_mittager`.

## Ordner

| Ordner | Inhalt |
|---|---|
| `einstellungen/` | alle einstellbaren Werte (Neigung, Fläche, Gleitzahl …) |
| `analyse/` | Python-Skripte der Berechnung, nummeriert nach Reihenfolge |
| `rohdaten/` | heruntergeladene Höhenmodelle usw. (nur während der Berechnung, nicht auf GitHub) |
| `daten/` | kleine Eingangsdaten je Gebiet (OSM, bekannte Startplätze) und [QUELLEN.md](daten/QUELLEN.md) |
| `ergebnisse/` | kompakte Ergebnisse (GeoJSON), ein Unterordner je Gebiet |
| `docs/` | die Website (GitHub Pages); `docs/daten/` enthält eine Kopie der Ergebnisse |
| `docs/vorschau/` | Testbilder und die Masterarbeit (PDF) |
| `.github/workflows/` | Abläufe für GitHub Actions („Datenprüfung“, „Berechnung“) |
