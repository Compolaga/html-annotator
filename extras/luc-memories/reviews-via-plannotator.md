---
name: reviews-via-plannotator
description: "Documentreviews (md/docx) lopen via Plannotator, niet via docx-comments — HTML-deliverables lopen via het annotator-component"
metadata:
  node_type: memory
  type: feedback
---

Sinds 25-07-2026: alle documentiteraties die eerst via .docx met tracked
changes/comments liepen, voortaan via Plannotator op het bron-md-bestand doen.

**Why:** annoteren in Plannotator werkt "chiller" dan Word-comments; de
docx-review-mode-flow (pandoc, tracked diffs, Word-verificatie) is bovendien veel
zwaarder.

**How to apply:** bij een reviewvraag op een document standaard de md-bron in
Plannotator openen (plannotator-annotate skill) i.p.v. een docx-ronde. Alleen nog
een .docx opleveren als het eindproduct zelf een Word-bestand moet zijn (extern
delen); tussenrondes gaan via Plannotator.

Deze memory hoort bij [[html-annotator-standaard]] als grensafbakening: is de
deliverable een HTML-pagina, dan is het annotator-component de route, niet
Plannotator.
