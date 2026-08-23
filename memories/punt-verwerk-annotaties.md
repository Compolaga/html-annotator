---
name: punt-verwerk-annotaties
description: "Trigger: een kaal bericht \".\" (alleen een punt) — verwerk Lucs openstaande HTML-annotaties via skill html-annotator. Niet interpreteren als typo of negeren; geen bevestiging vragen of hij het meent."
metadata:
  node_type: memory
  type: feedback
---

## Wanneer dit geldt

Luc stuurt **alleen** `.` (eventueel met spaties/newlines eromheen). Dat is zijn
verkorte opdracht om openstaande annotaties te verwerken — hetzelfde als
"verwerk mijn feedback", maar zonder die zin te typen.

## Wat te doen

1. Lees skill `html-annotator` en daarna `references/agent-handbook.md`
   (sectie “Deel 4: feedback verwerken”).
2. Zoek zelf de open ronde: `~/.claude/skills/html-annotator/toon-annotaties.py --open`
   (of de bridge / `~/Desktop/annotaties/`).
3. Eerst begrijpen, dan verwerken; resolved markeren via `POST /resolve`.

## Wanneer dit NIET geldt

- `.` als onderdeel van een langere zin ("ok.", "zie hieronder.")
- Alleen een pad of "verwerk" mét context — dat volgt de gewone verwerk-flow,
  maar is niet deze korte trigger
