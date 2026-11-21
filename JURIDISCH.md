# De Golem – juridisch overzicht

*Laatst bijgewerkt: 21 november 2026. Dit is geen juridisch advies: laat de teksten nakijken door een jurist voor de officiële lancering.*

## 1. Uitgangspunt

De Golem is **louter informatief**: reizigers melden waar ze een controle ("platte band") zagen. Wat De Golem uitdrukkelijk zegt en doet:

- **Ticket verplicht:** een geldig vervoerbewijs blijft altijd verplicht. Zonder geldig vervoerbewijs riskeer je een boete van De Lijn, tot € 474.
- **Geen aansporing:** De Golem moedigt zwartrijden niet aan en is niet bedoeld om controles te ontwijken.
- **Geen garantie:** meldingen zijn waarnemingen van gebruikers, zonder garantie op juistheid of volledigheid.
- **Onafhankelijk:** De Golem is niet verbonden aan De Lijn. Lijnnummers, haltenamen en lijnkleuren worden alleen beschrijvend gebruikt. Gebruik geen logo van De Lijn.

## 2. Waar staat wat op de site?

| Plaats | Inhoud |
|---|---|
| Melding bij het openen | Verschijnt één keer per versie (`VOORAF_VERSIE` in `albeter`). Bevat: ticket verplicht (boete tot € 474), louter informatief, niet verbonden aan De Lijn, respect voor controleurs en geen herkenbare personen fotograferen. Met links naar de voorwaarden en het privacybeleid. |
| Meldformulier | Vaste regel: "Louter informatief: een geldig vervoerbewijs blijft altijd verplicht." |
| `/voorwaarden` | Informatief karakter, ticketplicht, geen garantie en beperking van aansprakelijkheid, regels voor meldingen en foto's, moderatie, niet verbonden aan De Lijn, wijzigingen, Belgisch recht. |
| `/privacy` | Welke gegevens, doel en grondslag, bewaartermijnen, delen (Cloudflare, OpenFreeMap), lokale opslag en cookie, rechten en klacht bij de Gegevensbeschermingsautoriteit. |
| `/over`, `/contact`, `/misbruik` | Wie we zijn, bronvermelding OpenStreetMap, hoe je misbruik meldt. |

**Wijzig je de voorwaarden inhoudelijk?** Verhoog dan `VOORAF_VERSIE`. Iedereen ziet de melding bij het openen dan opnieuw.

## 3. Privacy (GDPR) in de praktijk

| Gegeven | Waarom | Bewaartermijn |
|---|---|---|
| Melding (lijn, halte, tijdstip, "rijdt mee") | De dienst laten werken | 1 uur zichtbaar, daarna alleen voor statistiek (zonder naam) |
| Gehashte code van de internetverbinding | Misbruik voorkomen en meldlimiet | 24 uur (automatisch gewist) |
| GPS (optioneel, alleen na tikken) | Vergelijken met de halte | Niet bewaard |
| Foto (optioneel) | Melding staven | 30 dagen (automatisch gewist); EXIF/GPS van de foto wordt in de app verwijderd |
| Account (optioneel) | Inloggen | Zolang het account bestaat |

**Foto's en portretrecht:** voor het nemen en publiceren van een herkenbare foto van iemand is in principe diens toestemming nodig. Daarom:
- vraagt de app om geen gezichten of herkenbare personen te fotograferen;
- wordt een foto pas openbaar na 3 × "nog daar" of na goedkeuring door een beheerder;
- kunnen beheerders elke foto weigeren of verwijderen.

## 4. Nog te doen vóór de officiële lancering

1. **Contactadres invullen:** zet `CONTACT_EMAIL` in `albeter` (bv. `info@…`). Onder de GDPR moet duidelijk zijn wie verantwoordelijk is en hoe je die bereikt. Vermeld eventueel ook een naam of een organisatie (vzw of onderneming).
2. **Meldlimiet terugzetten:** zet `MELDLIMIET_PER_UUR` terug op een lage waarde (bv. 3) na de testfase.
3. **Jurist:** laat de voorwaarden, het privacybeleid en het concept (meldingen over controles) nakijken door een jurist.
4. **Verwijderverzoeken:** zorg voor een vaste werkwijze voor verzoeken tot inzage of verwijdering. Antwoord binnen een maand.
5. **Moderatie:** controleer foto's in de beheerderslijst vóór je ze goedkeurt. Weiger foto's met herkenbare personen.

## 5. Bronnen

- De Lijn – boete tot € 474 voor reizen zonder geldig vervoerbewijs: <https://www.delijn.be/en/nieuws/zwartrijden-is-geen-spelletje/>
- Algemene reisvoorwaarden De Lijn: <https://www.delijn.be/>
- Gegevensbeschermingsautoriteit: <https://www.gegevensbeschermingsautoriteit.be/>
