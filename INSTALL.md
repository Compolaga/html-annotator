# INSTALL

Install this skill so it behaves the same as on the machine it came
from: files, hooks, and the deliver rule. Do not skip steps 2 and 3;
those are what make "the skill is there" into "the skill works".

## Fast path

```bash
git clone https://github.com/Compolaga/html-annotator.git ~/repos/html-annotator
~/repos/html-annotator/install.sh
```

`install.sh` does steps 1–3 and is idempotent. Still do step 4 by hand.
If the script fails (for example no `jq`), follow the steps yourself.

Agent rules live in `SKILL.md` and `references/`. No memories are copied.

## Step 1 — skill on disk

The skill must be reachable as `~/.claude/skills/html-annotator/`. A
symlink to the clone is preferred: an update is one `git pull`.

```bash
ln -s ~/repos/html-annotator ~/.claude/skills/html-annotator
chmod +x ~/.claude/skills/html-annotator/bin/*.sh ~/.claude/skills/html-annotator/bin/*.py
```

If something already sits on that path, do not overwrite it without asking.

## Step 2 — register the two hooks

These keep the bridge up. Without them, someone has to run
`ensure-bridge.sh` by hand, and "why did nothing save" is almost always
"the bridge was down".

In `~/.claude/settings.local.json`, under `hooks`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "<HOME>/.claude/skills/html-annotator/bin/hook-ensure-bridge.sh",
            "timeout": 15,
            "statusMessage": "annotator-bridge check"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "<HOME>/.claude/skills/html-annotator/bin/hook-ensure-bridge.sh",
            "timeout": 15,
            "statusMessage": "annotator-bridge check"
          }
        ]
      }
    ]
  }
}
```

Replace `<HOME>` with the real home path; the hook field does not accept
`~`. If other hooks already sit under `PostToolUse` or `SessionStart`,
append these instead of replacing them.

The empty-matcher SessionStart hook runs on every agent session on the
machine, including sessions that never touch annotations. That is
intentional: one curl per session, and the PostToolUse layer misses an
agent that writes HTML via Bash. If the owner wants it narrower, that
is their choice — do not narrow it unasked.

## Step 3 — deliver rule in the global instructions

The strongest trigger is not in the skill but in the global instructions.
Put a rule like this in `~/.claude/CLAUDE.md`, adapted to how the owner
wants it:

```markdown
## Deliverables

Mails, plans, analyses and other write-ups ship as HTML via the
`html-annotator` skill, not as chat text, so they can take inline and
selection comments.
```

Ask before writing that — it touches every project.

## Upgrading from an older install

Re-run `./install.sh` (or `./install.sh --copy` if the skill is a copy,
not a symlink). `--copy` refreshes `$DOEL`. Without `--copy`, an
existing directory that is not this clone is left alone, and the script
does not register a hook it cannot see.

The old installer placed memories. Those are no longer in this skill.
If they still sit under `~/.claude/projects/*/memory/`, they are:

- `annotator-bridge-autostart.md`
- `html-annotator-standaard.md`

Do not delete them automatically — they are project rules. Remove them
by hand if `references/agent-handbook.md` replaces them.

The hook must point at `bin/hook-ensure-bridge.sh`, not
`hook-ensure-bridge.sh` in the skill root.

## Step 4 — verify

```bash
~/.claude/skills/html-annotator/bin/ensure-bridge.sh
curl -s http://127.0.0.1:8791/ping
```

Expected: `{"ok": true, "bridge": "luc-annotator", "version": 2, ...}`.

Run the suite (Node + Playwright; install once):

```bash
(cd ~/.claude/skills/html-annotator/tests && npm i --no-save playwright-core)
~/.claude/skills/html-annotator/tests/run.sh
```

Two limits, also in `CRITERIA.md`: the fresh-agent case has never been
verified in practice (it reports BLOCKED, not pass), and the hidden-panel
variant emulates `document.hidden` so it tests branch logic, not Chrome
throttling.

The test that counts: make an HTML file with the snippet, open it via
`http://127.0.0.1:8791/p/<path-from-home>`, drag a rectangle, type a
comment, Save. There should now be an `annotations.json` plus a crop
under `~/Desktop/annotaties/<slug>/ronde-01/`.

## Requirements

- **python3** (stdlib is enough) — the bridge runs on it.
- **Chrome or Edge** — for screenshot crops. Found via `ANNOTATOR_CHROME`,
  then PATH, then the usual install paths. Without either, region
  annotations store without a crop.
- **Pillow** (optional) — faster crops.
- **jq** (optional) — only for automatic hook registration.
- **Node** (optional) — only for the test suite.
- Port **8791** must be free. Chosen on purpose: 8080 is often Docker.

## Windows

The bridge itself is plain Python and runs natively on Windows: it
finds Chrome or Edge in the usual places, opens `claude://` links via
the shell, and serves `/p/<path-from-home>` with forward slashes in the
URL and backslashes on disk. CI runs the Python tests and a real
`/save` on `windows-latest`.

What is not native:

- `install.sh`, `bin/ensure-bridge.sh`, `bin/hook-ensure-bridge.sh` and
  `bin/vind-todolijst.sh` are bash. Use **Git Bash** (comes with Git for
  Windows) or **WSL**. The hooks in `settings.local.json` then need a
  command Claude Code can start, for example
  `bash "C:/Users/<you>/.claude/skills/html-annotator/bin/hook-ensure-bridge.sh"`.
  Test that by hand first; hook behaviour on Windows has not been
  verified by the maintainer.
- The scripts look for `python3` first and fall back to `python`, which
  is what Git Bash usually has. Disable the Microsoft Store
  "python3" alias if it gets in the way.
- Symlinks need Developer Mode or admin rights; use `./install.sh --copy`.
- The Playwright suite (`tests/run.sh`) is only exercised on macOS and
  Linux.

Checklist: Python 3 in PATH, Chrome or Edge installed, port 8791 free,
Git Bash or WSL for the shell scripts.

## What this repo deliberately does not ship

- `~/Desktop/annotaties/` — user data, created on first save.
- Skills that `SKILL.md` mentions but that are not in this repo:
  `task-spawnen`, `nieuwe-sessie` (`POST /sessie`), `bericht-sturen`.
  The annotator works without them; say so instead of failing silently.
