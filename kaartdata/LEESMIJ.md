# Lijntrajecten op de kaart

De kaart van De Golem tekent elke bus- en tramlijn langs de echte straten, in de eigen kleur van de lijn.
De trajecten komen uit **OpenStreetMap** (dezelfde bron als de achtergrondkaart van OpenFreeMap), dus ze vallen precies samen met de straten op de kaart.

## Hoe het werkt

1. Elke **maandagnacht** draait de GitHub Action *Kaartdata lijntrajecten* (`.github/workflows/kaartdata.yml`).
2. Die downloadt OpenStreetMap voor België en houdt alleen de bus- en tramtrajecten van De Lijn over.
3. `bouw_lijnen.py` haalt alle lijnen en haltes op uit de app (`/api/routes` en `/api/stops`) en zoekt per lijn (per richting) het traject dat echt langs die haltes rijdt:
   - zelfde lijnnummer;
   - haltes binnen 50 m van het traject;
   - bij voorkeur dezelfde haltenummers (zo kiest het script ook de juiste rijrichting).
4. Het resultaat komt op de branch **`kaartdata`**: een `index.json`, één klein bestand per traject (`lijnen/r<nummer>.json`) en een `RAPPORT.md`.
5. De Worker (`albeter`) geeft die bestanden door via `/kaartdata/...`. De kaart laadt alleen de lijnen die in beeld zijn.

De kleur komt uit OpenStreetMap (tag `colour` van het traject of de lijn). Ontbreekt die, dan krijgt een buslijn blauw en een tramlijn oranje, zoals de haltes.

## Wat moet je zelf doen?

Niets. Komen er nieuwe lijnen of steden bij in de databank, dan neemt de volgende run ze automatisch mee. Dat werkt voor heel Vlaanderen.

- **Meteen bijwerken:** tabblad *Actions* → *Kaartdata lijntrajecten* → *Run workflow*.
- **Rapport bekijken:** open de laatste run in *Actions* (het rapport staat onderaan de samenvatting), of `RAPPORT.md` op de branch `kaartdata`. Daar staan lijnen die niet gekoppeld konden worden en haltes die meer dan 40 m van hun plaats in OpenStreetMap liggen.

## Een lijn ontbreekt of loopt verkeerd

Bijna altijd ontbreekt het traject in OpenStreetMap, of heeft het daar een ander lijnnummer. Je kunt het zelf verbeteren op openstreetmap.org (zoek het trajectnummer uit het rapport). De volgende maandag neemt het script de verbetering over.

## Instellingen

Bovenaan `bouw_lijnen.py`:

| Instelling | Standaard | Betekenis |
|---|---|---|
| `MAX_AFSTAND_M` | 50 | een halte "ligt op" het traject binnen deze afstand |
| `MIN_SCORE` | 0.6 | minimale overeenkomst om een traject te aanvaarden |
| `VEREENVOUDIG_M` | 2.0 | punten die minder dan 2 m afwijken worden weggelaten (kleinere bestanden) |
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
