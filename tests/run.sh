#!/bin/bash
# Runner voor de annotator-bridge-suite.
#
#   tests/run.sh                # alles, case-01 met de vastgelegde drempel
#   tests/run.sh 02 03          # alleen deze cases
#   CASE01_RUNS=1 tests/run.sh  # goedkoper draaien tijdens ontwikkelen
#
# Uitgangspunten die deze runner bewust hardmaakt:
# - Een case die niet kón draaien (exit 2) is geen pass. Hij wordt als BLOKKED geteld
#   en de suite eindigt rood, want een test die niets deed bewijst niets.
# - Case-01 test agent-gedrag en is dus flaky. De drempel staat vooraf vast in
#   criteria.md: alle runs moeten slagen. k/n wordt altijd afgedrukt.
# - Wat de suite NIET dekt wordt afgedrukt, zodat groen niet als volledige dekking leest.

set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

CASE01_RUNS="${CASE01_RUNS:-3}"
GEVRAAGD=("$@")
wil() { [ ${#GEVRAAGD[@]} -eq 0 ] && return 0; for g in "${GEVRAAGD[@]}"; do [ "$g" = "$1" ] && return 0; done; return 1; }

BRIDGE_BIJ_START=$(bridge_pid)
FALEN=0
BLOKKED=0
echo "=== annotator-bridge suite · $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "snippet: $(shasum -a 256 ../annotator-snippet.html | cut -c1-12)  hook: $(shasum -a 256 ../hook-ensure-bridge.sh | cut -c1-12)  ensure: $(shasum -a 256 ../ensure-bridge.sh | cut -c1-12)"
echo

if wil 02; then
  if [ ! -d node_modules/playwright-core ]; then
    echo "BLOKKED case-02: playwright-core ontbreekt. Installeer met:"
    echo "  (cd ~/.claude/skills/html-annotator/tests && npm i --no-save playwright-core)"
    BLOKKED=$((BLOKKED + 1))
  else
    node ./case-02-selfheal.mjs
    [ $? -ne 0 ] && FALEN=$((FALEN + 1))
    # Verborgen paneel: Luc's eigenlijke situatie, want het sideview-paneel staat er
    # terwijl hij in de chat typt. Alleen de file-origin; data: is daar al afgedekt.
    CASE02_ORIGINS=file CASE02_VERBORGEN=1 node ./case-02-selfheal.mjs
    rc=$?
    [ $rc -eq 2 ] && BLOKKED=$((BLOKKED + 1))
    [ $rc -eq 1 ] && FALEN=$((FALEN + 1))
  fi
  echo
fi

if wil 03; then
  ./case-03-ensure-bridge-eerlijk.sh
  rc=$?
  [ $rc -eq 2 ] && BLOKKED=$((BLOKKED + 1))
  [ $rc -eq 1 ] && FALEN=$((FALEN + 1))
  echo
fi

if wil 04; then
  ./case-04-bridge-omhoog-los-van-schrijfroute.sh
  rc=$?
  [ $rc -eq 2 ] && BLOKKED=$((BLOKKED + 1))
  [ $rc -eq 1 ] && FALEN=$((FALEN + 1))
  echo
fi

if wil 01; then
  geslaagd=0
  geblokkeerd=0
  for i in $(seq 1 "$CASE01_RUNS"); do
    echo "case-01 run $i/$CASE01_RUNS"
    ./case-01-verse-agent.sh
    rc=$?
    [ $rc -eq 0 ] && geslaagd=$((geslaagd + 1))
    [ $rc -eq 2 ] && geblokkeerd=$((geblokkeerd + 1))
  done
  echo "case-01: $geslaagd/$CASE01_RUNS geslaagd, $geblokkeerd geblokkeerd (drempel: $CASE01_RUNS/$CASE01_RUNS)"
  [ "$geblokkeerd" -gt 0 ] && BLOKKED=$((BLOKKED + 1))
  [ "$geslaagd" -lt "$CASE01_RUNS" ] && FALEN=$((FALEN + 1))
  echo
fi

if wil 05; then
  echo "case-05: tracked changes op een conceptbericht"
  node ./case-05-tracked-changes.mjs
  [ $? -ne 0 ] && FALEN=$((FALEN + 1))
  echo
fi

echo "NIET GEAUTOMATISEERD — de echte Claude Desktop sideviewer. Case-02 draait in"
echo "systeem-Chrome; Electron heeft eigen CSP en flags. Handmatig gemeten 18-08-2026"
echo "(criteria.md, AC-4): als BESTAND openen werkt daar niet en herstelt niet; via"
echo "http://127.0.0.1:8791/p/<pad> werkt alles, inclusief zelfherstel."
echo "Opnieuw meten: tests/sideview-test.sh"
echo

if [ "$FALEN" -eq 0 ] && [ "$BLOKKED" -eq 0 ]; then
  echo "GROEN — alle gedraaide cases geslaagd"
else
  echo "ROOD — $FALEN gefaald, $BLOKKED geblokkeerd"
fi

# De bridge terugzetten zoals we hem aantroffen: de tests zetten hem herhaaldelijk om.
[ -n "$BRIDGE_BIJ_START" ] && bridge_up >/dev/null 2>&1

[ "$FALEN" -eq 0 ] && [ "$BLOKKED" -eq 0 ]
