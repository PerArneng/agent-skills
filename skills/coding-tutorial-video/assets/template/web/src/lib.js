// Engine: one paused GSAP timeline per episode; every frame is a pure function of t.
// Timing comes from the narration (data/<ep>.json): beats and word-level times.
import gsap from 'gsap';
import cfg from '../config.json';

export const W = cfg.width, H = cfg.height, FPS = cfg.fps;
export const SEAM = 1.8; // must match assemble.py

export const C = {
  bg: '#0e1a21', panel: '#12242d', struct: '#35505e', muted: '#8ba2af', ink: '#e6eef2',
  accent: '#3ed1c7', amber: '#f2b84b', source: '#76a9a5',
};

/** Master timeline — everything is placed at absolute seconds. */
export const tl = gsap.timeline({ paused: true });
/** Procedural per-frame functions (t) => void; must be pure functions of t. */
export const drivers = [];
export const drive = (fn) => drivers.push(fn);

// ------------------------------------------------------------------ timing
let DATA = null;
const BEATS = {};
export function setData(d) {
  DATA = d;
  d.beats.forEach((b) => (BEATS[b.id] = b));
}
export const data = () => DATA;
/** beat info: start (anticipation begins), v0/v1 (voice), end (after hold/silence) */
export function B(id) {
  const b = BEATS[id];
  if (!b) throw new Error('unknown beat ' + id);
  return b;
}
/** time at a fraction of the beat's voice */
export const at = (id, f = 0) => { const b = B(id); return b.v0 + f * (b.v1 - b.v0); };
/**
 * Time a word is spoken in a beat (Whisper word timing). Starts an entrance
 * slightly before the word so it has landed when the word is heard.
 * Falls back to the word's character position in the sentence.
 */
const NUM = { one: '1', two: '2', three: '3', four: '4', five: '5', six: '6', seven: '7', eight: '8', nine: '9',
  ten: '10', nineteen: '19' };
export function word(id, w, nth = 0, lead = 0.15) {
  const b = B(id);
  const q = w.toLowerCase().replace(/[^a-z0-9]/g, '');
  const alt = NUM[q];
  const hits = b.words.filter((x) => x.w === q || x.w.startsWith(q) || (alt && x.w.startsWith(alt)));
  if (hits[nth]) return Math.max(b.start, hits[nth].t - lead);
  // Whisper often drops the first word after a long silence (e.g. right after a retrieval
  // window); the first word is spoken at the voice start, so that's exact enough.
  const first = b.say.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(/\s+/)[0];
  if (nth === 0 && (q === first || first.startsWith(q))) return Math.max(b.start, b.v0 - lead);
  const pos = b.say.toLowerCase().indexOf(w.toLowerCase());
  if (!DATA.estimated) console.warn(`word "${w}" not heard in ${id}; estimating`);
  return at(id, pos >= 0 ? pos / b.say.length : 0.5) - lead;
}
export const seam = (sceneId) => DATA.seams.find((s) => s.scene === sceneId);

// ------------------------------------------------------------------ icons
// Every lucide icon by name (https://lucide.dev/icons), inheriting currentColor.
const LUCIDE = import.meta.glob('/node_modules/lucide-static/icons/*.svg', { query: '?raw', import: 'default', eager: true });
export function icon(name, strokeWidth = 2) {
  const s = LUCIDE[`/node_modules/lucide-static/icons/${name}.svg`];
  if (!s) throw new Error('unknown lucide icon: ' + name);
  return s.replace(/<!--.*?-->/s, '').replace('stroke-width="2"', `stroke-width="${strokeWidth}"`);
}

// ------------------------------------------------------------------ dom
export const ui = () => document.getElementById('ui');
export function el(tag, cls, parent, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  (parent || ui()).appendChild(e);
  return e;
}
/** absolutely place an element centred on (x,y) */
export function place(e, x, y, props = {}) {
  gsap.set(e, { x, y, xPercent: -50, yPercent: -50, ...props });
  return e;
}
export function svgLayer(z = 0, parent) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', `0 0 ${W} ${H}`);
  s.setAttribute('width', W); s.setAttribute('height', H);
  s.style.cssText = `position:absolute;left:0;top:0;overflow:visible;z-index:${z}`;
  (parent || ui()).appendChild(s);
  return s;
}
export function svgEl(tag, attrs, parent) {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// ------------------------------------------------------------------ math
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, p) => a + (b - a) * p;
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const E = {
  inOutSine: (p) => -(Math.cos(Math.PI * p) - 1) / 2,
  inOutCubic: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  outCubic: (p) => 1 - Math.pow(1 - p, 3),
};

// ------------------------------------------------------------------ motion vocabulary
// Slow-in/slow-out on everything that means something; no bounce on claims.
export const EASE = 'power2.inOut';

/** fade/settle in (content entrance): eased, short, no springs */
export function show(targets, t, { dur = 0.6, y = 12, stagger = 0 } = {}) {
  gsap.set(targets, { opacity: 0, y: `+=${y}` });
  tl.to(targets, { opacity: 1, y: `-=${y}`, duration: dur, ease: 'power2.out', stagger }, t);
}
export function hide(targets, t, { dur = 0.5, y = 0 } = {}) {
  tl.to(targets, { opacity: 0, y: y ? `+=${y}` : '+=0', duration: dur, ease: 'power2.in' }, t);
}
export function fadeTo(targets, t, opacity, dur = 0.5) {
  tl.to(targets, { opacity, duration: dur, ease: EASE }, t);
}
/** move/scale a GSAP-owned element (centre coordinates) */
export function moveTo(target, t, vars, dur = 0.9) {
  tl.to(target, { ...vars, duration: dur, ease: EASE }, t);
}

export { gsap };
