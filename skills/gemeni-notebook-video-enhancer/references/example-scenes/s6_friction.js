// 49.88 – 67.4  Intentional friction
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, mulberry32, prog, lerp, E, env, sceneTitle, click, cursorHide, gsap } from '../lib.js';
import { circle, eye, road, roadY, roundRect, star4 } from '../shapes.js';

const ROAD_Y = 1250, BUMPS = [320, 560, 800];

export default function s6() {
  sceneTitle('03', 'Intentional Friction', 50.0, 67.2);
  morph(49.8, circle(540, 900, 280), 1.0, 'expo.inOut');
  heroColor(49.9, '#22d3ee', '#818cf8', '#34d399', 0.8);
  bgTo(49.8, '#0b2447', '#0e7490', '#4338ca', 0.6, 1.4);

  // Auto-approve orb
  const orb = el('div', 'abs');
  orb.style.cssText = 'width:500px;height:500px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;z-index:3;overflow:hidden';
  orb.innerHTML = `<div class="g" style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 32% 28%,#a5f3fc 0%,#22d3ee 22%,#6366f1 60%,#1e1b4b 100%)"></div>
    <div class="r" style="position:absolute;inset:0;border-radius:50%;opacity:0;background:radial-gradient(circle at 32% 28%,#fecdd3 0%,#fb7185 22%,#be123c 60%,#3b0718 100%)"></div>
    <div class="sheen" style="position:absolute;inset:-20%;background:conic-gradient(from 0deg,transparent 0 70%,rgba(255,255,255,.35) 80%,transparent 90%)"></div>
    <div style="position:absolute;inset:0;border-radius:50%;box-shadow:inset 0 -30px 80px rgba(0,0,0,.45), inset 0 8px 20px rgba(255,255,255,.4)"></div>
    <div class="lbl" style="position:relative;font:700 64px/1.02 var(--head);letter-spacing:-.02em;text-shadow:0 4px 20px rgba(0,0,0,.4)">Auto-<br>Approve<br>All</div>`;
  place(orb, 540, 900);
  pop(orb, 50.3, { dur: 1.0, ease: 'elastic.out(1,0.6)', scale: 0.3 });
  const sheen = orb.querySelector('.sheen');
  drive((t) => (sheen.style.transform = `rotate(${(t * 90) % 360}deg)`));
  tl.to(orb.querySelector('.r'), { opacity: 1, duration: 0.8 }, 54.5);
  tl.to(orb, { boxShadow: '0 0 120px rgba(251,59,94,.7)', duration: 0.8 }, 54.5);
  gsap.set(orb, { boxShadow: '0 0 110px rgba(34,211,238,.55)' });

  // seamless stream of items flying through
  const rnd = mulberry32(5);
  const NI = 18;
  const items = [];
  for (let i = 0; i < NI; i++) {
    const it = el('div', 'abs glass-lite');
    const red = i % 4 === 1;
    it.style.cssText += 'width:110px;height:110px;border-radius:26px;display:flex;align-items:center;justify-content:center;z-index:2';
    it.innerHTML = `<span class="ico" style="width:54px;height:54px;color:#67e8f9">${icon('file', 1.8)}</span>`;
    items.push({ e: it, off: i / NI, y: 900 + (rnd() - 0.5) * 360, red, ico: it.querySelector('.ico') });
  }
  drive((t) => {
    const vis = env(t, 51.9, 56.6, 0.4, 0.5);
    const redOn = t > 54.6;
    for (const it of items) {
      if (vis <= 0) { it.e.style.display = 'none'; continue; }
      it.e.style.display = 'flex';
      const ph = (t * 0.55 + it.off) % 1;
      const x = lerp(-120, 1200, ph);
      const y = lerp(it.y, 900, Math.exp(-Math.pow((x - 540) / 260, 2)));
      it.e.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) scale(${(0.75 + 0.25 * Math.sin(ph * Math.PI)).toFixed(3)})`;
      it.e.style.opacity = (vis * Math.sin(ph * Math.PI) ** 0.5).toFixed(3);
      it.ico.style.color = redOn && it.red ? '#fb3b5e' : '#67e8f9';
      it.e.style.borderColor = redOn && it.red ? 'rgba(251,59,94,.8)' : '';
    }
  });
  // speed lines
  const speed = el('div', 'abs', null, `<svg width="1080" height="600" viewBox="0 0 1080 600">${Array.from({ length: 14 }, (_, i) => `<line x1="0" x2="${200 + (i * 97) % 300}" y1="${30 + i * 40}" y2="${30 + i * 40}" stroke="rgba(165,243,252,.35)" stroke-width="3" stroke-linecap="round"/>`).join('')}</svg>`);
  const sl = [...speed.querySelectorAll('line')];
  place(speed, 540, 900, { opacity: 0 });
  speed.style.zIndex = 1;
  drive((t) => {
    speed.style.opacity = (env(t, 52.0, 56.4, 0.4, 0.4) * 0.9).toFixed(3);
    sl.forEach((l, i) => l.setAttribute('transform', `translate(${(((t * 1400 + i * 211) % 1500) - 300).toFixed(0)} 0)`));
  });

  // complacent eye above
  const eyeW = el('div', 'abs', null, `<svg width="300" height="160" viewBox="-150 -80 300 160"><path d="${eye(0, 0, 260, 110)}" fill="rgba(255,255,255,.08)" stroke="#e0e7ff" stroke-width="7"/><circle class="iris" r="38" fill="#67e8f9"/><circle r="15" fill="#0b0820"/></svg>`);
  place(eyeW, 540, 530);
  pop(eyeW, 52.4);
  const lid = eyeW.querySelector('svg');
  tl.to(lid, { scaleY: 0.08, transformOrigin: '50% 50%', duration: 0.5, ease: 'power2.in' }, 55.1);
  const zz = el('div', 'abs', null, 'z z z');
  zz.style.cssText = 'font:700 44px var(--mono);color:#c7d2fe;letter-spacing:.2em';
  place(zz, 700, 450);
  pop(zz, 55.5);
  heroColor(54.5, '#fb3b5e', '#f97316', '#e11d48', 0.8);
  bgTo(54.4, '#2e0a1f', '#7f1d1d', '#581c87', 0.7, 1.0);

  // speed bumps: orb collapses into a rolling ball, hero becomes a road
  out([eyeW, zz], 56.2, { dur: 0.4 });
  tl.to(orb, { scale: 0.13, x: 80, y: ROAD_Y - 36, duration: 0.9, ease: 'power3.inOut' }, 56.3);
  tl.to(orb.querySelector('.lbl'), { opacity: 0, duration: 0.3 }, 56.3);
  tl.to(orb.querySelector('.r'), { opacity: 0, duration: 0.6 }, 56.4);
  morph(56.3, road(ROAD_Y, BUMPS, 80, 170), 1.0, 'expo.inOut');
  heroColor(56.4, '#fbbf24', '#fb923c', '#facc15', 0.6);
  bgTo(56.3, '#1f1406', '#92400e', '#3730a3', 0.5, 1.2);
  // ball physics: slows at each bump (60–61.3 then continues offscreen)
  const bs = { x: 80 };
  tl.to(bs, { x: 320, duration: 0.9, ease: 'power2.out' }, 57.25);
  tl.to(bs, { x: 560, duration: 0.8, ease: 'power2.inOut' }, 58.15);
  tl.to(bs, { x: 800, duration: 0.8, ease: 'power2.inOut' }, 58.95);
  tl.to(bs, { x: 980, duration: 0.8, ease: 'power2.inOut' }, 59.75);
  const ball = el('div', 'abs');
  ball.style.cssText = 'width:66px;height:66px;border-radius:50%;z-index:4;background:radial-gradient(circle at 32% 28%,#a5f3fc,#22d3ee 30%,#6366f1 80%);box-shadow:0 0 40px rgba(34,211,238,.9)';
  drive((t) => {
    const vis = t >= 57.2 && t < 62.2;
    ball.style.display = vis ? 'block' : 'none';
    if (!vis) return;
    const y = roadY(bs.x, ROAD_Y, BUMPS, 80, 170) - 33;
    ball.style.transform = `translate(${bs.x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%)`;
    ball.style.opacity = (1 - prog(t, 61.8, 62.2)).toFixed(3);
  });
  tl.to(orb, { opacity: 0, duration: 0.05 }, 57.2);
  const bumpLbls = BUMPS.map((b, i) => {
    const l = el('div', 'abs ico', null, icon('hand', 2));
    l.style.cssText += 'width:64px;height:64px;color:#fbbf24;filter:drop-shadow(0 0 14px #fbbf24)';
    place(l, b, ROAD_Y - 150);
    pop(l, 57.0 + i * 0.12);
    return l;
  });

  // override modal
  const modal = el('div', 'abs glass');
  modal.style.cssText += 'width:860px;padding:44px 48px;border-radius:48px;z-index:6';
  const OPTS = ['Contradicting evidence', 'Patient preference', 'Data quality issue'];
  modal.innerHTML = `<div style="display:flex;align-items:center;gap:20px;font:700 50px var(--head);letter-spacing:-.01em"><span class="ico" style="width:60px;height:60px;color:#fbbf24">${icon('shieldAlert', 2)}</span>Override AI decision</div>
    <div style="font:500 32px var(--body);color:var(--muted);margin:14px 0 30px">Select a reason to continue</div>
    <div class="dd" style="position:relative;height:104px;border-radius:26px;background:rgba(0,0,0,.28);border:2px solid rgba(255,255,255,.28);display:flex;align-items:center;padding:0 30px;font:500 36px var(--body)">
      <span class="val" style="flex:1;color:var(--muted)">Choose reason…</span><span class="ico" style="width:44px;height:44px">${icon('chevron')}</span></div>
    <div class="opts" style="margin-top:14px;border-radius:26px;overflow:hidden;background:rgba(10,8,30,.7);border:1.5px solid rgba(255,255,255,.18)">
      ${OPTS.map((o, i) => `<div class="op" style="height:92px;display:flex;align-items:center;padding:0 30px;font:500 34px var(--body);border-top:${i ? '1px solid rgba(255,255,255,.1)' : 'none'}">${o}</div>`).join('')}</div>
    <div class="sub" style="margin-top:30px;height:110px;border-radius:999px;display:flex;align-items:center;justify-content:center;font:700 40px var(--head);background:rgba(255,255,255,.1);color:rgba(255,255,255,.4)">Submit override</div>`;
  place(modal, 540, 800, { y: 900 });
  const opts = modal.querySelector('.opts'), val = modal.querySelector('.val'), sub = modal.querySelector('.sub'), op0 = modal.querySelectorAll('.op')[0];
  gsap.set(opts, { opacity: 0, height: 0 });
  pop(modal, 58.7, { dur: 0.8, ease: 'expo.out', scale: 0.85 });
  tl.to(modal, { y: 800, duration: 0.8, ease: 'expo.out' }, 58.7);
  // modal centre 800; dd at approx y=800-? – measured positions below
  click(820, 700, 59.95, 60.0, 0.6);
  tl.to(opts, { opacity: 1, height: 280, duration: 0.35, ease: 'power3.out' }, 60.1);
  tl.to(op0, { backgroundColor: 'rgba(103,232,249,.22)', duration: 0.15 }, 60.45);
  click(420, 772, 60.65, 60.7, 0.35);
  tl.to(val, { color: '#fff', duration: 0.1 }, 60.8);
  drive((t) => (val.textContent = t >= 60.8 ? OPTS[0] : 'Choose reason…'));
  tl.to(opts, { opacity: 0, height: 0, duration: 0.3, ease: 'power3.in' }, 60.85);
  tl.to(sub, { background: 'linear-gradient(120deg,#f59e0b,#f97316)', color: '#fff', boxShadow: '0 20px 50px -10px rgba(249,115,22,.8)', duration: 0.3 }, 61.0);
  click(560, 945, 61.35, 61.4, 0.45);
  cursorHide(61.8);
  out(modal, 61.85, { dur: 0.45, scale: 0.8, blur: 20 });
  out(bumpLbls, 61.8, { dur: 0.4 });

  // autopilot toggle
  morph(61.9, roundRect(540, 880, 420, 200, 100), 0.8, 'expo.inOut');
  heroColor(61.9, '#34d399', '#22d3ee', '#a78bfa', 0.5);
  const ap = el('div', 'abs');
  ap.style.cssText = 'text-align:center';
  ap.innerHTML = `<div style="font:700 48px var(--mono);letter-spacing:.3em;margin-bottom:40px;color:#e0e7ff">AUTOPILOT</div>
    <div class="sw" style="position:relative;width:380px;height:170px;border-radius:85px;background:#10b981;box-shadow:0 0 60px rgba(16,185,129,.7), inset 0 4px 12px rgba(0,0,0,.3)">
      <div class="kn" style="position:absolute;top:15px;left:15px;width:140px;height:140px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,#d1d5db);box-shadow:0 10px 30px rgba(0,0,0,.5)"></div>
      <span class="on" style="position:absolute;left:44px;top:50%;transform:translateY(-50%);font:800 50px var(--head)">ON</span>
      <span class="off" style="position:absolute;right:36px;top:50%;transform:translateY(-50%);font:800 50px var(--head);opacity:0">OFF</span></div>`;
  place(ap, 540, 820);
  const kn = ap.querySelector('.kn'), sw = ap.querySelector('.sw');
  gsap.set(kn, { x: 210 });
  pop(ap, 62.0, { dur: 0.6, ease: 'expo.out', scale: 0.7 });
  tl.to(kn, { x: 0, duration: 0.45, ease: 'back.inOut(2)' }, 62.84);
  tl.to(sw, { background: '#3f3f58', boxShadow: '0 0 0 rgba(0,0,0,0), inset 0 4px 12px rgba(0,0,0,.4)', duration: 0.4 }, 62.9);
  tl.to(ap.querySelector('.on'), { opacity: 0, duration: 0.2 }, 62.84);
  tl.to(ap.querySelector('.off'), { opacity: 1, duration: 0.3 }, 63.05);
  heroColor(62.85, '#94a3b8', '#64748b', '#a78bfa', 0.4);
  bgTo(62.8, '#0f0d24', '#1e293b', '#312e81', 0.3, 0.8);
  tl.to(ap, { y: 560, scale: 0.72, duration: 0.8, ease: 'power3.inOut' }, 64.0);

  // professional judgment activates
  morph(64.2, star4(540, 1120, 400, 90), 1.0, 'expo.inOut');
  heroColor(64.3, '#fde68a', '#f472b6', '#22d3ee', 0.6);
  bgTo(64.3, '#26104f', '#9d174d', '#0e7490', 0.9, 1.0);
  const judge = el('div', 'abs');
  judge.style.cssText = 'width:230px;height:230px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:4;background:radial-gradient(circle at 35% 30%,#fef3c7,#f59e0b 50%,#7c2d12);box-shadow:0 0 100px rgba(251,191,36,.9)';
  judge.innerHTML = `<span class="ico" style="width:130px;height:130px;color:#1c0f02">${icon('brain', 1.8)}</span>`;
  place(judge, 540, 1120);
  pop(judge, 64.4, { ease: 'back.out(2.2)' });
  const rays = el('div', 'abs', null, `<svg width="900" height="900" viewBox="-450 -450 900 900">${Array.from({ length: 16 }, (_, i) => {
    const a = (i / 16) * Math.PI * 2;
    return `<line x1="${Math.cos(a) * 170}" y1="${Math.sin(a) * 170}" x2="${Math.cos(a) * 420}" y2="${Math.sin(a) * 420}" stroke="#fde68a" stroke-width="6" stroke-linecap="round"/>`;
  }).join('')}</svg>`);
  place(rays, 540, 1120, { opacity: 0, scale: 0.4, rotation: 0 });
  rays.style.zIndex = 3;
  tl.to(rays, { opacity: 0.8, scale: 1, duration: 0.8, ease: 'expo.out' }, 64.5);
  tl.to(rays, { rotation: 30, duration: 2.6, ease: 'none' }, 64.5);
  tl.to(rays, { opacity: 0.25, duration: 0.8 }, 65.4);
  tl.to(judge, { scale: 1.15, duration: 0.25, yoyo: true, repeat: 1, ease: 'power2.out' }, 66.3);
  tl.to(rays, { opacity: 0.9, duration: 0.2, yoyo: true, repeat: 1 }, 66.3);
  const jl = el('div', 'abs chip glass', null, `<span>Professional judgment</span>`);
  place(jl, 540, 1420);
  pop(jl, 65.0);

  out([ap, judge, rays, jl], 67.15, { dur: 0.5, stagger: 0.03, blur: 20 });
}
