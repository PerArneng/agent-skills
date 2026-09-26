// 6.48 – 12.2  "But forcing users to babysit algorithms all day causes severe cognitive fatigue."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, mulberry32, prog, lerp, E, hash, gsap } from '../lib.js';
import { triangle } from '../shapes.js';

export const TILES = [[320, 730], [760, 730], [320, 1170], [760, 1170]];

export default function s2() {
  morph(6.45, triangle(540, 800, 660, 70), 1.0, 'expo.inOut');
  heroColor(6.5, '#fbbf24', '#fb923c', '#f43f5e', 0.8);
  bgTo(6.4, '#2a1406', '#8a3b0a', '#6b1d5c', 0.8, 1.2);

  // counter badge
  const badge = el('div', 'abs badge', null, '0');
  place(badge, 790, 520);
  pop(badge, 7.0, { ease: 'back.out(3)' });

  // swarm of alerts
  const N = 72, rnd = mulberry32(42);
  const cards = [];
  for (let i = 0; i < N; i++) {
    const c = el('div', 'abs glass-lite');
    c.style.cssText += 'width:230px;height:76px;display:flex;align-items:center;gap:14px;padding:0 18px;display:none';
    const w1 = 60 + rnd() * 70, w2 = 40 + rnd() * 60;
    c.innerHTML = `<span class="ico" style="width:36px;height:36px;color:#fbbf24;flex:none">${icon('alert', 2.4)}</span>
      <span style="display:flex;flex-direction:column;gap:9px"><i style="display:block;height:10px;width:${w1}px;border-radius:5px;background:rgba(255,255,255,.75)"></i><i style="display:block;height:8px;width:${w2}px;border-radius:4px;background:rgba(255,255,255,.35)"></i></span>`;
    const a = rnd() * Math.PI * 2, rr = 0.35 + rnd() * 0.65;
    cards.push({
      e: c, ts: 6.9 + 4.3 * Math.pow(i / N, 0.8),
      tx: 540 + Math.cos(a) * 420 * rr, ty: 900 + Math.sin(a) * 640 * rr,
      rot: (rnd() - 0.5) * 30, ph: rnd() * 10, tile: TILES[i % 4], cd: rnd() * 0.35,
    });
  }
  drive((t) => {
    let spawned = 0;
    for (const c of cards) {
      const p = E.outExpo(prog(t, c.ts, c.ts + 0.9));
      const cv = E.inOutCubic(prog(t, 12.25 + c.cd, 13.25 + c.cd));
      if (t < c.ts || cv >= 1) { c.e.style.display = 'none'; continue; }
      spawned++;
      c.e.style.display = 'flex';
      const jit = prog(t, 10.4, 11.9) * (1 - cv);
      const f = Math.floor(t * 30);
      const jx = (hash(f + c.ph * 100) - 0.5) * 16 * jit, jy = (hash(f + c.ph * 50 + 3) - 0.5) * 16 * jit;
      let x = lerp(540, c.tx, p) + Math.sin(t * 1.3 + c.ph) * 10 + jx;
      let y = lerp(800, c.ty, p) + Math.cos(t * 1.1 + c.ph) * 10 + jy;
      x = lerp(x, c.tile[0], cv); y = lerp(y, c.tile[1], cv);
      const s = lerp(0.3, 1, p) * lerp(1, 0.25, cv);
      c.e.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%,-50%) rotate(${(c.rot * p * (1 - cv)).toFixed(1)}deg) scale(${s.toFixed(3)})`;
      c.e.style.opacity = (Math.min(1, p * 3) * (1 - cv)).toFixed(3);
      c.e.style.filter = jit > 0.05 ? `blur(${(jit * 1.5).toFixed(2)}px)` : '';
    }
    badge.textContent = t < 12.25 ? String(Math.round(spawned * 3.4)) : badge.textContent;
  });
  out(badge, 12.2, { dur: 0.5 });

  // the human babysitter
  const av = el('div', 'abs glass');
  av.style.cssText += 'width:210px;height:210px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:5';
  av.innerHTML = `<span class="ico" style="width:110px;height:110px;color:#e9e5ff">${icon('user', 1.6)}</span>`;
  place(av, 380, 1400);
  pop(av, 7.5);
  const ring = el('div', 'abs', null, `<svg width="270" height="270" viewBox="0 0 270 270"><circle cx="135" cy="135" r="125" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="8"/><circle class="arc" cx="135" cy="135" r="125" fill="none" stroke="#fbbf24" stroke-width="8" stroke-linecap="round" transform="rotate(-90 135 135)"/></svg>`);
  ring.style.zIndex = 5;
  place(ring, 380, 1400, { opacity: 0 });
  tl.to(ring, { opacity: 1, duration: 0.3 }, 8.0);
  const arc = ring.querySelector('.arc');
  gsap.set(arc, { drawSVG: '0%' });
  tl.to(arc, { drawSVG: '100%', duration: 2.2, ease: 'sine.inOut' }, 8.3);
  const clock = el('div', 'abs chip glass', null, `<span class="ico" style="color:#fbbf24">${icon('clock')}</span><span>All day</span>`);
  clock.style.zIndex = 6;
  place(clock, 380, 1230);
  pop(clock, 9.3);

  // attention battery draining
  const bat = el('div', 'abs');
  bat.style.cssText = 'z-index:5;width:320px';
  bat.innerHTML = `<div style="font:600 32px var(--head);margin-bottom:14px;display:flex;justify-content:space-between"><span>Focus</span><span class="pct" style="font-family:var(--mono)">100%</span></div>
    <div class="glass" style="height:74px;border-radius:22px;padding:10px;"><div class="fill" style="height:100%;border-radius:14px;background:#34d399;transform-origin:0 50%;box-shadow:0 0 30px rgba(52,211,153,.6)"></div></div>`;
  place(bat, 740, 1400);
  pop(bat, 7.8);
  const fill = bat.querySelector('.fill'), pct = bat.querySelector('.pct');
  const st = { v: 1 };
  tl.to(st, { v: 0.07, duration: 1.6, ease: 'power2.in' }, 10.3);
  tl.to(fill, { backgroundColor: '#fb3b5e', boxShadow: '0 0 30px rgba(251,59,94,.8)', duration: 1.2 }, 10.6);
  drive(() => { fill.style.transform = `scaleX(${st.v.toFixed(3)})`; pct.textContent = Math.round(st.v * 100) + '%'; });
  tl.to(av, { opacity: 0.45, filter: 'grayscale(1) blur(1px)', duration: 1.2 }, 10.8);
  heroColor(10.6, '#fb3b5e', '#f97316', '#be123c', 1.0);

  out([av, ring, clock, bat], 12.1, { dur: 0.5, stagger: 0.04, blur: 20 });
}
