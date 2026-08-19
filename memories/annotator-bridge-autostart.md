---
name: annotator-bridge-autostart
description: "Waarom de annotator-bridge \"uit\" leek te staan bij een verse agent, wat de fix was (poller + SessionStart-hook), en de harde grens dat een data:-origin de bridge nooit kan bereiken"
metadata:
  node_type: memory
  type: project
---

Onderzocht en gefixt op 2026-08-18. De klacht: een verse agent gebruikt
`html-annotator`, en dan staat de bridge niet aan — of de pagina moet nog een
"na-zwengel" krijgen voordat die de bridge ziet.

Twee oorzaken, beide bevestigd met een rood-groen-suite in
`~/.claude/skills/html-annotator/tests/` (zie `tests/criteria.md`):

1. **Het snippet checkte de bridge één keer bij het laden.** Kwam de bridge een seconde
   later omhoog, dan bleef een al openstaande pagina op "bridge uit" staan tot een
   reload. Dát was de na-zwengel. Fix: een poller elke 3s zolang de bridge niet
   antwoordt, plus `visibilitychange`/`focus`. Mutatietest wijst uit dat de **timer** het
   dragende deel is; de listeners zijn er voor een verborgen tab, waar Chrome
   `setInterval` naar ~1×/minuut throttelt.
2. **De PostToolUse-hook hing aan `Edit|Write`.** Een agent die de HTML via Bash
   wegschrijft (in auto-mode juist de voorgeschreven route) triggerde hem nooit. Fix:
   een SessionStart-tak in `hook-ensure-bridge.sh` plus registratie op SessionStart in
   `settings.local.json` — één aanroep per sessie dekt álle schrijfroutes. Bewust NIET
   de matcher naar `Bash` verbreed: dat vuurt op elke Bash-call in elk project.

**Twee keuzes die de gebruiker zelf bekrachtigde (18-08-2026), nadat een geïsoleerde
rubric-review ze als scope-overschrijding aanwees:** de SessionStart-hook mag globaal
blijven, dus bij élke sessie op de machine — hij wil dat de bridge praktisch altijd
aanstaat. En de `origin=`-logging in `annotator-bridge.py` blijft permanent aan.
Verklein geen van beide zonder het te vragen.

**Harde grens.** Vanuit een `data:`-origin kan de bridge nooit bereikt worden. Chrome:
*"the resource is in more-private address space `loopback`"* — Private Network Access.
Geen CORS-header of hook repareert dat. Vandaar de regel in SKILL.md om pagina's via
`http://127.0.0.1:8791/p/<pad-vanaf-home>` te openen. Op `file://` werkt opslaan wél.

**GEMETEN 2026-08-18 in de echte Claude Desktop-sideviewer (Electron 42.9.2), twee keer:**

- **bestand openen** → `data:`-snapshot, `origin: "null"`, `isSecureContext: false`,
  `fetch` faalt met "Failed to fetch". Slaat niets op, en herstelt ook niet als de bridge
  omhoog komt.
- **via `http://127.0.0.1:8791/p/<pad-vanaf-home>` openen** → `origin` is de bridge zelf,
  secure, loopback bereikbaar, pil groen binnen 1s, zelfherstel werkt.

De sideviewer is dus niet het probleem; de manier van openen is het. Lever altijd de
`/p/`-URL, nooit het bestandspad.

De bridge logt `origin=` per verzoek, dus dit is één meting waard in plaats van een
aanname:
`grep -o 'origin=[^ ]*' ~/.claude/skills/html-annotator/bridge.log | sort -u` nadat er
een pagina in de sideviewer open is geweest.

**Val bij dit soort tests:** `claude -p` als "verse agent" liep op 2026-08-18 stuk op een
spend-limit. Reken erop dat een agent-in-the-loop-case geblokkeerd kan raken, en laat een
geblokkeerde case nooit als pass lezen.

Zie [[html-annotator-standaard]] voor waarom dit component overal in zit.
