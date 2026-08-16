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

DIR="$HOME/.claude/skills/html-annotator"

file=$(/usr/bin/python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("")
else:
    print(d.get("tool_input", {}).get("file_path", "") or "")
' 2>/dev/null)

[ -n "$file" ] || exit 0

case "$file" in
  *.html|*.htm) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0
grep -q "LUC-ANNOTATOR" "$file" 2>/dev/null || exit 0

"$DIR/ensure-bridge.sh" >>"$DIR/bridge-hook.log" 2>&1

exit 0
