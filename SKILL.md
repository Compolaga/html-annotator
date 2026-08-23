---
name: html-annotator
description: >
  Visual HTML annotation skill for fast iteration in agentic work.
  Embed the annotation snippet in every HTML deliverable (prototypes,
  slides, comparison pages, dashboards) without being asked. Also
  trigger when processing feedback: a bare "." (period only),
  "process my feedback", or a path to annotations.json / an annotation
  round — then this skill describes how to read and process rounds and
  screenshot crops.
---

# HTML annotator: embed + process feedback

**Read `references/agent-handbook.md` before you act.** It covers the
bridge, rounds, processing (`.` / resolve / refs / locators / hunks),
todo-list spawn, draft cards (`la-draft`) and `la-sub`. This file is
only the port: embed, start the bridge, `/p/` URL, plus the short
process trigger.

Criteria (and what must stay green): `CRITERIA.md`. Dated choices: `docs/DECISIONS.md`. Install: `INSTALL.md`.

## Part 1: embed (every HTML deliverable)

Paste the full contents of `references/annotator-snippet.html` at the
bottom of every HTML file, just before `</body>` or at the end of the
file. The block runs from `<!-- LUC-ANNOTATOR v2 -->` to
`<!-- /LUC-ANNOTATOR -->`.

On an existing page:
- `LUC-ANNOTATOR v2` already present: do nothing;
- older block (`LUC-ANNOTATOR v1`, no end marker): replace everything
  from `<!-- LUC-ANNOTATOR` through the matching `</script>` with the
  new block;
- nothing there: append at the bottom.

Self-contained: no libraries, no CDN, no external fonts. Works on
`file://` and localhost.

**Always start the bridge afterwards.** One command, idempotent, so
call it blindly on every deliverable and every update of a page that
already has the snippet:

```bash
~/.claude/skills/html-annotator/bin/ensure-bridge.sh
```

If it is already running, the script does nothing. If not, it starts
the bridge detached from your shell (nohup), writes the pid to
`bridge.pid` and output to `bridge.log` in the skill directory, and
waits until it answers (max 5 seconds). Never skip this: without the
bridge, feedback lands in localStorage and nothing is on disk.

**Safety net, two layers.** Both run `bin/hook-ensure-bridge.sh` from
this skill (log: `bridge-hook.log`), registered in
`~/.claude/settings.local.json`:

- **SessionStart** — one call per session, regardless of how that
  session later writes HTML. This is the layer that counts: the
  PostToolUse layer misses an agent that writes the file via Bash, and
  in auto-mode Bash is the prescribed route.
- **PostToolUse on `Edit|Write`** — if the written file is `.html`/`.htm`
  with the `LUC-ANNOTATOR` marker, the bridge comes up.

The matcher is not widened to `Bash`, because that would fire on every
Bash call in every project. What the chosen route does: the
SessionStart registration is user-level with an empty matcher, so it
runs at the start of every agent session on this machine, including
sessions that never touch annotations. That is one curl per session,
and nothing more if the bridge is already listening. The choice lives
in `docs/DECISIONS.md` (2026-08-18). Do not narrow it without a new decision.

**Self-heal in the page.** The snippet does not check the bridge once
on load; it retries every 3 seconds until it answers (plus on
`visibilitychange` and `focus`). If the bridge comes up later — via
the hook, or by hand — the status pill flips on its own and no reload
is needed.

Verification: `tests/run.sh`, criteria in `CRITERIA.md`. Two known
gaps: (1) the fresh-agent case is BLOCKED; (2) the hidden-panel
variant emulates `document.hidden`, not Chrome throttling.

**Always open the page through the bridge, never via `file://` or a
preview pane.** The bridge serves local files on `GET /p/<path-from-home>`:

```
~/Desktop/todos.html
→ http://127.0.0.1:8791/p/Desktop/todos.html
```

Build: absolute path, strip the home directory, put the rest after
`http://127.0.0.1:8791/p/`. Paths outside home → 403. A preview pane
as `data:` can never reach loopback (Private Network Access). Via
`/p/` the page is same-origin with the bridge.

What the reviewer can do (behaviour unchanged; details in the handbook):
- drag a region, select text, link text (chips), Save;
- status pill `X saved` or `bridge off - localStorage only`;
- orphan list **"N likely processed"**;
- no download button, no Remove-all in the UI.

Test/debug API: `window.LucAnnotator.add({type:'region'|'text', rect,
comment, selectedText})`, `.anns()`, `.bridge()`, `.session()`,
`.resolve(annotation)`.

## Processing (short port)

Triggers — do not ask for confirmation:

- a bare **`.`** (period only, surrounding whitespace is fine);
- "process my feedback" / a path to `annotations.json` or a round.

On `.`, find the open round yourself (`bin/show-annotations.py --open`
or the bridge). Understand first, then apply, then `POST /resolve`.
Read `references/agent-handbook.md` (part 4) for refs, locators, hunks,
crops. `bin/show-annotations.py` reprints the work rule whenever
something is still open.
