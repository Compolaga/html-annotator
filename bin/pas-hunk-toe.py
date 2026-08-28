#!/usr/bin/env python3
"""Past losse blokken uit een bewerking toe op de pagina waar ze bij horen.

Zo hoef je een bewerking niet als geheel over te nemen: is blok 1 goed en blok 2
iets waar je nog een vraag over hebt, dan voer je alleen blok 1 door.

  pas-hunk-toe.py <annotations.json> --nr 1                 alle open blokken
  pas-hunk-toe.py <annotations.json> --nr 1 --hunks 2,3     alleen deze
  pas-hunk-toe.py <annotations.json> --nr 1 --droog         alleen tonen
  pas-hunk-toe.py <annotations.json> --nr 1 --afvinken      en meteen resolven

Plaatsen gebeurt op de tekst eromheen, niet op een positie. Een teken- of
regelnummer klopt niet meer zodra er iets bóven de wijziging verandert; de
omringende woorden vinden het blok ook in een gewijzigd document terug. Dat is
dezelfde reden waarom `patch` een hunk met een verschoven regelnummer alsnog plaatst.

Drie pogingen per blok, van streng naar soepel, en de gebruikte manier staat in de
uitvoer zodat je kunt zien hoe zeker de plaatsing was:
  1. voor + verwijderd + na   — volledige context, geen twijfel mogelijk
  2. voor + verwijderd        — alleen de linkerkant; genoeg als die uniek is
  3. verwijderd               — kaal, en alleen als het precies één keer voorkomt
Lukt geen van drieën, dan gebeurt er niets voor dat blok en zegt het script waarom.
"""

import argparse
import json
import os
import sys
import urllib.request


def laad(pad):
    pad = os.path.expanduser(pad)
    if not os.path.isfile(pad):
        sys.exit("niet gevonden: %s" % pad)
    with open(pad, encoding="utf-8") as f:
        return pad, json.load(f)


def plaats(tekst, hunk):
    """Geeft (nieuwe_tekst, manier) of (None, reden)."""
    voor = hunk.get("voor") or ""
    na = hunk.get("na") or ""
    weg = hunk.get("verwijderd") or ""
    erbij = hunk.get("toegevoegd") or ""

    pogingen = [
        ("volledige context", voor + weg + na, voor + erbij + na),
        ("linkercontext", voor + weg, voor + erbij),
    ]
    if weg:
        pogingen.append(("kaal", weg, erbij))

    for manier, zoek, vervang in pogingen:
        if not zoek:
            continue
        aantal = tekst.count(zoek)
        if aantal == 1:
            return tekst.replace(zoek, vervang, 1), manier
        if aantal > 1 and manier != "kaal":
            # meerdere treffers met context is verdacht; probeer de volgende poging
            continue
    if not weg and not voor and not na:
        return None, "blok heeft geen anker en geen tekst"
    return None, "anker niet teruggevonden (of niet uniek) in de pagina"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--nr", type=int, required=True, help="annotatienummer")
    ap.add_argument("--hunks", default="", help="komma-gescheiden blokken; leeg = alle open")
    ap.add_argument("--bestand", default="", help="doelbestand; standaard pageFile uit de ronde")
    ap.add_argument("--droog", action="store_true", help="niets wegschrijven")
    ap.add_argument("--afvinken", action="store_true", help="geplaatste blokken meteen resolven")
    ap.add_argument("--poort", default=os.environ.get("LUC_ANNOTATOR_PORT", "8791"))
    a = ap.parse_args()

    json_pad, data = laad(a.json)
    ann = next((x for x in data.get("annotations", []) if x.get("nr") == a.nr), None)
    if not ann:
        sys.exit("annotatie %d niet gevonden in %s" % (a.nr, json_pad))
    if ann.get("type") != "edit":
        sys.exit("annotatie %d is geen bewerking maar '%s'" % (a.nr, ann.get("type")))

    alle = ann.get("hunks") or []
    if not alle:
        sys.exit("annotatie %d heeft geen blokken; dit is een oudere bewerking "
                 "zonder hunks — neem 'nieuw' als geheel over" % a.nr)

    gevraagd = [int(x) for x in a.hunks.split(",") if x.strip()] if a.hunks else None
    doel_hunks = [h for h in alle
                  if (gevraagd is None and not h.get("resolved")) or
                     (gevraagd is not None and h.get("n") in gevraagd)]
    if not doel_hunks:
        sys.exit("geen blokken om toe te passen (alles al afgevinkt?)")

    bestand = os.path.expanduser(a.bestand or data.get("pageFile") or "")
    if not bestand or not os.path.isfile(bestand):
        sys.exit("doelbestand niet gevonden: %s" % (bestand or "(geen pageFile in de ronde)"))

    with open(bestand, encoding="utf-8") as f:
        tekst = f.read()

    gelukt, mislukt = [], []
    for h in doel_hunks:
        if h.get("soort") == "opmaak":
            # Een opmaakwijziging staat niet in de tekst en is dus niet met zoek-en-
            # vervang te plaatsen: de vorm van een regel zit in de HTML eromheen. Het
            # script raakt hem daarom niet aan en zegt wat er moet gebeuren.
            print("  blok %s  OVERGESLAGEN  opmaak: %s"
                  % (h.get("n"), h.get("omschrijving") or "gewijzigd"))
            print("            neem de opmaak over uit 'nieuwHtml' van annotatie %d" % a.nr)
            mislukt.append(h.get("n"))
            continue
        nieuw, manier = plaats(tekst, h)
        label = "%s -> %s" % (
            (h.get("verwijderd") or "(niets)").replace("\n", "\\n")[:45],
            (h.get("toegevoegd") or "(niets)").replace("\n", "\\n")[:45])
        if nieuw is None:
            print("  blok %s  MISLUKT   %s  [%s]" % (h.get("n"), label, manier))
            mislukt.append(h.get("n"))
        else:
            tekst = nieuw
            print("  blok %s  geplaatst  %s  [via %s, alinea %s]"
                  % (h.get("n"), label, manier, h.get("alinea")))
            gelukt.append(h.get("n"))

    if a.droog:
        print("\ndroog gedraaid; %s wordt niet aangepast" % bestand)
        return

    if gelukt:
        with open(bestand, "w", encoding="utf-8") as f:
            f.write(tekst)
        print("\n%d van %d blokken doorgevoerd in %s" % (len(gelukt), len(doel_hunks), bestand))
    if mislukt:
        print("niet geplaatst: %s — kijk zelf of de tekst intussen veranderd is"
              % ", ".join(str(x) for x in mislukt))

    if a.afvinken and gelukt:
        body = json.dumps({"jsonPath": json_pad, "nrs": [a.nr], "hunks": gelukt}).encode()
        req = urllib.request.Request("http://127.0.0.1:%s/resolve" % a.poort, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                uit = json.load(r)
            print("afgevinkt: blokken %s; nog open in deze ronde: %s annotaties, %s blokken"
                  % (uit.get("hunksResolved"), uit.get("open"), uit.get("hunksOpen")))
        except Exception as e:
            print("afvinken mislukte (%s); doe het met POST /resolve" % e)

    sys.exit(1 if mislukt else 0)


if __name__ == "__main__":
    main()
