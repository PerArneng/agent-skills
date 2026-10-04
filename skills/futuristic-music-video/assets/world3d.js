// world3d.js: the 3D layer of the overlay (three.js). LINE GRAPHICS ONLY: lines, ticks, rings, grids and dots
// that live in 3D, plus "panels" (the overlay's own 2D drawings on planes) that can tilt and swing in 3D.
// No lit or shaded surfaces: everything is additive lines/points in the palette, so it reads as the same
// HUD language as the 2D layers, just with depth.
//
// The overlay owns time and music. Each frame it builds a STATE object from t (loudness, story, drop / break /
// hit-run ages, the active lyric scene, phase, panel poses) and calls world.seek(state). Nothing here reads a
// clock, keeps history or simulates, so frames can be rendered in any order and in parallel.
//
// Vocabulary (deliberately NO hero object: no sphere, blob or "physical" thing - ambient lines and dots only)
//   ribbons  3 bundles of 7 polylines twisting in depth (the 2D ribbon strands with a z axis)
//   floor    a perspective wire grid ("data landscape"); loudness heights, ripple ring on drops, collapse
//   swarm    ~3k agent dots on closed-form paths; lock onto a torus-knot loop, engulf = gather into a cloud
//   scenes   wireframe lyric scenes (SCENES3D): fired, crash, progress, won (racks/servers stay 2D: the 3D
//            version read as ugly boxes)
//   panels   named 2D canvases (full-frame, same size as the overlay) shown on planes that rotate about a pivot.
//            A FLAT pose is not rendered here: the overlay draws the canvas directly, pixel-exact. Only a tilted
//            pose goes through 3D, so "2D" really is 2D and the 3D swing is a smooth departure from it.
//
//   import { createWorld3D } from './world3d.js';
//   import { LineSegments2 } from 'three/addons/lines/LineSegments2.js'; (+ LineSegmentsGeometry, LineMaterial)
//   const world = createWorld3D({ THREE, LINES: { LineSegments2, LineSegmentsGeometry, LineMaterial }, canvas, W, H, DPR,
//                                scale, palette: C, layout, panels: { stage: cv1, hud: cv2 } });
// Lines are three's 'fat lines' (screen-space width in CSS px), because WebGL's native lines are always 1 px.
//   const { flat } = world.seek(state);   // then: g.drawImage(canvas, 0, 0, W, H); draw flat panels directly

const SWARM_VS = /* glsl */`
attribute vec4 aSeed;
uniform float uT, uDensity, uLock, uEngulf, uSize, uR, uCoreR, uRed, uDPR;
uniform vec3 uCore, uCool, uWarn, uAlarm;
varying vec3 vCol; varying float vOn;
vec3 knot(float s){ float a=s*6.2831853; float r=cos(3.0*a)+2.0; return vec3(r*cos(2.0*a), r*sin(2.0*a)*0.9, -sin(3.0*a))*0.33; }
void main(){
  float s = aSeed.x + uT*(0.025 + aSeed.y*0.045);
  vec3 f = vec3(sin(aSeed.x*40.0 + uT*0.30*(0.5+aSeed.y)), sin(aSeed.z*37.0 + uT*0.23), sin(aSeed.w*29.0 + uT*0.27));
  vec3 free = normalize(f + 1e-4)*(0.55 + aSeed.z*1.25)
            + 0.15*vec3(sin(uT*1.3+aSeed.w*20.0), cos(uT*1.1+aSeed.x*17.0), sin(uT*0.9+aSeed.y*13.0));
  vec3 path = knot(s) + 0.07*vec3(sin(aSeed.z*50.0+uT*2.0), cos(aSeed.w*50.0+uT*2.3), sin(aSeed.y*50.0+uT*1.7));
  vec3 p = mix(free, path*1.6, uLock)*uR;
  vec3 sph = normalize(p + 1e-4)*uCoreR*(1.05 + 0.2*aSeed.z);
  p = mix(p, sph, uEngulf*step(aSeed.w, 0.85));
  p += uCore;
  vOn = step(aSeed.y, uDensity);
  vec4 mv = viewMatrix*vec4(p,1.0);
  gl_PointSize = vOn*uSize*uDPR*(0.5 + aSeed.z)*30.0/(-mv.z);
  gl_Position = projectionMatrix*mv;
  vCol = mix(aSeed.w < 0.12 ? uWarn : uCool, uAlarm, uRed*step(0.35, aSeed.x));
}`;

const DOT_FS = /* glsl */`
uniform float uOpacity;
varying vec3 vCol; varying float vOn;
void main(){
  if (vOn < 0.5) discard;
  vec2 q = gl_PointCoord*2.0 - 1.0; float r = dot(q,q);
  if (r > 1.0) discard;
  float a = uOpacity*(0.25*exp(-r*3.0) + step(r, 0.25));        // crisp dot with a faint halo
  gl_FragColor = vec4(vCol*a, a);
}`;

export function createWorld3D({ THREE, LINES, canvas, W, H, DPR = 1, scale = 1, palette, layout, panels = {} }) {
  THREE.ColorManagement.enabled = false;                       // hex in = colour out, like the 2D canvas
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true,
                                             premultipliedAlpha: true, powerPreference: 'high-performance' });
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.setPixelRatio(1);
  renderer.setSize(Math.round(W * DPR * scale), Math.round(H * DPR * scale), false);
  renderer.setClearColor(0x000000, 0);
  const info = renderer.getContext().getExtension('WEBGL_debug_renderer_info');
  const glName = info ? renderer.getContext().getParameter(info.UNMASKED_RENDERER_WEBGL) : 'unknown';

  const scene = new THREE.Scene();
  const FOV = 28, VIEW_H = 10, CAMZ = VIEW_H / 2 / Math.tan(FOV / 2 * Math.PI / 180);
  const camera = new THREE.PerspectiveCamera(FOV, W / H, 0.1, 400);
  const px = (x, y, z = 0) => new THREE.Vector3((x - W / 2) / H * VIEW_H, (H / 2 - y) / H * VIEW_H, z);
  const pxLen = (l) => l / H * VIEW_H;
  const col = (hex) => new THREE.Color(hex);
  const DEFAULTS = { cool: '#7CFFE1', warn: '#FFB25A', alarm: '#FF3B3B', human: '#A46BFF', type: '#EDEFF2', dim: '#3A4650' };
  const P = Object.fromEntries(Object.entries({ ...DEFAULTS, ...palette }).filter(([, v]) => v).map(([k, v]) => [k, col(v)]));
  const hash = (i, s = 0) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ease = k => 1 - Math.pow(1 - clamp(k), 4);
  const lerp = (a, b, k) => a + (b - a) * k;
  const ADD = { transparent: true, depthWrite: false, depthTest: false, premultipliedAlpha: true,
                blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor };
  const lineMat = (c, o = {}) => new THREE.LineBasicMaterial({ color: c, ...ADD, ...o });
  const tmpC = new THREE.Color();
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const put = (arr, i, v) => { arr[i * 3] = v.x; arr[i * 3 + 1] = v.y; arr[i * 3 + 2] = v.z; };

  // fat lines: width in CSS px. fat(arr, colour, width) = static; dyn(nVerts, width) = rewritten each frame
  const { LineSegments2, LineSegmentsGeometry, LineMaterial } = LINES;
  const RES = new THREE.Vector2(W * DPR * scale, H * DPR * scale);
  const fatMat = (color, width, vertexColors = false) => {
    const m = new LineMaterial({ color, linewidth: width * DPR * scale, vertexColors, worldUnits: false });
    Object.assign(m, ADD); m.resolution.copy(RES); return m;
  };
  const fat = (arr, color, width) => {
    const o = new LineSegments2(new LineSegmentsGeometry().setPositions(arr), fatMat(color, width));
    o.frustumCulled = false; return o;
  };
  function dyn(n, width, color = 0xffffff) {
    const geo = new LineSegmentsGeometry(), obj = new LineSegments2(geo, fatMat(color, width, true));
    obj.frustumCulled = false;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    return { obj, pos, col, n, commit(count = n) {
      count -= count % 2;
      geo.setPositions(pos.subarray(0, Math.max(6, count * 3))); geo.setColors(col.subarray(0, Math.max(6, count * 3)));
    } };
  }

  // ---------- ribbons ----------
  const RIB = 3, STR = 7, RP = 160, ribbons = [];
  for (let b = 0; b < RIB; b++) for (let s = 0; s < STR; s++) { const l = dyn((RP - 1) * 2, s === 3 ? 3.2 : 1.3); scene.add(l.obj); ribbons.push({ b, s, l }); }

  // ---------- floor ----------
  const FX = 30, FZ = 18, floor = dyn((FX * FZ * 2) * 2, 1.3); scene.add(floor.obj);

  // ---------- swarm ----------
  const N_SWARM = 3000, seeds = new Float32Array(N_SWARM * 4);
  for (let i = 0; i < seeds.length; i++) seeds[i] = hash(i, 3.7);
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N_SWARM * 3), 3));
  sg.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 4));
  const swU = { uT: { value: 0 }, uDensity: { value: 0 }, uLock: { value: 0 }, uEngulf: { value: 0 }, uSize: { value: 3.2 },
    uR: { value: 1.6 }, uCoreR: { value: 1 }, uRed: { value: 0 }, uDPR: { value: DPR * scale }, uCore: { value: new THREE.Vector3() },
    uCool: { value: P.cool }, uWarn: { value: P.warn }, uAlarm: { value: P.alarm }, uOpacity: { value: 1 } };
  const swarm = new THREE.Points(sg, new THREE.ShaderMaterial({ uniforms: swU, vertexShader: SWARM_VS, fragmentShader: DOT_FS, ...ADD }));
  swarm.frustumCulled = false; scene.add(swarm);

  // ---------- panels: the overlay's 2D canvases on planes that can tilt ----------
  const PANELS = {};
  for (const [name, cv] of Object.entries(panels)) {
    const tex = new THREE.CanvasTexture(cv);
    tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    tex.colorSpace = THREE.NoColorSpace; tex.premultiplyAlpha = true;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(pxLen(W), pxLen(H)),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, depthTest: false,
        blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor }));
    const pivot = new THREE.Group(); pivot.add(mesh); scene.add(pivot);
    mesh.renderOrder = 10; mesh.frustumCulled = false;
    PANELS[name] = { tex, mesh, pivot };
  }
  const isFlat = (p) => !p || (Math.abs(p.rx || 0) + Math.abs(p.ry || 0) + Math.abs(p.rz || 0) < 2e-3 && Math.abs(p.z || 0) < 2e-3
                               && Math.abs((p.s ?? 1) - 1) < 2e-3);

  // ---------- wireframe lyric scenes ----------
  const stage = layout.stage;
  const sc = px(stage.x + stage.w / 2, stage.y + stage.h / 2), sw = pxLen(stage.w), shh = pxLen(stage.h);
  const SCENES3D = {};

  { // fired: 1,000 dots drop out in 3D and turn red
    const cols = 40, rows = 25, n = cols * rows, grp = new THREE.Group(), g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ size: 7 * DPR * scale, vertexColors: true, sizeAttenuation: false, ...ADD }));
    pts.frustumCulled = false; grp.add(pts); grp.visible = false; scene.add(grp);
    const sp = sw / cols;
    SCENES3D.fired = (s) => {
      grp.position.copy(sc); grp.position.y += shh * 0.1;
      grp.rotation.set(-0.15 - 0.55 * ease(s.age / 1.2), Math.sin(s.age * 0.5) * 0.3, 0);
      const pos = g.attributes.position.array, ca = g.attributes.color.array, gone = s.u * 1.2 * n;
      for (let i = 0; i < n; i++) {
        const a = clamp((gone - hash(i, 9) * n) / 80), fall = a * a * 4;
        put(pos, i, V((i % cols - cols / 2 + 0.5) * sp, -fall, (Math.floor(i / cols) - rows / 2) * sp * 1.1 + fall * 0.5));
        tmpC.copy(a > 0 ? P.alarm : P.type).multiplyScalar(s.k * (a > 0 ? 1 - a * 0.6 : 0.8));
        ca.set([tmpC.r, tmpC.g, tmpC.b], i * 3);
      }
      g.attributes.position.needsUpdate = g.attributes.color.needsUpdate = true;
    };
    SCENES3D.fired.group = grp;
  }
  { // crash: a line candlestick chart that starts flat (reads as 2D), tilts into perspective and plunges
    const n = 22, grp = new THREE.Group(), L = dyn(n * 10, 2.4); grp.add(L.obj); grp.visible = false; scene.add(grp);
    SCENES3D.crash = (s) => {
      const tilt = ease((s.u - 0.15) / 0.5), plunge = ease((s.u - 0.65) / 0.35);
      grp.position.copy(sc); grp.position.y -= plunge * shh * 0.25; grp.position.z = -plunge * 3;
      grp.rotation.set(-tilt * 1.0, tilt * 0.35, 0);
      const vals = [0];
      for (let i = 0; i < n; i++) vals.push(vals[i] + (i / n > 0.35 ? 0.10 + hash(i, 2) * 0.16 : -0.07 + hash(i, 2) * 0.1));
      const lo = Math.min(...vals), hi = Math.max(...vals), Y = (v) => shh * 0.42 - (v - lo) / (hi - lo) * shh * 0.84;
      const vis = ease(s.u * 1.6) * n, pos = L.pos, ca = L.col;
      let vi = 0;
      const seg = (a, b, c) => { put(pos, vi, a); ca.set([c.r, c.g, c.b], vi * 3); vi++; put(pos, vi, b); ca.set([c.r, c.g, c.b], vi * 3); vi++; };
      for (let i = 0; i < n; i++) {
        const show = clamp(vis - i), w = sw / n * 0.36, x = (i - n / 2 + 0.5) * sw / n;
        const o = Y(vals[i]), c = Y(vals[i + 1]), top = Math.max(o, c), bot = lerp(top, Math.min(o, c), show);
        const cc = tmpC.copy(vals[i + 1] > vals[i] ? P.alarm : P.cool).multiplyScalar(s.k * (show > 0 ? 1 : 0)).clone();
        seg(V(x - w, top, 0), V(x + w, top, 0), cc); seg(V(x + w, top, 0), V(x + w, bot, 0), cc);
        seg(V(x + w, bot, 0), V(x - w, bot, 0), cc); seg(V(x - w, bot, 0), V(x - w, top, 0), cc);
        seg(V(x, top + 0.12 * show, 0), V(x, bot - 0.12 * show, 0), cc);
      }
      L.commit();
    };
    SCENES3D.crash.group = grp;
  }
  { // progress: a ring of tick segments, flat at first, tilting into 3D as it fills
    const n = 60, grp = new THREE.Group(), L = dyn(n * 6, 2.6); grp.add(L.obj); grp.visible = false; scene.add(grp);
    SCENES3D.progress = (s) => {
      const p = ease(s.u * 1.25), R = Math.min(sw, shh) * 0.36;
      grp.position.copy(sc); grp.rotation.set(ease(s.u) * 1.05, 0, -s.age * 0.3);
      const pos = L.pos, ca = L.col;
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2, on = i / n < p, l = on ? 0.42 : 0.2;
        for (let k = 0; k < 3; k++) {
          const off = (k - 1) * 0.02, z = on ? (k - 1) * 0.1 : 0;
          put(pos, i * 6 + k * 2, V(Math.cos(a + off) * R, Math.sin(a + off) * R, z));
          put(pos, i * 6 + k * 2 + 1, V(Math.cos(a + off) * (R - l), Math.sin(a + off) * (R - l), z));
          tmpC.copy(on ? P.cool : P.dim).multiplyScalar(s.k);
          ca.set([tmpC.r, tmpC.g, tmpC.b, tmpC.r, tmpC.g, tmpC.b], (i * 6 + k * 2) * 3);
        }
      }
      L.commit();
    };
    SCENES3D.progress.group = grp;
  }
  { // won: a grid of square outlines flipping around X, human purple -> agent teal
    const cols = 14, rows = Math.max(8, Math.round(cols * shh / sw)), n = cols * rows, grp = new THREE.Group();
    const L = dyn(n * 8, 2.0); grp.add(L.obj); grp.visible = false; scene.add(grp);
    SCENES3D.won = (s) => {
      grp.position.copy(sc); grp.rotation.set(-0.5 * ease(s.age / 1.0), Math.sin(s.age * 0.3) * 0.12, 0);
      const p = ease(s.u * 1.3), sp = sw / cols, h = sp * 0.4;
      const pos = L.pos, ca = L.col;
      for (let i = 0; i < n; i++) {
        const fl = clamp((p - hash(i, 11)) / 0.12), a = fl * Math.PI;
        const cx = (i % cols - cols / 2 + 0.5) * sp, cy = (rows / 2 - Math.floor(i / cols) - 0.5) * sp;
        const cs = Math.cos(a), sn = Math.sin(a);
        const c4 = [[-h, -h], [h, -h], [h, h], [-h, h]].map(([x, y]) => V(cx + x, cy + y * cs, y * sn));
        tmpC.copy(fl > 0.5 ? P.cool : P.human).multiplyScalar(s.k);
        for (let e = 0; e < 4; e++) {
          put(pos, i * 8 + e * 2, c4[e]); put(pos, i * 8 + e * 2 + 1, c4[(e + 1) % 4]);
          ca.set([tmpC.r, tmpC.g, tmpC.b, tmpC.r, tmpC.g, tmpC.b], (i * 8 + e * 2) * 3);
        }
      }
      L.commit();
    };
    SCENES3D.won.group = grp;
  }

  // ---------- per-frame ----------
  function seek(S) {
    const t = S.t, red = S.red || 0;
    const sh = S.cam?.shake || 0, si = Math.floor(t * 30);
    camera.position.set((hash(si, 1) - 0.5) * 0.3 * sh, (hash(si, 2) - 0.5) * 0.3 * sh, CAMZ - (S.cam?.push || 0));
    camera.lookAt(camera.position.x, camera.position.y, 0);

    // ribbons: 3 bundles of strands twisting in depth
    const rb = S.ribbon || {}, L = S.loud || 0, len = pxLen(W) * 1.3;
    for (const { b, s, l } of ribbons) {
      l.obj.visible = (rb.on || 0) > 0.001;
      if (!l.obj.visible) continue;
      const ph = b * 2.1, base = px(W / 2, layout.ribbonY + b * 22);
      const amp = (0.35 + 1.5 * L) * (0.7 + 0.3 * Math.sin(t * 0.7 + b));
      const cc = tmpC.copy(b === 1 ? P.warn : P.cool).lerp(P.alarm, red * (b === 2 ? 1 : 0.5)).multiplyScalar(rb.on * (s === 3 ? 0.95 : 0.22 + 0.05 * s)).clone();
      let prev = null, vi = 0;
      for (let i = 0; i < RP; i++) {
        const u = i / (RP - 1), x = (u - 0.5) * len;
        const tw = u * 4.0 + t * 0.9 + ph + s * 0.25;
        const spread = (s - (STR - 1) / 2) * (0.035 + 0.05 * L);
        const y = Math.sin(u * 5.0 + t * 1.5 + ph) * 0.35 * amp + Math.sin(u * 11.0 - t * 2.3 + ph * 2) * 0.1 * amp
                - (S.doom || 0) * u * 0.6 + Math.cos(tw) * spread;
        const z = Math.sin(tw) * spread * 3 + Math.sin(u * 3 + t * 0.6 + ph) * 0.8;
        const v = V(base.x + x, base.y + y, z), f = Math.min(1, u * 8, (1 - u) * 8);   // fade the ends
        if (prev) {
          put(l.pos, vi, prev.v); l.col.set([cc.r * prev.f, cc.g * prev.f, cc.b * prev.f], vi * 3); vi++;
          put(l.pos, vi, v); l.col.set([cc.r * f, cc.g * f, cc.b * f], vi * 3); vi++;
        }
        prev = { v, f };
      }
      l.commit(vi);
    }

    // floor: perspective wire grid, loudness heights, ripple on drops
    const F = S.floor || {};
    floor.obj.visible = (F.on || 0) > 0.001;
    if (floor.obj.visible) {
      const fy = px(W / 2, layout.floor.y), wide = pxLen(W) * 1.8, deep = 10;
      floor.obj.position.set(0, fy.y, 0);
      floor.obj.rotation.set(0.05 + (F.tilt || 0), 0, 0);
      const pos = floor.pos, ca = floor.col;
      const rip = F.ripple || { age: 1e9, s: 0 }, col0 = tmpC.clone().copy(P.cool).lerp(P.alarm, red);
      const hgt = (gx, gz) => {
        const x = (gx / (FX - 1) - 0.5) * wide, z = -gz / (FZ - 1) * deep, d = Math.hypot(x, z + deep * 0.25);
        let y = (0.08 + 0.4 * L) * Math.sin(x * 1.3 + t * 1.2) * Math.cos(z * 0.9 - t * 0.8) * (1 - (F.collapse || 0));
        y += rip.s * Math.exp(-rip.age * 2.2) * Math.sin(d * 3 - rip.age * 14) * Math.exp(-Math.max(0, d - rip.age * 6) * 0.8) * 0.5;
        y -= (F.collapse || 0) * Math.pow(d / 6, 2) * 2;
        return V(x, y, z);
      };
      let vi = 0;
      const vtx = (v, f) => { put(pos, vi, v); ca.set([col0.r * F.on * f, col0.g * F.on * f, col0.b * F.on * f], vi * 3); vi++; };
      for (let gz = 0; gz < FZ; gz++) for (let gx = 0; gx < FX - 1; gx++) { const f = 1 - gz / FZ; vtx(hgt(gx, gz), f); vtx(hgt(gx + 1, gz), f); }
      for (let gx = 0; gx < FX; gx++) for (let gz = 0; gz < FZ - 1; gz++) { vtx(hgt(gx, gz), 1 - gz / FZ); vtx(hgt(gx, gz + 1), 1 - (gz + 1) / FZ); }
      floor.commit(vi);
    }

    // swarm
    const w = S.swarm || {};
    swarm.visible = (w.density || 0) > 0.001;
    if (swarm.visible) {
      swU.uT.value = t; swU.uDensity.value = w.density; swU.uLock.value = w.lock || 0; swU.uEngulf.value = w.engulf || 0;
      swU.uRed.value = red; swU.uOpacity.value = w.opacity ?? 0.8;
      const sc0 = layout.swarmCenter || { x: W / 2, y: H / 2, r: Math.min(W, H) * 0.18 };
      swU.uCore.value.copy(px(sc0.x, sc0.y)); swU.uCoreR.value = pxLen(sc0.r);
      swU.uR.value = pxLen(layout.swarmR ?? Math.min(W, H) * 0.45);
    }

    // wireframe scenes
    for (const fn of Object.values(SCENES3D)) fn.group.visible = false;
    if (S.scene && SCENES3D[S.scene.name] && S.scene.k > 0.001) {
      SCENES3D[S.scene.name].group.visible = true;
      SCENES3D[S.scene.name]({ ...S.scene, t });
    }

    // panels: only tilted ones are rendered here; flat ones the overlay draws directly (pixel-exact)
    const flat = {};
    for (const [name, Pn] of Object.entries(PANELS)) {
      const pose = S.panels?.[name];
      flat[name] = isFlat(pose);
      Pn.pivot.visible = !flat[name] && (pose?.opacity ?? 1) > 0.001;
      if (!Pn.pivot.visible) continue;
      const pv = px(pose.px ?? W / 2, pose.py ?? H / 2), c = px(W / 2, H / 2);
      Pn.pivot.position.set(pv.x, pv.y, pose.z || 0);
      Pn.pivot.rotation.set(pose.rx || 0, pose.ry || 0, pose.rz || 0);
      Pn.pivot.scale.setScalar(pose.s ?? 1);
      Pn.mesh.position.set(c.x - pv.x, c.y - pv.y, 0);
      Pn.mesh.material.opacity = pose.opacity ?? 1;
      Pn.tex.needsUpdate = true;
    }
    renderer.render(scene, camera);
    return { flat };
  }
  return { seek, has: (name) => !!SCENES3D[name], renderer: glName, px, pxLen };
}
