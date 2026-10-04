// YouTube thumbnail (16:9) in the v4 look, drawn in code: a frame from a Veo clip, the tracked lock-on (face
// reticle + label, brackets) from plate_features.py, a faint agent mesh, a typed terminal hook
// and the title as a split-flap departure board in the video's own fonts. Every word is spelled by code.
//
//   node video/tools/make_thumbnail_v4.mjs            (run from the project root)
// Writes assets/thumbnail/thumb-v4{,-b,-c,-d}.png (1920x1080) + .jpg (1280x720, YouTube size) and a shelf-size preview.
import { chromium } from '../../.claude/skills/futuristic-music-video/scripts/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const FEAT = JSON.parse(fs.readFileSync('assets/plate-features/index.json', 'utf8'));
const VARIANTS = {
  'v4': { clip: 'assets/video-clips/perf-hairwhip-fast.mp4', t: 1.5, hook: '> WHO BUYS THE PRODUCT?', status: 'STATUS: OBSOLETE', red: true, zoom: 1.35, dx: -400 },
  'v4-b': { clip: 'assets/video-clips/perf-red-fast.mp4', t: 2.5, hook: '> HUMANS IN THE LOOP: 0', status: 'STATUS: REPLACEABLE', red: true, zoom: 1.25, dx: -330 },
  // A/B concepts: the shock headline as a departure board, and the verdict as a big signage slam
  'v4-c': { clip: 'assets/video-clips/perf-hairwhip-fast.mp4', t: 4.0, hook: '> AGENTS IN THE LOOP', status: 'STATUS: FIRED', red: true, zoom: 1.3, dx: -400,
            title: { style: 'board', rows: ['WORKERS', 'FIRED'], colors: ['#FFFFFF', '#FF3B3B'], head: ['LABOR BOARD · DEPARTURES', 'ALL GATES'] } },
  'v4-d': { clip: 'assets/video-clips/perf-racks-fast.mp4', t: 3.0, hook: '> AGENTS IN THE LOOP', status: 'STATUS: OBSOLETE', red: true, zoom: 1.18, dx: -400, dy: 90,
            title: { style: 'slam', lines: ['THE AGENTS', 'HAVE WON'], colors: ['#FFFFFF', '#FF3B3B'], size: 205 } },
};
const font = f => 'data:font/ttf;base64,' + fs.readFileSync('assets/overlay/fonts/' + f).toString('base64');

const html = (v, img, smp) => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: "Big Shoulders Display"; src: url(${font('BigShouldersDisplay.ttf')}); font-weight: 100 900; }
@font-face { font-family: "Share Tech Mono"; src: url(${font('ShareTechMono-Regular.ttf')}); }
html,body{margin:0;width:1920px;height:1080px;background:#07090C} canvas{display:block}</style></head><body>
<canvas id="c" width="1920" height="1080"></canvas><script>
(async () => {
  const W = 1920, H = 1080, V = ${JSON.stringify(v)}, S = ${JSON.stringify(smp)};
  const C = { cool: '#7CFFE1', warn: '#FFB25A', alarm: '#FF3B3B', type: '#EDEFF2', dim: '#3A4650', human: '#A46BFF' };
  const FS = '"Big Shoulders Display"', FT = '"Share Tech Mono"', FM = 'Menlo, monospace';
  await Promise.all(['900 100px ' + FS, '800 100px ' + FS, '400 60px ' + FT].map(f => document.fonts.load(f)));
  const g = document.getElementById('c').getContext('2d');
  const hash = (i, s = 0) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };
  const im = new Image(); im.src = ${JSON.stringify(img)}; await im.decode();
  const s = Math.max(W / im.width, H / im.height) * V.zoom, ox = Math.min(im.width * s - W, Math.max(0, (im.width * s - W) / 2 - V.dx)), oy = Math.min(im.height * s - H, Math.max(0, (im.height * s - H) / 2 - (V.dy || 0)));
  const map = (x, y) => [x * im.width * s - ox, y * im.height * s - oy];
  g.fillStyle = '#07090C'; g.fillRect(0, 0, W, H);
  g.filter = 'contrast(1.1) saturate(1.08)'; g.drawImage(im, -ox, -oy, im.width * s, im.height * s); g.filter = 'none';
  const acc = V.red ? C.alarm : C.cool;
  // grade: the right side darkens for the board, vignette
  let gr = g.createLinearGradient(W * 0.45, 0, W, 0); gr.addColorStop(0, 'rgba(4,6,9,0)'); gr.addColorStop(0.45, 'rgba(4,6,9,0.78)'); gr.addColorStop(1, 'rgba(4,6,9,0.9)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  const vg = g.createRadialGradient(W * 0.35, H / 2, H * 0.4, W / 2, H / 2, W * 0.62);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  // agent mesh on the right: translucent nodes + links, never on her
  const P = S.person, fb = P.face, fc = map(fb[0] + fb[2] / 2, fb[1] + fb[3] / 2), fh = fb[3] * im.height * s;
  const [qx0] = map(P.bbox[0], 0), [qx1] = map(P.bbox[0] + P.bbox[2], 0);
  const N = []; for (let i = 0; i < 46; i++) { const x = 40 + hash(i, 1) * (W - 80), y = 40 + hash(i, 2) * (H - 80), z = 0.4 + 0.6 * hash(i, 3);
    if ((x < qx0 - 40 || x > qx1 + 40) && Math.hypot(x - fc[0], y - fc[1]) > fh + 140) N.push({ x, y, z }); }
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) { const d = Math.hypot(N[i].x - N[j].x, N[i].y - N[j].y);
    if (d < 260) { g.strokeStyle = 'rgba(124,255,225,' + (0.3 * (1 - d / 260) * Math.min(N[i].z, N[j].z)) + ')'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(N[i].x, N[i].y); g.lineTo(N[j].x, N[j].y); g.stroke(); } }
  N.forEach((n, i) => { const r = 5 + 9 * n.z, c = hash(i, 4) < 0.25 ? '255,178,90' : '124,255,225';
    g.strokeStyle = 'rgba(' + c + ',' + (0.3 + 0.25 * n.z) + ')'; g.lineWidth = 2; g.beginPath(); g.arc(n.x, n.y, r, 0, 6.283); g.stroke();
    g.fillStyle = 'rgba(' + c + ',0.22)'; g.beginPath(); g.arc(n.x, n.y, r * 0.4, 0, 6.283); g.fill(); });
  // traced silhouette + lock-on brackets
  if (V.trace && P.poly) {                                   // off: the clip's silhouette is too loose at thumbnail size
    const poly = P.poly.map(([x, y]) => map(x, y));
    g.save(); g.beginPath(); poly.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.closePath();
    g.shadowColor = C.cool; g.shadowBlur = 18; g.strokeStyle = 'rgba(124,255,225,0.7)'; g.lineWidth = 3; g.stroke();
    g.setLineDash([180, 99999]); g.lineDashOffset = -500; g.strokeStyle = '#FFFFFF'; g.lineWidth = 5; g.stroke(); g.restore();
  }
  const [bx, by, bw, bh] = P.bbox, a = map(bx, by), b = map(bx + bw, by + bh), pad = 26;
  const X0 = Math.max(30, a[0] - pad), X1 = Math.min(W - 30, b[0] + pad), Y0 = Math.max(110, a[1] - pad), Y1 = Math.min(b[1] + pad, H - 30);
  g.strokeStyle = acc; g.lineWidth = 6;
  const br = (x, y, sx, sy) => { g.beginPath(); g.moveTo(x, y + sy * 64); g.lineTo(x, y); g.lineTo(x + sx * 64, y); g.stroke(); };
  br(X0, Y0, 1, 1); br(X1, Y0, -1, 1); br(X0, Y1, 1, -1); br(X1, Y1, -1, -1);
  // face reticle with the label to its left (the board owns the right side)
  const r = Math.max(56, fh * 0.75);
  g.save(); g.shadowColor = acc; g.shadowBlur = 16; g.strokeStyle = acc; g.lineWidth = 5; g.beginPath(); g.arc(fc[0], fc[1], r, 0, 6.283); g.stroke();
  for (let i = 0; i < 4; i++) { const an = i * Math.PI / 2 + 0.4; g.beginPath();
    g.moveTo(fc[0] + Math.cos(an) * (r + 6), fc[1] + Math.sin(an) * (r + 6)); g.lineTo(fc[0] + Math.cos(an) * (r + 30), fc[1] + Math.sin(an) * (r + 30)); g.stroke(); }
  g.restore();
  g.font = '400 38px ' + FT; const lw = Math.max(g.measureText('SUBJECT 01 · HUMAN').width, g.measureText(V.status).width) + 10;
  const left = fc[0] - r - 50 - lw > 40, lx = left ? fc[0] - r - 50 : fc[0] - lw / 2, ly = left ? fc[1] + r * 0.4 : fc[1] + r + 40;
  if (left) { g.strokeStyle = acc; g.lineWidth = 3; g.beginPath(); g.moveTo(fc[0] - r * 0.72, fc[1] + r * 0.72); g.lineTo(lx + 10, ly + 30); g.stroke(); }
  g.textAlign = left ? 'right' : 'left';
  g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(left ? lx - lw - 12 : lx - 12, ly - 2, lw + 24, 92);
  g.fillStyle = C.type; g.fillText('SUBJECT 01 · HUMAN', lx, ly + 37); g.fillStyle = acc; g.fillText(V.status, lx, ly + 79); g.textAlign = 'left';
  const TT = V.title || { style: 'board', rows: ['AGENTS', 'IN THE LOOP'], colors: ['#FFFFFF', C.cool], head: ['NOW BOARDING · #ETHACC', 'GATE 24/7'] };
  const hook = (x1, y) => {                                     // typed terminal line ending at x1, block cursor
    g.font = '400 58px ' + FT; const hw = g.measureText(V.hook).width, hx = x1 - hw - 44;
    g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(hx - 20, y, hw + 70, 88);
    g.fillStyle = acc; g.fillText(V.hook, hx, y + 64); g.fillRect(hx + hw + 10, y + 16, 30, 56);
  };
  if (TT.style === 'board') {
    // title: split-flap departure board on the right
    const rows = TT.rows, n = 11, fs = 138, tw = 74, th = 158, gap = 6;
    const bw2 = n * (tw + gap) - gap, x0 = W - 70 - bw2, y0 = 360;
    g.fillStyle = 'rgba(5,7,10,0.88)'; g.fillRect(x0 - 22, y0 - 70, bw2 + 44, 2 * th + 3 * gap + 100);
    g.strokeStyle = 'rgba(58,70,80,1)'; g.lineWidth = 2; g.strokeRect(x0 - 22, y0 - 70, bw2 + 44, 2 * th + 3 * gap + 100);
    g.font = '400 28px ' + FT; g.fillStyle = C.warn; if ('letterSpacing' in g) g.letterSpacing = '6px';
    g.fillText(TT.head[0], x0, y0 - 26); g.textAlign = 'right'; g.fillText(TT.head[1], x0 + bw2, y0 - 26); g.textAlign = 'left';
    if ('letterSpacing' in g) g.letterSpacing = '0px';
    g.font = '800 ' + fs + 'px ' + FS; g.textAlign = 'center'; g.textBaseline = 'middle';
    rows.forEach((row, ri) => {
      const pad0 = Math.floor((n - row.length) / 2);
      for (let ci = 0; ci < n; ci++) {
        const ch = row[ci - pad0] || ' ', x = x0 + ci * (tw + gap), y = y0 + ri * (th + gap * 2), hy = y + th / 2;
        const grd = g.createLinearGradient(0, y, 0, y + th); grd.addColorStop(0, '#20262d'); grd.addColorStop(0.5, '#13171b'); grd.addColorStop(1, '#0b0d10');
        g.fillStyle = grd; g.beginPath(); g.roundRect(x, y, tw, th, 8); g.fill();
        if (ch !== ' ') { g.fillStyle = TT.colors[ri]; g.fillText(ch, x + tw / 2, hy + 6); }
        g.fillStyle = 'rgba(0,0,0,0.85)'; g.fillRect(x, hy - 1.5, tw, 3);
        g.fillStyle = 'rgba(255,255,255,0.05)'; g.fillRect(x, y, tw, th / 2 - 2);
      }
    });
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    hook(x0 + bw2, y0 + 2 * th + 3 * gap + 70);
  } else {
    // title: big signage slam on the right (chromatic split, accent underline), the typed hook above it
    const X1 = W - 80, fs = TT.size || 230, lh = fs * 0.88, y0 = 470;
    hook(X1, 250);
    g.font = '900 ' + fs + 'px ' + FS; g.textAlign = 'right'; g.textBaseline = 'middle'; if ('letterSpacing' in g) g.letterSpacing = '6px';
    TT.lines.forEach((ln, i) => {
      const y = y0 + i * lh;
      g.save(); g.shadowColor = 'rgba(0,0,0,0.8)'; g.shadowBlur = 40;
      g.fillStyle = 'rgba(255,59,59,0.55)'; g.fillText(ln, X1 - 9, y); g.fillStyle = 'rgba(124,255,225,0.5)'; g.fillText(ln, X1 + 9, y);
      g.fillStyle = TT.colors[i]; g.fillText(ln, X1, y); g.restore();
    });
    if ('letterSpacing' in g) g.letterSpacing = '0px';
    g.fillStyle = acc; g.fillRect(X1 - 260, y0 + (TT.lines.length - 0.4) * lh + 22, 260, 10);
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  }
  // HUD corners, readouts, scanlines
  g.strokeStyle = 'rgba(237,239,242,0.6)'; g.lineWidth = 3;
  const c4 = (x, y, sx, sy) => { g.beginPath(); g.moveTo(x, y + sy * 46); g.lineTo(x, y); g.lineTo(x + sx * 46, y); g.stroke(); };
  c4(24, 24, 1, 1); c4(W - 24, 24, -1, 1); c4(24, H - 24, 1, -1); c4(W - 24, H - 24, -1, -1);
  g.font = '600 26px ' + FM; g.fillStyle = 'rgba(237,239,242,0.8)'; g.fillText('T 02:28.4   136 BPM', 56, 74);
  g.textAlign = 'right'; g.fillStyle = C.alarm; g.fillText('HUMANS IN THE LOOP 3.1%', W - 56, 74); g.textAlign = 'left';
  g.fillStyle = 'rgba(0,0,0,0.07)'; for (let y = 0; y < H; y += 3) g.fillRect(0, y, W, 1);
  window.done = true;
})();
</script></body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (const [k, v] of Object.entries(VARIANTS)) {
  const png = `/tmp/thumb-src-${k}.png`;
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(v.t), '-i', v.clip, '-frames:v', '1', '-vf', 'unsharp=5:5:0.5', png]);
  const F = FEAT[v.clip], smp = F.samples.reduce((a, b) => (b.person?.face && Math.abs(b.t - v.t) < Math.abs(a.t - v.t)) || !a.person?.face ? b : a);
  await page.setContent(html(v, 'data:image/png;base64,' + fs.readFileSync(png).toString('base64'), smp));
  await page.waitForFunction(() => window.done === true, null, { timeout: 30000 });
  const out = `assets/thumbnail/thumb-${k}.png`;
  await page.screenshot({ path: out });
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out, '-vf', 'scale=1280:720:flags=lanczos', '-q:v', '2', out.replace('.png', '.jpg')]);
  console.log('wrote', out, '+ .jpg');
}
await browser.close();
execFileSync('ffmpeg', ['-v', 'error', '-y', ...Object.keys(VARIANTS).flatMap(k => ['-i', `assets/thumbnail/thumb-${k}.png`]),
  '-filter_complex', Object.keys(VARIANTS).map((_, i) => `[${i}]scale=320:-1[s${i}]`).join(';') + ';' + Object.keys(VARIANTS).map((_, i) => `[s${i}]`).join('') + `hstack=${Object.keys(VARIANTS).length}`,
  'assets/thumbnail/thumb-v4-small.png']);
console.log('wrote assets/thumbnail/thumb-v4-small.png');
