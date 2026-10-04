"""Schritt 4: Untergrund für das Testgebiet laden (Realnutzungskarte + Infrarot-Orthofoto).

Quellen (siehe daten/QUELLEN.md):
- Realnutzungskarte 1:10.000 der Provinz Bozen (WFS, CC0, Stand 2005)
- Orthofoto 2023 Infrarot/CIR der Provinz Bozen (WMS, CC BY 4.0)

Beide werden auf das Raster des Geländemodells (2,5 m) umgerechnet.
Eingabe:  rohdaten/dgm_2_5m.tif (nur als Bezugsraster)
Ausgabe:  rohdaten/realnutzung_2_5m.tif  – Klassencode (Feld CODE) je Zelle
          rohdaten/vegetation_2_5m.tif   – Vegetationsindex aus dem CIR-Bild
          rohdaten/realnutzung.geojson   – Flächen der Realnutzungskarte
(alles nicht im Repository)
"""

import json
import time
import warnings

import numpy as np
import rasterio
import requests
from rasterio.features import rasterize
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from shapely.geometry import shape

from gemeinsam import ROHDATEN, einstellungen, testgebiet_utm

# Die Bildkacheln haben keine Georeferenz; sie wird unten selbst gesetzt.
warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)


def abrufen(url, params, versuche=4):
    for versuch in range(versuche):
        try:
            r = requests.get(url, params=params, timeout=300)
            if r.status_code == 200:
                return r
            fehler = f"HTTP {r.status_code}: {r.text[:200]!r}"
        except requests.RequestException as ex:
            fehler = str(ex)
        time.sleep(2 ** (versuch + 1))
    raise RuntimeError(f"{url} nicht erreichbar ({fehler})")


def realnutzung_laden(e, bezug):
    rn = e["realnutzung"]
    w, s, o, n = testgebiet_utm(e, mit_rand=True)
    r = abrufen(rn["wfs_url"], {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": rn["layer"], "outputFormat": "application/json",
        "srsName": "EPSG:25832", "bbox": f"{w},{s},{o},{n},EPSG:25832",
    })
    fc = r.json()
    (ROHDATEN / "realnutzung.geojson").write_text(json.dumps(fc), encoding="utf-8")
    formen = [(shape(f["geometry"]), int(f["properties"]["CODE"]))
              for f in fc["features"] if f.get("geometry") and f["properties"].get("CODE")]
    print(f"  Realnutzungskarte: {len(formen)} Flächen")
    raster = rasterize(formen, out_shape=(bezug.height, bezug.width),
                       transform=bezug.transform, fill=0, dtype="int32")
    profil = bezug.profile | {"dtype": "int32", "nodata": 0, "compress": "deflate"}
    with rasterio.open(ROHDATEN / "realnutzung_2_5m.tif", "w", **profil) as ds:
        ds.write(raster, 1)
    werte, anzahl = np.unique(raster, return_counts=True)
    zelle = abs(bezug.transform.a * bezug.transform.e)
    namen = {int(f["properties"]["CODE"]): f["properties"]["NAME_DE"]
             for f in fc["features"] if f["properties"].get("CODE")}
    for wert, a in sorted(zip(werte, anzahl), key=lambda x: -x[1]):
        print(f"    {wert:>6} {namen.get(int(wert), 'ohne Angabe'):<45} {a * zelle / 1e4:8.1f} ha")


def cir_laden(e, bezug):
    """Lädt das Infrarotbild kachelweise und berechnet den Vegetationsindex."""
    of = e["orthofoto"]
    res = of["cir_aufloesung_m"]
    px = of["cir_kachel_px"]
    kante = px * res
    w, s, o, n = testgebiet_utm(e, mit_rand=True)
    nx = int(np.ceil((o - w) / kante))
    ny = int(np.ceil((n - s) / kante))
    bild = np.zeros((3, ny * px, nx * px), dtype="uint8")
    for iy in range(ny):
        for ix in range(nx):
            x0 = w + ix * kante
            y1 = n - iy * kante
            r = abrufen(of["wms_url"], {
                "service": "WMS", "version": "1.3.0", "request": "GetMap",
                "layers": of["cir_layer"], "styles": "", "crs": "EPSG:25832",
                "bbox": f"{x0},{y1 - kante},{x0 + kante},{y1}",
                "width": px, "height": px, "format": "image/png",
            })
            if not r.headers.get("Content-Type", "").startswith("image/"):
                raise RuntimeError(f"CIR-Kachel {ix},{iy}: keine Bilddatei ({r.text[:200]!r})")
            with MemoryFile(r.content) as mf, mf.open() as ds:
                bild[:, iy * px:(iy + 1) * px, ix * px:(ix + 1) * px] = ds.read([1, 2, 3])
            print(f"  CIR-Kachel {iy * nx + ix + 1}/{nx * ny}")
    # Im CIR-Bild steht Infrarot im ersten Kanal (rot dargestellt), Rot im zweiten.
    nir = bild[0].astype("float32")
    rot = bild[1].astype("float32")
    index = (nir - rot) / np.maximum(nir + rot, 1)
    index[(nir + rot) == 0] = np.nan  # außerhalb des Bildes
    quelle = from_origin(w, n, res, res)
    ziel = np.full((bezug.height, bezug.width), np.nan, dtype="float32")
    reproject(index, ziel, src_transform=quelle, src_crs="EPSG:25832", src_nodata=np.nan,
              dst_transform=bezug.transform, dst_crs=bezug.crs, dst_nodata=np.nan,
              resampling=Resampling.average)
    profil = bezug.profile | {"dtype": "float32", "nodata": np.nan, "compress": "deflate",
                              "predictor": 3}
    with rasterio.open(ROHDATEN / "vegetation_2_5m.tif", "w", **profil) as ds:
        ds.write(ziel, 1)
    kahl = np.nanmean(ziel < e["untergrund"]["vegetation_ab"])
    print(f"  Vegetationsindex: Median {np.nanmedian(ziel):.2f}, "
          f"{100 * kahl:.0f} % der Fläche unter {e['untergrund']['vegetation_ab']} (kahl)")


def main():
    e = einstellungen()
    with rasterio.open(ROHDATEN / "dgm_2_5m.tif") as bezug:
        print("Lade Realnutzungskarte …")
        realnutzung_laden(e, bezug)
        print("Lade Infrarot-Orthofoto …")
        cir_laden(e, bezug)


if __name__ == "__main__":
    main()
