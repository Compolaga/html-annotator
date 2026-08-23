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

`install.sh` zet alleen de drie annotator-memories. Vijf Luc-workflow-memories
staan in `extras/luc-memories/` en worden niet gekopieerd. Bestaande
project-`MEMORY.md`-regels worden niet verwijderd.
