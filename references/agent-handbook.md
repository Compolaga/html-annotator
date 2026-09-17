# Agent-handbook (html-annotator)

Lees dit bestand wanneer `SKILL.md` dat vraagt — vóór het opleveren van HTML en vóór het verwerken van annotaties. Delen 1 (inplakken) staat in `SKILL.md`; wat hier stond over taken spawnen, conceptkaarten en `la-sub` is verhuisd naar `extras/agent-handbook-extras.md` (zie `docs/SCOPE.md`).

## Deel 2: de bridge

Een browserpagina kan zelf niet naar schijf schrijven. `annotator-bridge.py`
(stdlib only) lost dat op: hij luistert op **127.0.0.1:8791** (niet 0.0.0.0,
en niet 8080 want dat is van Docker), beheert de rondemappen, schrijft de JSON
en snijdt de screenshot-crops uit.

Starten gaat via `python -m html_annotator ensure` (zie deel 1), niet
handmatig. Dat commando checkt eerst of hij al luistert, start hem anders
losgekoppeld van je shell, en schrijft pid en log naar een state-map per
gebruiker (`~/.local/state/html-annotator`, op Windows `%LOCALAPPDATA%`).
Op de voorgrond draaien kan ook, om te debuggen:

```bash
python -m html_annotator serve
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

Endpoints: `GET /ping`, `GET /p/<pad-vanaf-home>` (forward slashes in de URL, ook op Windows), `POST /session`, `/save`, `/delete`,
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
<annotatie-root>/<pagina-slug>/
  ronde-01/
    annotations.json
    screenshots/annotatie-01.png
  ronde-02/
    ...
```

De annotatie-root is `~/annotations` (of `HTML_ANNOTATOR_ROOT`; op een machine
die de oude map `annotaties` op het bureaublad al gebruikt, blijft die staan). De slug komt van de
bestandsnaam van de pagina (file://) of anders van de paginatitel, en is op elk
besturingssysteem een geldige mapnaam. Oude rondes worden nooit overschreven.

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
`python -m html_annotator show --open` or the bridge), instead of waiting for an
explicit path. Check on the same trigger whether the page's `state.json`
holds unprocessed LA-SUGGEST decisions (component `suggest`, deel 6) — the
reviewer uses one `.` for both channels.

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
  `python -m html_annotator show` — die expandeert markers en waarschuwt als `refs` ontbreekt.
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
  python -m html_annotator apply-hunk <json> --nr 1 --hunks 2 --resolve
  ```

  Het anker is de tekst, niet de positie — een blok blijft dus plaatsbaar als de pagina
  intussen elders veranderd is. Vind je een blok niet terug, verzin dan geen plek: meld
  het en vraag. Neem `nieuw` over als de tekst van dat concept; er valt hier niets te
  interpreteren, hij heeft het al opgeschreven zoals hij het wil. Vraag alleen door als
  zijn herschrijving iets aanraakt dat elders in de pagina ook staat.
  `python -m html_annotator show` drukt dit af als een leesbare diff.
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

`python -m html_annotator show` drukt deze werkregel zelf af zodra er open annotaties zijn,
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
  -d '{"jsonPath":"~/annotations/todos/ronde-09/annotations.json","nrs":[1,3,4]}'
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

## Deel 5: het checklist-component (LA-CHECKLIST)

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
feedbackronde: ze leven per pagina in `<annotatie-root>/<slug>/state.json`,
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

## Deel 6: voorgestelde wijzigingen (LA-SUGGEST-laag)

Voor wijzigingen die jij als agent in een bestaande HTML aanbrengt en die de
reviewer per stuk wil kunnen accepteren of terugdraaien — zoals suggested
changes in code. Sinds v5 is dit **geen apart snippet meer**: de laag zit in
het gewone annotator-snippet en activeert zichzelf zodra er elementen met
`data-la-suggest` op de pagina staan. Een pagina met het LUC-ANNOTATOR-blok
heeft dus alles al; `references/suggest-snippet.html` is vervallen.

**Markeren (bij het maken van de wijziging):** zet op elk gewijzigd element

- `data-la-suggest="<unieke-key>"` — stabiele key (bv. `"wi-29119"`), verplicht;
- `data-la-suggest-desc="..."` — één zin die zegt wát je veranderd hebt; dit
  wordt het quote-blok in de popup;
- `data-la-suggest-old="..."` — de oorspronkelijke tekst, zodat een afwijzing
  exact terug te draaien is. Verplicht bij `kind="edit"`;
- `data-la-suggest-kind` — `"edit"` (default), `"add"` (nieuw; afwijzen =
  weghalen), `"del"` (voorstel tot verwijderen; afwijzen = laten staan);
- `data-la-suggest-mode` — meestal weglaten: tekst krijgt vanzelf
  tekstregel-selecties en visuals (`figure`/`svg`/`img`/`canvas`/`video`/
  `table`, of iets dat die bevat) één regiokader. Zet hem alleen expliciet
  (`"text"` of `"region"`) als die autodetectie verkeerd kiest.

**Eén key = één suggestie = één pill.** De beslissing wordt per key opgeslagen,
dus zet dezelfde `data-la-suggest` alleen op meerdere elementen als het écht
één beslissing is. Doe je dat, dan tekent de laag alle rects van die elementen
als één visuele groep met precies één pill erbij — wat je ziet is dan wat er
gebeurt. Wil de reviewer per rij kunnen beslissen (een work-item-rij met zijn
subtaakrijen bijvoorbeeld), geef elke rij dan een eigen key: parent `wi-<id>`,
subtaken `wi-<parentid>-<subid>`, elk met een eigen `data-la-suggest-desc`.
(Tot 31-08-2026 tekende de laag per element een pill op een gedeelde key: vijf
knoppen die stiekem samen één beslissing waren.)

**Verborgen bij het laden mag.** Suggesties in een ingeklapte tabelgroep, achter
een filter of in later ingevoegde DOM krijgen hun pill zodra ze zichtbaar
worden: de laag hertekent op DOM- en zichtbaarheidswijzigingen. Je hoeft dus
niets extra's te doen om inklapbare secties te ondersteunen. Wat de laag daarvoor
ziet: DOM die erbij komt of weggaat, en de attributen `class`, `style`,
`hidden` en `open`. Klapt jouw pagina puur in CSS in of uit (een
`input:checked ~ tabel`-truc, of een stylesheet die wisselt), dan verandert er
geen attribuut en blijft de pill weg — laat zo'n toggle dan ook een class of
een style zetten.

**Wat de reviewer ziet:** exact de annotatie-mechaniek. Elke suggestie krijgt
de vertrouwde selectie-rects (blauw) over de gewijzigde tekst, met aan het
einde de badge breed uitgetrokken tot een pill met de drie acties erin:
**✕ afwijzen · ✓ accepteren · ✎ anders**. Bij ✎ opent de gewone
annotator-popup, met het voorstel als quote en het volledige commentveld
(inclusief tekst-chips via het kettingicoon); Save = "anders, namelijk zó".
Na een beslissing krimpt de pill tot één gekleurd badge (groen ✓ / rood ✕ /
oranje ✎); daarop klikken draait de keuze terug naar pending. Bij een
change-beslissing blijft de getypte tekst daarbij bewaard: kiest de reviewer
opnieuw ✎, dan staat zijn eigen zin (chips incluis) weer in de popup en kan
hij hem bijschaven in plaats van overtypen. Dat werkt ook na een reload — de
voorvulling komt uit de geladen state, niet uit een variabele. Accepteren of
afwijzen laat de tekst juist vallen, zodat jij geen dode change-comment op
een accepted key vindt.

**State.** Beslissingen zijn blijvende status, geen feedbackronde: ze staan in
`<annotatie-root>/<slug>/state.json` onder component `suggest`
(`POST /state-save`), met per key `decision` (`"accepted"`, `"rejected"`,
`"change"`, `"pending"`), `comment`, en bij chips ook `refs` (id +
selectedText + locator) en `commentExpanded` (chips inline uitgeschreven).

**Verwerken als agent.** Zelfde triggers als annotaties (kale `.`, "verwerk").
Lees de state (`state.json` of `POST /state`) en handel per key af:

- `accepted` → de wijziging blijft. Haal de `data-la-suggest*`-attributen weg.
- `rejected` → draai exact terug: bij `kind="edit"` zet je
  `data-la-suggest-old` terug, bij `"add"` verwijder je het element, bij
  `"del"` laat je het staan. Daarna de attributen weghalen.
- `change` → voer `commentExpanded` uit; gebruik `refs[].locator` als de
  bedoelde tekst vaker op de pagina staat. Onduidelijk: vragen, niet gokken.
- `pending` of geen entry → laten staan. Een pending entry kan nog een
  `comment` dragen (tekst van een teruggeklikte change): dat is een concept
  van de reviewer, geen opdracht — niet uitvoeren.

Meld elke afgehandelde key af met `POST /state-save` en
`{"component":"suggest","key":"...","value":{"processed":true}}` — de laag
slaat entries met `processed` over bij het herladen. Zeg in je antwoord wat
je geaccepteerd gelaten, teruggedraaid en gewijzigd hebt.

Een LA-SUGGEST-beslissing is status (zoals een vinkje), géén annotatie: hij
komt niet in `annotations.json` en hoeft niet via `/resolve`. Gewone
annotaties op dezelfde pagina blijven gewoon werken.
