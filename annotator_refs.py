"""Gedeelde hulp voor inline tekst-referenties (⟦r1⟧ + refs-array)."""

import re

REF_RE = re.compile(r"\u27e6([^\u27e7]+)\u27e7")


def ref_ids_in_comment(comment):
    return REF_RE.findall(comment or "")


def expand_comment(comment, refs, missing_label="ONTBREEKT"):
    by_id = {r.get("id"): r for r in (refs or []) if r.get("id")}

    def vervang(m):
        rid = m.group(1)
        r = by_id.get(rid)
        if not r:
            return "\u27e6%s \u2014 %s\u27e7" % (rid, missing_label)
        t = (r.get("selectedText") or "").replace("\n", " ")
        if len(t) > 100:
            t = t[:98] + "\u2026"
        return '\u27e6"%s"\u27e7' % t

    return REF_RE.sub(vervang, comment or "")


def validate_refs(comment, refs):
    by_id = {r.get("id") for r in (refs or []) if r.get("id")}
    in_comment = set(ref_ids_in_comment(comment))
    missing = sorted(in_comment - by_id)
    unused = sorted(by_id - in_comment)
    return missing, unused
