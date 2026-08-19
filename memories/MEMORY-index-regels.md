# Regels voor MEMORY.md

Voeg deze regels toe aan de bestaande `MEMORY.md` in de memory-map van het project.
Niet het hele bestand overschrijven — alleen deze regels aanvullen, en alleen de
regels die er nog niet staan.

```
- [html-annotator standaard](html-annotator-standaard.md) — elke HTML-oplevering krijgt het snipping-feedbackcomponent; verwerking via de bridge-rondes en screenshot-crops
- [annotator-bridge autostart](annotator-bridge-autostart.md) — waarom de bridge "uit" leek bij een verse agent; poller + SessionStart-hook, en data:-origin kan loopback nooit bereiken
- [done-prefix op trigger](done-prefix-op-trigger.md) — kaal "zet op done" = sessie hernoemen; MET naam/item erbij = todolijst-item afvinken, sessie met rust laten
- [Reviews via Plannotator](reviews-via-plannotator.md) — md/docx-reviewrondes lopen via Plannotator; HTML-deliverables via het annotator-component
- [Bevindingen in het werkdocument](bevindingen-in-werkdocument.md) — advies/bevindingen als genummerde beslispunten in het document, niet in de chat; bestand bevriezen tijdens een annotatieronde
- [Feedback per punt via subagent](feedback-per-punt-subagent.md) — grote feedbackrondes: één subagent per feedbackpunt (volledige context mee), sequentieel; voorkomt weggevallen besluiten
- [grill-me via AskUserQuestion](grill-me-askuserquestion.md) — keuzevragen klikbaar stellen via AskUserQuestion i.p.v. platte tekst
```
