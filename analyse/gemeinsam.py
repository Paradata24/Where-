"""Gemeinsame Hilfsfunktionen für alle Analyse-Skripte."""

import tomllib
from pathlib import Path

from pyproj import Transformer

PROJEKT = Path(__file__).resolve().parent.parent
ROHDATEN = PROJEKT / "rohdaten"
ERGEBNISSE = PROJEKT / "ergebnisse"
DATEN = PROJEKT / "daten"


def einstellungen():
    """Liest einstellungen/einstellungen.toml."""
    with open(PROJEKT / "einstellungen" / "einstellungen.toml", "rb") as f:
        return tomllib.load(f)


def testgebiet_utm(e=None):
    """Rechteck des Testgebiets in EPSG:25832: (west, sued, ost, nord)."""
    e = e or einstellungen()
    t = e["testgebiet"]
    h = t["kantenlaenge_m"] / 2
    return (t["mitte_x"] - h, t["mitte_y"] - h, t["mitte_x"] + h, t["mitte_y"] + h)


def testgebiet_wgs84(e=None):
    """Rechteck des Testgebiets in Längen-/Breitengrad: (west, sued, ost, nord).

    Etwas größer als das UTM-Rechteck, damit es dieses vollständig umschließt.
    """
    e = e or einstellungen()
    w, s, o, n = testgebiet_utm(e)
    t = Transformer.from_crs(e["testgebiet"]["crs"], "EPSG:4326", always_xy=True)
    ecken = [t.transform(x, y) for x in (w, o) for y in (s, n)]
    lons = [p[0] for p in ecken]
    lats = [p[1] for p in ecken]
    return (min(lons), min(lats), max(lons), max(lats))
