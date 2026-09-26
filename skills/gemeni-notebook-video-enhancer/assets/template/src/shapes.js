// Path generators in stage coordinates (config.json width×height; 1080×1920 for Shorts). All return SVG path `d` strings.
const f = (n) => +n.toFixed(1);
const K = 0.5523; // cubic bezier circle constant

export function roundRect(cx, cy, w, h, r) {
  const x = cx - w / 2, y = cy - h / 2;
  r = Math.min(r, w / 2, h / 2);
  const k = r * (1 - K);
  return [
    `M${f(x + r)} ${f(y)}`, `H${f(x + w - r)}`,
    `C${f(x + w - k)} ${f(y)} ${f(x + w)} ${f(y + k)} ${f(x + w)} ${f(y + r)}`,
    `V${f(y + h - r)}`,
    `C${f(x + w)} ${f(y + h - k)} ${f(x + w - k)} ${f(y + h)} ${f(x + w - r)} ${f(y + h)}`,
    `H${f(x + r)}`,
    `C${f(x + k)} ${f(y + h)} ${f(x)} ${f(y + h - k)} ${f(x)} ${f(y + h - r)}`,
    `V${f(y + r)}`,
    `C${f(x)} ${f(y + k)} ${f(x + k)} ${f(y)} ${f(x + r)} ${f(y)}`, 'Z',
  ].join(' ');
}

export function circle(cx, cy, r) {
  const k = r * K;
  return [
    `M${f(cx)} ${f(cy - r)}`,
    `C${f(cx + k)} ${f(cy - r)} ${f(cx + r)} ${f(cy - k)} ${f(cx + r)} ${f(cy)}`,
    `C${f(cx + r)} ${f(cy + k)} ${f(cx + k)} ${f(cy + r)} ${f(cx)} ${f(cy + r)}`,
    `C${f(cx - k)} ${f(cy + r)} ${f(cx - r)} ${f(cy + k)} ${f(cx - r)} ${f(cy)}`,
    `C${f(cx - r)} ${f(cy - k)} ${f(cx - k)} ${f(cy - r)} ${f(cx)} ${f(cy - r)}`, 'Z',
  ].join(' ');
}

/** speech bubble with tail bottom-left */
export function bubble(cx, cy, w, h, r) {
  const x = cx - w / 2, y = cy - h / 2, k = r * (1 - K);
  const tx = x + w * 0.22;
  return [
    `M${f(x + r)} ${f(y)}`, `H${f(x + w - r)}`,
    `C${f(x + w - k)} ${f(y)} ${f(x + w)} ${f(y + k)} ${f(x + w)} ${f(y + r)}`,
    `V${f(y + h - r)}`,
    `C${f(x + w)} ${f(y + h - k)} ${f(x + w - k)} ${f(y + h)} ${f(x + w - r)} ${f(y + h)}`,
    `H${f(tx + 70)}`,
    `L${f(tx - 40)} ${f(y + h + 110)}`,
    `L${f(tx)} ${f(y + h)}`,
    `H${f(x + r)}`,
    `C${f(x + k)} ${f(y + h)} ${f(x)} ${f(y + h - k)} ${f(x)} ${f(y + h - r)}`,
    `V${f(y + r)}`,
    `C${f(x)} ${f(y + k)} ${f(x + k)} ${f(y)} ${f(x + r)} ${f(y)}`, 'Z',
  ].join(' ');
}

/** rounded equilateral-ish triangle, pointing up */
export function triangle(cx, cy, s, r = 60) {
  const h = s * 0.866;
  const P = [[cx, cy - h * 0.6], [cx + s / 2, cy + h * 0.4], [cx - s / 2, cy + h * 0.4]];
  const out = [];
  for (let i = 0; i < 3; i++) {
    const p = P[i], a = P[(i + 2) % 3], b = P[(i + 1) % 3];
    const da = Math.hypot(a[0] - p[0], a[1] - p[1]), db = Math.hypot(b[0] - p[0], b[1] - p[1]);
    const p1 = [p[0] + ((a[0] - p[0]) / da) * r, p[1] + ((a[1] - p[1]) / da) * r];
    const p2 = [p[0] + ((b[0] - p[0]) / db) * r, p[1] + ((b[1] - p[1]) / db) * r];
    out.push(`${i === 0 ? 'M' : 'L'}${f(p1[0])} ${f(p1[1])}`, `Q${f(p[0])} ${f(p[1])} ${f(p2[0])} ${f(p2[1])}`);
  }
  return out.join(' ') + ' Z';
}

/** funnel: wide top at yTop, neck at yNeck, stem down to yBottom */
export function funnel(cx, yTop, wTop, yNeck, wNeck, yBottom) {
  const a = wTop / 2, n = wNeck / 2;
  return [
    `M${f(cx - a)} ${f(yTop)}`, `H${f(cx + a)}`,
    `C${f(cx + a)} ${f(yTop + 120)} ${f(cx + n)} ${f(yNeck - 140)} ${f(cx + n)} ${f(yNeck)}`,
    `V${f(yBottom)}`, `H${f(cx - n)}`, `V${f(yNeck)}`,
    `C${f(cx - n)} ${f(yNeck - 140)} ${f(cx - a)} ${f(yTop + 120)} ${f(cx - a)} ${f(yTop)}`, 'Z',
  ].join(' ');
}

/** almond eye; open = 0..1 */
export function eye(cx, cy, w, h) {
  return `M${f(cx - w / 2)} ${f(cy)} C${f(cx - w / 4)} ${f(cy - h)} ${f(cx + w / 4)} ${f(cy - h)} ${f(cx + w / 2)} ${f(cy)} C${f(cx + w / 4)} ${f(cy + h)} ${f(cx - w / 4)} ${f(cy + h)} ${f(cx - w / 2)} ${f(cy)} Z`;
}

/** road band with speed bumps */
export function road(y, bumps = [300, 540, 780], bh = 70, bw = 150, x0 = 40, x1 = 1040, th = 16) {
  const top = [`M${x0} ${y}`];
  for (const b of bumps) {
    top.push(`H${f(b - bw / 2)}`, `C${f(b - bw / 4)} ${f(y)} ${f(b - bw / 4)} ${f(y - bh)} ${f(b)} ${f(y - bh)}`,
      `C${f(b + bw / 4)} ${f(y - bh)} ${f(b + bw / 4)} ${f(y)} ${f(b + bw / 2)} ${f(y)}`);
  }
  top.push(`H${x1}`, `V${y + th}`, `H${x0}`, 'Z');
  return top.join(' ');
}
/** height of the road surface at x (matches road()) */
export function roadY(x, y, bumps = [300, 540, 780], bh = 70, bw = 150) {
  for (const b of bumps) {
    const d = Math.abs(x - b);
    if (d < bw / 2) return y - bh * (0.5 + 0.5 * Math.cos((d / (bw / 2)) * Math.PI));
  }
  return y;
}

/** gauge arc band (upper half) */
export function arcBand(cx, cy, R, th) {
  const r = R - th;
  return `M${f(cx - R)} ${f(cy)} A${R} ${R} 0 0 1 ${f(cx + R)} ${f(cy)} L${f(cx + r)} ${f(cy)} A${r} ${r} 0 0 0 ${f(cx - r)} ${f(cy)} Z`;
}

export function star4(cx, cy, R, r) {
  const p = [];
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? r : R;
    p.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]);
  }
  // concave star: quadratic curves pulled to centre
  let d = `M${f(p[0][0])} ${f(p[0][1])}`;
  for (let i = 0; i < 8; i += 2) {
    const n = p[(i + 2) % 8];
    d += ` Q${f(p[i + 1][0])} ${f(p[i + 1][1])} ${f(n[0])} ${f(n[1])}`;
  }
  return d + ' Z';
}

export function hexagon(cx, cy, R) {
  const p = [];
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 - Math.PI / 2;
    p.push(`${i ? 'L' : 'M'}${f(cx + Math.cos(a) * R)} ${f(cy + Math.sin(a) * R)}`);
  }
  return p.join(' ') + ' Z';
}

/** human bust silhouette (head + shoulders) as a compound path */
export function human(cx, cy, s = 1) {
  const hr = 105 * s, hy = cy - 190 * s;
  const sw = 300 * s, top = cy - 40 * s, bot = cy + 260 * s;
  const body = [
    `M${f(cx - sw)} ${f(bot)}`,
    `C${f(cx - sw)} ${f(top + 60 * s)} ${f(cx - sw * 0.55)} ${f(top)} ${f(cx)} ${f(top)}`,
    `C${f(cx + sw * 0.55)} ${f(top)} ${f(cx + sw)} ${f(top + 60 * s)} ${f(cx + sw)} ${f(bot)}`, 'Z',
  ].join(' ');
  return circle(cx, hy, hr) + ' ' + body;
}

/** infinity / lemniscate */
export function infinity(cx, cy, w, h) {
  const a = w / 2, b = h / 2;
  return [
    `M${f(cx)} ${f(cy)}`,
    `C${f(cx + a * 0.35)} ${f(cy - b * 1.25)} ${f(cx + a)} ${f(cy - b * 1.25)} ${f(cx + a)} ${f(cy)}`,
    `C${f(cx + a)} ${f(cy + b * 1.25)} ${f(cx + a * 0.35)} ${f(cy + b * 1.25)} ${f(cx)} ${f(cy)}`,
    `C${f(cx - a * 0.35)} ${f(cy - b * 1.25)} ${f(cx - a)} ${f(cy - b * 1.25)} ${f(cx - a)} ${f(cy)}`,
    `C${f(cx - a)} ${f(cy + b * 1.25)} ${f(cx - a * 0.35)} ${f(cy + b * 1.25)} ${f(cx)} ${f(cy)}`, 'Z',
  ].join(' ');
}

export function pills(cx, ys, w, h) {
  return ys.map((y) => roundRect(cx, y, w, h, h / 2)).join(' ');
}

/** security shield: shoulders at the top, curving to a point */
export function shield(cx, cy, w, h) {
  const x0 = cx - w / 2, x1 = cx + w / 2, y0 = cy - h / 2, y1 = cy + h / 2;
  return [
    `M${f(cx)} ${f(y0)}`,
    `C${f(cx + w * 0.22)} ${f(y0 + h * 0.07)} ${f(x1 - w * 0.12)} ${f(y0 + h * 0.08)} ${f(x1)} ${f(y0 + h * 0.08)}`,
    `C${f(x1)} ${f(y0 + h * 0.45)} ${f(x1 - w * 0.08)} ${f(y1 - h * 0.22)} ${f(cx)} ${f(y1)}`,
    `C${f(x0 + w * 0.08)} ${f(y1 - h * 0.22)} ${f(x0)} ${f(y0 + h * 0.45)} ${f(x0)} ${f(y0 + h * 0.08)}`,
    `C${f(x0 + w * 0.12)} ${f(y0 + h * 0.08)} ${f(cx - w * 0.22)} ${f(y0 + h * 0.07)} ${f(cx)} ${f(y0)}`, 'Z',
  ].join(' ');
}
