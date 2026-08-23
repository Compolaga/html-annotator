#!/bin/bash
# Zorgt dat de annotator-bridge draait. Idempotent: al draaiend = niets doen.
# Aanroepen bij elke HTML-oplevering, direct na het inplakken van het snippet.
#
#   ~/.claude/skills/html-annotator/ensure-bridge.sh
#
# De bridge wordt losgekoppeld van de aanroepende shell gestart, zodat hij
# blijft draaien nadat de sessie of het terminalvenster verdwijnt.

set -uo pipefail

PORT="${LUC_ANNOTATOR_PORT:-8791}"
DIR="$HOME/.claude/skills/html-annotator"
BRIDGE="$DIR/annotator-bridge.py"
LOG="$DIR/bridge.log"
PIDFILE="$DIR/bridge.pid"

ping_bridge() {
  curl -fsS --max-time 2 "http://127.0.0.1:$PORT/ping" 2>/dev/null
}

# Draait hij al? Dan zijn we klaar.
if ping_bridge >/dev/null; then
  echo "bridge draait al op 127.0.0.1:$PORT"
  exit 0
fi

if [ ! -f "$BRIDGE" ]; then
  echo "FOUT: $BRIDGE niet gevonden" >&2
  exit 1
fi

# Stale pidfile van een gestorven proces opruimen.
if [ -f "$PIDFILE" ] && ! kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  rm -f "$PIDFILE"
fi

# Losgekoppeld starten. nohup + & maakt hem onafhankelijk van deze shell.
nohup python3 "$BRIDGE" >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
disown 2>/dev/null || true

# Wachten tot hij antwoordt, maximaal 5 seconden.
for _ in $(seq 1 25); do
  if ping_bridge >/dev/null; then
    echo "bridge gestart op 127.0.0.1:$PORT (pid $(cat "$PIDFILE"))"
    exit 0
  fi
  sleep 0.2
done

echo "FOUT: bridge reageert niet binnen 5s. Laatste logregels:" >&2
tail -n 15 "$LOG" >&2
exit 1
