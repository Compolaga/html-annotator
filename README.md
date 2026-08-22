# html-annotator

Een Claude Code-skill die van elke HTML die een agent voor je maakt een pagina maakt
waarop je kunt annoteren — een rechthoek slepen zoals bij een snipping tool, of tekst
selecteren — en die feedback als JSON plus uitgesneden screenshots op schijf zet, waar
de volgende agentsessie hem gewoon leest.

Geen libraries, geen CDN, geen accounts. Eén HTML-snippet en een lokale
Python-bridge van de stdlib.

## Waarom

Feedback op een prototype geven in chat is omslachtig: je moet beschrijven waar je
naar kijkt. Met dit component wijs je het aan. De agent krijgt een crop van precies
dat gebied naast je comment, of de exact geselecteerde tekst.

## Hoe het werkt

```
HTML-pagina  ──►  annotator-snippet.html   (badges, snipping-UI, conceptkaarten)
                          │  fetch naar 127.0.0.1:8791
                          ▼
                  annotator-bridge.py      (schrijft JSON, snijdt crops, serveert /p/)
                          │
                          ▼
        ~/Desktop/annotaties/<pagina>/ronde-NN/annotations.json
                                            screenshots/annotatie-01.png
```

- **Rondes** — een ronde blijft open tot hij via `POST /remove-all` wordt
  afgesloten. Oude rondes worden nooit overschreven, dus de feedbackgeschiedenis
  van een pagina blijft staan.
- **Resolven** — een verwerkte annotatie wordt afgevinkt bij de bridge en verdwijnt van
  de pagina, maar blijft in de JSON als historie.
- **Zelfherstel** — de pagina blijft de bridge elke 3 seconden opnieuw proberen, dus als
  de bridge later opkomt slaat de statuspil vanzelf om zonder reload.
- **Conceptberichten** — een nog niet verstuurde mail of chat komt als kaart in de
  pagina, waarin je de tekst zelf kunt herschrijven; dat komt als losse hunks met
  tekst-ankers terug bij de agent.

Eén ding is niet optioneel: open de pagina via `http://127.0.0.1:8791/p/<pad-vanaf-home>`,
niet via `file://` of een preview-pane. Vanuit een `data:`-origin blokkeert Chrome elk
verzoek naar loopback (Private Network Access) en wordt er niets opgeslagen. Dat is
browserbeleid, geen instelling.

## Installeren

```bash
git clone https://github.com/kompolaga/html-annotator.git ~/repos/html-annotator
~/repos/html-annotator/install.sh
```

Het script zet de skill op zijn plek, installeert de bijbehorende memories en
registreert de twee hooks. **Lees [INSTALL.md](INSTALL.md)** — daar staan ook de twee
stappen die het script niet voor je doet, en de instructie voor een agent die dit voor
je installeert.

De memories zijn geen extraatje. Ze zijn de reden dat een verse agent het component
uit zichzelf inbouwt en de `/p/`-URL oplevert in plaats van een bestandspad.

## Wat er in zit

| bestand | wat het doet |
|---|---|
| `SKILL.md` | de skill zelf — wat de agent moet doen, in zeven delen |
| `annotator-snippet.html` | het blok dat onderaan elke HTML gaat |
| `annotator-bridge.py` | lokale server op 127.0.0.1:8791 (stdlib only) |
| `ensure-bridge.sh` | start de bridge, idempotent |
| `hook-ensure-bridge.sh` | dezelfde check, als Claude Code-hook |
| `toon-annotaties.py` | drukt een ronde leesbaar af, inclusief diffs |
| `pas-hunk-toe.py` | past één blok uit een herschreven conceptbericht toe |
| `vind-todolijst.sh` | vindt de HTML-todolijst op het bureaublad |
| `memories/` | de memories die het gedrag compleet maken |
| `tests/` | rood-groen-suite + `criteria.md` met de criteria |

## Grenzen

- macOS is de geteste omgeving. De scripts zijn POSIX-sh/Python en zouden op Linux
  moeten werken, maar dat is niet geverifieerd.
- `~/Desktop` zit op twee plekken hardcoded: de rondes landen daar, en
  `vind-todolijst.sh` scant daar.
- De testsuite heeft twee bekende blinde vlekken; die staan benoemd in
  `tests/criteria.md` en in INSTALL.md stap 5. Lees ze voordat je groen vertrouwt.
- De skill is in het Nederlands geschreven, inclusief SKILL.md en de commentaren.
