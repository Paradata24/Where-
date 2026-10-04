"""Schritt 3: Bekannte Startplätze aus paraglidingearth.com laden.

Lizenz: CC BY-SA 3.0 (neuere Beiträge zusätzlich ODbL 1.0), © ParaglidingEarth-Mitwirkende.
Die DHV-Geländedatenbank wird bewusst NICHT geladen: Ihre Nutzungsbedingungen
verbieten Vervielfältigung und Veröffentlichung (siehe daten/QUELLEN.md).
Ergebnis: daten/startplaetze/<gebiet>/paraglidingearth.geojson
Aufruf: python 03_startplaetze_laden.py [gebiet …]  (ohne Angabe: alle Gebiete)
"""

import json
import sys
from datetime import datetime, timezone

import requests

from gemeinsam import einstellungen, gebiete

# Die Schnittstelle antwortet derzeit nur über http zuverlässig
PGE_URL = "http://www.paraglidingearth.com/api/geojson/getBoundingBoxSites.php"


def main():
    e = einstellungen()
    ok = True
    for gebiet in gebiete(e):
        print(f"{gebiet.name}:")
        ok &= gebiet_laden(e, gebiet)
    sys.exit(0 if ok else 1)


def gebiet_laden(e, gebiet):
    w, s, o, n = gebiet.wgs84()
    r = requests.get(PGE_URL, params={"north": n, "south": s, "east": o, "west": w,
                                      "style": "detailled"},
                     headers={"User-Agent": e["osm"]["user_agent"]}, timeout=60)
    if r.status_code != 200:
        print(f"FEHLER: HTTP {r.status_code}")
        return False
    fc = r.json()
    fc["quelle"] = "© ParaglidingEarth-Mitwirkende, CC BY-SA 3.0 (www.paraglidingearth.com)"
    fc["abgerufen"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ziel = gebiet.startplaetze
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "paraglidingearth.geojson").write_text(
        json.dumps(fc, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in fc["features"]:
        p = f["properties"]
        print(f"  {p['name']} ({p.get('takeoff_altitude')} m): {f['geometry']['coordinates']}")
    print(f"  {len(fc['features'])} Startplätze gespeichert")
    return True


if __name__ == "__main__":
    main()
