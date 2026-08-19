/* AC-7: geneste subpunten hangen visueel onder hun ouder — elk niveau springt een stap
   verder in en krijgt een verbindingshaakje naar boven.

   Waarom dit een eigen case is: deze opmaak was eerst ad hoc in één todolijst gezet, met
   selectors die aan die pagina's `.card` hingen en aan haar `--line`-token. Bij de volgende
   lijst was hij weg. De eigenschap die hier bewezen moet worden is dus niet "het staat in
   het snippet", maar dat het werkt zónder dat de pagina meewerkt: op een willekeurig
   blok-element en op een pagina die geen kleurtokens definieert.

   Het bewijs komt uit de computed styles in de browser, niet uit de CSS-tekst: een
   selector die niet matcht of een var() die niets oplevert leest in de bron nog steeds
   goed. */

import { chromium } from 'playwright-core';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const SKILL = join(homedir(), '.claude', 'skills', 'html-annotator');
const PORT = process.env.LUC_ANNOTATOR_PORT || '8791';

const slug = `zz-test-subindent-${Date.now()}`;
const bestand = join(homedir(), 'Desktop', `${slug}.html`);

/* Twee omgevingen in één pagina. De eerste sectie doet wat een todolijst doet: eigen
   .card en een eigen --line. De tweede definieert bewust niets — geen tokens, geen
   .card — en gebruikt een <li>, om te zien of de opmaak op zichzelf staat. */
writeFileSync(bestand, `<!doctype html><meta charset="utf-8"><title>${slug}</title>
<style>
  #met { --line: #e3e3de }
  #met .card { border: 1px solid var(--line); padding: 12px; margin-bottom: 8px }
  #zonder ul { list-style: none; padding: 0 }
</style>
<section id="met">
  <div class="card" id="m0">ouder</div>
  <div class="card la-sub" id="m1">niveau 1</div>
  <div class="card la-sub2" id="m2">niveau 2</div>
  <div class="card la-sub3" id="m3">niveau 3</div>
  <div class="card la-sub4" id="m4">niveau 4</div>
</section>
<section id="zonder">
  <ul>
    <li id="z0">ouder</li>
    <li class="la-sub" id="z1">niveau 1</li>
    <li class="la-sub2" id="z2">niveau 2</li>
  </ul>
  <div class="la-sub" id="zstap" style="--la-stap: 12px">eigen stap</div>
</section>
${readFileSync(join(SKILL, 'annotator-snippet.html'), 'utf8')}`);

let falen = 0;
const zeg = (ok, tekst) => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  case-07: ${tekst}`); if (!ok) falen++; };

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
await page.goto(`http://127.0.0.1:${PORT}/p/Desktop/${slug}.html`, { waitUntil: 'load' });

const meet = await page.evaluate(() => {
  const uit = {};
  for (const el of document.querySelectorAll('[id]')) {
    const s = getComputedStyle(el);
    const b = getComputedStyle(el, '::before');
    uit[el.id] = {
      ml: parseFloat(s.marginLeft),
      pos: s.position,
      haakje: b.content !== 'none' && parseFloat(b.borderLeftWidth) > 0 && parseFloat(b.borderBottomWidth) > 0,
      kleur: b.borderLeftColor,
      links: parseFloat(b.left),
      breed: parseFloat(b.width),
    };
  }
  return uit;
});
await browser.close();

// Inspringing loopt op per niveau, en een ouder zonder klasse blijft staan waar hij staat.
zeg([0, 30, 60, 90, 120].every((v, i) => meet[`m${i}`].ml === v),
  `elk niveau springt 30px verder in (gemeten: ${[0, 1, 2, 3, 4].map((i) => meet[`m${i}`].ml).join(', ')})`);

// Het haakje hangt aan een ::before, dus het element moet zelf relatief gepositioneerd
// zijn. Dat mag niet van de pagina komen: de <li> in sectie 2 doet dat niet.
zeg(['m1', 'm2', 'm3', 'm4', 'z1', 'z2'].every((id) => meet[id].pos === 'relative' && meet[id].haakje),
  'elk subpunt is relatief gepositioneerd en tekent een haakje — ook de <li> zonder pagina-CSS');

zeg(!meet.m0.haakje && !meet.z0.haakje,
  'een punt zonder subklasse krijgt geen haakje');

// De pagina-token wordt gevolgd als hij bestaat, en anders is de lijn nog steeds
// zichtbaar. Onzichtbaar (transparant, of dezelfde kleur als wit) is de faalmodus die
// de fallback moet voorkomen.
zeg(meet.m1.kleur === 'rgb(227, 227, 222)',
  `--line van de pagina wordt gevolgd (${meet.m1.kleur})`);
// Let op de ondergrens: zonder border erft borderLeftColor de tekstkleur (zwart), dus
// "niet wit" is geen bewijs. Een licht grijs op een lichte pagina is wat het moet zijn.
const z1rgb = meet.z1.kleur.match(/\d+/g).map(Number);
zeg(meet.z1.haakje && z1rgb.every((k) => k > 150 && k < 245),
  `zonder --line valt de lijn terug op een zichtbaar grijs (${meet.z1.kleur})`);

// Het haakje ligt in de goot links van het punt: linkerrand negatief, en het blijft
// binnen de inspringing zodat het niet over de tekst van de ouder valt.
zeg(meet.m1.links < 0 && Math.abs(meet.m1.links) < 30 && meet.m1.breed < 30,
  `het haakje ligt binnen de goot van 30px (left ${meet.m1.links}, breedte ${meet.m1.breed})`);

// De stap is te verstellen, en het haakje rekent mee — anders hangt de lijn los zodra
// een smallere pagina de inspringing verkleint.
zeg(meet.zstap.ml === 12 && Math.abs(meet.zstap.links) < 12 && meet.zstap.breed < 12,
  `--la-stap verstelt inspringing én haakje (ml ${meet.zstap.ml}, left ${meet.zstap.links}, breedte ${meet.zstap.breed})`);

rmSync(bestand, { force: true });
rmSync(join(homedir(), 'Desktop', 'annotaties', slug), { recursive: true, force: true });
process.exit(falen ? 1 : 0);
