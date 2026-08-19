#!/usr/bin/env python3
"""Lokale bridge voor de HTML-annotator (LUC-ANNOTATOR v2).

Draait op 127.0.0.1:8791 en schrijft annotaties direct naar
~/Desktop/annotaties/<pagina-slug>/ronde-NN/annotations.json, inclusief
screenshot-crops in ronde-NN/screenshots/.

Alleen stdlib nodig. Pillow wordt gebruikt als het toevallig beschikbaar is;
anders knipt headless Chrome de crop zelf uit via een iframe-clip.

Starten:  python3 ~/.claude/skills/html-annotator/annotator-bridge.py
Checken:  curl -s http://127.0.0.1:8791/ping
"""

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = int(os.environ.get("LUC_ANNOTATOR_PORT", "8791"))
ROOT = os.path.expanduser(os.environ.get("LUC_ANNOTATOR_ROOT", "~/Desktop/annotaties"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CACHE = os.path.join(tempfile.gettempdir(), "luc-annotator-shots")
MARGE = 12
LOCK = threading.Lock()

try:
    from PIL import Image  # type: ignore
    HEEFT_PILLOW = True
except Exception:  # pragma: no cover - afhankelijk van omgeving
    HEEFT_PILLOW = False


# ---------------------------------------------------------------- hulpjes

def slugify(tekst, standaard="pagina"):
    s = re.sub(r"[^a-z0-9]+", "-", (tekst or "").lower()).strip("-")
    return s[:60] or standaard


def pad_van_page(page, page_file):
    """Absoluut bestandspad van de pagina, of None."""
    if page_file:
        p = os.path.expanduser(page_file)  # "~/Desktop/x.html" komt van de /p/-route
        if os.path.isfile(p):
            return p
    if page and page.startswith("file://"):
        p = urllib.parse.unquote(urllib.parse.urlparse(page).path)
        if os.path.isfile(p):
            return p
    if page and "/p/" in page:
        try:
            rel = urllib.parse.unquote(urllib.parse.urlparse(page).path).split("/p/", 1)[1]
            p = os.path.join(os.path.expanduser("~"), rel)
            if os.path.isfile(p):
                return p
        except Exception:
            pass
    return None


ANNOTATOR_BLOK = re.compile(
    r"<!--\s*LUC-ANNOTATOR.*?<!--\s*/LUC-ANNOTATOR\s*-->", re.S | re.I)


def content_hash(bestand, dom_hash):
    """Hash van de pagina-inhoud zonder het annotator-blok."""
    if bestand:
        try:
            with open(bestand, "r", encoding="utf-8", errors="replace") as f:
                bron = f.read()
            bron = ANNOTATOR_BLOK.sub("", bron)
            # ook een niet-afgesloten v1-blok wegknippen
            i = bron.find("<!-- LUC-ANNOTATOR")
            if i >= 0:
                bron = bron[:i]
            return "sha256:" + hashlib.sha256(bron.encode("utf-8")).hexdigest()[:32]
        except OSError:
            pass
    return "dom:" + (dom_hash or "onbekend")


def pagina_map(payload):
    bestand = pad_van_page(payload.get("page"), payload.get("pageFile"))
    if bestand:
        slug = slugify(os.path.splitext(os.path.basename(bestand))[0])
    else:
        slug = slugify(payload.get("slug") or payload.get("title"))
    return os.path.join(ROOT, slug), bestand


def rondes(map_pad):
    if not os.path.isdir(map_pad):
        return []
    uit = []
    for naam in os.listdir(map_pad):
        m = re.fullmatch(r"ronde-(\d+)", naam)
        if m and os.path.isdir(os.path.join(map_pad, naam)):
            uit.append(int(m.group(1)))
    return sorted(uit)


def lees_ronde(map_pad, nr):
    p = os.path.join(map_pad, "ronde-%02d" % nr, "annotations.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def bepaal_ronde(payload, maak=False):
    """Geeft (ronde-nr, ronde-map, json-pad, data-of-None, paginabestand).

    De lopende ronde is de hoogste bestaande ronde die niet gesloten is. Een
    gewijzigde pagina-inhoud opent dus GEEN nieuwe ronde meer; alleen een
    afgesloten ronde (Remove all) doet dat. De contentHash wordt nog wel
    bijgehouden, als context bij welke paginaversie de feedback hoorde.
    """
    map_pad, bestand = pagina_map(payload)
    h = content_hash(bestand, payload.get("domHash"))
    bestaand = rondes(map_pad)
    nr, data = None, None
    if bestaand:
        laatste = bestaand[-1]
        d = lees_ronde(map_pad, laatste)
        if d is not None and not d.get("closed"):
            nr, data = laatste, d
        else:
            nr = laatste + 1
    else:
        nr = 1
    ronde_map = os.path.join(map_pad, "ronde-%02d" % nr)
    json_pad = os.path.join(ronde_map, "annotations.json")
    if data is None:
        data = {
            "page": payload.get("page"),
            "pageFile": bestand,
            "round": nr,
            "contentHash": h,
            "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "doc": payload.get("doc") or {},
            "annotations": [],
        }
    if maak:
        os.makedirs(os.path.join(ronde_map, "screenshots"), exist_ok=True)
    return nr, ronde_map, json_pad, data, bestand, h


def schrijf(json_pad, data):
    os.makedirs(os.path.dirname(json_pad), exist_ok=True)
    tmp = json_pad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, json_pad)


# ------------------------------------------------------------ screenshots

def volledige_shot(bestand, page_url, dw, dh):
    """Volledige paginascreenshot (gecached op inhoud + afmeting)."""
    os.makedirs(CACHE, exist_ok=True)
    sleutel = hashlib.sha256(
        ("%s|%s|%s|%s" % (bestand or page_url, dw, dh,
                          os.path.getmtime(bestand) if bestand else "")
         ).encode()).hexdigest()[:24]
    uit = os.path.join(CACHE, sleutel + ".png")
    if os.path.isfile(uit):
        return uit
    url = page_url
    if bestand:
        url = "file://" + urllib.parse.quote(bestand)
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check",
         "--allow-file-access-from-files",
         "--screenshot=" + uit, "--window-size=%d,%d" % (dw, dh), url],
        check=True, capture_output=True, timeout=90)
    return uit


def crop_via_chrome(bestand, page_url, dw, dh, box, uit):
    """Fallback zonder Pillow: iframe-clip renderen met headless Chrome."""
    x0, y0, x1, y1 = box
    url = "file://" + urllib.parse.quote(bestand) if bestand else page_url
    html = (
        "<!doctype html><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:0;overflow:hidden;background:#fff}"
        "iframe{position:absolute;border:0;left:%dpx;top:%dpx;width:%dpx;height:%dpx}"
        "</style><iframe src=\"%s\" scrolling=no></iframe>"
        % (-x0, -y0, dw, dh, url))
    os.makedirs(CACHE, exist_ok=True)
    wrapper = os.path.join(CACHE, "clip-%d.html" % int(time.time() * 1000))
    with open(wrapper, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--no-first-run", "--no-default-browser-check",
             "--allow-file-access-from-files",
             "--screenshot=" + uit,
             "--window-size=%d,%d" % (max(1, x1 - x0), max(1, y1 - y0)),
             "file://" + urllib.parse.quote(wrapper)],
            check=True, capture_output=True, timeout=90)
    finally:
        try:
            os.remove(wrapper)
        except OSError:
            pass
    return uit


def maak_crop(bestand, page_url, doc, rect, uit_pad):
    dw = int(doc.get("w") or 800)
    dh = int(doc.get("h") or 2000)
    x0 = max(0, int(rect["x"]) - MARGE)
    y0 = max(0, int(rect["y"]) - MARGE)
    x1 = min(dw, int(rect["x"]) + int(rect["w"]) + MARGE)
    y1 = min(dh, int(rect["y"]) + int(rect["h"]) + MARGE)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("lege crop")
    os.makedirs(os.path.dirname(uit_pad), exist_ok=True)
    if HEEFT_PILLOW:
        vol = volledige_shot(bestand, page_url, dw, dh)
        with Image.open(vol) as img:
            img.crop((x0, y0, min(x1, img.width), min(y1, img.height))).save(uit_pad)
    else:
        crop_via_chrome(bestand, page_url, dw, dh, (x0, y0, x1, y1), uit_pad)
    return uit_pad


# -------------------------------------------------------------- endpoints

def h_session(payload):
    nr, ronde_map, json_pad, data, _, h = bepaal_ronde(payload)
    lijst = data.get("annotations", [])
    open_ann = []
    for a in lijst:
        if a.get("resolved"):
            continue
        open_ann.append({
            "nr": a.get("nr"), "id": a.get("id"), "type": a.get("type"),
            "rect": a.get("_rect") or a.get("rect") or None,
            "comment": a.get("comment") or "",
            "target": a.get("target") or "",
            "selectedText": a.get("selectedText") or "",
            "veld": a.get("veld") or "",
            "origineel": a.get("origineel") or "",
            "nieuw": a.get("nieuw") or "",
            "diff": a.get("diff") or [],
            "hunks": a.get("hunks") or [],
            "createdAt": a.get("createdAt"),
            # anker is verdacht zodra de pagina sinds die annotatie gewijzigd is
            "stale": bool(a.get("contentHash")) and a.get("contentHash") != h,
        })
    return {"ok": True, "round": nr, "dir": ronde_map, "jsonPath": json_pad,
            "count": len(open_ann),
            "total": len(lijst),
            "resolved": len(lijst) - len(open_ann),
            "maxNr": max([a.get("nr", 0) for a in lijst] or [0]),
            "annotations": open_ann,
            "exists": os.path.isfile(json_pad),
            "contentHash": h}


def h_resolve(payload):
    """Markeert annotaties als verwerkt (of draait dat terug met resolved:false).

    Body: {"jsonPath": "...", "nrs": [1,2]} of {"ids": [...]}, eventueel met
    {"resolved": false}. Zonder jsonPath wordt de lopende ronde van de pagina
    gebruikt (page/pageFile/slug, net als de andere routes).
    """
    json_pad = payload.get("jsonPath")
    if json_pad:
        json_pad = os.path.expanduser(json_pad)
        if not os.path.isfile(json_pad):
            raise ValueError("annotations.json niet gevonden: %s" % json_pad)
        with open(json_pad, "r", encoding="utf-8") as f:
            data = json.load(f)
        nr = data.get("round")
    else:
        nr, _ronde_map, json_pad, data, _bestand, _h = bepaal_ronde(payload)
        if not os.path.isfile(json_pad):
            raise ValueError("nog geen annotaties voor deze pagina")

    nrs = set(int(x) for x in (payload.get("nrs") or []))
    ids = set(str(x) for x in (payload.get("ids") or []))
    hunks = set(int(x) for x in (payload.get("hunks") or []))
    if hunks and len(nrs) != 1:
        # Een hunknummer is alleen betekenisvol binnen één bewerking; zonder die
        # koppeling zou "hunk 2" van drie annotaties tegelijk afgevinkt worden.
        raise ValueError("geef bij hunks precies één nr mee")
    if not nrs and not ids:
        raise ValueError("geef nrs of ids mee")
    waarde = payload.get("resolved", True) is not False
    nu = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    geraakt = []
    hunks_geraakt = []
    hunks_ontbreken = []
    for a in data.get("annotations", []):
        if not (a.get("nr") in nrs or str(a.get("id")) in ids):
            continue
        if hunks:
            # Alleen de genoemde blokken afvinken. De bewerking zelf geldt pas als
            # verwerkt zodra er geen enkel blok meer openstaat.
            gevonden = set()
            for h in a.get("hunks") or []:
                if h.get("n") in hunks:
                    h["resolved"] = waarde
                    gevonden.add(h.get("n"))
            hunks_geraakt = sorted(gevonden)
            hunks_ontbreken = sorted(hunks - gevonden)
            alle = a.get("hunks") or []
            a["resolved"] = bool(alle) and all(h.get("resolved") for h in alle)
            if a["resolved"]:
                a["resolvedAt"] = nu
            else:
                a.pop("resolvedAt", None)
            geraakt.append(a.get("nr"))
            continue
        a["resolved"] = waarde
        if waarde:
            a["resolvedAt"] = nu
        else:
            a.pop("resolvedAt", None)
        # de hele bewerking afvinken vinkt ook alle losse blokken af
        for h in a.get("hunks") or []:
            h["resolved"] = waarde
        geraakt.append(a.get("nr"))
    ontbreekt = sorted(nrs - set(geraakt))
    data["updatedAt"] = nu
    schrijf(json_pad, data)
    open_n = len([a for a in data.get("annotations", []) if not a.get("resolved")])
    uit = {"ok": True, "round": nr, "jsonPath": json_pad, "resolved": sorted(geraakt),
           "notFound": ontbreekt, "open": open_n,
           "total": len(data.get("annotations", []))}
    if hunks:
        uit["hunksResolved"] = hunks_geraakt
        uit["hunksNotFound"] = hunks_ontbreken
        uit["hunksOpen"] = sum(
            1 for a in data.get("annotations", []) for h in (a.get("hunks") or [])
            if not h.get("resolved"))
    return uit


def h_save(payload):
    ann = dict(payload.get("annotation") or {})
    nr, ronde_map, json_pad, data, bestand, h = bepaal_ronde(payload, maak=True)
    data["lastContentHash"] = h
    data["doc"] = payload.get("doc") or data.get("doc") or {}
    lijst = data.setdefault("annotations", [])

    bestaande = next((a for a in lijst if a.get("id") == ann.get("id")), None)
    nummer = bestaande.get("nr") if bestaande else (
        max([a.get("nr", 0) for a in lijst] or [0]) + 1)

    rec = {
        "nr": nummer,
        "type": ann.get("type") or ("text" if ann.get("selectedText") else "region"),
        "target": (ann.get("target") or "").strip(),
        "comment": (ann.get("comment") or "").strip(),
        "id": ann.get("id"),
        "createdAt": ann.get("createdAt") or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        # paginaversie waarop deze annotatie is gezet (context + stale-detectie)
        "contentHash": h,
    }
    if bestaande and bestaande.get("resolved"):
        rec["resolved"] = True
        rec["resolvedAt"] = bestaande.get("resolvedAt")

    if rec["type"] == "text":
        rec["selectedText"] = ann.get("selectedText") or ""
    elif rec["type"] == "edit":
        # Luc heeft de tekst van een conceptbericht zelf herschreven. Bewaren als
        # voor/na plus de losse wijzigingen, zodat een agent ziet wat er moet
        # veranderen zonder de twee versies te hoeven vergelijken. Geen crop: het
        # bewijs is de tekst zelf.
        rec["veld"] = (ann.get("veld") or "").strip()
        rec["origineel"] = ann.get("origineel") or ""
        rec["nieuw"] = ann.get("nieuw") or ""
        rec["diff"] = ann.get("diff") or []
        # Per hunk bewaren we of hij al verwerkt is. Bestond deze bewerking al, dan
        # blijven eerder afgevinkte hunks afgevinkt zolang ze inhoudelijk hetzelfde
        # zijn — anders zou een nieuwe wijziging elders het hele blok heropenen.
        oude_hunks = {}
        if bestaande:
            for h in bestaande.get("hunks") or []:
                sleutel = (h.get("verwijderd", ""), h.get("toegevoegd", ""))
                oude_hunks[sleutel] = h.get("resolved", False)
        hunks = []
        for h in ann.get("hunks") or []:
            h = dict(h)
            sleutel = (h.get("verwijderd", ""), h.get("toegevoegd", ""))
            h["resolved"] = oude_hunks.get(sleutel, False)
            hunks.append(h)
        rec["hunks"] = hunks
    else:
        rect = ann.get("rect") or {}
        rel = "screenshots/annotatie-%02d.png" % nummer
        rec["_rect"] = rect
        # Bewerkt Luc een annotatie die bij een oudere paginaversie hoort, dan zou
        # opnieuw croppen de goede oude crop overschrijven met het verkeerde gebied.
        # In dat geval de bestaande crop en hash laten staan.
        hergebruik = (bestaande and bestaande.get("image")
                      and bestaande.get("_rect") == rect
                      and bestaande.get("contentHash")
                      and bestaande["contentHash"] != h)
        if hergebruik:
            rec["image"] = bestaande["image"]
            rec["contentHash"] = bestaande["contentHash"]
        else:
            try:
                maak_crop(bestand, payload.get("page"), data["doc"], rect,
                          os.path.join(ronde_map, rel))
                rec["image"] = rel
            except Exception as e:  # crop mislukt: annotatie toch bewaren
                rec["image"] = None
                rec["imageError"] = str(e)[:200]

    # meegestuurde afbeelding (geplakt/bijgevoegd) als los bestand wegschrijven
    img = ann.get("img")
    if isinstance(img, str) and img.startswith("data:image"):
        kop, _, body = img.partition(",")
        ext = "png" if "png" in kop else ("jpg" if "jpeg" in kop or "jpg" in kop else "png")
        rel = "screenshots/annotatie-%02d-bijlage.%s" % (nummer, ext)
        try:
            os.makedirs(os.path.join(ronde_map, "screenshots"), exist_ok=True)
            with open(os.path.join(ronde_map, rel), "wb") as f:
                f.write(base64.b64decode(body))
            rec["attachment"] = rel
        except Exception:
            pass
    elif bestaande and bestaande.get("attachment"):
        # bijlage stond al op schijf; de pagina stuurt hem na een refresh niet opnieuw mee
        rec["attachment"] = bestaande["attachment"]

    if bestaande:
        lijst[lijst.index(bestaande)] = rec
    else:
        lijst.append(rec)
    data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    schrijf(json_pad, data)
    return {"ok": True, "round": nr, "jsonPath": json_pad, "nr": nummer,
            "image": rec.get("image"), "count": len(lijst)}


def h_delete(payload):
    nr, ronde_map, json_pad, data, _, _h = bepaal_ronde(payload)
    if not os.path.isfile(json_pad):
        return {"ok": True, "round": nr, "count": 0, "jsonPath": json_pad}
    lijst = data.get("annotations", [])
    weg = [a for a in lijst if a.get("id") == payload.get("id")]
    data["annotations"] = [a for a in lijst if a.get("id") != payload.get("id")]
    for a in weg:
        for sleutel in ("image", "attachment"):
            if a.get(sleutel):
                try:
                    os.remove(os.path.join(ronde_map, a[sleutel]))
                except OSError:
                    pass
    data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    schrijf(json_pad, data)
    return {"ok": True, "round": nr, "jsonPath": json_pad,
            "count": len(data["annotations"])}


def h_remove_all(payload):
    """Wist de lopende ronde en sluit hem af; de volgende annotatie opent ronde+1."""
    nr, ronde_map, json_pad, data, _, _h = bepaal_ronde(payload)
    if not os.path.isfile(json_pad):
        return {"ok": True, "round": nr, "cleared": 0, "nextRound": nr}
    aantal = len(data.get("annotations", []))
    shots = os.path.join(ronde_map, "screenshots")
    if os.path.isdir(shots):
        shutil.rmtree(shots, ignore_errors=True)
    os.makedirs(shots, exist_ok=True)
    data["annotations"] = []
    data["closed"] = True
    data["clearedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    schrijf(json_pad, data)
    return {"ok": True, "round": nr, "cleared": aantal, "nextRound": nr + 1,
            "jsonPath": json_pad}


def h_sessie(payload):
    """Opent een nieuwe Claude Code-sessie met een voorgeladen prompt.

    Nodig omdat een ingebedde browser custom schemes als claude:// niet aan het
    OS doorgeeft: een klik doet daar stilzwijgend niets. De bridge draait buiten
    de browser en kan `open` wel aanroepen.

    Bewust beperkt tot het claude-scheme, zodat dit geen algemene URL-opener
    wordt waarmee een willekeurige pagina van alles kan starten.
    """
    url = (payload.get("url") or "").strip()
    if not url:
        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            raise ValueError("geef url of prompt mee")
        url = "claude://code/new?q=" + urllib.parse.quote(prompt)
    if not url.startswith("claude://"):
        raise ValueError("alleen claude:// is toegestaan")
    subprocess.run(["open", url], check=True, capture_output=True, timeout=20)
    return {"ok": True, "geopend": url[:80] + ("..." if len(url) > 80 else "")}


ROUTES = {"/session": h_session, "/save": h_save, "/delete": h_delete,
          "/remove-all": h_remove_all, "/resolve": h_resolve,
          "/sessie": h_sessie}


class Handler(BaseHTTPRequestHandler):
    server_version = "LucAnnotatorBridge/2.0"

    def log_message(self, fmt, *args):
        # Origin/Referer meeloggen: dat is de enige manier om vast te stellen vanaf welke
        # origin een ingebedde weergave (preview-pane, sideviewer) de bridge aanroept.
        # Zonder die waarde blijft elke uitspraak daarover een aanname. Zie tests/criteria.md, AC-4.
        try:
            herkomst = self.headers.get("Origin") or self.headers.get("Referer") or ""
        except Exception:
            herkomst = ""
        sys.stderr.write("[bridge] %s%s\n" % (fmt % args, (" origin=%s" % herkomst) if herkomst else ""))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _bestand(self, pad):
        """Serveert een lokaal bestand, zodat de pagina same-origin met de bridge draait."""
        if not os.path.isfile(pad):
            return self._json(404, {"ok": False, "error": "bestand niet gevonden: %s" % pad})
        soort = {
            ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
            ".json": "application/json; charset=utf-8",
        }.get(os.path.splitext(pad)[1].lower(), "application/octet-stream")
        with open(pad, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", soort)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        pad = self.path.split("?")[0]
        if pad == "/ping":
            return self._json(200, {"ok": True, "bridge": "luc-annotator", "version": 2,
                                    "root": ROOT, "pillow": HEEFT_PILLOW})
        # /p/<pad-vanaf-home> serveert een lokale pagina same-origin met de bridge.
        # Voorbeeld: http://127.0.0.1:8791/p/Desktop/todos.html
        if pad.startswith("/p/"):
            rel = urllib.parse.unquote(pad[3:])
            doel = os.path.realpath(os.path.join(os.path.expanduser("~"), rel))
            # nooit buiten de home-map serveren
            if not doel.startswith(os.path.realpath(os.path.expanduser("~")) + os.sep):
                return self._json(403, {"ok": False, "error": "pad buiten home"})
            return self._bestand(doel)
        self._json(404, {"ok": False, "error": "onbekend pad"})

    def do_POST(self):
        pad = self.path.split("?")[0]
        fn = ROUTES.get(pad)
        if not fn:
            return self._json(404, {"ok": False, "error": "onbekend pad"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._json(400, {"ok": False, "error": "ongeldige body: %s" % e})
        try:
            with LOCK:
                self._json(200, fn(payload))
        except ValueError as e:
            # verkeerde of ontbrekende invoer is een clientfout, geen serverfout
            self._json(400, {"ok": False, "error": str(e)[:300]})
        except Exception as e:
            self._json(500, {"ok": False, "error": str(e)[:300]})


def main():
    os.makedirs(ROOT, exist_ok=True)
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print("Annotator-bridge luistert op http://%s:%d (root: %s, pillow: %s)"
          % (HOST, PORT, ROOT, HEEFT_PILLOW))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nGestopt.")


if __name__ == "__main__":
    main()
