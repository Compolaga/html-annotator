# Acceptatiecriteria

Bron van waarheid voor gedrag. `VERIFICATION.md` blijft de freeze-samenvatting;
dit bestand koppelt elk MUST aan een check. Een criterium zonder check is een
benoemd gat, geen stille dekking.

Intent (bevestigd 2026-08-18 t/m 2026-08-23): een annotatie die de gebruiker
zet, landt op schijf en verdwijnt niet door een herstart, een reload, of een
paginawijziging elders. Openen gebeurt via `/p/`. De repo moet een skill zijn
die een ander kan installeren, zonder persoonlijke workflow-bestanden.

## Seams

Tests raken alleen deze randen: HTTP van de bridge, CLI van `toon-annotaties.py`
en `pas-hunk-toe.py`, `ensure-bridge.sh` exitcodes, het snippet via Playwright
(bestaande case-02/05/06/07/08), en na de verhuizing de publieke paden in
`bin/` plus de root-inhoud.

Geen tests tegen interne helpers, geen snapshots van hele JSON-dumps.

## Bestaand gedrag (lock, vóór verhuizing)

| ID | Criterium | Check | Gat |
|---|---|---|---|
| B1 | `/ping` 200, CORS `*`, OPTIONS 204 | `test_bridge_contract.py` | geen mutatie (identiteit/CORS) |
| B2 | `/p/` buiten home → 403 | idem + `mutate-contract.sh` | |
| B3 | POST `/session` `/save` `/delete` `/remove-all` `/resolve` `/sessie` bestaan; `/resolve` zet `resolved` op schijf | idem + mutate (resolve-noop) | geen mutatie per overige route |
| B4 | Ronde wordt niet overschreven; nieuwe ronde alleen na `/remove-all` | idem + mutate | |
| B5 | `contentHash` negeert het annotator-blok | idem + mutate | |
| B6 | Crop-fout bewaart de annotatie toch | `h_save` + `maak_crop` die opbolt (geen live Chrome) + mutate | |
| B7 | JSON-schrijf is atomair (tmp + replace); dump-fout laat het origineel | idem (direct `schrijf`) | tmp-opruim is B21 |
| B8 | `toon-annotaties.py --open` toont WERKREGEL, expandeert refs, toont locator | `test_toon.py` + mutate (WERKREGEL) | refs/locator niet gemuteerd |
| B9 | Ontbrekende refs: niet gokken, wel waarschuwen | idem + `test_record.py` | geen mutatie |
| B10 | Zelfherstel pil + save-op-schijf | case-02 | geen contract-mutatie |
| B11 | SessionStart brengt bridge omhoog | case-04 | geen contract-mutatie |
| B12 | `ensure-bridge.sh` liegt niet | case-03 | geen contract-mutatie |
| B13 | Draft-edit landt als `type: edit` | case-05 | geen contract-mutatie |
| B14 | Hunks apart toepasbaar | case-06 + `pas-hunk-toe.py` | geen contract-mutatie |
| B15 | `la-sub*` +30px, haakje zonder pagina-CSS | case-07 | geen contract-mutatie |
| B17 | Sideviewer-origin | `sideview-test.sh` | handmatig |
| B18 | Verse agent plakt snippet | case-01 | BLOKKED (spend limit); niet in `run.sh` default |
| B19 | Chrome-throttling echte achtergrondtab | — | ongetest, zo laten |
| B20 | Model plakt snippet / belt resolve | — | niet afdwingbaar |

## Architectuur (nog te bouwen; test eerst rood)

| ID | Criterium | Check |
|---|---|---|
| A1 | Root bevat alleen poorten: README, SKILL, INSTALL, HANDOFF, VERIFICATION, decisions, snippet, install.sh, `.gitignore`, plus `annotator/` `bin/` `references/` `tests/` `docs/`. Gitignored runtime (`bridge.log`, `bridge.pid`, `bridge-hook.log`, `__pycache__`) telt niet mee. | `test_layout.py` (runtime uit `.gitignore`) |
| A2 | Geen `memories/`. Agent-regels staan in `references/` | idem |
| A3 | `extras/` weg; niet geïnstalleerd | idem + install.sh |
| A4 | CLI’s en hooks leven in `bin/`; install/hooks wijzen daarheen | idem |
| A5 | Python-modulenamen: `snake_case`. Scripts in `bin/`: kebab-case | idem |
| A6 | Agent-facing tekst noemt geen persoonsnaam. Allowlist (gedrag): `LucAnnotator`, `LucAnnotatorBridge`, `LUC-ANNOTATOR`, `luc-annotator`, `luc-annotaties`, `LUC_ANNOTATOR_*`. Exempt: `decisions.md`, `VERIFICATION.md`. | `test_layout.py` |
| A7 | B1–B15 plus B16/B21/B22 blijven groen | `tests/run.sh` (default: 00 02–09 11; case-01 en case-10 expliciet) |

## Gewijzigd gedrag (deze ronde, geen lock van 472cf63)

| ID | Criterium | Check | Gat |
|---|---|---|---|
| B16 | Locator overleeft rij-insert; wees alleen als tekst weg is; herhaalde celtekst blijft op de gelabelde rij. Nieuw t.o.v. 472cf63 (`zoekHostViaLabel`, `laHostPast`). Bug: Reconi-owners, 2026-08-23. | case-08 + mutate (label, wees-te-vroeg, `zoekHostViaLabel`) | geen echte Reconi-pagina in de repo |
| B21 | Dump-fout ruimt het `.tmp` op | `test_bridge_contract.py` + mutate (`os.remove`) | |
| B22 | Pagina onder `/p/` op een niet-default poort praat met die poort | case-08 (eist `LUC_ANNOTATOR_PORT`) + mutate (hard 8791) | |

## Identifiers (geen-doel)

`window.LucAnnotator`, `<!-- LUC-ANNOTATOR -->`, de bridge-identiteit
`luc-annotator`, de localStorage-prefix `luc-annotaties` en de env-vars
`LUC_ANNOTATOR_*` blijven. Hernoemen orphaned
bestaande geannoteerde pagina's tenzij er een migratie bij zit; die migratie
hoort niet bij deze opruimronde.
