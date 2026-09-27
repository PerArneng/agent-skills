// Screenshot the timeline at given seconds and tile them into one contact sheet for review.
// usage: node shot.mjs [--ep ep1] 1.5 3.2 12 ...   (server on :5199 must be running: dev or preview)
// writes shots/t_<t>.jpg and shots/sheet.jpg (tiles in the order given)
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';

const cfg = JSON.parse(fs.readFileSync('config.json', 'utf8'));
const epArg = process.argv.indexOf('--ep');
const EP = epArg > 0 ? process.argv[epArg + 1] : 'ep1';
const ts = process.argv.slice(2).filter((a, i, all) => all[i - 1] !== '--ep').map(Number).filter((n) => !Number.isNaN(n));
fs.rmSync('shots', { recursive: true, force: true });
fs.mkdirSync('shots');
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: cfg.width, height: cfg.height } });
page.on('console', (m) => m.type() === 'error' && console.log('console:', m.text()));
page.on('pageerror', (e) => console.log('pageerror:', e.message));
await page.goto(`http://localhost:5199/?render&ep=${EP}`);
await page.waitForFunction(() => window.ready, null, { timeout: 30000 });
const files = [];
for (const [i, t] of ts.entries()) {
  await page.evaluate((t) => { window.seek(t); return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }, t);
  const f = `shots/${String(i).padStart(3, '0')}_t${t.toFixed(2)}.jpg`;
  await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
  files.push(f);
}
await browser.close();
if (files.length) {
  const cols = Math.min(8, files.length), rows = Math.ceil(files.length / cols);
  const tw = cfg.width >= cfg.height ? 480 : 270, th = Math.round((tw * cfg.height) / cfg.width);
  files.forEach((f, i) => fs.copyFileSync(f, `shots/seq_${String(i).padStart(3, '0')}.jpg`));
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', 'shots/seq_%03d.jpg', '-vf', `scale=${tw}:${th},tile=${cols}x${rows}`, '-frames:v', '1', 'shots/sheet.jpg']);
  files.forEach((_, i) => fs.rmSync(`shots/seq_${String(i).padStart(3, '0')}.jpg`));
  console.log('contact sheet: shots/sheet.jpg  order:', ts.join(', '));
}
