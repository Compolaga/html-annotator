/* AC-16: elementen die dezelfde data-la-suggest-key delen zijn ÉÉN suggestie.

   In een KPI-HTML uit een klantproject stonden work-item-clusters waar de
   parent-rij en zijn subtaakrijen dezelfde key hadden (vijf rijen op één
   key). De laag tekende
   toen vijf pills, maar de beslissing gaat per key naar state.json — één ✓
   besliste dus stiekem over vijf rijen terwijl er vijf losse knoppen stonden.

   Wat de laag nu doet: alle rects van alle elementen met die key worden
   gehighlight als één groep, met precies één pill. Wie per rij wil beslissen,
   geeft elke rij een eigen key (dat is case-17).

   Draait in systeem-Chrome via de bridge (/p/), net als case-14. */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const slug = `zz-test-gedeelde-key-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);
const stateDir = join(homedir(), 'Desktop', 'annotaties', slug);
const statePad = join(stateDir, 'state.json');

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<table>
  <tbody>
    <tr><td id="p" data-la-suggest="wi-1042"
        data-la-suggest-desc="work item 1042">Parent: voorbeeldtaak</td></tr>
    <tr><td id="s1" data-la-suggest="wi-1042">Subtaak A</td></tr>
    <tr><td id="s2" data-la-suggest="wi-1042">Subtaak B</td></tr>
  </tbody>
</table>
${readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-16: ${tekst}`); if (!ok) falen++; };

let browser;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
  try {
    await page.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`, {
      waitUntil: 'load', timeout: 8000,
    });
    await page.waitForSelector('.la-badge.la-sug', { timeout: 5000 });
  } catch {
    console.log('  BLOKKED  case-16: bridge niet bereikbaar op poort ' + PORT);
    process.exit(2);
  }
  await sleep(500);

  const tel = (sel) => page.evaluate((s) => document.querySelectorAll(s).length, sel);

  zeg(await tel('.la-badge.la-sug') === 1,
    `drie rijen met dezelfde key geven één pill (${await tel('.la-badge.la-sug')})`);

  // de highlight dekt wel alle drie de rijen: per rij minstens één kader dat
  // horizontaal en verticaal over die rij heen ligt
  const dekking = await page.evaluate(() => {
    const rects = [...document.querySelectorAll('.la-sug-rect')].map((r) => {
      const b = r.getBoundingClientRect();
      return { l: b.left, t: b.top, r: b.right, b: b.bottom };
    });
    return ['p', 's1', 's2'].map((id) => {
      const b = document.getElementById(id).getBoundingClientRect();
      // net binnen de linkerrand: de tekst-rects zijn zo breed als de tekst,
      // niet zo breed als de cel, dus het midden van de cel zegt niets
      const cx = b.left + 4, cy = b.top + b.height / 2;
      return rects.some((r) => r.l <= cx && r.r >= cx && r.t <= cy && r.b >= cy);
    });
  });
  zeg(dekking.every(Boolean),
    `de groep is als geheel gehighlight, alle drie de rijen (${dekking.join(',')})`);

  // de pill hoort bij de rij die hij beschrijft — de eerste van de groep — en
  // niet onderaan het cluster bij een subtaak waar zijn tekst niet over gaat
  const plaats = await page.evaluate(() => {
    const p = document.getElementById('p').getBoundingClientRect();
    const b = document.querySelector('.la-badge.la-sug').getBoundingClientRect();
    return { pill: Math.round(b.top), parent: Math.round(p.top) };
  });
  zeg(Math.abs(plaats.pill - plaats.parent) < 30,
    `de pill staat bij de eerste rij van de groep (${plaats.pill} vs ${plaats.parent})`);

  // één beslissing dekt de hele groep: accepteren kleurt alle kaders groen
  await page.click('.la-sug-i-acc');
  await sleep(700);
  zeg(await tel('.la-badge.la-sug') === 1 && await tel('.la-badge.la-sug.la-sug-acc') === 1,
    'na accepteren staat er nog steeds precies één (groene) pill');
  zeg(await tel('.la-sug-rect') === await tel('.la-sug-rect.la-sug-acc'),
    'alle kaders van de groep kleuren mee met die ene beslissing');

  const state = existsSync(statePad) ? JSON.parse(readFileSync(statePad, 'utf8')) : {};
  const comp = state?.components?.suggest || {};
  zeg(Object.keys(comp).length === 1 && comp['wi-1042']?.decision === 'accepted',
    `state.json houdt één entry voor de key (${JSON.stringify(Object.keys(comp))})`);

  await browser.close();
} finally {
  try { rmSync(bestand); } catch {}
  try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
}
process.exit(falen ? 1 : 0);
