/* AC-5: Luc herschrijft de tekst van een conceptbericht rechtstreeks in de kaart, en dat
   verschil komt als bewerking op schijf te staan — met voor, na en de losse wijzigingen,
   zodat een agent niet hoeft te raden wat er moet veranderen.

   Waarom dit een eigen case is en niet een variant van case-02: hier gaat het niet om of
   de bridge bereikbaar is, maar of de diff klopt en of hij een reload overleeft. Het
   bewijs komt uit een ander systeem dan de pagina: annotations.json op schijf.

   Draait in systeem-Chrome via de bridge (/p/), want dat is de route waarlangs Luc de
   pagina echt opent — gemeten in AC-4. */

import { chromium } from 'playwright-core';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const SKILL = join(homedir(), '.claude', 'skills', 'html-annotator');
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';
const sh = (c, a) => { try { return execFileSync(c, a, { encoding: 'utf8' }).trim(); } catch { return ''; } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const ORIGINEEL = `Hi Anne,

Ik wil even bijpraten over de security-afscherming.

Groet,
Luc`;

const slug = `zz-test-tracked-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);
const pagina = `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<h2>Mail-concepten</h2>
<div class="la-draft">
  <div class="la-draft-hdr"><b>Aan:</b> Anne Dijkstra &nbsp;·&nbsp; <b>Onderwerp:</b> Security</div>
  <div class="la-draft-txt">${ORIGINEEL}</div>
  <div class="la-draft-na">Nog niet verstuurd.</div>
</div>
${readFileSync(join(SKILL, 'annotator-snippet.html'), 'utf8')}`;
writeFileSync(bestand, pagina);

const url = `http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`;
let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-05: ${tekst}`); if (!ok) falen++; };

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'load' });
await page.waitForSelector('.la-draft-bar button', { timeout: 5000 });

// 1. Luc klikt "Bewerk tekst" en herschrijft een zin
await page.click('.la-draft-bar button');
const NIEUW = ORIGINEEL.replace('Ik wil even bijpraten over de security-afscherming.',
  'Kunnen we deze week de security-afscherming doornemen?');
await page.evaluate((t) => {
  const box = document.querySelector('.la-draft-txt');
  box.textContent = t;
}, NIEUW);
await page.click('.la-draft-bar button');   // klaar met bewerken -> opslaan
await sleep(1200);

// 2. de markup moet ins én del tonen, niet alleen de nieuwe tekst
const markup = await page.evaluate(() => {
  const box = document.querySelector('.la-draft-txt');
  return { ins: box.querySelectorAll('ins').length, del: box.querySelectorAll('del').length };
});
zeg(markup.ins > 0 && markup.del > 0,
  `wijziging zichtbaar als tracked change (${markup.ins} ins, ${markup.del} del)`);

// 2b. een bewerking hoort géén badge te krijgen en niet in de weeslijst te belanden.
// Dit ging mis en was in de browser meteen zichtbaar ("1 annotatie waarschijnlijk
// verwerkt") terwijl de opslag gewoon klopte: de assertie op ins/del zag dat niet.
const rommel = await page.evaluate(() => ({
  badges: document.querySelectorAll('.la-badge').length,
  wees: !!document.getElementById('la-wees'),
}));
zeg(rommel.badges === 0 && !rommel.wees,
  `geen badge en geen weeslijst voor een bewerking (badges: ${rommel.badges}, wees: ${rommel.wees})`);

// 3. het bewijs: staat het op schijf, met voor, na en de diff?
const jsonPath = await page.evaluate(() => window.LucAnnotator.bridge().jsonPath);
const pad = (jsonPath || '').replace(/^~/, homedir());
let opSchijf = null;
if (pad && existsSync(pad)) {
  const data = JSON.parse(readFileSync(pad, 'utf8'));
  opSchijf = (data.annotations || []).filter((a) => a.type === 'edit')[0] || null;
}
zeg(!!opSchijf, `bewerking teruggelezen uit ${pad || '(geen pad)'}`);

if (opSchijf) {
  zeg(opSchijf.origineel === ORIGINEEL, 'originele tekst bewaard');
  zeg(opSchijf.nieuw === NIEUW, 'herschreven tekst bewaard');
  const verwijderd = (opSchijf.diff || []).filter((o) => o.op === '-').map((o) => o.t).join('');
  const toegevoegd = (opSchijf.diff || []).filter((o) => o.op === '+').map((o) => o.t).join('');
  zeg(/bijpraten/.test(verwijderd) && /doornemen/.test(toegevoegd),
    'de diff wijst het gewijzigde deel aan, niet de hele tekst');
  // Een diff die alles als vervangen markeert is technisch waar en praktisch nutteloos.
  // Niet toetsen op een percentage — bij het herschrijven van een hele zin verandert
  // terecht veel — maar op tekst die aantoonbaar níet is aangeraakt: aanhef en afsluiting.
  const gelijk = (opSchijf.diff || []).filter((o) => o.op === '=').map((o) => o.t).join('');
  zeg(/Hi Anne,/.test(gelijk) && /Groet,/.test(gelijk) && /Luc/.test(gelijk),
    'aanhef en afsluiting staan als onveranderd in de diff, niet als vervangen');
}

// 4. overleeft het een reload? Anders is Lucs werk weg zodra hij ververst.
await page.reload({ waitUntil: 'load' });
await sleep(2500);
const naReload = await page.evaluate(() => {
  const box = document.querySelector('.la-draft-txt');
  return { ins: box.querySelectorAll('ins').length, del: box.querySelectorAll('del').length,
           nr: (window.LucAnnotator.drafts()[0] || {}).nr };
});
zeg(naReload.ins > 0 && naReload.del > 0, 'de bewerking staat er na een reload nog');

await browser.close();
rmSync(bestand, { force: true });
rmSync(join(homedir(), 'Desktop', 'annotaties', slug), { recursive: true, force: true });
process.exit(falen ? 1 : 0);
