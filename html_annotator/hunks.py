#!/usr/bin/env python3
"""Applies single blocks of an edit to the page they belong to.

That way an edit does not have to be taken over as a whole: if block 1 is fine
and block 2 still raises a question, only block 1 goes in.

  python -m html_annotator apply-hunk <json> --nr 1               all open blocks
  python -m html_annotator apply-hunk <json> --nr 1 --hunks 2,3   only these
  python -m html_annotator apply-hunk <json> --nr 1 --dry-run     show only
  python -m html_annotator apply-hunk <json> --nr 1 --resolve     and resolve them

Placing happens on the surrounding text, not on a position. A character or line
number stops being true as soon as anything above the change moves; the words
around the block find it back in a changed document too. That is the same reason
`patch` still places a hunk whose line number shifted.

Three attempts per block, strict to lenient, and the attempt that worked is in
the output so you can see how certain the placement was:
  1. before + removed + after  — full context, no doubt possible
  2. before + removed          — left side only; enough when it is unique
  3. removed                   — bare, and only when it occurs exactly once
If none of the three works, nothing happens for that block and the script says why.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from . import config


def laad(pad):
    p = Path(os.path.expanduser(pad))
    if not p.is_file():
        sys.exit("not found: %s" % p)
    with p.open(encoding="utf-8") as f:
        return str(p), json.load(f)


def plaats(tekst, hunk):
    """Returns (new_text, how) or (None, reason)."""
    voor = hunk.get("voor") or ""
    na = hunk.get("na") or ""
    weg = hunk.get("verwijderd") or ""
    erbij = hunk.get("toegevoegd") or ""

    pogingen = [
        ("full context", voor + weg + na, voor + erbij + na),
        ("left context", voor + weg, voor + erbij),
    ]
    if weg:
        pogingen.append(("bare", weg, erbij))

    for manier, zoek, vervang in pogingen:
        if not zoek:
            continue
        aantal = tekst.count(zoek)
        if aantal == 1:
            return tekst.replace(zoek, vervang, 1), manier
        if aantal > 1 and manier != "bare":
            # several hits with context is suspicious; try the next attempt
            continue
    if not weg and not voor and not na:
        return None, "block has no anchor and no text"
    return None, "anchor not found back (or not unique) in the page"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m html_annotator apply-hunk")
    ap.add_argument("json")
    ap.add_argument("--nr", type=int, required=True, help="annotation number")
    ap.add_argument("--hunks", default="", help="comma separated blocks; empty = all open")
    ap.add_argument("--file", dest="file", default="",
                    help="target file; defaults to pageFile from the round")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="write nothing")
    ap.add_argument("--resolve", action="store_true",
                    help="resolve the blocks that were placed")
    ap.add_argument("--port", type=int, default=config.port())
    a = ap.parse_args(argv)

    json_pad, data = laad(a.json)
    ann = next((x for x in data.get("annotations", []) if x.get("nr") == a.nr), None)
    if not ann:
        sys.exit("annotation %d not found in %s" % (a.nr, json_pad))
    if ann.get("type") != "edit":
        sys.exit("annotation %d is not an edit but '%s'" % (a.nr, ann.get("type")))

    alle = ann.get("hunks") or []
    if not alle:
        sys.exit("annotation %d has no blocks; this is an older edit without "
                 "hunks — take 'nieuw' over as a whole" % a.nr)

    gevraagd = [int(x) for x in a.hunks.split(",") if x.strip()] if a.hunks else None
    doel_hunks = [h for h in alle
                  if (gevraagd is None and not h.get("resolved")) or
                     (gevraagd is not None and h.get("n") in gevraagd)]
    if not doel_hunks:
        sys.exit("no blocks to apply (everything resolved already?)")

    bestand = os.path.expanduser(a.file or data.get("pageFile") or "")
    if not bestand or not os.path.isfile(bestand):
        sys.exit("target file not found: %s" % (bestand or "(no pageFile in the round)"))

    with open(bestand, encoding="utf-8") as f:
        tekst = f.read()

    gelukt, mislukt = [], []
    for h in doel_hunks:
        if h.get("soort") == "opmaak":
            # A formatting change is not in the text, so search-and-replace cannot
            # place it: the shape of a line lives in the HTML around it. The script
            # leaves it alone and says what has to happen.
            print("  block %s  SKIPPED  formatting: %s"
                  % (h.get("n"), h.get("omschrijving") or "changed"))
            print("            take the formatting from 'nieuwHtml' on annotation %d" % a.nr)
            mislukt.append(h.get("n"))
            continue
        nieuw, manier = plaats(tekst, h)
        label = "%s -> %s" % (
            (h.get("verwijderd") or "(nothing)").replace("\n", "\\n")[:45],
            (h.get("toegevoegd") or "(nothing)").replace("\n", "\\n")[:45])
        if nieuw is None:
            print("  block %s  FAILED   %s  [%s]" % (h.get("n"), label, manier))
            mislukt.append(h.get("n"))
        else:
            tekst = nieuw
            print("  block %s  placed  %s  [via %s, paragraph %s]"
                  % (h.get("n"), label, manier, h.get("alinea")))
            gelukt.append(h.get("n"))

    if a.dry_run:
        print("\ndry run; %s is not changed" % bestand)
        return 0

    if gelukt:
        with open(bestand, "w", encoding="utf-8") as f:
            f.write(tekst)
        print("\n%d of %d blocks applied in %s" % (len(gelukt), len(doel_hunks), bestand))
    if mislukt:
        print("not placed: %s — check whether the text changed in the meantime"
              % ", ".join(str(x) for x in mislukt))

    if a.resolve and gelukt:
        body = json.dumps({"jsonPath": json_pad, "nrs": [a.nr], "hunks": gelukt}).encode()
        req = urllib.request.Request(config.base_url(a.port) + "/resolve", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                uit = json.load(r)
            print("resolved: blocks %s; still open in this round: %s annotations, %s blocks"
                  % (uit.get("hunksResolved"), uit.get("open"), uit.get("hunksOpen")))
        except Exception as e:
            print("resolving failed (%s); do it with POST /resolve" % e)

    return 1 if mislukt else 0
