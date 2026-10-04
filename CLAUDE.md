# Startplatz-Finder Südtirol – Projektbeschreibung

Diese Datei beschreibt das Projekt dauerhaft. Sie wird bei jeder Sitzung gelesen.

## Über den Auftraggeber

- Der Auftraggeber kann nicht programmieren und arbeitet ausschließlich über Claude Code im Browser und GitHub (kein Ordner auf dem eigenen Computer).
- Sprache: immer Deutsch, kurz und einfach erklärt.
- Arbeitsweise: in kleinen Schritten arbeiten. Vor größeren Entscheidungen nachfragen.
- Wenn der Auftraggeber auf GitHub selbst etwas klicken muss (z. B. Pull Request übernehmen, GitHub Pages aktivieren), genau sagen, wo.
- Keinen Pull Request ohne ausdrückliche Bitte erstellen.

## Ziel des Projekts

Eine neue, statische Website („Startplatz-Finder Südtirol"), die auf einer Karte mögliche Startplätze für Gleitschirmflieger in Südtirol anzeigt.

- Der Nutzer wählt eine Startrichtung (z. B. Süd bis Südsüdwest, passend zur Windprognose) und weitere Filter. Die Karte zeigt passende Kandidatenflächen.
- Die Analyse wird einmal vorab berechnet. Die Website zeigt nur die fertigen Ergebnisse an und filtert sie im Browser.
- Kein Server, keine laufenden Kosten.

## Technik

- Code und Website liegen auf GitHub. Die Website wird über GitHub Pages veröffentlicht.
- Berechnungen laufen über GitHub Actions oder lokal mit Python.
- Frontend: Leaflet mit OpenTopoMap als Hintergrund. Schlicht in HTML/CSS/JavaScript, ohne Build-Werkzeuge.
- Analyse: Python (z. B. rasterio, numpy, geopandas, shapely, scipy).

## Arbeitsweise in der Cloud

- Alles läuft in der Cloud: Claude Code im Browser für die Entwicklung, GitHub Actions für große Berechnungen, GitHub Pages für Vorschau und Website.
- Große Rohdaten (Höhenmodelle) kommen **nicht** ins Repository. Skripte laden sie bei Bedarf selbst herunter. Nur kompakte Ergebnisse werden gespeichert.
- Vorschauseiten werden über GitHub Pages veröffentlicht, damit der Auftraggeber sie im Browser öffnen kann.

## Datenquellen

- **Autonome Provinz Bozen, Landeskartografie:** Digitales Geländemodell (DGM/DTM) und Digitales Oberflächenmodell (DOM/DSM), landesweit 2,5 m, aus LiDAR.
  - Bezug über die Geodienste der Provinz: WCS für Rasterwerte, WMS/WMTS für Kartenbilder.
  - Geokatalog/MapView: https://mapview.civis.bz.it
  - Die Daten sind überwiegend CC0.
  - Genaue Dienst-Adressen und Layernamen über GetCapabilities ermitteln.
- **Achtung, Alter der Daten:** Die Befliegung für das landesweite DGM/DOM stammt aus 2004/2005.
  - Das Gelände ist dafür unproblematisch.
  - Der Waldstand kann aber stark veraltet sein (Zuwachs, Schlägerungen, Sturm Vaia 2018). Das muss bei der Baumerkennung berücksichtigt werden.
- **Aktuelle Orthofotos der Provinz (WMS):** als Hintergrund für die Kontrolle.
- **Untergrund (Entscheidung 04.10.2026):** nicht aus OpenStreetMap, sondern aus der **Realnutzungskarte 1:10.000** der Provinz (WFS, CC0, Stand 2005), geprüft mit dem **Infrarot-Orthofoto 2023** (Vegetationsindex) und der Objekthöhe (DOM minus DGM).
- **OpenStreetMap:** nur Wege, Straßen, Seilbahnen, Materialseilbahnen, Stromleitungen.
- **Bekannte Startplätze zum Abgleich:** DHV-Geländedatenbank, paraglidingearth.com, OSM (`sport=free_flying`).

## Fachliche Grundlage

Die Methode orientiert sich an der Masterarbeit von Elisabeth Egger, „Investigation of routing possibilities for Hike and Fly within paragliding", TU Graz 2022 (PDF: `docs/vorschau/74383.pdf`).

Ihre Kriterien gelten als Startwerte. **Alle Werte müssen später einstellbar sein** (zentrale Einstellungsdatei, nichts fest im Code).

- **Hangneigung:** zwischen 7° und 30°.
- **Hangausrichtung:** innerhalb ±45° der Startrichtung. Wir speichern die echte Ausrichtung stufenlos, nicht nur 8 Klassen.
- **Untergrund:** nur Wiese, Weide, offener Boden. Kein Fels, Geröll, Wald, Gebüsch, Wasser, Gebäude.
- **Mindestfläche:** 112 m².
- **„Startbahn":** In einem 90°-Kreisbogen mit 30 m Radius in Startrichtung muss die Mehrheit der Zellen geeignet sein.
- **Startpunkt:** Pro geeigneter Fläche wird der höchste Punkt bestimmt. Abweichung von Egger (04.10.2026): Innerhalb jeder Fläche werden Punkte im 10-m-Raster auf freien Abflug geprüft; Startpunkt ist der höchste Punkt *mit* freiem Abflug. Grund: Der höchste Punkt liegt oft auf einer flachen Kuppe, von der die Gleitlinie nie frei ist.
- **Zusammenfassen:** Kandidaten näher als 20 m zueinander werden zusammengefasst.
- **Hindernisprüfung:**
  - Vom Startpunkt aus wird ein dreieckiger Korridor in Startrichtung geprüft (500 m lang, 40° Öffnung).
  - Die Gleitlinie mit Gleitzahl 7 darf an keiner Stelle unter Gelände oder Hindernis fallen.
  - Egger hat pauschale Baumhöhen je Landbedeckung verwendet. Wir verwenden stattdessen die echte Objekthöhe (DOM minus DGM), ergänzt um Seilbahnen und Stromleitungen aus OSM.
  - Die genaue rasterbasierte Prüfung (alle Zellen im Dreieck) ist der vereinfachten Prüfung mit wenigen Sichtlinien vorzuziehen.
- **Abstand zum nächsten Weg** (Egger: max. 50 m): nicht als Ausschluss, sondern als Eigenschaft speichern, damit man auf der Website danach filtern kann.
- **Nationalpark Stilfserjoch und Luftraumbeschränkungen:** als Eigenschaft markieren (nicht ausschließen).

## Testgebiet

Zuerst nur ein Gebiet von ca. 6 × 6 km um das Rittner Horn (Ritten, Südtirol). Erst wenn die Ergebnisse dort plausibel sind, wird auf ganz Südtirol erweitert.

## Hinweis für die Website (Pflicht)

Die Ergebnisse sind **Kandidaten, keine geprüften oder erlaubten Startplätze**. Ein gut sichtbarer Hinweis auf der Website muss das klarstellen.

## Ordnerstruktur

- `einstellungen/` – alle einstellbaren Werte (Neigung, Fläche, Gleitzahl …) in einer Datei, nichts fest im Code.
- `analyse/` – Python-Skripte der Berechnung, nummeriert nach Reihenfolge.
- `rohdaten/` – heruntergeladene Höhenmodelle usw. Nur lokal bzw. in der Cloud, per `.gitignore` ausgeschlossen.
- `daten/` – kleine Eingangsdaten (OSM-Auszüge, bekannte Startplätze) und `QUELLEN.md` mit allen Quellen, Lizenzen und Aufnahmejahren.
- `ergebnisse/` – kompakte Ergebnisse (z. B. GeoJSON). Klein halten, damit die Website schnell lädt.
- `docs/` – die Website (GitHub Pages veröffentlicht diesen Ordner).
- `docs/vorschau/` – Testseiten zum Prüfen von Zwischenergebnissen.
- `.github/workflows/` – GitHub Actions für große Berechnungen.
