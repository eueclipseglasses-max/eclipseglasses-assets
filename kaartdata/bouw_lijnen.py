#!/usr/bin/env python3
"""
De Golem: lijntrajecten bouwen uit OpenStreetMap.

Wat dit script doet
1. Haalt alle lijnen en haltes op uit de De Golem-API (dezelfde data die de app gebruikt).
2. Leest de bus- en tramtrajecten van De Lijn uit een OpenStreetMap-bestand (.osm.pbf).
3. Zoekt per lijn (per richting) het OSM-traject dat echt langs de haltes van die lijn rijdt:
   zelfde lijnnummer, haltes binnen 50 m van het traject en bij voorkeur dezelfde haltenummers.
4. Bouwt één wegennet: per OSM-weg welke lijnen erover rijden. Lijnen die dezelfde straat delen,
   krijgen elk een eigen strook naast elkaar (zoals op een metroplan), in een vaste volgorde.
   Het net wordt in tegels van ~7 x 7 km geknipt, zodat de app alleen laadt wat in beeld is.
   Daarnaast een index (lijn -> kleur, soort, gebied, tegels).
5. Schrijft RAPPORT.md met wat niet gekoppeld kon worden en haltes die verdacht ver van OSM liggen.

Het script is bedoeld om wekelijks te draaien in GitHub Actions (zie .github/workflows/kaartdata.yml),
maar werkt ook lokaal:

    python kaartdata/bouw_lijnen.py --osm trajecten.osm.pbf --uit uitvoer

Benodigd: Python 3.10+, `pip install osmium`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium

# ---------------------------------------------------------------- instellingen
MAX_AFSTAND_M = 50          # een halte "ligt op" het traject als ze hier binnen ligt
MIN_SCORE = 0.6             # minimale overeenkomst om een traject te aanvaarden
MAX_STUKKEN = 6             # max. aantal OSM-trajecten die samen één lijn vormen (varianten of stukken)
VEREENVOUDIG_M = 2.0        # Douglas-Peucker-tolerantie: punten die minder dan 2 m afwijken vallen weg
DECIMALEN = 5               # ~1 m nauwkeurig
TEGEL_LON, TEGEL_LAT = 0.1, 0.0625   # tegelgrootte in graden (~7 x 7 km in Vlaanderen)
VERDACHTE_HALTE_M = 40      # haltes die verder dan dit van hun OSM-positie liggen, komen in het rapport
ROUTE_SOORTEN = {"bus", "tram"}
# Lijnnummers die in OSM anders heten (app-nummer -> woorden in de OSM-naam).
ALIASSEN = {"KT": ["kusttram"]}

# Lokale projectie naar meters (goed genoeg voor Vlaanderen).
M_PER_GRAAD_LAT = 110_574.0
M_PER_GRAAD_LON = 111_320.0 * math.cos(math.radians(51.0))


def xy(lon: float, lat: float) -> tuple[float, float]:
    return lon * M_PER_GRAAD_LON, lat * M_PER_GRAAD_LAT


# ---------------------------------------------------------------- app-data
def haal_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "DeGolem-kaartdata/1.0 (+github.com/eueclipseglasses-max)"})
    for poging in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as fout:  # noqa: BLE001
            if poging == 2:
                raise
            print(f"  ophalen mislukt ({fout}), opnieuw…", file=sys.stderr)
            time.sleep(5 * (poging + 1))
    return {}


def haltenummer(stop_id: str) -> str:
    """'gs:delijn:506865' -> '506865'."""
    m = re.search(r"(\d{4,7})$", str(stop_id))
    return m.group(1) if m else ""


def lees_app_data(args) -> tuple[list[dict], dict[str, list[dict]], dict[str, dict]]:
    if args.routes_json and args.stops_json:
        routes = json.loads(Path(args.routes_json).read_text(encoding="utf-8"))
        stops = json.loads(Path(args.stops_json).read_text(encoding="utf-8"))
    else:
        basis = args.app_url.rstrip("/")
        print(f"App-data ophalen van {basis} …")
        routes = haal_json(basis + "/api/routes")
        stops = haal_json(basis + "/api/stops")
    routes = routes.get("routes", routes) if isinstance(routes, dict) else routes
    stops = stops.get("stops", stops) if isinstance(stops, dict) else stops

    per_lijn: dict[str, list[dict]] = defaultdict(list)
    alle_haltes: dict[str, dict] = {}
    for s in stops:
        try:
            lat, lon = float(s["stop_lat"]), float(s["stop_lon"])
        except (KeyError, TypeError, ValueError):
            continue
        h = {"id": str(s["stop_id"]), "nr": haltenummer(s["stop_id"]), "naam": s.get("stop_name", ""), "lat": lat, "lon": lon}
        alle_haltes[h["id"]] = h
        for rid in str(s.get("route_ids") or "").split(","):
            if rid:
                per_lijn[rid].append(h)
    print(f"  {len(routes)} lijnen, {len(alle_haltes)} haltes")
    return routes, per_lijn, alle_haltes


# ---------------------------------------------------------------- OpenStreetMap
def is_de_lijn(tags: dict) -> bool:
    op = (tags.get("operator", "") + ";" + tags.get("network", "")).lower()
    return "de lijn" in op or tags.get("network", "").upper() == "DL"


def stop_refs(tags) -> set[str]:
    refs: set[str] = set()
    for key in ("ref:De_Lijn", "ref:De Lijn", "ref:delijn"):
        if key in tags:
            refs.update(v.strip() for v in tags[key].split(";"))
    if not refs and "ref" in tags:
        refs.update(v.strip() for v in tags["ref"].split(";") if re.fullmatch(r"\d{6}", v.strip()))
    return {r for r in refs if re.fullmatch(r"\d{4,7}", r)}


class Relaties(osmium.SimpleHandler):
    """Pass 1: alle De Lijn-trajecten en de route_masters (voor de lijnkleur)."""

    def __init__(self):
        super().__init__()
        self.routes: dict[int, dict] = {}
        self.master_kleur: dict[int, str] = {}

    def relation(self, r):
        tags = {t.k: t.v for t in r.tags}
        if tags.get("type") == "route_master" and tags.get("route_master") in ROUTE_SOORTEN:
            kleur = tags.get("colour") or tags.get("color")
            if kleur:
                for m in r.members:
                    if m.type == "r":
                        self.master_kleur[m.ref] = kleur
            return
        if tags.get("type") != "route" or tags.get("route") not in ROUTE_SOORTEN or not is_de_lijn(tags):
            return
        wegen, haltes = [], []
        for m in r.members:
            rol = m.role or ""
            if m.type == "w" and not rol.startswith("platform") and not rol.startswith("stop"):
                wegen.append(m.ref)
            elif m.type == "n":
                haltes.append(m.ref)
        self.routes[r.id] = {"id": r.id, "tags": tags, "wegen": wegen, "haltes": haltes}


class Geometrie(osmium.SimpleHandler):
    """Pass 2: coördinaten van de wegen en haltenummers van de haltes."""

    def __init__(self, weg_ids: set[int], halte_ids: set[int]):
        super().__init__()
        self.weg_ids, self.halte_ids = weg_ids, halte_ids
        self.wegen: dict[int, list[tuple[float, float]]] = {}
        self.haltes: dict[int, dict] = {}

    def node(self, n):
        if n.id in self.halte_ids and n.location.valid():
            self.haltes[n.id] = {"id": n.id, "lon": n.location.lon, "lat": n.location.lat, "refs": stop_refs(n.tags)}

    def way(self, w):
        if w.id not in self.weg_ids:
            return
        punten = []
        for nd in w.nodes:
            if nd.location.valid():
                punten.append((nd.location.lon, nd.location.lat))
        if len(punten) >= 2:
            self.wegen[w.id] = punten


def lees_osm(pad: str) -> tuple[dict, dict, dict]:
    print(f"OpenStreetMap lezen: {pad}")
    rel = Relaties()
    rel.apply_file(pad)
    weg_ids = {w for r in rel.routes.values() for w in r["wegen"]}
    halte_ids = {h for r in rel.routes.values() for h in r["haltes"]}
    geo = Geometrie(weg_ids, halte_ids)
    geo.apply_file(pad, locations=True)
    print(f"  {len(rel.routes)} De Lijn-trajecten, {len(geo.wegen)} wegen, {len(geo.haltes)} OSM-haltes")

    trajecten = {}
    for rid, r in rel.routes.items():
        lijnen = ketting([geo.wegen[w] for w in r["wegen"] if w in geo.wegen])
        if not lijnen:
            continue
        refs, halte_pos = set(), []
        for h in r["haltes"]:
            if h in geo.haltes:
                refs |= geo.haltes[h]["refs"]
                halte_pos.append(geo.haltes[h])
        t = r["tags"]
        kleur = normaliseer_kleur(t.get("colour") or t.get("color") or rel.master_kleur.get(rid))
        trajecten[rid] = Traject(rid, t, lijnen, refs, kleur, rijrichtingen(r["wegen"], geo.wegen))
    # Alle OSM-haltes met een haltenummer, om de app-haltes te controleren.
    osm_haltes = defaultdict(list)
    for h in geo.haltes.values():
        for ref in h["refs"]:
            osm_haltes[ref].append((h["lon"], h["lat"], h["id"]))
    return trajecten, osm_haltes, geo.wegen


def rijrichtingen(ids: list[int], wegen: dict) -> list[tuple[int, int]]:
    """Per weg van een traject: +1 als de bus de weg in tekenvolgorde rijdt, -1 als omgekeerd."""
    ids = [w for w in ids if w in wegen]
    res, uit = [], None
    for i, w in enumerate(ids):
        a, b = wegen[w][0], wegen[w][-1]
        d = 0
        if uit is not None:
            d = 1 if a == uit else (-1 if b == uit else 0)
        if d == 0 and i + 1 < len(ids):
            volgende = wegen[ids[i + 1]]
            einden = (volgende[0], volgende[-1])
            d = 1 if b in einden else (-1 if a in einden else 0)
        d = d or 1
        res.append((w, d))
        uit = b if d == 1 else a
    return res


def ketting(wegen: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """Plakt opeenvolgende wegen aan elkaar tot zo lang mogelijke lijnen."""
    kettingen: list[list[tuple[float, float]]] = []
    stukken: list[int] = []
    for w in wegen:
        if kettingen:
            k = kettingen[-1]
            if k[-1] == w[0]:
                k.extend(w[1:]); stukken[-1] += 1; continue
            if k[-1] == w[-1]:
                k.extend(reversed(w[:-1])); stukken[-1] += 1; continue
            if stukken[-1] == 1 and k[0] == w[0]:
                k.reverse(); k.extend(w[1:]); stukken[-1] += 1; continue
            if stukken[-1] == 1 and k[0] == w[-1]:
                k.reverse(); k.extend(reversed(w[:-1])); stukken[-1] += 1; continue
        kettingen.append(list(w)); stukken.append(1)
    return kettingen


KLEURNAMEN = {"red": "#E30613", "blue": "#0055A4", "green": "#009A44", "yellow": "#FFD500", "orange": "#F28C28",
              "purple": "#7B2D8E", "pink": "#E5007D", "brown": "#8B5A2B", "black": "#000000", "white": "#FFFFFF",
              "grey": "#808080", "gray": "#808080"}


def normaliseer_kleur(k: str | None) -> str | None:
    if not k:
        return None
    k = k.strip().lower()
    if k in KLEURNAMEN:
        return KLEURNAMEN[k]
    m = re.fullmatch(r"#?([0-9a-f]{3}|[0-9a-f]{6})", k)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


# ---------------------------------------------------------------- geometrie
class Traject:
    CEL = 200.0  # rastercel in meter voor snelle afstandsberekening

    def __init__(self, rid, tags, lijnen, refs, kleur, wegen=()):
        self.id, self.tags, self.lijnen, self.refs, self.kleur = rid, tags, lijnen, refs, kleur
        self.wegen = list(wegen)  # [(weg-id, +1 als in volgorde van de weg gereden, anders -1)]
        self.ref = (tags.get("ref") or "").strip()
        self.naam = tags.get("name", "")
        self.soort = tags.get("route", "bus")
        lons = [p[0] for l in lijnen for p in l]
        lats = [p[1] for l in lijnen for p in l]
        self.bbox = (min(lons), min(lats), max(lons), max(lats))
        self._raster = None

    def raster(self):
        if self._raster is None:
            segs, rooster = [], defaultdict(list)
            for l in self.lijnen:
                pts = [xy(*p) for p in l]
                for a, b in zip(pts, pts[1:]):
                    i = len(segs)
                    segs.append((a, b))
                    for cx in range(int(min(a[0], b[0]) // self.CEL), int(max(a[0], b[0]) // self.CEL) + 1):
                        for cy in range(int(min(a[1], b[1]) // self.CEL), int(max(a[1], b[1]) // self.CEL) + 1):
                            rooster[(cx, cy)].append(i)
            self._raster = (segs, rooster)
        return self._raster

    def afstand(self, lon, lat) -> float:
        segs, rooster = self.raster()
        px, py = xy(lon, lat)
        cx, cy = int(px // self.CEL), int(py // self.CEL)
        best = math.inf
        gezien = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in rooster.get((cx + dx, cy + dy), ()):
                    if i in gezien:
                        continue
                    gezien.add(i)
                    best = min(best, punt_segment(px, py, *segs[i]))
        return best


def punt_segment(px, py, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    lengte2 = dx * dx + dy * dy
    t = 0.0 if lengte2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / lengte2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def vereenvoudig(punten: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    """Douglas-Peucker in meters (niet-recursief)."""
    if len(punten) < 3:
        return punten
    p = [xy(*q) for q in punten]
    houden = [False] * len(p)
    houden[0] = houden[-1] = True
    stapel = [(0, len(p) - 1)]
    while stapel:
        s, e = stapel.pop()
        best, idx = -1.0, -1
        for i in range(s + 1, e):
            d = punt_segment(p[i][0], p[i][1], p[s], p[e])
            if d > best:
                best, idx = d, i
        if best > tol:
            houden[idx] = True
            stapel.append((s, idx))
            stapel.append((idx, e))
    return [q for q, h in zip(punten, houden) if h]


# ---------------------------------------------------------------- koppelen
def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def plaatsnamen(lang: str) -> tuple[str, str]:
    delen = [d.strip().lower() for d in re.split(r"\s+-\s+", lang or "") if d.strip()]
    return (delen[0], delen[-1]) if delen else ("", "")


def kandidaten(route: dict, haltes: list[dict], per_ref: dict, alle: list) -> list:
    nummer = norm(route.get("route_short_name", ""))
    lijst = list(per_ref.get(nummer, []))
    if not lijst:
        woorden = ALIASSEN.get(route.get("route_short_name", "").strip().upper(), [])
        lijst = [t for t in alle if any(w in norm(t.naam) for w in woorden)]
    if not haltes:
        return []
    marge_lon, marge_lat = 1000 / M_PER_GRAAD_LON, 1000 / M_PER_GRAAD_LAT
    w = min(h["lon"] for h in haltes) - marge_lon
    e = max(h["lon"] for h in haltes) + marge_lon
    s = min(h["lat"] for h in haltes) - marge_lat
    n = max(h["lat"] for h in haltes) + marge_lat
    return [t for t in lijst if not (t.bbox[2] < w or t.bbox[0] > e or t.bbox[3] < s or t.bbox[1] > n)]


def score(t: Traject, haltes: list[dict]) -> tuple[float, float, set[str]]:
    dichtbij = {h["id"] for h in haltes if t.afstand(h["lon"], h["lat"]) <= MAX_AFSTAND_M}
    geo = len(dichtbij) / len(haltes)
    nrs = {h["nr"] for h in haltes if h["nr"]}
    if t.refs and nrs:
        refscore = len(nrs & t.refs) / len(nrs)
        return 0.5 * geo + 0.5 * refscore, geo, dichtbij
    return geo, geo, dichtbij


def koppel(route: dict, haltes: list[dict], per_ref: dict, alle: list) -> dict:
    kand = kandidaten(route, haltes, per_ref, alle)
    if not kand:
        return {"status": "geen OSM-traject met dit lijnnummer in de buurt", "trajecten": [], "dekking": 0.0, "kandidaten": []}
    van, naar = plaatsnamen(route.get("route_long_name", ""))
    beoordeeld = []
    for t in kand:
        sc, geo, dichtbij = score(t, haltes)
        # Kleine voorkeur voor het traject in de juiste richting (bij gelijke score).
        richting = 0.0
        if naar and naar in norm(t.tags.get("to", "") + " " + t.naam.split("→")[-1]):
            richting += 0.02
        if van and van in norm(t.tags.get("from", "")):
            richting += 0.01
        beoordeeld.append((sc + richting, geo, t, dichtbij))
    beoordeeld.sort(key=lambda x: -x[0])
    top = [(t, sc) for sc, _, t, _ in beoordeeld[:3]]
    beste_sc, beste_geo, beste, gedekt = beoordeeld[0]
    # Begin bij het best passende traject en voeg stukken toe die nog niet gedekte haltes
    # van deze lijn bedienen: varianten (schoolritten, omleidingen) of lange lijnen die
    # in OSM in stukken staan (bv. de Kusttram). Een traject in de andere rijrichting
    # voegt niets toe, want het ligt op dezelfde straten.
    gekozen, gedekt = [beste], set(gedekt)
    rest = [x for x in beoordeeld[1:] if x[1] >= 0.15]
    while rest and len(gekozen) < MAX_STUKKEN and len(gedekt) < len(haltes):
        x = max(rest, key=lambda x: (len(x[3] - gedekt), x[0]))
        if len(x[3] - gedekt) < 2:
            break
        gekozen.append(x[2])
        gedekt |= x[3]
        rest.remove(x)
    dekking = len(gedekt) / len(haltes)
    alleen_beste_ok = beste_sc >= MIN_SCORE and beste_geo >= MIN_SCORE
    if alleen_beste_ok or (len(gekozen) > 1 and dekking >= MIN_SCORE):
        return {"status": "ok", "trajecten": gekozen, "dekking": dekking, "kandidaten": top}
    return {"status": f"beste OSM-traject past onvoldoende (score {beste_sc:.2f})", "trajecten": [],
            "dekking": beste_geo, "kandidaten": top}


# ---------------------------------------------------------------- uitvoer
def lijn_volgorde(naam: str):
    m = re.match(r"(\d+)(.*)", naam or "")
    return (0, int(m.group(1)), m.group(2)) if m else (1, 0, naam or "")


def codeer(punten: list[tuple[float, float]]) -> list[int]:
    """Coördinaten als gehele getallen (x 100000) en verschillen: ~3x kleiner dan gewone GeoJSON."""
    uit, vx, vy = [], 0, 0
    for lon, lat in punten:
        x, y = round(lon * 10 ** DECIMALEN), round(lat * 10 ** DECIMALEN)
        if uit and x == vx and y == vy:
            continue
        uit += [x - vx, y - vy]
        vx, vy = x, y
    return uit


def bouw_netwerk(gekoppeld: list[dict], wegen: dict, uit: Path) -> tuple[dict, list, list, dict]:
    """Eén wegennet met per weg de lijnen die erover rijden, in tegels.

    gekoppeld: [{"rid", "naam", "kleur", "soort", "trajecten": [Traject]}]
    Geeft (tegel-bbox per tegel, groepen, routes, extra info per route).
    """
    # Groepen: één groep per zichtbare lijn (zelfde nummer + kleur + soort; beide richtingen samen).
    sleutel = lambda g: (g["naam"].strip().upper(), g["kleur"] or "", g["soort"])
    groepen_set = sorted({sleutel(g) for g in gekoppeld}, key=lambda k: (lijn_volgorde(k[0]), k[1], k[2]))
    groep_nr = {k: i for i, k in enumerate(groepen_set)}
    groepen = [{"n": k[0], "k": k[1] or None, "m": k[2]} for k in groepen_set]
    gekoppeld = sorted(gekoppeld, key=lambda g: (groep_nr[sleutel(g)], g["rid"]))
    routes = [g["rid"] for g in gekoppeld]

    weg_routes = defaultdict(set)
    for i, g in enumerate(gekoppeld):
        for t in g["trajecten"]:
            for w, _ in t.wegen:
                weg_routes[w].add(i)

    # Rijrichting op elkaar afstemmen: elke weg krijgt één tekenrichting. Lijnen die een stuk
    # straat delen, volgen dezelfde richting, zodat hun strook links/rechts niet omwisselt.
    richting: dict[int, int] = {}
    per_groep = defaultdict(list)
    for g in gekoppeld:
        for t in g["trajecten"]:
            if t not in per_groep[groep_nr[sleutel(g)]]:
                per_groep[groep_nr[sleutel(g)]].append(t)
    for gi in range(len(groepen)):
        open_ = list(per_groep[gi])
        while open_:
            t = max(open_, key=lambda t: (sum(1 for w, _ in t.wegen if w in richting), len(t.wegen)))
            stemmen = sum(richting[w] * d for w, d in t.wegen if w in richting)
            teken = 1 if stemmen >= 0 else -1
            for w, d in t.wegen:
                richting.setdefault(w, d * teken)
            open_.remove(t)

    # Per weg: groepen (stroken) en routes, in een vaste volgorde; tegel volgens het midden van de weg.
    groep_van_route = [groep_nr[sleutel(g)] for g in gekoppeld]
    punten, sleutels = {}, {}
    for w, rs in weg_routes.items():
        pts = wegen[w] if richting.get(w, 1) == 1 else wegen[w][::-1]
        mid = pts[len(pts) // 2]
        tegel = (math.floor(mid[0] / TEGEL_LON), math.floor(mid[1] / TEGEL_LAT))
        gs = tuple(sorted({groep_van_route[r] for r in rs}))
        punten[w] = pts
        sleutels[w] = (tegel, gs, tuple(sorted(rs)))

    # Opeenvolgende wegen met dezelfde lijnen aan elkaar plakken (minder objecten om te tekenen).
    begin, einde = defaultdict(list), defaultdict(list)
    for w, k in sleutels.items():
        begin[(k, punten[w][0])].append(w)
        einde[(k, punten[w][-1])].append(w)
    gebruikt, kettingen = set(), []
    for w in sorted(sleutels):
        if w in gebruikt:
            continue
        k, cur, gezien = sleutels[w], w, {w}
        while True:
            knoop = (k, punten[cur][0])
            vorige = [x for x in einde[knoop] if x not in gebruikt and x not in gezien]
            if len(vorige) != 1 or len(begin[knoop]) != 1 or len(einde[knoop]) != 1:
                break
            cur = vorige[0]
            gezien.add(cur)
        gebruikt.add(cur)
        pts = list(punten[cur])
        while True:
            knoop = (k, pts[-1])
            volgende = [x for x in begin[knoop] if x not in gebruikt]
            if len(volgende) != 1 or len(begin[knoop]) != 1 or len(einde[knoop]) != 1:
                break
            gebruikt.add(volgende[0])
            pts.extend(punten[volgende[0]][1:])
        kettingen.append((k, vereenvoudig(pts, VEREENVOUDIG_M)))

    per_tegel = defaultdict(list)
    tegel_bbox: dict[str, list[float]] = {}
    route_tegels = defaultdict(set)
    for (tegel, gs, rs), pts in kettingen:
        naam = f"{tegel[0]}_{tegel[1]}"
        per_tegel[naam].append([list(gs), list(rs), codeer(pts)])
        lons, lats = [p[0] for p in pts], [p[1] for p in pts]
        bb = tegel_bbox.get(naam, [math.inf, math.inf, -math.inf, -math.inf])
        tegel_bbox[naam] = [min(bb[0], min(lons)), min(bb[1], min(lats)), max(bb[2], max(lons)), max(bb[3], max(lats))]
        for r in rs:
            route_tegels[routes[r]].add(naam)

    map_net = uit / "net"
    map_net.mkdir(parents=True, exist_ok=True)
    grootte = 0
    for naam, f in per_tegel.items():
        tekst = json.dumps({"f": f}, separators=(",", ":"))
        (map_net / f"{naam}.json").write_text(tekst, encoding="utf-8")
        grootte += len(tekst)
    tegels = {n: [round(v, 5) for v in bb] for n, bb in sorted(tegel_bbox.items())}
    extra = {rid: {"g": groep_van_route[i], "t": sorted(route_tegels[rid])} for i, rid in enumerate(routes)}
    print(f"  wegennet: {len(weg_routes)} wegen, {len(kettingen)} stukken, {len(tegels)} tegels, {grootte / 1024:.0f} KB")
    return {"tegels": tegels, "grootte": grootte, "stukken": len(kettingen)}, groepen, routes, extra


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--osm", required=True, help="OSM-bestand (.osm.pbf), liefst al gefilterd op route=bus,tram")
    ap.add_argument("--uit", default="uitvoer", help="uitvoermap")
    ap.add_argument("--app-url", default=os.environ.get("APP_URL", "https://eclipseglasses.eu"))
    ap.add_argument("--routes-json", help="lokaal bestand i.p.v. /api/routes (om te testen)")
    ap.add_argument("--stops-json", help="lokaal bestand i.p.v. /api/stops (om te testen)")
    args = ap.parse_args()

    routes, per_lijn, alle_haltes = lees_app_data(args)
    trajecten, osm_haltes, osm_wegen = lees_osm(args.osm)
    per_ref = defaultdict(list)
    for t in trajecten.values():
        per_ref[norm(t.ref)].append(t)
    alle = list(trajecten.values())

    uit = Path(args.uit)
    uit.mkdir(parents=True, exist_ok=True)

    index, problemen, gekoppeld = {}, [], []
    kleurbron = defaultdict(int)
    for r in routes:
        rid = str(r["route_id"])
        haltes = per_lijn.get(rid, [])
        if len(haltes) < 2:
            problemen.append((r, "minder dan 2 haltes in de app", 0.0, []))
            continue
        res = koppel(r, haltes, per_ref, alle)
        if res["status"] != "ok":
            problemen.append((r, res["status"], res["dekking"], res["kandidaten"]))
            continue
        ts = res["trajecten"]
        kleur = next((t.kleur for t in ts if t.kleur), None)
        gekoppeld.append({"rid": rid, "naam": str(r.get("route_short_name", "")), "kleur": kleur,
                          "soort": ts[0].soort, "trajecten": ts})
        kleurbron["OpenStreetMap" if kleur else "standaard bus/tram"] += 1
        w = min(t.bbox[0] for t in ts); s = min(t.bbox[1] for t in ts)
        e = max(t.bbox[2] for t in ts); n = max(t.bbox[3] for t in ts)
        index[rid] = {"k": kleur, "m": ts[0].soort,
                      "b": [round(w, 4), round(s, 4), round(e, 4), round(n, 4)], "d": round(res["dekking"], 2)}
        if res["dekking"] < 0.9:
            problemen.append((r, "gekoppeld, maar niet alle haltes liggen op het traject", res["dekking"], ts))

    net, groepen, net_routes, extra = bouw_netwerk(gekoppeld, osm_wegen, uit)
    for rid, x in extra.items():
        index[rid].update(x)
    nu = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (uit / "index.json").write_text(json.dumps(
        {"versie": 2, "gemaakt": nu, "bron": "© OpenStreetMap-bijdragers (ODbL)",
         "tegelmaat": [TEGEL_LON, TEGEL_LAT], "groepen": groepen, "routes": net_routes,
         "tegels": net["tegels"], "lijnen": index},
        separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    # Haltecontrole: app-positie vs. OSM-positie met hetzelfde haltenummer.
    verdacht = []
    for h in alle_haltes.values():
        posities = osm_haltes.get(h["nr"])
        if not posities:
            continue
        d, p = min((math.hypot(*(a - b for a, b in zip(xy(h["lon"], h["lat"]), xy(p[0], p[1])))), p) for p in posities)
        if d > VERDACHTE_HALTE_M:
            verdacht.append((d, h, p[2]))
    verdacht.sort(key=lambda x: -x[0])

    totaal = len(routes)
    ok = len(index)
    regels = [
        "# Rapport lijntrajecten", "",
        f"Gemaakt: {nu}", "",
        f"- Lijnen in de app: **{totaal}**",
        f"- Gekoppeld aan een OSM-traject: **{ok}** ({(ok / totaal * 100 if totaal else 0):.0f}%)",
        f"- Wegennet: {net['stukken']} stukken straat in {len(net['tegels'])} tegels ({net['grootte'] / 1024:.0f} KB samen)",
        f"- Kleur uit OpenStreetMap: {kleurbron['OpenStreetMap']}, standaardkleur bus/tram: {kleurbron['standaard bus/tram']}",
        f"- App-haltes met een haltenummer in OSM: {sum(1 for h in alle_haltes.values() if h['nr'] in osm_haltes)} van {len(alle_haltes)}",
        "",
        "## Lijnen om na te kijken", "",
    ]
    if problemen:
        regels += ["| Lijn | Traject | Probleem | Haltes op traject | OSM-trajecten |", "|---|---|---|---|---|"]
        for r, reden, dek, osm in sorted(problemen, key=lambda p: (str(p[0].get("route_short_name")), str(p[0]["route_id"]))):
            links = ", ".join(
                f"[{(x[0] if isinstance(x, tuple) else x).id}](https://www.openstreetmap.org/relation/{(x[0] if isinstance(x, tuple) else x).id})"
                + (f" ({x[1]:.2f})" if isinstance(x, tuple) else "") for x in osm) or "–"
            regels.append(f"| {r.get('route_short_name', '')} | {r.get('route_long_name', '')} (`{r['route_id']}`) | {reden} | {dek:.0%} | {links} |")
    else:
        regels.append("Geen: alle lijnen zijn volledig gekoppeld.")
    regels += ["", f"## Haltes die meer dan {VERDACHTE_HALTE_M} m van hun OSM-positie liggen", ""]
    if verdacht:
        regels += ["Vergelijk beide plaatsen: de halte die op de verkeerde plek staat moet verbeterd worden "
                   "(in de app-databank of in OpenStreetMap).", "",
                   "| Halte | Nummer | Afstand | In de app | In OSM |", "|---|---|---|---|---|"]
        regels += [f"| {h['naam']} | {h['nr']} | {d:.0f} m | "
                   f"[kaart](https://www.openstreetmap.org/?mlat={h['lat']:.6f}&mlon={h['lon']:.6f}#map=18/{h['lat']:.6f}/{h['lon']:.6f}) | "
                   f"[node {n}](https://www.openstreetmap.org/node/{n}) |" for d, h, n in verdacht[:200]]
    else:
        regels.append("Geen.")
    regels += ["", "Een lijn ontbreekt of klopt niet? Meestal ontbreekt het traject in OpenStreetMap of heeft het een ander lijnnummer.",
               "Je kunt het zelf aanvullen op openstreetmap.org; volgende week neemt dit script het automatisch over."]
    (uit / "RAPPORT.md").write_text("\n".join(regels) + "\n", encoding="utf-8")

    print(f"Klaar: {ok}/{totaal} lijnen gekoppeld, {len(net['tegels'])} tegels, {len(verdacht)} verdachte haltes.")
    if totaal and ok == 0:
        print("Geen enkele lijn gekoppeld: er is waarschijnlijk iets mis met de invoer.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
