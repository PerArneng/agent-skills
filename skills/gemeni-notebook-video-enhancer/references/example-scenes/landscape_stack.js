// The five-layer stack: born as the table of contents ("five structural layers"), docks to the
// right column, lights one slot per section, then returns to centre for the synthesis and
// collapses into the logo. It is the thread that runs through the whole video.
import { tl, el, place, icon, gsap, W, H } from '../lib.js';

export const LAYERS = [
  { n: '01', name: 'Context Graph', ico: 'network', t: 20.86 },
  { n: '02', name: 'Role-Bound Architecture', ico: 'id-card', t: 32.58 },
  { n: '03', name: 'Why-Trail', ico: 'scroll-text', t: 46.32 },
  { n: '04', name: 'AI-SMS Integration', ico: 'shield-check', t: 59.38 },
  { n: '05', name: 'Accumulating Context', ico: 'database', t: 71.88 },
];
export const DOCK_X = 1600;
const dockY = (i) => 868 - i * 84;
export const T_TOC = 18.74, T_DOCK = 20.2, T_CENTER = 82.1, T_COLLAPSE = 86.95;
export const centerY = (i) => 790 - i * 100;

export const slots = [];

export default function stack() {
  const hdr = el('div', 'abs eyebrow', null, 'Airflow · 5 structural layers');
  place(hdr, DOCK_X, dockY(4) - 72, { opacity: 0 });
  tl.to(hdr, { opacity: 1, duration: 0.6 }, T_DOCK + 0.8);
  tl.to(hdr, { opacity: 0, duration: 0.4 }, T_CENTER - 0.2);

  LAYERS.forEach((L, i) => {
    const s = el('div', 'abs panel slot', null,
      `<span class="acc"></span><span class="ico" style="width:1.05em;height:1.05em;color:var(--electric);flex:none">${icon(L.ico, 1.75)}</span>` +
      `<span class="sn">${L.n}</span><span class="sl">${L.name}</span><span class="ok ico">${icon('check', 2.5)}</span>`);
    slots.push(s);
    const acc = s.querySelector('.acc'), ok = s.querySelector('.ok');
    gsap.set(acc, { scaleY: 0, transformOrigin: '50% 50%' });
    gsap.set(ok, { opacity: 0, scale: 0.4 });
    gsap.set(s, { boxShadow: 'inset 0 0 0 300px rgba(0,99,121,0)' });

    // 1) table of contents, top→bottom 01..05, centre stage
    const ty = 392 + i * 104;
    place(s, 960 + 60, ty, { width: 880, height: 84, fontSize: 32, opacity: 0, filter: 'blur(10px)' });
    tl.to(s, { opacity: 1, x: 960, filter: 'blur(0px)', duration: 0.7, ease: 'expo.out' }, T_TOC + i * 0.13);

    // 2) dock: fly into the right column, foundation (01) at the bottom
    tl.to(s, { x: DOCK_X, y: dockY(i), width: 440, height: 66, fontSize: 21, duration: 1.1, ease: 'power3.inOut' }, T_DOCK + (4 - i) * 0.06);
    tl.to(s, { opacity: 0.42, duration: 0.5 }, T_DOCK + 1.0);

    // 3) active while its section plays, then "done"
    const tEnd = i < 4 ? LAYERS[i + 1].t : T_CENTER;
    tl.to(s, { opacity: 1, borderColor: 'rgba(106,244,249,0.6)', duration: 0.5 }, L.t - 0.1);
    tl.to(acc, { scaleY: 1, duration: 0.5, ease: 'expo.out' }, L.t);
    tl.to(s, { x: DOCK_X - 24, duration: 0.6, ease: 'expo.out' }, L.t);
    tl.to(s, { x: DOCK_X, borderColor: 'rgba(255,255,255,0.16)', opacity: 0.85, duration: 0.6, ease: 'power2.inOut' }, tEnd - 0.2);
    tl.to(acc, { scaleY: 0, duration: 0.4 }, tEnd - 0.2);
    tl.to(ok, { opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(2.5)' }, tEnd - 0.1);

    // 4) synthesis: centre, bigger, light up bottom→top
    tl.to(s, { x: 960, y: centerY(i), width: 760, height: 80, fontSize: 31, opacity: 1, duration: 1.2, ease: 'power3.inOut' }, T_CENTER + i * 0.05);
    tl.to(s, { borderColor: 'rgba(106,244,249,0.7)', boxShadow: 'inset 0 0 0 300px rgba(0,99,121,0.45)', duration: 0.35 }, 83.3 + i * 0.2);
    tl.to(acc, { scaleY: 1, duration: 0.35 }, 83.3 + i * 0.2);

    // 5) collapse into the logo
    tl.to(s, { y: 470, scale: 0.5, opacity: 0, filter: 'blur(14px)', duration: 0.7, ease: 'power3.in' }, T_COLLAPSE + (4 - i) * 0.04);
  });
}
