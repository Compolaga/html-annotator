# Verificatie en freeze

Doel: Luc verliest nooit een annotatie. Bewijs is
`~/Desktop/annotaties/<slug>/ronde-NN/annotations.json`, niet de chat.

De suite (`tests/run.sh`) toetst een **subset**. Dit bestand is de freeze:
refactor mag FUNC/LAYOUT/TECH hieronder niet wijzigen. Case die BLOKKED is
telt nooit als groen.

Mapping suite → B-rij: B10 case-02 · B11 case-04 · B18 case-01 (BLOCKED) ·
B12 case-03 · B17 sideview-test.sh (handmatig) · B13 case-05 · B14 case-06 ·
B15 case-07 · B16/B22 case-08.

## Non-goals

- Modelgedrag (agent plakt snippet / belt resolve) is niet door de suite
  afdwingbaar.
- Sideviewer is toegestaan, maar alleen via `/p/`, nooit als `file://`/`data:`.
- Chrome-throttling in een echte achtergrondtab is niet getest.

## MUST (samengevat)

### Delivery (DOC)

- Elke nieuwe/substantiële HTML voor Luc krijgt het v2-blok; geen duplicaat;
  v1 vervangen tot `</script>`.
- Daarna `ensure-bridge.sh`. URL = `/p/<pad-vanaf-home>`, nooit `file://`.
- Kaal `.` = verwerk open annotaties, geen bevestiging. Daarna `POST /resolve`.
- HTML-deliverables via deze skill; md/docx via Plannotator (niet in deze
  skill-install).

### Hooks & bridge (TECH)

- Luistert op `127.0.0.1:8791`. `GET /ping` ok, CORS `*`, OPTIONS 204.
- `ensure-bridge.sh` is idempotent; poort bezet door non-bridge → geen stille
  exit 0. Stale pidfile weg.
- SessionStart (lege matcher) + PostToolUse `Edit|Write` op HTML met marker.
  Matcher niet verbreden naar alle Bash.
- POST: `/session` `/save` `/delete` `/remove-all` `/resolve` `/sessie`.
- Root `~/Desktop/annotaties` (`LUC_ANNOTATOR_ROOT`). Rondes nooit
  overschrijven. Nieuwe ronde alleen na `/remove-all`.
- `contentHash` zonder annotator-blok. Crop via Pillow of Chrome; falen
  bewaart de annotatie toch. Stale region hergebruikt crop.
- `/p/` binnen home, anders 403. JSON atomair (tmp + replace).

### Pagina (FUNC / LAYOUT)

- Poller 3s + visibility/focus; hidden slaat over. Pil: `checking bridge...` →
  `N saved` of `bridge off - localStorage only`. Engels. Geen Remove-all,
  geen download.
- Regio ≥8×8, ghost blijft tot Save/Cancel. Tekst ≥2 tekens, locator + nth;
  highlight = tekstregels, niet de celbox. Oude annotaties zonder locator:
  tekstzoeken.
- Refs: chips `⟦rN⟧`, Escape-lagen, Cmd+Enter slaat op, incomplete refs
  blokkeren save.
- Weeslijst `N likely processed`, default ingeklapt.
- Bridge leidend bij load; localStorage-vangnet; ronde-wissel wist lokale badges.
- Draft: klik-edit, tracked changes, type `edit`, geen badge/wees. Hunks
  plaatsbaar via anker. `la-sub*` +30px/niveau.

### Agent-leesbaarheid (DOC)

- `toon-annotaties.py` toont WERKREGEL bij open items, expandeert refs,
  toont locator. `refsIncomplete` → vraag opnieuw te saven, niet gokken.

## Vrijgavepoort (na refactor)

1. `python3 -m compileall -q annotator bin`
2. Hook-bestanden staan in `bin/` (`ensure-bridge.sh`,
   `hook-ensure-bridge.sh`); `install.sh` registreert `bin/hook-ensure-bridge.sh`.
3. `install.sh` kopieert geen memories; agent-regels staan in `references/`.
4. Suite: `tests/run.sh` — rood als een case faalt of BLOKKED telt als pass.
5. Geen diff op snippet-CSS of Engelse UI-strings, behalve paden naar
   `bin/` en comment-koppen.
