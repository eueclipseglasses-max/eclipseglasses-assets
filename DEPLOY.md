# Automatisch naar Cloudflare (met versies)

**Doel:** elke merge naar `main` zet de nieuwe `albeter` automatisch live, zonder kopiëren en plakken.

**Versies:**
- Cloudflare bewaart elke uitrol als **versie**. Je kunt er altijd naar terug: Worker → **Deployments** → **Rollback**.
- GitHub bewaart elke wijziging (commits en pull requests).
- Andere branches kunnen een **preview** krijgen: een aparte testlink, zonder dat de echte site verandert.

## Eenmalig instellen (± 10 minuten)

1. **Vul `wrangler.toml` in** (drie waarden, staan erin uitgelegd):
   - de naam van de Worker;
   - de naam en het ID van de D1-databank;
   - hoe het domein gekoppeld is: Custom Domain of Route.

   Commit dit via een pull request. Met die waarden kan ik het ook voor je doen.
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
