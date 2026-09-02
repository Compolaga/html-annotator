#!/bin/bash
# Geeft het pad van de actuele HTML-todolijst. Gebruik dit in plaats van een pad te
# onthouden of te hardcoden: de lijst verhuist en wordt hernoemd.
#
#   bin/vind-todolijst.sh          # alleen het pad
#   bin/vind-todolijst.sh -v       # met uitleg van de keuze
#
# Hoe hij kiest: een HTML op het bureaublad (of één map diep) die genummerde punten heeft
# én zich als todolijst laat herkennen — een prioriteitsband (`class="band"`) of een titel
# met "to-do". Die twee samen zijn nodig: genummerde punten alleen komen ook voor in
# analysepagina's met genummerde bevindingen. Bij meerdere kandidaten wint de meest recent
# gewijzigde.
#
# Genummerde punten herkent hij aan `class="uid"` (het format sinds de Notion-restyle, waar
# elk punt een <details> is) of aan `<span class="num">` (het oude format). Allebei, zodat
# een lijst die nog niet omgezet is ook gevonden wordt.
#
# Exit 1 als er geen kandidaat is. Dan niet zelf een lijst verzinnen: vraag het.

set -uo pipefail
UITLEG=0
[ "${1:-}" = "-v" ] && UITLEG=1

ZOEK="$HOME/Desktop"
KANDIDATEN=()

while IFS= read -r f; do
  grep -qE 'class="uid"|<span class="num">' "$f" 2>/dev/null || continue
  if grep -q 'class="band"' "$f" 2>/dev/null || \
     grep -qiE '<title>[^<]*to-?do' "$f" 2>/dev/null; then
    KANDIDATEN+=("$f")
  fi
done < <(find "$ZOEK" -maxdepth 2 -name '*.html' -type f 2>/dev/null)

if [ ${#KANDIDATEN[@]} -eq 0 ]; then
  echo "geen todolijst gevonden onder $ZOEK" >&2
  exit 1
fi

# Meest recent gewijzigde wint.
BESTE=$(for f in "${KANDIDATEN[@]}"; do
  printf '%s\t%s\n' "$(stat -f '%m' "$f")" "$f"
done | sort -rn | head -1 | cut -f2-)

if [ "$UITLEG" -eq 1 ]; then
  echo "gekozen: $BESTE"
  echo "gewijzigd: $(stat -f '%Sm' -t '%d-%m-%Y %H:%M' "$BESTE")"
  echo "punten: $(grep -cE 'class="uid"|<span class="num">' "$BESTE")"
  echo "hoogste nummer: $(grep -oE 'class="uid">#[0-9]+|<span class="num">[0-9]+' "$BESTE" | grep -oE '[0-9]+$' | sort -n | tail -1)"
  if [ ${#KANDIDATEN[@]} -gt 1 ]; then
    echo "andere kandidaten:"
    for f in "${KANDIDATEN[@]}"; do
      [ "$f" = "$BESTE" ] || echo "  $f ($(stat -f '%Sm' -t '%d-%m %H:%M' "$f"))"
    done
  fi
else
  echo "$BESTE"
fi
