#!/bin/bash
# AC-2a: de bridge komt omhoog zonder dat het uitmaakt hoe de agent de HTML wegschrijft.
#
# Waarom deze case bestaat: de PostToolUse-hook hangt aan Edit|Write. Een agent die het
# bestand via Bash wegschrijft (heredoc, python, sed) triggert hem dus nooit — en in
# auto-mode is Bash juist de voorgeschreven route. Dit is het deterministische deel van
# AC-2: geen model, geen k/n, geen kosten. Het gedragsdeel (levert een verse agent het
# echt goed op?) staat in case-01.
#
# Twee assertions, want het kan op twee plekken misgaan:
#   1. de registratie — is er een hook die niet van de schrijfroute afhangt?
#   2. het gedrag — brengt die geregistreerde hook de bridge daadwerkelijk omhoog?
# Alleen 1 zonder 2 is een hook die er staat en niets doet.

set -uo pipefail
source "$(dirname "$0")/lib.sh"

echo "case-04: bridge komt omhoog los van de schrijfroute"
RC=0

# --- 1. registratie ----------------------------------------------------------
GEVONDEN=$(python3 - <<'PY'
import json, os
pad = os.path.expanduser("~/.claude")
treffers = []
for naam in ("settings.json", "settings.local.json"):
    try:
        d = json.load(open(os.path.join(pad, naam)))
    except Exception:
        continue
    for ev, groepen in d.get("hooks", {}).items():
        for g in groepen:
            for h in g.get("hooks", []):
                c = h.get("command", "")
                if "ensure-bridge" in c:
                    vlag = "ok" if os.path.isfile(c) else "WEG"
                    treffers.append("%s:%s:%s:%s" % (naam, ev, g.get("matcher", ""), vlag))
print("\n".join(treffers))
PY
)

# Een route die niet van de schrijfroute afhangt: SessionStart (eens per sessie), of een
# PostToolUse-matcher die Bash meeneemt.
if echo "$GEVONDEN" | grep -q "WEG"; then
  fail "hook wijst naar een bestand dat er niet is: ${GEVONDEN}"
  RC=1
elif echo "$GEVONDEN" | grep -q "SessionStart"; then
  pass "hook geregistreerd op SessionStart (bestand bestaat)"
elif echo "$GEVONDEN" | grep -qE "PostToolUse:.*Bash"; then
  pass "PostToolUse-matcher neemt Bash mee"
else
  fail "alleen schrijfroute-afhankelijke registratie gevonden: ${GEVONDEN:-geen}"
  RC=1
fi

# --- 2. gedrag ---------------------------------------------------------------
# De geregistreerde SessionStart-hook echt aanroepen met een SessionStart-payload, met de
# bridge aantoonbaar omlaag. Dit toetst het commando zoals de harness het zou draaien.
COMMANDO=$(python3 - <<'PY'
import json, os
pad = os.path.expanduser("~/.claude")
for naam in ("settings.json", "settings.local.json"):
    try:
        d = json.load(open(os.path.join(pad, naam)))
    except Exception:
        continue
    for g in d.get("hooks", {}).get("SessionStart", []):
        for h in g.get("hooks", []):
            cmd = h.get("command", "")
            if "ensure-bridge" in cmd and os.path.isfile(cmd):
                print(cmd); raise SystemExit
PY
)

if [ -z "$COMMANDO" ]; then
  fail "geen SessionStart-hook om te draaien, dus gedrag niet te toetsen"
  exit $((RC == 0 ? 1 : RC))
fi

if ! bridge_down; then
  fail "kon de bridge niet omlaag krijgen; gedragsdeel zegt niets"
  exit 2
fi

echo '{"hook_event_name":"SessionStart","source":"startup","cwd":"'"$HOME"'"}' \
  | $COMMANDO >/dev/null 2>&1

if wait_for_bridge 8; then
  pass "SessionStart-hook bracht de bridge omhoog (pid $(bridge_pid))"
else
  fail "SessionStart-hook liet de bridge omlaag"
  RC=1
fi

# --- 3. de oude route mag niet gesneuveld zijn -------------------------------
# De SessionStart-tak is in hetzelfde script gebouwd als de PostToolUse-tak. Die tak was
# het bestaande vangnet en moet blijven werken; anders ruilt deze fix het ene gat voor
# het andere.
if ! bridge_down; then
  fail "kon de bridge niet omlaag krijgen; PostToolUse-deel zegt niets"
  exit 2
fi
TIJDELIJK=$(mktemp "${TMPDIR:-/tmp}/annotator-case04.XXXXXX.html")
printf '<p>test</p>\n<!-- LUC-ANNOTATOR v2 -->\n' >"$TIJDELIJK"
printf '{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"%s"}}' "$TIJDELIJK" \
  | "$SKILL_DIR/bin/hook-ensure-bridge.sh" >/dev/null 2>&1
if wait_for_bridge 8; then
  pass "PostToolUse-tak (Write) brengt de bridge nog steeds omhoog"
else
  fail "PostToolUse-tak is gesneuveld door de SessionStart-uitbreiding"
  RC=1
fi
rm -f "$TIJDELIJK"

exit $RC
