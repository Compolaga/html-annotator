#!/usr/bin/env bash
# C6: A1/A2/A6 moeten rood worden als de layout-eis stuk is.
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
if [ "$rc" -eq 0 ]; then zeg 0 "ongemutileerd A1–A6 groen"
else zeg 1 "ongemutileerd A1–A6 niet groen"
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
  zeg 1 "A6 blijft groen met Luc in SKILL.md"
else
  zeg 0 "A6 wordt rood door een persoonsnaam"
fi
# herstel SKILL voor de install-mutanten
rsync -a "$ORIG/SKILL.md" "$werk/repo/SKILL.md"

python3 - <<'PY' "$werk/repo/install.sh"
import sys
p = sys.argv[1]
t = open(p).read()
oud = "      --exclude=bridge.log --exclude=bridge.pid --exclude=bridge-hook.log \\"
nieuw = "      --exclude=tests/node_modules \\"
if oud not in t:
    raise SystemExit("anker voor tar-exclude ontbreekt")
open(p, "w").write(t.replace(oud, nieuw, 1))
PY
# zorg dat er iets is om mee te kopiëren
: >> "$werk/repo/bridge.log"
if python3 ./test_layout.py >/tmp/ann-mut-layout-copy.txt 2>&1; then
  zeg 1 "A1 blijft groen als install.sh runtime meeneemt"
else
  zeg 0 "A1-install wordt rood als bridge.log meegekopieerd wordt"
fi
rsync -a "$ORIG/install.sh" "$werk/repo/install.sh"

python3 - <<'PY' "$werk/repo/install.sh"
import sys
p = sys.argv[1]
t = open(p).read()
oud = 'HOOK="$DOEL/bin/hook-ensure-bridge.sh"'
nieuw = 'HOOK="$DOEL/hook-ensure-bridge.sh"'
if oud not in t:
    raise SystemExit("anker voor hook-pad ontbreekt")
open(p, "w").write(t.replace(oud, nieuw, 1))
PY
if python3 ./test_layout.py >/tmp/ann-mut-layout-hook.txt 2>&1; then
  zeg 1 "A4 blijft groen als de hook buiten bin/ wijst"
else
  zeg 0 "A4 wordt rood als de geïnstalleerde hook niet bestaat"
fi
rsync -a "$ORIG/install.sh" "$werk/repo/install.sh"

printf '\nDraai python3 ~/.claude/skills/html-annotator/annotator_record.py\n' >> "$werk/repo/SKILL.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-oud.txt 2>&1; then
  zeg 1 "A4 blijft groen met een pre-bin pad"
else
  zeg 0 "A4 wordt rood door een pre-bin pad"
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

mkdir -p "$werk/repo/extras"
echo x > "$werk/repo/extras/x.md"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a3.txt 2>&1; then
  zeg 1 "A3 blijft groen met extras/"
else
  zeg 0 "A3 wordt rood als extras/ terugkomt"
fi
rm -rf "$werk/repo/extras"

echo 'x = 1' > "$werk/repo/annotator/foo-bar.py"
if python3 ./test_layout.py >/tmp/ann-mut-layout-a5.txt 2>&1; then
  zeg 1 "A5 blijft groen met een hyphen-module"
else
  zeg 0 "A5 wordt rood door een hyphen-modulenaam"
fi
rm -f "$werk/repo/annotator/foo-bar.py"

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
oud = "bin/toon-annotaties.py"
if oud not in t:
    raise SystemExit("anker voor toon-annotaties ontbreekt")
open(p, "w").write(t.replace(oud, "bin/show-annotations.py"))
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
