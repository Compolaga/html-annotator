#!/bin/bash
# PostToolUse-hook (Write|Edit) uit ~/.claude/settings.json.
# Start de annotator-bridge zodra een geschreven/bewerkt HTML-bestand de
# LUC-ANNOTATOR-marker bevat. Draait in de gewone gebruikerssessie, dus geen
# TCC-problemen met ~/Desktop (in tegenstelling tot launchd/cron).
#
# Goedkoop en stil: niet-HTML-bestanden vallen direct af, daarna één grep;
# ensure-bridge.sh is idempotent. Exit altijd 0: dit mag nooit een tool-call
# laten falen.

set -u

# python3 uit PATH, anders python (Git Bash op Windows kent vaak alleen `python`).
zoek_python() {
  local c
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}

BIN="$(cd "$(dirname "$0")" && pwd)"
DIR="$(cd "$BIN/.." && pwd)"

PY=$(zoek_python) || exit 0
gelezen=$("$PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("\t")
else:
    print("%s\t%s" % (d.get("hook_event_name", ""),
                      d.get("tool_input", {}).get("file_path", "") or ""))
' 2>/dev/null)

event=${gelezen%%$'\t'*}
file=${gelezen#*$'\t'}

# SessionStart: één keer per sessie de bridge omhoog, ongeacht hoe deze sessie straks
# HTML wegschrijft. De PostToolUse-tak hieronder ziet alleen Edit/Write en mist dus een
# agent die het bestand via Bash wegschrijft — in auto-mode juist de voorgeschreven
# route. Zie tests/case-04.
if [ "$event" = "SessionStart" ]; then
  "$BIN/ensure-bridge.sh" >>"$DIR/bridge-hook.log" 2>&1
  exit 0
fi

[ -n "$file" ] || exit 0

case "$file" in
  *.html|*.htm) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0
grep -q "LUC-ANNOTATOR" "$file" 2>/dev/null || exit 0

"$BIN/ensure-bridge.sh" >>"$DIR/bridge-hook.log" 2>&1

exit 0
