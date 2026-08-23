# html-annotator

Skill die van elke HTML die een agent voor Luc maakt een annoteerbare pagina
maakt. Feedback landt als JSON plus crops op schijf.

Geen libraries, geen CDN. Eén plakbaar snippet en een lokale Python-bridge
(stdlib).

## Start hier

| Voor | Bestand |
|---|---|
| Installeren / uitrollen | [HANDOFF.md](HANDOFF.md) → [INSTALL.md](INSTALL.md) |
| Wat een agent moet doen | [SKILL.md](SKILL.md) + verplicht [references/agent-handbook.md](references/agent-handbook.md) |
| Wat groen betekent | [VERIFICATION.md](VERIFICATION.md) · `tests/run.sh` |
| Waarom iets zo is | [decisions.md](decisions.md) |

## Hoe het werkt

```
HTML-pagina  ──►  annotator-snippet.html
                     fetch 127.0.0.1:8791
                          ▼
                  annotator-bridge.py
                          ▼
        ~/Desktop/annotaties/<pagina>/ronde-NN/annotations.json
```

Open pagina's via `http://127.0.0.1:8791/p/<pad-vanaf-home>`, niet via
`file://` of een preview-pane. Een `data:`-origin kan loopback niet bereiken.

## Installeren

```bash
git clone https://github.com/kompolaga/html-annotator.git ~/repos/html-annotator
~/repos/html-annotator/install.sh
```

Het script linkt de skill, zet **drie** annotator-memories en registreert de
hooks. Details en handmatige reststappen: [INSTALL.md](INSTALL.md).

## Wat er in zit

| pad | rol |
|---|---|
| `SKILL.md` | agent-poort (inbouwen, `/p/`, `.`) |
| `references/` | handbook + annotation-record |
| `annotator-snippet.html` | het blok onderaan elke HTML |
| `annotator-bridge.py` | `127.0.0.1:8791` |
| `ensure-bridge.sh` / `hook-ensure-bridge.sh` | start + hooks (blijven in de root) |
| `toon-annotaties.py` / `pas-hunk-toe.py` | agent-leesbaarheid / hunks |
| `memories/` | drie annotator-memories |
| `extras/luc-memories/` | Luc-workflow, niet geïnstalleerd |
| `tests/` | suite + `criteria.md` (subset van de freeze) |

## Grenzen

- macOS is de geteste omgeving.
- `~/Desktop/annotaties` en `vind-todolijst.sh` → Desktop blijven de default.
- Twee blinde vlekken in de suite: zie VERIFICATION.md / INSTALL.md stap 5.
