#!/usr/bin/env python3
"""
De Golem: lijntrajecten bouwen uit OpenStreetMap.

Wat dit script doet
1. Haalt alle lijnen en haltes op uit de De Golem-API (dezelfde data die de app gebruikt).
2. Leest de bus- en tramtrajecten van De Lijn uit een OpenStreetMap-bestand (.osm.pbf).
3. Zoekt per lijn (per richting) het OSM-traject dat echt langs de haltes van die lijn rijdt:
   zelfde lijnnummer, haltes binnen 50 m van het traject en bij voorkeur dezelfde haltenummers.
4. Schrijft per traject een klein GeoJSON-bestand en een index (lijn -> traject, kleur, soort, gebied).
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
MAX_VARIANTEN = 3           # max. aantal OSM-trajecten dat samen één lijn vormt (bv. schoolritten)
VEREENVOUDIG_M = 2.0        # Douglas-Peucker-tolerantie: punten die minder dan 2 m afwijken vallen weg
DECIMALEN = 5               # ~1 m nauwkeurig
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
            self.haltes[n.id] = {"lon": n.location.lon, "lat": n.location.lat, "refs": stop_refs(n.tags)}

    def way(self, w):
        if w.id not in self.weg_ids:
            return
        punten = []
        for nd in w.nodes:
            if nd.location.valid():
                punten.append((nd.location.lon, nd.location.lat))
        if len(punten) >= 2:
            self.wegen[w.id] = punten


def lees_osm(pad: str) -> tuple[dict, dict]:
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
        trajecten[rid] = Traject(rid, t, lijnen, refs, kleur)
    # Alle OSM-haltes met een haltenummer, om de app-haltes te controleren.
    osm_haltes = defaultdict(list)
    for h in geo.haltes.values():
        for ref in h["refs"]:
            osm_haltes[ref].append((h["lon"], h["lat"]))
    return trajecten, osm_haltes


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

    def __init__(self, rid, tags, lijnen, refs, kleur):
        self.id, self.tags, self.lijnen, self.refs, self.kleur = rid, tags, lijnen, refs, kleur
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
        return {"status": "geen OSM-traject met dit lijnnummer in de buurt", "trajecten": [], "dekking": 0.0}
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
    beste_sc, beste_geo, beste, gedekt = beoordeeld[0]
    if beste_sc < MIN_SCORE or beste_geo < MIN_SCORE:
        return {"status": f"beste OSM-traject past onvoldoende (score {beste_sc:.2f})", "trajecten": [], "dekking": beste_geo}
    gekozen, gedekt = [beste], set(gedekt)
    # Varianten toevoegen die haltes dekken die nog ontbreken (bv. schoolritten of omleidingen).
    for sc, geo, t, dichtbij in beoordeeld[1:]:
        if len(gekozen) >= MAX_VARIANTEN or len(gedekt) == len(haltes):
            break
        nieuw = dichtbij - gedekt
        if sc >= 0.5 and len(nieuw) >= 2:
            gekozen.append(t)
            gedekt |= dichtbij
    return {"status": "ok", "trajecten": gekozen, "dekking": len(gedekt) / len(haltes)}


# ---------------------------------------------------------------- uitvoer
def schrijf_traject(t: Traject, map_lijnen: Path) -> int:
    lijnen = []
    for l in t.lijnen:
        v = vereenvoudig(l, VEREENVOUDIG_M)
        coords, vorige = [], None
        for lon, lat in v:
            p = [round(lon, DECIMALEN), round(lat, DECIMALEN)]
            if p != vorige:
                coords.append(p)
            vorige = p
        if len(coords) >= 2:
            lijnen.append(coords)
    data = {"type": "Feature", "properties": {"osm": t.id},
            "geometry": {"type": "MultiLineString", "coordinates": lijnen}}
    tekst = json.dumps(data, separators=(",", ":"))
    (map_lijnen / f"r{t.id}.json").write_text(tekst, encoding="utf-8")
    return len(tekst)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--osm", required=True, help="OSM-bestand (.osm.pbf), liefst al gefilterd op route=bus,tram")
    ap.add_argument("--uit", default="uitvoer", help="uitvoermap")
    ap.add_argument("--app-url", default=os.environ.get("APP_URL", "https://eclipseglasses.eu"))
    ap.add_argument("--routes-json", help="lokaal bestand i.p.v. /api/routes (om te testen)")
    ap.add_argument("--stops-json", help="lokaal bestand i.p.v. /api/stops (om te testen)")
    args = ap.parse_args()

    routes, per_lijn, alle_haltes = lees_app_data(args)
    trajecten, osm_haltes = lees_osm(args.osm)
    per_ref = defaultdict(list)
    for t in trajecten.values():
        per_ref[norm(t.ref)].append(t)
    alle = list(trajecten.values())

    uit = Path(args.uit)
    map_lijnen = uit / "lijnen"
    map_lijnen.mkdir(parents=True, exist_ok=True)

    index, problemen, geschreven = {}, [], {}
    kleurbron = defaultdict(int)
    for r in routes:
        rid = str(r["route_id"])
        haltes = per_lijn.get(rid, [])
        if len(haltes) < 2:
            problemen.append((r, "minder dan 2 haltes in de app", 0.0))
            continue
        res = koppel(r, haltes, per_ref, alle)
        if res["status"] != "ok":
            problemen.append((r, res["status"], res["dekking"]))
            continue
        ts = res["trajecten"]
        for t in ts:
            if t.id not in geschreven:
                geschreven[t.id] = schrijf_traject(t, map_lijnen)
        kleur = next((t.kleur for t in ts if t.kleur), None)
        kleurbron["OpenStreetMap" if kleur else "standaard bus/tram"] += 1
        w = min(t.bbox[0] for t in ts); s = min(t.bbox[1] for t in ts)
        e = max(t.bbox[2] for t in ts); n = max(t.bbox[3] for t in ts)
        index[rid] = {"r": [t.id for t in ts], "k": kleur, "m": ts[0].soort,
                      "b": [round(w, 4), round(s, 4), round(e, 4), round(n, 4)], "d": round(res["dekking"], 2)}
        if res["dekking"] < 0.9:
            problemen.append((r, "gekoppeld, maar niet alle haltes liggen op het traject", res["dekking"]))

    nu = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (uit / "index.json").write_text(json.dumps(
        {"versie": 1, "gemaakt": nu, "bron": "© OpenStreetMap-bijdragers (ODbL)", "lijnen": index},
        separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    # Haltecontrole: app-positie vs. OSM-positie met hetzelfde haltenummer.
    verdacht = []
    for h in alle_haltes.values():
        posities = osm_haltes.get(h["nr"])
        if not posities:
            continue
        d = min(math.hypot(*(a - b for a, b in zip(xy(h["lon"], h["lat"]), xy(*p)))) for p in posities)
        if d > VERDACHTE_HALTE_M:
            verdacht.append((d, h))
    verdacht.sort(key=lambda x: -x[0])

    totaal = len(routes)
    ok = len(index)
    regels = [
        "# Rapport lijntrajecten", "",
        f"Gemaakt: {nu}", "",
        f"- Lijnen in de app: **{totaal}**",
        f"- Gekoppeld aan een OSM-traject: **{ok}** ({(ok / totaal * 100 if totaal else 0):.0f}%)",
        f"- Trajectbestanden: {len(geschreven)} ({sum(geschreven.values()) / 1024:.0f} KB samen)",
        f"- Kleur uit OpenStreetMap: {kleurbron['OpenStreetMap']}, standaardkleur bus/tram: {kleurbron['standaard bus/tram']}",
        f"- App-haltes met een haltenummer in OSM: {sum(1 for h in alle_haltes.values() if h['nr'] in osm_haltes)} van {len(alle_haltes)}",
        "",
        "## Lijnen om na te kijken", "",
    ]
    if problemen:
        regels += ["| Lijn | Traject | Probleem | Haltes op traject |", "|---|---|---|---|"]
        for r, reden, dek in sorted(problemen, key=lambda p: (str(p[0].get("route_short_name")), str(p[0]["route_id"]))):
            regels.append(f"| {r.get('route_short_name', '')} | {r.get('route_long_name', '')} (`{r['route_id']}`) | {reden} | {dek:.0%} |")
    else:
        regels.append("Geen: alle lijnen zijn volledig gekoppeld.")
    regels += ["", f"## Haltes die meer dan {VERDACHTE_HALTE_M} m van hun OSM-positie liggen", ""]
    if verdacht:
        regels += ["| Halte | Nummer | Afstand |", "|---|---|---|"]
        regels += [f"| {h['naam']} | {h['nr']} | {d:.0f} m |" for d, h in verdacht[:200]]
    else:
        regels.append("Geen.")
    regels += ["", "Een lijn ontbreekt of klopt niet? Meestal ontbreekt het traject in OpenStreetMap of heeft het een ander lijnnummer.",
               "Je kunt het zelf aanvullen op openstreetmap.org; volgende week neemt dit script het automatisch over."]
    (uit / "RAPPORT.md").write_text("\n".join(regels) + "\n", encoding="utf-8")

    print(f"Klaar: {ok}/{totaal} lijnen gekoppeld, {len(geschreven)} trajecten, {len(verdacht)} verdachte haltes.")
    if totaal and ok == 0:
        print("Geen enkele lijn gekoppeld: er is waarschijnlijk iets mis met de invoer.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
