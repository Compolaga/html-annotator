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
# Staat er een pad in ~/.claude/todolijst-pad en bestaat dat bestand, dan wint dat altijd
# en wordt er niet gezocht. Die pointer bestaat omdat de heuristiek één keer verkeerd koos:
# op 29-08-2026 stond er een backup (.todos-backup-voor-notion-restyle.html) naast de echte
# lijst, en omdat een sessie daarin schreef werd hij ook nog de meest recent gewijzigde —
# waardoor de volgende sessie er weer in schreef. Werk landde zo in een bestand dat de
# reviewer nooit opent. Zet de pointer dus opnieuw als de lijst verhuist of hernoemd wordt, in plaats van
# op mtime te vertrouwen.
#
# Exit 1 als er geen kandidaat is. Dan niet zelf een lijst verzinnen: vraag het.

set -uo pipefail
UITLEG=0
[ "${1:-}" = "-v" ] && UITLEG=1

POINTER="$HOME/.claude/todolijst-pad"
if [ -s "$POINTER" ]; then
  PAD=$(head -1 "$POINTER" | sed "s#^~#$HOME#")
  if [ -f "$PAD" ]; then
    if [ "$UITLEG" -eq 1 ]; then
      echo "gekozen: $PAD"
      echo "bron: pointer $POINTER (niet gezocht)"
      echo "gewijzigd: $(stat -f '%Sm' -t '%d-%m-%Y %H:%M' "$PAD")"
      echo "punten: $(grep -cE 'class="uid"|<span class="num">' "$PAD")"
      echo "hoogste nummer: $(grep -oE 'class="uid">#[0-9]+|<span class="num">[0-9]+' "$PAD" | grep -oE '[0-9]+$' | sort -n | tail -1)"
    else
      echo "$PAD"
    fi
    exit 0
  fi
  echo "let op: $POINTER wijst naar $PAD, maar dat bestand bestaat niet — verder gezocht" >&2
fi

ZOEK="$HOME/Desktop"
KANDIDATEN=()

while IFS= read -r f; do
  # backups en verborgen kopieën tellen niet mee — daar mag niets in geschreven worden
  case "$(basename "$f")" in .*|*backup*|*bak*|*kopie*|*copy*|*oud*|*archief*) continue ;; esac
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
