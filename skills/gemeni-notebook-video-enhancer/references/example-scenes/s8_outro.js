// 82.44 – 95.06  "The best AI systems don't try to automate you away…  strategic decision-making partner."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, mulberry32, prog, lerp, E, env, gsap, DURATION } from '../lib.js';
import { human, infinity } from '../shapes.js';
import { PATTERNS } from './s3_four.js';

const HC = [540, 900];

export default function s8() {
  morph(82.4, human(HC[0], HC[1], 1.1), 1.1, 'expo.inOut');
  heroColor(82.4, '#67e8f9', '#a78bfa', '#f472b6', 0.8);
  bgTo(82.3, '#170b4a', '#0e7490', '#86198f', 0.6, 1.4);

  const lift = { y: 0 };
  tl.to(lift, { y: -200, duration: 1.3, ease: 'power3.inOut' }, 88.1);
  drive(() => gsap.set('#heroG', { y: lift.y }));

  // AI orb
  const orb = el('div', 'abs');
  orb.style.cssText = 'width:170px;height:170px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:4;background:radial-gradient(circle at 35% 30%,#f5d0fe,#c026d3 45%,#3b0764);box-shadow:0 0 90px rgba(217,70,239,.8), inset 0 3px 0 rgba(255,255,255,.5)';
  orb.innerHTML = `<span class="ico" style="width:90px;height:90px;color:#fff">${icon('bot', 1.7)}</span>`;
  place(orb, 880, 520);
  pop(orb, 83.4, { ease: 'back.out(2)' });
  tl.to(orb, { x: 820, y: 700, scale: 1.1, duration: 1.0, ease: 'expo.inOut' }, 90.0);

  // beam from orb toward human ("automate you away") that fails
  const beam = el('div', 'abs');
  beam.style.cssText = 'width:420px;height:10px;border-radius:10px;background:linear-gradient(90deg,rgba(217,70,239,0),#f0abfc);box-shadow:0 0 30px #e879f9;transform-origin:100% 50%;z-index:2';
  gsap.set(beam, { x: 820 - 420, y: 560, rotation: -20, scaleX: 0, opacity: 0, transformOrigin: '100% 50%' });
  tl.to(beam, { scaleX: 1, opacity: 1, duration: 0.4, ease: 'power2.out' }, 84.2);
  tl.to(beam, { opacity: 0, scaleX: 0.2, duration: 0.4 }, 85.1);

  // dissolve particles (sampled inside the silhouette)
  const rnd = mulberry32(3);
  const dots = [];
  while (dots.length < 110) {
    const x = HC[0] + (rnd() - 0.5) * 660, y = HC[1] - 300 + rnd() * 560;
    const inHead = Math.hypot(x - HC[0], y - (HC[1] - 209)) < 115;
    const inBody = y > HC[1] - 44 && Math.abs(x - HC[0]) < 330 * Math.min(1, (y - (HC[1] - 44)) / 110 + 0.35);
    if (!inHead && !inBody) continue;
    const d = el('div', 'abs');
    const s = 6 + rnd() * 10;
    d.style.cssText = `width:${s}px;height:${s}px;border-radius:50%;background:${rnd() > 0.5 ? '#a5f3fc' : '#f0abfc'};box-shadow:0 0 12px currentColor;color:#e9d5ff;display:none`;
    dots.push({ e: d, x, y, a: -Math.PI / 4 + (rnd() - 0.5) * 1.6, r: 150 + rnd() * 450 });
  }
  drive((t) => {
    const o = E.inOutCubic(prog(t, 84.25, 84.95)) * (1 - E.inOutCubic(prog(t, 85.0, 85.6)));
    const vis = env(t, 84.2, 85.7, 0.15, 0.15);
    for (const d of dots) {
      if (vis <= 0) { d.e.style.display = 'none'; continue; }
      d.e.style.display = 'block';
      const x = d.x + Math.cos(d.a) * d.r * o, y = d.y + Math.sin(d.a) * d.r * o;
      d.e.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px)`;
      d.e.style.opacity = (vis * (0.3 + 0.7 * o)).toFixed(3);
    }
  });
  tl.to('#heroG', { opacity: 0.2, duration: 0.6, ease: 'power2.in' }, 84.3);
  tl.to('#heroG', { opacity: 1, duration: 0.5, ease: 'power2.out' }, 85.05);
  const no = el('div', 'abs');
  no.style.cssText = 'width:150px;height:150px;border-radius:50%;border:10px solid #fb3b5e;box-shadow:0 0 40px #fb3b5e;z-index:5';
  no.innerHTML = '<i style="position:absolute;left:50%;top:50%;width:150px;height:10px;background:#fb3b5e;transform:translate(-50%,-50%) rotate(-45deg);display:block"></i>';
  place(no, 690, 560);
  pop(no, 84.3, { ease: 'back.out(3)' });
  out(no, 85.5, { dur: 0.4 });

  // orbiting pattern icons
  const orbit = PATTERNS.map(([, , ic, col], i) => {
    const o = el('div', 'abs glass');
    o.style.cssText += `width:130px;height:130px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 40px -6px ${col}, inset 0 1.5px 0 rgba(255,255,255,.3);z-index:3`;
    o.innerHTML = `<span class="ico" style="width:64px;height:64px;color:${col}">${icon(ic, 2)}</span>`;
    return { e: o, i };
  });
  drive((t) => {
    const vis = prog(t, 85.9, 86.9);
    const gather = E.inOutCubic(prog(t, 90.1, 90.9));
    for (const o of orbit) {
      const appear = E.outBack(prog(t, 85.9 + o.i * 0.18, 86.6 + o.i * 0.18));
      if (appear <= 0 || gather >= 1) { o.e.style.display = 'none'; continue; }
      o.e.style.display = 'flex';
      const a = t * 1.1 + (o.i * Math.PI) / 2;
      const depth = Math.sin(a);
      let x = HC[0] + Math.cos(a) * 420 * appear, y = HC[1] - 60 + depth * 150 + lift.y;
      x = lerp(x, 540, gather); y = lerp(y, 700, gather);
      const s = (0.85 + 0.25 * depth) * appear * (1 - gather * 0.7);
      o.e.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) scale(${Math.max(0, s).toFixed(3)})`;
      o.e.style.zIndex = depth > 0 ? 6 : 1;
      o.e.style.opacity = (Math.min(1, vis * 2) * (1 - gather)).toFixed(3);
    }
  });

  // elevate: light pillar + "manual operator" left behind
  const pillar = el('div', 'abs');
  pillar.style.cssText = 'width:520px;height:1100px;background:radial-gradient(ellipse 50% 60% at 50% 100%,rgba(165,243,252,.45),transparent 70%);filter:blur(10px);z-index:0';
  place(pillar, 540, 1200, { opacity: 0 });
  tl.to(pillar, { opacity: 1, duration: 0.8 }, 88.1);
  tl.to(pillar, { opacity: 0, duration: 0.8 }, 90.0);
  const op = el('div', 'abs chip glass', null, `<span class="ico" style="color:#94a3b8">${icon('wrench')}</span><span style="color:#cbd5e1">Manual operator</span>`);
  place(op, 540, 1330);
  pop(op, 89.0);
  tl.to(op, { y: 1480, opacity: 0, filter: 'blur(12px)', scale: 0.8, duration: 0.7, ease: 'power2.in' }, 89.9);

  // partner: human ∞ AI
  morph(89.95, infinity(540, 900, 840, 330), 1.1, 'expo.inOut');
  heroColor(90.0, '#67e8f9', '#c084fc', '#f472b6', 0.8);
  bgTo(90.0, '#1a0b52', '#0e7490', '#a21caf', 0.9, 1.4);
  const hu = el('div', 'abs');
  hu.style.cssText = 'width:170px;height:170px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:4;background:radial-gradient(circle at 35% 30%,#cffafe,#0891b2 45%,#082f49);box-shadow:0 0 90px rgba(34,211,238,.8), inset 0 3px 0 rgba(255,255,255,.5)';
  hu.innerHTML = `<span class="ico" style="width:90px;height:90px;color:#fff">${icon('user', 1.7)}</span>`;
  place(hu, 260, 700);
  pop(hu, 90.3, { ease: 'back.out(2)', scale: 0.2 });

  // particles flowing around the infinity loop
  const hero = document.getElementById('hero');
  const flow = Array.from({ length: 28 }, (_, i) => {
    const d = el('div', 'abs');
    d.style.cssText = `width:${i % 3 ? 10 : 16}px;height:${i % 3 ? 10 : 16}px;border-radius:50%;background:#fff;box-shadow:0 0 18px ${i % 2 ? '#67e8f9' : '#f0abfc'};display:none;z-index:3`;
    return d;
  });
  drive((t) => {
    const vis = prog(t, 90.9, 91.4);
    if (vis <= 0) { flow.forEach((d) => (d.style.display = 'none')); return; }
    const L = hero.getTotalLength();
    flow.forEach((d, i) => {
      const p = hero.getPointAtLength(((t * 0.18 + i / flow.length) % 1) * L);
      d.style.display = 'block';
      d.style.transform = `translate(${p.x.toFixed(1)}px,${(p.y + lift.y).toFixed(1)}px) translate(-50%,-50%)`;
      d.style.opacity = vis.toFixed(3);
    });
  });

  // end card
  const end = el('div', 'abs');
  end.style.cssText = 'text-align:center;white-space:nowrap';
  end.innerHTML = `<div class="grad-text" style="font:700 150px/1 var(--head);letter-spacing:-.04em">Human + AI</div>
    <div style="font:600 46px var(--head);margin-top:22px;color:#ede9fe">strategic decision-making partners</div>
    <div style="font:500 28px var(--mono);margin-top:46px;color:var(--muted);letter-spacing:.08em">ROUTING · DECOMPOSITION · FRICTION · TRUST</div>`;
  place(end, 540, 1180, { opacity: 0, y: 1260, filter: 'blur(24px)' });
  tl.to(end, { opacity: 1, y: 1180, filter: 'blur(0px)', duration: 1.2, ease: 'expo.out' }, 92.0);
  const words = end.children;
  gsap.set(words, { opacity: 0, y: 30 });
  tl.to(words, { opacity: 1, y: 0, duration: 0.9, stagger: 0.25, ease: 'expo.out' }, 92.05);
}
