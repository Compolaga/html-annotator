---
name: feedback-per-punt-subagent
description: "Grote feedbackrondes verwerken = per feedbackpunt één eigen subagent, niet alles zelf als main agent — anders vallen besluiten stilletjes weg"
metadata:
  node_type: memory
  type: feedback
---

Bij het verwerken van grote feedbackladingen op een plan, document of
geannoteerde HTML-pagina: spawn per feedbackpunt één subagent die dat ene punt
verwerkt, met als context het volledige document én de volledige feedbacklijst
(zodat hij weet wat de andere punten doen en daar wegblijft). Sequentieel draaien
als ze hetzelfde bestand bewerken.

**Why:** op 31-07-2026 bleek uit een audit van een reeks feedbacksessies dat bij
grote rondes meerdere genomen besluiten stilletjes wegvielen of verwaterden toen
de main agent alles zelf verwerkte. Deze werkwijze is expliciet gevraagd "zodat er
voortaan geen dingen meer wegvallen".

**How to apply:** per punt: subagent leest het hele document, verwerkt alleen zíjn
punt surgical, rapporteert compact met citaat van de wijziging. Main agent doet
daarna een integriteitscheck (grep op de ankers) en markeert de verwerkte
annotaties resolved bij de bridge. Zie ook [[bevindingen-in-werkdocument]] en
deel 4 van SKILL.md.
