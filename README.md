# html-annotator

Visual HTML annotation skill for fast iteration in agentic work. Every
HTML page an agent ships becomes annotatable. Feedback lands as JSON
plus crops on disk.

No libraries, no CDN. One pasteable snippet and a local Python bridge
(stdlib).

## Start here

1. Read [INSTALL.md](INSTALL.md) and run `./install.sh` (or `--copy`).
2. Start the bridge: `~/.claude/skills/html-annotator/bin/ensure-bridge.sh`.
3. Check: `curl -s http://127.0.0.1:8791/ping`.
4. Open pages only via `http://127.0.0.1:8791/p/<path-from-home>`.
5. Agent behaviour: [SKILL.md](SKILL.md) + required [references/agent-handbook.md](references/agent-handbook.md).
6. What green means: [VERIFICATION.md](VERIFICATION.md) · `tests/run.sh`.
7. Criteria: [CRITERIA.md](CRITERIA.md). Why something is that way: [docs/DECISIONS.md](docs/DECISIONS.md).

Teardown: hooks live in `~/.claude/settings.local.json` (backup next to
the file). Skill symlink: `~/.claude/skills/html-annotator`.

## How it works

```
HTML page  ──►  references/annotator-snippet.html
                   fetch 127.0.0.1:8791
                        ▼
                bin/annotator-bridge.py
                        ▼
      ~/Desktop/annotaties/<page>/ronde-NN/annotations.json
```

Open pages via `http://127.0.0.1:8791/p/<path-from-home>`, not via
`file://` or a preview pane. A `data:` origin cannot reach loopback.

## Install

```bash
git clone https://github.com/Compolaga/html-annotator.git ~/repos/html-annotator
~/repos/html-annotator/install.sh
```

The script links the skill and registers the hooks. Details:
[INSTALL.md](INSTALL.md).

## What's in here

| path | role |
|---|---|
| `SKILL.md` | agent port (embed, `/p/`, `.`) |
| `CRITERIA.md` | acceptance criteria |
| `references/` | handbook, snippet, record schema |
| `annotator/` | Python library (config, record, refs) |
| `bin/` | bridge, ensure/hook, show, hunks, todo list |
| `tests/` | suite |

## Limits

- macOS is the tested environment.
- `~/Desktop/annotaties` and `bin/find-todo-list.sh` → Desktop stay the default.
- Two blind spots in the suite: see VERIFICATION.md / INSTALL.md step 4.
