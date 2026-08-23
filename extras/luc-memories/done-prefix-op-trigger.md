---
name: done-prefix-op-trigger
description: "Trigger-woorden \"mark as done\", \"zet op done\", \"zet 'm op done\" (kaal, zonder ander object erbij) — hernoem de HUIDIGE sessie met een [DONE]--prefix. Eigen titel vind je met een shell-oneliner (env vars + jq), niet via list_sessions/get_session (die weigeren de huidige sessie altijd) en niet door te gokken. Ook relevant om net NIET te triggeren wanneer er een naam/item bij genoemd wordt (\"zet <naam> op done\", \"vink X af\") — dat gaat over een to-do-item op de lijst, niet over de sessie."
metadata:
  node_type: memory
  type: feedback
---

## Wanneer dit wel geldt

Kaal "zet op done" / "mark as done" / "zet 'm op done", zonder een naam, persoon
of to-do-item erbij, betekent: de huidige sessie/taak is klaar. Dat is de trigger
om de sessietitel te hernoemen met een `[DONE]-`-prefix.

## Wanneer dit NIET geldt

Wordt er een naam of item bij genoemd ("zet <naam> op done", "vink X af",
"zet punt 3 op done")? Dan gaat het over een regel op de HTML-todolijst
(skill `html-annotator`), niet over de sessienaam. Dat is een andere actie: het
punt in de lijst doorstrepen/afvinken, de sessie blijft ongemoeid.

## Je eigen titel vinden — het opgeloste probleem

`list_sessions` sluit de huidige sessie uit en `get_session` weigert 'm
expliciet (getest 18-08-2026, ook met het exacte session-ID i.p.v. `"self"` —
```
Refusing to return the current session; use list_sessions for other sessions
or your own session context for this one.
```
), dus via de MCP-tools zelf kom je er niet. **Maar** de titel staat gewoon
lokaal op schijf, per sessie, en is met één commando op te vragen (getest en
werkend, 19-08-2026):

```bash
jq -r .title "$(find "$CLAUDE_USER_DATA_DIR/claude-code-sessions" -name "${CLAUDE_CODE_HOST_SESSION_ID}.json")"
```

Dit gebruikt twee env vars die in elke sessie al bestaan (`CLAUDE_USER_DATA_DIR`,
`CLAUDE_CODE_HOST_SESSION_ID`) en leest hetzelfde JSON-bestand dat de app zelf
ook bijhoudt (bevat o.a. `sessionId`, `title`, `cwd`, `createdAt`). Gebruik dit
commando **altijd** als eerste stap bij de kale trigger, in plaats van te
gokken of te vragen.

## Hoe uit te voeren

1. Haal je exacte huidige titel op met het commando hierboven.
2. Nieuwe titel = **exact** `[DONE]-` (koppelteken, geen spatie) + die titel,
   **karakter voor karakter ongewijzigd** — geen hoofdletters toevoegen, geen
   `-` vervangen door spaties, geen cijfers/kebab-case "netjes" herschrijven.
3. Roep `mcp__ccd_session_mgmt__set_session_title` aan met `session_id: "self"`
   en de titel uit stap 2. (Deze MCP-tool bestaat alleen in de Claude-desktop-omgeving.)
4. Titel is al `[DONE]`-geprefixt? Niets doen, niet dubbel prefixen.
5. Lukt stap 1 onverhoopt niet (env var ontbreekt, bestand niet gevonden)?
   Dán pas vragen wat de titel is — dat is het uitzonderingspad, niet de
   standaardroute.

**Why:** vastgelegd 18-08-2026, aangescherpt 19-08-2026. Eerste versies gingen
mis doordat de agent zonder `session_id` aanriep, daarna doordat hij een titel
verzon in plaats van hem op te halen (spatie i.p.v. koppelteken, en herschreven
i.p.v. letterlijke tekst). Op 19-08 bleek `list_sessions`/`get_session` de
titel principieel nooit te kunnen teruggeven — daarna is de work-around
gevonden: het sessie-JSON op schijf, vindbaar via env vars.

**How to apply:** geldt voor élke sessie, niet alleen gespawnde task-sessies.
Belangrijk voor deze skill is vooral het NIET-geldt-geval hierboven: dat is de
disambiguatie met de HTML-todolijst uit deel 5 van SKILL.md.
