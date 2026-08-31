/* AC-15: een suggestie op een element dat pas later zichtbaar wordt, krijgt
   meteen zijn pill — zonder dat de reviewer eerst iets anders moet doen.

   De echte situatie: een KPI-tabel met inklapbare procesgroepen. De rijen met
   data-la-suggest staan bij het laden op display:none (class collapsed-hide) en
   de tabel zit in een eigen overflow:auto-scroller onder een body met
   overflow:hidden. De pagina groeit dus niet als je uitklapt, de ResizeObserver
   op body vuurt niet, en er werd nooit hertekend: de pills bleven weg tot een
   andere interactie toevallig een render uitlokte.

   Draait in systeem-Chrome via de bridge (/p/), net als case-12 en case-14. */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const slug = `zz-test-zichtbaar-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);
const stateDir = join(homedir(), 'Desktop', 'annotaties', slug);

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; font: 13px sans-serif }
  .stage { height: 100%; overflow: auto }
  tr.dicht { display: none }
  #los { display: none }
</style>
<div class="stage">
  <table>
    <tbody>
      <tr><td><button id="klap">+</button> groep 1</td></tr>
      <tr class="dicht"><td id="rij" data-la-suggest="s-rij"
          data-la-suggest-desc="rij in een ingeklapte groep">Scoping: subprocessen</td></tr>
    </tbody>
  </table>
  <p id="los" data-la-suggest="s-los" data-la-suggest-desc="los verborgen blok">los blok</p>
  <p id="later-anker">hier komt straks nieuwe DOM</p>
</div>
<script>
  document.getElementById('klap').addEventListener('click', function () {
    document.querySelectorAll('tr.dicht').forEach(function (r) { r.classList.remove('dicht'); });
  });
</script>
${readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-15: ${tekst}`); if (!ok) falen++; };

let browser;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 900, height: 500 } });
  try {
    await page.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`, {
      waitUntil: 'load', timeout: 8000,
    });
  } catch {
    console.log('  BLOKKED  case-15: bridge niet bereikbaar op poort ' + PORT);
    process.exit(2);
  }
  await page.waitForFunction(() => window.LucAnnotator && window.LucAnnotator.add);
  await sleep(600);

  const pills = () => page.evaluate(() =>
    document.querySelectorAll('.la-badge.la-sug').length);

  zeg(await pills() === 0, 'verborgen suggesties krijgen bij het laden nog geen pill');

  // 1. class weghalen op de rij (de +-knop van de tabel)
  await page.click('#klap');
  await sleep(400);
  zeg(await pills() === 1, 'uitklappen laat de pill vanzelf verschijnen (class weg)');

  // 2. inline style op een los element
  await page.evaluate(() => { document.getElementById('los').style.display = 'block'; });
  await sleep(400);
  zeg(await pills() === 2, 'een style-wijziging laat de tweede pill verschijnen');

  // 3. nieuwe DOM met een suggestie erin
  await page.evaluate(() => {
    const p = document.createElement('p');
    p.setAttribute('data-la-suggest', 's-nieuw');
    p.setAttribute('data-la-suggest-desc', 'later ingevoegd');
    p.textContent = 'later ingevoegde alinea';
    document.getElementById('later-anker').after(p);
  });
  await sleep(400);
  zeg(await pills() === 3, 'een later ingevoegd element krijgt ook zijn pill');

  // 4. het hertekenen komt tot rust: geen eindeloze render-lus op eigen mutaties
  const t0 = await page.evaluate(() => {
    window.__laTel = 0;
    const obs = new MutationObserver((recs) => { window.__laTel += recs.length; });
    obs.observe(document.body, { childList: true, subtree: true });
    return window.__laTel;
  });
  await sleep(1200);
  const t1 = await page.evaluate(() => window.__laTel);
  zeg(t1 - t0 === 0, `de laag tekent niet oneindig door (${t1 - t0} mutaties in 1,2s rust)`);

  /* 5. Een pagina die zichzelf sneller aanraakt dan de debounce mag het
     hertekenen niet eindeloos vooruitschuiven. Zonder plafond op de debounce
     reset elke mutatie de timer en verschijnt de pill nooit — hetzelfde
     symptoom als de bug zelf, alleen met een andere oorzaak. Een animatie die
     per frame een style zet (rAF) is precies zo'n pagina. */
  await page.evaluate(() => {
    const p = document.createElement('p');
    p.id = 'druk';
    p.setAttribute('data-la-suggest', 's-druk');
    p.setAttribute('data-la-suggest-desc', 'ingevoegd tijdens een drukke pagina');
    p.textContent = 'alinea tijdens onrust';
    p.style.display = 'none';
    document.getElementById('later-anker').after(p);
    window.__laOnrust = false;
    (function frame() {
      if (window.__laOnrust) return;
      document.getElementById('later-anker').style.paddingLeft =
        (Date.now() % 2) ? '1px' : '0px';
      requestAnimationFrame(frame);
    })();
  });
  await sleep(300);
  await page.evaluate(() => { document.getElementById('druk').style.display = 'block'; });
  await sleep(1200);
  const drukPills = await pills();
  await page.evaluate(() => { window.__laOnrust = true; });
  zeg(drukPills === 4,
    `ook op een pagina die per frame muteert komt de pill (${drukPills} van 4)`);

  await browser.close();
} finally {
  try { rmSync(bestand); } catch {}
  try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
}
process.exit(falen ? 1 : 0);
