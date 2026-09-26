// 17.46 – 30.5  Selective routing
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, mulberry32, prog, lerp, E, sceneTitle, gsap } from '../lib.js';
import { roundRect, funnel } from '../shapes.js';

const CORE = [540, 470];
const DASH = [540, 1340];

export default function s4() {
  sceneTitle('01', 'Selective Routing', 17.55, 30.35);
  morph(17.5, roundRect(DASH[0], DASH[1], 920, 440, 56), 1.0, 'expo.inOut');
  heroColor(17.5, '#22d3ee', '#38bdf8', '#a78bfa', 0.8);
  bgTo(17.4, '#0c1a4a', '#075985', '#312e81', 0.5, 1.4);

  // AI core
  const core = el('div', 'abs');
  core.style.cssText = 'width:180px;height:180px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:4;background:radial-gradient(circle at 35% 30%,#a5f3fc,#0891b2 45%,#1e1b4b 100%);box-shadow:0 0 80px rgba(34,211,238,.75), inset 0 3px 0 rgba(255,255,255,.5)';
  core.innerHTML = `<span class="ico" style="width:90px;height:90px;color:#fff">${icon('cpu', 1.7)}</span>`;
  place(core, ...CORE);
  pop(core, 18.0, { ease: 'back.out(2)' });
  const coreRings = [0, 1].map(() => {
    const r = el('div', 'abs');
    r.style.cssText = 'width:180px;height:180px;border-radius:50%;border:3px solid rgba(103,232,249,.8)';
    place(r, ...CORE, { opacity: 0 });
    return r;
  });
  drive((t) => coreRings.forEach((r, i) => {
    const on = t > 18.2 && t < 30.3;
    const p = ((t * 0.7 + i * 0.5) % 1);
    r.style.opacity = on ? ((1 - p) * 0.8).toFixed(3) : '0';
    r.style.transform = `translate(${CORE[0]}px,${CORE[1]}px) translate(-50%,-50%) scale(${(1 + p * 1.2).toFixed(3)})`;
  }));
  const coreLbl = el('div', 'abs', null, 'AI agent');
  coreLbl.style.cssText = 'font:600 30px var(--mono);color:var(--muted)';
  place(coreLbl, CORE[0], CORE[1] + 130);
  pop(coreLbl, 18.3);

  // Dashboard
  const dash = el('div', 'abs glass');
  dash.style.cssText += 'width:880px;height:400px;border-radius:46px;z-index:1';
  dash.innerHTML = `<div style="display:flex;align-items:center;gap:20px;padding:30px 36px">
    <span class="ico bell" style="width:54px;height:54px;color:#fff;transform-origin:50% 10%">${icon('bell', 2)}</span>
    <span style="font:600 42px var(--head);flex:1">Your dashboard</span>
    <span class="badge dbadge" style="height:78px;min-width:78px;font-size:36px">0</span></div>`;
  place(dash, ...DASH);
  pop(dash, 18.35, { dur: 0.9, ease: 'expo.out', scale: 0.8 });
  const bell = dash.querySelector('.bell'), dbadge = dash.querySelector('.dbadge');

  // Phase A: bombard
  const rnd = mulberry32(7);
  const NA = 42;
  const A = [];
  for (let i = 0; i < NA; i++) {
    const c = el('div', 'abs glass-lite');
    c.style.cssText += 'width:300px;height:74px;display:none;align-items:center;gap:14px;padding:0 18px;z-index:2;font:500 26px var(--mono)';
    c.innerHTML = `<span class="ico" style="width:32px;height:32px;color:#67e8f9;flex:none">${icon('bell', 2.2)}</span><span style="flex:1">Action #${1040 + i}</span><span class="ico" style="width:28px;height:28px;color:#34d399">${icon('check', 3)}</span>`;
    A.push({ e: c, te: 19.35 + 3.7 * Math.pow(i / NA, 0.85), x: 170 + rnd() * 740, y: 1250 + rnd() * 260, rot: (rnd() - 0.5) * 34, bx: rnd() - 0.5, by: rnd() * 0.6 + 0.2 });
  }
  let arrivedA = 0;
  drive((t) => {
    arrivedA = 0;
    for (const c of A) {
      const p = E.outCubic(prog(t, c.te, c.te + 0.65));
      const b = E.inCubic(prog(t, 23.62, 24.3));
      if (t < c.te || b >= 1) { c.e.style.display = 'none'; continue; }
      if (p >= 1) arrivedA++;
      c.e.style.display = 'flex';
      const x = lerp(CORE[0], c.x, p) + Math.sin(p * Math.PI) * c.bx * 300 + c.bx * 1400 * b;
      const y = lerp(CORE[1], c.y, p) - Math.sin(p * Math.PI) * 40 + c.by * 1200 * b;
      const s = lerp(0.2, 1, p);
      c.e.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) rotate(${(c.rot * p + b * c.bx * 180).toFixed(1)}deg) scale(${s.toFixed(3)})`;
      c.e.style.opacity = (Math.min(1, p * 4) * (1 - b)).toFixed(3);
    }
  });
  // bell shake
  drive((t) => {
    const k = Math.min(prog(t, 19.5, 20.5), 1 - prog(t, 23.4, 23.8));
    const calm = prog(t, 28.5, 28.9);
    bell.style.rotate = `${(Math.sin(t * 38) * 22 * k).toFixed(1)}deg`;
    bell.style.color = calm > 0 ? '#34d399' : '#fff';
  });

  // Phase B: filtered
  const NB = 24, AMBER = { 4: 0, 11: 1, 18: 2 };
  const B = [];
  for (let i = 0; i < NB; i++) {
    const amber = i in AMBER;
    const c = el('div', 'abs glass-lite');
    const col = amber ? '#fbbf24' : '#34d399';
    const pct = amber ? [41, 37, 52][AMBER[i]] : 90 + Math.floor(rnd() * 9);
    c.style.cssText += `width:${amber ? 700 : 300}px;height:${amber ? 80 : 74}px;display:none;align-items:center;gap:16px;padding:0 22px;z-index:${amber ? 3 : 2};font:500 26px var(--mono);border-color:${col}88`;
    if (amber) {
      c.style.boxShadow = '0 0 40px rgba(251,191,36,.35)';
      c.innerHTML = `<span class="ico" style="width:36px;height:36px;color:${col};flex:none">${icon('alert', 2.2)}</span><span style="flex:1">Prediction #${2200 + i}</span><span style="color:${col};font-weight:700">${pct}% · review</span>`;
    } else {
      c.innerHTML = `<span class="ico" style="width:30px;height:30px;color:${col};flex:none">${icon('circleCheck', 2.2)}</span><span style="flex:1">#${2200 + i}</span><span style="color:${col};font-weight:700">${pct}%</span>`;
    }
    B.push({ e: c, te: 24.05 + i * 0.172, amber, slot: AMBER[i], side: i % 2 ? 1 : -1 });
  }
  let arrivedB = 0;
  drive((t) => {
    arrivedB = 0;
    const exitB = E.inCubic(prog(t, 30.15, 30.7));
    for (const c of B) {
      const u = t - c.te;
      if (u < 0 || exitB >= 1) { c.e.style.display = 'none'; continue; }
      c.e.style.display = 'flex';
      let x, y, s, o = 1;
      const p1 = E.inOutCubic(prog(u, 0, 0.55));
      x = CORE[0]; y = lerp(CORE[1], 700, p1); s = lerp(0.2, 0.62, p1);
      if (!c.amber) {
        const p2 = E.inOutCubic(prog(u, 0.5, 1.25));
        x = lerp(x, 540 + c.side * 400, p2); y = lerp(y, 800, p2) - Math.sin(p2 * Math.PI) * 60;
        s = lerp(s, 0.45, p2); o = 1 - prog(u, 0.95, 1.25);
        if (u > 1.25) { c.e.style.display = 'none'; continue; }
      } else {
        const p2 = E.inOutCubic(prog(u, 0.5, 1.0));
        y = lerp(y, 1060, p2); s = lerp(s, 0.4, p2);
        const p3 = E.outBack(prog(u, 1.0, 1.55));
        y = lerp(y, 1262 + c.slot * 92, p3); s = lerp(s, 1, p3);
        if (u >= 1.55) arrivedB++;
      }
      c.e.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) scale(${s.toFixed(3)})`;
      c.e.style.opacity = (Math.min(1, u * 5) * o * (1 - exitB)).toFixed(3);
    }
    // badge
    if (t < 23.62) dbadge.textContent = arrivedA * 3 > 99 ? '99+' : String(arrivedA * 3);
    else dbadge.textContent = String(arrivedB);
  });
  tl.to(dbadge, { background: 'radial-gradient(circle at 35% 30%, #fde68a, #d97706 70%)', boxShadow: '0 0 30px rgba(251,191,36,.6)', duration: 0.4 }, 23.7);
  tl.to(dbadge, { background: 'radial-gradient(circle at 35% 30%, #a7f3d0, #059669 70%)', boxShadow: '0 0 40px rgba(52,211,153,.8)', duration: 0.5 }, 28.55);

  // funnel
  morph(23.62, funnel(540, 640, 800, 1010, 170, 1120), 0.9, 'expo.inOut');
  heroColor(23.62, '#67e8f9', '#a78bfa', '#fbbf24', 0.8);

  // auto-resolved chips
  const autos = [-1, 1].map((side, k) => {
    const c = el('div', 'abs chip glass', null, `<span class="ico" style="color:#34d399">${icon('circleCheck')}</span><span>Auto</span><span class="n" style="font-family:var(--mono);color:#34d399">0</span>`);
    place(c, 540 + side * 360, 900);
    pop(c, 24.3 + k * 0.1);
    return c;
  });
  drive((t) => {
    const n = B.filter((c) => !c.amber && t - c.te > 1.1).length;
    autos[0].querySelector('.n').textContent = String(Math.ceil(n / 2) + 1280);
    autos[1].querySelector('.n').textContent = String(Math.floor(n / 2) + 964);
  });

  const thr = el('div', 'abs chip', null, `<span style="font-family:var(--mono)">conf &lt; 60%</span><span class="ico" style="color:#fbbf24">${icon('user')}</span>`);
  thr.style.cssText += 'background:rgba(251,191,36,.14);border:1.5px solid rgba(251,191,36,.6);color:#fde68a;font-size:30px';
  place(thr, 820, 1060);
  pop(thr, 26.5);

  // cured
  tl.to(dash, { boxShadow: '0 0 90px rgba(52,211,153,.45), inset 0 1.5px 0 rgba(255,255,255,.28)', borderColor: 'rgba(52,211,153,.7)', duration: 0.6 }, 28.55);
  heroColor(28.55, '#34d399', '#22d3ee', '#a78bfa', 0.8);
  bgTo(28.5, '#06243a', '#0f766e', '#1e3a8a', 0.35, 1.2);

  out([core, coreLbl, dash, thr, ...autos], 30.2, { dur: 0.55, stagger: 0.03, blur: 20 });
}
