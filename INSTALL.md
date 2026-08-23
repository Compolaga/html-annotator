# INSTALL — instructie voor de agent

Lees dit als je Claude Code bent en gevraagd wordt deze repo te installeren.
Doel: de skill gedraagt zich na afloop precies zoals op de machine waar hij vandaan
komt — dus niet alleen de bestanden, maar ook de hooks en de
opleverregel. Sla geen stap over; stap 2 en 3 zijn juist de stappen die het verschil
maken tussen "de skill staat er" en "de skill werkt vanzelf".

## De snelle route

```bash
git clone https://github.com/kompolaga/html-annotator.git ~/repos/html-annotator
~/repos/html-annotator/install.sh
```

`install.sh` doet stap 1 t/m 3 hieronder en is idempotent. Draai daarna alsnog stap 4
met de hand. Wil je het handmatig, of faalde het script
(bijvoorbeeld geen `jq`), volg dan de stappen zelf.

Agent-regels staan in `SKILL.md` en `references/`. Er worden geen memories
gekopieerd.

## Stap 1 — skill op zijn plek

De skill moet vindbaar zijn als `~/.claude/skills/html-annotator/`. Een symlink naar
de clone is prima en de voorkeur: dan is een update één `git pull`.

```bash
ln -s ~/repos/html-annotator ~/.claude/skills/html-annotator
chmod +x ~/.claude/skills/html-annotator/bin/*.sh ~/.claude/skills/html-annotator/bin/*.py
```

Bestaat er al iets op dat pad, overschrijf dat dan niet zonder te vragen.

## Stap 2 — de twee hooks registreren

Deze zorgen dat de bridge praktisch altijd aanstaat. Zonder deze hooks moet de
gebruiker of de agent `ensure-bridge.sh` handmatig draaien, en dan is het antwoord op
"waarom slaat hij niets op" bijna altijd: de bridge stond uit.

In `~/.claude/settings.local.json`, onder `hooks`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "<HOME>/.claude/skills/html-annotator/bin/hook-ensure-bridge.sh",
            "timeout": 15,
            "statusMessage": "annotator-bridge check"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "<HOME>/.claude/skills/html-annotator/bin/hook-ensure-bridge.sh",
            "timeout": 15,
            "statusMessage": "annotator-bridge check"
          }
        ]
      }
    ]
  }
}
```

Vervang `<HOME>` door het echte home-pad; het hook-veld accepteert geen `~`. Staan er
al andere hooks onder `PostToolUse` of `SessionStart`, voeg deze er dan bij in plaats
van ze te vervangen.

De SessionStart-hook met lege matcher draait bij élke Claude Code-sessie op de
machine, ook sessies die niets met annotaties doen. Dat is bewust: het is één curl per
sessie, en de PostToolUse-laag mist een agent die de HTML via Bash wegschrijft. Wil de
gebruiker dat smaller, dan is dat zijn keuze — verklein het niet ongevraagd.

## Stap 3 — de opleverregel in CLAUDE.md

De sterkste trigger zit niet in de skill maar in de globale instructies. Zet in
`~/.claude/CLAUDE.md` een regel in deze geest, aangepast aan hoe de gebruiker het wil:

```markdown
## Opleveren

Mails, plannen, analyses en andere uitwerkingen lever je als HTML via de skill
`html-annotator`, niet als tekst in de chat, zodat er inline en op selectie
commentaar op gezet kan worden.
```

Vraag dit even na bij de gebruiker in plaats van het er ongevraagd in te zetten —
het raakt al zijn projecten.

## Upgraden vanaf een oudere install

Draai `./install.sh` opnieuw (of `./install.sh --copy` als de skill een
kopie is, geen symlink). `--copy` ververst `$DOEL`. Zonder `--copy` wordt
een bestaande map die niet deze clone is met rust gelaten, en registreert
het script geen hook die het bestand niet kan zien.

Oude installer zette memories. Die staan niet meer in deze skill. Als je ze
nog hebt onder `~/.claude/projects/*/memory/`, zijn dat:

- `annotator-bridge-autostart.md`
- `html-annotator-standaard.md`

Niet automatisch wissen — het zijn projectregels. Zelf weghalen als de
handbook (`references/agent-handbook.md`) ze vervangt.

De hook moet wijzen naar `bin/hook-ensure-bridge.sh`, niet naar
`hook-ensure-bridge.sh` in de skill-root.

## Stap 4 — verifiëren

```bash
~/.claude/skills/html-annotator/bin/ensure-bridge.sh
curl -s http://127.0.0.1:8791/ping
```

Verwacht: `{"ok": true, "bridge": "luc-annotator", "version": 2, ...}`.

De suite draaien (Node + Playwright; eenmalig zelf installeren):

```bash
(cd ~/.claude/skills/html-annotator/tests && npm i --no-save playwright-core)
~/.claude/skills/html-annotator/tests/run.sh
```

Twee grenzen die je moet kennen voordat je op groen vertrouwt, en die ook in
`references/acceptance.md` staan: de "verse agent"-case is nooit in de praktijk geverifieerd
(hij meldt zich als BLOCKED, niet als pass), en de verborgen-paneel-variant emuleert
`document.hidden` en toetst dus de branch-logica, niet Chrome's echte throttling.

Eindtest die telt: maak een HTML met het snippet erin, open hem via
`http://127.0.0.1:8791/p/<pad-vanaf-home>`, sleep een rechthoek, typ een comment,
Save. Er hoort nu een `annotations.json` plus een crop te staan onder
`~/Desktop/annotaties/<slug>/ronde-01/`.

## Systeemeisen

- **python3** (stdlib is genoeg) — de bridge draait hierop.
- **Chrome** — voor de screenshot-crops (`--headless=new --screenshot`). Zonder Chrome
  worden regio-annotaties opgeslagen zonder crop.
- **Pillow** (optioneel) — snellere crops; zonder Pillow snijdt Chrome zelf via een
  iframe-clip. Beide routes zijn getest.
- **jq** (optioneel) — alleen voor het automatisch registreren van de hooks.
- **Node** (optioneel) — alleen voor de testsuite.
- Poort **8791** moet vrij zijn. Die is bewust gekozen: 8080 is vaak van Docker.

## Wat deze repo bewust niet meelevert

- `~/Desktop/annotaties/` — dat is gebruikersdata, die ontstaat vanzelf.
- De skills waar SKILL.md naar verwijst en die hier niet in zitten:
  `task-spawnen` (deel 5, sessienaamgeving bij spawnen), `nieuwe-sessie`
  (`POST /sessie`, de claude://-deeplink) en `bericht-sturen` (deel 6, de
  verstuurregel bij conceptberichten). De annotator werkt zonder, maar die drie
  verwijzingen lopen dan dood — meld dat aan de gebruiker in plaats van ze stil te
  laten falen.
