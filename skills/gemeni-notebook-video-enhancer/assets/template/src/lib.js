import gsap from 'gsap';

import { W, H, FPS, DURATION } from './config.js';
export { W, H, FPS, DURATION };

// Every lucide icon is available by its lucide name (https://lucide.dev/icons), e.g. icon('triangle-alert').
const LUCIDE = import.meta.glob('/node_modules/lucide-static/icons/*.svg', { query: '?raw', import: 'default', eager: true });
// short aliases used by the example scenes
const ALIAS = {
  alert: 'triangle-alert', check: 'check', x: 'x', eye: 'eye', scanEye: 'scan-eye', user: 'user-round',
  sparkles: 'sparkles', cpu: 'cpu', file: 'file-text', route: 'route', listChecks: 'list-checks', hand: 'hand',
  gauge: 'gauge', shieldCheck: 'shield-check', shieldAlert: 'shield-alert', brain: 'brain', wrench: 'wrench',
  chevron: 'chevron-down', circleCheck: 'circle-check', circleX: 'circle-x', help: 'circle-help', zap: 'zap',
  bot: 'bot', clock: 'clock', layers: 'layers', bell: 'bell',
};


/** Master timeline — everything is placed at absolute seconds. */
export const tl = gsap.timeline({ paused: true });

/** Procedural per-frame functions: (t) => void. Must be pure functions of t. */
export const drivers = [];
export const drive = (fn) => drivers.push(fn);

export const ui = () => document.getElementById('ui');

export function el(tag, cls, parent, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  (parent || ui()).appendChild(e);
  return e;
}

export function icon(name, strokeWidth = 2) {
  const s = LUCIDE[`/node_modules/lucide-static/icons/${ALIAS[name] || name}.svg`];
  if (!s) throw new Error('unknown lucide icon: ' + name);
  return s.replace(/<!--.*?-->/s, '').replace('stroke-width="2"', `stroke-width="${strokeWidth}"`);
}

/** absolutely place an element centred on (x,y), hidden unless visible=true */
export function place(e, x, y, props = {}) {
  gsap.set(e, { x, y, xPercent: -50, yPercent: -50, ...props });
  return e;
}

export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const hash = (n) => { const r = mulberry32(Math.floor(n) * 9973 + 17); return r(); };

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, p) => a + (b - a) * p;
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const E = {
  outCubic: (p) => 1 - Math.pow(1 - p, 3),
  inCubic: (p) => p * p * p,
  inOutCubic: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  outExpo: (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  inOutSine: (p) => -(Math.cos(Math.PI * p) - 1) / 2,
  outBack: (p) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
};

/** soft window: 0 before a, ramps to 1 over fin, holds, ramps down over fout ending at b */
export const env = (t, a, b, fin = 0.4, fout = 0.4) =>
  Math.min(E.inOutSine(prog(t, a, a + fin)), 1 - E.inOutSine(prog(t, b - fout, b)));

/** gentle float using the independent CSS `translate`/`rotate` props (never clashes with GSAP transforms) */
export function float(e, { amp = 10, speed = 0.5, seed = 1, rot = 0 } = {}) {
  drive((t) => {
    const dx = Math.sin(t * speed * 2.1 + seed * 1.7) * amp;
    const dy = Math.cos(t * speed * 1.6 + seed * 2.9) * amp;
    e.style.translate = `${dx.toFixed(2)}px ${dy.toFixed(2)}px`;
  });
  return e;
}

/** standard exits / entrances as timeline tweens */
export function pop(targets, t, opts = {}) {
  const { dur = 0.7, stagger = 0.06, ease = 'back.out(1.8)', scale = 0.4, blur = 12 } = opts;
  gsap.set(targets, { opacity: 0, scale, filter: `blur(${blur}px)` });
  tl.to(targets, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: dur, ease, stagger }, t);
}

export function out(targets, t, opts = {}) {
  const { dur = 0.6, stagger = 0, scale = 0.85, blur = 16, y = 0, ease = 'power2.in' } = opts;
  tl.to(targets, { opacity: 0, scale, filter: `blur(${blur}px)`, y: y ? `+=${y}` : '+=0', duration: dur, stagger, ease }, t);
}

/** Title chip "01  Selective Routing" */
export function sceneTitle(num, name, tIn, tOut) {
  const w = el('div', 'abs title glass');
  w.innerHTML = `<span class="num">${num}</span><span class="name">${name
    .split('')
    .map((c) => `<span class="ch">${c === ' ' ? '&nbsp;' : c}</span>`)
    .join('')}</span>`;
  const ty = Math.round(H * 0.13); // 250 on a 1920-high stage, 140 on 1080
  place(w, W / 2, ty + 50, { opacity: 0, scale: 0.9, filter: 'blur(18px)' });
  tl.to(w, { opacity: 1, y: ty, scale: 1, filter: 'blur(0px)', duration: 0.9, ease: 'expo.out' }, tIn);
  const chars = w.querySelectorAll('.ch');
  gsap.set(chars, { opacity: 0, yPercent: 60 });
  tl.to(chars, { opacity: 1, yPercent: 0, duration: 0.5, stagger: 0.018, ease: 'power3.out' }, tIn + 0.12);
  tl.to(w, { opacity: 0, y: ty - 60, scale: 0.94, filter: 'blur(16px)', duration: 0.55, ease: 'power2.in' }, tOut);
  return w;
}

/** colour helpers for hero + background */
export const bgState = {
  c1r: 0.09, c1g: 0.05, c1b: 0.32,   // deep
  c2r: 0.02, c2g: 0.45, c2b: 0.65,   // cool accent
  c3r: 0.55, c3g: 0.18, c3b: 0.75,   // warm accent
  energy: 0.5,
};
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
export function bgTo(t, c1, c2, c3, energy = 0.5, dur = 1.4) {
  const [a, b, c] = [hex(c1), hex(c2), hex(c3)];
  tl.to(bgState, {
    c1r: a[0], c1g: a[1], c1b: a[2], c2r: b[0], c2g: b[1], c2b: b[2], c3r: c[0], c3g: c[1], c3b: c[2],
    energy, duration: dur, ease: 'sine.inOut',
  }, t);
}
export function heroColor(t, s1, s2, s3, dur = 0.8) {
  tl.to('#hs1', { attr: { 'stop-color': s1 }, duration: dur }, t);
  tl.to('#hs2', { attr: { 'stop-color': s2 }, duration: dur }, t);
  tl.to('#hs3', { attr: { 'stop-color': s3 }, duration: dur }, t);
  tl.to('#hf1', { attr: { 'stop-color': s2 }, duration: dur }, t);
}
export function morph(t, d, dur = 0.9, ease = 'power3.inOut', shapeIndex = 'auto') {
  tl.to('#hero', { morphSVG: { shape: d, shapeIndex }, duration: dur, ease }, t);
}

/** global cursor */
let _cursor;
export function cursor() {
  if (_cursor) return _cursor;
  _cursor = el('div', 'abs cursor',
    null,
    `<svg viewBox="0 0 24 24"><path d="M4 2.5 L4 19 L8.6 14.8 L11.6 21.2 L14.6 19.8 L11.7 13.6 L18 13.3 Z" fill="#fff" stroke="#0b0820" stroke-width="1.3" stroke-linejoin="round"/></svg>`);
  gsap.set(_cursor, { x: W + 120, y: H - 120, opacity: 0, xPercent: -8, yPercent: -6, zIndex: 50 });
  return _cursor;
}
/** move cursor then click at time tClick */
export function click(x, y, tArrive, tClick, dur = 0.6) {
  const c = cursor();
  tl.to(c, { x, y, opacity: 1, duration: dur, ease: 'power3.inOut' }, tArrive - dur);
  tl.to(c, { scale: 0.82, duration: 0.09, yoyo: true, repeat: 1, ease: 'power1.inOut' }, tClick);
  const r = el('div', 'abs ripple');
  place(r, x, y, { opacity: 0, scale: 0.2 });
  tl.to(r, { opacity: 1, duration: 0.05 }, tClick);
  tl.to(r, { scale: 1.6, opacity: 0, duration: 0.6, ease: 'power2.out' }, tClick + 0.05);
}
export function cursorHide(t) { tl.to(cursor(), { opacity: 0, duration: 0.3 }, t); }

/** full-stage SVG overlay inside #ui for connectors, cracks, gauges (z-index below cards unless given) */
export function svgLayer(z = 0) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', `0 0 ${W} ${H}`);
  s.setAttribute('width', W); s.setAttribute('height', H);
  s.style.cssText = `position:absolute;left:0;top:0;overflow:visible;z-index:${z}`;
  ui().appendChild(s);
  return s;
}
export function svgEl(tag, attrs, parent) {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent.appendChild(e);
  return e;
}
/** flowing dashes on paths that have a stroke-dasharray (driver) */
export function flow(paths, speed = 60) {
  drive((t) => paths.forEach((p) => p.setAttribute('stroke-dashoffset', (-t * speed).toFixed(1))));
}
/** slam-in stamp ("UNVERIFIED", "BLOCKED", ✕ icon …) */
export function stamp(e, t, rot = -8) {
  gsap.set(e, { opacity: 0, scale: 2.2, rotation: rot });
  tl.to(e, { opacity: 1, scale: 1, duration: 0.28, ease: 'power4.in' }, t);
}
/** text typed by a driver between t0 and t1, with a blinking caret while typing */
export function typeText(e, text, t0, t1, caret = true) {
  drive((t) => {
    const n = Math.round(text.length * prog(t, t0, t1));
    const on = caret && t > t0 - 0.3 && t < t1 + 0.6 && Math.floor(t * 3) % 2 === 0;
    e.textContent = text.slice(0, n) + (on ? '▍' : '');
  });
}
/**
 * Inline an SVG (e.g. a brand logo imported with `import raw from './assets/logo.svg?raw'`) at a given width.
 * Gradient/clip ids are prefixed so several copies can coexist, and inline `transform` styles are stripped so
 * GSAP can own the children. Returns { wrap, svg, parts } — parts are the top-level drawable children
 * (a wordmark is often one group per letter: stagger them for a letter-by-letter reveal).
 */
let _svgN = 0;
export function inlineSvg(raw, width, parent) {
  const pre = `sv${_svgN++}-`;
  const ids = [...raw.matchAll(/id="([^"]+)"/g)].map((m) => m[1]);
  let s = raw;
  ids.forEach((id) => { s = s.replaceAll(`id="${id}"`, `id="${pre}${id}"`).replaceAll(`url(#${id})`, `url(#${pre}${id})`).replaceAll(`href="#${id}"`, `href="#${pre}${id}"`); });
  s = s.replace(/<svg([^>]*?)\sclass="[^"]*"/, '<svg$1').replace(/\sstyle="[^"]*transform[^"]*"/g, '');
  const wrap = el('div', 'abs', parent, s);
  const svg = wrap.querySelector('svg');
  const vb = (svg.getAttribute('viewBox') || '0 0 100 100').split(/[ ,]+/).map(Number);
  svg.setAttribute('width', width); svg.setAttribute('height', Math.round((width * vb[3]) / vb[2]));
  svg.style.cssText = 'display:block;overflow:visible';
  const parts = [...svg.children].filter((c) => !['defs', 'title', 'desc', 'style'].includes(c.tagName));
  return { wrap, svg, parts };
}

export { gsap };
