#!/usr/bin/env bash
# Installs the html-annotator skill on this machine:
#   1. skill in place (~/.claude/skills/html-annotator) — symlink to this clone
#   2. the two hooks in ~/.claude/settings.local.json
#
# Idempotent: running twice changes nothing extra.
#
# Usage:
#   ./install.sh                      # link + hooks
#   ./install.sh --copy               # copy the skill instead of symlink
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
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) PROJECT="$arg" ;;
  esac
done

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
info() { printf '  \033[33m·\033[0m %s\n' "$1"; }
fout() { printf '  \033[31m✗\033[0m %s\n' "$1" >&2; }

echo "installing html-annotator"
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
  ok "skill already linked at $DOEL"
elif [ "$MODUS" = "copy" ]; then
  kopieer_skill
  ok "skill copied to $DOEL"
elif [ -e "$DOEL" ]; then
  info "$DOEL already exists and is not this clone — left alone"
  info "remove or rename it first, or run ./install.sh --copy"
else
  ln -s "$BRON" "$DOEL"
  ok "skill linked: $DOEL -> $BRON"
fi

chmod +x "$BRON"/bin/*.sh "$BRON"/bin/*.py "$BRON"/install.sh 2>/dev/null || true

# --- 2. hooks -------------------------------------------------------------
HOOK="$DOEL/bin/hook-ensure-bridge.sh"
if [ ! -f "$HOOK" ]; then
  fout "hook $HOOK missing — not registered"
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  fout "jq not found — hooks not registered"
  echo "     Install jq (brew install jq) and rerun this script,"
  echo "     or add the two hooks by hand (see INSTALL.md, step 2)."
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
  ok "hooks registered in $SETTINGS (backup written next to it)"
fi

# --- 4. environment ------------------------------------------------------
echo
echo "Environment:"
command -v python3 >/dev/null && ok "python3 present" || fout "python3 missing — the bridge needs it"
python3 -c 'import PIL' 2>/dev/null && ok "Pillow present (faster crops)" || info "Pillow missing — crops go through Chrome, still works"
if ls /Applications/Google\ Chrome.app >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
  ok "Chrome found (needed for screenshot crops)"
else
  info "Chrome not found — region annotations then store without a crop"
fi

echo
echo "Done. Still do by hand:"
echo "  - Put the deliver rule in ~/.claude/CLAUDE.md (see INSTALL.md, step 3)."
echo "  - Start the bridge: $DOEL/bin/ensure-bridge.sh"
echo "  - Test: curl -s http://127.0.0.1:8791/ping"
