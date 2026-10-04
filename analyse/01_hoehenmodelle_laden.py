"""Schritt 1: DGM und DOM (2,5 m) der Provinz Bozen für das Testgebiet (mit Rand) laden.

Quelle: WCS der Autonomen Provinz Bozen (siehe daten/QUELLEN.md).
Ergebnis: rohdaten/dgm_2_5m.tif und rohdaten/dom_2_5m.tif (nicht im Repository).
"""

import sys
import time

import requests

from gemeinsam import ROHDATEN, einstellungen, testgebiet_utm


def coverage_laden(e, layer, ziel):
    h = e["hoehenmodelle"]
    w, s, o, n = testgebiet_utm(e, mit_rand=True)
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
    ROHDATEN.mkdir(exist_ok=True)
    h = e["hoehenmodelle"]
    ok = True
    for layer, datei in ((h["dgm_layer"], "dgm_2_5m.tif"), (h["dom_layer"], "dom_2_5m.tif")):
        print(f"Lade {layer} …")
        try:
            coverage_laden(e, layer, ROHDATEN / datei)
        except RuntimeError as ex:
            print(ex)
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
