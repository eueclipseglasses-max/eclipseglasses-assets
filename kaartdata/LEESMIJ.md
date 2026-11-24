# Lijntrajecten op de kaart

De kaart van De Golem tekent elke bus- en tramlijn langs de echte straten, in de eigen kleur van de lijn.
De trajecten komen uit **OpenStreetMap** (dezelfde bron als de achtergrondkaart van OpenFreeMap), dus ze vallen precies samen met de straten op de kaart.

## Hoe het werkt

1. Elke **nacht** controleert de GitHub Action *Kaartdata lijntrajecten* (`.github/workflows/kaartdata.yml`) of er iets veranderd is: een nieuw netwerk in de app (`/api/netwerk`), of kaartdata die een week oud is. Alleen dan bouwt ze opnieuw. Loopt de import van het netwerk nog, dan wacht ze.
2. Die downloadt OpenStreetMap voor België en houdt alleen de bus- en tramtrajecten van De Lijn over.
3. `bouw_lijnen.py` haalt alle lijnen en haltes van heel Vlaanderen op uit de app (`/api/routes` en `/api/stops`, in pagina's) en zoekt per lijn (per richting) het traject dat echt langs die haltes rijdt:
   - zelfde lijnnummer;
   - haltes binnen 50 m van het traject;
   - bij voorkeur dezelfde haltenummers (zo kiest het script ook de juiste rijrichting).
4. Daarna bouwt het één **wegennet**: per straat (OSM-weg) welke lijnen erover rijden.
   - Rijden er meerdere lijnen door dezelfde straat, dan krijgt elke lijn een eigen strook, zoals op een metroplan. Zo verdwijnt geen enkele kleur onder een andere.
   - De volgorde van de stroken ligt vast: lijnnummer van klein naar groot. Lijnen die samen rijden, gebruiken dezelfde rijrichting, zodat ze in bochten niet van kant wisselen.
   - Op een drukke straat worden de stroken smaller, zodat de bundel niet te breed wordt.
5. Het net wordt geknipt in tegels van ongeveer 7 × 7 km. Het resultaat komt op de branch **`kaartdata`**:
   - `index.json` met per lijn de kleur, de soort, het gebied en de tegels;
   - `net/<x>_<y>.json` per tegel;
   - `RAPPORT.md`.
6. De Worker (`albeter`) geeft die bestanden door via `/kaartdata/...`. De app vraagt tegels en routes op met `?v=<bouwtijd>` uit `index.json`, zodat na een nieuwe bouw nooit oude en nieuwe bestanden door elkaar gebruikt worden. De kaart laadt alleen de tegels die in beeld zijn (vanaf zoom 10,5), plus de tegels van de gekozen lijn.

## Op de kaart

- **Standaard rustig:** alle lijnen zijn één dunne grijze lijn per straat.
- **Kleur verschijnt alleen waar het iets betekent:**
  - de lijn die je kiest in het formulier (beide richtingen, zodat een eindhalte met een lus niet onderbroken lijkt);
  - de lijnen van een halte of straat waarop je tikt, zolang de popup open is (bij meer dan 5 lijnnummers niet, dan wordt het te druk);
  - een melding op een lijn kleurt alleen het stuk van die halte tot de volgende halte rood (met een pulserende gloed) en het stuk daarna geel, in de rijrichting van de lijn.
- **Zelfde kleur = één strook:** gekleurde lijnen die dezelfde straat delen, liggen naast elkaar. Lijnen met dezelfde kleur, zoals de witte streeklijnen, delen één strook.
- **Vloeiende lijnen:**
  - Hoeken worden afgerond, met een straal van hoogstens 15 m.
  - Waar een lijn invoegt of afbuigt, schuift ze geleidelijk op over ongeveer 60 m in plaats van met een sprong.
- **Meldingen in de tijd:** een melding of een herbevestiging ("nog daar") is 25 minuten "vers": het haltebolletje pulseert rood. Daarna wordt het grijs (ook het stuk lijn) en na 1 uur verdwijnt de melding.
- **Achtergrondkaart:** water blauw en parken, gras en bos groen (functie `kaartKleuren` in `albeter`).
- **Haltes:** geel voor bus, paars voor tram. Ze zijn klein en worden groter naarmate je inzoomt.
- **Eigen locatie:** een blauw bolletje. Tik op de knop onder + en − om ernaartoe te gaan. Heb je eerder al toestemming gegeven, dan staat het bolletje er meteen.
- **Gsm:** tik je op een halte of lijn, dan verschijnen de keuzes onderaan in een blad met grote knoppen. Dat blad kun je scrollen en sluiten met ×.
- **Badges overal:** het lijnbadge (kleur en cijferkleur zoals het lijnbord) staat in de popups van lijnen en haltes, naast de lijnkeuze in het formulier, bij elke melding en bij de controles in de haltepopup.

De kleur is de officiële kleur van De Lijn (uit de app). Ontbreekt die, dan de kleur uit OpenStreetMap (tag `colour`), en anders de standaardkleur voor bus of tram.

## Wat moet je zelf doen?

Niets. De app laadt zelf het netwerk van heel Vlaanderen in (zie DEPLOY.md, "Netwerk van heel Vlaanderen"). Is dat klaar, dan bouwt de volgende nacht de kaartdata opnieuw.

- **Meteen bijwerken:** tabblad *Actions* → *Kaartdata lijntrajecten* → *Run workflow*.
- **Rapport bekijken:** open de laatste run in *Actions* (het rapport staat onderaan de samenvatting), of `RAPPORT.md` op de branch `kaartdata`. Daar staan lijnen die niet gekoppeld konden worden en haltes die meer dan 40 m van hun plaats in OpenStreetMap liggen.

## Gaten in een lijn

Soms ontbreekt in OpenStreetMap een stukje weg in een traject. Het script dicht zo'n gat automatisch:
- eerst via het kortste pad over andere bus- en tramwegen (ook van andere vervoerders, tot 1,5 km);
- lukt dat niet, dan met een recht stukje als het gat kleiner is dan 60 m.

Gaten die open blijven, staan in het rapport onder "Onderbrekingen", met een link naar de plek.

## Een lijn ontbreekt of loopt verkeerd

Bijna altijd ontbreekt het traject in OpenStreetMap, of heeft het daar een ander lijnnummer. Je kunt het zelf verbeteren op openstreetmap.org (zoek het trajectnummer uit het rapport). Binnen een week neemt het script de verbetering over (of meteen met *Run workflow*).

## Instellingen

Bovenaan `bouw_lijnen.py`:

| Instelling | Standaard | Betekenis |
|---|---|---|
| `MAX_AFSTAND_M` | 50 | een halte "ligt op" het traject binnen deze afstand |
| `MIN_SCORE` | 0.6 | minimale overeenkomst om een traject te aanvaarden |
| `VEREENVOUDIG_M` | 2.0 | punten die minder dan 2 m afwijken worden weggelaten (kleinere bestanden) |
| `MAX_STUKKEN` | 6 | max. aantal OSM-trajecten die samen één lijn vormen (varianten, of een lijn die in OSM in stukken staat) |
| `TEGEL_LON`, `TEGEL_LAT` | 0.1, 0.0625 | tegelgrootte in graden |
| `ALIASSEN` | `KT` → kusttram | lijnnummers die in OpenStreetMap anders heten |

## Lokaal testen

```sh
pip install osmium
osmium tags-filter belgium-latest.osm.pbf r/route=bus,tram r/route_master=bus,tram -o trajecten.osm.pbf
python kaartdata/bouw_lijnen.py --osm trajecten.osm.pbf --uit uitvoer
```

## Goed om te weten

- **Kosten:** gratis. GitHub Actions is gratis voor openbare repositories; een run duurt enkele minuten.
- **Privé repository?** Dan kan de Worker de bestanden niet meer van `raw.githubusercontent.com` lezen. Zet dan een GitHub-token als geheim in de Worker, of zet de bestanden in Cloudflare R2.
- **Bronvermelding:** de kaart toont "Lijntrajecten © OpenStreetMap-bijdragers". Laat dat staan; het is verplicht onder de ODbL-licentie.
