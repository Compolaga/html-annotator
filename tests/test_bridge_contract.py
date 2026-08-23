#!/usr/bin/env python3
"""B1–B7: bridge-HTTP en ronde-gedrag, zonder de live poort 8791."""

import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(SKILL, "bin", "annotator-bridge.py")


def check(naam, conditie):
    if not conditie:
        print("FAIL  %s" % naam)
        return 1
    print("PASS  %s" % naam)
    return 0


def vrije_poort():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    poort = s.getsockname()[1]
    s.close()
    return poort


def laad_bridge_mod():
    spec = importlib.util.spec_from_file_location("annbridge", BRIDGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def http(method, url, body=None, headers=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            raw = r.read()
            return r.status, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def start_bridge(root, poort):
    env = os.environ.copy()
    env["LUC_ANNOTATOR_PORT"] = str(poort)
    env["LUC_ANNOTATOR_ROOT"] = root
    proc = subprocess.Popen(
        [sys.executable, BRIDGE],
        cwd=SKILL,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    basis = "http://127.0.0.1:%d" % poort
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            code, _, _ = http("GET", basis + "/ping")
            if code == 200:
                return proc, basis
        except OSError:
            time.sleep(0.05)
    proc.kill()
    raise RuntimeError("bridge kwam niet omhoog op poort %s" % poort)


def main():
    n = 0
    root = tempfile.mkdtemp(prefix="ann-root-")
    pagina = os.path.join(tempfile.mkdtemp(prefix="ann-page-"), "demo.html")
    blok = "<!-- LUC-ANNOTATOR v2 -->\n<script>var x=1;</script>\n<!-- /LUC-ANNOTATOR -->"
    with open(pagina, "w", encoding="utf-8") as f:
        f.write("<!doctype html><title>demo</title><p>inhoud</p>\n" + blok + "\n")

    mod = laad_bridge_mod()
    h1 = mod.content_hash(pagina, "abc")
    kaal = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    kaal.write("<!doctype html><title>demo</title><p>inhoud</p>\n\n")
    kaal.close()
    h2 = mod.content_hash(kaal.name, "abc")
    n += check("B5 hash negeert annotator-blok", h1 == h2 and h1.startswith("sha256:"))
    with open(pagina, "a", encoding="utf-8") as f:
        f.write("<p>gewijzigd</p>\n")
    h3 = mod.content_hash(pagina, "abc")
    n += check("B5 hash ziet echte wijziging", h1 != h3)

    poort = vrije_poort()
    proc, basis = start_bridge(root, poort)
    try:
        code, hdr, raw = http("GET", basis + "/ping")
        ping = json.loads(raw.decode("utf-8"))
        n += check("B1 ping 200", code == 200 and ping.get("ok") is True)
        n += check("B1 ping identiteit", ping.get("bridge") == "luc-annotator")
        n += check("B1 CORS *", hdr.get("Access-Control-Allow-Origin") == "*")

        code, _, _ = http("OPTIONS", basis + "/save")
        n += check("B1 OPTIONS 204", code == 204)

        code, _, raw = http("GET", basis + "/p/../etc/passwd")
        body = json.loads(raw.decode("utf-8"))
        n += check("B2 /p/ buiten home is 403", code == 403 and body.get("ok") is False)

        for pad in ("/session", "/save", "/delete", "/remove-all", "/resolve", "/sessie"):
            code, _, raw = http("POST", basis + pad, {})
            n += check("B3 %s antwoordt" % pad, code in (200, 400))
        code, _, raw = http("POST", basis + "/sessie", {"url": "file:///etc/passwd"})
        n += check("B3 /sessie weigert file://", code == 400)

        slug = {"page": "http://127.0.0.1:%d/p/Desktop/demo.html" % poort,
                "pageFile": pagina, "slug": "demo", "title": "demo"}
        code, _, raw = http("POST", basis + "/save", {
            **slug,
            "annotation": {
                "id": "t-1", "type": "text", "selectedText": "inhoud",
                "comment": "zet \u27e6r1\u27e7 gelijk",
                "refs": [{"id": "r1", "selectedText": "andere"}],
                "locator": {"path": "p:nth-of-type(1)", "nth": 0},
            },
        })
        save1 = json.loads(raw.decode("utf-8"))
        n += check("B3 save ok", code == 200 and save1.get("ok") and save1.get("round") == 1)
        json_pad = save1["jsonPath"]
        n += check("B7 json bestaat", os.path.isfile(json_pad))
        n += check("B7 geen tmp-rest", not os.path.exists(json_pad + ".tmp"))

        atomair = os.path.join(tempfile.mkdtemp(prefix="ann-atom-"), "annotations.json")
        oud = {"annotations": [{"id": "keep-me"}]}
        mod.schrijf(atomair, oud)
        try:
            mod.schrijf(atomair, {"bad": object()})
            n += check("B7 dump-fout laat origineel staan", False)
        except TypeError:
            na = json.loads(open(atomair, encoding="utf-8").read())
            n += check("B7 dump-fout laat origineel staan", na == oud)
            n += check("B7 dump-fout laat geen tmp", not os.path.exists(atomair + ".tmp"))
        data = json.loads(open(json_pad, encoding="utf-8").read())
        rec = data["annotations"][0]
        n += check("B3 text-save houdt locator", rec.get("type") == "text" and rec.get("locator", {}).get("path"))
        n += check("B9 refs bewaard", rec.get("refs") and rec["refs"][0]["id"] == "r1")

        mod.ROOT = tempfile.mkdtemp(prefix="ann-crop-")
        def _crop_faalt(*_a, **_k):
            raise RuntimeError("crop kapot")
        mod.maak_crop = _crop_faalt
        crop_uit = mod.h_save({
            "page": "http://127.0.0.1/p/Desktop/crop-demo.html",
            "pageFile": pagina,
            "slug": "crop-demo",
            "title": "crop",
            "doc": {"w": 800, "h": 600},
            "annotation": {
                "id": "regio-1", "type": "region",
                "rect": {"x": 10, "y": 10, "w": 40, "h": 40},
                "comment": "regio blijft",
            },
        })
        regio = next(a for a in json.loads(open(crop_uit["jsonPath"], encoding="utf-8").read())["annotations"]
                     if a.get("id") == "regio-1")
        n += check("B6 crop-fout bewaart toch", crop_uit.get("ok") is True and regio.get("comment") == "regio blijft")
        n += check("B6 imageError gezet", bool(regio.get("imageError")) and regio.get("image") is None)

        code, _, raw = http("POST", basis + "/save", {
            **slug,
            "annotation": {"id": "t-2", "type": "text", "selectedText": "nog", "comment": "tweede"},
        })
        save2 = json.loads(raw.decode("utf-8"))
        n += check("B4 zelfde ronde", save2.get("round") == 1)
        http("POST", basis + "/delete", {"id": "t-1", **slug})
        over = json.loads(open(json_pad, encoding="utf-8").read())["annotations"]
        n += check("B3 delete houdt de rest", [a.get("id") for a in over] == ["t-2"])

        http("POST", basis + "/remove-all", slug)
        code, _, raw = http("POST", basis + "/save", {
            **slug,
            "annotation": {"id": "t-3", "type": "text", "selectedText": "nieuw", "comment": "ronde 2"},
        })
        save3 = json.loads(raw.decode("utf-8"))
        n += check("B4 nieuwe ronde na remove-all", save3.get("round") == 2)
        n += check("B4 ronde 1 blijft staan", os.path.isfile(json_pad))

        code, _, raw = http("POST", basis + "/resolve", {
            "jsonPath": save3["jsonPath"], "nrs": [1],
        })
        res = json.loads(raw.decode("utf-8"))
        n += check("B3 resolve", code == 200 and 1 in (res.get("resolved") or []))
        op_schijf = json.loads(open(save3["jsonPath"], encoding="utf-8").read())
        rec3 = op_schijf["annotations"][0]
        n += check("B3 resolve op schijf", rec3.get("resolved") is True and rec3.get("resolvedAt"))
        http("POST", basis + "/resolve", {
            "jsonPath": save3["jsonPath"], "nrs": [1], "resolved": False,
        })
        terug = json.loads(open(save3["jsonPath"], encoding="utf-8").read())["annotations"][0]
        n += check("B3 resolve terug te draaien", terug.get("resolved") is not True)
    finally:
        proc.kill()
        proc.wait(timeout=3)

    return n


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
