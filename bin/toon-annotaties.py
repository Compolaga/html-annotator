#!/usr/bin/env python3
"""Toont open annotaties, zodat je daar geen ad-hoc script meer voor schrijft.

Gebruik:
  toon-annotaties.py                    laatste ronde van de enige/laatste pagina
  toon-annotaties.py todos     laatste ronde van die pagina
  toon-annotaties.py todos 8   ronde 8
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

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from annotator.config import ROOT
from annotator.refs import expand_comment, validate_refs

# Komt mee zodra er open annotaties zijn. Staat hier en niet alleen in SKILL.md,
# zodat het altijd in de context terechtkomt van wie deze feedback verwerkt.
WERKREGEL = """
╭─ Voor de agent: eerst begrijpen, dan pas verwerken ───────────────
│ Een kaal bericht "." is "verwerk mijn annotaties", geen typo.
│ Geen bevestiging vragen; gewoon deze flow.
│
│ Neem deze annotaties niet klakkeloos over. Ze worden vaak gedicteerd,
│ dus zinnen lopen soms dood, en vanzelfsprekende context ontbreekt.
│
│ Loop ze één voor één na en vraag jezelf per annotatie af:
│   · Snap ik wat er bedoeld wordt, of vul ik het zelf in? Vul je in, vraag.
│   · Kan dit meer dan één kant op? Leg de lezingen voor, kies er niet
│     zelf een.
│   · Ben ik het er niet mee eens, of zie ik een gevolg dat niet
│     genoemd wordt? Zeg dat, met je reden erbij.
│   · Is het te vaag om op te handelen? Vraag door tot het scherp is.
│   · Spreekt dit iets tegen dat eerder gezegd is? Benoem het.
│
│ Zitten er keuzes in, stel je vragen dan klikbaar met AskUserQuestion.
│ Twijfel je of je moet vragen: vragen. Verkeerd raden kost meer tijd
│ dan een vraag.
│
│ Verwerk pas daarna, en vink af wat af is via POST /resolve.
│
│ Wordt hierna een taak gespawnd? Die hangt aan de todolijst:
│ bin/vind-todolijst.sh geeft het pad, skill `task-spawnen` de titel.
╰───────────────────────────────────────────────────────────────────
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
    if open_n:
        print(WERKREGEL)

    map_ = os.path.dirname(f)
    for a in tonen:
        vlag = " ✓resolved" if a.get("resolved") else ""
        print("\n  [%s] %s%s" % (a.get("nr"), a.get("type", "?"), vlag))
        doel = a.get("target") or ""
        if doel:
            print("      op     : %s" % doel[:100])
        if a.get("selectedText"):
            print("      select : %s" % a["selectedText"][:120])
        loc = a.get("locator") or {}
        if loc.get("path") or loc.get("start"):
            pad = loc.get("path") or (loc.get("start") or {}).get("path") or ""
            print("      locatie: %s%s" % (pad[:100],
                  ("  [nth %s]" % loc["nth"]) if loc.get("nth") else ""))
            if loc.get("label") and loc.get("label") != a.get("selectedText"):
                print("      context: %s" % loc["label"][:120])
        if a.get("type") == "edit":
            # De tekst is zelf herschreven. De diff is het antwoord op "wat moet er
            # anders": - is eruit, + is erin. De volledige nieuwe tekst staat eronder,
            # zodat je hem kunt overnemen zonder de wijzigingen te hoeven toepassen.
            if (a.get("veld") or "") != (a.get("target") or ""):
                print("      veld   : %s" % (a.get("veld") or "?"))
            hunks = a.get("hunks") or []
            if hunks:
                # Per blok, zodat je ze los kunt beoordelen en toepassen. Het
                # alineanummer is om naar te verwijzen; het anker is de tekst eromheen.
                for h in hunks:
                    vlag = " (afgevinkt)" if h.get("resolved") else ""
                    print("      blok %s, alinea %s%s"
                          % (h.get("n"), h.get("alinea"), vlag))
                    if h.get("verwijderd"):
                        print("        - %s" % h["verwijderd"].replace("\n", " ")[:100])
                    if h.get("toegevoegd"):
                        print("        + %s" % h["toegevoegd"].replace("\n", " ")[:100])
                    context = (h.get("voor") or "").replace("\n", " ")[-40:]
                    if context.strip():
                        print("          volgt op: ...%s" % context.strip())
                print("      toepassen: pas-hunk-toe.py <json> --nr %s --hunks <n>" % a.get("nr"))
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
                print("      nieuwe tekst:")
                for regel in nieuwe.splitlines():
                    print("        | %s" % regel[:110])
        if a.get("image"):
            pad = os.path.join(map_, a["image"])
            print("      crop   : %s%s" % (pad if paden else a["image"],
                                           "" if os.path.isfile(pad) else "  (ONTBREEKT)"))
        for i, regel in enumerate(expand_comment(a.get("comment", ""), a.get("refs")).split("\n")):
            print("      %s %s" % ("zegt   :" if i == 0 else "        ", regel))
        refs = a.get("refs") or []
        missing, unused = validate_refs(a.get("comment", ""), refs)
        if missing:
            print("      refs   : ONTBREEKT in JSON: %s" % ", ".join(missing))
        if unused:
            print("      refs   : niet in comment: %s" % ", ".join(unused))
        if refs:
            for r in refs:
                rid = r.get("id") or "?"
                tekst = (r.get("selectedText") or "").replace("\n", " ")
                print("      ref %s: %s" % (rid, tekst[:120]))
        elif a.get("comment") and "\u27e6" in a.get("comment", ""):
            print("      refs   : markers in comment maar geen refs-array \u2014 opnieuw saven")


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
