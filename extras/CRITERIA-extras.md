# Criteria for the extras (not part of the skill contract)

B13, B15, B24 and B25 covered the draft message card (`la-draft`) and the
nested sub-points (`la-sub`). Both moved out of scope in the F0 pass
(`docs/SCOPE.md`): their CSS and JS still ship inside the snippet, but no
criterion keeps them green and their Playwright cases live in
`extras/tests/`. Kept verbatim so a later pass can pick them up again.

<details><summary><strong>B13 — A draft edit lands as <code>type: edit</code>.</strong></summary>

*Expected behaviour:* click-edit in a draft card stores `type: edit`
with original, new (both as plain-text projection), `origineelHtml` /
`nieuwHtml`, and a diff that points at the changed span, and survives
reload. No badge, no orphan list.

*Evidence:* `tests/case-05` (draft edit).

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

