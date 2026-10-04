"""Schritt 0: Prüfen, ob alle Datenquellen erreichbar sind (Phase 1).

Läuft lokal oder in GitHub Actions. Lädt nur kleine Proben herunter und
speichert nichts im Repository. Der Bericht erscheint in der Konsole und –
in GitHub Actions – zusätzlich als Zusammenfassung auf der Seite des Laufs.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import rasterio
import requests

from gemeinsam import einstellungen, gebiete

ZEILEN = []


def melden(ok, was, details=""):
    zeichen = "✅" if ok else "❌"
    ZEILEN.append(f"| {zeichen} | {was} | {details} |")
    print(f"{zeichen} {was}: {details}")
    return ok


def kachel_laden(url, layer, w, s, kante, ziel):
    """Lädt ein quadratisches Stück eines Höhenmodells über WCS 2.0."""
    params = [
        ("service", "WCS"),
        ("version", "2.0.1"),
        ("request", "GetCoverage"),
        ("coverageId", layer.replace(":", "__")),
        ("format", "image/tiff"),
        ("subset", f"E({w},{w + kante})"),
        ("subset", f"N({s},{s + kante})"),
    ]
    t0 = time.time()
    r = requests.get(url, params=params, timeout=600)
    dauer = time.time() - t0
    if r.status_code != 200 or r.content[:4] not in (b"II*\x00", b"MM\x00*"):
        return None, f"HTTP {r.status_code}, {r.text[:150]!r}"
    ziel.write_bytes(r.content)
    with rasterio.open(ziel) as ds:
        a = ds.read(1)
        gueltig = a != ds.nodata if ds.nodata is not None else np.ones(a.shape, bool)
        info = (
            f"{len(r.content) / 1e6:.0f} MB in {dauer:.0f} s, {ds.width}×{ds.height} Zellen, "
            f"{ds.res[0]} m, {ds.crs}, gültig {100 * gueltig.mean():.0f} %"
        )
        if gueltig.any():
            info += f", Höhe {a[gueltig].min():.0f}–{a[gueltig].max():.0f} m"
    return (a, gueltig), info


def main():
    e = einstellungen()
    h = e["hoehenmodelle"]
    t = gebiete(e, auswahl=[])[0]  # Proben im ersten Gebiet
    url = h["wcs_url"]
    alles_ok = True

    # 1) Dienstbeschreibung des WCS
    try:
        r = requests.get(
            url,
            params={"service": "WCS", "version": "2.0.1", "request": "GetCapabilities"},
            timeout=120,
        )
        ids = [h["dgm_layer"].replace(":", "__"), h["dom_layer"].replace(":", "__")]
        fehlt = [i for i in ids if i not in r.text]
        alles_ok &= melden(
            r.status_code == 200 and not fehlt,
            "WCS-Dienst der Provinz (GetCapabilities)",
            f"HTTP {r.status_code}" + (f", fehlt: {fehlt}" if fehlt else ", DGM und DOM vorhanden"),
        )
    except requests.RequestException as ex:
        alles_ok &= melden(False, "WCS-Dienst der Provinz (GetCapabilities)", str(ex)[:150])

    # 2) Probe 1 × 1 km am Rittner Horn: DGM und DOM, dazu Objekthöhe
    w = round(t.mitte_x - 500, -3)
    s = round(t.mitte_y - 500, -3)
    with tempfile.TemporaryDirectory() as tmp:
        proben = {}
        for name, layer in (("DGM", h["dgm_layer"]), ("DOM", h["dom_layer"])):
            try:
                ergebnis, info = kachel_laden(url, layer, w, s, 1000, Path(tmp) / f"{name}.tif")
            except requests.RequestException as ex:
                ergebnis, info = None, str(ex)[:150]
            alles_ok &= melden(ergebnis is not None, f"{name} 2,5 m, Probe 1 × 1 km", info)
            proben[name] = ergebnis
        if proben["DGM"] and proben["DOM"]:
            (dgm, g1), (dom, g2) = proben["DGM"], proben["DOM"]
            diff = (dom - dgm)[g1 & g2]
            anteil = 100 * (diff >= e["objekthoehe"]["baum_ab_m"]).mean()
            melden(
                True,
                "Objekthöhe (DOM minus DGM) in der Probe",
                f"max. {diff.max():.1f} m, {anteil:.0f} % der Zellen ≥ {e['objekthoehe']['baum_ab_m']} m",
            )

        # 3) Große Kachel 20 × 20 km: liefert der Server so große Stücke?
        kante = e["gesamtgebiet"]["kachel_m"]
        try:
            ergebnis, info = kachel_laden(url, h["dgm_layer"], w - 10000, s - 10000, kante,
                                          Path(tmp) / "gross.tif")
        except requests.RequestException as ex:
            ergebnis, info = None, str(ex)[:150]
        alles_ok &= melden(ergebnis is not None, f"DGM 2,5 m, große Kachel {kante // 1000} × {kante // 1000} km", info)

    # 4) OpenStreetMap: Overpass (Abfrage) oder Geofabrik (fertiger Auszug).
    #    Eine der beiden Quellen genügt. Overpass ist oft überlastet.
    osm_ok = False
    abfrage = '[out:json][timeout:60];node["sport"="free_flying"](46.6,11.4,46.7,11.6);out count;'
    for o_url in e["osm"]["overpass_urls"]:
        name = f"OpenStreetMap Overpass ({o_url.split('/')[2]})"
        details = ""
        for versuch in range(3):
            try:
                r = requests.post(o_url, data={"data": abfrage}, timeout=120,
                                  headers={"User-Agent": e["osm"]["user_agent"]})
                details = f"HTTP {r.status_code}"
                if r.status_code == 200 and "elements" in r.text:
                    osm_ok = True
                    break
            except requests.RequestException as ex:
                details = str(ex)[:150]
            time.sleep(10 * (versuch + 1))
        melden(osm_ok, name, details + (f" (nach {versuch + 1} Versuch(en))" if osm_ok else ", 3 Versuche"))
        if osm_ok:
            break

    g_url = e["osm"]["geofabrik_url"]
    try:
        r = requests.head(g_url, timeout=60, allow_redirects=True,
                          headers={"User-Agent": e["osm"]["user_agent"]})
        groesse = int(r.headers.get("Content-Length", 0)) / 1e6
        g_ok = r.status_code == 200 and groesse > 0
        melden(g_ok, f"OpenStreetMap Geofabrik ({g_url.rsplit('/', 1)[1]})",
               f"HTTP {r.status_code}, {groesse:.0f} MB, Stand {r.headers.get('Last-Modified', '?')}")
        osm_ok |= g_ok
    except requests.RequestException as ex:
        melden(False, "OpenStreetMap Geofabrik", str(ex)[:150])
    alles_ok &= osm_ok

    bericht = "## Datenprüfung Startplatz-Finder\n\n| | Prüfung | Ergebnis |\n|---|---|---|\n"
    bericht += "\n".join(ZEILEN) + "\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(bericht)
    sys.exit(0 if alles_ok else 1)


if __name__ == "__main__":
    main()
