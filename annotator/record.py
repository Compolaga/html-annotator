"""Schoonmaak van het annotation-record zoals h_save het al wegschreef.

Geen nieuwe velden, geen strengere validatie. Eén interface voor locator,
refs en commentExpanded — dezelfde output als de oude inline code in de bridge.
"""

from annotator_refs import expand_comment, validate_refs


def schoon_punt(p):
    if not isinstance(p, dict) or not (p.get("path") or "").strip():
        return None
    uit = {"path": str(p.get("path") or "").strip(), "offset": int(p.get("offset") or 0)}
    if p.get("node") is not None:
        try:
            uit["node"] = int(p["node"])
        except (TypeError, ValueError):
            pass
    return uit


def schoon_locator(loc):
    if not isinstance(loc, dict):
        return None
    uit = {}
    start, end = schoon_punt(loc.get("start")), schoon_punt(loc.get("end"))
    if start:
        uit["start"] = start
    if end:
        uit["end"] = end
    path = (loc.get("path") or "").strip()
    if path:
        uit["path"] = path
    label = (loc.get("label") or "").strip()
    if label:
        uit["label"] = label[:200]
    if loc.get("nth") is not None:
        try:
            uit["nth"] = max(0, int(loc["nth"]))
        except (TypeError, ValueError):
            pass
    return uit or None


def schoon_refs(refs):
    if not isinstance(refs, list) or not refs:
        return None
    uit = []
    for r in refs:
        if not isinstance(r, dict) or not (r.get("selectedText") or "").strip():
            continue
        item = {
            "id": (r.get("id") or "").strip(),
            "selectedText": (r.get("selectedText") or "").strip(),
        }
        loc = schoon_locator(r.get("locator"))
        if loc:
            item["locator"] = loc
        uit.append(item)
    return uit


def zet_ref_velden(rec, refs):
    """Zet refs / commentExpanded / refsIncomplete op rec, identiek aan h_save."""
    schoon = schoon_refs(refs)
    if schoon is not None:
        rec["refs"] = schoon
    rec["commentExpanded"] = expand_comment(rec.get("comment") or "", rec.get("refs"))
    missing, _ = validate_refs(rec.get("comment") or "", rec.get("refs"))
    if missing:
        rec["refsIncomplete"] = missing
    return rec
