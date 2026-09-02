# Criteria

An annotation the reviewer places lands on disk and does not disappear
after a restart, a reload, or an edit elsewhere on the page. Pages open
via `/p/`. The repo is a skill someone else can install, without
personal workflow files.

Proof is `~/Desktop/annotaties/<slug>/ronde-NN/annotations.json`, not
the chat. `tests/run.sh` covers a **subset**. A BLOCKED case never
counts as green. Dated choices: `docs/DECISIONS.md`.

## Out of scope

- Model behaviour (agent pastes the snippet / calls resolve) is not
  enforceable by the suite.
- A sideviewer is allowed, but only via `/p/`, never as `file://`/`data:`.
- Chrome throttling of a real background tab is untested.
- Identifiers stay: `window.LucAnnotator`, `<!-- LUC-ANNOTATOR -->`,
  bridge identity `luc-annotator`, localStorage `luc-annotaties`,
  `LUC_ANNOTATOR_*`. Renaming them orphans existing pages unless a
  migration ships with the rename.

## Functional requirements

<details><summary><strong>B1 — <code>/ping</code> returns 200, CORS <code>*</code>, OPTIONS 204.</strong></summary>

*Expected behaviour:* `GET /ping` answers; any origin is allowed; a
preflight is 204.

*Evidence:* `tests/test_bridge_contract.py`.

*Gap:* no mutation on identity or CORS.

</details>

<details><summary><strong>B2 — <code>/p/</code> outside home is 403.</strong></summary>

*Expected behaviour:* a path that leaves the home directory is refused.

*Evidence:* `tests/test_bridge_contract.py` · `tests/mutate-contract.sh`.

</details>

<details><summary><strong>B3 — POST <code>/session</code> <code>/save</code> <code>/delete</code> <code>/remove-all</code> <code>/resolve</code> <code>/sessie</code> exist; <code>/resolve</code> sets <code>resolved</code> on disk.</strong></summary>

*Expected behaviour:* each route answers; resolve writes `resolved` on
the record.

*Evidence:* `tests/test_bridge_contract.py` · mutate (resolve-noop).

*Gap:* no mutation per remaining route.

</details>

<details><summary><strong>B4 — A round is never overwritten; a new round only after <code>/remove-all</code>.</strong></summary>

*Expected behaviour:* a second save stays in the current round; a new
`ronde-NN` appears only after remove-all.

*Evidence:* `tests/test_bridge_contract.py` · `tests/mutate-contract.sh`.

</details>

<details><summary><strong>B5 — <code>contentHash</code> ignores the annotator block.</strong></summary>

*Expected behaviour:* editing only the snippet does not change the page hash.

*Evidence:* `tests/test_bridge_contract.py` · `tests/mutate-contract.sh`.

</details>

<details><summary><strong>B6 — A crop failure still stores the annotation.</strong></summary>

*Expected behaviour:* when `maak_crop` raises, the JSON record is still written.

*Evidence:* `h_save` with a raising crop (no live Chrome) · mutate.

</details>

<details><summary><strong>B7 — JSON write is atomic (tmp + replace); a dump error leaves the original.</strong></summary>

*Expected behaviour:* a failed dump does not truncate `annotations.json`.

*Evidence:* `tests/test_bridge_contract.py` (direct `schrijf`). Tmp cleanup is B21.

</details>

<details><summary><strong>B8 — <code>toon-annotaties.py --open</code> prints the work rule, expands refs, shows locator.</strong></summary>

*Expected behaviour:* open items include the work rule, resolved refs, and the locator.

*Evidence:* `tests/test_toon.py` · mutate (work rule).

*Gap:* refs and locator are not mutated.

</details>

<details><summary><strong>B9 — Missing refs: do not guess, do warn.</strong></summary>

*Expected behaviour:* `refsIncomplete` asks to save again; the CLI does not invent a target.

*Evidence:* `tests/test_toon.py` · `tests/test_record.py`.

*Gap:* no mutation.

</details>

<details><summary><strong>B10 — Pill self-heals and a later save lands on disk.</strong></summary>

*Expected behaviour:* given a page that is already open while the bridge
is down, when the bridge comes up the pill flips to `X saved` within 10s
without a reload, and a save after that lands in `annotations.json`.
The hidden-panel variant emulates `document.hidden`; it does not
measure Chrome timer throttling (B19).

*Evidence:* `tests/case-02-selfheal.mjs`.

*Gap:* no contract mutation.

</details>

<details><summary><strong>B11 — SessionStart brings the bridge up.</strong></summary>

*Expected behaviour:* given the hooks in `settings.local.json`, a route
exists that starts the bridge without depending on how the agent writes
the file, and the `Edit|Write` route still works. SessionStart covers
Bash writes; the matcher is not widened to every Bash call.

*Evidence:* `tests/case-04-bridge-omhoog-los-van-schrijfroute.sh`.

*Gap:* no contract mutation.

</details>

<details><summary><strong>B12 — <code>ensure-bridge.sh</code> does not lie.</strong></summary>

*Expected behaviour:* given port 8791 held by a non-bridge,
`ensure-bridge.sh` ends with a live answering bridge or a non-zero
exit — never exit 0 while `/ping` is empty. Stale pidfile is removed.

*Evidence:* `tests/case-03-ensure-bridge-eerlijk.sh`.

*Gap:* no contract mutation.

</details>

<details><summary><strong>B13 — A draft edit lands as <code>type: edit</code>.</strong></summary>

*Expected behaviour:* click-edit in a draft card stores `type: edit`
with original, new (both as plain-text projection), `origineelHtml` /
`nieuwHtml`, and a diff that points at the changed span, and survives
reload. No badge, no orphan list.

*Evidence:* `tests/case-05` (draft edit).

*Gap:* no contract mutation.

</details>

<details><summary><strong>B14 — Hunks are independently applicable.</strong></summary>

*Expected behaviour:* each contiguous edit is its own hunk with
surrounding text as the anchor. Hunks apply and resolve independently.
The edit is done only when no hunk is open.

*Evidence:* `tests/case-06-hunks.mjs` · `bin/pas-hunk-toe.py`.

*Gap:* no contract mutation.

</details>

<details><summary><strong>B15 — <code>la-sub*</code> +30px, hook without page CSS.</strong></summary>

*Expected behaviour:* each nest level steps 30px further in, at least
four deep. A child draws a hook on any block element, including a bare
`<li>`. Line colour follows `--line` when set, and stays visible
without it. `--la-stap` moves indent and hook together.

*Evidence:* `tests/case-07`.

*Gap:* no contract mutation.

</details>

<details><summary><strong>B16 — Locator survives a row insert; orphan only when the text is gone; repeated cell text stays on the labeled row.</strong></summary>

*Expected behaviour:* inserting a row above does not move the mark;
deleting the text orphans it; two identical cells keep the mark on the
row the locator named.

*Evidence:* `tests/case-08-locator-tabel.mjs` · `tests/mutate-contract.sh`.

*Gap:* no real client page in the repo.

</details>

<details><summary><strong>B17 — Sideviewer origin.</strong></summary>

*Expected behaviour:* opening a file in the sideviewer is a `data:`
snapshot and cannot reach the bridge. The same page via `/p/` works,
including self-heal.

*Evidence:* `tests/sideview-test.sh` (manual). Measured 2026-08-18.

</details>

<details><summary><strong>B18 — A fresh agent pastes the snippet.</strong></summary>

*Expected behaviour:* a fresh agent asked to ship HTML via Bash starts
the bridge (new pid) and includes the `LUC-ANNOTATOR` marker. All runs
must pass.

*Evidence:* `tests/case-01`. Currently BLOCKED on a spend limit; not in
default `tests/run.sh`.

</details>

<details><summary><strong>[gap]</strong> <s>B19 — Chrome throttling of a real background tab.</s> — untested, leave it.</summary>

*Evidence:* not collected.

</details>

<details><summary><strong>[gap]</strong> <s>B20 — The model pastes the snippet / calls resolve.</s> — not enforceable.</summary>

*Evidence:* not collected.

</details>

<details><summary><strong>B21 — A dump error removes the <code>.tmp</code>.</strong></summary>

*Expected behaviour:* after a failed dump the leftover tmp file is gone.

*Evidence:* `tests/test_bridge_contract.py` · mutate (`os.remove`).

</details>

<details><summary><strong>B22 — A page under <code>/p/</code> on a non-default port talks to that port.</strong></summary>

*Expected behaviour:* when the bridge is not on 8791, the snippet still
posts to the port that served `/p/`.

*Evidence:* `tests/case-08-locator-tabel.mjs` (requires `LUC_ANNOTATOR_PORT`)
· `tests/mutate-contract.sh`.

</details>

<details><summary><strong>B24 — A draft card renders as the mail: lists, bold and links.</strong></summary>

*Expected behaviour:* `.la-draft-txt` shows real `<ul>`/`<ol>` items,
bold, italic and links, and the reviewer applies them from the card's own
toolbar (⌘B/⌘I/⌘K too). The stored `nieuwHtml` uses only
`p, ul, ol, li, b, i, a, br`, so it can go into a mail body as-is. A card
the agent wrote as plain text stays plain until a format button is used.

*Evidence:* `tests/case-13-rijke-concepten.mjs`.

</details>

<details><summary><strong>B25 — Formatting is its own hunk kind, and the text diff stays plain.</strong></summary>

*Expected behaviour:* turning a line into a bullet or a word bold leaves
the plain-text projection untouched and produces a hunk with
`soort: "opmaak"` naming what changed and on which block. Text hunks keep
plain-text anchors clamped to their own block, so `pas-hunk-toe.py` still
places them in the HTML source; it refuses formatting hunks out loud
instead of guessing. Both kinds come back on their anchor after a reload.

*Evidence:* `tests/case-13-rijke-concepten.mjs`; decision in
`docs/DECISIONS.md` (2026-08-28).

</details>

<details><summary><strong>B26 — Checklist state persists per page, outside the rounds.</strong></summary>

*Expected behaviour:* `POST /state-save` with `{component, key, value}`
merges the value over the existing entry, stamps `changedAt` on the entry
and `updatedAt` on the whole, and writes `<slug>/state.json` next to the
`ronde-NN` dirs — never inside one. `POST /state` reads it back; an unknown
page yields empty `components`, a save with no `key` is a 400. Checked
state is a lasting status, not a feedback round: `remove-all` does not
touch it. Snippet: `references/checklist-snippet.html` (LA-CHECKLIST).

*Evidence:* `tests/test_bridge_contract.py`.

</details>

<details><summary><strong>B27 — A LA-SUGGEST "change" is editable, and pending keeps the typed text.</strong></summary>

*Expected behaviour:* opening the ✎ popup for a suggestion that already
carries a `change` decision prefills the comment field with the stored
comment (chips included) and puts the caret behind it; saving replaces the
decision instead of stacking one. Clicking the orange badge still returns
the suggestion to pending, but keeps `comment`/`refs`/`commentExpanded` in
`state.json`, so the text is still there after a reload — the prefill comes
from `POST /state`, not from an in-memory variable. `accepted` and
`rejected` drop the text, so a processing agent never finds a dead change
comment on an accepted key.

*Evidence:* `tests/case-14-suggest-change-bewerken.mjs`; decision in
`docs/DECISIONS.md` (2026-08-31).

</details>

<details><summary><strong>B28 — A suggestion that becomes visible later gets its pill on its own.</strong></summary>

*Expected behaviour:* an element with `data-la-suggest` that is hidden at
load (a collapsed table group, an inline `display:none`) or inserted into
the DOM later shows its rects and pill as soon as it becomes visible — no
other interaction needed, also when the page itself does not resize because
the table sits in its own `overflow:auto` scroller. Redrawing settles: the
layer's own nodes never trigger another redraw.

*Evidence:* `tests/case-15-suggest-zichtbaar.mjs`; decision in
`docs/DECISIONS.md` (2026-08-31).

</details>

<details><summary><strong>B29 — One suggest key is one suggestion with one pill.</strong></summary>

*Expected behaviour:* elements sharing a `data-la-suggest` key are drawn as
one visual group — every rect highlighted — with exactly one pill, because
the decision is stored per key. Elements with different keys keep their own
pill and decide independently: accepting one leaves the other pending, and
`state.json` only carries the key that was clicked.

*Evidence:* `tests/case-16-suggest-gedeelde-key.mjs` ·
`tests/case-17-suggest-losse-keys.mjs`; decision in `docs/DECISIONS.md`
(2026-08-31).

</details>

<details><summary><strong>B23 — Region and text boxes scroll with the HTML they mark, including inside an <code>overflow:auto</code> scroller.</strong></summary>

*Expected behaviour:* after the marked row moves in a nested scroller, the
box and badge sit on that row — not at the same viewport coordinates.
Window-scroll still follows too.

*Evidence:* `tests/case-12-scroll-mee.mjs` (listener mutant included).

</details>

## Architecture

<details><summary><strong>A1 — Root holds only ports.</strong></summary>

*Expected behaviour:* root files are README, SKILL, INSTALL, CRITERIA,
`install.sh`, `.gitignore`. Directories: `annotator/` `bin/`
`references/` `tests/` `docs/`. Snippet lives in `references/`.
Gitignored runtime does not count.

*Evidence:* `tests/test_layout.py`.

</details>

<details><summary><strong>A2 — No <code>memories/</code>. Agent rules live in <code>references/</code>.</strong></summary>

*Evidence:* `tests/test_layout.py`.

</details>

<details><summary><strong>A3 — <code>extras/</code> gone; not installed.</strong></summary>

*Evidence:* `tests/test_layout.py` · `install.sh`.

</details>

<details><summary><strong>A4 — CLIs and hooks live in <code>bin/</code>; install/hooks point there; a <code>bin/&lt;name&gt;.(py|sh)</code> string in agent-facing docs names a file that exists.</strong></summary>

*Evidence:* `tests/test_layout.py` · `tests/mutate-layout.sh` (invented name).

</details>

<details><summary><strong>A5 — Python modules: <code>snake_case</code>. Scripts in <code>bin/</code>: kebab-case.</strong></summary>

*Evidence:* `tests/test_layout.py`.

</details>

<details><summary><strong>A6 — Agent-facing text names no person.</strong></summary>

*Expected behaviour:* allowlist (behaviour): `LucAnnotator`,
`LucAnnotatorBridge`, `LUC-ANNOTATOR`, `luc-annotator`,
`luc-annotaties`, `LUC_ANNOTATOR_*`. Exempt: `docs/DECISIONS.md`.

*Evidence:* `tests/test_layout.py`.

</details>

<details><summary><strong>A7 — B1–B15 plus B16/B21/B22/B23/B24/B25/B26/B27/B28/B29 stay green.</strong></summary>

*Evidence:* `tests/run.sh` (default: 00 02–09 11–17). The suite header
prints `git rev-parse --short HEAD` and a dirty-tree count. Captures
live in `tests/red/ronde-NN-*.txt`; never overwrite an existing ronde.

</details>

<details><summary><strong>A8 — Root ports are English.</strong></summary>

*Expected behaviour:* `SKILL.md`, `README.md`, `INSTALL.md`,
`CRITERIA.md`, and `install.sh` have no Dutch function-word leftovers.
The handbook and the CLI work-rule stay Dutch until a dedicated pass
(`docs/DECISIONS.md`, 2026-08-23).

*Evidence:* `tests/test_layout.py` · `tests/mutate-layout.sh`.

</details>

## Seams

Tests only touch these edges: the bridge HTTP API, the
`toon-annotaties.py` and `pas-hunk-toe.py` CLIs, `ensure-bridge.sh`
exit codes, the snippet via Playwright (cases 02/05/06/07/08), and the
public paths in `bin/` plus root contents.

No tests against internal helpers, no snapshots of whole JSON dumps.

## Release gate

1. `python3 -m compileall -q annotator bin`
2. Hook files live in `bin/`; `install.sh` registers
   `bin/hook-ensure-bridge.sh`.
3. `install.sh` copies no memories; agent rules live in `references/`.
4. Suite: `tests/run.sh` — red if a case fails or BLOCKED is treated as pass.
5. No diff on snippet CSS or English UI strings, except paths into
   `bin/` and comment headers.
