#!/usr/bin/env python3
"""B8–B9: toon-annotaties toont werkregel, refs en locator."""

import json
import os
import subprocess
import sys
import tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOON = os.path.join(SKILL, "bin", "toon-annotaties.py")


def check(naam, conditie):
    if not conditie:
        print("FAIL  %s" % naam)
        return 1
    print("PASS  %s" % naam)
    return 0


def draai(root, *args):
    env = os.environ.copy()
    env["LUC_ANNOTATOR_ROOT"] = root
    return subprocess.run(
        [sys.executable, TOON, *args],
        cwd=SKILL, env=env, capture_output=True, text=True,
    )


def main():
    n = 0
    root = tempfile.mkdtemp(prefix="ann-toon-")
    ronde = os.path.join(root, "demo-pagina", "ronde-01")
    os.makedirs(ronde)
    rec = {
        "page": "http://127.0.0.1:8791/p/Desktop/demo.html",
        "round": 1,
        "annotations": [
            {
                "nr": 1,
                "type": "text",
                "target": "cel A",
                "comment": "maak \u27e6r1\u27e7 gelijk aan \u27e6r2\u27e7",
                "selectedText": "cel A",
                "locator": {
                    "path": "tr:nth-of-type(3) > td.ei",
                    "label": "2.3 Gamma Backlog",
                    "nth": 1,
                    "start": {"path": "td.ei", "offset": 0},
                },
                "refs": [{"id": "r1", "selectedText": "cel B"}],
            }
        ],
    }
    with open(os.path.join(ronde, "annotations.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f)

    leeg = draai(tempfile.mkdtemp(prefix="ann-leeg-"))
    n += check("B8 geen root → exit 1", leeg.returncode == 1)

    uit = draai(root, "--open")
    n += check("B8 --open slaagt", uit.returncode == 0)
    n += check("B8 WERKREGEL", "eerst begrijpen, dan pas verwerken" in uit.stdout)
    n += check("B8 punt-trigger",
               'Een kaal bericht "." is "verwerk mijn annotaties"' in uit.stdout)
    n += check("B8 locator-pad", "tr:nth-of-type(3) > td.ei" in uit.stdout)
    n += check("B8 locator nth", "nth 1" in uit.stdout)
    n += check("B8 context-label", "2.3 Gamma Backlog" in uit.stdout)
    n += check("B8 ref geëxpandeerd", "cel B" in uit.stdout)
    n += check("B9 ontbrekende r2", "ONTBREEKT" in uit.stdout and "r2" in uit.stdout)
    n += check("B8 resolve-hint", "/resolve" in uit.stdout)

    rec["annotations"][0]["resolved"] = True
    rec["annotations"][0]["resolvedAt"] = "2026-08-23"
    with open(os.path.join(ronde, "annotations.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f)
    uit2 = draai(root, "--open")
    n += check("B8 resolved verborgen",
               uit2.returncode == 0
               and "maak" not in uit2.stdout
               and "(niets open)" in uit2.stdout
               and "eerst begrijpen" not in uit2.stdout)
    return n


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
