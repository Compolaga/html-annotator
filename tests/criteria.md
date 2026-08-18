# Acceptatiecriteria: bridge draait, annotaties landen op schijf

Vastgelegd 2026-08-18, vóór de implementatie. Bron: Luc, deze sessie.

Wat moet gelden: **Luc verliest nooit een annotatie.** Alle criteria hieronder zijn
uitwerkingen daarvan. De statuspil is een proxy; het bewijs ligt in
`~/Desktop/annotaties/<slug>/ronde-NN/annotations.json`.

## Over de rondes in `tests/red/`

De bestandsnamen lopen van ronde 1 tot 10; ronde 9 is er niet. Die is vervangen door
ronde 10 na een label-only wijziging in de testoutput (de twee `file`-regels waren niet
van elkaar te onderscheiden), zonder inhoudelijke verandering. Ronde 5 en 7 zijn
tussenstanden van dezelfde groene suite.

## Non-goals

- **De sideviewer wordt niet verboden.** Luc stelde (deze sessie, 18:37) dat sideviewer
  plus bridge samen werken zodra de bridge draait, en dat hij er alleen een na-zwengel
  aan moest geven. Op die basis is deze suite gebouwd. **De meting onder AC-4 (22:17)
  weerlegt dat**: de sideviewer draait op een `data:`-origin en kan de bridge nooit
  bereiken. De tweede meting (22:21) laat zien dat het wél werkt zodra dezelfde pagina via
  `/p/` geladen wordt. De non-goal houdt dus stand, met een scherpere formulering: de
  sideviewer mag blijven, maar alleen via de bridge-URL — een bestand openen werkt daar
  principieel niet.
- Geen cloud-VM. Claude Desktop is een macOS-GUI-app; een Linux-sandbox kan hem niet
  draaien en niet als Luc inloggen.
- Geen garantie over modelgedrag. Dat een verse agent het snippet correct inplakt en
  achteraf resolved zet is een eval-vraag, geen test-vraag, en valt buiten deze suite.

## AC-1 — Zelfherstel zonder reload

**Gegeven** een pagina met het snippet die al open staat terwijl de bridge niet draait,
**wanneer** de bridge daarna omhoog komt,
**dan** slaat de statuspil binnen 10 seconden om naar `round N - X annotaties opgeslagen`
zonder dat de pagina herladen wordt, **en** landt een annotatie die daarna wordt
opgeslagen daadwerkelijk in `annotations.json` op schijf.

Dit is de na-zwengel. Faalt nu: `verversSessie()` wordt één keer aangeroepen
(`annotator-snippet.html`, einde van het script), zonder retry.

Uitkomst: rood aangetoond (`red/ronde-1-case02-03.txt`, snippet `841914d16650`), groen na
de poller (`red/ronde-5-groen-02-03-04.txt`, snippet `0479237cce6a`).

Mutatie over de fix zelf (`red/ronde-6-mutaties.txt`), omdat "rood voor, groen na" niet
zegt wélk deel van het zelfherstel dragend is:

- timer eruit → geen herstel. De timer doet het werk, niet de focus-listeners. Dat is de
  uitkomst die telt: focus-events vuren nooit in een sideview-paneel waar Luc niet in
  klikt, dus de fix helpt daar echt.
- listeners eruit → herstel blijft werken. **Niet lezen als "listeners zijn overbodig".**
  Chrome throttelt `setInterval` in een verborgen tab naar ~1×/minuut en de timer slaat
  een verborgen pagina bewust over; dan is `visibilitychange` wat direct bijwerkt. Deze
  case draait met een zichtbare pagina en is blind voor dat scenario; de
  verborgen-variant hieronder dekt het deels af.
- alles eruit → geen herstel, wat aantoont dat de assertie meet wat hij beweert te meten.

Verborgen-paneel-variant (`CASE02_VERBORGEN=1`, `red/ronde-8-verborgen-paneel.txt`), omdat
Luc's paneel er staat terwijl hij in de chat typt en de timer een verborgen pagina bewust
overslaat: pagina blijft correct op "bridge uit" zolang hij verborgen is, en komt bij
zodra hij weer bekeken wordt. `geen-poller` wordt daar betrapt. Wat deze variant **niet**
doet: de timer en de listeners van elkaar scheiden — zodra de pagina weer zichtbaar is
mag de timer ook vuren, en met de listeners eruit herstelde hij alsnog. De variant bewijst
dus dát het paneel bijkomt, niet welke regel dat deed. En de verborgen staat is
geëmuleerd (`document.hidden` overschreven), want Chrome levert via Playwright geen echte
achtergrondtab; Chrome's throttling van timers in echte achtergrondtabs blijft daarmee
ongetoetst.

Bijkomende meting, niet voorzien toen dit criterium geschreven werd: op `file://` landde
de annotatie al op schijf terwijl de pil "bridge uit" meldde. De pil loog daar dus, en
het snippet waarschuwde Luc onterecht dat er niets bewaard was. Met de poller lopen pil
en werkelijkheid weer gelijk.

## AC-2a — Bridge komt omhoog los van de schrijfroute

**Gegeven** de hook-registratie in `~/.claude/settings*.json`,
**dan** bestaat er een route die de bridge omhoog brengt zonder af te hangen van hóe de
agent het bestand wegschrijft, **en** brengt die route de bridge daadwerkelijk omhoog,
**en** blijft de bestaande `Edit|Write`-route werken.

Dit is het deterministische deel van AC-2: geen model, geen k/n, geen kosten. De reden
dat het bestaat is dat de PostToolUse-hook aan `Edit|Write` hing, terwijl auto-mode
agents juist naar Bash stuurt — die route triggerde de hook nooit.

Uitkomst: rood aangetoond (hook `73d62cdf69ef`), groen na een SessionStart-registratie
plus een SessionStart-tak in `hook-ensure-bridge.sh` (hook `ed2fd46ae9e2`).

Niet gekozen: de matcher verbreden naar `Bash`. Dat vuurt op élke Bash-call in élk
project, terwijl SessionStart één aanroep per sessie is en álle schrijfroutes dekt.

## AC-2b — Verse agent levert een pagina op met draaiende bridge

**Gegeven** een verse Claude Code-sessie zonder context van deze sessie, en een bridge
die aantoonbaar niet draait,
**wanneer** die agent gevraagd wordt een HTML-pagina voor Luc te maken en het bestand
via Bash wegschrijft (heredoc, niet de Write-tool),
**dan** draait de bridge na afloop, **en** is dat een nieuw proces (andere pid dan
vóór de run), **en** bevat de opgeleverde HTML de `LUC-ANNOTATOR`-marker.

De pid-eis staat er omdat "ping antwoordt" ook waar is als de bridge al draaide: dan
zou de test om de verkeerde reden slagen.

Flaky gedrag: dit is agent-gedrag, dus de uitslag is k/n. Drempel vooraf vastgelegd:
**alle runs moeten slagen**. Eén faalronde is een bevinding, geen ruis.

Uitkomst: **nog niet geverifieerd.** `claude -p` weigert met "You've hit your monthly
spend limit" (`red/ronde-4-case01.txt`), dus de case kon niet draaien. De runner meldt
dat als BLOKKED en zet de suite rood — een case die niets deed mag nooit als pass
lezen. Dit blijft openstaan tot het budget het toelaat; AC-2a dekt het
mechanisme-deel intussen deterministisch.

## AC-3 — `ensure-bridge.sh` liegt niet

**Gegeven** een bezette poort 8791 waarop geen annotator-bridge luistert (of een
stale `bridge.pid`),
**wanneer** `ensure-bridge.sh` draait,
**dan** eindigt het script óf met een draaiende, antwoordende bridge, óf met een
niet-nul exitcode — nooit met exitcode 0 terwijl `/ping` niets teruggeeft.

Aanleiding: `bridge.log` bevat vier `OSError: [Errno 48] Address already in use`
tracebacks terwijl `bridge-hook.log` op dezelfde momenten "bridge gestart" meldt.

Uitkomst: **dit criterium hield al.** `ensure-bridge.sh` eindigt met exit 1 zodra `/ping`
stil blijft. De tracebacks zijn een onschuldige race tussen twee gelijktijdige
hook-aanroepen die beide starten; de verliezer crasht op de bezette poort, de winnaar
luistert, en beide melden terecht succes. De verdenking van een liegend script was
onjuist; de test blijft staan als regressievangnet.

## AC-4 — De echte origin van de sideviewer is bekend

**Gegeven** een pagina die in de Claude Desktop-sideviewer geopend wordt terwijl de
bridge draait,
**dan** staat in `bridge.log` welke `Origin`/`Referer` die verzoeken hebben.

Dit is geen gedragscriterium maar een meting: zonder die waarde blijft elke uitspraak
over de sideviewer een aanname. Vereist één handmatige actie van Luc en is daarom
geen onderdeel van de geautomatiseerde suite.

Uitvoeren — één commando, de rest doet het script:

```bash
~/.claude/skills/html-annotator/tests/sideview-test.sh
```

Het bouwt de probe op `~/Desktop/sideview-probe.html`, haalt de bridge omlaag, geeft Luc
45 seconden om die pagina in de sideviewer te openen, brengt de bridge daarna omhoog en
drukt af wat de pagina over zichzelf meldde: origin, protocol, of loopback bereikbaar was,
en of de pil vanzelf omsloeg. De probe stuurt dat als queryparameter op `/ping`, zodat het
in `bridge.log` landt zonder dat de bridge een endpoint nodig heeft, én toont het op het
scherm voor het geval loopback juist geblokkeerd is — dan is de stilte in het log het
antwoord en staat de reden op de pagina.

**Uitkomst, gemeten 2026-08-18 22:17.** De sideviewer serveert de pagina als
`data:text/html;charset=utf-8,...` — `protocol: "data:"`, `origin: "null"`,
`isSecureContext: false`, runtime `Claude/1.32352.1 Chrome/148 Electron/42.9.2`. De
bridge is daar niet bereikbaar: `fetch` faalt met "Failed to fetch", er kwam niets in
`bridge.log`, en de pagina herstelde zich niet toen de bridge omhoog kwam
(`zelfherstel: false` na 15s).

**Tweede meting, 22:21 — en die draait de conclusie om.** Dezelfde sideviewer, dezelfde
Electron-runtime, maar de pagina geladen via `http://127.0.0.1:8791/p/Desktop/...`:
`origin: "http://127.0.0.1:8791"`, `isSecureContext: true`, loopback bereikbaar, pil
groen binnen 1 seconde, `zelfherstel: true`.

De sideviewer is dus niet het probleem — de **manier van openen** is het. Een bestand
openen levert een `data:`-snapshot die nooit kan opslaan; hetzelfde bestand via `/p/`
openen werkt volledig, inclusief zelfherstel. Dat maakt de regel "open altijd via
`/p/<pad-vanaf-home>`" uit SKILL.md geen advies meer maar de enige werkende route, nu
gemeten op het echte oppervlak in plaats van afgeleid.

Wat blijft staan: als een pagina tóch als bestand in de sideviewer belandt, meldt de
statuspil "bridge uit - alleen localStorage". Dat leest als "de bridge moet even
aangezwengeld worden" terwijl er niets aan te zwengelen valt — die misleiding startte dit
onderzoek, en is een openstaand verbeterpunt voor het snippet.

Losse origins nakijken kan ook:

```bash
grep -o 'origin=[^ ]*' ~/.claude/skills/html-annotator/bridge.log | sort -u
```

De logging die dit mogelijk maakt zit in `annotator-bridge.py` en blijft permanent aan;
dat viel buiten de oorspronkelijke scope en is nadien door Luc bekrachtigd (18-08-2026).

## AC-5 — Bewerkingen op een conceptbericht komen als diff op schijf

**Gegeven** een pagina met een conceptkaart (`la-draft-txt`),
**wanneer** Luc de tekst daarin herschrijft en de bewerking afsluit,
**dan** toont de kaart het verschil als doorhaling en onderstreping, **en** staat er een
annotatie van `type: "edit"` op schijf met `origineel`, `nieuw` en een `diff` die alleen
het gewijzigde deel aanwijst, **en** overleeft die weergave een reload.

Waarom dit bestaat: een comment naast de tekst dwingt Luc uit te leggen wat er anders
moet, terwijl het vaak sneller is om het gewoon anders op te schrijven. Dan hoeft er ook
niets vertaald te worden van bedoeling naar tekst.

Uitkomst: rood aangetoond en groen gemaakt in drie rondes
(`red/ronde-11-case05.txt`). Wat de rondes opleverden:

- de bewerkvelden vielen weg in de payload naar de bridge én in het antwoord terug — twee
  aparte plekken met een vaste veldenlijst, waardoor de opslag leeg was terwijl de pagina
  klopte;
- de eerste assertie toetste of meer dan de helft van de tekst onveranderd bleef. Bij het
  herschrijven van een hele zin klopt dat niet, en de assertie is vervangen door een
  scherpere: aanhef en afsluiting moeten aantoonbaar als onveranderd in de diff staan;
- de browsercheck vond wat de test niet zag: een bewerking belandde als ankerloze
  annotatie in de weeslijst en stond daar als "waarschijnlijk verwerkt" terwijl er niets
  aan de hand was. Daar staat nu een eigen assertie op.

## Wat de suite niet toetst

De echte Claude Desktop-sideviewer. AC-1 wordt getoetst in systeem-Chrome over twee
origins (`file://` en een `data:`-snapshot). Dat is een benadering: Electron heeft
eigen CSP en flags. De runner drukt dit als SKIPPED af, zodat groen niet als volledige
dekking leest.
