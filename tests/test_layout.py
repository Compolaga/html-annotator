#!/usr/bin/env python3
"""A1–A6: de repo ziet eruit als een skill, niet als een persoonlijke scriptbak."""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A1: ports. Snippet and handbook live in references/. Decisions in docs/.
ROOT_OK = {
    "README.md", "SKILL.md", "INSTALL.md",
    "CRITERIA.md", "install.sh", ".gitignore",
}
ROOT_DIRS_OK = {"annotator", "bin", "references", "tests", "docs", ".git"}

# Agent-facing: what a stranger or installer reads. No tests/, no docs/
# history.
AGENT_FILES = (
    "SKILL.md", "README.md", "INSTALL.md", "CRITERIA.md", "install.sh",
)
# Identifiers die gedrag dragen: B1 assert luc-annotator; contentHash stript
# LUC-ANNOTATOR; window.LucAnnotator is de publieke API; env LUC_ANNOTATOR_*;
# localStorage-prefix luc-annotaties.
ALLOW = re.compile(
    r"LucAnnotator(?:Bridge)?|/?LUC-ANNOTATOR|luc-annotator|luc-annotaties|"
    r"LUC_ANNOTATOR_[A-Z0-9_*]+",
    re.I,
)
NAAM = re.compile(r"luc|luke", re.I)


RUNTIME = {"bridge.log", "bridge.pid", "bridge-hook.log", "__pycache__"}
DOT_OK = {".gitignore", ".git"}
OUD_NAMEN = (
    "annotator_config.py", "annotator_record.py", "annotator_refs.py",
    "annotator-bridge.py", "ensure-bridge.sh", "hook-ensure-bridge.sh",
    "toon-annotaties.py", "pas-hunk-toe.py", "vind-todolijst.sh",
)
OUD_PAD = re.compile(
    r"(?:skills/html-annotator/|\$DOEL/|\./)"
    r"(?!bin/|annotator/)"
    r"(?:%s)" % "|".join(re.escape(n) for n in OUD_NAMEN)
)


def heeft_oud_pad(tekst):
    return bool(OUD_PAD.search(tekst))


def gitignore_rootnamen():
    namen = set()
    pad = os.path.join(ROOT, ".gitignore")
    if not os.path.isfile(pad):
        return namen
    for regel in open(pad, encoding="utf-8"):
        regel = regel.strip()
        if not regel or regel.startswith("#"):
            continue
        if "/" in regel.rstrip("/"):
            continue
        namen.add(regel.rstrip("/").replace("\\", ""))
    return namen - {"*.pyc"}


def agent_paden():
    paden = [os.path.join(ROOT, rel) for rel in AGENT_FILES]
    ref = os.path.join(ROOT, "references")
    if os.path.isdir(ref):
        for naam in sorted(os.listdir(ref)):
            if naam.endswith((".md", ".html")):
                paden.append(os.path.join(ref, naam))
    bindir = os.path.join(ROOT, "bin")
    if os.path.isdir(bindir):
        for naam in sorted(os.listdir(bindir)):
            if naam.endswith((".py", ".sh")):
                paden.append(os.path.join(bindir, naam))
    return [p for p in paden if os.path.isfile(p)]


def check(naam, conditie):
    if not conditie:
        print("FAIL  %s" % naam)
        return 1
    print("PASS  %s" % naam)
    return 0


def main():
    n = 0
    namen = set(os.listdir(ROOT))
    runtime = set(RUNTIME)
    los = []
    for naam in sorted(namen):
        if naam.startswith("."):
            if naam not in DOT_OK:
                los.append(naam)
            continue
        if naam in runtime:
            continue
        pad = os.path.join(ROOT, naam)
        if os.path.isdir(pad):
            if naam not in ROOT_DIRS_OK:
                los.append(naam + "/")
            continue
        if naam not in ROOT_OK:
            los.append(naam)
    n += check("A1 root alleen poorten", los == [])
    if los:
        print("      nog in root: %s" % ", ".join(los))
    n += check("A1 snippet in references/",
               os.path.isfile(os.path.join(ROOT, "references", "annotator-snippet.html")))
    n += check("A1 .gitignore bestaat", os.path.isfile(os.path.join(ROOT, ".gitignore")))
    n += check("A1 gitignore-runtime is subset", gitignore_rootnamen() <= RUNTIME)
    n += check("A1 runtime staat in gitignore", RUNTIME <= gitignore_rootnamen())

    handbook = os.path.join(ROOT, "references", "agent-handbook.md")
    hb = open(handbook, encoding="utf-8").read() if os.path.isfile(handbook) else ""
    n += check("A2 geen memories/", "memories" not in namen)
    skill_md = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
    n += check("A2 agent rules in references/",
               os.path.isfile(handbook) and "/p/" in hb and "bare" in hb)
    n += check("A2 SKILL period trigger", 'a bare "."' in skill_md)
    n += check("A3 geen extras/", "extras" not in namen)
    n += check("A4 bin/ bestaat", os.path.isdir(os.path.join(ROOT, "bin")))
    n += check("A4 annotator-pakket", os.path.isfile(os.path.join(ROOT, "annotator", "__init__.py")))

    for verplicht in (
        "bin/ensure-bridge.sh",
        "bin/hook-ensure-bridge.sh",
        "bin/annotator-bridge.py",
        "bin/toon-annotaties.py",
        "bin/pas-hunk-toe.py",
        "bin/vind-todolijst.sh",
    ):
        n += check("A4 %s" % verplicht, os.path.isfile(os.path.join(ROOT, verplicht)))

    oud = []
    for pad in agent_paden():
        if heeft_oud_pad(open(pad, encoding="utf-8").read()):
            oud.append(os.path.relpath(pad, ROOT))
    n += check("A4 geen pre-bin paden", oud == [])
    if oud:
        print("      oude paden in: %s" % ", ".join(oud))

    n += check("A5 geen hyphen-module in annotator/", not any(
        f.endswith(".py") and "-" in f
        for f in os.listdir(os.path.join(ROOT, "annotator"))
        if os.path.isdir(os.path.join(ROOT, "annotator"))
    ) if os.path.isdir(os.path.join(ROOT, "annotator")) else False)
    n += check("A5 bin kebab-case", all(
        "_" not in f
        for f in os.listdir(os.path.join(ROOT, "bin"))
        if f.endswith((".py", ".sh"))
    ) if os.path.isdir(os.path.join(ROOT, "bin")) else False)

    luc = []
    for pad in agent_paden():
        tekst = ALLOW.sub("", open(pad, encoding="utf-8").read())
        if NAAM.search(tekst):
            luc.append(os.path.relpath(pad, ROOT))
    n += check("A6 geen persoonsnaam in agent-facing docs", luc == [])
    if luc:
        print("      nog Luc/Luke in: %s" % ", ".join(luc))

    import json
    import subprocess
    import tempfile
    home = tempfile.mkdtemp(prefix="ann-inst-")
    env = os.environ.copy()
    env["HOME"] = home
    uit = subprocess.run(
        ["bash", os.path.join(ROOT, "install.sh"), "--copy"],
        env=env, capture_output=True, text=True,
    )
    dest = os.path.join(home, ".claude", "skills", "html-annotator")
    n += check("A3 install zonder memories/", uit.returncode == 0 and not os.path.isdir(os.path.join(dest, "memories")))
    n += check("A3 install zonder extras/", not os.path.isdir(os.path.join(dest, "extras")))
    runtime_mee = [naam for naam in RUNTIME if os.path.exists(os.path.join(dest, naam))]
    n += check("A1 install zonder runtime", runtime_mee == [])
    if runtime_mee:
        print("      meegekopieerd: %s" % ", ".join(runtime_mee))
    settings = os.path.join(home, ".claude", "settings.local.json")
    hook_ok = False
    if os.path.isfile(settings):
        d = json.load(open(settings, encoding="utf-8"))
        for groepen in (d.get("hooks") or {}).values():
            for g in groepen:
                for h in g.get("hooks") or []:
                    c = h.get("command") or ""
                    if "ensure-bridge" in c and os.path.isfile(c):
                        hook_ok = True
    heeft_jq = subprocess.run(["bash", "-lc", "command -v jq"], capture_output=True).returncode == 0
    if heeft_jq:
        n += check("A4 install-hook bestaat", hook_ok)
        stale = tempfile.mkdtemp(prefix="ann-stale-")
        env2 = os.environ.copy()
        env2["HOME"] = stale
        dest2 = os.path.join(stale, ".claude", "skills", "html-annotator")
        os.makedirs(dest2)
        open(os.path.join(dest2, "OUD"), "w").write("x")
        uit2 = subprocess.run(
            ["bash", os.path.join(ROOT, "install.sh"), "--copy"],
            env=env2, capture_output=True, text=True,
        )
        hook2 = os.path.join(dest2, "bin", "hook-ensure-bridge.sh")
        n += check("A4 --copy ververst stale doel",
                   uit2.returncode == 0 and os.path.isfile(hook2))
    else:
        n += check("A4 install zegt jq ontbreekt",
                   "jq not found" in (uit.stdout + uit.stderr))
    return n


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
