#!/usr/bin/env bash
# Installeert de html-annotator skill op deze machine:
#   1. skill op zijn plek (~/.claude/skills/html-annotator) — symlink naar deze clone
#   2. de twee hooks in ~/.claude/settings.local.json
#
# Idempotent: twee keer draaien verandert niets extra's.
#
# Gebruik:
#   ./install.sh                      # link + hooks
#   ./install.sh --copy               # kopieer de skill i.p.v. symlinken
set -euo pipefail

BRON="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="$HOME/.claude/skills"
DOEL="$SKILLS/html-annotator"
SETTINGS="$HOME/.claude/settings.local.json"
MODUS="symlink"
PROJECT="$HOME/Desktop"

for arg in "$@"; do
  case "$arg" in
    --copy) MODUS="copy" ;;
    -*) echo "onbekende optie: $arg" >&2; exit 2 ;;
    *) PROJECT="$arg" ;;
  esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
info() { printf '  \033[33m·\033[0m %s\n' "$1"; }
fout() { printf '  \033[31m✗\033[0m %s\n' "$1" >&2; }

echo "html-annotator installeren"
echo

# --- 1. skill op zijn plek ------------------------------------------------
mkdir -p "$SKILLS"
kopieer_skill() {
  mkdir -p "$DOEL"
  (cd "$BRON" && tar cf - \
      --exclude=.git --exclude=tests/node_modules \
      --exclude=bridge.log --exclude=bridge.pid --exclude=bridge-hook.log \
      --exclude=__pycache__ --exclude='*.pyc' .) | (cd "$DOEL" && tar xf -)
}

if [ -L "$DOEL" ] && [ "$(readlink "$DOEL")" = "$BRON" ]; then
  ok "skill staat al gelinkt op $DOEL"
elif [ "$MODUS" = "copy" ]; then
  kopieer_skill
  ok "skill gekopieerd naar $DOEL"
elif [ -e "$DOEL" ]; then
  info "$DOEL bestaat al en is niet deze clone — met rust gelaten"
  info "verwijder of hernoem hem eerst, of draai ./install.sh --copy"
else
  ln -s "$BRON" "$DOEL"
  ok "skill gelinkt: $DOEL -> $BRON"
fi

chmod +x "$BRON"/bin/*.sh "$BRON"/bin/*.py "$BRON"/install.sh 2>/dev/null || true

# --- 2. hooks -------------------------------------------------------------
HOOK="$DOEL/bin/hook-ensure-bridge.sh"
if [ ! -f "$HOOK" ]; then
  fout "hook $HOOK ontbreekt — niet geregistreerd"
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  fout "jq niet gevonden — hooks niet geregistreerd"
  echo "     Installeer jq (brew install jq) en draai dit script opnieuw,"
  echo "     of voeg de twee hooks met de hand toe (zie INSTALL.md, stap 3)."
else
  [ -f "$SETTINGS" ] || printf '{}\n' > "$SETTINGS"
  cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d%H%M%S)"
  jq --arg hook "$HOOK" '
    def entry($m): {
      matcher: $m,
      hooks: [{type:"command", command:$hook, timeout:15, statusMessage:"annotator-bridge check"}]
    };
    def zonder($arr): [ ($arr // [])[] | select(
      ([.hooks[]?.command // empty] | map(test("ensure-bridge")) | any) | not
    ) ];
    .hooks              //= {}
    | .hooks.PostToolUse  = (zonder(.hooks.PostToolUse)  + [entry("Edit|Write")])
    | .hooks.SessionStart = (zonder(.hooks.SessionStart) + [entry("")])
  ' "$SETTINGS" > "$SETTINGS.tmp" && mv "$SETTINGS.tmp" "$SETTINGS"
  ok "hooks geregistreerd in $SETTINGS (back-up ernaast gezet)"
fi

# --- 4. omgeving controleren ---------------------------------------------
echo
echo "Omgeving:"
command -v python3 >/dev/null && ok "python3 aanwezig" || fout "python3 ontbreekt — de bridge draait hierop"
python3 -c 'import PIL' 2>/dev/null && ok "Pillow aanwezig (snellere crops)" || info "Pillow ontbreekt — crops gaan via de Chrome-route, werkt ook"
if ls /Applications/Google\ Chrome.app >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
  ok "Chrome gevonden (nodig voor screenshot-crops)"
else
  info "Chrome niet gevonden — regio-annotaties worden dan zonder crop opgeslagen"
fi

echo
echo "Klaar. Nog met de hand doen:"
echo "  - Zet de opleverregel in ~/.claude/CLAUDE.md (zie INSTALL.md, stap 4)."
echo "  - Start de bridge: $DOEL/bin/ensure-bridge.sh"
echo "  - Test: curl -s http://127.0.0.1:8791/ping"
