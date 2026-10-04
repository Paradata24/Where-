"""Schritt 1: DGM und DOM (2,5 m) der Provinz Bozen je Gebiet (mit Rand) laden.

Quelle: WCS der Autonomen Provinz Bozen (siehe daten/QUELLEN.md).
Ergebnis: rohdaten/<gebiet>/dgm_2_5m.tif und dom_2_5m.tif (nicht im Repository).
Aufruf: python 01_hoehenmodelle_laden.py [gebiet …]  (ohne Angabe: alle Gebiete)
"""

import sys
import time

import requests

from gemeinsam import einstellungen, gebiete


def coverage_laden(e, gebiet, layer, ziel):
    h = e["hoehenmodelle"]
    w, s, o, n = gebiet.utm(mit_rand=True)
    # GeoServer schreibt bei WCS 2.0 "__" statt ":" in der Coverage-ID
    ids = [layer.replace(":", "__"), layer]
    fehler = []
    for cov in ids:
        params = [
            ("service", "WCS"),
            ("version", h["wcs_version"]),
            ("request", "GetCoverage"),
            ("coverageId", cov),
            ("format", "image/tiff"),
            ("subset", f"E({w},{o})"),
            ("subset", f"N({s},{n})"),
        ]
        for versuch in range(4):
            try:
                r = requests.get(h["wcs_url"], params=params, timeout=300)
            except requests.RequestException as ex:
                fehler.append(f"{cov}: {ex}")
                time.sleep(2 ** (versuch + 1))
                continue
            if r.status_code == 200 and r.content[:4] in (b"II*\x00", b"MM\x00*"):
                ziel.write_bytes(r.content)
                print(f"  gespeichert: {ziel} ({len(r.content) / 1e6:.1f} MB)")
                return
            fehler.append(f"{cov}: HTTP {r.status_code} {r.text[:200]!r}")
            if r.status_code < 500:
                break  # falsche Coverage-ID o. Ä. – nächste ID probieren
            time.sleep(2 ** (versuch + 1))
    raise RuntimeError(f"{layer} konnte nicht geladen werden:\n  " + "\n  ".join(fehler))


def main():
    e = einstellungen()
    h = e["hoehenmodelle"]
    ok = True
    for gebiet in gebiete(e):
        gebiet.rohdaten.mkdir(parents=True, exist_ok=True)
        for layer, datei in ((h["dgm_layer"], "dgm_2_5m.tif"), (h["dom_layer"], "dom_2_5m.tif")):
            print(f"{gebiet.name}: lade {layer} …")
            try:
                coverage_laden(e, gebiet, layer, gebiet.rohdaten / datei)
            except RuntimeError as ex:
                print(ex)
                ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
