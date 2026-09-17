"""Shows open annotations, so nobody has to write an ad-hoc script for it.

Usage (through the CLI):
  python -m html_annotator show --open        the page annotated most recently
  python -m html_annotator show todos         last round of that page
  python -m html_annotator show todos 8       round 8
  python -m html_annotator show --list        pages with open annotations, compact
  python -m html_annotator show --search x    pages whose name contains that term
  python -m html_annotator show --all         every page, every round, counts only

Without a page name the script picks one itself: the most recently changed page
with open annotations, within a 7-day window. Older work stays on disk and is
findable with --list or --search, but never lands in context unasked: that saves
thousands of tokens per call.

Extra flags:
  --resolved   also show annotations that were processed (hidden by default)
  --paths      print absolute paths to the json and the screenshot crops
  --since N    widen the window to N days (--since 0 = no window)
"""

import json
import os
import re
import sys
import time

from . import config
from .refs import expand_comment, validate_refs

ROOT = str(config.root())

if hasattr(sys.stdout, "reconfigure"):  # the Windows console is not UTF-8 by default
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Printed whenever something is still open. It lives here and not only in
# SKILL.md, so it always reaches the context of whoever processes this feedback.
WERKREGEL = """
╭─ For the agent: understand first, process second ──────────────────
│ A bare "." message means "process my annotations", not a typo.
│ Do not ask for confirmation; just follow this flow.
│
│ Do not apply these annotations blindly. They are often dictated, so
│ sentences run dead and context that was obvious to the reviewer is
│ missing.
│
│ Walk through them one by one and ask yourself, per annotation:
│   · Do I understand what is meant, or am I filling it in? If you
│     fill it in, ask.
│   · Can this go more than one way? Put the readings to the reviewer,
│     do not pick one yourself.
│   · Do I disagree, or do I see a consequence that is not mentioned?
│     Say so, with your reason.
│   · Is it too vague to act on? Keep asking until it is sharp.
│   · Does it contradict something said earlier? Name it.
│
│ If there are choices in it, ask them clickably with AskUserQuestion.
│ In doubt about whether to ask: ask. Guessing wrong costs more time
│ than a question.
│
│ Only then process, and check off what is done via POST /resolve.
╰────────────────────────────────────────────────────────────────────
"""


def rondes(pagina):
    d = os.path.join(ROOT, pagina)
    if not os.path.isdir(d):
        return []
    uit = []
    for naam in sorted(os.listdir(d)):
        f = os.path.join(d, naam, "annotations.json")
        if re.match(r"^ronde-\d+$", naam) and os.path.isfile(f):
            uit.append((int(naam.split("-")[1]), f))
    return uit


def paginas():
    if not os.path.isdir(ROOT):
        return []
    return sorted(p for p in os.listdir(ROOT)
                  if os.path.isdir(os.path.join(ROOT, p)) and rondes(p))


def laad(f):
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


VENSTER_DAGEN = 7


def open_info(pagina):
    """(number of open annotations, mtime of the most recently changed round)."""
    n, mt = 0, 0.0
    for _, f in rondes(pagina):
        try:
            d = laad(f)
        except (OSError, ValueError):
            continue
        n += len([a for a in d.get("annotations", []) if not a.get("resolved")])
        mt = max(mt, os.path.getmtime(f))
    return n, mt


def kandidaten(ps, alleen_open, venster_dagen):
    """Pages that qualify, newest first.

    Without a window every call would show the whole history; with one, only
    recent work shows up. That sidesteps the question of when a round is
    "done": unresolved work from weeks ago ages out of the default by itself.
    """
    grens = time.time() - venster_dagen * 86400 if venster_dagen else 0
    uit = []
    for p in ps:
        n, mt = open_info(p)
        if alleen_open and not n:
            continue
        if mt < grens:
            continue
        uit.append((p, n, mt))
    uit.sort(key=lambda r: r[2], reverse=True)
    return uit


def datum(mt):
    return time.strftime("%d-%m", time.localtime(mt)) if mt else "?"


def toon(f, nr, alleen_open, ook_resolved, paden):
    d = laad(f)
    anns = d.get("annotations", [])
    open_n = [a for a in anns if not a.get("resolved")]
    res_n = [a for a in anns if a.get("resolved")]

    kop = "ronde-%02d  %d annotations" % (nr, len(anns))
    if res_n:
        kop += "  (%d open, %d resolved)" % (len(open_n), len(res_n))
    if d.get("closed"):
        kop += "  [closed]"
    print("\n" + kop)
    print("-" * len(kop))
    if paden:
        print(f)

    tonen = open_n if (alleen_open or not ook_resolved) else anns
    if ook_resolved:
        tonen = anns
    if not tonen:
        print("  (nothing open)")
        return
    if open_n:
        print(WERKREGEL)

    map_ = os.path.dirname(f)
    for a in tonen:
        vlag = " ✓resolved" if a.get("resolved") else ""
        print("\n  [%s] %s%s" % (a.get("nr"), a.get("type", "?"), vlag))
        doel = a.get("target") or ""
        if doel:
            print("      on     : %s" % doel[:100])
        if a.get("selectedText"):
            print("      select : %s" % a["selectedText"][:120])
        loc = a.get("locator") or {}
        if loc.get("path") or loc.get("start"):
            pad = loc.get("path") or (loc.get("start") or {}).get("path") or ""
            print("      locator: %s%s" % (pad[:100],
                  ("  [nth %s]" % loc["nth"]) if loc.get("nth") else ""))
            if loc.get("label") and loc.get("label") != a.get("selectedText"):
                print("      context: %s" % loc["label"][:120])
        if a.get("type") == "edit":
            # The reviewer rewrote the text. The diff answers "what should be
            # different": - is out, + is in. The full new text follows, so it can be
            # taken over without applying the changes one by one.
            if (a.get("veld") or "") != (a.get("target") or ""):
                print("      field  : %s" % (a.get("veld") or "?"))
            hunks = a.get("hunks") or []
            if hunks:
                # Per block, so they can be judged and applied separately. The
                # paragraph number is there to refer to; the anchor is the text around it.
                for h in hunks:
                    vlag = " (resolved)" if h.get("resolved") else ""
                    if h.get("soort") == "opmaak":
                        # Formatting is not in the text, so there is nothing to
                        # replace: this block says what happened to the shape of a line.
                        print("      block %s, formatting%s: %s"
                              % (h.get("n"), vlag, h.get("omschrijving") or "changed"))
                        if h.get("blok"):
                            print("        on: %s" % h["blok"].replace("\n", " ")[:100])
                        continue
                    print("      block %s, paragraph %s%s"
                          % (h.get("n"), h.get("alinea"), vlag))
                    if h.get("verwijderd"):
                        print("        - %s" % h["verwijderd"].replace("\n", " ")[:100])
                    if h.get("toegevoegd"):
                        print("        + %s" % h["toegevoegd"].replace("\n", " ")[:100])
                    context = (h.get("voor") or "").replace("\n", " ")[-40:]
                    if context.strip():
                        print("          follows: ...%s" % context.strip())
                print("      apply: python -m html_annotator apply-hunk <json> --nr %s --hunks <n>" % a.get("nr"))
                if any(h.get("soort") == "opmaak" for h in hunks):
                    print("      note: the script does not apply formatting blocks — take"
                          " the formatting from 'new HTML' below")
            else:
                for o in a.get("diff") or []:
                    if o.get("op") == "=":
                        continue
                    teken = "-" if o.get("op") == "-" else "+"
                    for regel in (o.get("t") or "").splitlines() or [""]:
                        if regel.strip():
                            print("      %s %s" % (teken, regel.strip()[:110]))
            nieuwe = a.get("nieuw") or ""
            if nieuwe:
                print("      new text:")
                for regel in nieuwe.splitlines():
                    print("        | %s" % regel[:110])
            # The full new version including formatting, mail-safe (p/ul/ol/li/b/i/a/br).
            # This is the ground truth when both text and formatting changed.
            if a.get("nieuwHtml"):
                print("      new HTML:")
                print("        | %s" % a["nieuwHtml"][:600])
        if a.get("image"):
            pad = os.path.join(map_, a["image"])
            print("      crop   : %s%s" % (pad if paden else a["image"],
                                           "" if os.path.isfile(pad) else "  (MISSING)"))
        for i, regel in enumerate(expand_comment(a.get("comment", ""), a.get("refs")).split("\n")):
            print("      %s %s" % ("says   :" if i == 0 else "        ", regel))
        refs = a.get("refs") or []
        missing, unused = validate_refs(a.get("comment", ""), refs)
        if missing:
            print("      refs   : MISSING in JSON: %s" % ", ".join(missing))
        if unused:
            print("      refs   : not in comment: %s" % ", ".join(unused))
        if refs:
            for r in refs:
                rid = r.get("id") or "?"
                tekst = (r.get("selectedText") or "").replace("\n", " ")
                print("      ref %s: %s" % (rid, tekst[:120]))
        elif a.get("comment") and "\u27e6" in a.get("comment", ""):
            print("      refs   : markers in comment but no refs array \u2014 save again")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    vlaggen = {a for a in argv if a.startswith("--")}
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--since" and i + 1 < len(argv):
            i += 2
            continue
        if a == "--search" and i + 1 < len(argv):
            i += 2
            continue
        if not a.startswith("--"):
            args.append(a)
        i += 1

    def waarde(vlag, standaard):
        if vlag in argv:
            k = argv.index(vlag)
            if k + 1 < len(argv):
                return argv[k + 1]
        return standaard

    alleen_open = "--open" in vlaggen
    ook_resolved = "--resolved" in vlaggen
    paden = "--paths" in vlaggen
    zoekterm = waarde("--search", None)
    try:
        venster = int(waarde("--since", VENSTER_DAGEN))
    except ValueError:
        venster = VENSTER_DAGEN

    ps = paginas()
    if not ps:
        print("No annotations found in %s" % ROOT)
        return 1

    if zoekterm or "--list" in vlaggen:
        rijen = kandidaten(ps, alleen_open or not zoekterm, 0)
        if zoekterm:
            rijen = [r for r in rijen if zoekterm.lower() in r[0].lower()]
        if not rijen:
            print("Nothing found%s." % (" for '%s'" % zoekterm if zoekterm else ""))
            return 1
        kop = "pages matching '%s'" % zoekterm if zoekterm else "pages with open annotations"
        print("%s (%d):" % (kop, len(rijen)))
        for naam, n, mt in rijen[:40]:
            print("  %-52s %3d open  %s" % (naam, n, datum(mt)))
        if len(rijen) > 40:
            print("  ... %d more, narrow it down with --search" % (len(rijen) - 40))
        return 0

    if "--all" in vlaggen:
        for p in ps:
            print("\n=== %s" % p)
            for nr, f in rondes(p):
                d = laad(f)
                anns = d.get("annotations", [])
                o = len([a for a in anns if not a.get("resolved")])
                print("  ronde-%02d  %2d annotations, %d open%s"
                      % (nr, len(anns), o, "  [closed]" if d.get("closed") else ""))
        return 0

    rest = []
    if args:
        pagina = args[0]
        if pagina not in ps:
            treffers = [p for p in ps if pagina.lower() in p.lower()]
            if len(treffers) == 1:
                pagina = treffers[0]
            elif not treffers:
                print("Unknown page '%s'. Search with: --search %s" % (pagina, pagina))
                return 1
            else:
                print("'%s' matches %d pages:" % (pagina, len(treffers)))
                for t in treffers[:15]:
                    print("  %s" % t)
                if len(treffers) > 15:
                    print("  ... %d more" % (len(treffers) - 15))
                return 1
    else:
        rijen = kandidaten(ps, alleen_open, venster)
        if not rijen and alleen_open:
            # Nothing open is not an error: say it briefly and exit 0.
            binnen = " (last %d days)" % venster if venster else ""
            ouder = kandidaten(ps, True, 0)
            print("(nothing open)%s" % binnen)
            if ouder:
                print("%d page%s with older open annotations  ->  --list"
                      % (len(ouder), "s" if len(ouder) != 1 else ""))
            return 0
        if not rijen:
            print("No annotations in the last %d days. Older work: --list or --search <term>."
                  % venster if venster else "No annotations found.")
            return 1
        pagina = rijen[0][0]
        rest = rijen[1:]

    rs = rondes(pagina)
    print("=== %s  (%d rounds)" % (pagina, len(rs)))
    if len(args) > 1:
        gevraagd = int(args[1])
        rs = [(n, f) for n, f in rs if n == gevraagd]
        if not rs:
            print("ronde-%02d does not exist" % gevraagd)
            return 1
    else:
        rs = rs[-1:]

    for nr, f in rs:
        toon(f, nr, alleen_open, ook_resolved, paden)

    if rest:
        namen = ", ".join("%s (%d)" % (n, o) for n, o, _ in rest[:3])
        extra = ", ..." if len(rest) > 3 else ""
        binnen = " within %d days" % venster if venster else ""
        print("\n%d more page%s with open annotations%s: %s%s   ->  --list for all"
              % (len(rest), "s" if len(rest) != 1 else "", binnen, namen, extra))
    return 0
