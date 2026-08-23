# Verification and freeze

Proof is `~/Desktop/annotaties/<slug>/ronde-NN/annotations.json`, not
the chat. The suite (`tests/run.sh`) covers a **subset**. This file is
the freeze: a refactor must not change FUNC/LAYOUT/TECH below. A
BLOCKED case never counts as green.

Suite → B-row: B10 case-02 · B11 case-04 · B18 case-01 (BLOCKED) ·
B12 case-03 · B17 sideview-test.sh (manual) · B13 case-05 · B14 case-06 ·
B15 case-07 · B16/B22 case-08. Full mapping: `CRITERIA.md`.

## Non-goals

- Model behaviour (agent pastes snippet / calls resolve) is not
  enforceable by the suite.
- A sideviewer is allowed, but only via `/p/`, never as `file://`/`data:`.
- Chrome throttling of a real background tab is untested.

## MUST (summary)

### Delivery

- Every new or substantial HTML gets the v2 block; no duplicate; v1
  replaced through `</script>`.
- Then `ensure-bridge.sh`. URL = `/p/<path-from-home>`, never `file://`.
- A bare `.` = process open annotations, no confirmation. Then
  `POST /resolve`.
- HTML deliverables through this skill; md/docx through Plannotator
  (not in this install).

### Hooks and bridge

- Listens on `127.0.0.1:8791`. `GET /ping` ok, CORS `*`, OPTIONS 204.
- `ensure-bridge.sh` is idempotent; port held by a non-bridge → no
  silent exit 0. Stale pidfile removed.
- SessionStart (empty matcher) + PostToolUse `Edit|Write` on HTML with
  the marker. Do not widen the matcher to all Bash.
- POST: `/session` `/save` `/delete` `/remove-all` `/resolve` `/sessie`.
- Root `~/Desktop/annotaties` (`LUC_ANNOTATOR_ROOT`). Rounds never
  overwritten. New round only after `/remove-all`.
- `contentHash` without the annotator block. Crop via Pillow or Chrome;
  failure still stores the annotation.
- `/p/` inside home, else 403. JSON atomic (tmp + replace).

### Page

- Poller 3s + visibility/focus; hidden skips. Pill: `checking bridge...`
  → `N saved` or `bridge off - localStorage only`. English. No
  Remove-all, no download.
- Region ≥8×8. Text ≥2 characters, locator + nth; highlight = text
  lines, not the cell box.
- Refs: chips `⟦rN⟧`. Incomplete refs block save.
- Orphan list `N likely processed`, collapsed by default.
- Draft: click-edit, tracked changes, type `edit`, no badge/orphan.
  Hunks place via anchor. `la-sub*` +30px per level.

### Agent readability

- `toon-annotaties.py` prints the work rule on open items, expands
  refs, shows locator. `refsIncomplete` → ask to save again, do not guess.

## Release gate

1. `python3 -m compileall -q annotator bin`
2. Hook files live in `bin/`; `install.sh` registers
   `bin/hook-ensure-bridge.sh`.
3. `install.sh` copies no memories; agent rules live in `references/`.
4. Suite: `tests/run.sh` — red if a case fails or BLOCKED is treated as pass.
5. No diff on snippet CSS or English UI strings, except paths into
   `bin/` and comment headers.
