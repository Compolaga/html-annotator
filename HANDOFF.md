# Agentpoort

Begin hier als je deze repo installeert of uitrolt. Wijzig geen hooks en geen
poort zonder Luc.

1. Lees `INSTALL.md` en draai `./install.sh` (of `--copy`).
2. Start de bridge: `~/.claude/skills/html-annotator/ensure-bridge.sh`.
3. Check: `curl -s http://127.0.0.1:8791/ping`.
4. Open pagina's alleen via `http://127.0.0.1:8791/p/<pad-vanaf-home>`.
5. Agent-gedrag: `SKILL.md` (poort) + verplicht `references/agent-handbook.md`.
6. Wat groen betekent: `VERIFICATION.md` + `tests/run.sh`.
7. Waarom iets zo is: `decisions.md`.

Teardown: hooks staan in `~/.claude/settings.local.json` (back-up naast het
bestand). Skill-symlink: `~/.claude/skills/html-annotator`.
