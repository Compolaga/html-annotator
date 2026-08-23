---
name: html-annotator
description: >
  Standaard feedback-component voor ELKE HTML-pagina die een agent oplevert
  (prototypes, slides, vergelijkingspagina's, dashboards). Bouw het
  annotatie-snippet standaard in bij elke nieuwe of substantieel herziene
  HTML-oplevering, zonder erom te vragen. Trigger óók bij
  feedbackverwerking: een kaal bericht "." (alleen een punt), of "verwerk mijn
  feedback" / "check mijn bewaarde feedback" / een pad naar annotations.json of
  een annotatieronde — dan beschrijft deze skill hoe je de rondes en
  screenshot-crops uitleest en verwerkt.
---

# HTML-annotator: standaardcomponent + feedbackverwerking

**Lees vóór uitvoering `references/agent-handbook.md`.** Daar staan bridge,
rondes, verwerken (`.` / resolve / refs / locators / hunks), todolijst-spawn,
conceptkaarten (`la-draft`) en `la-sub`. Dit bestand is alleen de poort:
inbouwen, bridge starten, `/p/`-URL, plus de korte verwerk-trigger.

De volledige freeze (wat niet mag veranderen) staat in `VERIFICATION.md`.
Gedateerde keuzes: `decisions.md`. Installatie: `INSTALL.md`.

## Deel 1: inbouwen (bij elke HTML-oplevering)

Plak de volledige inhoud van `annotator-snippet.html` (in deze skill-map) onderaan
elke HTML, vlak voor `</body>` of aan het einde van het bestand. Het blok loopt
van `<!-- LUC-ANNOTATOR v2 -->` tot `<!-- /LUC-ANNOTATOR -->`.

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
~/.claude/skills/html-annotator/bin/ensure-bridge.sh
```

Draait hij al, dan doet het script niets. Draait hij niet, dan start het hem
losgekoppeld van je shell (nohup), schrijft de pid naar `bridge.pid` en de
output naar `bridge.log` in de skill-map, en wacht het tot hij antwoordt (max
5 seconden). Sla dit nooit over: zonder bridge belandt feedback in localStorage
en staat er niets op schijf.

**Vangnet, twee lagen.** Beide draaien `bin/hook-ensure-bridge.sh` uit deze
skill-map (log: `bridge-hook.log`), geregistreerd in
`~/.claude/settings.local.json`:

- **SessionStart** — één aanroep per sessie, ongeacht hoe die sessie straks HTML
  wegschrijft. Dit is de laag die telt: de PostToolUse-laag mist een agent die het
  bestand via Bash wegschrijft, en in auto-mode is Bash juist de voorgeschreven route.
- **PostToolUse op `Edit|Write`** — is het geschreven bestand een `.html`/`.htm` met de
  marker `LUC-ANNOTATOR`, dan gaat de bridge omhoog.

De matcher is niet verbreed naar `Bash`, want dat zou op élke Bash-call in élk project
vuren. Wat de gekozen route wél doet: de SessionStart-registratie staat op user-niveau met
een lege matcher, dus hij draait bij het starten van élke Claude Code-sessie op deze
machine, ook sessies die niets met annotaties doen. Dat is één curl per sessie, en niets
meer als de bridge al luistert. Die keuze staat in `decisions.md` (18-08-2026).
Verklein dit niet zonder een nieuw besluit.

**Zelfherstel in de pagina.** Het snippet controleert de bridge niet één keer bij het
laden, maar blijft elke 3 seconden opnieuw proberen zolang hij niet antwoordt (plus bij
`visibilitychange` en `focus`). Komt de bridge later omhoog — door de hook, of met de
hand — dan slaat de statuspil vanzelf om en is er geen reload nodig.

Verificatie: `tests/run.sh`, criteria in `references/acceptance.md`, freeze in
`VERIFICATION.md`. Twee bekende gaten: (1) verse-agent case is BLOKKED; (2) verborgen
paneel emuleert `document.hidden`, niet Chrome-throttling.

**Open de pagina altijd via de bridge, nooit via `file://` of de preview-pane.**
De bridge serveert lokale bestanden zelf op `GET /p/<pad-vanaf-home>`:

```
~/Desktop/todos.html
→ http://127.0.0.1:8791/p/Desktop/todos.html
```

Bouwen: absoluut pad, home-map eraf, rest achter `http://127.0.0.1:8791/p/`.
Paden buiten home → 403. Preview-pane als `data:` kan loopback nooit bereiken
(Private Network Access). Via `/p/` is de pagina same-origin met de bridge.

Wat de reviewer kan (gedrag ongewijzigd; details in het handbook):
- regio slepen, tekst selecteren, tekst koppelen (chips), Save;
- statuspil `X saved` of `bridge off - localStorage only`;
- weeslijst **"N likely processed"**;
- geen download-knop, geen Remove-all in de UI.

Test/debug-API: `window.LucAnnotator.add({type:'region'|'text', rect, comment,
selectedText})`, `.anns()`, `.bridge()`, `.session()`, `.resolve(annotatie)`.

## Verwerken (korte poort)

Triggers — geen bevestiging vragen:

- kaal **`.`** (alleen een punt, whitespace eromheen mag);
- "verwerk mijn feedback" / pad naar `annotations.json` of een ronde.

Bij `.` zelf de open ronde zoeken (`bin/toon-annotaties.py --open` of de bridge).
Eerst begrijpen, dan doorvoeren, dan `POST /resolve`. Lees
`references/agent-handbook.md` (deel 4) voor refs, locators, hunks, crops.
`bin/toon-annotaties.py` print de werkregel opnieuw als er iets openstaat.
