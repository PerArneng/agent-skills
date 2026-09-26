// 46.3–59.2  03 Why-Trail: "Blackbox AI is unacceptable in aviation, so Airflow records a fully auditable causal
// trace, proving exactly which inputs and constraints drove every single recommendation."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, sceneTitle, svgLayer, svgEl, flow, stamp, gsap, prog, E } from '../lib.js';
import { roundRect } from '../shapes.js';

export default function s6() {
  sceneTitle('03', 'Why-Trail', 46.32, 58.95);
  morph(46.1, roundRect(720, 580, 330, 330, 30), 1.1);

  // ---- black box ----
  const box = el('div', 'abs');
  box.style.cssText += 'width:280px;height:280px;border-radius:22px;background:#02080f;border:1.5px solid rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;overflow:hidden;z-index:2';
  box.innerHTML = `<span class="q" style="font:700 150px/1 var(--head);color:rgba(255,255,255,.14)">?</span>`;
  place(box, 720, 580);
  pop(box, 48.55, { scale: 0.6, ease: 'expo.out' });
  const qs = Array.from({ length: 7 }, (_, i) => {
    const q = el('div', 'abs', null, '?');
    q.style.cssText += `font:700 ${26 + (i % 3) * 10}px/1 var(--head);color:rgba(142,164,176,.55)`;
    return q;
  });
  drive((t) => qs.forEach((q, i) => {
    const on = prog(t, 48.8 + i * 0.12, 49.3 + i * 0.12) * (1 - prog(t, 51.4, 51.9));
    if (on <= 0) return (q.style.display = 'none');
    q.style.display = 'block';
    const a = t * 0.5 + (i / 7) * Math.PI * 2;
    q.style.transform = `translate(${(720 + Math.cos(a) * 250).toFixed(1)}px,${(580 + Math.sin(a) * 200).toFixed(1)}px) translate(-50%,-50%)`;
    q.style.opacity = on.toFixed(3);
  }));
  const bl = el('div', 'abs eyebrow', null, 'Black box AI');
  bl.style.color = 'var(--n-300)';
  place(bl, 720, 770, { opacity: 0 });
  tl.to(bl, { opacity: 1, duration: 0.4 }, 48.9);
  const no = el('div', 'abs ico');
  no.style.cssText += 'width:96px;height:96px;color:var(--red);z-index:3;background:#02080f;border-radius:50%';
  no.innerHTML = icon('circle-x', 2);
  place(no, 850, 450);
  stamp(no, 49.9, 0);
  heroColor(49.9, '#ff4d5e', '#ff791a', '#ff4d5e', 0.4);
  tl.to(box, { borderColor: 'rgba(255,77,94,.7)', duration: 0.3 }, 49.95);
  // "so Airflow records…" → the box opens into the trace
  out([box, bl, no], 51.6, { dur: 0.5, scale: 1.3 });
  heroColor(51.6, '#15a2ae', '#6af4f9', '#ffa05c', 0.6);
  morph(51.7, roundRect(700, 590, 1240, 470, 26), 1.0);

  // ---- causal trace: 4 columns ----
  const cols = [
    { h: 'Inputs', ico: 'database', t: 55.55, rows: ['Crew duty · 17:22', 'WX · TS at 18Z', 'Fuel · 16,000 lb', 'MEL 21-01 open'] },
    { h: 'Constraints', ico: 'shield-check', t: 56.15, rows: ['FAR 117 limits', 'ETOPS 120', 'Slot · 14:42Z', 'Curfew · 23:00'] },
    { h: 'Logic', ico: 'git-merge', t: 56.65, rows: ['3 routes compared', 'Risk scored', 'Limits verified'] },
    { h: 'Recommendation', ico: 'route', t: 57.8, rows: [] },
  ];
  const xs = [250, 550, 850, 1150], cy = 600;
  const sv = svgLayer(1);
  const links = [];
  for (let i = 0; i < 3; i++) {
    const d = `M${xs[i] + 128} ${cy} L${xs[i + 1] - 128} ${cy}`;
    const base = svgEl('path', { d, stroke: 'rgba(106,244,249,.4)', 'stroke-width': 2, fill: 'none' }, sv);
    const dash = svgEl('path', { d, stroke: '#6af4f9', 'stroke-width': 4, 'stroke-dasharray': '2 14', 'stroke-linecap': 'round', fill: 'none' }, sv);
    const head = svgEl('path', { d: `M${xs[i + 1] - 140} ${cy - 8} L${xs[i + 1] - 128} ${cy} L${xs[i + 1] - 140} ${cy + 8}`, stroke: '#6af4f9', 'stroke-width': 2.5, fill: 'none' }, sv);
    gsap.set([base, dash], { drawSVG: '0%' });
    gsap.set(head, { opacity: 0 });
    tl.to([base, dash], { drawSVG: '100%', duration: 0.35, ease: 'none' }, 53.5 + i * 0.3);
    tl.to(head, { opacity: 1, duration: 0.1 }, 53.8 + i * 0.3);
    links.push(dash);
  }
  flow(links, 60);

  const colEls = cols.map((c, i) => {
    const e = el('div', 'abs panel');
    e.style.cssText += 'width:250px;height:330px;padding:20px 18px;display:flex;flex-direction:column;gap:10px;z-index:2';
    e.innerHTML = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <span class="ico" style="width:24px;height:24px;color:var(--electric)">${icon(c.ico, 1.8)}</span>
        <span class="eyebrow" style="font-size:14px;color:${i === 3 ? 'var(--glow)' : 'var(--n-300)'}">${c.h}</span></div>`;
    c.rowEls = c.rows.map((r) => {
      const x = el('div', 'mono', e, r);
      x.style.cssText = 'font-size:16.5px;padding:9px 10px;border-radius:7px;background:rgba(255,255,255,.05);border-left:3px solid var(--moon);white-space:nowrap';
      return x;
    });
    place(e, xs[i], cy);
    return e;
  });
  pop(colEls, 52.1, { stagger: 0.16, scale: 0.85, ease: 'expo.out' });
  cols.forEach((c) => c.rowEls.forEach((r, j) => {
    gsap.set(r, { opacity: 0, x: -14 });
    tl.to(r, { opacity: 1, x: 0, duration: 0.35, ease: 'expo.out' }, c.t + j * 0.12);
  }));

  // recommendation
  const rec = el('div', '', colEls[3]);
  rec.style.cssText = 'margin-top:8px;display:flex;flex-direction:column;gap:12px';
  rec.innerHTML = `<div style="font:700 44px/1 var(--head);letter-spacing:-.02em">Route B</div>
    <div class="mono" style="font-size:17px;color:var(--n-300)">Fuel 17,200 lb<br>ETA +6 min</div>
    <div style="display:flex;align-items:center;gap:8px;color:var(--green);font:600 20px/1 var(--head)"><span class="ico" style="width:24px;height:24px">${icon('circle-check', 2)}</span>Within limits</div>`;
  gsap.set(rec, { opacity: 0, y: 16 });
  tl.to(rec, { opacity: 1, y: 0, duration: 0.5, ease: 'expo.out' }, 57.8);
  tl.to(colEls[3], { borderColor: 'rgba(255,160,92,.7)', duration: 0.4 }, 57.8);

  // a pulse travels the whole chain on "drove every single recommendation"
  const pulse = el('div', 'abs');
  pulse.style.cssText += 'width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 0 24px 8px rgba(106,244,249,.8);z-index:3';
  drive((t) => {
    const p = E.inOutCubic(prog(t, 56.7, 57.85));
    if (p <= 0 || p >= 1) return (pulse.style.display = 'none');
    pulse.style.display = 'block';
    pulse.style.transform = `translate(${(250 + p * 900).toFixed(1)}px,${cy}px) translate(-50%,-50%)`;
  });

  const aud = el('div', 'abs stamp', null, 'AUDITABLE');
  aud.style.cssText += 'color:var(--green);z-index:4;font-size:24px';
  place(aud, 1150, 380);
  stamp(aud, 58.2, -6);
  const id = el('div', 'abs mono', null, 'TRACE #A7F3-22 · 142 SIGNED STEPS');
  id.style.cssText += 'font-size:17px;letter-spacing:.1em;color:var(--n-400);white-space:nowrap';
  place(id, 700, 872, { opacity: 0 });
  tl.to(id, { opacity: 1, duration: 0.5 }, 53.9);

  out([...colEls, aud, id], 58.95, { dur: 0.5, stagger: 0.03 });
  tl.to(sv, { opacity: 0, duration: 0.4 }, 58.95);
}
