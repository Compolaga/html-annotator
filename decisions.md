# Besluiten (html-annotator)

Alleen keuzes die een latere opruimronde niet mag heropenen zonder Luc.
Gedrag wijzigen hoort hier niet thuis — dat is een nieuwe beslissing.

## 2026-08-18 — SessionStart-hook altijd aan

De bridge-hook draait op user-niveau bij élke Claude Code-sessie (lege matcher).
PostToolUse blijft beperkt tot `Edit|Write` op HTML met `LUC-ANNOTATOR`.
Niet versmallen zonder Luc: hij wil dat de bridge praktisch altijd luistert.

## 2026-08-18 — Pagina's via `/p/`, niet `file://` of preview-pane

`data:`-origin kan loopback nooit bereiken (Private Network Access).
Opleveren = `http://127.0.0.1:8791/p/<pad-vanaf-home>`.

## 2026-08-18 — Origin-log blijft aan

Elk bridge-verzoek logt `origin=` naar stderr / `bridge.log`.

## 2026-08-23 — Geen Remove-all in de UI

`POST /remove-all` bestaat nog. De knop is weg. Rondes sluiten alleen via dat
endpoint, niet via een pagina-wijziging.

## 2026-08-23 — Engelse UI-copy, statuspil `X saved`

Gebruikerszichtbare annotator-teksten zijn Engels. De pil toont het aantal
openstaande annotaties, zonder `round N -`-prefix.

## 2026-08-23 — Paste-blok blijft één bestand

`annotator-snippet.html` is het enige dat onderaan HTML gaat. Geen bundler,
geen gesplitst runtime-JS zolang de output niet byte-identiek is.

## 2026-08-23 — Skill-install zonder persoonlijke memories

`install.sh` zet geen memories. Agent-regels staan in `SKILL.md` en
`references/`. Bestaande project-`MEMORY.md`-regels worden niet verwijderd.
`extras/luc-memories/` is verwijderd (plan zei: verplaatsen). Bron: deze
opruimronde, "het mag drastisch veranderen". Inhoud alleen nog in git op
`472cf63`.

## 2026-08-23 — Locator volgt de rij, niet de eerste herhaalde span

`zoekAnker` behandelt “start-span bestaat nog” niet meer als verwerkt.
Label komt van de start-rij; `zoekHostViaLabel` / `laHostPast` houden
herhaalde celtekst op die rij. Bron: Luc, Reconi-owners 14:47. Geen
Reconi-pagina in de suite — case-08 is de gereduceerde vorm.

## 2026-08-23 — Root is poort, CLI's in bin/

CLIs en hooks leven in `bin/`. Python-bibliotheek in `annotator/` (snake_case).
`ensure-bridge.sh` en `hook-ensure-bridge.sh` zijn locatie-relatief, niet
hardcoded naar `~/.claude/skills/...`. Agent-facing docs noemen geen
persoonsnaam; `window.LucAnnotator` en de marker `LUC-ANNOTATOR` blijven
(publieke API).
