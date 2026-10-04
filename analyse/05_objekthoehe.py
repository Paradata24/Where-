"""Schritt 5: Objekthöhe (DOM minus DGM) berechnen und prüfen.

Je Gebiet:
Eingabe:  rohdaten/<gebiet>/dgm_2_5m.tif, dom_2_5m.tif, realnutzung_2_5m.tif
Ausgabe:  rohdaten/<gebiet>/objekthoehe_2_5m.tif (nicht im Repository),
          ergebnisse/<gebiet>/objekthoehe_zusammenfassung.json,
          docs/vorschau/<gebiet>/objekthoehe.png
Aufruf: python 05_objekthoehe.py [gebiet …]  (ohne Angabe: alle Gebiete)
"""

import json

import matplotlib
import numpy as np
import rasterio

from gemeinsam import einstellungen, gebiete

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def lesen(pfad):
    with rasterio.open(pfad) as ds:
        a = ds.read(1, masked=True).astype("float64")
        return a.filled(np.nan), ds.profile, ds.transform, ds.crs


def main():
    e = einstellungen()
    for gebiet in gebiete(e):
        print(f"{gebiet.name}:")
        auswerten(e, gebiet)


def auswerten(e, gebiet):
    oh = e["objekthoehe"]
    dgm, profil, transform, crs = lesen(gebiet.rohdaten / "dgm_2_5m.tif")
    dom, profil_dom, transform_dom, _ = lesen(gebiet.rohdaten / "dom_2_5m.tif")

    pruefungen = []
    if dgm.shape != dom.shape or transform != transform_dom:
        pruefungen.append(f"DGM und DOM haben unterschiedliche Raster: {dgm.shape} / {dom.shape}")
        raise SystemExit(pruefungen[-1])

    ndom = dom - dgm
    zelle = abs(transform.a * transform.e)  # m² pro Zelle
    gueltig = np.isfinite(ndom)
    n = int(gueltig.sum())
    v = ndom[gueltig]

    baum = gueltig & (ndom >= oh["baum_ab_m"])
    zu_hoch = gueltig & (ndom > oh["unplausibel_ab_m"])
    negativ = gueltig & (ndom < oh["negativ_grenze_m"])

    hoehen_baum = ndom[baum]
    perz = {f"p{p}": round(float(np.percentile(hoehen_baum, p)), 1) for p in (10, 25, 50, 75, 90, 99)} \
        if hoehen_baum.size else {}

    # Vergleich mit dem Wald der Realnutzungskarte (Schritt 4)
    vergleich = {}
    rn_pfad = gebiet.rohdaten / "realnutzung_2_5m.tif"
    if rn_pfad.exists():
        with rasterio.open(rn_pfad) as ds:
            karte_wald = np.isin(ds.read(1), e["realnutzung"]["wald"]) & gueltig
        vergleich = {
            "karte_wald_ha": round(karte_wald.sum() * zelle / 1e4, 1),
            "anteil_karte_wald_mit_objekt_ueber_grenze": round(float((baum & karte_wald).sum() / max(karte_wald.sum(), 1)), 3),
            "objekt_ueber_grenze_ausserhalb_karte_wald_ha": round(float((baum & ~karte_wald).sum() * zelle / 1e4), 1),
            "median_objekthoehe_im_karte_wald_m": round(float(np.nanmedian(ndom[karte_wald])), 1) if karte_wald.any() else None,
        }

    zus = {
        "flaeche_gesamt_ha": round(n * zelle / 1e4, 1),
        "zellen_ohne_wert": int((~gueltig).sum()),
        "dgm_hoehe_min_max_m": [round(float(np.nanmin(dgm)), 1), round(float(np.nanmax(dgm)), 1)],
        "baum_grenze_m": oh["baum_ab_m"],
        "flaeche_objekt_ueber_grenze_ha": round(baum.sum() * zelle / 1e4, 1),
        "anteil_objekt_ueber_grenze": round(float(baum.sum() / n), 3),
        "objekthoehe_baumzellen_perzentile_m": perz,
        "objekthoehe_max_m": round(float(v.max()), 1),
        "objekthoehe_min_m": round(float(v.min()), 1),
        "zellen_unplausibel_hoch": int(zu_hoch.sum()),
        "zellen_negativ": int(negativ.sum()),
        "anteil_genau_null": round(float((np.abs(v) < 0.01).sum() / n), 3),
        "vergleich_realnutzung_wald": vergleich,
    }
    gebiet.ergebnisse.mkdir(parents=True, exist_ok=True)
    (gebiet.ergebnisse / "objekthoehe_zusammenfassung.json").write_text(
        json.dumps(zus, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(zus, ensure_ascii=False, indent=2))

    profil.update(dtype="float32", nodata=-9999, compress="deflate", predictor=3)
    with rasterio.open(gebiet.rohdaten / "objekthoehe_2_5m.tif", "w", **profil) as ds:
        ds.write(np.where(gueltig, ndom, -9999).astype("float32"), 1)

    # Vorschaubild
    vorschau = gebiet.vorschau
    vorschau.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(14, 7))
    im = ax[0].imshow(np.clip(ndom, 0, 40), cmap="YlGn", interpolation="nearest")
    ax[0].set_title(f"{gebiet.name}: Objekthöhe DOM − DGM (m, 0–40)")
    fig.colorbar(im, ax=ax[0], fraction=0.046)
    ax[1].hist(np.clip(v, -5, 60), bins=130, color="#3a7d44")
    ax[1].set_yscale("log")
    ax[1].set_title("Häufigkeit der Objekthöhen (log)")
    ax[1].set_xlabel("m")
    for a in ax[:1]:
        a.set_xticks([]), a.set_yticks([])
    fig.tight_layout()
    fig.savefig(vorschau / "objekthoehe.png", dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    main()
