# Datenquellen – Startplatz-Finder Südtirol

Stand der Recherche: 01.10.2026. Erstes Testgebiet: 6 × 6 km um das Rittner Horn
(EPSG:25832, West 685 460 / Süd 5 162 330 / Ost 691 460 / Nord 5 168 330).

## 1. Höhenmodelle der Autonomen Provinz Bozen

| | DGM 2,5 m (Gelände) | DOM 2,5 m (Oberfläche) |
|---|---|---|
| Layer / Coverage | `p_bz-Elevation:DigitalTerrainModel-2.5m` | `p_bz-Elevation:DigitalElevationModel-2.5m` |
| Coverage-ID für WCS 2.0 (GeoServer) | `p_bz-Elevation__DigitalTerrainModel-2.5m` | `p_bz-Elevation__DigitalElevationModel-2.5m` |
| Dienst (WCS 2.0.1) | https://geoservices9.civis.bz.it/geoserver/ows | gleich |
| Kartenbild (WMS 1.3.0) | gleiche Adresse, `service=WMS` | gleich |
| Schummerung (WMS/WMTS) | `p_bz-Elevation:DigitalTerrainModel-2.5m-Hillshade` | `p_bz-Elevation:DigitalElevationModel-2.5m-Hillshade` |
| Lizenz | CC0 1.0 (gemeinfrei) | CC0 1.0 (gemeinfrei) |
| Befliegung | LiDAR, landesweit 2004/2005 (Metadaten: erstellt/veröffentlicht 30.06.2006) | gleich |
| Koordinatensystem | ETRS89 / UTM 32N (EPSG:25832) | gleich |

- Metadaten: https://data.europa.eu/data/datasets/p_bz-elevation-digitalterrainmodel-2-5m
  und https://data.europa.eu/data/datasets/p_bz-elevation-digitalelevationmodel-2-5m
- Open-Data-Portal Südtirol: https://data.civis.bz.it/de/dataset/modello-digitale-del-terreno-dtm-25m
- Technische Beschreibung: https://natur-raum.provinz.bz.it/de/digitale-hohenmodelle
- Geokatalog/MapView: https://mapview.civis.bz.it
- Download-Skript: `analyse/01_hoehenmodelle_laden.py` → `rohdaten/dgm_2_5m.tif`, `rohdaten/dom_2_5m.tif`
  (nicht im Repository).

**Achtung, Alter:** Der Waldstand im DOM ist rund 20 Jahre alt (Zuwachs, Schlägerungen,
Sturm Vaia 2018). Das Gelände selbst ist dafür unproblematisch.

**Erreichbarkeit (01.10.2026):** Der WCS-Server war aus der Cloud-Umgebung nicht erreichbar
(„HTTP 503 Service Unavailable“).

**Erreichbarkeit (04.10.2026, Phase 1):** Der WCS-Server funktioniert. Getestet mit
`analyse/00_datenpruefung.py` (auch als GitHub-Actions-Workflow „Datenprüfung“):
- Probe 1 × 1 km am Rittner Horn: DGM und DOM je 400 × 400 Zellen, 2,5 m, EPSG:25832, 100 % gültig.
- Große Kachel 20 × 20 km: 8000 × 8000 Zellen, 268 MB (unkomprimiertes GeoTIFF, float32), 1–4 Minuten.
- Kein Zugangsschlüssel nötig (`Fees: NONE`, `AccessConstraints: NONE`).
- Es gibt **keinen** ZIP-/Kachel-Download auf dem Open-Data-Portal; der WCS ist der offizielle Bezugsweg.
- Ganz Südtirol (Umriss-Rechteck ca. 155 × 105 km) ≈ 40 Kacheln à 20 km je Modell
  → ca. 11 GB je Modell unkomprimiert. Darum Verarbeitung Kachel für Kachel, Rohdaten danach löschen.

**Weitere Höhenmodelle, die gefunden wurden (noch nicht verwendet):**
- DGM 0,5 m / DOM 0,5 m (`p_bz-Elevation:DigitalTerrainModel-0.5m`, `…DigitalElevationModel-0.5m`),
  gleicher WCS, CC0, laut Metadaten nur für die *besiedelten Gebiete* Südtirols (veröffentlicht 2013).
  Geprüft am 04.10.2026: Der Gipfelbereich des Rittner Horns ist **nicht** abgedeckt (nur Leerwerte).
- DGM/DOM 0,2 m Etschtal 2024 (`…EtschAdige-0.2m-2024`): nur Etschtal, aktueller Waldstand.
- DOM Gletscher 0,5 m (2016/17 und 2023): nur Gletscherflächen, für uns nicht relevant.

## 2. Untergrund: Realnutzungskarte und Infrarot-Orthofoto

Entscheidung vom 04.10.2026: Der Untergrund (Wiese, Wald, Fels, Geröll) kommt **nicht** aus
OpenStreetMap, sondern aus Daten der Provinz. Skript: `analyse/04_untergrund_laden.py`.

**Realnutzungskarte 1:10.000 (Flächen)**
- Dienst (WFS 2.0): https://geoservices1.civis.bz.it/geoserver/p_bz-LandUse/ows,
  Layer `p_bz-LandUse:RealLandUseMap-Polygons`, Felder `CODE`, `NAME_DE`, `NAME_IT`.
- Lizenz: **CC0 1.0**. Erstellt/veröffentlicht 06.10.2005, keine Aktualisierung geplant.
  Entstanden durch Stereo-Auswertung von Schwarz-Weiß- und teils Infrarot-Luftbildern.
- Metadaten: https://data.civis.bz.it/de/dataset/carta-delluso-del-suolo-1-10-000
- Klassen am Rittner Horn (6 × 6 km + Rand): Wald 2832 ha, Grasland 1587 ha, Krummholz 426 ha,
  vegetationsloses Lockermaterial 128 ha, Ackerland 105 ha, Feuchtflächen 94 ha, Fels 8 ha u. a.
- Als startbar gelten (einstellbar): 32300 Grasland, 32400 Wiese/Weide/Zwergstrauchgesellschaften.
- Landesweit 81 234 Flächen (Test 04.10.2026).

**Orthofoto 2023 Infrarot (CIR)**
- Layer `p_bz-Orthoimagery:Aerial-2023-CIR`, WMS https://geoservices.buergernetz.bz.it/mapproxy/ows,
  20 cm, Lizenz **CC BY 4.0** („Autonome Provinz Bozen – Südtirol“).
- Geladen mit 1 m Auflösung in Kacheln von 2000 × 2000 Bildpunkten (größere Bilder lehnt der Dienst ab).
- Daraus Vegetationsindex (Infrarot − Rot) / (Infrarot + Rot), gemittelt auf 2,5 m.
  Median je Klasse am Rittner Horn: Grasland 0,20, Wald 0,43, Krummholz 0,40,
  Lockermaterial 0,13, Fels 0,09. Unter 0,08 gilt eine Zelle als kahl.

## 2a. Orthofoto (Hintergrund zur Kontrolle)

- Aktuellstes landesweites Orthofoto: **Orthofoto 2023**, 20 cm Auflösung, Layer
  `p_bz-Orthoimagery:Aerial-2023-RGB` (zusätzlich Infrarot: `p_bz-Orthoimagery:Aerial-2023-CIR`).
- Dienst: WMS https://geoservices.buergernetz.bz.it/mapproxy/ows
  (WMTS: https://geoservices.buergernetz.bz.it/mapproxy/wmts/1.0.0/WMTSCapabilities.xml)
- Lizenz: **CC BY 4.0**. Namensnennung nötig: „Autonome Provinz Bozen – Südtirol“.
- Aufnahme: 2023 (Metadaten: erstellt 15.09.2023, veröffentlicht 08.04.2024).
- Test am 01.10.2026: Der WMS liefert Bilder (GetMap in EPSG:25832 funktioniert).
- Neuere Orthofotos von 2024 gibt es nur für Teilgebiete (`Aerial-2024-EtschAdige-RGB` = Etschtal,
  `gvcc-Orthoimagery:Aerial-2024-RGB` = Gemeinde Auer). Beide decken den Ritten **nicht** ab.
- Metadaten: https://data.europa.eu/data/datasets/p_bz-orthoimagery-aerial-2023-rgb

## 3. OpenStreetMap

- Abfrage über Overpass API (https://overpass-api.de/api/interpreter), Skript `analyse/02_osm_laden.py`.
- Lizenz: **ODbL 1.0**. Namensnennung: „© OpenStreetMap-Mitwirkende“.
- Abrufdatum: steht in jeder Datei im Feld `abgerufen`.
- Verwendet nur für Hindernisse und Wege (nicht für den Untergrund). Abfragegebiet: Testgebiet plus 600 m Rand.
- Dateien in `daten/osm/`:
  - `wege_strassen.geojson` – alle `highway=*`
  - `seilbahnen.geojson` – alle `aerialway=*` (inkl. Materialseilbahnen `aerialway=goods`)
  - `stromleitungen.geojson` – `power=line|minor_line|cable`, Masten `power=tower|pole`
  - `startplaetze_osm.geojson` – `sport=free_flying` und `free_flying:*`

## 4. Bekannte Startplätze

- **paraglidingearth.com**: frei verfügbar über die Schnittstelle
  http://www.paraglidingearth.com/api/ (Skript `analyse/03_startplaetze_laden.py`).
  Lizenz: **CC BY-SA 3.0** (neue Beiträge seit 10.12.2024 zusätzlich ODbL 1.0).
  Namensnennung: „© ParaglidingEarth-Mitwirkende“. Datei: `daten/startplaetze/paraglidingearth.geojson`.
  Hinweis der Seite: Angaben ohne Gewähr, teils veraltet.
- **DHV-Geländedatenbank** (https://www.dhv.de): **nicht frei verfügbar.** Die Nutzungsbedingungen
  (https://service.dhv.de/dbfiles/managed/gelaendedaten/nutzung_gelaendedb.pdf, § 5 und § 6)
  erlauben nur persönliche, nicht-kommerzielle Nutzung. Veröffentlichen, Verbreiten und das Einbinden
  in eigene Websites sind verboten. Deshalb wird nichts davon im Repository gespeichert. Ein Abgleich
  von Hand („Gibt es dort einen DHV-Startplatz?“) ist möglich.

## 5. Noch offen

- Nationalpark Stilfserjoch (Grenze) und Luftraumbeschränkungen: noch nicht gesucht (betrifft das
  Testgebiet Ritten nicht direkt).
