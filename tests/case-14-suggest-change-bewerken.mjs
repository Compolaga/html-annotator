/* AC-14: een change-suggestie is te BEWERKEN, niet alleen te overschrijven.

   De reviewer kiest ✎ op een LA-SUGGEST-pill, typt wat er anders moet en saved.
   Wil hij daarna zijn eigen zin bijschaven, dan moet die zin weer in de popup
   staan — ook nadat hij de beslissing heeft teruggeklikt naar pending, en ook
   na een reload (dan komt de tekst uit /state, niet uit een variabele).

   Wat hier stuk kon (en stuk was): de klik op het oranje ✎-badge sloeg
   {decision:"pending", comment:""} op en gooide de getypte tekst daarmee weg,
   zowel in sugState als in state.json. De volgende popup was leeg.

   Draait in systeem-Chrome via de bridge (/p/), net als case-05 en case-13. */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL = process.env.LUC_ANNOTATOR_SKILL_DIR
  || join(fileURLToPath(new URL('..', import.meta.url)));
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const slug = `zz-test-suggest-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);
const stateDir = join(homedir(), 'Desktop', 'annotaties', slug);
const statePad = join(stateDir, 'state.json');
const TEKST = 'liever "vanaf 1 september" hier';

writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<h2>Maandupdate</h2>
<p id="doel" data-la-suggest="s-1"
   data-la-suggest-desc="datum aangescherpt"
   data-la-suggest-old="Per direct starten we met de uitrol."
   data-la-suggest-kind="edit">Vanaf september starten we met de uitrol.</p>
${readFileSync(join(SKILL, 'references', 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-14: ${tekst}`); if (!ok) falen++; };

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
const url = `http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`;
await page.goto(url, { waitUntil: 'load' });
await page.waitForSelector('.la-badge.la-sug', { timeout: 5000 });

const edTekst = () => page.evaluate(() => {
  const ed = document.querySelector('#la-popup .la-comment-ed');
  return ed ? ed.textContent : null;
});
const typEnSave = async (t) => {
  await page.click('.la-sug-i-chg');
  await page.waitForSelector('#la-popup .la-comment-ed', { timeout: 3000 });
  await page.click('#la-popup .la-comment-ed');
  await page.keyboard.type(t);
  await page.click('#la-popup .la-save');
  await sleep(600);
};

// 1. ✎ op een verse suggestie opent leeg en de save wordt een oranje badge
await page.click('.la-sug-i-chg');
await page.waitForSelector('#la-popup .la-comment-ed', { timeout: 3000 });
zeg((await edTekst()) === '', 'een verse suggestie opent met een leeg commentveld');
await page.click('#la-popup .la-cancel');
await sleep(200);
await typEnSave(TEKST);
zeg(await page.$('.la-badge.la-sug.la-sug-chg') !== null,
  'na de save staat er een oranje ✎-badge');

// 2. de beslissing staat met comment in state.json (server-side, niet alleen in de pagina)
let state = existsSync(statePad) ? JSON.parse(readFileSync(statePad, 'utf8')) : {};
let entry = state?.components?.suggest?.['s-1'] || {};
zeg(entry.decision === 'change' && entry.comment === TEKST,
  `state.json houdt decision+comment vast (${entry.decision}, "${entry.comment}")`);

// 3. badge terugklikken -> pending, maar de getypte tekst blijft en staat weer in de popup
await page.click('.la-badge.la-sug.la-sug-chg');
await sleep(500);
zeg(await page.$('.la-badge.la-sug.la-sug-open') !== null,
  'terugklikken zet de suggestie weer op pending (de pill met drie acties)');
await page.click('.la-sug-i-chg');
await page.waitForSelector('#la-popup .la-comment-ed', { timeout: 3000 });
zeg((await edTekst()) === TEKST,
  `na terugklikken staat de eerder getypte tekst weer in de popup ("${await edTekst()}")`);
await page.click('#la-popup .la-cancel');
await sleep(200);

state = JSON.parse(readFileSync(statePad, 'utf8'));
entry = state?.components?.suggest?.['s-1'] || {};
zeg(entry.decision === 'pending' && entry.comment === TEKST,
  `pending wist de comment niet in state.json ("${entry.comment}")`);

// 4. hetzelfde na een reload: de voorvulling komt uit de geladen state
await typEnSave(' — en noem het kwartaal');
await page.reload({ waitUntil: 'load' });
await page.waitForSelector('.la-badge.la-sug', { timeout: 5000 });
await sleep(800);
zeg(await page.$('.la-badge.la-sug.la-sug-chg') !== null,
  'de change-beslissing overleeft een reload');
await page.click('.la-badge.la-sug.la-sug-chg');
await sleep(500);
await page.click('.la-sug-i-chg');
await page.waitForSelector('#la-popup .la-comment-ed', { timeout: 3000 });
zeg((await edTekst()) === TEKST + ' — en noem het kwartaal',
  `na een reload is de popup voorgevuld uit /state ("${await edTekst()}")`);

// bijwerken vervangt de beslissing, hij stapelt niet
await page.keyboard.type('!');
await page.click('#la-popup .la-save');
await sleep(600);
state = JSON.parse(readFileSync(statePad, 'utf8'));
entry = state?.components?.suggest?.['s-1'] || {};
zeg(entry.decision === 'change' && entry.comment === TEKST + ' — en noem het kwartaal!',
  `de save vervangt de bestaande beslissing ("${entry.comment}")`);

// 5. accepteren/afwijzen laat géén dode change-tekst achter voor de verwerkende agent
await page.click('.la-badge.la-sug.la-sug-chg');
await sleep(400);
await page.click('.la-sug-i-acc');
await sleep(600);
state = JSON.parse(readFileSync(statePad, 'utf8'));
entry = state?.components?.suggest?.['s-1'] || {};
zeg(entry.decision === 'accepted' && !entry.comment,
  `een accepted key draagt geen oude change-tekst mee ("${entry.comment || ''}")`);

await browser.close();
try { rmSync(bestand); } catch {}
try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
process.exit(falen ? 1 : 0);
