#!/usr/bin/env node
// Render a seek(t) overlay to a transparent PNG sequence with headless Chromium.
//
//   node render_overlay.mjs --html assets/overlay/overlay.html --out assets/overlay/frames \
//        --beats assets/audio-analysis/beats.json [--lyrics assets/overlay/lyrics.json] \
//        [--storyboard video/storyboard.json] [--start 0] [--end <duration>] [--fps 30] [--workers 4]
//   node render_overlay.mjs ... --frames 12.5,45,120.2,210 --out video/contact-sheets/raw
//
// Modular re-render — only redo what changed, then assemble.py rebuilds only the chunks whose frames changed:
//   --ranges 12-18,40.5-44     time ranges in seconds
//   --cuts 3,7-9               storyboard cut indices (0-based) → their time ranges
//   --sections chorus,bridge   every storyboard cut with that section
//   --layers ribbon,lyric      draw only these layers (debugging a layer in isolation; don't use for final frames)
//   --scale 2                  supersampled output (2 → 3840x2160 for a 4K master)
//   --width 1080 --height 1920 CSS viewport of the overlay layout (default 1920x1080; vertical Shorts use 1080x1920)
//   --gl gpu|swiftshader|off   3D layer (three.js/WebGL): gpu (default; Metal on macOS) | software | disable (?gl=off)
//   --features <index.json>    plate features (plate_features.py) so graphics can follow the picture
//   --gl-scale 0.5             render the 3D layer at half resolution and upscale (soft fluid material hides it)
//
// The page is served from http://overlay.local/<absolute path> (requests are answered from disk), so ES modules
// work: `import ... from './world3d.js'` and the import map entries "three": "/__three/three.module.js" and
// "three/addons/": "/__three_addons/" map to this folder's node_modules/three (build/ and examples/jsm/).
// Nothing is fetched from the network.
//
// Files are named frame_%06d.png by ABSOLUTE frame index (round(t*fps)), so a partial re-render
// of a bad section drops straight into the full sequence. --green renders on #00FF00 instead of alpha.
// First run: (cd <skill>/scripts && npm install && npx playwright install chromium)
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
    return acc;
  }, []),
);
const need = (k) => { if (!args[k]) { console.error(`missing --${k}`); process.exit(1); } return args[k]; };

const html = path.resolve(need('html'));
const out = path.resolve(need('out'));
const readJson = (p) => (p && fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null);
const beatsPath = args.beats || 'assets/audio-analysis/beats.json';
const data = {
  beats: readJson(beatsPath),
  lyrics: readJson(args.lyrics || 'assets/overlay/lyrics.json'),
  storyboard: readJson(args.storyboard || 'video/storyboard.json'),
  scenes: readJson(args.scenes || 'assets/overlay/scenes.json'),   // optional lyric-driven graphic scenes
  features: readJson(args.features || 'assets/plate-features/index.json'),   // optional: plate_features.py output
};
if (!data.beats) { console.error(`beats.json not found at ${beatsPath}`); process.exit(1); }
const fps = Number(args.fps || data.beats.fps || 30);
const workers = Math.max(1, Number(args.workers || 4));
const skipExisting = !!args['skip-existing'];
// --scale 2 → 3840x2160 frames from the same 1920x1080 CSS layout (the overlay draws at devicePixelRatio).
const scale = Number(args.scale || 1);
const vw = Number(args.width || 1920), vh = Number(args.height || 1080);

const rangeList = (spec) => String(spec).split(',').map((r) => r.split('-').map(Number));
let times;
let ranges = null;
if (args.ranges) ranges = rangeList(args.ranges);
if (args.cuts || args.sections) {
  const cuts = data.storyboard?.cuts;
  if (!cuts) { console.error('--cuts/--sections need storyboard.json (--storyboard)'); process.exit(1); }
  ranges = ranges || [];
  if (args.cuts) for (const [a, b] of rangeList(args.cuts)) {
    for (let i = a; i <= (Number.isNaN(b) || b === undefined ? a : b); i++) if (cuts[i]) ranges.push([cuts[i].start, cuts[i].end]);
  }
  if (args.sections) {
    const want = String(args.sections).split(',');
    for (const c of cuts) if (want.includes(c.section)) ranges.push([c.start, c.end]);
  }
}
if (args.frames) {
  times = String(args.frames).split(',').map(Number);
} else if (ranges) {
  const set = new Set();
  for (const [a, b] of ranges) for (let f = Math.round(a * fps); f < Math.round(b * fps); f++) set.add(f);
  times = [...set].sort((x, y) => x - y).map((f) => f / fps);
  console.log(`re-rendering ${times.length} frames across ${ranges.length} range(s)`);
} else {
  const start = Number(args.start || 0);
  const end = Number(args.end || data.beats.duration);
  const f0 = Math.round(start * fps), f1 = Math.round(end * fps);
  times = Array.from({ length: f1 - f0 }, (_, i) => (f0 + i) / fps);
}
fs.mkdirSync(out, { recursive: true });

const q = new URLSearchParams();
if (args.green) q.set('bg', 'green');
if (args.layers) q.set('layers', String(args.layers));
const glMode = String(args.gl || 'gpu');
if (glMode === 'off') q.set('gl', 'off');
if (args['gl-scale']) q.set('glscale', String(args['gl-scale']));
const url = 'http://overlay.local' + html.split(path.sep).map(encodeURIComponent).join('/') + (q.toString() ? `?${q}` : '');
const THREE_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), 'node_modules', 'three', 'build');
const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json',
               '.png': 'image/png', '.jpg': 'image/jpeg', '.css': 'text/css', '.woff2': 'font/woff2' };
const launchArgs = glMode === 'gpu'
  ? (process.platform === 'darwin' ? ['--use-angle=metal', '--ignore-gpu-blocklist', '--enable-gpu-rasterization']
                                   : ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'])
  : glMode === 'swiftshader' ? ['--use-angle=swiftshader'] : [];
let reported = false;
let done = 0;
const t0 = Date.now();

// One browser per worker: pages in a shared browser serialise on its single compositor/GPU process.
// --capture canvas (default when not --green) reads the overlay canvas directly via toDataURL, so PNG encoding
// runs in each renderer in parallel instead of going through page.screenshot.
const capture = args.capture || (args.green ? 'screenshot' : 'canvas');
async function worker(slice) {
  const browser = await chromium.launch({ args: launchArgs });
  const page = await browser.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: scale });
  page.on('pageerror', (e) => console.error('pageerror:', e.message));
  await page.route('http://overlay.local/**', (route) => {
    let f = decodeURIComponent(new URL(route.request().url()).pathname);
    if (f.startsWith('/__three/')) f = path.join(THREE_DIR, f.slice('/__three/'.length));
    else if (f.startsWith('/__three_addons/')) f = path.join(THREE_DIR, '..', 'examples', 'jsm', f.slice('/__three_addons/'.length));
    if (!fs.existsSync(f)) return route.fulfill({ status: 404, body: 'not found' });
    route.fulfill({ status: 200, contentType: MIME[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await page.addInitScript((d) => { window.__DATA__ = d; }, data);
  await page.goto(url);
  await page.evaluate(() => window.ready);
  if (!reported) {
    reported = true;
    const gl = await page.evaluate(() => window.__gl3d || null);
    if (gl) console.log(`3D layer: ${gl}${/SwiftShader/i.test(gl) ? '  (software: slow; try --gl gpu or --gl-scale 0.5)' : ''}`);
  }
  for (const t of slice) {
    const file = path.join(out, `frame_${String(Math.round(t * fps)).padStart(6, '0')}.png`);
    if (skipExisting && fs.existsSync(file)) { done++; continue; }
    await page.evaluate((tt) => window.seek(tt), t);
    if (capture === 'canvas') {
      const url = await page.evaluate(() => (document.getElementById('c') || document.querySelector('canvas')).toDataURL('image/png'));
      fs.writeFileSync(file, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
    } else {
      await page.screenshot({ path: file, omitBackground: !args.green, type: 'png' });
    }
    done++;
    if (done % 300 === 0) {
      const rate = done / ((Date.now() - t0) / 1000);
      console.log(`${done}/${times.length} frames  ${rate.toFixed(1)} fps  eta ${((times.length - done) / rate).toFixed(0)}s`);
    }
  }
  await page.close();
  await browser.close();
}

// Contiguous chunks per worker keep each page's work local.
const n = Math.min(workers, times.length);
const size = Math.ceil(times.length / n);
await Promise.all(Array.from({ length: n }, (_, i) => worker(times.slice(i * size, (i + 1) * size))));
console.log(`rendered ${done} frames to ${out} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
