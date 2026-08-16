#!/usr/bin/env python3
"""Toont Lucs annotaties, zodat je daar geen ad-hoc script meer voor schrijft.

Gebruik:
  toon-annotaties.py                    laatste ronde van de enige/laatste pagina
  toon-annotaties.py todos-uit-mail     laatste ronde van die pagina
  toon-annotaties.py todos-uit-mail 8   ronde 8
  toon-annotaties.py --alles            elke pagina, elke ronde, alleen tellingen
  toon-annotaties.py --open             alleen nog niet resolved annotaties

Extra vlaggen:
  --resolved   toon ook de al afgehandelde annotaties (standaard verborgen)
  --paden      print de absolute paden naar json en screenshot-crops
"""

import json
import os
import re
import sys

ROOT = os.path.expanduser("~/Desktop/annotaties")


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
    with open(f) as fh:
        return json.load(fh)


def toon(f, nr, alleen_open, ook_resolved, paden):
    d = laad(f)
    anns = d.get("annotations", [])
    open_n = [a for a in anns if not a.get("resolved")]
    res_n = [a for a in anns if a.get("resolved")]

    kop = "ronde-%02d  %d annotaties" % (nr, len(anns))
    if res_n:
        kop += "  (%d open, %d resolved)" % (len(open_n), len(res_n))
    if d.get("closed"):
        kop += "  [gesloten]"
    print("\n" + kop)
    print("-" * len(kop))
    if paden:
        print(f)

    tonen = open_n if (alleen_open or not ook_resolved) else anns
    if ook_resolved:
        tonen = anns
    if not tonen:
        print("  (niets open)")
        return

    map_ = os.path.dirname(f)
    for a in tonen:
        vlag = " ✓resolved" if a.get("resolved") else ""
        print("\n  [%s] %s%s" % (a.get("nr"), a.get("type", "?"), vlag))
        doel = a.get("target") or ""
        if doel:
            print("      op     : %s" % doel[:100])
        if a.get("selectedText"):
            print("      select : %s" % a["selectedText"][:120])
        if a.get("image"):
            pad = os.path.join(map_, a["image"])
            print("      crop   : %s%s" % (pad if paden else a["image"],
                                           "" if os.path.isfile(pad) else "  (ONTBREEKT)"))
        for i, regel in enumerate(str(a.get("comment", "")).split("\n")):
            print("      %s %s" % ("zegt   :" if i == 0 else "        ", regel))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    vlaggen = {a for a in sys.argv[1:] if a.startswith("--")}
    alleen_open = "--open" in vlaggen
    ook_resolved = "--resolved" in vlaggen
    paden = "--paden" in vlaggen

    ps = paginas()
    if not ps:
        print("Geen annotaties gevonden in %s" % ROOT)
        return 1

    if "--alles" in vlaggen:
        for p in ps:
            print("\n=== %s" % p)
            for nr, f in rondes(p):
                d = laad(f)
                anns = d.get("annotations", [])
                o = len([a for a in anns if not a.get("resolved")])
                print("  ronde-%02d  %2d annotaties, %d open%s"
                      % (nr, len(anns), o, "  [gesloten]" if d.get("closed") else ""))
        return 0

    pagina = args[0] if args else (ps[-1] if len(ps) == 1 else None)
    if pagina is None:
        print("Meerdere pagina's, kies er een: %s" % ", ".join(ps))
        return 1
    if pagina not in ps:
        treffers = [p for p in ps if pagina in p]
        if len(treffers) != 1:
            print("Onbekende pagina '%s'. Beschikbaar: %s" % (pagina, ", ".join(ps)))
            return 1
        pagina = treffers[0]

    rs = rondes(pagina)
    print("=== %s  (%d rondes)" % (pagina, len(rs)))
    if len(args) > 1:
        gevraagd = int(args[1])
        rs = [(n, f) for n, f in rs if n == gevraagd]
        if not rs:
            print("ronde-%02d bestaat niet" % gevraagd)
            return 1
    else:
        rs = rs[-1:]

    for nr, f in rs:
        toon(f, nr, alleen_open, ook_resolved, paden)
    return 0


if __name__ == "__main__":
    sys.exit(main())
