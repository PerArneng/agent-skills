// Reusable, time-placed components. All state changes are timeline tweens at
// absolute seconds, or drivers that are pure functions of t (see references/engine.md).
import { tl, drive, el, place, svgEl, svgLayer, gsap, C, E, prog, lerp, clamp, B, EASE, icon } from './lib.js';

// ================================================================== flow map
// A system diagram whose parts keep their identity for the whole lesson: nodes
// (the "cast of characters"), edges between them, and a token that travels along
// edges to show a request, a message or a file moving through the system.
// Examples: agent loop (messages → model → tools), Ansible (control node → SSH →
// hosts), CI (commit → build → test → deploy), HTTP (browser → server → DB).

const STATE = {
  idle: { stroke: C.struct, 'stroke-opacity': 1, 'fill-opacity': 0 },
  live: { stroke: C.accent, 'stroke-opacity': 1, 'fill-opacity': 0.14 },
  done: { stroke: C.accent, 'stroke-opacity': 0.45, 'fill-opacity': 0 },
  source: { stroke: C.source, 'stroke-opacity': 1, 'fill-opacity': 0 },  // analogy source
  dim: { stroke: C.struct, 'stroke-opacity': 0.35, 'fill-opacity': 0 },
};

export function hexPath(cx, cy, r) {
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = Math.PI / 6 + (i * Math.PI) / 3;
    return `${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`;
  });
  return `M${pts.join('L')}Z`;
}

/** Lucide icon as SVG children (so it can live inside the map and take state colours). */
function iconGroup(name, size, parent) {
  const g = svgEl('g', { fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': 1.6 }, parent);
  const doc = new DOMParser().parseFromString(icon(name, 1.6), 'image/svg+xml');
  [...doc.documentElement.children].forEach((c) => g.appendChild(document.importNode(c, true)));
  g.setAttribute('transform', `scale(${size / 24}) translate(-12 -12)`);
  return g;
}

/**
 * new FlowMap({ x, y, scale, nodes, edges, labels })
 *   node: { id, x, y, shape: 'box'|'hex'|'stack'|'circle'|'icon', w, h, r, count, icon, label, labelAt: 'top'|'bottom'|'left'|'right' }
 *         (x, y are map-local; the map's own x, y place it on the 1920×1080 stage)
 *   edge: { id, from, to, bend = 0.25 } — a curve between node borders
 *         { id, from, to, ring: { cx, cy, R } } — a clockwise arc on a circle (loops)
 * Methods take absolute seconds: state(t, ids, s), travel(t0, t1, edgeIds), moveTo(t, {x,y,scale}), …
 */
export class FlowMap {
  constructor({ x = 960, y = 540, scale = 1, nodes = [], edges = [], labels = true, layer } = {}) {
    this.layer = layer || svgLayer(2);
    this.pos = svgEl('g', {}, this.layer);
    this.g = svgEl('g', {}, this.pos);
    gsap.set(this.pos, { x, y });
    gsap.set(this.g, { scale, svgOrigin: '0 0' });
    this.nodes = {}; this.edges = {}; this.labels = {}; this.moves = [];
    this.edgeLayer = svgEl('g', {}, this.g);
    nodes.forEach((n) => this.addNode(n, labels));
    edges.forEach((e) => this.addEdge(e));
    this.dot = svgEl('circle', { r: 12, fill: C.accent, opacity: 0 }, this.g);
    drive((t) => this._dot(t));
  }

  addNode(n, labels = true) {
    const g = svgEl('g', {}, this.g);
    const sw = 5, els = [];
    const w = n.w || 170, h = n.h || 130, r = n.r || 42;
    if (n.shape === 'hex') {
      const k = n.count || 1;
      for (let i = 0; i < k; i++) els.push(svgEl('path', { d: hexPath(n.x + (i - (k - 1) / 2) * r * 2.2, n.y, r), 'stroke-width': sw }, g));
    } else if (n.shape === 'stack') {
      const k = n.count || 3, cw = n.w || 144, ch = 32, gap = 12;
      for (let i = 0; i < k; i++) els.push(svgEl('rect', { x: n.x - cw / 2, y: n.y - (k * (ch + gap) - gap) / 2 + i * (ch + gap), width: cw, height: ch, rx: 9, 'stroke-width': 4 }, g));
    } else if (n.shape === 'circle') {
      els.push(svgEl('circle', { cx: n.x, cy: n.y, r: n.r || 70, 'stroke-width': sw }, g));
    } else if (n.shape === 'icon') {
      const ig = iconGroup(n.icon, n.size || 96, svgEl('g', { transform: `translate(${n.x} ${n.y})` }, g));
      ig.dataset.icon = '1';
      els.push(ig);
    } else { // box
      els.push(svgEl('rect', { x: n.x - w / 2, y: n.y - h / 2, width: w, height: h, rx: 28, 'stroke-width': sw }, g));
      if (n.core !== false) els.push(svgEl('circle', { cx: n.x, cy: n.y, r: 18, 'stroke-width': 0, 'data-core': 1 }, g));
    }
    const box = this._extent(n);
    this.nodes[n.id] = { ...n, g, els, box };
    this._style(els, 'idle', true);
    if (n.label) {
      const at = n.labelAt || 'bottom';
      const pos = { top: [n.x, box.y0 - 22, 'middle'], bottom: [n.x, box.y1 + 44, 'middle'],
        left: [box.x0 - 24, n.y + 10, 'end'], right: [box.x1 + 24, n.y + 10, 'start'] }[at];
      const l = svgEl('text', { x: pos[0], y: pos[1], 'text-anchor': pos[2], fill: C.muted,
        'font-family': 'Inter Variable', 'font-size': 28, 'font-weight': 500 }, this.g);
      l.textContent = n.label;
      if (!labels) gsap.set(l, { opacity: 0 });
      this.labels[n.id] = l;
    }
    return this.nodes[n.id];
  }

  _extent(n) {
    const w = n.shape === 'hex' ? (n.count || 1) * (n.r || 42) * 2.2 : n.shape === 'circle' ? 2 * (n.r || 70)
      : n.shape === 'icon' ? (n.size || 96) : n.shape === 'stack' ? (n.w || 144) : (n.w || 170);
    const h = n.shape === 'hex' ? 2 * (n.r || 42) : n.shape === 'circle' ? 2 * (n.r || 70)
      : n.shape === 'icon' ? (n.size || 96) : n.shape === 'stack' ? (n.count || 3) * 44 : (n.h || 130);
    return { x0: n.x - w / 2, x1: n.x + w / 2, y0: n.y - h / 2, y1: n.y + h / 2, w, h };
  }

  /** where a ray from the node centre toward (tx, ty) leaves its bounding box */
  _border(n, tx, ty, pad = 14) {
    const dx = tx - n.x, dy = ty - n.y;
    const sx = (n.box.w / 2 + pad) / Math.abs(dx || 1e-6), sy = (n.box.h / 2 + pad) / Math.abs(dy || 1e-6);
    const s = Math.min(sx, sy);
    return [n.x + dx * s, n.y + dy * s];
  }

  addEdge(e) {
    const a = this.nodes[e.from], b = this.nodes[e.to];
    let d;
    if (e.ring) {
      const { cx = 0, cy = 0, R } = e.ring;
      const ang = (n) => Math.atan2(-(n.y - cy), n.x - cx);
      const gap = e.gap ?? 0.3;
      const a0 = ang(a) - gap;
      let a1 = ang(b) + gap;
      while (a1 >= a0) a1 -= 2 * Math.PI;
      const P = (t) => [cx + R * Math.cos(t), cy - R * Math.sin(t)];
      const [x0, y0] = P(a0), [x1, y1] = P(a1);
      d = `M${x0},${y0} A${R},${R} 0 ${a0 - a1 > Math.PI ? 1 : 0} 1 ${x1},${y1}`;
    } else {
      const [x0, y0] = this._border(a, b.x, b.y), [x1, y1] = this._border(b, a.x, a.y);
      const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, bend = e.bend ?? 0.25;
      const cx = mx - (y1 - y0) * bend, cy = my + (x1 - x0) * bend;
      d = `M${x0},${y0} Q${cx},${cy} ${x1},${y1}`;
    }
    const path = svgEl('path', { d, fill: 'none', 'stroke-width': 5, 'stroke-linecap': 'round' }, this.edgeLayer);
    const L = path.getTotalLength();
    const p1 = path.getPointAtLength(L), p0 = path.getPointAtLength(Math.max(0, L - 2));
    const tx = p1.x - p0.x, ty = p1.y - p0.y, n = Math.hypot(tx, ty) || 1;
    const ux = tx / n, uy = ty / n, nx = -uy, ny = ux;
    const head = svgEl('path', { d: `M${p1.x + ux * 3},${p1.y + uy * 3} L${p1.x - ux * 18 + nx * 11},${p1.y - uy * 18 + ny * 11} L${p1.x - ux * 18 - nx * 11},${p1.y - uy * 18 - ny * 11}Z`,
      'stroke-width': 2 }, this.edgeLayer);
    if (e.arrow === false) head.setAttribute('display', 'none');
    this.edges[e.id] = { ...e, path, head, L, els: [path, head] };
    this._style([path, head], 'idle', true);
    return this.edges[e.id];
  }

  _style(els, st, now = false, t = 0, dur = 0.5) {
    const s = STATE[st];
    els.forEach((e) => {
      const solid = e.dataset?.core || (e.tagName === 'path' && Object.values(this.edges).some((x) => x.head === e));
      const attr = e.dataset?.icon ? { stroke: s.stroke, 'stroke-opacity': s['stroke-opacity'] }
        : solid ? { fill: s.stroke, 'fill-opacity': s['stroke-opacity'], stroke: s.stroke, 'stroke-opacity': s['stroke-opacity'] }
          : e.tagName === 'path' && Object.values(this.edges).some((x) => x.path === e) ? { stroke: s.stroke, 'stroke-opacity': s['stroke-opacity'] }
            : { ...s, fill: s.stroke };
      if (now) gsap.set(e, { attr });
      else tl.to(e, { attr, duration: dur, ease: EASE }, t);
    });
  }

  _els(ids) {
    return [].concat(ids).flatMap((id) => (this.nodes[id] ? this.nodes[id].els : this.edges[id] ? this.edges[id].els : []));
  }

  /** style nodes and/or edges: 'idle' | 'live' (the one live idea) | 'done' | 'source' | 'dim' */
  state(t, ids, st, dur = 0.5) {
    const els = this._els(ids);
    if (!els.length) throw new Error(`FlowMap.state: unknown id(s) ${ids}`);
    // head/core detection needs edges registered first, so style per element
    this._style(els, st, false, t, dur);
  }

  /** all nodes + edges */
  all() { return [...Object.keys(this.nodes), ...Object.keys(this.edges)]; }

  /** token travels along one edge, or a chain of edges, eased as one motion */
  travel(t0, t1, edgeIds, color) {
    const chain = [].concat(edgeIds).map((id) => { const e = this.edges[id]; if (!e) throw new Error(`no edge ${id}`); return e; });
    this.moves.push({ t0, t1, chain, total: chain.reduce((s, e) => s + e.L, 0), color });
    return t1;
  }
  /** token moves in a straight line between two map-local points */
  glide(t0, t1, [x0, y0], [x1, y1], color) { this.moves.push({ t0, t1, line: [x0, y0, x1, y1], color }); return t1; }

  _dot(t) {
    let vis = false, x = 0, y = 0, col = C.accent;
    for (const m of this.moves) {
      if (t < m.t0 - 0.25 || t > m.t1 + 0.35) continue;
      vis = true; col = m.color || C.accent;
      const p = E.inOutSine(prog(t, m.t0, m.t1));
      if (m.line) { x = lerp(m.line[0], m.line[2], p); y = lerp(m.line[1], m.line[3], p); continue; }
      let d = p * m.total;
      for (const e of m.chain) {
        if (d <= e.L || e === m.chain[m.chain.length - 1]) { const pt = e.path.getPointAtLength(Math.min(d, e.L)); x = pt.x; y = pt.y; break; }
        d -= e.L;
      }
    }
    this.dot.setAttribute('cx', x.toFixed(2));
    this.dot.setAttribute('cy', y.toFixed(2));
    this.dot.setAttribute('opacity', vis ? 1 : 0);
    this.dot.setAttribute('fill', col);
  }

  showLabels(t, on = true, ids = Object.keys(this.labels), dur = 0.5) {
    [].concat(ids).forEach((k) => this.labels[k] && tl.to(this.labels[k], { opacity: on ? 1 : 0, duration: dur, ease: EASE }, t));
  }
  /** fade parts in/out (e.g. build the cast one part at a time) */
  fade(t, ids, o, dur = 0.5) { tl.to(this._els(ids), { opacity: o, duration: dur, ease: EASE }, t); }
  hideNow(ids) { gsap.set(this._els(ids), { opacity: 0 }); }
  moveTo(t, { x, y, scale } = {}, dur = 1.0) {
    if (x != null || y != null) tl.to(this.pos, { x, y, duration: dur, ease: EASE }, t);
    if (scale != null) tl.to(this.g, { scale, duration: dur, ease: EASE }, t);
  }
  opacity(t, o, dur = 0.6) { tl.to(this.g, { opacity: o, duration: dur, ease: EASE }, t); }
  /** stage coordinates of a node for a given map placement (to connect HTML elements) */
  stageXY(id, { x = 960, y = 540, scale = 1 } = {}) { const n = this.nodes[id]; return [x + n.x * scale, y + n.y * scale]; }
}

/** Helper for loops: place node ids evenly on a circle (first at the top, clockwise) and connect them with ring arcs. */
export function ringLayout(ids, { R = 250, start = 90, shapes = {}, labels = {} } = {}) {
  const nodes = ids.map((id, i) => {
    const a = ((start - (360 / ids.length) * i) * Math.PI) / 180;
    return { id, x: R * Math.cos(a), y: -R * Math.sin(a), shape: 'box', ...(shapes[id] || {}), label: labels[id] ?? id };
  });
  const edges = ids.map((id, i) => ({ id: `${id}>${ids[(i + 1) % ids.length]}`, from: id, to: ids[(i + 1) % ids.length], ring: { R } }));
  return { nodes, edges };
}

// ================================================================== code panel
// Minimal, muted syntax roles per language: keywords (--kw) and comments (--muted).
// Colour is kept deliberately quiet so the accent can mark the live token.
const LANGS = {
  python: { kw: /\b(from|import|def|class|return|while|if|elif|else|in|break|for|with|as|None|True|False|not|and|or|async|await|try|except|raise|lambda|yield)\b/g, cm: ['#'], doc: '"""' },
  yaml: { kw: /^(\s*-?\s*)([\w.-]+)(?=:)/gm, cm: ['#'], keyGroup: 2 },
  bash: { kw: /\b(if|then|else|fi|for|do|done|while|case|esac|function|export|local|return|sudo|cd|echo)\b/g, cm: ['#'] },
  js: { kw: /\b(import|from|export|default|const|let|var|function|return|if|else|for|while|await|async|new|class|extends|try|catch|throw|of|in)\b/g, cm: ['//'] },
  json: { kw: /("[\w-]+")(?=\s*:)/g, cm: [] },
  go: { kw: /\b(package|import|func|return|if|else|for|range|var|const|type|struct|interface|go|defer|nil|err)\b/g, cm: ['//'] },
  rust: { kw: /\b(fn|let|mut|use|pub|struct|enum|impl|match|if|else|for|in|loop|return|async|await|mod|crate)\b/g, cm: ['//'] },
  sql: { kw: /\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|JOIN|ON|GROUP|BY|ORDER|LIMIT|AND|OR|NOT|NULL)\b/gi, cm: ['--'] },
  docker: { kw: /^(FROM|RUN|COPY|ADD|WORKDIR|ENV|EXPOSE|CMD|ENTRYPOINT|ARG|USER|VOLUME)\b/gm, cm: ['#'] },
  ini: { kw: /^\s*(\[[^\]]+\]|[\w.-]+(?=\s*=))/gm, cm: ['#', ';'] },
  text: { kw: /$^/g, cm: [] },
};
const EXT = { py: 'python', yml: 'yaml', yaml: 'yaml', sh: 'bash', bash: 'bash', zsh: 'bash', js: 'js', mjs: 'js', ts: 'js',
  tsx: 'js', jsx: 'js', json: 'json', go: 'go', rs: 'rust', sql: 'sql', toml: 'ini', ini: 'ini', cfg: 'ini', conf: 'ini', env: 'ini' };
export function langOf(name) {
  if (/dockerfile/i.test(name)) return 'docker';
  if (/^\.env/.test(name) || /inventory|hosts$/i.test(name)) return 'ini';
  return EXT[(name.split('.').pop() || '').toLowerCase()] || 'text';
}

function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

/**
 * Real source in a panel. Lines are numbered as in the file. `lights` registers
 * substrings (per file line) that can be lit in the accent colour later.
 */
export class CodePanel {
  constructor(src, { name, from = 1, to, x = 960, y = 560, width = 1180, rows, fs = 26, lh = 40, lights = {}, z = 3, lang } = {}) {
    const L = LANGS[lang || langOf(name)] || LANGS.text;
    const all = src.replace(/\n$/, '').split('\n');
    to = to || all.length;
    this.from = from; this.lh = lh;
    this.lines = all.slice(from - 1, to);
    this.rows = rows || this.lines.length;
    this.root = el('div', 'abs code');
    this.root.style.cssText += `width:${width}px;z-index:${z};--fs:${fs}px;--lh:${lh}px`;
    el('div', 'hdr', this.root, esc(name));
    this.win = el('div', 'win', this.root);
    this.win.style.height = `${this.rows * lh + 18}px`;
    this.scroll = el('div', 'scroll', this.win);
    this.scroll.style.top = '6px';
    this.band = el('div', 'band', this.scroll);
    this.band.style.height = `${lh}px`;
    this.lineEls = [];
    this.toks = {};
    let inDoc = false;
    this.lines.forEach((line, i) => {
      const n = from + i;
      const q = L.doc ? line.split(L.doc).length - 1 : 0;
      const isDoc = inDoc || q > 0;
      if (q === 1) inDoc = !inDoc;
      const cm = isDoc || L.cm.some((c) => line.trim().startsWith(c));
      const ranges = [];
      (lights[n] || []).forEach((s, k) => {
        const idx = line.indexOf(s);
        if (idx >= 0) ranges.push({ a: idx, b: idx + s.length, cls: 'tok', key: s });
      });
      if (!cm) for (const m of line.matchAll(new RegExp(L.kw.source, L.kw.flags))) {
        const txt = L.keyGroup ? m[L.keyGroup] : m[0];
        const a = m.index + (L.keyGroup ? m[0].indexOf(txt) : 0), bb = a + txt.length;
        if (!txt) continue;
        if (!ranges.some((r) => a < r.b && bb > r.a)) ranges.push({ a, b: bb, cls: 'kw' });
      }
      ranges.sort((p, q2) => p.a - q2.a);
      let html = '', cur = 0;
      for (const r of ranges) {
        html += esc(line.slice(cur, r.a));
        html += `<span class="${r.cls}"${r.key ? ` data-k="${esc(r.key).replace(/"/g, '&quot;')}"` : ''}>${esc(line.slice(r.a, r.b))}</span>`;
        cur = r.b;
      }
      html += esc(line.slice(cur));
      const ln = el('div', 'ln', this.scroll, `<span class="num">${n}</span><span class="src${cm ? ' cm' : ''}">${html || ' '}</span>`);
      this.lineEls.push(ln);
      ln.querySelectorAll('.tok').forEach((s) => {
        s.dataset.base = cm ? C.muted : C.ink;
        gsap.set(s, { color: s.dataset.base });
        this.toks[`${n}:${s.dataset.k}`] = s;
      });
    });
    place(this.root, x, y);
    gsap.set(this.root, { opacity: 0 });
    this.lit = [];
  }
  el(n) { return this.lineEls[n - this.from]; }
  show(t, dur = 1.0) {
    tl.to(this.root, { opacity: 1, duration: 0.4, ease: EASE }, t);
    const vis = this.lineEls.slice(0, this.rows);
    gsap.set(vis, { opacity: 0, x: -10 });
    tl.to(vis, { opacity: 1, x: 0, duration: 0.45, ease: 'power2.out', stagger: Math.min(0.05, (dur - 0.45) / vis.length) }, t + 0.1);
    this.lineEls.slice(this.rows).forEach((e) => gsap.set(e, { opacity: 1 }));
    return t + dur;
  }
  hide(t, dur = 0.5) { tl.to(this.root, { opacity: 0, duration: dur, ease: 'power2.in' }, t); }
  /** light lines a..b (file line numbers), dim the rest; reset earlier token lights */
  focus(t, a, b = a, dur = 0.55) {
    this.lit.forEach((s) => tl.to(s, { color: s.dataset.base, duration: dur, ease: EASE }, t));
    this.lit = [];
    this.lineEls.forEach((e, i) => {
      const n = this.from + i;
      tl.to(e, { opacity: n >= a && n <= b ? 1 : 0.28, duration: dur, ease: EASE }, t);
    });
    const top = (a - this.from) * this.lh, h = (b - a + 1) * this.lh;
    tl.to(this.band, { top, height: h, opacity: 1, duration: dur, ease: EASE }, t);
    // keep the focused block inside the visible window
    if (this.lineEls.length > this.rows) {
      const first = clamp(Math.round((a + b) / 2 - this.from - this.rows / 2), 0, this.lineEls.length - this.rows);
      tl.to(this.scroll, { y: -first * this.lh, duration: dur + 0.2, ease: EASE }, t);
    }
  }
  unfocus(t, dur = 0.5) {
    this.lit.forEach((s) => tl.to(s, { color: s.dataset.base, duration: dur }, t));
    this.lit = [];
    tl.to(this.lineEls, { opacity: 1, duration: dur, ease: EASE }, t);
    tl.to(this.band, { opacity: 0, duration: dur, ease: EASE }, t);
  }
  /** dim one line further (e.g. the body a model never reads) */
  dimLine(t, n, o = 0.1) { tl.to(this.el(n), { opacity: o, duration: 0.7, ease: EASE }, t); }
  light(t, n, s, color = C.accent) {
    const e = this.toks[`${n}:${s}`];
    if (!e) throw new Error(`no light registered for line ${n}: ${s}`);
    tl.to(e, { color, duration: 0.45, ease: EASE }, t);
    this.lit.push(e);
  }
  /** amber if–then mark around lines a..b (reserved colour: act on this) */
  mark(t, a, b, t1) {
    const m = el('div', 'mark', this.scroll);
    m.style.cssText += `left:52px;right:14px;top:${(a - this.from) * this.lh - 4}px;height:${(b - a + 1) * this.lh + 8}px`;
    tl.to(m, { opacity: 1, duration: 0.5, ease: EASE }, t);
    if (t1) tl.to(m, { opacity: 0, duration: 0.4, ease: EASE }, t1);
    return m;
  }
  moveTo(t, vars, dur = 0.9) { tl.to(this.root, { ...vars, duration: dur, ease: EASE }, t); }
  /** stage coords of a line's right end (for connectors) */
  box() { return this.root; }
}

// ================================================================== terminal
/**
 * A terminal replaying real captured output. Content is driver-rendered from a
 * list of timed entries, so any frame can be rendered independently.
 */
export class Terminal {
  constructor({ x = 960, y = 560, width = 1100, rows = 10, fs = 23, lh = 36, title = 'terminal', z = 3 } = {}) {
    this.rows = rows; this.lh = lh;
    this.maxChars = Math.floor((width - 44) / (fs * 0.6));
    this.root = el('div', 'abs term');
    this.root.style.cssText += `width:${width}px;z-index:${z};--fs:${fs}px;--lh:${lh}px`;
    el('div', 'hdr', this.root, esc(title));
    const win = el('div', 'win', this.root);
    win.style.height = `${rows * lh + 22}px`;
    this.body = el('div', 'body', win);
    this.body.style.top = '8px';
    place(this.root, x, y);
    gsap.set(this.root, { opacity: 0 });
    this.entries = [];
    this.clears = [];
    drive((t) => this._render(t));
  }
  _fit(s) { return s.length <= this.maxChars ? s : s.slice(0, this.maxChars - 1) + '…'; }
  /** typed shell command; returns the time typing ends */
  cmd(t, text, cps = 26) {
    const t1 = t + Math.max(0.4, text.length / cps);
    this.entries.push({ t, t1, prompt: '$ ', text: this._fit(text), typed: true });
    return t1;
  }
  input(t, prompt, text, cps = 28) {
    const t1 = t + Math.max(0.4, text.length / cps);
    this.entries.push({ t, t1, prompt: prompt + ' ', text: this._fit(text), typed: true });
    return t1;
  }
  /** output lines streaming in (like tokens arriving); cls: 'hi' | 'dim' per line */
  out(t, lines, { gap = 0.1, cls = {} } = {}) {
    lines.forEach((text, i) => this.entries.push({ t: t + i * gap, text: this._fit(text), cls: cls[i] || '' }));
    return t + lines.length * gap;
  }
  clear(t) { this.clears.push(t); }
  show(t, dur = 0.4) { tl.to(this.root, { opacity: 1, duration: dur, ease: EASE }, t); }
  hide(t, dur = 0.5) { tl.to(this.root, { opacity: 0, duration: dur, ease: 'power2.in' }, t); }
  moveTo(t, vars, dur = 0.9) { tl.to(this.root, { ...vars, duration: dur, ease: EASE }, t); }
  _render(t) {
    const since = Math.max(-1, ...this.clears.filter((c) => c <= t));
    const vis = this.entries.filter((e) => e.t <= t && e.t > since);
    if (this._key === `${vis.length}|${Math.floor(t * 60)}` ) return;
    this._key = `${vis.length}|${Math.floor(t * 60)}`;
    let html = '';
    vis.forEach((e, i) => {
      let body = esc(e.text);
      let caret = '';
      if (e.typed) {
        const n = Math.round(e.text.length * prog(t, e.t, e.t1));
        body = esc(e.text.slice(0, n));
        const last = i === vis.length - 1;
        if (last && t < e.t1 + 0.5 && Math.floor(t * 2.5) % 2 === 0) caret = '<span class="caret">▍</span>';
      }
      const pre = e.prompt ? `<span class="p">${esc(e.prompt)}</span>` : '';
      html += `<div class="tl ${e.cls || ''}">${pre}${body}${caret}</div>`;
    });
    this.body.innerHTML = html;
    // eased scroll: each line beyond the window pushes the view up over 0.3 s
    let off = 0;
    vis.forEach((e, i) => { if (i >= this.rows) off += E.inOutSine(prog(t, e.t, e.t + 0.3)); });
    this.body.style.transform = `translateY(${(-off * this.lh).toFixed(2)}px)`;
  }
}

// ================================================================== small pieces
export function card(html, { x, y, cls = '', z = 4 } = {}) {
  const c = el('div', `abs card ${cls}`, null, html);
  c.style.zIndex = z;
  place(c, x, y, { opacity: 0 });
  return c;
}
export function chip(html, { x, y, cls = '', z = 4 } = {}) {
  const c = el('div', `abs chip ${cls}`, null, html);
  c.style.zIndex = z;
  place(c, x, y, { opacity: 0 });
  return c;
}
export function label(text, { x, y, cls = 'lbl', z = 4 } = {}) {
  const c = el('div', `abs ${cls}`, null, esc(text));
  c.style.zIndex = z;
  place(c, x, y, { opacity: 0 });
  return c;
}

/** segment title top-left: appears in the seam, stays faint for orientation */
export function segTitle(num, name, tIn, tOut) {
  const s = el('div', 'abs seg', null, `<b>${num}</b>${esc(name)}`);
  s.style.zIndex = 20;
  gsap.set(s, { x: 64, y: 44, opacity: 0 });
  tl.to(s, { opacity: 1, duration: 0.6, ease: EASE }, tIn);
  tl.to(s, { opacity: 0.55, duration: 0.8, ease: EASE }, tIn + 1.6);
  if (tOut != null) tl.to(s, { opacity: 0, duration: 0.5, ease: EASE }, tOut);
  return s;
}

/**
 * Retrieval beat: after the question is spoken, the field simplifies (veil),
 * a short amber prompt appears and an amber ring depletes over the silence.
 * Answers are only revealed after the window (feedback after the attempt).
 */
export function retrieval(beatId, prompt, { keep = [] } = {}) {
  const b = B(beatId);
  const t0 = b.v1 + 0.05, t1 = b.end - 0.35;
  const veil = el('div', 'veil');
  veil.style.zIndex = 30;
  const q = el('div', 'abs ask', null, esc(prompt));
  q.style.zIndex = 32;
  place(q, 960, 470, { opacity: 0 });
  const layer = svgLayer(32);
  const Rr = 46, circ = 2 * Math.PI * Rr;
  svgEl('circle', { cx: 960, cy: 600, r: Rr, fill: 'none', stroke: C.struct, 'stroke-width': 8 }, layer);
  const arc = svgEl('circle', { cx: 960, cy: 600, r: Rr, fill: 'none', stroke: C.amber, 'stroke-width': 8,
    'stroke-linecap': 'round', transform: 'rotate(-90 960 600)', 'stroke-dasharray': circ.toFixed(1) }, layer);
  gsap.set(layer, { opacity: 0 });
  tl.to(veil, { opacity: 0.92, duration: 0.5, ease: EASE }, t0);
  tl.to([q, layer], { opacity: 1, duration: 0.5, ease: EASE }, t0 + 0.1);
  drive((t) => arc.setAttribute('stroke-dashoffset', (circ * prog(t, t0 + 0.4, t1 - 0.2)).toFixed(1)));
  keep.forEach((k) => { k.style.zIndex = 31; });
  tl.to([veil, q, layer], { opacity: 0, duration: 0.45, ease: EASE }, t1);
  return { t0, t1 };
}

export { esc };
