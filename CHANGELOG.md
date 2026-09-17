# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims
at [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0rc1] — 2026-09-17

First release candidate as an installable package. Everything below is the
delta against the last state on `main`, which was a personal skill folder with
bash installers and Dutch-named entry points.

### Added

- `pyproject.toml` (hatchling): the distribution is `html-annotator`, the
  console script is `html-annotator`, and `python -m html_annotator` keeps
  working. Runtime dependencies: none (stdlib only); `pip install
  "html-annotator[crops]"` adds Pillow for faster screenshot crops.
- `html-annotator --version` and a `release` field in the bridge `/ping`
  answer. The version lives in exactly one place,
  `html_annotator/__init__.py`, and `pyproject.toml` reads it dynamically.
- The snippets are importable at runtime as
  `html_annotator/snippets/<name>.html` in an installed package, while
  `references/` stays the single source on disk.
- `install-skill` also works from a pip/pipx install: it copies `SKILL.md`,
  `references/` and the `bin/` wrappers into `~/.claude/skills/html-annotator`
  instead of requiring a checkout.
- `bin/show-annotations.py` and `bin/apply-hunk.py`.
- `LICENSE` (MIT, copyright "your-online") and this changelog.
- CI matrix on `ubuntu-latest`, `macos-latest` and `windows-latest`, plus a
  best-effort Playwright job; an end-to-end run on a Linux server.
- Criteria A10 (packaging: installable, `--version`, snippet importable) and
  A11 (one snippet source) in `CRITERIA.md`, covered by `tests/test_layout.py`.

### Changed

- **Scope cut (F0).** Core is snippet + bridge + CLI + handbook, plus the
  checklist and suggest layers. Todo-list spawning, the draft message card and
  `la-sub` moved to `extras/` (their code stays inside the one paste block).
- **One Python CLI (F1).** `install.sh`, `bin/ensure-bridge.sh` and
  `bin/hook-ensure-bridge.sh` are gone; everything runs through
  `python -m html_annotator`. No bash, no jq, so macOS, Linux and Windows take
  the same steps. Pid file and log moved to a per-user state directory.
- **Public names (F3).** `window.HtmlAnnotator` is the API, new embeds write
  the `<!-- HTML-ANNOTATOR v3 -->` … `<!-- /HTML-ANNOTATOR -->` markers, and
  the bridge identifies itself as `"bridge": "html-annotator"` in `/ping`.
- **Language.** The snippet UI, the bridge log lines, the CLI output and the
  work-rule box printed by `show` are English.
- Default annotation root is `~/annotations`; a machine that already uses the
  older folder on the desktop keeps it.

### Deprecated

- The previous page-global object name (still assigned as an alias of
  `window.HtmlAnnotator`), the `LUC_ANNOTATOR_*` environment variables, and
  `bin/toon-annotaties.py` / `bin/pas-hunk-toe.py`. All kept until 1.1; the
  exact names are in the migration table below.

### Removed

- The four bash scripts, the personal todo-list finder, and the installer step
  that placed personal memories.

## Migration from LUC-ANNOTATOR v2

Nothing breaks on upgrade; all of the old names still work.

| what | old | new | status of the old name |
|---|---|---|---|
| env: port | `LUC_ANNOTATOR_PORT` | `HTML_ANNOTATOR_PORT` | deprecated alias, still read |
| env: root | `LUC_ANNOTATOR_ROOT` | `HTML_ANNOTATOR_ROOT` | deprecated alias, still read |
| env: browser | `LUC_ANNOTATOR_CHROME` | `HTML_ANNOTATOR_CHROME` | deprecated alias, still read |
| page API | `window.LucAnnotator` | `window.HtmlAnnotator` | alias assigned by the snippet |
| markers | `<!-- LUC-ANNOTATOR v2 -->` … `<!-- /LUC-ANNOTATOR -->` | `<!-- HTML-ANNOTATOR v3 -->` … `<!-- /HTML-ANNOTATOR -->` | still recognised by the bridge (content hash), the hooks and the tests |
| bridge identity | `"bridge": "luc-annotator"` | `"bridge": "html-annotator"` | changed; check for the new value |
| install | `install.sh` | `python -m html_annotator install-skill` + `install-hooks` | removed |
| show annotations | `bin/toon-annotaties.py` | `html-annotator show` / `bin/show-annotations.py` | deprecated wrapper, still works |
| apply a hunk | `bin/pas-hunk-toe.py` | `html-annotator apply-hunk` / `bin/apply-hunk.py` | deprecated wrapper, still works |

Practical steps on an existing machine:

1. `git pull`, then `python -m html_annotator install-skill` and
   `python -m html_annotator install-hooks` — both idempotent; the hook entries
   from the bash era are replaced, not duplicated.
2. Existing pages keep their `LUC-ANNOTATOR` block and keep working. Re-embed
   only when you want the new markers; do not mix two blocks in one page.
3. Scripts that grep `/ping` for `luc-annotator` must look for
   `html-annotator` instead.

[1.0.0rc1]: https://github.com/your-online/html-annotator/releases/tag/v1.0.0rc1
