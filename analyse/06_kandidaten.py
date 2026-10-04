"""Schritt 6: Kandidaten für Startplätze berechnen (Methode nach Egger 2022, Kap. 8.2).

Für jede der 16 Startrichtungen:
  1. Zellen mit passender Neigung, Ausrichtung und Untergrund suchen.
  2. „Startbahn“: Mehrheitsfilter in einem Kreisbogen in Startrichtung.
  3. Zusammenhängende Flächen ab Mindestgröße bilden; höchster Punkt = Startpunkt.
  4. Rasterbasierte Hindernisprüfung im Dreieck vor dem Startpunkt
     (Gleitlinie gegen Gelände + Objekthöhe + Leitungen aus OSM).
Danach werden Startpunkte verschiedener Richtungen, die nahe beieinander
liegen, zu einem Kandidaten zusammengefasst.

Eingabe:  rohdaten/dgm_2_5m.tif, rohdaten/dom_2_5m.tif,
          rohdaten/realnutzung_2_5m.tif, rohdaten/vegetation_2_5m.tif (Schritt 4),
          daten/osm/seilbahnen.geojson, stromleitungen.geojson, wege_strassen.geojson
Ausgabe:  ergebnisse/kandidaten.geojson     – Startpunkte mit Eigenschaften
          ergebnisse/startflaechen.geojson  – Startflächen je Richtung
          ergebnisse/kandidaten_info.json   – Stand, Einstellungen, Kennzahlen
          (dieselben Dateien auch in docs/daten/ für die Website)
"""

import json
import shutil
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize, shapes
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely import STRtree
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform as shp_transform

from gemeinsam import DATEN, ERGEBNISSE, PROJEKT, ROHDATEN, einstellungen, testgebiet_utm

SEKTOR_NAMEN_16 = ["N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def sektor_namen(anzahl):
    if anzahl == 16:
        return SEKTOR_NAMEN_16
    if anzahl == 8:
        return SEKTOR_NAMEN_16[::2]
    return [f"{i * 360 / anzahl:.0f}°" for i in range(anzahl)]


def raster(pfad):
    with rasterio.open(pfad) as ds:
        a = ds.read(1, masked=True)
        return a.astype("float64").filled(np.nan), ds.transform, ds.crs, ds.profile


def neigung_ausrichtung(dgm, res):
    """Neigung (Grad) und Ausrichtung (Grad, 0 = Nord, im Uhrzeigersinn; Richtung
    hangabwärts) nach Horn (3 × 3 Zellen)."""
    z = np.where(np.isfinite(dgm), dgm, np.nanmean(dgm))
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]) / (8 * res)
    ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]]) / (8 * res)
    dz_ost = ndimage.correlate(z, kx, mode="nearest")
    dz_nord = ndimage.correlate(z, ky, mode="nearest")
    neigung = np.degrees(np.arctan(np.hypot(dz_ost, dz_nord)))
    ausrichtung = np.degrees(np.arctan2(-dz_ost, -dz_nord)) % 360
    neigung[~np.isfinite(dgm)] = np.nan
    return neigung, ausrichtung


def winkel_abstand(a, b):
    return np.abs((a - b + 180) % 360 - 180)


def versatz_gitter(radius_m, res):
    r = int(np.ceil(radius_m / res))
    zeilen, spalten = np.mgrid[-r:r + 1, -r:r + 1]
    ost = spalten * res
    nord = -zeilen * res
    dist = np.hypot(ost, nord)
    richtung = np.degrees(np.arctan2(ost, nord)) % 360
    return zeilen, spalten, dist, richtung


def bogen_kern(richtung_grad, radius_m, oeffnung_grad, res):
    _, _, dist, richt = versatz_gitter(radius_m, res)
    return ((dist > 0) & (dist <= radius_m)
            & (winkel_abstand(richt, richtung_grad) <= oeffnung_grad / 2)).astype("float64")


def dreieck(richtung_grad, laenge_m, oeffnung_grad, res, ab_m=0.0):
    """Zellen im Abflug-Dreieck (ab Entfernung ab_m): Zeilen-/Spaltenversatz und Entfernung."""
    zeilen, spalten, dist, richt = versatz_gitter(laenge_m, res)
    # Das Dreieck endet an der Linie senkrecht zur Startrichtung (Egger S. 48)
    vorwaerts = dist * np.cos(np.radians(richt - richtung_grad))
    m = ((dist > ab_m) & (vorwaerts <= laenge_m)
         & (winkel_abstand(richt, richtung_grad) <= oeffnung_grad / 2))
    return zeilen[m], spalten[m], dist[m]


def abflug_pruefen(zeilen, spalten, dgm, oberflaeche, dz, ds_, dd, gleitzahl, block=256):
    """Rasterbasierte Hindernisprüfung (Egger S. 52) für viele Startpunkte.

    Frei ist ein Startpunkt, wenn die Gleitlinie im ganzen Dreieck über Gelände
    und Hindernissen bleibt. Gibt (frei, Entfernung der ersten Kollision) zurück.
    """
    frei = np.zeros(len(zeilen), bool)
    erste = np.full(len(zeilen), np.inf)
    hz, hs = oberflaeche.shape
    abfall = dd / gleitzahl
    for a in range(0, len(zeilen), block):
        z = zeilen[a:a + block, None] + dz[None, :]
        s = spalten[a:a + block, None] + ds_[None, :]
        aussen = (z < 0) | (z >= hz) | (s < 0) | (s >= hs)
        hoehe = oberflaeche[np.clip(z, 0, hz - 1), np.clip(s, 0, hs - 1)]
        hoehe[aussen] = np.inf  # außerhalb der Daten: nicht prüfbar = nicht frei
        luft = dgm[zeilen[a:a + block], spalten[a:a + block]][:, None] - abfall[None, :] - hoehe
        kollision = luft < 0
        frei[a:a + block] = ~kollision.any(axis=1)
        erste[a:a + block] = np.where(kollision, dd[None, :], np.inf).min(axis=1)
    return frei, erste


def leitungen_rastern(e, form, transform, crs):
    """Höhe von Seilbahnen und Stromleitungen über Grund als Raster."""
    h = e["hindernisse"]
    hoehe = np.zeros(form, dtype="float64")
    for datei, wert in (("seilbahnen", h["seilbahn_hoehe_m"]),
                        ("stromleitungen", h["stromleitung_hoehe_m"])):
        pfad = DATEN / "osm" / f"{datei}.geojson"
        if not pfad.exists():
            print(f"  Hinweis: {pfad.name} fehlt")
            continue
        gdf = gpd.read_file(pfad)
        gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
        if gdf.empty:
            continue
        gdf = gdf.to_crs(crs)
        r = rasterize(((g, wert) for g in gdf.geometry), out_shape=form,
                      transform=transform, fill=0, all_touched=True, dtype="float64")
        hoehe = np.maximum(hoehe, r)
        print(f"  {datei}: {len(gdf)} Linien, {wert} m über Grund angenommen")
    return hoehe


def runden(obj, stellen=6):
    if isinstance(obj, float):
        return round(obj, stellen)
    if isinstance(obj, (list, tuple)):
        return [runden(o, stellen) for o in obj]
    if isinstance(obj, dict):
        return {k: runden(v, stellen) for k, v in obj.items()}
    return obj


def main():
    e = einstellungen()
    sf, sb, hi = e["startflaeche"], e["startbahn"], e["hindernisse"]
    un, rn = e["untergrund"], e["realnutzung"]

    print("Lese Raster …")
    dgm, transform, crs, _ = raster(ROHDATEN / "dgm_2_5m.tif")
    dom, _, _, _ = raster(ROHDATEN / "dom_2_5m.tif")
    nutzung, _, _, _ = raster(ROHDATEN / "realnutzung_2_5m.tif")
    veg, _, _, _ = raster(ROHDATEN / "vegetation_2_5m.tif")
    res = transform.a
    zelle_m2 = res * res
    form = dgm.shape
    ndom = np.nan_to_num(dom - dgm, nan=0.0)

    # --- Untergrund -------------------------------------------------------
    keine_baeume = ndom < e["objekthoehe"]["baum_ab_m"]
    nicht_kahl = np.nan_to_num(veg, nan=-1) >= un["vegetation_ab"]
    untergrund_ok = np.isin(nutzung, rn["geeignet"]) & nicht_kahl & keine_baeume
    wald_offen = np.zeros(form, bool)
    if un["wald_ohne_baeume_zulassen"]:
        wald_offen = (np.isin(nutzung, rn["wald"]) & keine_baeume & nicht_kahl
                      & (np.nan_to_num(veg, nan=9) < un["wiese_bis"]))
    untergrund_ok |= wald_offen
    print(f"  Untergrund geeignet: {untergrund_ok.sum() * zelle_m2 / 1e4:.0f} ha "
          f"(davon „Wald 2005, heute offen?“: {wald_offen.sum() * zelle_m2 / 1e4:.0f} ha)")

    # --- Hindernisse: Oberfläche, über die die Gleitlinie führen muss --------
    objekt = np.where(ndom >= hi["objekt_ab_m"], ndom, 0.0)
    objekt = np.maximum(objekt, leitungen_rastern(e, form, transform, crs))
    oberflaeche = dgm + objekt + hi["sicherheitsabstand_m"]
    oberflaeche[~np.isfinite(oberflaeche)] = np.inf  # ohne Daten = nicht prüfbar

    neigung, ausrichtung = neigung_ausrichtung(dgm, res)
    neigung_ok = (neigung > sf["neigung_min_grad"]) & (neigung < sf["neigung_max_grad"])

    # Nur Startpunkte innerhalb des Testgebiets (ohne Rand)
    w, s, o, n = testgebiet_utm(e)
    inv = ~transform
    c0, r0 = inv * (w, n)
    c1, r1 = inv * (o, s)
    im_gebiet = np.zeros(form, bool)
    im_gebiet[max(int(r0), 0):int(np.ceil(r1)), max(int(c0), 0):int(np.ceil(c1))] = True

    namen = sektor_namen(sf["sektoren"])
    min_zellen = int(np.ceil(sf["mindestflaeche_m2"] / zelle_m2))
    schritt = max(1, int(round(hi["pruefraster_m"] / res)))
    r_bahn = int(np.ceil(sb["radius_m"] / res))
    punkte, flaechen = [], []
    for k, name in enumerate(namen):
        richtung = k * 360 / sf["sektoren"]
        maske = (neigung_ok & untergrund_ok
                 & (winkel_abstand(ausrichtung, richtung) <= sf["ausrichtung_toleranz_grad"]))
        kern = bogen_kern(richtung, sb["radius_m"], sb["oeffnung_grad"], res)
        anteil = ndimage.correlate(maske.astype("float64"), kern, mode="constant") / kern.sum()
        maske &= anteil > sb["mindestanteil"]

        etiketten, anzahl = ndimage.label(maske, structure=np.ones((3, 3)))
        if anzahl == 0:
            continue
        groessen = np.bincount(etiketten.ravel())
        zu_klein = groessen < min_zellen
        zu_klein[0] = True
        etiketten[zu_klein[etiketten]] = 0
        ids = np.flatnonzero(~zu_klein)

        # Prüfpunkte: Raster mit Abstand pruefraster_m, dazu der höchste Punkt
        # jeder Fläche (Egger: nur der höchste Punkt)
        pruef = np.zeros(form, bool)
        pruef[::schritt, ::schritt] = True
        pruef &= etiketten > 0
        for zi, sj in ndimage.maximum_position(dgm, etiketten, ids):
            pruef[zi, sj] = True
        pruef &= im_gebiet
        rr, cc = np.nonzero(pruef)
        if len(rr) == 0:
            continue
        dz, ds_, dd = dreieck(richtung, hi["laenge_m"], hi["oeffnung_grad"], res,
                              hi["pruefung_ab_m"])
        frei, erste = abflug_pruefen(rr, cc, dgm, oberflaeche, dz, ds_, dd, hi["gleitzahl"])
        fl = etiketten[rr, cc]

        # Freie Prüfpunkte, die im Prüfraster benachbart sind, bilden eine Zone;
        # je Zone wird der höchste freie Punkt der Startpunkt.
        grob = np.zeros((form[0] // schritt + 1, form[1] // schritt + 1), bool)
        grob[rr[frei] // schritt, cc[frei] // schritt] = True
        zonen, _ = ndimage.label(grob, structure=np.ones((3, 3)))
        zone = np.where(frei, zonen[rr // schritt, cc // schritt], 0)
        auswahl = {}
        for i in np.flatnonzero(frei):
            schluessel = (fl[i], zone[i])
            if schluessel not in auswahl or dgm[rr[i], cc[i]] > dgm[rr[auswahl[schluessel]], cc[auswahl[schluessel]]]:
                auswahl[schluessel] = i
        flaechen_mit_frei = {f for f, _ in auswahl}
        # Flächen ganz ohne freien Abflug: höchster Punkt, als „blockiert“ markiert
        for i in np.flatnonzero(~frei):
            if fl[i] in flaechen_mit_frei:
                continue
            schluessel = (fl[i], 0)
            if schluessel not in auswahl or dgm[rr[i], cc[i]] > dgm[rr[auswahl[schluessel]], cc[auswahl[schluessel]]]:
                auswahl[schluessel] = i

        for (nr, _), i in auswahl.items():
            zi, sj = rr[i], cc[i]
            # Neigung/Ausrichtung: Mittel der Startfläche im Umkreis der Startbahn
            umkreis = (etiketten == nr)[max(zi - r_bahn, 0):zi + r_bahn + 1,
                                        max(sj - r_bahn, 0):sj + r_bahn + 1]
            ausschnitt = (slice(max(zi - r_bahn, 0), zi + r_bahn + 1),
                          slice(max(sj - r_bahn, 0), sj + r_bahn + 1))
            a_lokal = np.radians(ausrichtung[ausschnitt][umkreis])
            x, y = transform * (sj + 0.5, zi + 0.5)
            punkte.append({
                "x": x, "y": y, "sektor": name, "richtung": richtung,
                "hoehe": float(dgm[zi, sj]), "frei": bool(frei[i]),
                "erste_kollision_m": None if frei[i] else float(erste[i]),
                "flaeche_m2": float(groessen[nr] * zelle_m2),
                "neigung": float(np.nanmean(neigung[ausschnitt][umkreis])),
                "ausrichtung": float(np.degrees(np.arctan2(np.sin(a_lokal).mean(),
                                                           np.cos(a_lokal).mean())) % 360),
                "wald_hinweis": bool(wald_offen[ausschnitt][umkreis].any()),
                "flaeche_nr": (k, nr),
            })
        # Umrisse der Startflächen mit mindestens einem freien Startpunkt
        objekte = ndimage.find_objects(etiketten)
        for nr in flaechen_mit_frei:
            scheibe = objekte[nr - 1]
            teil = etiketten[scheibe] == nr
            versatz = transform * transform.translation(scheibe[1].start, scheibe[0].start)
            for geom, _ in shapes(teil.astype("uint8"), mask=teil, transform=versatz):
                flaechen.append({"geom": shape(geom).simplify(res), "sektor": name,
                                 "flaeche_nr": (k, nr)})
        n_frei = sum(1 for f, z in auswahl if z > 0)
        print(f"  {name:>3}: {len(ids):4d} Startflächen, {len(rr):6d} Prüfpunkte, "
              f"{n_frei:4d} freie Startpunkte in {len(flaechen_mit_frei):4d} Flächen")

    # --- Zusammenfassen: Startpunkte näher als zusammenfassen_m ---------------
    xy = np.array([[p["x"], p["y"]] for p in punkte]) if punkte else np.zeros((0, 2))
    eltern = list(range(len(punkte)))

    def wurzel(a):
        while eltern[a] != a:
            eltern[a] = eltern[eltern[a]]
            a = eltern[a]
        return a

    for a, b in cKDTree(xy).query_pairs(e["startpunkt"]["zusammenfassen_m"]) if len(xy) else []:
        eltern[wurzel(a)] = wurzel(b)
    gruppen = {}
    for i in range(len(punkte)):
        gruppen.setdefault(wurzel(i), []).append(i)

    # Abstand zum nächsten Weg (nur Eigenschaft, kein Ausschluss)
    wege = gpd.read_file(DATEN / "osm" / "wege_strassen.geojson").to_crs(crs)
    wege = wege[wege.geometry.type.isin(["LineString", "MultiLineString"])]
    baum = STRtree(list(wege.geometry))

    nach_wgs = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
    kandidaten = []
    for nr, glieder in enumerate(sorted(gruppen.values(), key=lambda g: -max(punkte[i]["hoehe"] for i in g))):
        oben = max(glieder, key=lambda i: punkte[i]["hoehe"])
        p = punkte[oben]
        groesste = max(glieder, key=lambda i: punkte[i]["flaeche_m2"])
        reihenfolge = sorted(glieder, key=lambda i: punkte[i]["richtung"])
        frei = [punkte[i]["sektor"] for i in reihenfolge if punkte[i]["frei"]]
        blockiert = [punkte[i]["sektor"] for i in reihenfolge if not punkte[i]["frei"]]
        pt = Point(p["x"], p["y"])
        idx = baum.query_nearest(pt)
        weg = float(min(pt.distance(baum.geometries[i]) for i in idx)) if len(idx) else None
        lon, lat = nach_wgs(p["x"], p["y"])
        for i in glieder:
            punkte[i]["kandidat"] = nr + 1
        kandidaten.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id": nr + 1,
                "hoehe_m": round(p["hoehe"]),
                "sektoren_frei": frei,
                "sektoren_blockiert": blockiert,
                "erste_kollision_m": {punkte[i]["sektor"]: round(punkte[i]["erste_kollision_m"])
                                      for i in reihenfolge if not punkte[i]["frei"]},
                "flaeche_m2": round(punkte[groesste]["flaeche_m2"]),
                "neigung_grad": round(punkte[groesste]["neigung"], 1),
                "ausrichtung_grad": round(punkte[groesste]["ausrichtung"]),
                "weg_abstand_m": None if weg is None else round(weg),
                "wald_hinweis": any(punkte[i]["wald_hinweis"] for i in glieder),
            },
        })

    zu_kandidat = {}
    for p_ in punkte:
        if p_["frei"]:
            zu_kandidat.setdefault(p_["flaeche_nr"], []).append(p_["kandidat"])
    flaechen_fc = []
    for f in flaechen:
        g = shp_transform(nach_wgs, f["geom"])
        flaechen_fc.append({"type": "Feature", "geometry": runden(mapping(g), 5),
                            "properties": {"sektor": f["sektor"],
                                           "kandidaten": sorted(set(zu_kandidat.get(f["flaeche_nr"], [])))}})

    # --- Abgleich mit bekannten Startplätzen ----------------------------------
    abgleich = []
    pge = DATEN / "startplaetze" / "paraglidingearth.geojson"
    if pge.exists() and kandidaten:
        nach_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform
        kxy = np.array([nach_utm(*k["geometry"]["coordinates"]) for k in kandidaten])
        frei_maske = np.array([bool(k["properties"]["sektoren_frei"]) for k in kandidaten])
        for f in json.loads(pge.read_text(encoding="utf-8"))["features"]:
            bx, by = nach_utm(*f["geometry"]["coordinates"])
            d = np.hypot(kxy[:, 0] - bx, kxy[:, 1] - by)
            d_frei = np.where(frei_maske, d, np.inf)
            abgleich.append({
                "name": f["properties"].get("name"),
                "naechster_kandidat_m": round(float(d.min())),
                "naechster_freier_kandidat_m": None if np.isinf(d_frei.min()) else round(float(d_frei.min())),
                "kandidat_id": int(np.argmin(d)) + 1,
            })

    info = {
        "stand": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "gebiet": e["testgebiet"]["name"],
        "sektoren": namen,
        "anzahl_kandidaten": len(kandidaten),
        "anzahl_mit_freiem_abflug": sum(bool(k["properties"]["sektoren_frei"]) for k in kandidaten),
        "abgleich_bekannte_startplaetze": abgleich,
        "einstellungen": {k: e[k] for k in ("startflaeche", "startbahn", "startpunkt",
                                            "hindernisse", "untergrund", "eigenschaften")},
        "quellen": [
            "Gelände- und Oberflächenmodell 2,5 m (2004/05), Realnutzungskarte (2005): "
            "Autonome Provinz Bozen – Südtirol, CC0",
            "Orthofoto 2023 (Infrarot): Autonome Provinz Bozen – Südtirol, CC BY 4.0",
            "Wege, Seilbahnen, Stromleitungen: © OpenStreetMap-Mitwirkende, ODbL",
        ],
    }

    ERGEBNISSE.mkdir(exist_ok=True)
    web = PROJEKT / "docs" / "daten"
    web.mkdir(parents=True, exist_ok=True)
    dateien = {
        "kandidaten.geojson": {"type": "FeatureCollection",
                               "features": [runden(k) for k in kandidaten]},
        "startflaechen.geojson": {"type": "FeatureCollection", "features": flaechen_fc},
        "kandidaten_info.json": info,
    }
    for name, inhalt in dateien.items():
        ziel = ERGEBNISSE / name
        ziel.write_text(json.dumps(inhalt, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
        shutil.copy(ziel, web / name)
        print(f"  {name}: {ziel.stat().st_size / 1e3:.0f} kB")
    if pge.exists():
        shutil.copy(pge, web / pge.name)  # bekannte Startplätze zum Vergleich auf der Karte
    print(json.dumps({k: info[k] for k in ("anzahl_kandidaten", "anzahl_mit_freiem_abflug",
                                           "abgleich_bekannte_startplaetze")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
