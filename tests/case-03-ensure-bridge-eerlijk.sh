#!/bin/bash
# AC-3: ensure-bridge.sh mag nooit met exitcode 0 eindigen terwijl er geen bridge
# antwoordt. Aanleiding: bridge.log bevat "OSError: [Errno 48] Address already in use"
# tracebacks terwijl bridge-hook.log op dezelfde momenten succes meldt.
#
# Opzet: poort 8791 bezetten met een luisteraar die géén bridge is, en kijken wat het
# script dan doet. Het mag falen; het mag niet liegen.

set -uo pipefail
source "$(dirname "$0")/lib.sh"

echo "case-03: ensure-bridge.sh liegt niet over een bezette poort"

if ! bridge_down; then
  fail "kon de bridge niet omlaag krijgen; test zegt niets"
  exit 2
fi

# Kale TCP-luisteraar op de poort: accepteert verbindingen, spreekt geen HTTP.
python3 - "$PORT" <<'PY' &
import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", int(sys.argv[1])))
s.listen(5)
time.sleep(60)
PY
BEZETTER=$!
trap 'kill $BEZETTER 2>/dev/null' EXIT

for _ in $(seq 1 25); do
  [ -n "$(bridge_pid)" ] && break
  sleep 0.2
done
if [ -z "$(bridge_pid)" ]; then
  fail "kon de poort niet bezetten; test zegt niets"
  exit 2
fi

"$SKILL_DIR/ensure-bridge.sh" >/dev/null 2>&1
EXIT_CODE=$?
ANTWOORD=$(ping_bridge)

RC=0
if [ "$EXIT_CODE" -eq 0 ] && [ -z "$ANTWOORD" ]; then
  fail "ensure-bridge.sh meldde succes (exit 0) terwijl /ping niets teruggeeft"
  RC=1
else
  pass "exit $EXIT_CODE past bij de werkelijkheid (ping: ${ANTWOORD:-leeg})"
fi

exit $RC
