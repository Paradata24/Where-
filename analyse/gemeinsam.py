"""Gemeinsame Hilfsfunktionen für alle Analyse-Skripte."""

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pyproj import Transformer

PROJEKT = Path(__file__).resolve().parent.parent
ROHDATEN = PROJEKT / "rohdaten"
ERGEBNISSE = PROJEKT / "ergebnisse"
DATEN = PROJEKT / "daten"
WEB_DATEN = PROJEKT / "docs" / "daten"
VORSCHAU = PROJEKT / "docs" / "vorschau"


def einstellungen():
    """Liest einstellungen/einstellungen.toml."""
    with open(PROJEKT / "einstellungen" / "einstellungen.toml", "rb") as f:
        return tomllib.load(f)


@dataclass
class Gebiet:
    """Ein quadratisches Rechengebiet aus [gebiete] in den Einstellungen."""

    kuerzel: str
    name: str
    mitte_x: float
    mitte_y: float
    kantenlaenge_m: float
    rand_m: float
    crs: str

    def utm(self, mit_rand=False):
        """Rechteck in EPSG:25832: (west, sued, ost, nord).

        mit_rand=True: um den Rand vergrößert (Berechnungsgebiet).
        """
        h = self.kantenlaenge_m / 2 + (self.rand_m if mit_rand else 0)
        return (self.mitte_x - h, self.mitte_y - h, self.mitte_x + h, self.mitte_y + h)

    def wgs84(self, mit_rand=False):
        """Rechteck in Längen-/Breitengrad: (west, sued, ost, nord).

        Etwas größer als das UTM-Rechteck, damit es dieses vollständig umschließt.
        """
        w, s, o, n = self.utm(mit_rand)
        t = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)
        ecken = [t.transform(x, y) for x in (w, o) for y in (s, n)]
        lons = [p[0] for p in ecken]
        lats = [p[1] for p in ecken]
        return (min(lons), min(lats), max(lons), max(lats))

    # Ordner je Gebiet
    @property
    def rohdaten(self):
        return ROHDATEN / self.kuerzel

    @property
    def osm(self):
        return DATEN / "osm" / self.kuerzel

    @property
    def startplaetze(self):
        return DATEN / "startplaetze" / self.kuerzel

    @property
    def ergebnisse(self):
        return ERGEBNISSE / self.kuerzel

    @property
    def web(self):
        return WEB_DATEN / self.kuerzel

    @property
    def vorschau(self):
        return VORSCHAU / self.kuerzel


def gebiete(e=None, auswahl=None):
    """Alle Gebiete aus den Einstellungen.

    auswahl: Liste von Kürzeln; ohne Angabe werden die Kürzel aus der
    Befehlszeile genommen (z. B. "python 06_kandidaten.py rittner_horn"),
    und wenn dort keine stehen, alle Gebiete.
    """
    e = e or einstellungen()
    g = e["gebiete"]
    alle = [Gebiet(kuerzel=x["kuerzel"], name=x["name"], mitte_x=x["mitte_x"],
                   mitte_y=x["mitte_y"], kantenlaenge_m=g["kantenlaenge_m"],
                   rand_m=g["rand_m"], crs=g["crs"]) for x in g["liste"]]
    auswahl = auswahl if auswahl is not None else sys.argv[1:]
    if not auswahl:
        return alle
    unbekannt = set(auswahl) - {x.kuerzel for x in alle}
    if unbekannt:
        raise SystemExit(f"Unbekannte Gebiete: {sorted(unbekannt)}. "
                         f"Vorhanden: {[x.kuerzel for x in alle]}")
    return [x for x in alle if x.kuerzel in auswahl]
