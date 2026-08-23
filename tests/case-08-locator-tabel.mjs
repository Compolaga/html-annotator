/* AC: een tekstannotatie in een tabel blijft op de goede rij staan als er
   erboven een rij bij komt, en verdwijnt pas naar "likely processed" als de
   geselecteerde tekst nergens meer op de pagina staat.

   Waarom dit een eigen case is: de eerste locator-versie behandelde "start-span
   bestaat nog" als "verwerkt". In een proces-tabel is die span vaak "Backlog"
   of "2.4.1" — die blijven staan terwijl de rij-index verschuift.

   De selectie móet over twee rijen lopen (anders is de gemeenschappelijke
   voorouder de cel zelf en vangt het label-assert de tbody-bug niet) en de
   start móet op een herhaalde span ("Backlog") staan (anders komt zoekAnker
   nooit bij de fallback die de wees-te-vroeg-bug was). */
import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
if (!process.env.LUC_ANNOTATOR_PORT) {
  console.log('  BLOKKED  case-08: LUC_ANNOTATOR_PORT verplicht (anders is de origin-assert tandeloos op 8791)');
  process.exit(2);
}
const PORT = process.env.LUC_ANNOTATOR_PORT;

const slug = `zz-test-locator-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);

function opruimen() {
  rmSync(bestand, { force: true });
  rmSync(join(homedir(), 'Desktop', 'annotaties', slug), { recursive: true, force: true });
}

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<div class="wrap">
<table>
<tbody>
<tr data-row="r1"><td class="proc-num"><span>2.1</span><span>Alpha</span></td><td class="rol">Mark</td><td><span class="tag">Backlog</span></td><td class="ei">E mid / I hoog <span class="tag">checken</span></td></tr>
<tr data-row="r2"><td class="proc-num"><span>2.2</span><span>Beta</span></td><td class="rol">Menno</td><td><span class="tag">Backlog</span></td><td class="ei">E mid / I hoog <span class="tag">checken</span></td></tr>
<tr data-row="r3"><td class="proc-num"><span>2.3</span><span>Gamma-uniek</span></td><td class="rol">Gwen</td><td><span class="tag">Backlog</span></td><td class="ei">E laag / I mid <span class="tag">checken</span></td></tr>
</tbody>
</table>
</div>
${readFileSync(join(SKILL, 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
let code = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-08: ${tekst}`); if (!ok) falen++; };

let browser;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  try {
    await page.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`, {
      waitUntil: 'load',
      timeout: 8000,
    });
  } catch {
    console.log('  BLOKKED  case-08: bridge niet bereikbaar op poort ' + PORT);
    code = 2;
  }
  if (code !== 2) {
  await page.waitForFunction(() => (
    window.LucAnnotator
    && window.LucAnnotator._test
    && typeof window.LucAnnotator._test.zoekAnker === 'function'
    && typeof window.LucAnnotator._test.laTekstNogDaar === 'function'
  ));

  const labelHit = await page.evaluate(() => {
    const range = document.createRange();
    range.setStartBefore(document.querySelector('[data-row="r2"] td.ei').firstChild);
    range.setEndAfter(document.querySelector('[data-row="r3"] td.ei').lastChild);
    const locator = window.LucAnnotator._test.locatorVanRange(range);
    return locator && locator.label;
  });

  zeg(!!(labelHit && /Beta/.test(labelHit) && /Menno/.test(labelHit)),
    `label komt van de start-rij (${(labelHit || '').slice(0, 60)})`);
  zeg(!/Alpha/.test(labelHit || '') && !/\bMark\b/.test(labelHit || ''),
    `label bevat niet rij 1 (${(labelHit || '').slice(0, 60)})`);

  const herhaald = await page.evaluate(() => {
    const rij = document.querySelector('[data-row="r2"]');
    const start = rij.querySelector('span.tag');
    const ei = rij.querySelector('td.ei');
    const range = document.createRange();
    range.setStartBefore(start.firstChild);
    range.setEndAfter(ei.lastChild);
    const locator = window.LucAnnotator._test.locatorVanRange(range);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    const selectedText = sel.toString().replace(/\s+/g, ' ').trim();
    return { selectedText, locator };
  });

  const naHerhaald = await page.evaluate((ann) => {
    const tbody = document.querySelector('tbody');
    const extra = document.createElement('tr');
    extra.setAttribute('data-row', 'extra');
    extra.innerHTML = '<td class="proc-num"><span>1.9</span><span>Nieuw</span></td><td class="rol">x</td><td><span class="tag">Backlog</span></td><td class="ei">E mid / I hoog <span class="tag">checken</span></td>';
    tbody.insertBefore(extra, tbody.firstChild);
    const hit = window.LucAnnotator._test.zoekAnker(ann);
    let opRij2 = false;
    let opRij1 = false;
    if (hit && hit.rects && hit.rects.length) {
      const mid = hit.rects[0].y - window.scrollY + (hit.rects[0].h || 0) / 2;
      const r2 = document.querySelector('[data-row="r2"]').getBoundingClientRect();
      const r1 = document.querySelector('[data-row="r1"]').getBoundingClientRect();
      opRij2 = mid >= r2.top && mid <= r2.bottom;
      opRij1 = mid >= r1.top && mid <= r1.bottom;
    }
    const extraEl = document.querySelector('[data-row="extra"]');
    if (extraEl) extraEl.remove();
    return { wees: !hit, opRij2, opRij1 };
  }, herhaald);

  zeg(!naHerhaald.wees && naHerhaald.opRij2 && !naHerhaald.opRij1,
    `herhaalde E/I-tekst blijft op Beta via het label (wees=${naHerhaald.wees}, opRij2=${naHerhaald.opRij2}, opRij1=${naHerhaald.opRij1})`);

  const basis = await page.evaluate(() => {
    const rij = document.querySelector('[data-row="r3"]');
    const start = rij.querySelector('span.tag');
    const ei = rij.querySelector('td.ei');
    const range = document.createRange();
    range.setStartBefore(start.firstChild);
    range.setEndAfter(ei.lastChild);
    const locator = window.LucAnnotator._test.locatorVanRange(range);
    /* Selection.toString() zet spaties tussen cellen; Range.toString() niet.
       De runtime slaat sel.toString() op — dezelfde vorm hier, anders vindt
       zoekTekst "BacklogE laag" niet terug als "Backlog E laag". */
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    const selectedText = sel.toString().replace(/\s+/g, ' ').trim();
    const hit = window.LucAnnotator._test.zoekAnker({ type: 'text', selectedText, locator });
    return {
      selectedText,
      locator,
      gevonden: !!(hit && hit.rects && hit.rects.length),
    };
  });

  zeg(basis.gevonden, `eerste match start op Backlog van rij 3 ("${basis.selectedText}")`);

  const naInsert = await page.evaluate((ann) => {
    const tbody = document.querySelector('tbody');
    const extra = document.createElement('tr');
    extra.innerHTML = '<td class="proc-num"><span>1.9</span><span>Nieuw</span></td><td class="rol">x</td><td><span class="tag">Backlog</span></td><td class="ei">E mid / I hoog <span class="tag">checken</span></td>';
    tbody.insertBefore(extra, tbody.firstChild);
    const hit = window.LucAnnotator._test.zoekAnker(ann);
    const wees = !hit;
    let opRij3 = false;
    if (hit && hit.rects && hit.rects.length) {
      const r3 = document.querySelector('[data-row="r3"]').getBoundingClientRect();
      const y = hit.rects[0].y - window.scrollY;
      opRij3 = y >= r3.top - 4 && y <= r3.bottom + 4;
    }
    return { wees, opRij3 };
  }, { type: 'text', selectedText: basis.selectedText, locator: basis.locator });

  zeg(!naInsert.wees && naInsert.opRij3,
    `na een rij erboven blijft de annotatie op Gamma staan (wees=${naInsert.wees}, opRij3=${naInsert.opRij3})`);

  const naEdit = await page.evaluate((ann) => {
    document.querySelector('[data-row="r3"] td.ei').textContent = 'E hoog / I hoog';
    document.querySelector('[data-row="r3"] .tag').textContent = 'Klaar';
    const hit = window.LucAnnotator._test.zoekAnker(ann);
    return { wees: !hit };
  }, { type: 'text', selectedText: basis.selectedText, locator: basis.locator });

  zeg(naEdit.wees,
    'als de geselecteerde tekst nergens meer staat, is het wél een wees');

  const ws = await page.evaluate(() => {
    const rij = document.querySelector('[data-row="r2"]');
    const start = rij.querySelector('span.tag');
    const ei = rij.querySelector('td.ei');
    const range = document.createRange();
    range.setStartBefore(start.firstChild);
    range.setEndAfter(ei.lastChild);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    const metSpatie = sel.toString().replace(/\s+/g, ' ').trim();
    const zonder = range.toString();
    const t = window.LucAnnotator._test;
    const first = t.laRectsVanRange(t.laRangeVanLocator(t.locatorVanRange(range)));
    const hit = t.zoekAnker({
      type: 'text',
      selectedText: metSpatie,
      locator: t.locatorVanRange(range),
    });
    return {
      verschillend: metSpatie !== zonder,
      nogDaar: t.laTekstNogDaar(range, metSpatie),
      zelfdeTak: !!(hit && first && Math.abs(hit.y - first.y) < 4),
    };
  });
  zeg(ws.verschillend && ws.nogDaar,
    'laTekstNogDaar accepteert Selection-spaties vs Range.toString()');
  zeg(ws.zelfdeTak, 'eerste zoekAnker-tak dekt de ongewijzigde pagina');
  const origin = await page.evaluate(() => window.LucAnnotator._test.bridgeOrigin);
  zeg(origin === `http://127.0.0.1:${PORT}`,
    `bridge-origin volgt /p/ (${origin} vs poort ${PORT})`);
  }
  if (code !== 2) code = falen ? 1 : 0;
} finally {
  if (browser) await browser.close();
  opruimen();
}

process.exit(code);
