# Agent-handbook (html-annotator)

Lees dit bestand wanneer `SKILL.md` dat vraagt — vóór opleveren van HTML met conceptkaarten/`la-sub`, en vóór het verwerken van annotaties. Dit is de voormalige SKILL.md deel 2–7. Gedrag ongewijzigd.

## Deel 2: de bridge

Een browserpagina kan zelf niet naar schijf schrijven. `annotator-bridge.py`
(stdlib only) lost dat op: hij luistert op **127.0.0.1:8791** (niet 0.0.0.0,
en niet 8080 want dat is van Docker), beheert de rondemappen, schrijft de JSON
en snijdt de screenshot-crops uit.

Starten gaat via `bin/ensure-bridge.sh` (zie deel 1), niet handmatig. Dat script
checkt eerst of hij al luistert, start hem anders met nohup, schrijft de pid
naar `bridge.pid` en de output naar `bridge.log` in de skill-map. Rechtstreeks
starten kan ook, voor debuggen in de voorgrond:

```bash
python3 ~/.claude/skills/html-annotator/bin/annotator-bridge.py
```

Draait hij? `curl -s http://127.0.0.1:8791/ping` geeft
`{"ok": true, "bridge": "luc-annotator", "version": 2, ...}`. In de pagina zelf
is het te zien aan de groene statuspil ("X saved"). Staat die pil
oranje op "bridge off - localStorage only", dan is er niets weggeschreven;
de pagina valt dan terug op localStorage en zegt dat ook bij elke Save.

Croppen doet de bridge met headless Chrome (`--headless=new --screenshot
--window-size=<doc.w>,<doc.h>`) plus Pillow als dat geïnstalleerd is; zonder
Pillow rendert Chrome het gebied zelf via een iframe-clip. Beide routes zijn
getest. Volledige paginascreenshots worden gecached in
`$TMPDIR/luc-annotator-shots`.

Endpoints: `GET /ping`, `GET /p/<pad>`, `POST /session`, `/save`, `/delete`,
`/remove-all`, `/resolve`, `/state`, `/state-save`, `/sessie`.

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

**Triggers.** Lees en verwerk openstaande annotaties zodra de reviewer een van deze
berichten stuurt (geen extra bevestiging vragen of hij het meent):

- a bare **`.`** (period only, surrounding whitespace is fine) — that is
  the short "process my annotations";
- "process my feedback", "check my saved feedback", or a path to
  `annotations.json` / an annotation round.

On a bare `.` find the open round yourself (via
`bin/toon-annotaties.py --open` or the bridge), instead of waiting for an
explicit path.

de reviewer plakt soms ook een berichtje in de trant van "Kijk, hier staan de annotaties:
`<pad>/ronde-NN/annotations.json`. Het zijn er X." Lees dat bestand.

Per annotatie:

```json
{ "nr": 1, "type": "region", "target": "kop van de kaart",
  "comment": "...", "image": "screenshots/annotatie-01.png", "_rect": {...} }
{ "nr": 2, "type": "text", "target": "...", "comment": "Maak hetzelfde als ⟦r1⟧",
  "selectedText": "de exact geselecteerde tekst",
  "locator": { "path": "#a", "start": { "path": "#a", "node": 0, "offset": 0 },
               "end": { "path": "#a", "node": 0, "offset": 27 }, "nth": 0,
               "label": "This is the first paragraph. Make me match the second one." },
  "refs": [{ "id": "r1", "selectedText": "andere tekst op de pagina" }] }
```

- `locator` (bij `type: "text"`): de plek op de pagina, niet alleen de tekst. `path`
  is het gemeenschappelijke element, `start`/`end` de exacte range, `nth` welk
  voorkomen als dezelfde tekst vaker staat, `label` de context (rij/kaart). Gebruik
  dit om te weten wélk "checken" of welke rij de reviewer bedoelde. Geen locator + tekst
  die vaker voorkomt: vraag door, kies niet de eerste hit.
- `refs` (optioneel): andere tekstfragmenten die de reviewer in de comment heeft gekoppeld.
  In `comment` staan ze als `⟦r1⟧`, `⟦r2⟧`, …; `refs` geeft per id de volledige
  `selectedText`. Gebruik dit voor "hetzelfde als …"-feedback.
- Bij verwerken: lees **`commentExpanded`** (refs ingevuld als `"tekst"`) of
  `bin/toon-annotaties.py` — die expandeert markers en waarschuwt als `refs` ontbreekt.
  Staat er `refsIncomplete`, vraag de reviewer opnieuw te saven; gok niet welke tekst r1/r2 was.
- Veelvoorkomende bedoelingen: **"Maak ⟦r1⟧ hetzelfde als ⟦r2⟧"** → pas de tekst
  van r1 (of de geannoteerde `selectedText`) aan naar r2; **"veranderen naar"** =
  vervangen door de ref-tekst. `selectedText` is het primaire anker; refs zijn
  vergelijkingstekst elders op de pagina.

- `type: "region"` → open `image` (pad is relatief aan de rondemap) met de
  Read-tool en lees de crop naast de comment. Zelf croppen hoeft niet meer, dat
  is al gebeurd op het moment van opslaan. `_rect` is intern, negeer het.
- `type: "text"` → gebruik `selectedText`; er is geen screenshot.
- `type: "edit"` → de reviewer heeft de tekst van een conceptbericht zelf herschreven. `hunks`
  geeft de wijzigingen als losse blokken, elk met de omringende tekst als anker
  (`voor`/`na`), het `alinea`-nummer om naar te verwijzen, en `verwijderd`/`toegevoegd`.
  `diff` is dezelfde informatie als platte reeks, `origineel` en `nieuw` de twee volledige
  versies. Blokken zijn los toe te passen en los af te vinken:

  ```bash
  ~/.claude/skills/html-annotator/bin/pas-hunk-toe.py <json> --nr 1 --hunks 2 --afvinken
  ```

  Het anker is de tekst, niet de positie — een blok blijft dus plaatsbaar als de pagina
  intussen elders veranderd is. Vind je een blok niet terug, verzin dan geen plek: meld
  het en vraag. Neem `nieuw` over als de tekst van dat concept; er valt hier niets te
  interpreteren, hij heeft het al opgeschreven zoals hij het wil. Vraag alleen door als
  zijn herschrijving iets aanraakt dat elders in de pagina ook staat.
  `bin/toon-annotaties.py` drukt dit af als een leesbare diff.
- `attachment` staat er als de reviewer zelf een afbeelding plakte of bijvoegde; ook
  die met de Read-tool bekijken.

**Eerst begrijpen, dan pas verwerken.** Dit is geen formaliteit: de reviewer dicteert
zijn annotaties vaak, waardoor zinnen soms doodlopen en context die voor hem
vanzelfsprekend is niet op papier staat. Loop ze één voor één na en leg voor wat
je niet zeker weet, in plaats van het in te vullen. Vraag door als iets te vaag
is om op te handelen, benoem het als je het er niet mee eens bent of een gevolg
ziet dat hij niet noemt, en zeg het als een punt iets tegenspreekt dat hij eerder
zei. Zitten er keuzes in, stel de vraag dan klikbaar met `AskUserQuestion`.
Twijfel je of je moet vragen: vragen. Verkeerd raden kost hem meer tijd dan een
vraag.

`bin/toon-annotaties.py` drukt deze werkregel zelf af zodra er open annotaties zijn,
zodat hij ook meekomt in een sessie die deze skill niet gelezen heeft.

Bij veel annotaties mag je subagents inzetten (één per annotatie of per groepje)
of er stapsgewijs doorheen gaan. Verwerk punt voor punt.

Ga voor de context van een oudere ronde naar de bijbehorende `ronde-NN`-map; de
`contentHash` en `capturedAt` vertellen bij welke versie van de pagina die
feedback hoorde.

### VERPLICHT: verwerkte annotaties resolved markeren

Dit is de stap die het vaakst vergeten wordt, en precies daar loopt het mis: een
verwerkte annotatie waarvan je de vlag niet zet, verliest zijn anker (je hebt de
tekst immers aangepast), belandt in de lijst "likely processed" en komt
elke ronde terug. Verwerken zonder afvinken is dus **niet af**.

Heb je een annotatie verwerkt in de pagina, meld hem dan direct af bij de bridge.
Hij blijft als historie in de JSON staan (met `"resolved": true` en
`"resolvedAt"`), maar verdwijnt van de pagina, zodat de reviewer na een refresh alleen
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
- `jsonPath` is het pad dat de reviewer je stuurde (`~` mag). Laat je het weg, dan pakt
  de bridge de lopende ronde van de pagina (`pageFile`/`page`/`slug`, net als de
  andere routes).
- Terugdraaien kan met `"resolved": false`.
- Zeg er in je antwoord bij welke nummers je hebt afgevinkt en wat er nog
  openstaat.

Positionering na een pagina-wijziging: tekstannotaties zoekt het snippet
opnieuw op via hun `locator` (pad, start-rij-label, daarna `selectedText` + nth).
Alleen als die tekst nergens meer op de pagina staat, verschijnt de annotatie in
het kaartje "likely processed" linksonder. Regio-annotaties van een oudere
paginaversie worden niet op mogelijk verkeerde coördinaten getekend en komen
in datzelfde kaartje. Verwerk je zo'n annotatie, dan verdwijnt hij daaruit
zodra je hem resolved zet; de reviewer kan hem daar ook zelf afvinken met het ✓.

## Deel 5: taken spawnen vanaf de todolijst

Vraagt de reviewer om een taak te spawnen (`spawn_task`), dan hangt die altijd aan een punt op
zijn HTML-todolijst, en het nummer van dat punt hoort in de sessietitel. De volledige
conventie staat in de skill **`task-spawnen`** — lees die voordat je spawnt; hier staat
alleen wat je moet weten om er te komen.

**Zoek de lijst, onthoud hem niet.** Het bestand verhuist en wordt hernoemd, dus nooit
een pad uit je hoofd of uit een eerder gesprek:

```bash
~/.claude/skills/html-annotator/bin/vind-todolijst.sh        # pad
~/.claude/skills/html-annotator/bin/vind-todolijst.sh -v     # met hoogste nummer erbij
```

Het script kiest de meest recent gewijzigde HTML op het bureaublad die genummerde punten
heeft (`<span class="num">`) én zich als todolijst laat herkennen. Vindt hij niets, dan
verzin je er geen: vraag het de reviewer.

Daarna, in het kort — de details en de reden erachter staan in `task-spawnen`:

1. Zoek het punt waar de taak bij hoort en pak zijn nummer. Bestaat het nog niet, maak
   het dan eerst aan op de lijst, met een nummer dat één hoger is dan het hoogste in het
   **hele** bestand (de prioriteitsbanden delen één doorlopende reeks).
2. Noem de sessie `XX.YY-kebab-case-naam`, met twee cijfers per segment.
3. Zet in de meegegeven prompt dat de gespawnde sessie zichzelf aan het eind hernoemt
   naar `[DONE]-<titel>`.

## Deel 6: de concept-berichtkaart

Een conceptbericht (mail, Teams, WhatsApp) dat nog niet verstuurd is, hoort niet
als platte tekst in de chat maar als kaart in de HTML. Dan kan de reviewer de tekst zien
zoals de ontvanger hem krijgt, en er met de annotator per zin op reageren.

De CSS zit in `references/annotator-snippet.html`, dus elke pagina met het snippet kan het
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
  <div class="la-draft-txt">
    <p>Hi Anne,</p>
    <p>Eerste alinea van het bericht.</p>
    <ul>
      <li>Anne: schiet het issue in bij <a href="https://…/pbi/1234">PBI 1234</a></li>
      <li>Ik: stuur de opzet door</li>
    </ul>
    <p>Groet,<br>de reviewer</p>
  </div>
  <div class="la-draft-na">Openstaand: welk issue heb je ingeschoten? Zodra je dat zegt maak ik de eerste zin concreet.</div>
</div>
```

**Rich text.** De kaart toont het bericht zoals de ontvanger het krijgt: alinea's,
opsommingen, vet, cursief en links. Het toegestane setje is klein en mail-veilig —
`p`, `ul`, `ol`, `li`, `b`, `i`, `a`, `br` — precies de doorsnede die Outlook, Gmail en
Teams zonder eigen interpretatie renderen. Wat je er verder in zet wordt bij het inlezen
platgeslagen tot tekst; plakken gaat altijd als platte tekst. Er is geen bibliotheek en
geen CDN in het spel: het snippet blijft één bestand.

De reviewer heeft onder elke kaart een balkje met **B**, *I*, link, • en 1. (en ⌘B / ⌘I /
⌘K). Een kaart die je als platte tekst schreef blijft platte tekst — pre-wrap,
`plaintext-only` — tot hij zelf een opmaakknop gebruikt; dan gaat de héle kaart in één
keer over op blokken. Half omschakelen zou de overgebleven harde regelovergangen op één
hoop gooien.

**Tracked changes.** Elke `la-draft-txt` is direct bewerkbaar: de reviewer klikt in de tekst,
de cursor staat waar hij klikte, en hij typt. Er is bewust geen knop om "de bewerkmodus
aan te zetten" — dat was een drempel voor iets wat hij gewoon wil kunnen doen. Klikt hij
eruit, dan verschijnt het verschil met de oorspronkelijke tekst als doorhaling en
onderstreping — in de opgemaakte kaart, dus een gewijzigde bullet blijft een bullet — en
gaat het als annotatie van `type: "edit"` naar de bridge. Dat is vaak sneller dan een
comment: in plaats van uitleggen wat er anders moet, schrijft hij het gewoon anders op.
"↺ Herstel origineel" zet de kaart terug en verwijdert de bewerking.

Er wordt **niet op de HTML gedift maar op de platte-tekstprojectie** ervan: precies de
tekst die in een plain-text mail zou staan, zonder opmaakmarkeringen erin. Opmaak is een
eigen kanaal. Dat levert twee soorten blokken op:

- `soort: "tekst"` — de vertrouwde hunk met `voor` / `na` / `verwijderd` / `toegevoegd`.
  Het anker blijft binnen zijn eigen blok, want tussen twee blokken staat in de bron een
  tag. `pas-hunk-toe.py` plaatst deze blokken gewoon.
- `soort: "opmaak"` — "alinea werd opsomming", `vet aan op "issue"`. Die staan per
  definitie niet in de tekst, dus `pas-hunk-toe.py` raakt ze niet aan en zegt dat ook:
  die neem je over uit `nieuwHtml`.

Wijzigden tekst én opmaak in hetzelfde blok, dan zie je alleen het tekstblok.
`nieuwHtml` op de annotatie is dan de grondwaarheid: dat is de volledige nieuwe versie,
mail-veilig, klaar om als body te gebruiken.

Meerdere wijzigingen in dezelfde kaart worden losse blokken, genummerd in de tekst (¹ ² ³)
zodat de reviewer en jij hetzelfde blok bedoelen. Je kunt ze los doorvoeren en los afvinken; wat
nog openstaat blijft na een reload zichtbaar, herplaatst op zijn anker in de tekst zoals
die dan is.

Klikt hij terug in een tekst waar de opmaak zichtbaar is, dan wordt de klikpositie
omgerekend naar de kale tekst voordat de cursor gezet wordt. Zonder dat sprong de cursor,
want de doorgehaalde tekst verdwijnt bij het terugschakelen en de regel loopt dan anders.

Een bewerking krijgt bewust géén badge en komt niet in de weeslijst: hij is al zichtbaar
in de kaart zelf. Na een reload wordt hij teruggezet, gekoppeld op de kop van de kaart.
Is de concepttekst zelf ongewijzigd, dan komt de bewerkte versie compleet terug, opmaak
incluis. Is de tekst wél veranderd sinds de bewerking, dan worden alleen de openstaande
blokken op hun anker herplaatst en meldt het snippet wat het niet meer terugvond.

Regels bij het gebruik:

- Schrijf de berichttekst in blokken: `<p>` per alinea, `<ul>`/`<ol>` met `<li>` voor
  opsommingen, `<br>` voor een harde regelovergang binnen een alinea. Alleen die tags,
  plus `<b>`, `<i>` en `<a href>`. Geen `style`, geen `<div>`, geen tabellen.
- Streepjes-als-bullet (`- Anne: …` als gewone tekstregel) zijn geen opsomming meer.
  Wil je een opsomming, schrijf er dan één.
- Kortere kaarten mogen nog steeds platte tekst zijn: laat je de blokken weg, dan
  gedraagt de kaart zich als voorheen (echte regelafbrekingen, `white-space: pre-wrap`,
  geen `<br>` of `<p>`). Bedoel je opmaak, gebruik dan blokken — niet allebei door elkaar.
- `la-draft-na` is jouw notitie, niet die van de ontvanger: wat nog open staat,
  welke vraag beantwoord moet worden, of wat er gebeurt zodra het verstuurd is.
- De concepten staan bovenaan de pagina, met een lead-regel die duidelijk maakt
  dat er nog niets verstuurd is.
- Een concept in de pagina zetten is geen goedkeuring. De verzendregel uit
  CLAUDE.md en de skill `bericht-sturen` blijft onverkort gelden.

## Deel 7: geneste subpunten (`la-sub`)

Heeft een punt subtaken, dan wil de reviewer die visueel onder hun ouder zien hangen: hoe
dieper genest, hoe verder ingesprongen. Een platte lijst waarin de hiërarchie
alleen uit de tekst blijkt kost hem leeswerk dat de opmaak gratis kan doen.

De CSS zit in `references/annotator-snippet.html`, dus elke pagina met het snippet heeft het
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

## Deel 8: het checklist-component (LA-CHECKLIST)

Voor elke HTML met afvinkbare items of rijen (todolijsten, testcase-tabellen,
reviewrijen). Het component is een los blok, `<!-- LA-CHECKLIST v1` t/m
`<!-- /LA-CHECKLIST -->`, canoniek in `references/checklist-snippet.html`.
Self-contained, geen dependencies, net als het annotator-snippet.

**Inbouwen:**

1. Plak het volledige blok uit `references/checklist-snippet.html` vlak vóór
   het LUC-ANNOTATOR-blok.
2. Zet `data-la-check="<unieke-key>"` op elk afvinkbaar element. De key is het
   blijvende anker in de state — kies iets stabiels (bv. het itemnummer,
   `"#74"`), geen volgnummer dat verschuift.
3. Optioneel `data-la-label="..."` voor een expliciet label; anders pakt het
   script de tekst van `.what` of van het element zelf (max 140 tekens).

Het script injecteert een Notion-stijl checkbox — in `.la-check-slot` als die
er is, anders in de eerste `summary`, anders vooraan het element — laadt de
opgeslagen state bij page load via `POST /state`, en schrijft elke wijziging
via `POST /state-save` met `{component:"checklist", key, value:{checked,
label}}`. Een aangevinkt element krijgt de class `la-checked` (titel
doorgestreept en gedimd; de CSS mikt op `.what`, ook binnen een `summary`).

**State, los van de rondes.** De vinkjes zijn blijvende status, geen
feedbackronde: ze leven per pagina in `~/Desktop/annotaties/<slug>/state.json`,
naast de `ronde-NN`-mappen. Formaat:

```json
{ "components": { "checklist": {
    "#74": { "checked": true, "label": "…", "changedAt": "2026-08-28T…" } } },
  "updatedAt": "2026-08-28T…" }
```

**Uitlezen als agent:** lees `state.json` direct, of vraag het de bridge met
`POST /state` en `{"page": "..."}` (of `pageFile`/`slug`, zoals de andere
routes). Gebruik `changedAt` per key en `updatedAt` op het geheel om te zien
wat er sinds de vorige keer veranderd is — analoog aan hoe je
`annotations.json` leest. Er valt niets te resolven: een vinkje ís de status.

`/state-save` merget de meegegeven `value` over de bestaande entry en zet
`changedAt`; andere componenten dan `checklist` kunnen dezelfde twee routes
gebruiken met een eigen `component`-naam.
