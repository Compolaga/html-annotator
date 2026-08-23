# Decisions

Choices a later cleanup must not reopen without the owner.
Changing behaviour is a new decision, not an edit here.

## 2026-08-18 — SessionStart hook always on

The bridge hook runs at user level on every agent session (empty
matcher). PostToolUse stays limited to `Edit|Write` on HTML with
`LUC-ANNOTATOR`. Do not narrow it: the bridge should be listening.

## 2026-08-18 — Pages via `/p/`, not `file://` or a preview pane

A `data:` origin cannot reach loopback (Private Network Access).
Deliver as `http://127.0.0.1:8791/p/<path-from-home>`.

## 2026-08-18 — Origin log stays on

Every bridge request logs `origin=` to stderr / `bridge.log`.

## 2026-08-23 — No Remove-all in the UI

`POST /remove-all` still exists. The button is gone. Rounds close only
through that endpoint, not through a page change.

## 2026-08-23 — English UI copy, status pill `X saved`

User-visible annotator strings are English. The pill shows the number
of open annotations, without a `round N -` prefix.

## 2026-08-23 — Paste block stays one file

`references/annotator-snippet.html` is the only thing that goes at the
bottom of HTML. No bundler, no split runtime JS until the output is
byte-identical.

## 2026-08-23 — Install without personal memories

`install.sh` does not install memories. Agent rules live in `SKILL.md`
and `references/`. Existing project `MEMORY.md` rules are not deleted.
`extras/luc-memories/` was removed (the plan said move). Source: this
cleanup, "it may change drastically". Content remains in git at
`472cf63`.

## 2026-08-23 — Locator follows the row, not the first repeated span

`zoekAnker` no longer treats "start span still exists" as processed.
The label comes from the start row; `zoekHostViaLabel` / `laHostPast`
keep repeated cell text on that row. Source: Reconi owners, 2026-08-23.
No Reconi page in the suite — case-08 is the reduced form.

## 2026-08-23 — Root is a port, CLIs in bin/

CLIs and hooks live in `bin/`. Python library in `annotator/`
(snake_case). `ensure-bridge.sh` and `hook-ensure-bridge.sh` are
location-relative. Agent-facing docs name no person;
`window.LucAnnotator` and the `LUC-ANNOTATOR` marker stay (public API).

## 2026-08-23 — Criteria at root, decisions in docs

`CRITERIA.md` is the contract (criterion, expected behaviour, evidence).
Dated lab notes live in `tests/red/`. Binding choices live in this file.
