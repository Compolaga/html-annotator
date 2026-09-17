# html-annotator

Visual HTML annotation skill for fast iteration in agentic work. Every
HTML page an agent ships becomes annotatable. Feedback lands as JSON
plus crops on disk.

No libraries, no CDN. One pasteable snippet and a local Python bridge
(stdlib). One CLI, `python -m html_annotator`, on macOS, Linux and
Windows — no bash, no jq.

## Start here

1. Read [INSTALL.md](INSTALL.md); it is two commands.
2. Start the bridge: `python -m html_annotator ensure`.
3. Check: `python -m html_annotator status`.
4. Open pages only via `http://127.0.0.1:8791/p/<path-from-home>`
   (`python -m html_annotator url <file>` prints that link).
5. Agent behaviour: [SKILL.md](SKILL.md) + required [references/agent-handbook.md](references/agent-handbook.md).
6. What is core and what is not: [docs/SCOPE.md](docs/SCOPE.md).
7. Criteria and what green means: [CRITERIA.md](CRITERIA.md) · `tests/run.sh`.
8. Why something is that way: [docs/DECISIONS.md](docs/DECISIONS.md).

Teardown: `python -m html_annotator stop`, then drop the hooks from
`~/.claude/settings.local.json` (a backup sits next to the file) and
remove `~/.claude/skills/html-annotator`.

## How it works

```
HTML page  ──►  references/annotator-snippet.html
                   fetch 127.0.0.1:8791
                        ▼
                python -m html_annotator serve
                        ▼
      ~/annotations/<page>/ronde-NN/annotations.json
```

Open pages via `http://127.0.0.1:8791/p/<path-from-home>`, not via
`file://` or a preview pane. A `data:` origin cannot reach loopback.

## Install

```bash
git clone https://github.com/Compolaga/html-annotator.git ~/repos/html-annotator
cd ~/repos/html-annotator
python -m html_annotator install-skill      # --copy on Windows
python -m html_annotator install-hooks
```

Details: [INSTALL.md](INSTALL.md).

## Commands

| command | role |
|---|---|
| `serve` | bridge in the foreground |
| `ensure` | start it detached if it is not answering (idempotent) |
| `stop` · `status` | stop it · print `/ping` |
| `show [page] [--open\|--list\|--search X\|--since N]` | open annotations |
| `resolve <slug\|json> --nrs 1,2` | mark annotations as processed |
| `apply-hunk <json> --nr 1 --hunks 2` | apply one block of a draft edit |
| `url <file>` | the `/p/` link for a local file |
| `install-skill` · `install-hooks` | install, both idempotent |

## What's in here

| path | role |
|---|---|
| `SKILL.md` | agent port (embed, `/p/`, `.`) |
| `CRITERIA.md` | acceptance criteria |
| `references/` | handbook, snippet, record schema |
| `html_annotator/` | Python package (CLI, bridge, config) |
| `bin/` | thin wrappers for the hooks and older shortcuts |
| `docs/` | scope, decisions |
| `extras/` | not part of the skill install (see `extras/README.md`) |
| `tests/` | suite |

## Limits

- Python tests run on macOS, Linux and Windows in CI; the Playwright
  suite is only exercised on macOS and Linux.
- Default annotation root: `~/annotations`. A machine that already uses
  the older `annotaties` folder on the Desktop keeps it, so an upgrade
  orphans nothing.
- Two blind spots in the suite: see CRITERIA.md (B18, B19).
