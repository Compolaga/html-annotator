# Decisions

Choices a later cleanup must not reopen without the owner.
Changing behaviour is a new decision, not an edit here.

## 2026-08-18 — SessionStart hook always on

The bridge hook runs at user level on every agent session (empty
matcher). PostToolUse stays limited to `Edit|Write` on HTML with
`LUC-ANNOTATOR`. Do not narrow it: the bridge should be listening.

## 2026-08-18 — Pages via `/p/`, not `file://` or a preview pane

A `data:` origin cannot reach loopback (Private Network Access).
Deliver as `http://127.0.0.1:8791/p/<path-from-home>`.

## 2026-08-18 — Origin log stays on

Every bridge request logs `origin=` to stderr / `bridge.log`.

## 2026-08-23 — No Remove-all in the UI

`POST /remove-all` still exists. The button is gone. Rounds close only
through that endpoint, not through a page change.

## 2026-08-23 — English UI copy, status pill `X saved`

User-visible annotator strings are English. The pill shows the number
of open annotations, without a `round N -` prefix.

## 2026-08-23 — Paste block stays one file

`references/annotator-snippet.html` is the only thing that goes at the
bottom of HTML. No bundler, no split runtime JS until the output is
byte-identical.

## 2026-08-23 — Install without personal memories

`install.sh` does not install memories. Agent rules live in `SKILL.md`
and `references/`. Existing project `MEMORY.md` rules are not deleted.
`extras/luc-memories/` was removed (the plan said move). Source: this
cleanup, "it may change drastically". Content remains in git at
`472cf63`.

## 2026-08-23 — Locator follows the row, not the first repeated span

`zoekAnker` no longer treats "start span still exists" as processed.
The label comes from the start row; `zoekHostViaLabel` / `laHostPast`
keep repeated cell text on that row. Source: Reconi owners, 2026-08-23.
No Reconi page in the suite — case-08 is the reduced form.

## 2026-08-23 — Root is a port, CLIs in bin/

CLIs and hooks live in `bin/`. Python library in `annotator/`
(snake_case). `ensure-bridge.sh` and `hook-ensure-bridge.sh` are
location-relative. Agent-facing docs name no person;
`window.LucAnnotator` and the `LUC-ANNOTATOR` marker stay (public API).

## 2026-08-23 — Criteria at root, decisions in docs

`CRITERIA.md` is the contract (criterion, expected behaviour, evidence).
Dated lab notes live in `tests/red/`. Binding choices live in this file.

## 2026-08-23 — English on ports, Dutch handbook until a dedicated pass

Root ports a stranger opens first — `SKILL.md`, `README.md`,
`INSTALL.md`, `CRITERIA.md`, `install.sh` — are English (A8).
`references/agent-handbook.md` and the work-rule block printed by
`bin/toon-annotaties.py` stay Dutch until a dedicated translation.
CLI filenames (`toon-annotaties.py`, `vind-todolijst.sh`,
`pas-hunk-toe.py`) stay: they are the same class of identifier as
`LUC_ANNOTATOR_*`. `annotator/` stays an importable package;
`install.sh` stays at root; `INSTALL.md` stays a port, not a file
in `bin/`.

## 2026-08-28 — Draft cards are rich text; the diff stays on the plain-text projection

`.la-draft-txt` renders as the recipient will see it: paragraphs, bulleted
and numbered lists, bold, italic and links. The allowed set is exactly
`p, ul, ol, li, b, i, a, br` — the intersection Outlook, Gmail and Teams
render without interpreting anything of their own. Reading the card back
into the block model *is* the sanitizer: anything else is flattened to
text, and paste is always plain text.

The tracked changes did **not** move to HTML. Two channels:

- **text** — diffed word-level on the plain-text projection of the card:
  the exact text a plain-text mail would carry, with no formatting
  sigils (`- `, `**`) in it. Hunks keep their shape
  (`voor/na/verwijderd/toegevoegd`), so anchoring, reload replay and
  `pas-hunk-toe.py` keep working unchanged.
- **formatting** — its own hunks, `soort: "opmaak"`, saying what happened
  to a block ("alinea werd opsomming", `vet aan op "issue"`).

Why not sigils in the projection: a reviewer types `- ` himself, so a
sigil cannot be told apart from content, and it would push every
formatting change through the word diff as noise. Why not diff the HTML:
the anchors would stop being findable in the page source.

Consequences accepted:

- A text hunk's anchor is clamped to its own block, because in the source
  a block boundary is a tag. An anchor that still runs through inline
  markup (`<b>`, `<a>`) is reported as MISLUKT by `pas-hunk-toe.py`
  rather than placed — never a silent wrong edit.
- `pas-hunk-toe.py` does not apply formatting hunks; it names them and
  points at `nieuwHtml`.
- A block whose text *and* formatting changed reports only the text hunk.
  `nieuwHtml` on the annotation is the complete new version and is the
  ground truth in that case.
- A card the agent wrote as plain text stays plain text (pre-wrap,
  `plaintext-only`) until the reviewer uses a formatting button. Then the
  whole card converts to blocks in one step — half-converting would
  collapse the remaining hard line breaks.

## 2026-08-29 — LA-SUGGEST als laag in het annotator-snippet, niet als los component

Suggested changes (agent wijzigt de pagina, reviewer accepteert/wijst af per
stuk) begonnen als eigen snippet met eigen highlight, pill en popup. Drie
iteraties lieten zien dat elke eigen implementatie (cel-gebonden knoppen,
gele mark, zelf positioneren in sticky tabellen) opnieuw de problemen opriep
die de annotator al lang had opgelost. Besluit: de laag leeft ín
annotator-snippet.html en hergebruikt letterlijk de annotatie-mechaniek —
la-rect-selecties (tekstregels voor tekst, één regiokader voor visuals), de
badge breed uitgetrokken tot pill met ✕ ✓ ✎, en voor ✎ de echte popup via
`LucAnnotator.openComposer` (chips incluis). Beslissingen zijn status
(state.json, component `suggest`), geen annotaties. `references/
suggest-snippet.html` is een deprecatie-pointer; niet meer inplakken.

## 2026-08-31 — Een LA-SUGGEST-change is te bewerken; pending wist de tekst niet

Bug: na ✎ + tekst + save kon de reviewer zijn eigen suggestie niet meer
bijschaven. Het oranje ✎-badge draait de keuze terug naar pending, en dat
deed `sugSave(elm, "pending", "")` — met een leeg `comment` en zonder
`refs`/`commentExpanded`, dus de getypte zin werd zowel in `sugState` als in
`state.json` overschreven. De volgende popup opende leeg.

Besluit: terugklikken naar pending is nog steeds terugklikken (de badge-flow
blijft), maar het bewaart de change-tekst, chips incluis. `sugPopup` vult het
commentveld met wat er in `sugState` staat — dat komt bij het laden uit
`POST /state`, dus de voorvulling overleeft een reload. Een al `processed`
entry telt daarbij als leeg. Bij `accepted`/`rejected` valt de tekst juist
weg: een verwerkende agent hoort geen dode change-comment op een accepted key
te vinden. En een voorgevuld commentveld zet de cursor achter de tekst in
plaats van ervoor — dat gold ook al voor het bewerken van een gewone
annotatie. Bewijs: `tests/case-14-suggest-change-bewerken.mjs`.

## 2026-08-31 — De LA-SUGGEST-laag hertekent bij zichtbaarheid, en één key is één pill

Twee bugs uit de KPI-pagina's van een klantproject, allebei in de LA-SUGGEST-laag.

**Verborgen rijen kregen geen pill.** De suggest-rijen zaten in ingeklapte
tabelgroepen (`collapsed-hide`) en dus zonder rect bij het tekenen; de laag
sloeg ze over. Uitklappen leverde geen hertekening op: de ResizeObserver kijkt
naar `document.body`, en die groeit niet als de tabel in zijn eigen
`overflow:auto`-scroller onder een `overflow:hidden`-body zit. Pas een andere
interactie (een annotatie plaatsen) liet de pills alsnog verschijnen. Besluit:
generiek meeliften op DOM- en zichtbaarheidswijzigingen — een MutationObserver
op `documentElement` (`childList` + de attributen `class`/`style`/`hidden`/
`open`) die de bestaande debounced `herteken()` aanroept, niet iets specifieks
voor deze inklapknoppen. Om te voorkomen dat de laag zichzelf aan de gang
houdt, gooit `render()` aan het eind zijn eigen mutatierecords weg
(`takeRecords`); filteren op klassenaam is te laat, want `el()` hangt de div
eerst in de body en zet de `la-`class er daarna pas op. Bewijs:
`tests/case-15-suggest-zichtbaar.mjs`, inclusief een rustmeting die een
render-lus zou betrappen.

**Eén key besliste stiekem over vijf rijen.** In de HTML van dat project deelden een
work-item-rij en zijn subtaakrijen dezelfde key (`wi-1042` op vijf rijen). De
laag tekende per element een pill, maar de beslissing gaat per key naar
`state.json` — vijf knoppen die samen één beslissing waren. Besluit: één key is
één suggestie, dus `renderSuggesties()` groepeert per key: alle rects van alle
elementen met die key worden gehighlight als één groep, met precies één pill.
Wat je ziet is dan wat er gebeurt. Wie per rij wil beslissen geeft elke rij een
eigen key (parent `wi-<id>`, subtaken `wi-<parentid>-<subid>`); zo staan de
live pagina's nu ook. Bewijs: `tests/case-16-suggest-gedeelde-key.mjs` en
`tests/case-17-suggest-losse-keys.mjs`.

Neveneffect in de suite: de mutant in `case-12` (snippet zonder scroll-listener
moet blijven plakken) sloeg om, omdat het plaatsen van de testannotatie zelf de
DOM muteert en de debounced hertekening dan ná de scroll viel. De mutant wacht
nu eerst 400ms uit; hij blijft daarmee aantoonbaar plakken en meet nog steeds
het ontbreken van de scroll-listener.

### Wat de falsificatieronde van 31-08-2026 aan die twee fixes veranderde

Twee onafhankelijke falsifiers vonden drie gaten die er toe deden, allemaal
verholpen voor de uitrol:

- **De debounce was uit te hongeren.** Nu elke mutatie `herteken()` voedt, kan
  een pagina die zichzelf per frame aanraakt (een rAF-animatie die een style
  zet) de timer eindeloos resetten: er wordt dan nooit getekend en de pill
  blijft weg — hetzelfde symptoom als de bug zelf. De debounce heeft daarom een
  plafond van 250ms: langer dan dat wachten we niet. Bewijs: assertie 5 in
  `case-15`, die rood wordt op een snippet zonder plafond.
- **De pill van een groep stond bij de verkeerde rij.** Hij hing aan het laatste
  rect van de hele groep, terwijl zijn tekst en popup van het eerste element
  komen: op een cluster van vijf rijen stond de knop naast de laatste subtaak.
  Het eerste element in documentvolgorde draagt nu de pill.
- **Een lege `data-la-suggest=""` voegde losse suggesties samen.** Een lege key
  groepeert niet meer.

Blijvende grens, bewust: de laag kijkt naar DOM-wijzigingen en naar de
attributen `class`, `style`, `hidden`, `open`. Een in- en uitklap die puur in
CSS gebeurt (`input:checked ~ tabel`) verandert geen attribuut en levert dus
geen hertekening op; dat staat als voorwaarde in het handboek. Een periodieke
sanity-render zou dat dekken, maar kost stroom op elke pagina en is voor de
KPI-pagina's (die `classList.toggle` gebruiken) niet nodig.
