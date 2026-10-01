"""Schritt 3: Bekannte Startplätze aus paraglidingearth.com laden.

Lizenz: CC BY-SA 3.0 (neuere Beiträge zusätzlich ODbL 1.0), © ParaglidingEarth-Mitwirkende.
Die DHV-Geländedatenbank wird bewusst NICHT geladen: Ihre Nutzungsbedingungen
verbieten Vervielfältigung und Veröffentlichung (siehe daten/QUELLEN.md).
Ergebnis: daten/startplaetze/paraglidingearth.geojson
"""

import json
import sys
from datetime import datetime, timezone

import requests

from gemeinsam import DATEN, einstellungen, testgebiet_wgs84

# Die Schnittstelle antwortet derzeit nur über http zuverlässig
PGE_URL = "http://www.paraglidingearth.com/api/geojson/getBoundingBoxSites.php"


def main():
    e = einstellungen()
    w, s, o, n = testgebiet_wgs84(e)
    r = requests.get(PGE_URL, params={"north": n, "south": s, "east": o, "west": w,
                                      "style": "detailled"},
                     headers={"User-Agent": e["osm"]["user_agent"]}, timeout=60)
    if r.status_code != 200:
        print(f"FEHLER: HTTP {r.status_code}")
        sys.exit(1)
    fc = r.json()
    fc["quelle"] = "© ParaglidingEarth-Mitwirkende, CC BY-SA 3.0 (www.paraglidingearth.com)"
    fc["abgerufen"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ziel = DATEN / "startplaetze"
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "paraglidingearth.geojson").write_text(
        json.dumps(fc, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in fc["features"]:
        p = f["properties"]
        print(f"  {p['name']} ({p.get('takeoff_altitude')} m): {f['geometry']['coordinates']}")
    print(f"{len(fc['features'])} Startplätze gespeichert")


if __name__ == "__main__":
    main()
