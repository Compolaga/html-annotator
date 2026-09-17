"""Toont open annotaties, zodat je daar geen ad-hoc script meer voor schrijft.

Gebruik (via de CLI):
  python -m html_annotator show --open        de pagina die als laatste is geannoteerd
  python -m html_annotator show todos         laatste ronde van die pagina
  python -m html_annotator show todos 8       ronde 8
  python -m html_annotator show --list        pagina's met open annotaties, compact
  python -m html_annotator show --search x    pagina's waarvan de naam die term bevat
  python -m html_annotator show --all         elke pagina, elke ronde, alleen tellingen

Zonder paginanaam kiest het script zelf: de meest recent gewijzigde pagina met
open annotaties, binnen een venster van 7 dagen. Oudere blijven op schijf en zijn
vindbaar met --list of --search, maar komen niet ongevraagd in beeld: dat scheelt
duizenden tokens context bij elke aanroep.

Extra vlaggen:
  --resolved   toon ook de al afgehandelde annotaties (standaard verborgen)
  --paths      print de absolute paden naar json en screenshot-crops
  --since N    verruim het venster naar N dagen (--since 0 = geen venster)
"""

import json
import os
import re
import sys
import time

from . import config
from .refs import expand_comment, validate_refs

ROOT = str(config.root())

if hasattr(sys.stdout, "reconfigure"):  # Windows-console is standaard geen UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


VENSTER_DAGEN = 7


def open_info(pagina):
    """(aantal open annotaties, mtime van de laatst gewijzigde ronde)."""
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
    """Pagina's die in aanmerking komen, nieuwste eerst.

    Zonder venster zou elke aanroep de hele geschiedenis tonen; met venster komt
    alleen recent werk in beeld. Dat omzeilt de vraag wanneer een ronde 'klaar'
    is: niet-afgevinkt werk van weken geleden verjaart vanzelf uit de default.
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
                    if h.get("soort") == "opmaak":
                        # Opmaak zit niet in de tekst, dus valt er niets te vervangen:
                        # dit blok beschrijft wat er met de vorm van een regel gebeurde.
                        print("      blok %s, opmaak%s: %s"
                              % (h.get("n"), vlag, h.get("omschrijving") or "gewijzigd"))
                        if h.get("blok"):
                            print("        op: %s" % h["blok"].replace("\n", " ")[:100])
                        continue
                    print("      blok %s, alinea %s%s"
                          % (h.get("n"), h.get("alinea"), vlag))
                    if h.get("verwijderd"):
                        print("        - %s" % h["verwijderd"].replace("\n", " ")[:100])
                    if h.get("toegevoegd"):
                        print("        + %s" % h["toegevoegd"].replace("\n", " ")[:100])
                    context = (h.get("voor") or "").replace("\n", " ")[-40:]
                    if context.strip():
                        print("          volgt op: ...%s" % context.strip())
                print("      toepassen: python -m html_annotator apply-hunk <json> --nr %s --hunks <n>" % a.get("nr"))
                if any(h.get("soort") == "opmaak" for h in hunks):
                    print("      let op: opmaakblokken plaatst het script niet — neem de"
                          " opmaak over uit 'nieuwe HTML' hieronder")
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
            # De volledige nieuwe versie inclusief opmaak, mail-veilig (p/ul/ol/li/b/i/a/br).
            # Dit is de grondwaarheid als tekst en opmaak allebei wijzigden.
            if a.get("nieuwHtml"):
                print("      nieuwe HTML:")
                print("        | %s" % a["nieuwHtml"][:600])
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
        print("Geen annotaties gevonden in %s" % ROOT)
        return 1

    if zoekterm or "--list" in vlaggen:
        rijen = kandidaten(ps, alleen_open or not zoekterm, 0)
        if zoekterm:
            rijen = [r for r in rijen if zoekterm.lower() in r[0].lower()]
        if not rijen:
            print("Niets gevonden%s." % (" voor '%s'" % zoekterm if zoekterm else ""))
            return 1
        kop = "pagina's met '%s'" % zoekterm if zoekterm else "pagina's met open annotaties"
        print("%s (%d):" % (kop, len(rijen)))
        for naam, n, mt in rijen[:40]:
            print("  %-52s %3d open  %s" % (naam, n, datum(mt)))
        if len(rijen) > 40:
            print("  ... nog %d, verfijn met --search" % (len(rijen) - 40))
        return 0

    if "--all" in vlaggen:
        for p in ps:
            print("\n=== %s" % p)
            for nr, f in rondes(p):
                d = laad(f)
                anns = d.get("annotations", [])
                o = len([a for a in anns if not a.get("resolved")])
                print("  ronde-%02d  %2d annotaties, %d open%s"
                      % (nr, len(anns), o, "  [gesloten]" if d.get("closed") else ""))
        return 0

    rest = []
    if args:
        pagina = args[0]
        if pagina not in ps:
            treffers = [p for p in ps if pagina.lower() in p.lower()]
            if len(treffers) == 1:
                pagina = treffers[0]
            elif not treffers:
                print("Onbekende pagina '%s'. Zoek met: --search %s" % (pagina, pagina))
                return 1
            else:
                print("'%s' past op %d pagina's:" % (pagina, len(treffers)))
                for t in treffers[:15]:
                    print("  %s" % t)
                if len(treffers) > 15:
                    print("  ... nog %d" % (len(treffers) - 15))
                return 1
    else:
        rijen = kandidaten(ps, alleen_open, venster)
        if not rijen and alleen_open:
            # Niets open is geen fout: zeg het kort en stop met exit 0.
            binnen = " (laatste %d dagen)" % venster if venster else ""
            ouder = kandidaten(ps, True, 0)
            print("(niets open)%s" % binnen)
            if ouder:
                print("Wel %d pagina%s met oudere open annotaties  ->  --list"
                      % (len(ouder), "'s" if len(ouder) != 1 else ""))
            return 0
        if not rijen:
            print("Geen annotaties in de laatste %d dagen. Ouder werk: --list of --search <term>."
                  % venster if venster else "Geen annotaties gevonden.")
            return 1
        pagina = rijen[0][0]
        rest = rijen[1:]

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

    if rest:
        namen = ", ".join("%s (%d)" % (n, o) for n, o, _ in rest[:3])
        extra = ", ..." if len(rest) > 3 else ""
        binnen = " binnen %d dagen" % venster if venster else ""
        print("\nNog %d pagina%s met open annotaties%s: %s%s   ->  --list voor alles"
              % (len(rest), "'s" if len(rest) != 1 else "", binnen, namen, extra))
    return 0
