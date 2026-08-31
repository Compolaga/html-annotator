/* AC-17: twee elementen met VERSCHILLENDE keys zijn twee losse beslissingen.

   De keerzijde van case-16: als elke rij zijn eigen data-la-suggest heeft, dan
   hoort er per rij een pill te staan en mag de ene accepteren de andere niet
   meeslepen. Dat is precies wat de live klant-HTML's nu doen: parent
   "wi-<id>", subtaken "wi-<parentid>-<subid>".

   Draait in systeem-Chrome via de bridge (/p/), net als case-16. */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const slug = `zz-test-losse-keys-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);
const stateDir = join(homedir(), 'Desktop', 'annotaties', slug);
const statePad = join(stateDir, 'state.json');

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<table>
  <tbody>
    <tr><td id="p" data-la-suggest="wi-1042"
        data-la-suggest-desc="parent 1042">Parent: voorbeeldtaak</td></tr>
    <tr><td id="s1" data-la-suggest="wi-1042-7"
        data-la-suggest-desc="subtaak 7">Subtaak A</td></tr>
  </tbody>
</table>
${readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-17: ${tekst}`); if (!ok) falen++; };

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
    console.log('  BLOKKED  case-17: bridge niet bereikbaar op poort ' + PORT);
    process.exit(2);
  }
  await sleep(500);

  const tel = (sel) => page.evaluate((s) => document.querySelectorAll(s).length, sel);
  zeg(await tel('.la-badge.la-sug') === 2,
    `twee eigen keys geven twee pills (${await tel('.la-badge.la-sug')})`);

  // de bovenste pill hoort bij de parent-rij; accepteer die en laat de andere staan
  const eerst = await page.evaluate(() => {
    const b = [...document.querySelectorAll('.la-badge.la-sug')]
      .sort((a, z) => a.getBoundingClientRect().top - z.getBoundingClientRect().top)[0];
    b.querySelector('.la-sug-i-acc').click();
    return true;
  });
  zeg(eerst, 'de eerste pill is aanklikbaar');
  await sleep(700);

  zeg(await tel('.la-badge.la-sug.la-sug-acc') === 1,
    `precies één pill staat op accepted (${await tel('.la-badge.la-sug.la-sug-acc')})`);
  zeg(await tel('.la-badge.la-sug.la-sug-open') === 1,
    `de andere pill staat nog gewoon open/pending (${await tel('.la-badge.la-sug.la-sug-open')})`);

  const state = existsSync(statePad) ? JSON.parse(readFileSync(statePad, 'utf8')) : {};
  const comp = state?.components?.suggest || {};
  zeg(comp['wi-1042']?.decision === 'accepted' && !comp['wi-1042-7'],
    `state.json kent alleen een beslissing op de geklikte key (${JSON.stringify(Object.keys(comp))})`);

  await browser.close();
} finally {
  try { rmSync(bestand); } catch {}
  try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
}
process.exit(falen ? 1 : 0);
