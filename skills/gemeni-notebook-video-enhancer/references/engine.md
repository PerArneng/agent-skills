# Engine reference

This covers the project files (`motion/`) created by `scaffold.sh`:

```
config.json         source, output, width, height, fps, scale (render ×N), duration   ← single source of truth
index.html          #stage > canvas#bg, #world > (svg#fx with #hero path), div#ui ; #grain ; #vignette
src/main.js         builds the timeline from scenes/index.js, exposes window.seek(t) / window.ready / window.STAGE, preview playback
src/lib.js          helpers (below)
src/shapes.js       SVG path generators for the hero morph
src/bg.js           Three.js fbm/domain-warp shader background, colours driven by bgState
src/style.css       tokens, .glass / .glass-lite / .chip / .badge / .title / .cursor / .grad-text
src/scenes/*.js     one module per beat; each default-exports a function that registers tweens and drivers
render.mjs, shot.mjs
```

## Contents
1. The two animation mechanisms and the determinism rules
2. lib.js API
3. shapes.js API
4. Styling primitives
5. Patterns and snippets

---

## 1. The two animation mechanisms and the determinism rules

Every frame is produced by `seek(t)`, which runs `tl.seek(t)`, then every driver `d(t)`, then the background shader for `t`. Frames are rendered in parallel, out of order, by several browser pages. So **the image at time t must be a pure function of t.**

**A. GSAP timeline tweens** (`tl.to(target, vars, atSeconds)`)
- Use them for entrances, exits, state changes, morphs, colours and anything else with an ease.
- Always place them at **absolute seconds**, taken from the transcript cue.
- Prefer `tl.to` with the initial state set by `gsap.set` / `place()` at build time. Don't use `from`/`fromTo` with `immediateRender` on elements that get several tweens: several immediate renders on one element overwrite each other's starting values.
- `main.js` runs `tl.progress(1).progress(0)` after all scenes are built. That records every tween's start values in order, which is what makes backward seeks exact.
- **Don't use GSAP callbacks** (`onUpdate`, `onComplete`, `tl.call`) or `tl.set` on non-CSS properties such as `textContent`: they don't reverse. Use a driver for text instead.

**B. Drivers** (`drive(t => { ... })`)
- Use them for procedural motion: swarms, particles, conveyor streams, counters, orbiting items, flowing dashes, jitter/glitch, and text that depends on t.
- A driver must depend only on `t` and constants, plus the values of plain objects that GSAP tweens (e.g. `const gv = {v:0}; tl.to(gv, {v:.87}, 75.5)`, then read `gv.v` inside a driver). Drivers run after `tl.seek`, so those values are already current.
- For randomness, use `mulberry32(seed)` at build time, or `hash(frameIndex)` for per-frame noise. Never use `Math.random()` or `Date.now()`.

**One owner per property.** GSAP caches transforms, so if a driver writes `style.transform` on an element that GSAP also tweens, GSAP will later overwrite it from its stale cache. Pick one of these:
- The element is *driver-owned*: the driver writes the whole `style.transform` string (e.g. ``translate(${x}px,${y}px) translate(-50%,-50%) scale(${s})``) plus opacity and display, and GSAP never touches it.
- The element is *GSAP-owned*, and the driver only writes the independent CSS `translate` property, which is what `float()` does. `translate` composes with GSAP's transform.
- **Don't set CSS `scale` or `rotate` on a GSAP-placed element.** Those properties pivot around the element's untransformed box at the top-left of the stage, so the element flies off-centre.
- To hand an element over from GSAP to a driver mid-scene, use two elements: fade the GSAP one out and show a driver-owned twin at the same spot. In the example, the orb becomes a ball in `example-scenes/s6_friction.js`.

**Other rules.**
- No CSS animations or transitions, and no `requestAnimationFrame` loops inside scenes. The only clock is `t`.
- Hide driver-owned elements that are off-screen with `display:none` to keep frames fast (the swarm pattern does this).
- `#world` is owned by the camera driver in `main.js` (slow drift and the end push-in), so don't tween it. `#heroG` may be tweened (opacity), or moved by a driver via `gsap.set('#heroG', {y})` (see the lift in s8).

## 2. lib.js API

`import { … } from '../lib.js'`

| helper | what it does |
|---|---|
| `W, H, FPS, DURATION` | stage size, frame rate and duration from `config.json`. Position everything relative to `W`/`H` so it works in both portrait and landscape. |
| `tl` | the master paused timeline |
| `drive(fn)` | registers a driver `fn(t)` |
| `el(tag, cls, parent?, html?)` | creates an element; the parent defaults to `#ui` |
| `place(e, x, y, props?)` | `gsap.set` with the element centred on (x,y) (`xPercent/yPercent -50`); later `x`/`y` tweens are also centre coordinates |
| `pop(targets, t, {dur, stagger, ease, scale, blur})` | hidden → springy entrance at t (opacity + scale + blur) |
| `out(targets, t, {dur, stagger, scale, blur, y})` | blur, shrink and fade exit at t |
| `float(e, {amp, speed, seed})` | gentle idle drift through CSS `translate` (safe on GSAP-owned elements) |
| `sceneTitle(num, name, tIn, tOut)` | glass pill at the top with a number badge and per-character reveal |
| `morph(t, pathD, dur=0.9, ease='power3.inOut')` | morphs the hero outline to a new shape (GSAP MorphSVG) |
| `heroColor(t, c1, c2, c3, dur)` | tweens the hero stroke gradient; the gradient also rotates slowly on its own |
| `bgTo(t, deep, cool, warm, energy=0.5, dur=1.4)` | tweens the shader palette; `energy` (0–1) sets flow speed and iridescence. Use a warm/red palette with high energy for "problem" beats and a cool/teal palette with low energy for "solution/calm" beats. |
| `click(x, y, tArrive, tClick, moveDur)` | moves the shared cursor to (x,y) and clicks with a ripple at `tClick` |
| `cursorHide(t)` | fades the cursor out |
| `icon(name, strokeWidth=2)` | inline SVG for any lucide icon (`'triangle-alert'`, `'bell'`, …) or an alias (`alert, user, sparkles, cpu, file, route, listChecks, hand, gauge, shieldAlert, brain, bot, …`); inherits `currentColor` |
| `mulberry32(seed)`, `hash(n)` | deterministic randomness |
| `clamp, lerp, prog(t,a,b), env(t,a,b,fin,fout)` | `prog` is a 0→1 ramp over [a,b]; `env` is a soft on/off window |
| `E.outCubic / inCubic / inOutCubic / outExpo / inOutSine / outBack` | easing functions for drivers |
| `gsap` | re-exported, with MorphSVG and DrawSVG registered (`drawSVG: '0%'` → `'100%'` draws strokes) |
| `svgLayer(z)`, `svgEl(tag, attrs, parent)` | a full-stage `<svg>` inside `#ui` (for connectors, gauges, cracks) and a shorthand for creating SVG elements in it. Animate the layer's opacity/blur, not the inner groups. |
| `flow(paths, speed)` | flowing dashes: a driver that offsets `stroke-dashoffset` on paths that have a `stroke-dasharray` |
| `stamp(e, t, rot)` | slams an element in from scale 2.2 (for "UNVERIFIED", "BLOCKED", a ✕ icon) |
| `typeText(e, text, t0, t1)` | text typed out by a driver, with a blinking caret |
| `inlineSvg(raw, width, parent?)` | inlines an SVG (usually a brand logo imported with `?raw` from `src/assets/`), prefixes ids and strips inline transforms. Returns `{ wrap, svg, parts }`: place/scale `wrap`, and stagger `parts` (wordmark letters) with `y`/`opacity` for a reveal. |

## 3. shapes.js API

These return path `d` strings in stage coordinates, ready for `morph()`. MorphSVG handles different point counts and compound paths (several sub-paths), so any shape can morph into any other.

- `circle(cx,cy,r)`, `roundRect(cx,cy,w,h,r)`, `bubble(cx,cy,w,h,r)` (speech bubble), `triangle(cx,cy,size,cornerR)`
- `funnel(cx, yTop, wTop, yNeck, wNeck, yBottom)`, `eye(cx,cy,w,h)`, `hexagon(cx,cy,R)`, `star4(cx,cy,R,r)`
- `shield(cx,cy,w,h)` (security, safety, compliance)
- `road(y, bumps[], bumpH, bumpW)` plus `roadY(x, …)`, which gives the surface height so a driver can roll a ball over it
- `arcBand(cx,cy,R,thickness)` (a gauge), `human(cx,cy,scale)` (head + shoulders), `infinity(cx,cy,w,h)`, `pills(cx, ys[], w, h)` (a stack of pills; compound)

To add a new shape, write another generator using cubic `C`/quadratic `Q` segments and close it with `Z`. Closed shapes morph best. Anything symbolic (an arrow, a shield, a lightbulb, a globe, a chart bar group) is fair game.

## 4. Styling primitives (style.css)

- **Colour tokens:** `--cyan --violet --pink --amber --red --green --ink --muted`.
- `.panel` is a flat 2D card with a hairline border. Use it instead of `.glass` for a professional or corporate look. `.tag` is a small mono label; `.stamp` is a bordered mono stamp.
- **Font tokens:** `--head` (Space Grotesk), `--body` (Inter), `--mono` (JetBrains Mono). They are bundled locally, so no network is needed at render time.
- `.glass` is a frosted card with `backdrop-filter`. Use it for up to about 10 large elements on screen at once.
- `.glass-lite` is an opaque look-alike with no backdrop blur. Use it for swarms and streams of dozens of small cards, where backdrop blur would make rendering slow.
- `.chip` (pill label with `.ico`), `.badge` (red notification counter), `.title` (scene title), `.grad-text`, `.cursor`, `.ripple`.
- Set sizes inline with `style.cssText += '…'`. Don't write `style.cssText = '…'` on elements that have a class, because it wipes out class-applied inline state; only use `=` on plain elements.

## 5. Patterns and snippets

**Counter text from a tweened value.**
```js
const st = { v: 0 }; tl.to(st, { v: 247, duration: 3, ease: 'power2.in' }, 7.0);
drive(() => (badge.textContent = Math.round(st.v)));
```

**Swarm or stream** (driver-owned, spawn times spread across a window).
```js
const items = Array.from({length: 60}, (_, i) => ({ e: el('div','abs glass-lite'), ts: 7 + 4 * (i/60) ** 0.8, tx: …, ty: … }));
drive(t => items.forEach(c => {
  const p = E.outExpo(prog(t, c.ts, c.ts + 0.9));
  if (t < c.ts) return (c.e.style.display = 'none');
  c.e.style.display = 'flex';
  c.e.style.transform = `translate(${lerp(x0,c.tx,p)}px,${lerp(y0,c.ty,p)}px) translate(-50%,-50%) scale(${lerp(.3,1,p)})`;
  c.e.style.opacity = Math.min(1, p * 3);
}));
```
Add a later "converge" ramp that `lerp`s the swarm into the next scene's layout. That handoff is how scenes flow into each other.

**Glitch** (per-frame noise inside an `env` window):
```js
drive(t => { const g = env(t, 3.0, 4.4, .05, .3); const f = Math.floor(t*30);
  const dx = (hash(f)-.5)*26*g; res.style.textShadow = `${-8*g+dx}px 0 #22d3ee, ${8*g-dx}px 0 #ff006e`; });
```

**Flowing dashes along connectors:** give the SVG path `stroke-dasharray="4 40"`, then in a driver run `path.setAttribute('stroke-dashoffset', -t*90)`.

**Particles along the hero outline:** in a driver, `const L = hero.getTotalLength(); hero.getPointAtLength(((t*speed + i/n) % 1) * L)`.

**3D object:** use a `perspective` wrapper around a `transform-style:preserve-3d` cube whose faces use `translateZ(var(--z))`. Tween `'--z'` on the cube to explode it, and rotate it from a driver (see s7).

**Cursor-driven UI story:** open a dropdown with `tl.to(opts,{height})`, click with `click()` on each target, and switch text with a driver. Check the click coordinates with `shot.mjs`: layout positions inside cards are easy to misjudge.
