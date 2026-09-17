#!/usr/bin/env bash
# C6: A1–A9 moeten rood worden als de layout-eis stuk is. Elke mutant breekt
# precies één eis in een wegwerpkopie van de repo; blijft test_layout.py dan
# groen, dan bewijst die eis niets.
set -euo pipefail
ORIG="$(cd "$(dirname "$0")/.." && pwd)"
werk=$(mktemp -d)
trap 'rm -rf "$werk"' EXIT
rsync -a --exclude .git --exclude tests/node_modules --exclude __pycache__ \
  --exclude '*.pyc' --exclude bridge.log --exclude bridge.pid --exclude bridge-hook.log \
  "$ORIG"/ "$werk/repo/"
cd "$werk/repo/tests"

falen=0
zeg() {
  if [ "$1" = 0 ]; then echo "  PASS  mutate-layout: $2"
  else echo "  FAIL  mutate-layout: $2"; falen=1
  fi
}

set +e
python3 ./test_layout.py >/tmp/ann-mut-layout-ok.txt 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then zeg 0 "ongemutileerd A1–A9 groen"
else zeg 1 "ongemutileerd A1–A9 niet groen"; cat /tmp/ann-mut-layout-ok.txt
fi

echo 'los.py' > "$werk/repo/los.py"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a1.txt 2>&1; then
  zeg 1 "A1 blijft groen met een los bestand in root"
else
  zeg 0 "A1 wordt rood door een los root-bestand"
fi
rm -f "$werk/repo/los.py"

mkdir -p "$werk/repo/memories"
echo x > "$werk/repo/memories/x.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a2.txt 2>&1; then
  zeg 1 "A2 blijft groen met memories/"
else
  zeg 0 "A2 wordt rood als memories/ terugkomt"
fi
rm -rf "$werk/repo/memories"

printf '\nLuc wil dit zo.\n' >> "$werk/repo/SKILL.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a6.txt 2>&1; then
  zeg 1 "A6 blijft groen met een persoonsnaam in SKILL.md"
else
  zeg 0 "A6 wordt rood door een persoonsnaam"
fi
rsync -a "$ORIG/SKILL.md" "$werk/repo/SKILL.md"

# A3: extras/ mag bestaan, maar moet uitgelegd zijn en niet meegeïnstalleerd worden.
mv "$werk/repo/extras/README.md" "$werk/repo/extras/LEESMIJ.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a3.txt 2>&1; then
  zeg 1 "A3 blijft groen zonder extras/README.md"
else
  zeg 0 "A3 wordt rood als extras/ niet uitgelegd is"
fi
mv "$werk/repo/extras/LEESMIJ.md" "$werk/repo/extras/README.md"

python3 - <<'PY' "$werk/repo/html_annotator/install.py"
import sys
p = sys.argv[1]
t = open(p).read()
oud = 'EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", "extras"}'
nieuw = 'EXCLUDE_DIRS = {".git", "node_modules"}'
if oud not in t:
    raise SystemExit("anker voor de exclude-lijst ontbreekt")
open(p, "w").write(t.replace(oud, nieuw, 1))
PY
: >> "$werk/repo/bridge.log"
if python3 ./test_layout.py >/tmp/ann-mut-layout-copy.txt 2>&1; then
  zeg 1 "A1/A3 blijven groen als install-skill runtime en extras meeneemt"
else
  zeg 0 "A1/A3 worden rood als install-skill te veel kopieert"
fi
rsync -a "$ORIG/html_annotator/install.py" "$werk/repo/html_annotator/install.py"
rm -f "$werk/repo/bridge.log"

python3 - <<'PY' "$werk/repo/html_annotator/install.py"
import sys
p = sys.argv[1]
t = open(p).read()
oud = 'HOOK_SCRIPT = "bin/hook-ensure-bridge.py"'
nieuw = 'HOOK_SCRIPT = "hook-ensure-bridge.py"'
if oud not in t:
    raise SystemExit("anker voor het hook-pad ontbreekt")
open(p, "w").write(t.replace(oud, nieuw, 1))
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-hook.txt 2>&1; then
  zeg 1 "A4 blijft groen als de hook buiten bin/ wijst"
else
  zeg 0 "A4 wordt rood als de geregistreerde hook niet bestaat"
fi
rsync -a "$ORIG/html_annotator/install.py" "$werk/repo/html_annotator/install.py"

python3 - <<'PY' "$werk/repo/html_annotator/install.py"
import sys
p = sys.argv[1]
t = open(p).read()
oud = '''        hooks[event] = _zonder_annotator(hooks.get(event)) + [entry]'''
nieuw = '''        hooks[event] = list(hooks.get(event) or []) + [entry]'''
if oud not in t:
    raise SystemExit("anker voor de hook-dedup ontbreekt")
open(p, "w").write(t.replace(oud, nieuw, 1))
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-dubbel.txt 2>&1; then
  zeg 1 "A4 blijft groen als install-hooks zichzelf stapelt"
else
  zeg 0 "A4 wordt rood als install-hooks niet idempotent is"
fi
rsync -a "$ORIG/html_annotator/install.py" "$werk/repo/html_annotator/install.py"

printf '\nDraai python3 ~/.claude/skills/html-annotator/install.sh\n' >> "$werk/repo/SKILL.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-oud.txt 2>&1; then
  zeg 1 "A4 blijft groen met een pre-bin pad"
else
  zeg 0 "A4 wordt rood door een pad uit de bash-tijd"
fi
rsync -a "$ORIG/SKILL.md" "$werk/repo/SKILL.md"

python3 - <<'PY' "$werk/repo/.gitignore"
import sys
p = sys.argv[1]
regels = [r for r in open(p) if not r.startswith("bridge.log")]
open(p, "w").writelines(regels)
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-gi.txt 2>&1; then
  zeg 1 "A1 blijft groen als bridge.log uit .gitignore is"
else
  zeg 0 "A1 wordt rood als runtime niet in .gitignore staat"
fi
rsync -a "$ORIG/.gitignore" "$werk/repo/.gitignore"

echo 'x = 1' > "$werk/repo/html_annotator/foo-bar.py"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a5.txt 2>&1; then
  zeg 1 "A5 blijft groen met een hyphen-module"
else
  zeg 0 "A5 wordt rood door een hyphen-modulenaam"
fi
rm -f "$werk/repo/html_annotator/foo-bar.py"

printf '#!/bin/bash\necho hoi\n' > "$werk/repo/bin/doe-iets.sh"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a9.txt 2>&1; then
  zeg 1 "A9 blijft groen met bash in bin/"
else
  zeg 0 "A9 wordt rood door een shellscript in de core"
fi
rm -f "$werk/repo/bin/doe-iets.sh"

python3 - <<'PY' "$werk/repo/SKILL.md"
import sys
p = sys.argv[1]
t = open(p).read()
t = t.replace('a bare "." (period only)', "a message")
open(p, "w").write(t)
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-punt.txt 2>&1; then
  zeg 1 "A2 blijft groen zonder punt-trigger"
else
  zeg 0 "A2 wordt rood als de punt-trigger uit SKILL.md is"
fi
rsync -a "$ORIG/SKILL.md" "$werk/repo/SKILL.md"

python3 - <<'PY' "$werk/repo/SKILL.md"
import sys
p = sys.argv[1]
t = open(p).read()
oud = "bin/hook-ensure-bridge.py"
if oud not in t:
    raise SystemExit("anker voor de hook-verwijzing ontbreekt")
open(p, "w").write(t.replace(oud, "bin/bestaat-niet.py"))
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-binref.txt 2>&1; then
  zeg 1 "A4 blijft groen met een verzonnen bin-naam"
else
  zeg 0 "A4 wordt rood als een bin-ref nergens ligt"
fi
rsync -a "$ORIG/SKILL.md" "$werk/repo/SKILL.md"

printf '\nDit bestand wordt hieronder uitgelegd.\n' >> "$werk/repo/SKILL.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a8.txt 2>&1; then
  zeg 1 "A8 blijft groen met een Nederlandse zin in SKILL.md"
else
  zeg 0 "A8 wordt rood door Nederlands in een poort"
fi

exit $falen
