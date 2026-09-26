// 30.78 – 49.6  Claim decomposition
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, mulberry32, prog, lerp, E, sceneTitle, click, cursorHide, gsap } from '../lib.js';
import { roundRect, pills } from '../shapes.js';

const YS = [640, 830, 1020, 1210];
const FACTS = ['Q3 revenue grew 12%', 'Source: Annual Report p.14', 'Churn fell to 4.1%', 'Market share doubled'];

export default function s5() {
  sceneTitle('02', 'Claim Decomposition', 30.85, 49.4);
  morph(30.7, roundRect(540, 960, 800, 1000, 56), 1.0, 'expo.inOut');
  heroColor(30.8, '#a78bfa', '#818cf8', '#22d3ee', 0.8);
  bgTo(30.7, '#1b0f4f', '#3730a3', '#6d28d9', 0.5, 1.4);

  // document
  const doc = el('div', 'abs');
  doc.style.cssText = 'width:700px;height:880px';
  doc.innerHTML = `<div style="display:flex;align-items:center;gap:16px;font:600 38px var(--head);height:70px">
      <span class="ico" style="width:44px;height:44px;color:#c4b5fd">${icon('sparkles')}</span>AI Summary
      <span style="flex:1"></span><span style="font:500 26px var(--mono);color:var(--muted)">2,431 words</span></div>
    <div class="clip" style="position:relative;height:690px;overflow:hidden;margin-top:20px;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 6%,#000 88%,transparent 100%)"><div class="scroll"></div></div>`;
  place(doc, 540, 900);
  const scroll = doc.querySelector('.scroll');
  const rnd = mulberry32(11);
  const NL = 46, FLAW = [9, 17, 26];
  const lines = [];
  for (let i = 0; i < NL; i++) {
    const l = document.createElement('div');
    const w = i % 7 === 6 ? 30 + rnd() * 30 : 70 + rnd() * 30;
    l.style.cssText = `height:15px;width:${w}%;border-radius:8px;background:rgba(226,222,255,.5);margin-bottom:17px;transform-origin:0 50%`;
    scroll.appendChild(l);
    lines.push({ e: l, a: rnd() * Math.PI * 2, d: 300 + rnd() * 700, r: (rnd() - 0.5) * 120 });
  }
  gsap.set(doc, { opacity: 0 });
  tl.to(doc, { opacity: 1, duration: 0.4 }, 31.4);
  drive((t) => {
    scroll.style.transform = `translateY(${(-E.inOutSine(prog(t, 33.6, 37.6)) * 700).toFixed(1)}px)`;
    lines.forEach((L, i) => {
      const r = E.outCubic(prog(t, 32.3 + i * 0.04, 32.6 + i * 0.04));
      const x = E.inCubic(prog(t, 38.45 + i * 0.012, 39.3 + i * 0.012));
      const dx = Math.cos(L.a) * L.d * x, dy = Math.sin(L.a) * L.d * x;
      L.e.style.transform = `translate(${dx.toFixed(1)}px,${dy.toFixed(1)}px) rotate(${(L.r * x).toFixed(1)}deg) scaleX(${r.toFixed(3)})`;
      L.e.style.opacity = (1 - x).toFixed(3);
    });
  });
  FLAW.forEach((i) => tl.to(lines[i].e, { backgroundColor: '#fb3b5e', boxShadow: '0 0 18px rgba(251,59,94,.9)', duration: 0.25 }, 37.0 + (i % 3) * 0.08));

  // blind accept
  const acc = el('div', 'abs');
  acc.style.cssText = 'padding:26px 60px;border-radius:999px;font:700 40px var(--head);white-space:nowrap;display:flex;gap:16px;align-items:center;background:linear-gradient(120deg,#6366f1,#a855f7);box-shadow:0 20px 50px -10px rgba(139,92,246,.8), inset 0 2px 0 rgba(255,255,255,.35)';
  acc.innerHTML = `<span class="ico" style="width:44px;height:44px">${icon('check', 3)}</span><span class="lbl">Accept all</span>`;
  place(acc, 540, 1390);
  pop(acc, 34.9);
  click(560, 1400, 36.45, 36.6, 0.8);
  tl.to(acc, { scale: 0.92, duration: 0.1, yoyo: true, repeat: 1 }, 36.6);
  tl.to(acc, { background: 'linear-gradient(120deg,#475569,#334155)', boxShadow: '0 0 0 rgba(0,0,0,0)', duration: 0.3 }, 36.75);
  out(acc, 38.35, { dur: 0.4 });
  tl.to(doc, { opacity: 0, duration: 0.5 }, 39.0);

  // decompose into facts
  morph(38.5, pills(540, YS, 880, 150), 1.1, 'expo.inOut');
  heroColor(38.5, '#22d3ee', '#a78bfa', '#f472b6', 0.8);
  const chips = FACTS.map((txt, i) => {
    const c = el('div', 'abs');
    c.style.cssText = 'width:860px;height:130px;border-radius:65px;display:flex;align-items:center;gap:26px;padding:0 26px 0 30px';
    c.innerHTML = `<span style="flex:none;width:70px;height:70px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 32px var(--mono);background:rgba(255,255,255,.1);border:1.5px solid rgba(255,255,255,.25)">${i + 1}</span>
      <span style="flex:1;font:600 40px var(--head);letter-spacing:-.01em;white-space:nowrap" class="txt">${txt}</span>
      <span class="box" style="flex:none;width:78px;height:78px;border-radius:50%;border:3px solid rgba(255,255,255,.45);display:flex;align-items:center;justify-content:center"><span class="ico mk" style="width:44px;height:44px;opacity:0"></span></span>
      <span class="shine" style="position:absolute;inset:0;border-radius:65px;overflow:hidden;pointer-events:none"><i style="position:absolute;top:0;bottom:0;width:180px;left:-200px;background:linear-gradient(100deg,transparent,rgba(255,255,255,.35),transparent);display:block"></i></span>`;
    c.style.position = 'absolute';
    place(c, 540, YS[i]);
    return c;
  });
  pop(chips, 40.3, { stagger: 0.45, dur: 0.8, ease: 'expo.out', scale: 0.7, blur: 16 });
  chips.forEach((c, i) => tl.to(c.querySelector('.shine i'), { x: 1100, duration: 0.8, ease: 'power2.inOut' }, 42.7 + i * 0.12));

  // verify each fact
  const CLICKS = [44.6, 45.4, 46.2, 47.0];
  chips.forEach((c, i) => {
    const tc = CLICKS[i];
    click(868, YS[i], tc - 0.02, tc, i === 0 ? 0.9 : 0.55);
    const ok = i !== 3;
    const col = ok ? '#34d399' : '#fb3b5e';
    const box = c.querySelector('.box'), mk = c.querySelector('.mk');
    mk.innerHTML = icon(ok ? 'check' : 'x', 3.2);
    mk.style.color = '#0b0820';
    tl.to(box, { backgroundColor: col, borderColor: col, boxShadow: `0 0 30px ${col}`, duration: 0.25 }, tc + 0.05);
    tl.to(mk, { opacity: 1, duration: 0.2 }, tc + 0.08);
    tl.to(c, { boxShadow: `0 0 0 3px ${col}, 0 0 50px -6px ${col}`, borderRadius: 65, duration: 0.3 }, tc + 0.05);
    if (!ok) {
      tl.to(c, { x: '+=16', duration: 0.06, yoyo: true, repeat: 5, ease: 'none' }, tc + 0.1);
      tl.to(c.querySelector('.txt'), { color: '#fda4af', textDecoration: 'line-through', duration: 0.2 }, tc + 0.1);
    }
  });
  const tag = el('div', 'abs chip', null, `<span class="ico" style="color:#fb3b5e">${icon('shieldAlert')}</span><span>Unsupported claim caught</span>`);
  tag.style.cssText += 'background:rgba(251,59,94,.15);border:1.5px solid rgba(251,59,94,.7);color:#fecdd3;font-size:30px';
  place(tag, 540, 1340);
  pop(tag, 47.2);
  cursorHide(47.6);

  // "rather than trusting the whole block"
  const ghost = el('div', 'abs');
  ghost.style.cssText = 'padding:24px 56px;border-radius:999px;font:700 38px var(--head);white-space:nowrap;background:rgba(255,255,255,.08);border:1.5px dashed rgba(255,255,255,.35);color:rgba(255,255,255,.55)';
  ghost.innerHTML = `Accept all<i style="position:absolute;left:-4%;right:-4%;top:48%;height:8px;border-radius:4px;background:#fb3b5e;box-shadow:0 0 16px #fb3b5e;transform-origin:0 50%;display:block" class="st"></i>`;
  place(ghost, 540, 1470);
  pop(ghost, 47.9);
  const st = ghost.querySelector('.st');
  gsap.set(st, { scaleX: 0 });
  tl.to(st, { scaleX: 1, duration: 0.4, ease: 'power3.inOut' }, 48.5);

  out([...chips, tag, ghost], 49.35, { dur: 0.55, stagger: 0.04, blur: 20 });
}
