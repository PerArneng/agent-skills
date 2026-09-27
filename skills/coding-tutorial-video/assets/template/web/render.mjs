// Frame-accurate renderer: N parallel headless pages seek the timeline frame by frame,
// each pipes JPEGs into its own ffmpeg segment; segments are concatenated and the
// episode's narration (config.episodes[ep].audio) is muxed in.
//
// Needs a server on :5199 — use the production build (`npx vite build && npx vite preview --port 5199`),
// not the dev server: dev-server dependency re-optimisation can reload pages mid-render.
//
// usage: node render.mjs --ep ep1 [--scale 2] [--fps 60] [--workers 6] [--from 0] [--to <duration>] [--crf 18] [--out file.mp4]
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const cfg = JSON.parse(fs.readFileSync('config.json', 'utf8'));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const EP = arg('ep', 'ep1');
const epc = cfg.episodes[EP];
const FPS = +arg('fps', cfg.fps), WORKERS = +arg('workers', 6), CRF = arg('crf', '18');
const URL = arg('url', `http://localhost:5199/?render&ep=${EP}`);
fs.mkdirSync(path.dirname(epc.output), { recursive: true });
const OUT = path.resolve(arg('out', epc.output));
const AUDIO = path.resolve(epc.audio);
const T0 = +arg('from', 0), T1 = +arg('to', epc.duration);
const total = Math.round((T1 - T0) * FPS);
const tmp = path.resolve(`.render_${EP}`);
fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(tmp);

const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist'] });
const per = Math.ceil(total / WORKERS);
let done = 0;
const start = Date.now();

async function worker(w) {
  const a = w * per, b = Math.min(total, a + per);
  if (a >= b) return null;
  // --scale / config.scale = deviceScaleFactor: a 1920×1080 stage at scale 2 renders true 3840×2160 (crisp text/vectors)
  const page = await browser.newPage({ viewport: { width: cfg.width, height: cfg.height }, deviceScaleFactor: +arg('scale', cfg.scale || 1) });
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(URL);
  await page.waitForFunction(() => window.ready, null, { timeout: 60000 });
  const file = path.join(tmp, `seg_${w}.mp4`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF, '-pix_fmt', 'yuv420p', '-tag:v', 'avc1', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    const t = T0 + f / FPS;
    await page.evaluate((t) => { window.seek(t); return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }, t);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (++done % 120 === 0) {
      const el = (Date.now() - start) / 1000;
      console.log(`${done}/${total} frames  ${(done / el).toFixed(1)} fps  eta ${((total - done) / (done / el) / 60).toFixed(1)} min`);
    }
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await page.close();
  return file;
}

const segs = (await Promise.all(Array.from({ length: WORKERS }, (_, w) => worker(w)))).filter(Boolean);
await browser.close();
fs.writeFileSync(path.join(tmp, 'list.txt'), segs.map((s) => `file '${s}'`).join('\n'));
execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'),
  '-ss', String(T0), '-t', String(T1 - T0), '-i', AUDIO,
  '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
fs.rmSync(tmp, { recursive: true, force: true });
console.log('wrote', OUT, `in ${((Date.now() - start) / 60000).toFixed(1)} min`);
