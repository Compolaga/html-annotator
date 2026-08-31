/* B23: region- and text-boxes stay on the HTML they mark when the
   page scrolls — including inside an overflow:auto scroller, the case
   the screenshots showed (boxes glued to the viewport). */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';

const slug = `zz-test-scroll-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<style>
  body { margin: 0; font: 16px/1.4 sans-serif }
  #rol { height: 220px; overflow: auto; border: 1px solid #ccc; margin: 16px }
  #rol .pad { height: 160px }
  #doel-regio { background: #eef; padding: 12px 8px }
  #doel-tekst { background: #efe; padding: 8px }
  #venster-doel { margin-top: 900px; padding: 12px; background: #ffe }
</style>
<div id="rol">
  <div class="pad">boven</div>
  <div id="doel-regio">regio-anker in de scroller</div>
  <p id="doel-tekst">unieke-scrolltekst in de scroller</p>
  <div class="pad">onder</div>
</div>
<div id="venster-doel">venster-anker onder de vouw</div>
${readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')}`);

function opruimen() {
  rmSync(bestand, { force: true });
  rmSync(join(homedir(), 'Desktop', 'annotaties', slug), { recursive: true, force: true });
}

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-12: ${tekst}`); if (!ok) falen++; };

let browser;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 900, height: 500 } });
  try {
    await page.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`, {
      waitUntil: 'load',
      timeout: 8000,
    });
  } catch {
    console.log('  BLOKKED  case-12: bridge niet bereikbaar op poort ' + PORT);
    process.exit(2);
  }

  await page.waitForFunction(() => window.LucAnnotator && window.LucAnnotator.add);

  const gezet = await page.evaluate(async () => {
    function box(id) {
      const el = document.getElementById(id);
      const b = el.getBoundingClientRect();
      return {
        x: Math.round(b.left + scrollX), y: Math.round(b.top + scrollY),
        w: Math.round(b.width), h: Math.round(b.height),
      };
    }
    await window.LucAnnotator.add({
      type: 'region', rect: box('doel-regio'), target: 'regio-anker in de scroller',
    });
    const range = document.createRange();
    range.selectNodeContents(document.getElementById('doel-tekst'));
    const locator = window.LucAnnotator._test.locatorVanRange(range);
    const rects = window.LucAnnotator._test.laRectsVanRange(range);
    await window.LucAnnotator.add({
      type: 'text', selectedText: range.toString().trim(), locator, rect: rects,
    });
    await window.LucAnnotator.add({
      type: 'region', rect: box('venster-doel'), target: 'venster-anker onder de vouw',
    });
    return {
      regio: document.querySelectorAll('.la-rect:not(.la-tekst)').length,
      tekst: document.querySelectorAll('.la-rect.la-tekst').length,
    };
  });
  zeg(gezet.regio >= 2 && gezet.tekst >= 1,
    `boxes getekend (regio ${gezet.regio}, tekst ${gezet.tekst})`);

  const voor = await page.evaluate(() => {
    const r = document.getElementById('doel-regio').getBoundingClientRect();
    const t = document.getElementById('doel-tekst').getBoundingClientRect();
    const rr = document.querySelector('.la-rect:not(.la-tekst)').getBoundingClientRect();
    const tr = document.querySelector('.la-rect.la-tekst').getBoundingClientRect();
    return { rTop: r.top, tTop: t.top, rrTop: rr.top, trTop: tr.top };
  });
  zeg(Math.abs(voor.rrTop - voor.rTop) < 4, `regio-box op het anker vóór scroll (${voor.rrTop} vs ${voor.rTop})`);
  zeg(Math.abs(voor.trTop - voor.tTop) < 14, `tekst-box op het anker vóór scroll (${voor.trTop} vs ${voor.tTop})`);

  await page.evaluate(() => { document.getElementById('rol').scrollTop = 160; });
  await page.waitForTimeout(120);

  const naBinnen = await page.evaluate(() => {
    const r = document.getElementById('doel-regio').getBoundingClientRect();
    const t = document.getElementById('doel-tekst').getBoundingClientRect();
    const rr = document.querySelector('.la-rect:not(.la-tekst)').getBoundingClientRect();
    const tr = document.querySelector('.la-rect.la-tekst').getBoundingClientRect();
    return { rTop: r.top, tTop: t.top, rrTop: rr.top, trTop: tr.top };
  });
  zeg(naBinnen.rTop < voor.rTop - 80, `scroller bewoog het anker (${naBinnen.rTop} < ${voor.rTop})`);
  zeg(Math.abs(naBinnen.rrTop - naBinnen.rTop) < 4,
    `regio-box volgt de scroller (${naBinnen.rrTop} vs ${naBinnen.rTop})`);
  zeg(Math.abs(naBinnen.trTop - naBinnen.tTop) < 14,
    `tekst-box volgt de scroller (${naBinnen.trTop} vs ${naBinnen.tTop})`);

  await page.evaluate(() => { window.scrollTo(0, 400); });
  await page.waitForTimeout(120);

  const naVenster = await page.evaluate(() => {
    const v = document.getElementById('venster-doel').getBoundingClientRect();
    const rects = Array.from(document.querySelectorAll('.la-rect:not(.la-tekst)'));
    const match = rects.map((el) => el.getBoundingClientRect())
      .sort((a, b) => Math.abs(a.top - v.top) - Math.abs(b.top - v.top))[0];
    return { vTop: v.top, boxTop: match ? match.top : null };
  });
  zeg(naVenster.boxTop != null && Math.abs(naVenster.boxTop - naVenster.vTop) < 4,
    `regio-box volgt window-scroll (${naVenster.boxTop} vs ${naVenster.vTop})`);

  /* Mutant: zonder scroll-listener blijven de kaders plakken. Blijft deze
     run groen, dan meet de case vorm en niet het meescrollen. */
  const stuk = readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')
    .replace('document.addEventListener("scroll", hertekenSnel, true);', '')
    .replace('addEventListener("scroll", hertekenSnel);', '');
  if (stuk === readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')) {
    zeg(false, 'mutant-anker (scroll-listener) ontbreekt in het snippet');
  } else {
    const slugM = `${slug}-mut`;
    const bestandM = join(homedir(), 'Desktop', `${slugM}.html`);
    writeFileSync(bestandM, `<!doctype html><meta charset="utf-8"><title>${slugM}</title>
<style>
  body { margin: 0; font: 16px/1.4 sans-serif }
  #rol { height: 220px; overflow: auto; border: 1px solid #ccc; margin: 16px }
  #rol .pad { height: 160px }
  #doel-regio { background: #eef; padding: 12px 8px }
</style>
<div id="rol">
  <div class="pad">boven</div>
  <div id="doel-regio">regio-anker in de scroller</div>
  <div class="pad">onder</div>
</div>
${stuk}`);
    const pageM = await browser.newPage({ viewport: { width: 900, height: 500 } });
    try {
      await pageM.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slugM}.html`, {
        waitUntil: 'load', timeout: 8000,
      });
      await pageM.waitForFunction(() => window.LucAnnotator && window.LucAnnotator.add);
      await pageM.evaluate(async () => {
        const el = document.getElementById('doel-regio');
        const b = el.getBoundingClientRect();
        await window.LucAnnotator.add({
          type: 'region',
          rect: { x: Math.round(b.left + scrollX), y: Math.round(b.top + scrollY),
                  w: Math.round(b.width), h: Math.round(b.height) },
          target: 'regio-anker in de scroller',
        });
      });
      /* Eerst laten uitrazen: het plaatsen van de annotatie muteert zelf de DOM
         en de laag hertekent daarop (debounce 60ms). Scroll je daar bovenop, dan
         valt die hertekening ná de scroll en volgen de kaders alsnog — dan meet
         de mutant de debounce en niet het ontbreken van de scroll-listener. */
      await pageM.waitForTimeout(400);
      await pageM.evaluate(() => { document.getElementById('rol').scrollTop = 160; });
      await pageM.waitForTimeout(120);
      const mut = await pageM.evaluate(() => {
        const r = document.getElementById('doel-regio').getBoundingClientRect();
        const box = document.querySelector('.la-rect').getBoundingClientRect();
        return { rTop: r.top, boxTop: box.top };
      });
      zeg(Math.abs(mut.boxTop - mut.rTop) > 40,
        `zonder scroll-listener blijft de regio-box plakken (${mut.boxTop} vs ${mut.rTop})`);
    } finally {
      await pageM.close();
      rmSync(bestandM, { force: true });
      rmSync(join(homedir(), 'Desktop', 'annotaties', slugM), { recursive: true, force: true });
    }
  }
} finally {
  if (browser) await browser.close();
  opruimen();
}

process.exit(falen ? 1 : 0);
