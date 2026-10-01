"""Schritt 2: OpenStreetMap-Daten für das Testgebiet laden.

Lädt über die Overpass-Schnittstelle: Wege und Straßen, Seilbahnen und
Materialseilbahnen, Stromleitungen, Wald, Fels und Geröll sowie bekannte
Gleitschirm-Startplätze. Ergebnis: je eine GeoJSON-Datei in daten/osm/.
Lizenz der Daten: ODbL, © OpenStreetMap-Mitwirkende.
"""

import json
import sys
import time
from datetime import datetime, timezone

import requests
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.ops import polygonize, unary_union

from gemeinsam import DATEN, einstellungen, testgebiet_wgs84

# Name der Ausgabedatei -> Overpass-Filter (ohne Begrenzungsrechteck)
THEMEN = {
    "wege_strassen": ['way["highway"]'],
    "seilbahnen": ['way["aerialway"]', 'node["aerialway"]'],
    "stromleitungen": [
        'way["power"~"^(line|minor_line|cable)$"]',
        'node["power"~"^(tower|pole)$"]',
    ],
    "wald": [
        'way["landuse"="forest"]', 'relation["landuse"="forest"]',
        'way["natural"="wood"]', 'relation["natural"="wood"]',
        'way["natural"~"^(scrub|heath)$"]', 'relation["natural"~"^(scrub|heath)$"]',
    ],
    "fels_geroell": [
        'way["natural"~"^(bare_rock|scree|shingle|cliff|rock|stone)$"]',
        'relation["natural"~"^(bare_rock|scree|shingle)$"]',
        'node["natural"~"^(rock|stone)$"]',
    ],
    "startplaetze_osm": [
        'nwr["sport"="free_flying"]',
        'nwr["free_flying:site"]',
        'nwr["free_flying:paragliding"]',
    ],
}

FLAECHEN_ZEICHEN = ("landuse", "natural", "building", "area")


def overpass(e, abfrage):
    o = e["osm"]
    letzter = None
    for versuch in range(3):
        for url in o["overpass_urls"]:
            try:
                r = requests.post(url, data={"data": abfrage},
                                  headers={"User-Agent": o["user_agent"]}, timeout=200)
                if r.status_code == 200:
                    return r.json()
                letzter = f"{url}: HTTP {r.status_code}"
            except requests.RequestException as ex:
                letzter = f"{url}: {ex}"
        time.sleep(10 * (versuch + 1))
    raise RuntimeError(f"Overpass nicht erreichbar ({letzter})")


def ist_flaeche(el):
    t = el.get("tags", {})
    if t.get("area") == "no" or "highway" in t or "aerialway" in t or "power" in t:
        return False
    if t.get("natural") == "cliff":
        return False
    return any(k in t for k in FLAECHEN_ZEICHEN)


def geometrie(el):
    if el["type"] == "node":
        return Point(el["lon"], el["lat"])
    if el["type"] == "way":
        pts = [(p["lon"], p["lat"]) for p in el.get("geometry", []) if p]
        if len(pts) < 2:
            return None
        if ist_flaeche(el) and len(pts) >= 4 and pts[0] == pts[-1]:
            return Polygon(pts)
        return LineString(pts)
    if el["type"] == "relation":
        aussen, innen = [], []
        for m in el.get("members", []):
            if m.get("type") != "way" or not m.get("geometry"):
                continue
            pts = [(p["lon"], p["lat"]) for p in m["geometry"] if p]
            if len(pts) >= 2:
                (innen if m.get("role") == "inner" else aussen).append(LineString(pts))
        if not aussen:
            return None
        flaeche = unary_union(list(polygonize(unary_union(aussen))))
        if innen:
            flaeche = flaeche.difference(unary_union(list(polygonize(unary_union(innen)))))
        return None if flaeche.is_empty else flaeche
    return None


def main():
    e = einstellungen()
    w, s, o, n = testgebiet_wgs84(e)
    bbox = f"({s:.6f},{w:.6f},{n:.6f},{o:.6f})"
    ziel = DATEN / "osm"
    ziel.mkdir(parents=True, exist_ok=True)
    stand = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ok = True
    for name, filter_ in THEMEN.items():
        abfrage = "[out:json][timeout:180];(" + "".join(f"{f}{bbox};" for f in filter_) + ");out geom;"
        print(f"Lade {name} …")
        try:
            daten = overpass(e, abfrage)
        except RuntimeError as ex:
            print(f"  FEHLER: {ex}")
            ok = False
            continue
        features = []
        for el in daten["elements"]:
            g = geometrie(el)
            if g is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": mapping(g),
                "properties": {"osm_id": f"{el['type']}/{el['id']}", **el.get("tags", {})},
            })
        fc = {
            "type": "FeatureCollection",
            "name": name,
            "quelle": "© OpenStreetMap-Mitwirkende, ODbL 1.0",
            "abgerufen": stand,
            "features": features,
        }
        (ziel / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(features)} Objekte")
        time.sleep(5)  # Overpass schonen
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
