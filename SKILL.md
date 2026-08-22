---
name: html-annotator
description: Standaard feedback-component voor ELKE HTML-pagina die voor Luc wordt gemaakt (prototypes, slides, vergelijkingspagina's, dashboards). Bouw het annotatie-snippet standaard in bij elke nieuwe of substantieel herziene HTML-oplevering, zonder dat Luc erom hoeft te vragen. Trigger ook wanneer Luc zegt "verwerk mijn feedback", "check mijn bewaarde feedback" of naar een annotations.json / annotatieronde verwijst; dan beschrijft deze skill hoe je de rondes en screenshot-crops uitleest en verwerkt.
---

# HTML-annotator: standaardcomponent + feedbackverwerking

## Deel 1: inbouwen (bij elke HTML-oplevering)

Plak de volledige inhoud van `annotator-snippet.html` (in deze skill-map) onderaan
elke HTML die Luc te zien krijgt, vlak voor `</body>` of aan het einde van het
bestand. Het blok loopt van `<!-- LUC-ANNOTATOR v2 -->` tot `<!-- /LUC-ANNOTATOR -->`.

Detectie bij een bestaande pagina:
- staat `LUC-ANNOTATOR v2` er al: niets doen;
- staat er een ouder blok (`LUC-ANNOTATOR v1`, zonder eindmarker): vervang alles
  vanaf `<!-- LUC-ANNOTATOR` tot en met het bijbehorende `</script>` door het
  nieuwe blok;
- staat er niets: onderaan toevoegen.

Self-contained: geen libraries, geen CDN, geen externe fonts. Werkt op file://
en localhost.

**Start daarna altijd de bridge.** Eén commando, idempotent, dus blind aanroepen
bij elke oplevering en elke update van een pagina met het snippet erin:

```bash
~/.claude/skills/html-annotator/ensure-bridge.sh
```

Draait hij al, dan doet het script niets. Draait hij niet, dan start het hem
losgekoppeld van je shell (nohup), schrijft de pid naar `bridge.pid` en de
output naar `bridge.log` in de skill-map, en wacht het tot hij antwoordt (max
5 seconden). Sla dit nooit over: zonder bridge annoteert Luc in localStorage en
staat er niets op schijf.

**Vangnet, twee lagen.** Beide draaien `hook-ensure-bridge.sh` uit deze skill-map
(log: `bridge-hook.log`), geregistreerd in `~/.claude/settings.local.json`:

- **SessionStart** — één aanroep per sessie, ongeacht hoe die sessie straks HTML
  wegschrijft. Dit is de laag die telt: de PostToolUse-laag mist een agent die het
  bestand via Bash wegschrijft, en in auto-mode is Bash juist de voorgeschreven route.
- **PostToolUse op `Edit|Write`** — is het geschreven bestand een `.html`/`.htm` met de
  marker `LUC-ANNOTATOR`, dan gaat de bridge omhoog.

De matcher is niet verbreed naar `Bash`, want dat zou op élke Bash-call in élk project
vuren. Wat de gekozen route wél doet: de SessionStart-registratie staat op user-niveau met
een lege matcher, dus hij draait bij het starten van élke Claude Code-sessie op deze
machine, ook sessies die niets met annotaties doen. Dat is één curl per sessie, en niets
meer als de bridge al luistert. **Luc heeft dat bewust zo gekozen** (18-08-2026), nadat het
verschil in bereik expliciet was voorgelegd: hij wil dat de bridge praktisch altijd
aanstaat. Verklein dit niet zonder hem te vragen.

**Zelfherstel in de pagina.** Het snippet controleert de bridge niet één keer bij het
laden, maar blijft elke 3 seconden opnieuw proberen zolang hij niet antwoordt (plus bij
`visibilitychange` en `focus`). Komt de bridge later omhoog — door de hook, of met de
hand — dan slaat de statuspil vanzelf om en is er geen reload nodig. Dit was een echte
bug: een al openstaande pagina bleef anders op "bridge uit" staan en waarschuwde dat er
niets bewaard werd, terwijl opslaan inmiddels wel lukte.

Verificatie hiervan staat in `tests/` — zie `tests/criteria.md` voor de criteria en
`tests/run.sh` voor de suite. Twee grenzen die je moet kennen voordat je op groen
vertrouwt: (1) dat een **verse agent** dit in de praktijk goed doet is nooit geverifieerd
— die case liep op een spend-limit en meldt zich als BLOKKED, niet als pass; (2) de
verborgen-paneel-variant emuleert `document.hidden` en toetst dus de branch-logica van het
snippet, niet Chrome's throttling van timers in een echte achtergrondtab.

**Open de pagina altijd via de bridge, nooit via `file://` of de preview-pane.**
De bridge serveert lokale bestanden zelf op `GET /p/<pad-vanaf-home>`:

```
/Users/lucmahieu/Desktop/todos.html
→ http://127.0.0.1:8791/p/Desktop/todos.html
```

Bouwen doe je zo: neem het absolute pad, haal de home-map (`/Users/lucmahieu/`)
eraf en plak de rest achter `http://127.0.0.1:8791/p/`. Paden buiten de home-map
geeft de bridge 403.

Dit lost een echt probleem op: de preview-pane van Claude Code serveert een
lokaal bestand als `data:`-snapshot, en vanuit zo'n snapshot blokkeert Chrome elk
verzoek naar localhost. Gemeten reden (`tests/case-02-selfheal.mjs`, origin `data`):
*"the resource is in more-private address space `loopback`"* — Private Network Access.
Dat is browserbeleid, niet iets wat een CORS-header of een hook kan repareren. De
statuspil bleef dan op "bridge uit" staan terwijl de bridge wel draaide, en er werd niets
weggeschreven.

De bridge logt daarom `origin=<waarde>` bij elk verzoek, zodat van een ingebedde weergave
vast te stellen is vanaf welke origin hij aanroept in plaats van het te moeten aannemen.
Blijft permanent aan, op verzoek van Luc (18-08-2026). Via `/p/` is de pagina
same-origin met de bridge en werkt opslaan altijd. Het snippet leidt het
bestandspad uit zo'n `/p/`-URL af, dus rondedetectie en crops blijven werken.

Wat Luc kan:
- **Annotate selection** (regio): knop rechtsonder → rechthoek slepen (snipping-stijl) →
  comment typen, afbeelding plakken of bijvoegen → Save. De gesleepte rechthoek
  blijft zichtbaar zolang de commentbox open staat (rest van de pagina gedimd)
  en verdwijnt pas bij Save of Cancel.
- **Toetsen in de commentbox**: Cmd+Enter of Ctrl+Enter slaat op, Escape
  annuleert.
- **Tekstselectie**: gewoon tekst selecteren → er verschijnt een paars knopje
  "Annoteer selectie" → comment typen → Save. De geselecteerde tekst komt in de
  JSON, er wordt geen screenshot gemaakt.
- Er is geen download-knop: de bridge is de enige opslagroute.
- Badges: blauw = regio, paars = tekstselectie. Klik erop om te bekijken,
  bewerken of verwijderen.
- Statuspil links van de knoppen: `round N - X annotaties opgeslagen` (X = het
  aantal **openstaande** annotaties op schijf), of "bridge uit - alleen
  localStorage".
- **Afvinken in de UI**: elk kaartje in de weeslijst heeft een ✓, en de popup van
  elke badge ook. Dat zet `resolved` via de bridge; de annotatie verdwijnt van de
  pagina en blijft in de JSON staan.

Elke Save schrijft direct weg via de bridge. Zodra de bridge bereikbaar is, is
hij ook leidend voor wat de pagina toont: bij het laden haalt het snippet de
openstaande (niet-resolved) annotaties van de lopende ronde op en tekent alleen
die. Zonder bridge blijft localStorage het vangnet.

Kan een anker niet meer geplaatst worden na een pagina-wijziging, dan verschijnt
er linksonder een klein kaartje **"N annotaties waarschijnlijk verwerkt"**. Dat
is bewust geen foutmelding: een anker verdwijnt meestal juist doordat de tekst is
aangepast, dus het is een opruimlijst. Het kaartje is standaard **ingeklapt**
(alleen de kopregel met chevron), onthoudt zijn open/dicht-stand in localStorage
en wijkt uit naar boven als het de knoppenbalk rechtsonder zou raken. Openklappen
geeft per annotatie de comment (klik = popup) en een ✓ om hem af te vinken.

Test/debug-API: `window.LucAnnotator.add({type:'region'|'text', rect, comment,
selectedText})` (geeft een promise terug), `.anns()`, `.bridge()`, `.session()`,
`.resolve(annotatie)`.

## Deel 2: de bridge

Een browserpagina kan zelf niet naar schijf schrijven. `annotator-bridge.py`
(stdlib only) lost dat op: hij luistert op **127.0.0.1:8791** (niet 0.0.0.0,
en niet 8080 want dat is van Docker), beheert de rondemappen, schrijft de JSON
en snijdt de screenshot-crops uit.

Starten gaat via `ensure-bridge.sh` (zie deel 1), niet handmatig. Dat script
checkt eerst of hij al luistert, start hem anders met nohup, schrijft de pid
naar `bridge.pid` en de output naar `bridge.log` in de skill-map. Rechtstreeks
starten kan ook, voor debuggen in de voorgrond:

```bash
python3 ~/.claude/skills/html-annotator/annotator-bridge.py
```

Draait hij? `curl -s http://127.0.0.1:8791/ping` geeft
`{"ok": true, "bridge": "luc-annotator", "version": 2, ...}`. In de pagina zelf
is het te zien aan de groene statuspil ("round N - X annotaties opgeslagen"). Staat die pil
oranje op "bridge uit - alleen localStorage", dan is er niets weggeschreven;
de pagina valt dan terug op localStorage en zegt dat ook bij elke Save.

Croppen doet de bridge met headless Chrome (`--headless=new --screenshot
--window-size=<doc.w>,<doc.h>`) plus Pillow als dat geïnstalleerd is; zonder
Pillow rendert Chrome het gebied zelf via een iframe-clip. Beide routes zijn
getest. Volledige paginascreenshots worden gecached in
`$TMPDIR/luc-annotator-shots`.

Endpoints: `GET /ping`, `GET /p/<pad>`, `POST /session`, `/save`, `/delete`,
`/remove-all`, `/resolve`, `/sessie`.

`/session` geeft naast de tellingen ook de openstaande annotaties terug (nr, id,
type, rect, comment, selectedText, `stale`), zodat de pagina weet wat hij moet
tekenen.

`POST /sessie` opent een nieuwe Claude Code-sessie met een voorgeladen prompt:
geef `{"prompt": "..."}` of een kant-en-klare `{"url": "claude://code/new?q=..."}`
mee. Alleen het claude-scheme wordt geaccepteerd, zodat dit geen algemene
URL-opener wordt. Dit bestaat omdat een ingebedde browser custom schemes niet
doorgeeft; zie de skill `nieuwe-sessie`.

## Deel 3: rondes en mapstructuur

```
~/Desktop/annotaties/<pagina-slug>/
  ronde-01/
    annotations.json
    screenshots/annotatie-01.png
  ronde-02/
    ...
```

De slug komt van de bestandsnaam van de pagina (file://) of anders van de
paginatitel. Oude rondes worden nooit overschreven.

Een nieuwe ronde begint **alleen** als de lopende ronde via `POST /remove-all`
wordt afgesloten: die ronde wordt leeggemaakt en op `"closed": true` gezet, en
de volgende annotatie opent ronde+1. In de pagina zelf zit daar geen knop meer
voor. De lopende ronde is altijd de hoogste bestaande ronde die niet gesloten is.

Een gewijzigde pagina-inhoud opent **geen** nieuwe ronde meer. Pas jij de HTML
aan naar aanleiding van feedback, dan blijft de ronde staan met de annotaties die
nog niet verwerkt zijn. De `contentHash` (hash van het HTML-bestand zonder het
annotator-blok; voor niet-schijf-pagina's een DOM-hash) wordt nog wel
weggeschreven, per ronde en per annotatie, puur als context bij welke
paginaversie die feedback hoorde, plus `lastContentHash` op rondeniveau.

## Deel 4: feedback verwerken

Luc plakt een berichtje in de trant van "Kijk, hier staan de annotaties:
`<pad>/ronde-NN/annotations.json`. Het zijn er X." Lees dat bestand.

Per annotatie:

```json
{ "nr": 1, "type": "region", "target": "kop van de kaart",
  "comment": "...", "image": "screenshots/annotatie-01.png", "_rect": {...} }
{ "nr": 2, "type": "text", "target": "...", "comment": "...",
  "selectedText": "de exact geselecteerde tekst" }
```

- `type: "region"` → open `image` (pad is relatief aan de rondemap) met de
  Read-tool en lees de crop naast de comment. Zelf croppen hoeft niet meer, dat
  is al gebeurd op het moment van opslaan. `_rect` is intern, negeer het.
- `type: "text"` → gebruik `selectedText`; er is geen screenshot.
- `type: "edit"` → Luc heeft de tekst van een conceptbericht zelf herschreven. `hunks`
  geeft de wijzigingen als losse blokken, elk met de omringende tekst als anker
  (`voor`/`na`), het `alinea`-nummer om naar te verwijzen, en `verwijderd`/`toegevoegd`.
  `diff` is dezelfde informatie als platte reeks, `origineel` en `nieuw` de twee volledige
  versies. Blokken zijn los toe te passen en los af te vinken:

  ```bash
  ~/.claude/skills/html-annotator/pas-hunk-toe.py <json> --nr 1 --hunks 2 --afvinken
  ```

  Het anker is de tekst, niet de positie — een blok blijft dus plaatsbaar als de pagina
  intussen elders veranderd is. Vind je een blok niet terug, verzin dan geen plek: meld
  het en vraag. Neem `nieuw` over als de tekst van dat concept; er valt hier niets te
  interpreteren, hij heeft het al opgeschreven zoals hij het wil. Vraag alleen door als
  zijn herschrijving iets aanraakt dat elders in de pagina ook staat.
  `toon-annotaties.py` drukt dit af als een leesbare diff.
- `attachment` staat er als Luc zelf een afbeelding plakte of bijvoegde; ook
  die met de Read-tool bekijken.

**Eerst begrijpen, dan pas verwerken.** Dit is geen formaliteit: Luc dicteert
zijn annotaties vaak, waardoor zinnen soms doodlopen en context die voor hem
vanzelfsprekend is niet op papier staat. Loop ze één voor één na en leg voor wat
je niet zeker weet, in plaats van het in te vullen. Vraag door als iets te vaag
is om op te handelen, benoem het als je het er niet mee eens bent of een gevolg
ziet dat hij niet noemt, en zeg het als een punt iets tegenspreekt dat hij eerder
zei. Zitten er keuzes in, stel de vraag dan klikbaar met `AskUserQuestion`.
Twijfel je of je moet vragen: vragen. Verkeerd raden kost hem meer tijd dan een
vraag.

`toon-annotaties.py` drukt deze werkregel zelf af zodra er open annotaties zijn,
zodat hij ook meekomt in een sessie die deze skill niet gelezen heeft.

Bij veel annotaties mag je subagents inzetten (één per annotatie of per groepje)
of er stapsgewijs doorheen gaan. Verwerk punt voor punt.

Ga voor de context van een oudere ronde naar de bijbehorende `ronde-NN`-map; de
`contentHash` en `capturedAt` vertellen bij welke versie van de pagina die
feedback hoorde.

### VERPLICHT: verwerkte annotaties resolved markeren

Dit is de stap die het vaakst vergeten wordt, en precies daar loopt het mis: een
verwerkte annotatie waarvan je de vlag niet zet, verliest zijn anker (je hebt de
tekst immers aangepast), belandt in de lijst "waarschijnlijk verwerkt" en komt
elke ronde terug. Verwerken zonder afvinken is dus **niet af**.

Heb je een annotatie verwerkt in de pagina, meld hem dan direct af bij de bridge.
Hij blijft als historie in de JSON staan (met `"resolved": true` en
`"resolvedAt"`), maar verdwijnt van de pagina, zodat Luc na een refresh alleen
nog ziet wat nog open staat. Doe dit per verwerkte batch, niet pas aan het eind:

```bash
curl -s -X POST http://127.0.0.1:8791/resolve \
  -H 'Content-Type: application/json' \
  -d '{"jsonPath":"~/Desktop/annotaties/todos/ronde-09/annotations.json","nrs":[1,3,4]}'
```

Antwoord: `{"ok":true,"round":9,"resolved":[1,3,4],"notFound":[],"open":2,"total":5}`.
Check `notFound` en `open`: dat is je eigen controle dat je de goede nummers had
en hoeveel er nog openstaan.

- `nrs` zijn de annotatienummers uit die ronde; `ids` mag ook.
- `jsonPath` is het pad dat Luc je stuurde (`~` mag). Laat je het weg, dan pakt
  de bridge de lopende ronde van de pagina (`pageFile`/`page`/`slug`, net als de
  andere routes).
- Terugdraaien kan met `"resolved": false`.
- Zeg er in je antwoord bij welke nummers je hebt afgevinkt en wat er nog
  openstaat.

Positionering na een pagina-wijziging: tekstannotaties zoekt het snippet
opnieuw op via hun `selectedText`, dus die schuiven vanzelf mee. Regio-annotaties
van een oudere paginaversie worden niet op mogelijk verkeerde coördinaten
getekend, maar verschijnen in het kaartje "waarschijnlijk verwerkt" linksonder. Verwerk je
zo'n annotatie, dan verdwijnt hij daaruit zodra je hem resolved zet; Luc kan hem
daar ook zelf afvinken met het ✓.

## Deel 5: taken spawnen vanaf de todolijst

Vraagt Luc om een taak te spawnen (`spawn_task`), dan hangt die altijd aan een punt op
zijn HTML-todolijst, en het nummer van dat punt hoort in de sessietitel. De volledige
conventie staat in de skill **`task-spawnen`** — lees die voordat je spawnt; hier staat
alleen wat je moet weten om er te komen.

**Zoek de lijst, onthoud hem niet.** Het bestand verhuist en wordt hernoemd, dus nooit
een pad uit je hoofd of uit een eerder gesprek:

```bash
~/.claude/skills/html-annotator/vind-todolijst.sh        # pad
~/.claude/skills/html-annotator/vind-todolijst.sh -v     # met hoogste nummer erbij
```

Het script kiest de meest recent gewijzigde HTML op het bureaublad die genummerde punten
heeft (`<span class="num">`) én zich als todolijst laat herkennen. Vindt hij niets, dan
verzin je er geen: vraag het Luc.

Daarna, in het kort — de details en de reden erachter staan in `task-spawnen`:

1. Zoek het punt waar de taak bij hoort en pak zijn nummer. Bestaat het nog niet, maak
   het dan eerst aan op de lijst, met een nummer dat één hoger is dan het hoogste in het
   **hele** bestand (de prioriteitsbanden delen één doorlopende reeks).
2. Noem de sessie `XX.YY-kebab-case-naam`, met twee cijfers per segment.
3. Zet in de meegegeven prompt dat de gespawnde sessie zichzelf aan het eind hernoemt
   naar `[DONE]-<titel>`.

## Deel 6: de concept-berichtkaart

Een conceptbericht (mail, Teams, WhatsApp) dat nog niet verstuurd is, hoort niet
als platte tekst in de chat maar als kaart in de HTML. Dan kan Luc de tekst zien
zoals de ontvanger hem krijgt, en er met de annotator per zin op reageren.

De CSS zit in `annotator-snippet.html`, dus elke pagina met het snippet kan het
component gebruiken zonder eigen opmaak. Klassen hebben de `la-`-prefix, net als
de rest van de annotator, en zijn vlak (`la-draft-hdr` in plaats van
`.la-draft .hdr`) zodat een pagina-eigen `.hdr`, `.txt` of `.na` er niet mee
botst. `--ink` en `--muted` worden gebruikt als de pagina ze definieert, met een
fallback als dat niet zo is.

```html
<h2>Mail-concepten <span class="count">1</span></h2>
<p class="lead">Nog niet verstuurd. Annoteer gerust in de tekst zelf, dan pas ik aan.</p>

<div class="la-draft">
  <div class="la-draft-hdr"><b>Aan:</b> Anne Dijkstra &nbsp;·&nbsp; <b>Cc:</b> Marco Bonsink &nbsp;·&nbsp; <b>Onderwerp:</b> Even bijpraten over security</div>
  <div class="la-draft-txt">Hi Anne,

Eerste alinea van het bericht.

Groet,
Luc</div>
  <div class="la-draft-na">Openstaand: welk issue heb je ingeschoten? Zodra je dat zegt maak ik de eerste zin concreet.</div>
</div>
```

**Tracked changes.** Elke `la-draft-txt` is direct bewerkbaar: Luc klikt in de tekst,
de cursor staat waar hij klikte, en hij typt. Er is bewust geen knop om "de bewerkmodus
aan te zetten" — dat was een drempel voor iets wat hij gewoon wil kunnen doen. Klikt hij
eruit, dan verschijnt het verschil met de oorspronkelijke tekst als doorhaling en
onderstreping, en gaat het als annotatie van `type: "edit"` naar de bridge. Dat is vaak
sneller dan een comment: in plaats van uitleggen wat er anders moet, schrijft hij het
gewoon anders op. "↺ Herstel origineel" zet de kaart terug en verwijdert de bewerking.

Meerdere wijzigingen in dezelfde kaart worden losse blokken, genummerd in de tekst (¹ ² ³)
zodat Luc en jij hetzelfde blok bedoelen. Je kunt ze los doorvoeren en los afvinken; wat
nog openstaat blijft na een reload zichtbaar, herplaatst op zijn anker in de tekst zoals
die dan is.

Klikt hij terug in een tekst waar de opmaak zichtbaar is, dan wordt de klikpositie
omgerekend naar de kale tekst voordat de cursor gezet wordt. Zonder dat sprong de cursor,
want de doorgehaalde tekst verdwijnt bij het terugschakelen en de regel loopt dan anders.

Een bewerking krijgt bewust géén badge en komt niet in de weeslijst: hij is al zichtbaar
in de kaart zelf. Na een reload wordt hij teruggezet, gekoppeld op de kop van de kaart.
Is de concepttekst zelf gewijzigd sinds de bewerking, dan zet het snippet niets terug —
dat zou Lucs oude tekst over de nieuwe heen leggen — maar meldt het dat bij de kaart.

Regels bij het gebruik:

- De berichttekst staat letterlijk in `la-draft-txt`, met echte regelafbrekingen.
  `white-space: pre-wrap` doet de rest, dus geen `<br>` of `<p>` erin.
- `la-draft-na` is jouw notitie, niet die van de ontvanger: wat nog open staat,
  welke vraag beantwoord moet worden, of wat er gebeurt zodra het verstuurd is.
- De concepten staan bovenaan de pagina, met een lead-regel die duidelijk maakt
  dat er nog niets verstuurd is.
- Een concept in de pagina zetten is geen goedkeuring. De verzendregel uit
  CLAUDE.md en de skill `bericht-sturen` blijft onverkort gelden.

## Deel 7: geneste subpunten (`la-sub`)

Heeft een punt subtaken, dan wil Luc die visueel onder hun ouder zien hangen: hoe
dieper genest, hoe verder ingesprongen. Een platte lijst waarin de hiërarchie
alleen uit de tekst blijkt kost hem leeswerk dat de opmaak gratis kan doen.

De CSS zit in `annotator-snippet.html`, dus elke pagina met het snippet heeft het
al. Zet de klasse op het blok zelf, naast wat de pagina er verder aan geeft:

```html
<div class="card">34 · Ouderpunt</div>
<div class="card la-sub">34a · Subtaak</div>
<div class="card la-sub2">34a1 · Sub-subtaak</div>
<div class="card la-sub3">34a1a · Nog een niveau dieper</div>
```

`la-sub` = niveau 1, `la-sub2` t/m `la-sub4` = dieper. Vier niveaus omdat daaronder
de inspringing meer leesbaarheid kost dan hij oplevert; heb je toch een vijfde nodig,
dan is dat één regel bij in het snippet (`--la-diepte: 5`).

Waarom klassen en geen `data-diepte`: `attr()` is in CSS niet in `calc()` te gebruiken,
dus een attribuut vraagt evengoed één selector per niveau. Dan zijn klassen korter,
en ze sluiten aan op wat er al op de todolijst stond.

Punten om op te letten:

- De klassen hangen bewust aan niets anders dan zichzelf — geen `.card` of andere
  pagina-klasse — zodat ze op elk blok-element werken: een kaart, een `<li>`, een
  losse `<div>` in een analyse of vergelijkingspagina.
- Het snippet zet zelf `position: relative` op het element, want het haakje is een
  `::before` die daaraan hangt. Positioneer zo'n element dus niet zelf absoluut.
- De lijnkleur volgt `--line` als de pagina die definieert, met een lichte grijze
  fallback. Zo is het haakje ook zichtbaar op een pagina zonder kleurtokens.
- De inspringstap is 30px en te overschrijven met `--la-stap` op een ouder-element,
  bijvoorbeeld `20px` op een smalle pagina. Het haakje rekent mee.
- Nesting is puur visueel: de blokken blijven zussen in de HTML. Dat is bewust —
  echte nesting zou de annotator, de banden en de tellingen op de todolijst raken.
