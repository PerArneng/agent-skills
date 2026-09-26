// 67.62 – 82.6  Calibrated trust
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, prog, lerp, E, hash, sceneTitle, click, cursorHide, gsap } from '../lib.js';
import { hexagon, roundRect, arcBand } from '../shapes.js';

const GC = [540, 1400], GR = 272;

export default function s7() {
  sceneTitle('04', 'Calibrated Trust', 67.8, 82.3);
  morph(67.55, hexagon(540, 760, 300), 1.0, 'expo.inOut');
  heroColor(67.6, '#94a3b8', '#6366f1', '#1e293b', 0.8);
  bgTo(67.5, '#07070f', '#1e1b4b', '#111827', 0.4, 1.4);

  // black box cube
  const persp = el('div', 'abs');
  persp.style.cssText = 'width:260px;height:260px;perspective:1100px;z-index:3';
  const cube = document.createElement('div');
  cube.style.cssText = 'position:absolute;inset:0;transform-style:preserve-3d;--z:130px';
  const FACES = ['rotateY(0deg)', 'rotateY(90deg)', 'rotateY(180deg)', 'rotateY(-90deg)', 'rotateX(90deg)', 'rotateX(-90deg)'];
  const faces = FACES.map((r) => {
    const f = document.createElement('div');
    f.style.cssText = `position:absolute;inset:0;transform:${r} translateZ(var(--z));background:linear-gradient(145deg,#1f1f33,#050509);border:2px solid rgba(165,180,252,.35);border-radius:18px;display:flex;align-items:center;justify-content:center;font:700 130px var(--head);color:rgba(199,210,254,.85);box-shadow:inset 0 0 60px rgba(99,102,241,.25)`;
    f.textContent = '?';
    cube.appendChild(f);
    return f;
  });
  persp.appendChild(cube);
  place(persp, 540, 760);
  pop(persp, 69.2, { dur: 0.9, ease: 'expo.out', scale: 0.3 });
  drive((t) => (cube.style.transform = `rotateX(${(-20 + Math.sin(t * 0.8) * 15).toFixed(2)}deg) rotateY(${(t * 50) % 360}deg)`));
  tl.to(cube, { '--z': '520px', duration: 0.8, ease: 'power3.in' }, 72.25);
  tl.to(faces, { opacity: 0, duration: 0.6, ease: 'power2.in' }, 72.4);
  const lbl = el('div', 'abs', null, 'BLACK BOX');
  lbl.style.cssText = 'font:700 30px var(--mono);letter-spacing:.35em;color:var(--muted)';
  place(lbl, 540, 520);
  pop(lbl, 69.8);
  out(lbl, 72.2, { dur: 0.4 });

  // recommendation card
  const rec = el('div', 'abs glass');
  rec.style.cssText += 'width:600px;padding:34px 40px;text-align:center;z-index:4;border-radius:40px';
  rec.innerHTML = `<div style="font:600 30px var(--mono);letter-spacing:.2em;color:var(--muted)">RECOMMENDATION</div><div style="font:700 84px/1.1 var(--head);margin-top:10px">Surgery</div>`;
  place(rec, 540, 1160);
  pop(rec, 70.55, { dur: 0.8, ease: 'expo.out', scale: 0.8 });
  const qs = [[210, 1060], [880, 1120], [800, 1330]].map(([x, y], i) => {
    const q = el('div', 'abs', null, '?');
    q.style.cssText = 'font:700 90px var(--head);color:rgba(199,210,254,.5)';
    place(q, x, y);
    float(q, { amp: 18, speed: 0.9, seed: i * 4 });
    pop(q, 70.9 + i * 0.12);
    return q;
  });
  out(qs, 72.3, { dur: 0.4 });

  // logic path reveal
  morph(72.3, roundRect(540, 690, 960, 620, 60), 1.0, 'expo.inOut');
  heroColor(72.3, '#22d3ee', '#a78bfa', '#34d399', 0.8);
  bgTo(72.2, '#0a1a3f', '#155e75', '#4c1d95', 0.55, 1.2);
  const TOP = [['Lab results', 220], ['Imaging', 540], ['History', 860]];
  const RISK = [['High', '#fb3b5e'], ['Med', '#fbbf24'], ['Low', '#34d399']];
  const graph = el('div', 'abs', null, `<svg width="1080" height="1920" viewBox="0 0 1080 1920">
    ${TOP.map(([, x]) => `<path class="e" d="M${x} 510 C${x} 610 540 590 540 660" fill="none" stroke="url(#heroStroke)" stroke-width="6" stroke-linecap="round"/>`).join('')}
    <path class="e" d="M540 740 L540 850" fill="none" stroke="url(#heroStroke)" stroke-width="6" stroke-linecap="round"/>
    ${TOP.map(([, x]) => `<path class="f" d="M${x} 510 C${x} 610 540 590 540 660" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-dasharray="4 40"/>`).join('')}
    <path class="f" d="M540 740 L540 850" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-dasharray="4 40"/></svg>`);
  graph.style.zIndex = 1;
  const edges = graph.querySelectorAll('.e'), flows = graph.querySelectorAll('.f');
  gsap.set(edges, { drawSVG: '0%' });
  gsap.set(flows, { opacity: 0 });
  tl.to(edges, { drawSVG: '100%', duration: 0.7, stagger: 0.15, ease: 'power2.inOut' }, 73.3);
  tl.to(flows, { opacity: 0.8, duration: 0.4 }, 74.2);
  drive((t) => flows.forEach((f) => f.setAttribute('stroke-dashoffset', (-t * 90).toFixed(1))));

  const nodes = TOP.map(([name, x], i) => {
    const n = el('div', 'abs chip glass', null, `<span>${name}</span>`);
    n.style.cssText += 'font-size:34px;z-index:3';
    place(n, x, 470);
    pop(n, 72.85 + i * 0.12);
    return n;
  });
  const risk = el('div', 'abs chip', null, `<span class="ico" style="color:#c4b5fd">${icon('brain')}</span><span>Risk model</span>`);
  risk.style.cssText += 'font-size:36px;background:linear-gradient(120deg,rgba(99,102,241,.5),rgba(168,85,247,.5));border:1.5px solid rgba(196,181,253,.7);z-index:3';
  place(risk, 540, 700);
  pop(risk, 73.2);
  tl.to(rec, { y: 930, scale: 0.78, duration: 0.9, ease: 'expo.inOut' }, 73.3);

  // risk priority cards
  const tags = RISK.map(([t, c], i) => {
    const g = el('div', 'abs', null, `<span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:${c};box-shadow:0 0 12px ${c}"></span> ${t}`);
    g.style.cssText = `font:700 26px var(--mono);padding:10px 20px;border-radius:999px;background:rgba(10,8,30,.85);border:2px solid ${c};color:#fff;z-index:4;white-space:nowrap;display:flex;gap:10px;align-items:center`;
    place(g, TOP[i][1] + 90, 405);
    pop(g, 76.5 + i * 0.13, { ease: 'back.out(3)' });
    tl.to(nodes[i], { borderColor: c, boxShadow: `0 0 36px -4px ${c}`, duration: 0.3 }, 76.5 + i * 0.13);
    return g;
  });

  // confidence gauge
  morph(74.5, arcBand(GC[0], GC[1], GR + 40, 80), 1.0, 'expo.inOut');
  const segs = [[0, 0.4, '#fb3b5e'], [0.4, 0.7, '#fbbf24'], [0.7, 1, '#34d399']];
  const pt = (v, r) => [GC[0] - Math.cos(v * Math.PI) * r, GC[1] - Math.sin(v * Math.PI) * r];
  const gauge = el('div', 'abs', null, `<svg width="1080" height="1920" viewBox="0 0 1080 1920">
    ${segs.map(([a, b, c]) => { const [x1, y1] = pt(a + 0.006, GR), [x2, y2] = pt(b - 0.006, GR); return `<path class="seg" d="M${x1} ${y1} A${GR} ${GR} 0 0 1 ${x2} ${y2}" fill="none" stroke="${c}" stroke-width="40" stroke-linecap="round" style="filter:drop-shadow(0 0 12px ${c})"/>`; }).join('')}
    ${Array.from({ length: 21 }, (_, i) => { const [x1, y1] = pt(i / 20, GR - 48), [x2, y2] = pt(i / 20, GR - (i % 5 ? 62 : 76)); return `<line class="tk" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="rgba(255,255,255,.5)" stroke-width="4" stroke-linecap="round"/>`; }).join('')}
    <g class="needle"><line x1="${GC[0]}" y1="${GC[1]}" x2="${GC[0]}" y2="${GC[1] - 225}" stroke="#fff" stroke-width="10" stroke-linecap="round" style="filter:drop-shadow(0 0 10px #fff)"/></g>
    <circle cx="${GC[0]}" cy="${GC[1]}" r="24" fill="#fff"/></svg>`);
  gauge.style.zIndex = 2;
  const segEls = gauge.querySelectorAll('.seg'), needle = gauge.querySelector('.needle');
  gsap.set(segEls, { drawSVG: '0%' });
  gsap.set(gauge, { opacity: 0 });
  tl.to(gauge, { opacity: 1, duration: 0.3 }, 74.9);
  tl.to(segEls, { drawSVG: '100%', duration: 0.5, stagger: 0.18, ease: 'power2.out' }, 74.95);
  const gv = { v: 0 };
  tl.to(gv, { v: 0.874, duration: 1.1, ease: 'elastic.out(1,0.55)' }, 75.5);
  tl.to(gv, { v: 0.34, duration: 0.9, ease: 'power3.inOut' }, 81.05);
  const num = el('div', 'abs');
  num.style.cssText = 'text-align:center;white-space:nowrap';
  num.innerHTML = `<div class="n" style="font:700 96px/1 var(--mono)">0%</div><div style="font:600 28px var(--mono);letter-spacing:.25em;color:var(--muted);margin-top:8px">CONFIDENCE</div>`;
  place(num, GC[0], GC[1] - 95);
  pop(num, 75.3);
  const nEl = num.querySelector('.n');
  drive((t) => {
    const jitter = t > 77.7 && t < 81.05 ? (hash(Math.floor(t * 6)) - 0.5) * 0.008 : 0;
    const v = gv.v + jitter;
    needle.setAttribute('transform', `rotate(${(-90 + v * 180).toFixed(2)} ${GC[0]} ${GC[1]})`);
    const precise = t > 77.7;
    nEl.textContent = (v * 100).toFixed(precise ? 1 : 0) + '%';
    nEl.style.color = v < 0.4 ? '#fb3b5e' : v < 0.7 ? '#fbbf24' : '#34d399';
  });
  tl.to(gauge.querySelectorAll('.tk'), { stroke: '#fff', duration: 0.1, stagger: 0.03, yoyo: true, repeat: 1 }, 78.2);

  // take control
  const tc = el('div', 'abs');
  tc.style.cssText = 'padding:28px 60px;border-radius:999px;font:700 44px var(--head);white-space:nowrap;display:flex;gap:18px;align-items:center;background:linear-gradient(120deg,#f43f5e,#f97316);box-shadow:0 0 70px rgba(244,63,94,.7), inset 0 2px 0 rgba(255,255,255,.35);z-index:5';
  tc.innerHTML = `<span class="ico" style="width:52px;height:52px">${icon('hand', 2.2)}</span>Take control`;
  place(tc, 540, 1520);
  pop(tc, 81.5, { ease: 'back.out(2.2)' });
  heroColor(81.1, '#fb3b5e', '#f97316', '#fbbf24', 0.6);
  bgTo(81.0, '#2a0a14', '#7c2d12', '#4c1d95', 0.7, 0.8);
  click(560, 1525, 82.05, 82.12, 0.5);
  cursorHide(82.4);

  out([persp, rec, graph, ...nodes, risk, ...tags, gauge, num, tc], 82.3, { dur: 0.55, stagger: 0.015, blur: 22 });
}
