---
name: html-annotator-standaard
description: Elke HTML-oplevering krijgt standaard het annotatie-component uit de html-annotator skill; feedback landt als annotations.json per ronde en selecties worden bij verwerking als screenshot-crops uitgesneden
metadata:
  node_type: memory
  type: feedback
---

De gebruiker wil in ELKE HTML die voor hem gemaakt wordt (prototypes, slides,
dashboards, vergelijkingspagina's) standaard het annotatie-component uit de skill
`~/.claude/skills/html-annotator/` ingebouwd hebben, zonder erom te vragen.

**Why:** hij geeft feedback het liefst visueel: rechthoek slepen (snipping-stijl),
comment plus eventueel een afbeelding erbij, en daarna alleen een genummerd badge
zichtbaar (zoals Codex/ChatGPT-annotaties). Losse feedbackflows per pagina kostten
steeds maatwerk (2026-08-07).

**How to apply:** snippet uit `annotator-snippet.html` onderaan de HTML plakken
(check op de marker `LUC-ANNOTATOR`). Opslaan gaat via de bridge naar
`~/Desktop/annotaties/<slug>/ronde-NN/`, met de crops er al uitgesneden. Volg SKILL.md;
zie [[annotator-bridge-autostart]] voor de bridge zelf. Dit component is voor
HTML-deliverables; zie [[reviews-via-plannotator]] voor de md/docx-reviewflow.
