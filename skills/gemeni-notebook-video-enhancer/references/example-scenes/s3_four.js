// 12.22 – 17.4  "Here are four UX patterns that integrate human judgment without overwhelming you."
import { tl, el, place, icon, pop, out, float, drive, morph, heroColor, bgTo, gsap } from '../lib.js';
import { roundRect } from '../shapes.js';
import { TILES } from './s2_fatigue.js';

export const PATTERNS = [
  ['01', 'Selective Routing', 'route', '#22d3ee'],
  ['02', 'Claim Decomposition', 'listChecks', '#a78bfa'],
  ['03', 'Intentional Friction', 'hand', '#fbbf24'],
  ['04', 'Calibrated Trust', 'gauge', '#34d399'],
];

export default function s3() {
  morph(12.2, roundRect(540, 950, 940, 940, 80), 1.1, 'expo.inOut');
  heroColor(12.3, '#22d3ee', '#a78bfa', '#f472b6', 1.0);
  bgTo(12.3, '#150d52', '#0b5e8f', '#6a2bc2', 0.5, 1.6);

  const head = el('div', 'abs');
  head.style.cssText = 'text-align:center;white-space:nowrap';
  head.innerHTML = `<div style="font:600 34px var(--head);letter-spacing:.3em;color:var(--muted);margin-bottom:16px">HUMAN-IN-THE-LOOP</div>
    <div class="grad-text" style="font:700 120px/1 var(--head);letter-spacing:-.03em">4 UX Patterns</div>`;
  place(head, 540, 330, { opacity: 0, y: 380, filter: 'blur(20px)' });
  tl.to(head, { opacity: 1, y: 330, filter: 'blur(0px)', duration: 1.0, ease: 'expo.out' }, 12.85);

  const tiles = PATTERNS.map(([n, name, ic, col], i) => {
    const t = el('div', 'abs glass');
    t.style.cssText += `width:390px;height:390px;border-radius:44px;padding:34px;display:flex;flex-direction:column;justify-content:space-between`;
    t.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font:700 46px var(--mono);color:${col}">${n}</span>
        <span class="ico" style="width:78px;height:78px;color:${col};filter:drop-shadow(0 0 16px ${col})">${icon(ic, 1.8)}</span></div>
      <div style="font:600 44px/1.08 var(--head);letter-spacing:-.01em">${name.replace(' ', '<br>')}</div>`;
    place(t, TILES[i][0], TILES[i][1]);
    float(t, { amp: 6, speed: 0.4, seed: i * 2.3 });
    return t;
  });
  pop(tiles, 13.05, { stagger: 0.14, dur: 0.9, ease: 'expo.out', scale: 0.5, blur: 18 });

  // human node in the middle with links
  const svg = el('div', 'abs', null, `<svg width="1080" height="1920" viewBox="0 0 1080 1920">${TILES.map(
    ([x, y]) => `<line x1="540" y1="950" x2="${x}" y2="${y}" stroke="url(#heroStroke)" stroke-width="5" stroke-linecap="round" stroke-dasharray="2 14"/>`
  ).join('')}</svg>`);
  gsap.set(svg, { opacity: 0 });
  svg.style.zIndex = 0;
  const node = el('div', 'abs glass');
  node.style.cssText += 'width:150px;height:150px;border-radius:50%;display:flex;align-items:center;justify-content:center;z-index:3;box-shadow:0 0 60px rgba(103,232,249,.55), inset 0 1.5px 0 rgba(255,255,255,.3)';
  node.innerHTML = `<span class="ico" style="width:80px;height:80px;color:#fff">${icon('user', 1.8)}</span>`;
  place(node, 540, 950);
  pop(node, 14.85, { ease: 'back.out(2.5)' });
  tl.to(svg, { opacity: 1, duration: 0.5 }, 14.9);
  const lines = svg.querySelectorAll('line');
  drive((t) => lines.forEach((l) => l.setAttribute('stroke-dashoffset', (-t * 60).toFixed(1))));

  // calm pulse rings — "without overwhelming you"
  const rings = [0, 1, 2].map(() => {
    const r = el('div', 'abs');
    r.style.cssText = 'width:200px;height:200px;border-radius:50%;border:3px solid rgba(103,232,249,.7)';
    place(r, 540, 950, { opacity: 0, scale: 0.6 });
    return r;
  });
  rings.forEach((r, i) => {
    tl.to(r, { opacity: 0.9, duration: 0.1 }, 15.6 + i * 0.35);
    tl.to(r, { scale: 5, opacity: 0, duration: 1.4, ease: 'power2.out' }, 15.7 + i * 0.35);
  });
  bgTo(15.6, '#0b1f4d', '#0b7a8f', '#3b2bb0', 0.35, 1.5);

  // transition: tile 01 flies up to become the title, others dissolve
  out([head, node, svg], 16.95, { dur: 0.5, blur: 18 });
  out(tiles.slice(1), 17.05, { dur: 0.55, stagger: 0.05, scale: 0.6, blur: 24 });
  tl.to(tiles[0], { x: 540, y: 250, scale: 0.3, duration: 0.7, ease: 'power3.inOut' }, 17.1);
  tl.to(tiles[0], { opacity: 0, filter: 'blur(10px)', duration: 0.3 }, 17.6);
}
