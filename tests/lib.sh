#!/bin/bash
# Gedeelde helpers voor de bridge-tests. Source dit, draai het niet.

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$TESTS_DIR/.." && pwd)"
PORT="${LUC_ANNOTATOR_PORT:-8791}"
BRIDGE_URL="http://127.0.0.1:$PORT"

ping_bridge() { curl -fsS --max-time 2 "$BRIDGE_URL/ping" 2>/dev/null; }

# Pid van wie er op de poort luistert. Leeg = niemand. Bewust via lsof en niet via
# bridge.pid: die pidfile is regelmatig stale.
bridge_pid() { lsof -tnP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -1; }

# Bridge hard omlaag, en pas terugkomen als de poort echt vrij is.
bridge_down() {
  local pids
  for _ in $(seq 1 30); do
    pids=$(lsof -tnP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null)
    [ -z "$pids" ] && [ -z "$(ping_bridge)" ] && return 0
    [ -n "$pids" ] && kill $pids 2>/dev/null
    sleep 0.2
  done
  echo "bridge_down: poort $PORT blijft bezet door pid(s) $(bridge_pid)" >&2
  return 1
}

bridge_up() { "$SKILL_DIR/bin/ensure-bridge.sh" >/dev/null 2>&1; [ -n "$(ping_bridge)" ]; }

# Wacht tot de bridge antwoordt. $1 = seconden (default 5).
wait_for_bridge() {
  local deadline=$(( $(date +%s) + ${1:-5} ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    [ -n "$(ping_bridge)" ] && return 0
    sleep 0.2
  done
  return 1
}

# Het snippet, om in een testpagina te plakken.
snippet() { cat "$SKILL_DIR/references/annotator-snippet.html"; }

# Pad naar de rondemap van een slug, of leeg als die niet bestaat.
laatste_ronde_json() {
  local slug="$1" dir="$HOME/Desktop/annotaties/$slug"
  [ -d "$dir" ] || return 1
  local r
  r=$(ls -1 "$dir" 2>/dev/null | grep -E '^ronde-[0-9]+$' | sort | tail -1)
  [ -n "$r" ] || return 1
  echo "$dir/$r/annotations.json"
}

# Testpagina's krijgen een eigen slug per run, zodat een test nooit op de rondes van
# een echte pagina van Luc gaat zitten en nooit op resten van een vorige run.
test_slug() { echo "zz-test-$1-$(date +%s)-$$"; }

pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; }
