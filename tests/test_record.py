#!/usr/bin/env python3
"""Vastgelegd gedrag van refs/locator-schoonmaak. Geen browser, geen bridge."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from annotator.record import schoon_locator, schoon_refs, zet_ref_velden
from annotator.refs import expand_comment, validate_refs


def check(naam, conditie):
    if not conditie:
        print("FAIL  %s" % naam)
        return 1
    print("PASS  %s" % naam)
    return 0


def main():
    n = 0
    n += check("lege locator", schoon_locator(None) is None)
    n += check("nth-only locator", schoon_locator({"nth": 1}) == {"nth": 1})
    loc = schoon_locator({
        "path": " #row-255 ",
        "label": "x" * 250,
        "nth": -3,
        "start": {"path": "#a", "node": "2", "offset": "4"},
        "end": {"path": "", "offset": 0},
    })
    n += check("path getrimd", loc and loc.get("path") == "#row-255")
    n += check("label max 200", loc and len(loc.get("label", "")) == 200)
    n += check("nth niet negatief", loc and loc.get("nth") == 0)
    n += check("start node int", loc and loc["start"]["node"] == 2)
    n += check("lege end weg", loc and "end" not in loc)

    refs = schoon_refs([
        {"id": " r1 ", "selectedText": "  foo  ", "locator": {"path": "#b"}},
        {"id": "r2", "selectedText": ""},
        "niet-dict",
    ])
    n += check("één geldige ref", refs and len(refs) == 1)
    n += check("ref id getrimd", refs and refs[0]["id"] == "r1")
    n += check("ref locator", refs and refs[0].get("locator", {}).get("path") == "#b")
    n += check("lege refs-lijst", schoon_refs([]) is None)
    rec_bad = {"comment": "x"}
    zet_ref_velden(rec_bad, [{"id": "r1", "selectedText": ""}])
    n += check("all-invalid refs → []", rec_bad.get("refs") == [])

    comment = "Maak \u27e6r1\u27e7 hetzelfde als \u27e6r2\u27e7"
    exp = expand_comment(comment, [{"id": "r2", "selectedText": "tweede"}])
    n += check("expand ontbreekt", "ONTBREEKT" in exp)
    n += check("expand aanwezig", '"tweede"' in exp)
    miss, unused = validate_refs(comment, [{"id": "r2", "selectedText": "x"}])
    n += check("missing r1", miss == ["r1"])
    n += check("geen unused", unused == [])

    rec = {"comment": comment}
    zet_ref_velden(rec, [{"id": "r1", "selectedText": "eerste"}])
    n += check("zet refs", rec.get("refs") and rec["refs"][0]["id"] == "r1")
    n += check("zet expanded", "eerste" in rec.get("commentExpanded", ""))
    n += check("zet incomplete r2", rec.get("refsIncomplete") == ["r2"])
    return n


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
