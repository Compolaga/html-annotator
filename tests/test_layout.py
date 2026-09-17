#!/usr/bin/env python3
"""A1–A9: de repo ziet eruit als een installeerbare skill, niet als een
persoonlijke scriptbak — en de core draait zonder bash."""

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A1: ports. Snippet and handbook live in references/. Decisions in docs/.
ROOT_OK = {
    "README.md", "SKILL.md", "INSTALL.md", "CRITERIA.md", ".gitignore",
}
ROOT_DIRS_OK = {"html_annotator", "bin", "references", "tests", "docs",
                "extras", ".git"}

# Agent-facing: what a stranger or installer reads. No tests/, no docs/
# history, no extras/.
AGENT_FILES = ("SKILL.md", "README.md", "INSTALL.md", "CRITERIA.md")
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
DOT_OK = {".gitignore", ".git", ".github", ".claude"}
OUD_NAMEN = (
    "annotator_config.py", "annotator_record.py", "annotator_refs.py",
    "annotator-bridge.py", "ensure-bridge.sh", "hook-ensure-bridge.sh",
    "toon-annotaties.py", "pas-hunk-toe.py", "vind-todolijst.sh",
    "install.sh",
)
OUD_PAD = re.compile(
    r"(?:skills/html-annotator/|\$DOEL/|\./)"
    r"(?!bin/|html_annotator/)"
    r"(?:%s)" % "|".join(re.escape(n) for n in OUD_NAMEN)
)
BIN_REF = re.compile(r"\bbin/([A-Za-z0-9._-]+\.(?:py|sh))\b")
# A8: ports only. Handbook and WERKREGEL stay Dutch (docs/DECISIONS.md).
PORT_EN = ("SKILL.md", "README.md", "INSTALL.md", "CRITERIA.md")
NL = re.compile(
    r"\b(worden|wordt|bestand|draai|hieronder|wanneer|voordat|nadat|tenzij|volgende)\b",
    re.I,
)
# A9: geen bash in de core. tests/ mag bash houden voor de Playwright-suite.
BASH_VRIJ = ("html_annotator", "bin", "references", "docs", ".github")


def heeft_oud_pad(tekst):
    return bool(OUD_PAD.search(tekst))


def ontbrekende_bin_refs():
    miss = []
    for pad in agent_paden():
        tekst = open(pad, encoding="utf-8").read()
        for m in BIN_REF.finditer(tekst):
            naam = m.group(1)
            if not os.path.isfile(os.path.join(ROOT, "bin", naam)):
                miss.append("%s → bin/%s" % (os.path.relpath(pad, ROOT), naam))
    return miss


def nederlandse_poorten():
    hit = []
    for rel in PORT_EN:
        pad = os.path.join(ROOT, rel)
        if not os.path.isfile(pad):
            continue
        if NL.search(open(pad, encoding="utf-8").read()):
            hit.append(rel)
    return hit


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
    for sub in ("bin", "html_annotator"):
        d = os.path.join(ROOT, sub)
        if os.path.isdir(d):
            for naam in sorted(os.listdir(d)):
                if naam.endswith((".py", ".sh")):
                    paden.append(os.path.join(d, naam))
    return [p for p in paden if os.path.isfile(p)]


def shell_scripts_in_core():
    hit = []
    for sub in BASH_VRIJ:
        for dirpad, dirs, files in os.walk(os.path.join(ROOT, sub)):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules")]
            for f in files:
                if f.endswith((".sh", ".bash")):
                    hit.append(os.path.relpath(os.path.join(dirpad, f), ROOT))
    for f in os.listdir(ROOT):
        if f.endswith((".sh", ".bash")):
            hit.append(f)
    return sorted(hit)


def check(naam, conditie):
    if not conditie:
        print("FAIL  %s" % naam)
        return 1
    print("PASS  %s" % naam)
    return 0


def cli(home, *args):
    """Draait de CLI met een eigen HOME, zoals een verse install."""
    env = os.environ.copy()
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["XDG_STATE_HOME"] = os.path.join(home, ".local", "state")
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "html_annotator", *args],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


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
    n += check("A3 extras/ heeft een README",
               os.path.isfile(os.path.join(ROOT, "extras", "README.md")))
    n += check("A3 scope-document", os.path.isfile(os.path.join(ROOT, "docs", "SCOPE.md")))
    n += check("A4 bin/ bestaat", os.path.isdir(os.path.join(ROOT, "bin")))
    n += check("A4 html_annotator-pakket",
               os.path.isfile(os.path.join(ROOT, "html_annotator", "__init__.py"))
               and os.path.isfile(os.path.join(ROOT, "html_annotator", "__main__.py")))

    for verplicht in (
        "bin/ensure-bridge.py",
        "bin/hook-ensure-bridge.py",
        "bin/annotator-bridge.py",
        "bin/toon-annotaties.py",
        "bin/pas-hunk-toe.py",
    ):
        n += check("A4 %s" % verplicht, os.path.isfile(os.path.join(ROOT, verplicht)))

    oud = []
    for pad in agent_paden():
        if heeft_oud_pad(open(pad, encoding="utf-8").read()):
            oud.append(os.path.relpath(pad, ROOT))
    n += check("A4 geen pre-bin paden", oud == [])
    if oud:
        print("      oude paden in: %s" % ", ".join(oud))
    bin_miss = ontbrekende_bin_refs()
    n += check("A4 bin-refs bestaan", bin_miss == [])
    if bin_miss:
        print("      ontbreekt: %s" % ", ".join(bin_miss))

    n += check("A5 geen hyphen-module in html_annotator/", not any(
        f.endswith(".py") and "-" in f
        for f in os.listdir(os.path.join(ROOT, "html_annotator"))
    ))
    n += check("A5 bin kebab-case", all(
        "_" not in f
        for f in os.listdir(os.path.join(ROOT, "bin"))
        if f.endswith((".py", ".sh"))
    ))

    luc = []
    for pad in agent_paden():
        tekst = ALLOW.sub("", open(pad, encoding="utf-8").read())
        if NAAM.search(tekst):
            luc.append(os.path.relpath(pad, ROOT))
    n += check("A6 geen persoonsnaam in agent-facing docs", luc == [])
    if luc:
        print("      nog een persoonsnaam in: %s" % ", ".join(luc))
    nl = nederlandse_poorten()
    n += check("A8 poorten Engels", nl == [])
    if nl:
        print("      Nederlands in: %s" % ", ".join(nl))

    sh = shell_scripts_in_core()
    n += check("A9 geen bash in de core", sh == [])
    if sh:
        print("      shell-scripts: %s" % ", ".join(sh))

    home = tempfile.mkdtemp(prefix="ann-inst-")
    uit = cli(home, "install-skill", "--copy")
    dest = os.path.join(home, ".claude", "skills", "html-annotator")
    n += check("A3 install zonder memories/",
               uit.returncode == 0 and not os.path.isdir(os.path.join(dest, "memories")))
    if uit.returncode != 0:
        print("      install-skill rc=%s\n%s\n%s" % (uit.returncode, uit.stdout, uit.stderr))
    n += check("A3 install zonder extras/", not os.path.isdir(os.path.join(dest, "extras")))
    runtime_mee = [naam for naam in RUNTIME if os.path.exists(os.path.join(dest, naam))]
    n += check("A1 install zonder runtime", runtime_mee == [])
    if runtime_mee:
        print("      meegekopieerd: %s" % ", ".join(runtime_mee))
    n += check("A4 install-skill is idempotent", cli(home, "install-skill", "--copy").returncode == 0)

    droog = cli(home, "install-hooks", "--print")
    n += check("A4 install-hooks --print schrijft niets",
               droog.returncode == 0
               and "hook-ensure-bridge.py" in droog.stdout
               and not os.path.isfile(os.path.join(home, ".claude", "settings.local.json")))
    uit2 = cli(home, "install-hooks")
    settings = os.path.join(home, ".claude", "settings.local.json")
    hook_ok = False
    events = set()
    if os.path.isfile(settings):
        d = json.load(open(settings, encoding="utf-8"))
        for event, groepen in (d.get("hooks") or {}).items():
            for g in groepen:
                for h in g.get("hooks") or []:
                    c = h.get("command") or ""
                    if "hook-ensure-bridge.py" in c:
                        events.add(event)
                        pad = c.split('" "')[-1].strip('"')
                        if os.path.isfile(pad):
                            hook_ok = True
    n += check("A4 install-hook bestaat", uit2.returncode == 0 and hook_ok)
    n += check("A4 beide hook-events",
               events == {"PostToolUse", "SessionStart"})
    # Nog een keer: geen dubbele registratie.
    cli(home, "install-hooks")
    d = json.load(open(settings, encoding="utf-8"))
    aantal = sum(
        1
        for groepen in (d.get("hooks") or {}).values()
        for g in groepen
        for h in (g.get("hooks") or [])
        if "hook-ensure-bridge.py" in (h.get("command") or "")
    )
    n += check("A4 install-hooks idempotent", aantal == 2)
    return n


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
