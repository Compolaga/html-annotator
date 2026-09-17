# extras — not part of the skill install

Nothing in this directory is installed by
`python -m html_annotator install-skill`, referenced by `SKILL.md`, or
covered by `CRITERIA.md`. It is kept because it documents behaviour that
still exists in the snippet, or because it is the history of an earlier
pass.

| path | what it is |
|---|---|
| `agent-handbook-extras.md` | handbook parts 5–7 (todo-list spawning, the `la-draft` message card, `la-sub` nesting) |
| `tests/case-05-tracked-changes.mjs` | Playwright case for draft-card tracked changes |
| `tests/case-07-subindentatie.mjs` | Playwright case for `la-sub` indentation |
| `tests/case-13-rijke-concepten.mjs` | Playwright case for rich draft cards |
| `docs/refactor-plan-fase-0-2.md` | superseded plan of the 2026-08 cleanup |
| `docs/reviews/` | a dated review of that pass |

The cases here are not in `tests/run.sh`. To run one by hand:

```bash
cd tests && npm i --no-save playwright-core && cd ..
node extras/tests/case-05-tracked-changes.mjs
```

They may drift: the CSS and JS they test still ship inside
`references/annotator-snippet.html`, but no criterion keeps them green.
Why the line runs here: `docs/SCOPE.md`.
