# Automatisch naar Cloudflare (met versies)

**Doel:** elke merge naar `main` zet de nieuwe `albeter` automatisch live, zonder kopiëren en plakken.

**Versies:**
- Cloudflare bewaart elke uitrol als **versie**. Je kunt er altijd naar terug: Worker → **Deployments** → **Rollback**.
- GitHub bewaart elke wijziging (commits en pull requests).
- Andere branches kunnen een **preview** krijgen: een aparte testlink, zonder dat de echte site verandert.

## Eenmalig instellen (± 10 minuten)

1. **`wrangler.toml` is ingevuld:** Worker `curly-block-7b36`, D1-databank op ID, domein `eclipseglasses.eu` als Custom Domain. De workers.dev-link en previewlinks blijven aan.
2. **Koppel GitHub in Cloudflare:** Workers & Pages → je Worker → **Settings** → **Build** → **Connect** → kies GitHub en de repository `eclipseglasses-assets`.
   - Productiebranch: `main`.
   - Build command: leeg laten (staat al in `wrangler.toml`).
   - Deploy command: `npx wrangler deploy`.
3. **Previews:** zet bij **Branch control** de optie voor builds van andere branches aan. Dan krijgt elke pull request een testversie met een eigen link, met de standaardopdracht `npx wrangler versions upload`.
4. **Geheimen controleren:** `DELIJN_API_KEY` en de tweede sleutel blijven gewoon in Cloudflare staan. Ze komen nooit in GitHub.

## Werkwijze daarna

1. Wijzigingen gebeuren in een **branch** met een **pull request**.
2. Bekijk de previewlink en test.
3. **Merge** naar `main`. Cloudflare bouwt en zet de nieuwe versie automatisch live.
4. Loopt er iets mis? Kies Worker → **Deployments** → vorige versie → **Rollback**.

**Belangrijk:** pas de code niet meer rechtstreeks aan in de Cloudflare-editor. De volgende merge overschrijft die wijziging. GitHub is vanaf nu de enige bron.

## Netwerk van heel Vlaanderen

De app laadt zelf alle lijnen, richtingen en haltes van De Lijn in (Kern Open Data, met dezelfde sleutel als de live posities). Dat gebeurt in kleine stappen:

- **Elke minuut** één stap via de cron in `wrangler.toml` (`[triggers]`). Zet je `albeter` met de hand in Cloudflare in plaats van via GitHub, voeg de cron dan zelf toe: Worker → **Settings** → **Triggers** → **Cron Triggers** → `* * * * *`.
- Zonder cron gaat het ook vooruit, maar trager: bij gewoon gebruik van de app doet de server af en toe een stap.
- Daarna **elke week** opnieuw. Alleen wat veranderd is, wordt geschreven.

**Hoe lang duurt de eerste keer?** Vlaanderen telt ongeveer 35.000 haltes. Het gratis plan van D1 laat 100.000 geschreven rijen per dag toe. De import gebruikt daarvan hoogstens 70.000 per dag, zodat de app zelf blijft werken. Op het gratis plan duurt de eerste keer daardoor enkele dagen. Je ziet de regio's een voor een verschijnen: eerst West-Vlaanderen, dan Oost-Vlaanderen, Antwerpen, Vlaams-Brabant en Limburg. De oude gegevens blijven intussen gewoon werken.

**Sneller op het betaalde plan (Workers Paid):** zet in Cloudflare twee variabelen (Settings → Variables):

| Variabele | Waarde | Betekenis |
|---|---|---|
| `NETWERK_SCHRIJF_PER_DAG` | `5000000` | maximum aantal geschreven rijen per dag |
| `NETWERK_PER_KEER` | `30` | stappen per minuut (standaard 8) |

**Stand volgen:** log in als beheerder, open het menu (☰) → *Beheer*. Daar staat hoe ver de import is, met een knop *Netwerk nu bijwerken*. Het netwerk opnieuw van nul inladen kan via een POST naar `/api/admin/netwerk` met `{"actie":"opnieuw"}`.

Is de import klaar, dan bouwt de GitHub Action de lijntrajecten op de kaart de volgende nacht opnieuw voor heel Vlaanderen (zie `kaartdata/LEESMIJ.md`).
