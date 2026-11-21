# Concept & juridische risicobeheersing

**Status:** werkdocument — geen juridisch advies of formeel advocatenadvies  
**Datum:** 21 november 2026  
**Repository:** `eueclipseglasses-max/eclipseglasses-assets`  
**Branch:** `concept-legale-indekking`  
**Werkgebied van deze nota:** Vlaanderen/België, met De Lijn als concreet referentiekader; FreiFahren als vergelijkend productvoorbeeld.

> **Belangrijke beperking:** volledige juridische indekking bestaat niet door alleen een disclaimer, algemene voorwaarden of een aparte rechtspersoon op te richten. Deze nota is een ontwerp- en due-diligencedocument. Laat de uiteindelijke functionaliteit, teksten, gegevensstromen en exploitatievorm vóór publieke lancering schriftelijk beoordelen door een Belgische advocaat met expertise in vervoersrecht, privacyrecht en IT-/platformrecht.

## 1. Besluit in één oogopslag

Het concept wordt in deze branch uitgewerkt als een **reizigers- en ticketgereedheidsdienst** die wrijving en onnodige vertraging tijdens het instappen en een normale ticketcontrole vermindert. De gebruiker kan zijn geldige vervoerbewijs vooraf klaarzetten, begrijpelijke uitleg krijgen over validering en zijn rechten en eventueel algemene hinder- of drukte-informatie ontvangen.

De juridische ontwerpkeuze is bewust strenger dan het voorbeeld FreiFahren:

- **Wel:** ticketgereedheid, uitleg over geldige vervoersbewijzen, toegankelijkheidsfuncties, algemene storings- en druktemeldingen, en statistieken die voldoende vertraagd en geaggregeerd zijn.
- **Niet:** actuele of voorspellende locaties van controleurs, live waarschuwingen voor controles, een risicokaart per lijn of halte, routes om controle te vermijden, foto's/namen/kenmerken van controlepersoneel, of instructies om controles te hinderen.

Deze grens is de kern van het risicobeheer. Ze voorkomt dat het product wordt ontworpen als hulpmiddel om een controle te ontwijken of zonder geldig vervoerbewijs te reizen. Ze is geen wettelijke vrijgeleide: de volledige implementatie en communicatie moeten nog juridisch worden beoordeeld.

## 2. Productdoel en afbakening

### 2.1 Probleem dat we oplossen

Een reiziger verliest tijd wanneer hij tijdens een instapmoment of controle nog moet zoeken naar zijn ticket, de juiste app moet openen, zijn vervoerbewijs moet activeren of niet weet welke stappen gelden. Het product moet die handelingen **vooraf** eenvoudiger maken. Het mag de uitvoering van een geldige controle niet blokkeren of ontmoedigen.

### 2.2 Voorgestelde gebruikersfuncties

1. **Ticket klaarzetten:** een lokale snelkoppeling of checklist waarmee de reiziger vóór het instappen zijn officiële ticket-app of MOBIB-bewijs opent en nagaat of hij correct heeft gevalideerd.
2. **Heldere statusuitleg:** uitleg over het verschil tussen een gekocht ticket, een geactiveerd ticket en een correct gevalideerd vervoerbewijs. De app beweert niet zelf dat een ticket geldig is, tenzij een vervoerder een officiële verificatie-interface en schriftelijke toestemming verstrekt.
3. **Controlehulp:** een korte, neutrale uitleg: houd het geldige bewijs beschikbaar, volg redelijke instructies van bevoegd personeel en gebruik de officiële kanalen als je een boete wilt betwisten.
4. **Algemene mobiliteitsinformatie:** storingen, vertragingen, toegankelijkheid, drukte of opstapproblemen. Meldingen mogen geen actuele controleploeg, controlevoertuig of controlelocatie identificeren.
5. **Historische inzichten:** uitsluitend statistieken die geen actuele controle kunnen voorspellen of een individuele medewerker kunnen identificeren. Hanteer vóór publicatie minstens een tijdsvertraging, aggregatie en een minimumaantal waarnemingen; laat de gekozen drempels in een DPIA en juridische review toetsen.

### 2.3 Niet-doelen

Het product biedt geen gratis-reizenmechanisme, geen garantie tegen boetes, geen vervangend vervoerbewijs en geen routeadvies om controlepersoneel te ontwijken. Het product wijzigt, genereert, deelt of valideert geen tickets namens een vervoerder zonder formele toestemming.

## 3. FreiFahren als voorbeeld — en als grensgeval

De openbare GitHub-beschrijving van [FreiFahren](https://github.com/FreiFahren/FreiFahren) omschrijft een web- en mobiele toepassing waarin gebruikers waarnemingen van ticketcontroleurs insturen. De app toont die meldingen op een livekaart. Volgens de eigen FAQ worden onder meer halte, optioneel lijn en richting en tijdstip verwerkt; de kaart wordt om de paar seconden bijgewerkt en toont standaard recente meldingen. De FAQ vermeldt ook dat FreiFahren geen juridisch advies verstrekt en dat reizen zonder ticket in Duitsland strafbaar is.

De [privacyverklaring van FreiFahren](https://freifahren.org/datenschutz/) (vermeld als bijgewerkt op 1 november 2026) stelt onder meer dat de exacte gps-locatie op het toestel blijft en niet naar de server wordt doorgestuurd. Dat is een nuttige privacy-ontwerpkeuze, maar bewijst op zichzelf niet dat het volledige productmodel in België rechtmatig is. Een station, lijn, richting en nauwkeurig tijdstip kunnen samen alsnog informatie opleveren over een specifieke controleploeg of medewerker.

**Wat we van FreiFahren kunnen leren:** duidelijke meldstromen, spambeperking, een privacyverklaring die de echte gegevensstromen uitlegt, en transparantie over de werking.

**Wat we niet kopiëren:** realtime controlelocaties, controle-risicovoorspellingen, onmiddellijke waarschuwingen of functionaliteit die gebruikers helpt een controle te vermijden. Een FAQ-tekst waarin staat dat de gebruiker zelf verantwoordelijk is, vormt geen juridische vrijwaring voor de ontwikkelaar of exploitant.

De Duitse strafbepaling [§ 265a StGB](https://www.gesetze-im-internet.de/stgb/__265a.html) gaat over het opzettelijk verkrijgen van bepaalde diensten, waaronder vervoer, zonder de verschuldigde betaling. Die Duitse bepaling geldt niet automatisch als Belgische rechtsgrond. Voor Vlaanderen moet de beoordeling gebeuren aan de hand van de Belgische en Vlaamse regels en de reisvoorwaarden van de betrokken vervoerder.

## 4. Juridisch kader voor Vlaanderen en De Lijn

### 4.1 Geldig vervoerbewijs en medewerking aan controle

De [algemene reisvoorwaarden van De Lijn](https://www.delijn.be/en/content/algemene-reisvoorwaarden/) bepalen onder meer dat een reiziger tijdens de volledige rit over een geldig vervoerbewijs moet beschikken en dit tijdens een controle moet kunnen tonen. Bij een abonnement kunnen correcte registratie/validatie en identiteitscontrole vereist zijn. De voorwaarden verbieden ook vervalste of frauduleus gebruikte vervoerbewijzen en laten toe dat bepaalde ongeldige of frauduleus gebruikte bewijzen in beslag worden genomen.

De Vlaamse Codex bevat het [decreet van 31 juli 1990 betreffende De Lijn](https://codex.vlaanderen.be/Portals/Codex/documenten/1001627.html). De actuele tekst van artikel 44quater beschrijft de bevoegdheden van lijncontroleurs. Daarin staat onder meer dat lijncontroleurs de hoedanigheid van agent van gerechtelijke politie hebben en, met het oog op de vaststelling van inbreuken op de reisvoorwaarden, vervoerbewijzen of verminderingskaarten in beslag mogen nemen, inlichtingen mogen inwinnen en betrokkenen om hun identiteitskaart mogen vragen. De toepasselijke bevoegdheden en de grenzen ervan moeten in concrete situaties door een advocaat worden uitgelegd; de app mag hierover geen stellige individuele rechtsadviezen geven.

Artikel 44ter van hetzelfde decreet vormt de basis voor administratieve geldboetes voor bepaalde inbreuken op de reisvoorwaarden, waaronder het niet beschikken over een geldig vervoerbewijs. De actuele bedragen en procedure moeten telkens worden geverifieerd op de officiële kanalen van De Lijn; neem geen boetebedragen hard op in de app zonder periodieke controle.

### 4.2 Gegevens bij controles

De [privacyinformatie van De Lijn over reizigerscontrole en boetes](https://www.delijn.be/en/content/privacy/reizigerscontrole-en-boetes/) beschrijft welke gegevens De Lijn bij controles en boetedossiers verwerkt, waaronder identiteitsgegevens, rit- en controlegegevens en identificatiegegevens van het betrokken personeelslid. De Lijn vermeldt daarvoor als rechtsgrond haar decretale opdracht en het algemeen belang/openbaar gezag.

Dat De Lijn zelf bepaalde gegevens voor haar wettelijke controletaak mag verwerken, geeft een onafhankelijke app **geen automatisch recht** om dezelfde gegevens te verzamelen, publiceren of hergebruiken. Onze eigen doeleinden, rechtsgrond, noodzaak en bewaartermijn moeten afzonderlijk worden onderbouwd.

### 4.3 Geen automatische conclusie over een meldapp

De openbare bronnen tonen dat FreiFahren meldingen van controleurs publiceert en dat de organisatie zelf haar app als community-meldplatform omschrijft. Ze bewijzen niet dat iedere melding van een controlelocatie op zichzelf strafbaar is, en evenmin dat een vergelijkbare app in België automatisch rechtmatig is. De juridische beoordeling hangt af van onder meer doel, ontwerp, marketing, timing, gegevens, aanmoediging van gebruikers, concrete gevolgen en de manier waarop het platform wordt geëxploiteerd.

Daarom bevat deze branch geen conclusie dat een realtime controlekaart juridisch veilig is. Voor die functionaliteit is een afzonderlijk, schriftelijk advies nodig. De productbaseline in deze nota sluit die functionaliteit uit.

## 5. Privacy en gegevensbescherming (AVG/GDPR)

### 5.1 Rollen en rechtsgrond

Bepaal vóór ontwikkeling wie de verwerkingsverantwoordelijke is (vennootschap, vereniging of natuurlijke persoon), welke verwerkers worden gebruikt en welke gegevens elke partij verwerkt. Leg per doel een passende rechtsgrond vast overeenkomstig artikel 6 AVG. Een algemene verwijzing naar “gerechtvaardigd belang” is niet voldoende: documenteer het doel, de noodzakelijkheid en de belangenafweging. Toestemming mag alleen worden gebruikt wanneer die vrij, specifiek, geïnformeerd en intrekbaar kan worden gegeven.

### 5.2 Dataminimalisatie en locatie

Pas artikel 5 AVG toe: verzamel alleen gegevens die noodzakelijk zijn, gebruik ze alleen voor vooraf bepaalde doelen en zorg voor juistheid, transparantie en beperkte bewaartermijnen. De Belgische Gegevensbeschermingsautoriteit waarschuwt in haar [richtsnoeren over geolocatie in apps](https://www.gegevensbeschermingsautoriteit.be/burger/thema-s/internet/geolocatie-in-apps) dat locatiegegevens alleen mogen worden gebruikt wanneer dat voor de dienst noodzakelijk is; ander gebruik vereist duidelijke informatie en, waar toepasselijk, toestemming.

**Standaardinstelling voor dit project:**
- Geen account verplicht voor basisfuncties.
- Geen continue gps-tracking.
- Geen exacte locatie van gebruikers naar de server sturen wanneer de functie lokaal op het toestel kan werken.
- Geen namen, foto's, gezichten, badges, personeelsnummers of persoonlijke kenmerken van controleurs verzamelen of publiceren.
- Geen individuele controleploeg profileren.
- Alleen geaggregeerde mobiliteitsstatistieken bewaren voor zover heridentificatie redelijkerwijs wordt voorkomen.
- Een concrete bewaartermijn en verwijderprocedure vastleggen voor ruwe meldingen, logs en supportverzoeken.

Een locatie of melding is niet automatisch anoniem omdat een naam ontbreekt. Combinaties van halte, lijn, richting, tijdstip, apparaatmetadata en openbare informatie kunnen personen indirect identificeerbaar maken. Noem gegevens pas anoniem na een gedocumenteerde beoordeling; gebruik anders de term gepseudonimiseerd.

### 5.3 Privacy by design en DPIA

Ontwerp de gegevensstromen vóór het bouwen. Maak een register van verwerkingen, een datastroomschema, een privacyverklaring en een procedure voor inzage-, verwijderings- en andere AVG-verzoeken. Beoordeel met een privacyadvocaat of een gegevensbeschermingseffectbeoordeling (DPIA) verplicht is, in het bijzonder zodra systematische locatieverwerking, monitoring of gegevens over medewerkers aan de orde zouden zijn. Leg passende beveiliging, toegangsbeheer, logging, back-ups, incidentrespons en contracten met verwerkers vast.

## 6. Platformverplichtingen en gebruikersmeldingen

Als de dienst gebruikersinhoud opslaat of publiek verspreidt, moet worden onderzocht of en in welke hoedanigheid de dienst onder de Digital Services Act (DSA) valt. Voor aanbieders van hostingdiensten bevat artikel 16 DSA een verplichting om een toegankelijk mechanisme te hebben waarmee gebruikers mogelijk illegale inhoud kunnen melden. De precieze verplichtingen hangen af van de dienstcategorie en eventuele toepasselijke uitzonderingen.

Minimale productmaatregelen:
- duidelijke gebruikersvoorwaarden en een aanvaardbaar-gebruikbeleid;
- zichtbare knop om inhoud te melden;
- procedure voor snelle triage, beperking of verwijdering van onrechtmatige inhoud;
- contactpunt voor juridische verzoeken;
- moderatielog met toegang op basis van noodzaak;
- bescherming tegen doxing, bedreiging, intimidatie, laster en spam;
- een procedure om gebruikers uit te leggen waarom inhoud is verwijderd of beperkt, waar wettelijk vereist.

Een gebruikersmelding mag niet automatisch als waar worden behandeld. Gebruik verificatie- en moderatiestappen, maar verzamel daarvoor niet méér persoonsgegevens dan nodig.

## 7. Rechten op kaart-, route- en vervoersdata

De huidige repository bevat kaart- en routegerelateerde assets. De bestaande ontwikkelcontext verwijst naar OpenStreetMap-gegevens. OpenStreetMap-data valt onder de [Open Database License (ODbL)](https://www.openstreetmap.org/copyright). De OpenStreetMap Foundation verlangt passende bronvermelding; bij interactieve kaarten hoort die normaal zichtbaar in of naast de kaart te staan, met toegang tot de licentie-informatie.

Controleer per databron:
- herkomst en licentie van ruwe data, routegeometrie, haltegegevens en afbeeldingen;
- of bewerkingen of afgeleide databanken aanvullende ODbL-verplichtingen meebrengen;
- correcte en zichtbare bronvermelding in de gebruikersinterface;
- voorwaarden voor eventuele De Lijn-data, logo's, merknamen, API's of feeds;
- of de presentatie geen officiële samenwerking of goedkeuring door De Lijn suggereert wanneer die er niet is.

Gebruik geen private API, interne controleplanning of niet-openbare vervoerdersdata zonder schriftelijke toestemming en passende contracten.

## 8. Risicomatrix

| Risico | Indicatie | Beheersmaatregel |
|---|---|---|
| Realtime controlelocaties of waarschuwingen | Hoog | Niet bouwen of publiceren in deze productversie; alleen na apart schriftelijk juridisch advies opnieuw beoordelen |
| Ticketfraude, ticketdelen of nagebootste bewijzen | Kritiek | Geen ticketgeneratie, wijziging, kopieerfunctie of omzeiling; uitsluitend officiële ticketkanalen |
| Persoonsgegevens of identificatie van controleurs | Hoog | Geen foto's, namen, badges, live tracking of personeelsprofielen |
| GPS- en gebruikerslocatie | Hoog | Geen server-side continue tracking; lokaal verwerken waar mogelijk; rechtsgrond, informatie en DPIA beoordelen |
| Valse meldingen, intimidatie of doxing | Hoog | Moderatie, meldknop, rate limits, verwijderprocedure en auditspoor |
| UGC/DSA-verplichtingen | Middel/hoog | Juridische classificatie en passend notice-and-action-proces vóór lancering |
| Onjuiste claim dat de app tickets valideert | Hoog | Claim alleen officiële verificatie wanneer een vervoerder die bevestigt en contractueel toestaat |
| Hergebruik van kaart- en routegegevens | Middel | Licentiecontrole, OSM-attributie en schriftelijke toestemming waar nodig |
| Misleidende indruk van officiële samenwerking | Middel | Duidelijke onafhankelijke status; geen logo's of formuleringen die endorsement suggereren |

De risicolabels zijn interne ontwerpinschattingen, geen officiële juridische classificaties.

## 9. Verplichte release-gates

De publieke release mag niet doorgaan voordat alle onderstaande punten aantoonbaar zijn afgevinkt:

- [ ] Exacte productbeschrijving, doelgroep, verdienmodel en landen vastgelegd.
- [ ] Belgische juridische review van de concrete gebruikersflows, meldingen, marketing en moderatie afgerond.
- [ ] Schriftelijke beoordeling van de vraag of enig onderdeel de omzeiling van controles faciliteert; realtime controlelocaties blijven standaard uitgesloten.
- [ ] Verwerkingsverantwoordelijke, verwerkers en eventuele gezamenlijke verantwoordelijkheden vastgelegd.
- [ ] Datastroomschema, register van verwerkingen, privacyverklaring en bewaartermijnen goedgekeurd.
- [ ] DPIA-noodzaak schriftelijk beoordeeld en, waar nodig, DPIA afgerond vóór verwerking.
- [ ] Gebruikersvoorwaarden, communityregels, notice-and-action, klachten- en verwijderproces gepubliceerd.
- [ ] Beveiligingsmaatregelen en incidentrespons getest.
- [ ] Licenties en bronvermelding van kaart-, route- en haltegegevens gecontroleerd.
- [ ] Toestemming/contracten van vervoerder geregeld voor elke officiële API, ticketverificatie of branding.
- [ ] Passende beroeps-, cyber- en aansprakelijkheidsverzekeringen beoordeeld; dekking schriftelijk bevestigd door verzekeraar.
- [ ] Support- en appealverwijzingen leiden naar de officiële vervoerder; de app belooft geen boetevrij reizen.

## 10. Aanbevolen juridische en organisatorische indekking

1. **Exploitant kiezen:** laat beoordelen of een Belgische vennootschap of vereniging zonder winstoogmerk past bij de feitelijke commerciële en maatschappelijke doelstelling. De rechtsvorm maakt onrechtmatige functionaliteit niet rechtmatig en sluit persoonlijke aansprakelijkheid niet in alle omstandigheden uit.
2. **Schriftelijk productadvies:** laat de advocaat de definitieve schermen, pushmeldingen, zoekfilters, databankvelden, moderatie, marketing en verdienmodel beoordelen. Vraag expliciet advies over het verschil tussen ticketgereedheid en het faciliteren van het ontwijken van controles.
3. **Contracten:** stel voorwaarden voor eindgebruikers, privacyverklaring, cookiebeleid, verwerkersovereenkomsten, interne toegangsregels en eventuele vervoerdersovereenkomsten op.
4. **Verzekeringen:** bespreek cyberverzekering, beroeps-/bedrijfsaansprakelijkheid en medi-/publicatieaansprakelijkheid. Vraag de verzekeraar expliciet of user-generated content, privacyclaims en intellectuele-eigendomsclaims gedekt zijn.
5. **Governance:** wijs één verantwoordelijke aan voor privacy, contentmoderatie en juridische verzoeken; houd een wijzigingslog bij en voer periodieke controles uit.
6. **Geen schijnzekerheid:** vermijd formuleringen zoals “100% legaal”, “boeteproof”, “juridisch volledig ingedekt” of “de gebruiker is volledig zelf aansprakelijk”. Een disclaimer vervangt geen wettelijke verplichtingen.

## 11. Voorlopige publiekscopy

> Deze dienst helpt reizigers hun rit en officiële vervoerbewijs vooraf klaar te zetten en geeft algemene mobiliteitsinformatie. De dienst is geen vervoerder, verkoopt of valideert geen vervoerbewijzen en vervangt de reisvoorwaarden van de vervoerder niet. Reizigers blijven zelf verantwoordelijk voor een geldig en correct gevalideerd vervoerbewijs en moeten redelijke, wettige controle-instructies opvolgen. De dienst toont geen actuele controlelocaties en geeft geen advies om controles te vermijden. Raadpleeg bij twijfel altijd de officiële informatie van je vervoerder.

Deze tekst is een startpunt, geen finale algemene voorwaarde. Laat hem aanpassen aan de echte functionaliteit en de gekozen exploitant.

## 12. Open punten voor formele beoordeling

De volgende vragen moeten door de projectverantwoordelijke en advocaat worden beantwoord vóór een definitief juridisch oordeel mogelijk is:

1. Is het beoogde doel het verkorten van de tijd die een reiziger nodig heeft om een geldig ticket te tonen, of het verminderen van de kans dat een reiziger tijdens een controle wordt betrapt? Alleen de eerste doelstelling is de uitgangspositie van deze nota.
2. Worden er gebruikersmeldingen ingestuurd? Welke exacte velden, tijdstippen, metadata en locaties worden verwerkt en hoe lang?
3. Worden de gegevens publiek getoond, aan partners verkocht of in pushmeldingen gebruikt?
4. Is de dienst uitsluitend actief in Vlaanderen/België, of ook in Duitsland of andere landen?
5. Is er een officiële samenwerking of API-toestemming van De Lijn of een andere vervoerder?
6. Welke rechtspersoon exploiteert de dienst, wie is verwerkingsverantwoordelijke en wie beheert meldingen en juridische verzoeken?

## 13. Bronnen en referenties

**België / Vlaanderen**
- [Decreet van 31 juli 1990 betreffende De Lijn — Vlaamse Codex](https://codex.vlaanderen.be/Portals/Codex/documenten/1001627.html) — in het bijzonder artikelen 44ter en 44quater.
- [Besluit Vlaamse Regering van 16 september 2022 over reisvoorwaarden en handhaving](https://codex.vlaanderen.be/PrintDocument.ashx?geannoteerd=false&id=1037735).
- [Algemene reisvoorwaarden De Lijn](https://www.delijn.be/en/content/algemene-reisvoorwaarden/).
- [De Lijn: reizigerscontrole en boetes / privacy](https://www.delijn.be/en/content/privacy/reizigerscontrole-en-boetes/).
- [Gegevensbeschermingsautoriteit: geolocatie in apps](https://www.gegevensbeschermingsautoriteit.be/burger/thema-s/internet/geolocatie-in-apps).

**EU**
- [AVG / GDPR — Verordening (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/), in het bijzonder artikelen 5 en 6.
- [Digital Services Act — Verordening (EU) 2022/2065](https://eur-lex.europa.eu/eli/reg/2022/2065/oj/eng/), in het bijzonder artikel 16.

**Vergelijkend voorbeeld Duitsland**
- [FreiFahren — openbare GitHub-repository](https://github.com/FreiFahren/FreiFahren).
- [FreiFahren — FAQ](https://freifahren.org/faq/).
- [FreiFahren — privacyverklaring](https://freifahren.org/datenschutz/).
- [§ 265a Strafgesetzbuch (Duitsland)](https://www.gesetze-im-internet.de/stgb/__265a.html).

**Kaart- en databronnen**
- [OpenStreetMap — Copyright en ODbL](https://www.openstreetmap.org/copyright).
- [OpenStreetMap Foundation — Attribution Guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines).

---

**Conclusie:** de verdedigbare uitgangspositie voor dit project is een hulpmiddel dat reizigers helpt correct en sneller hun geldige vervoerbewijs te tonen, niet een systeem dat actuele controleposities verspreidt. FreiFahren is een bruikbare functionele vergelijking, maar geen precedent, certificaat of juridische vrijwaring. De definitieve juridische zekerheid kan alleen volgen uit een beoordeling van de concrete Belgische implementatie door een bevoegde advocaat.
