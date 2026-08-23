# Criteria

Source of truth for behaviour. `VERIFICATION.md` is the freeze;
`docs/DECISIONS.md` is why a choice stayed. A criterion without a check
is a named gap, not silent coverage.

Intent: an annotation the reviewer places lands on disk and does not
disappear after a restart, a reload, or an edit elsewhere on the page.
Pages open via `/p/`. The repo is a skill someone else can install,
without personal workflow files.

## Seams

Tests only touch these edges: the bridge HTTP API, the
`toon-annotaties.py` and `pas-hunk-toe.py` CLIs, `ensure-bridge.sh`
exit codes, the snippet via Playwright (cases 02/05/06/07/08), and the
public paths in `bin/` plus root contents.

No tests against internal helpers, no snapshots of whole JSON dumps.

## Existing behaviour (lock)

| ID | Criterion | Check | Gap |
|---|---|---|---|
| B1 | `/ping` 200, CORS `*`, OPTIONS 204 | `test_bridge_contract.py` | no mutation (identity/CORS) |
| B2 | `/p/` outside home → 403 | same + `mutate-contract.sh` | |
| B3 | POST `/session` `/save` `/delete` `/remove-all` `/resolve` `/sessie` exist; `/resolve` sets `resolved` on disk | same + mutate (resolve-noop) | no mutation per remaining route |
| B4 | A round is never overwritten; a new round only after `/remove-all` | same + mutate | |
| B5 | `contentHash` ignores the annotator block | same + mutate | |
| B6 | A crop failure still stores the annotation | `h_save` + raising `maak_crop` (no live Chrome) + mutate | |
| B7 | JSON write is atomic (tmp + replace); a dump error leaves the original | same (direct `schrijf`) | tmp cleanup is B21 |
| B8 | `toon-annotaties.py --open` prints the work rule, expands refs, shows locator | `test_toon.py` + mutate (work rule) | refs/locator not mutated |
| B9 | Missing refs: do not guess, do warn | same + `test_record.py` | no mutation |
| B10 | Pill self-heals and a later save lands on disk | case-02 | no contract mutation |
| B11 | SessionStart brings the bridge up | case-04 | no contract mutation |
| B12 | `ensure-bridge.sh` does not lie | case-03 | no contract mutation |
| B13 | A draft edit lands as `type: edit` | case-05 | no contract mutation |
| B14 | Hunks are independently applicable | case-06 + `pas-hunk-toe.py` | no contract mutation |
| B15 | `la-sub*` +30px, hook without page CSS | case-07 | no contract mutation |
| B17 | Sideviewer origin | `sideview-test.sh` | manual |
| B18 | A fresh agent pastes the snippet | case-01 | BLOCKED (spend limit); not in default `run.sh` |
| B19 | Chrome throttling of a real background tab | — | untested, leave it |
| B20 | The model pastes the snippet / calls resolve | — | not enforceable |

### Case notes (what the suite actually measures)

**B10 / case-02.** Given a page that is already open while the bridge is
down, when the bridge comes up, the pill flips to `X saved` within 10s
without a reload, and a save after that lands in `annotations.json`.
The hidden-panel variant emulates `document.hidden`; it does not
measure Chrome timer throttling (B19).

**B11 / case-04.** Given the hooks in `settings.local.json`, a route
exists that starts the bridge without depending on how the agent writes
the file, and the `Edit|Write` route still works. SessionStart covers
Bash writes; the matcher is not widened to every Bash call.

**B12 / case-03.** Given port 8791 held by a non-bridge, `ensure-bridge.sh`
ends with a live answering bridge or a non-zero exit — never exit 0
while `/ping` is empty.

**B13 / case-05.** Click-edit in a draft card stores `type: edit` with
original, new, and a diff that points at the changed span, and survives
reload. No badge, no orphan list.

**B14 / case-06.** Each contiguous edit is its own hunk with surrounding
text as the anchor. Hunks apply and resolve independently. The edit is
done only when no hunk is open.

**B15 / case-07.** Each nest level steps 30px further in, at least four
deep. A child draws a hook on any block element, including a bare
`<li>`. Line colour follows `--line` when set, and stays visible
without it. `--la-stap` moves indent and hook together.

**B17.** Manual: `tests/sideview-test.sh`. Opening a file in the
sideviewer is a `data:` snapshot and cannot reach the bridge. The same
page via `/p/` works, including self-heal. Measured 2026-08-18.

**B18 / case-01.** A fresh agent asked to ship HTML via Bash must start
the bridge (new pid) and include the `LUC-ANNOTATOR` marker. All runs
must pass. Currently BLOCKED on a spend limit.

## Architecture

| ID | Criterion | Check |
|---|---|---|
| A1 | Root holds only ports: README, SKILL, INSTALL, VERIFICATION, CRITERIA, install.sh, `.gitignore`, plus `annotator/` `bin/` `references/` `tests/` `docs/`. Snippet lives in `references/`. Gitignored runtime does not count. | `test_layout.py` |
| A2 | No `memories/`. Agent rules live in `references/` | same |
| A3 | `extras/` gone; not installed | same + install.sh |
| A4 | CLIs and hooks live in `bin/`; install/hooks point there | same |
| A5 | Python modules: `snake_case`. Scripts in `bin/`: kebab-case | same |
| A6 | Agent-facing text names no person. Allowlist (behaviour): `LucAnnotator`, `LucAnnotatorBridge`, `LUC-ANNOTATOR`, `luc-annotator`, `luc-annotaties`, `LUC_ANNOTATOR_*`. Exempt: `docs/DECISIONS.md`, `VERIFICATION.md`. | `test_layout.py` |
| A7 | B1–B15 plus B16/B21/B22 stay green | `tests/run.sh` (default: 00 02–09 11) |

## Changed behaviour (not a lock of 472cf63)

| ID | Criterion | Check | Gap |
|---|---|---|---|
| B16 | Locator survives a row insert; orphan only when the text is gone; repeated cell text stays on the labeled row | case-08 + mutate | no real Reconi page in the repo |
| B21 | A dump error removes the `.tmp` | `test_bridge_contract.py` + mutate (`os.remove`) | |
| B22 | A page under `/p/` on a non-default port talks to that port | case-08 (requires `LUC_ANNOTATOR_PORT`) + mutate | |

## Identifiers (non-goal)

`window.LucAnnotator`, `<!-- LUC-ANNOTATOR -->`, the bridge identity
`luc-annotator`, the localStorage prefix `luc-annotaties` and
`LUC_ANNOTATOR_*` stay. Renaming them orphans existing annotated pages
unless a migration ships with the rename.
