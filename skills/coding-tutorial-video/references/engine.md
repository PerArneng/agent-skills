# Engine reference

## Contents
1. Layout of the workspace
2. How a frame is made (determinism rules)
3. Timing API (narration-driven)
4. Motion helpers (lib.js)
5. Components (ui.js): FlowMap, ringLayout, CodePanel, Terminal, small pieces, segTitle, retrieval
6. Layout conventions (1920×1080 stage)
7. Recipes
8. Review, render, verify

---

## 1. Workspace (created by `scripts/scaffold.sh`)

```
video/
  script.py            the lesson: PROJECT config, EPISODE_TITLES, EPISODES (scenes → beats)
  beats.py             Beat / Scene / b() / ask()
  tts.py               Gemini TTS + cache (provider isolated here)
  build_audio.py       takes → split → pace → build/audio/<scene>.wav, build/timeline.json
  check_narration.py   transcribe each beat, flag mismatches with the script
  assemble.py          episode audio + web/src/data/<ep>.json (+ --estimate storyboard mode)
  finalize.py          chapters, sidecar captions, joined series
  whisper_words.py     word timestamps (mlx-whisper / faster-whisper)
  example/, captures/  the example lesson's project + real output (replace with yours)
  web/
    config.json        stage 1920×1080, fps 60, scale 2 (→ 3840×2160), episodes {duration, audio, output}
    src/main.js        loads data/<ep>.json + episodes/<ep>.js, exposes window.seek(t), preview playback
    src/lib.js         timeline, drivers, timing API, motion helpers, icons, palette C
    src/ui.js          components
    src/style.css      palette tokens (--bg --struct --ink --accent --amber --source …), panels
    src/episodes/ep1.js   one module per episode (default export builds its timeline)
    src/data/          generated: <ep>.json (beats, words), source.json (code + captures)
    render.mjs         parallel frame renderer → out/<slug>_<ep>_4k.mp4
    shot.mjs           contact sheets for review
```

The episode module is where your creative work goes. Episode ids (`ep1`…) must match keys
of `EPISODES` in `script.py`; beat ids used in `word()`/`B()` must exist there.

## 2. How a frame is made

`seek(t)` runs `tl.seek(t)` (the master GSAP timeline), then every driver `d(t)`. Frames are
rendered out of order by several browser pages, so **the image at time t must be a pure
function of t**:
- Place tweens at absolute seconds: `tl.to(target, vars, t)`. Set initial state with
  `gsap.set` / `place()` at build time. Avoid `from/fromTo` with immediateRender on elements
  that get several tweens.
- No GSAP callbacks (`onUpdate`, `onComplete`, `tl.call`), no CSS animations/transitions, no
  `requestAnimationFrame`, no `Math.random()`/`Date.now()`. Text that depends on t (typing,
  counters) is written by a driver: `const v = {n:0}; tl.to(v, {n:19, duration:2}, t); drive(() => el.textContent = Math.round(v.n))`.
- One owner per property: an element is either tweened by GSAP or written by a driver.
- `main.js` calls `tl.progress(1).progress(0)` after building so backward seeks are exact.

## 3. Timing API (lib.js)

The narration decides time. `assemble.py` writes, per beat: `start` (anticipation begins),
`v0`/`v1` (voice start/end), `end` (after hold/silence), `words` (Whisper times).

| call | returns |
|---|---|
| `B('beatId')` | `{ start, v0, v1, end, silence, words, say, ask }` |
| `at('beatId', f)` | time at fraction `f` of the beat's voice |
| `word('beatId', 'word', nth = 0, lead = 0.15)` | time the word is spoken, minus a small lead so the change has landed when the word is heard. Matches prefixes and digits ("five" ↔ "5"); falls back to the word's position in the sentence (with a console warning) if Whisper didn't hear it |
| `seam('sceneId').t` | start of the settled seam before a scene (segment title time) |

Tips: check warnings in the page console (`node shot.mjs` prints them); if a cue word was
merged or misheard (e.g. "evals" → "e", "vals"; "uvicorn" → "uvacorn"), cue on the heard form
or a neighbouring word. In `--estimate` mode all cues are estimated (warnings suppressed).

## 4. Motion helpers (lib.js)

| helper | effect |
|---|---|
| `show(targets, t, { dur = .6, y = 12, stagger })` | eased settle-in (opacity + small rise). Use `y: 0` for in-place |
| `hide(targets, t, { dur = .5 })` | eased fade out |
| `fadeTo(targets, t, opacity, dur)` | dim/undim |
| `moveTo(target, t, { x, y, scale, … }, dur = .9)` | eased move of a GSAP-placed element (centre coords) |
| `place(el, x, y, props)` | set position centred on (x, y) |
| `el(tag, cls, parent?, html?)`, `svgLayer(z)`, `svgEl(tag, attrs, parent)` | DOM/SVG creation |
| `icon(lucideName)` | inline SVG string of any lucide icon (https://lucide.dev/icons) |
| `C.accent / C.amber / C.source / C.struct / C.muted / C.ink / C.panel / C.bg` | palette (matches style.css) |
| `EASE` | 'power2.inOut' — slow-in/slow-out for anything meaningful |

## 5. Components (ui.js)

### FlowMap — the persistent system diagram

```js
const map = new FlowMap({
  x: 960, y: 540, scale: 1,          // placement on the stage; node coords are map-local
  nodes: [
    { id: 'ctl', x: -420, y: 0, shape: 'icon', icon: 'laptop', label: 'control node' },
    { id: 'inv', x: 0, y: -200, shape: 'stack', count: 3, label: 'inventory', labelAt: 'top' },
    { id: 'host', x: 420, y: 0, shape: 'box', label: 'managed host' },
  ],
  edges: [
    { id: 'ssh', from: 'ctl', to: 'host', bend: 0 },          // curve between node borders
    { id: 'read', from: 'ctl', to: 'inv', bend: 0.2 },
  ],
});
```
Shapes: `box` (rounded, with a core dot; `core:false` to omit; `w`,`h`), `hex` (`r`, `count`),
`stack` (`count`, `w`), `circle` (`r`), `icon` (`icon`, `size`). `labelAt`: top/bottom/left/right.
Ring edges: `{ from, to, ring: { R, cx, cy }, gap }` draw a clockwise arc (loops).

| method | |
|---|---|
| `state(t, ids, 'idle'|'live'|'done'|'source'|'dim', dur)` | restyle nodes and/or edges (colour travels with the object) |
| `travel(t0, t1, edgeId | [edgeIds], color?)` | token moves along one edge or a chain, eased as one motion |
| `glide(t0, t1, [x0,y0], [x1,y1], color?)` | token moves in a straight line (e.g. exits to an answer card) |
| `fade(t, ids, opacity)`, `hideNow(ids)` | build the cast one part at a time |
| `showLabels(t, on, ids?)` | labels on/off (hide during retrieval) |
| `moveTo(t, { x, y, scale }, dur)` | dock as mini-map / return to centre |
| `opacity(t, o)`, `all()`, `nodes[id]`, `edges[id]`, `labels[id]` | |
| `stageXY(id, placement)` | a node's stage coordinates for a given placement (to connect HTML elements) |

`ringLayout(ids, { R = 250, start = 90, shapes, labels })` returns `{ nodes, edges }` for a loop:
ids evenly on a circle, clockwise from the top, edges named `a>b`.
```js
const { nodes, edges } = ringLayout(['model', 'tools', 'messages'], { shapes: { tools: { shape: 'hex', count: 2 }, messages: { shape: 'stack' } } });
const loop = new FlowMap({ nodes, edges });
loop.travel(t, t + 3, ['model>tools', 'tools>messages', 'messages>model']);
```
Adjust an arc's `gap` (radians, default 0.3) if a large node overlaps its arcs.

### CodePanel — a real file

```js
const p = new CodePanel(SRC.code['site.yml'], { name: 'site.yml', from: 1, to: 40, rows: 16,
  x: 1110, y: 560, width: 1320, fs: 24, lh: 38, lang: 'yaml',         // lang inferred from name if omitted
  lights: { 7: ['become: true'], 12: ['ansible.builtin.apt'] } });  // file line → substrings you'll light
p.show(t, dur);   p.focus(t, a, b);   p.light(t, line, 'substring');   p.dimLine(t, line, .1)
p.mark(t, a, b, tOff)   // amber if–then box around lines
p.unfocus(t);   p.moveTo(t, { x, y, scale });   p.hide(t)
```
Line numbers are the file's own. Lights must be registered in `lights` at construction (a
missing registration throws with the line and substring). `focus` resets previous lights,
dims other lines to 0.28 and scrolls a long file so the focus is visible. Languages:
python, yaml, bash, js/ts, json, go, rust, sql, docker, ini, text.

### Terminal — real output, replayed

```js
const term = new Terminal({ x: 1400, y: 620, width: 900, rows: 8, fs: 23, lh: 36, title: 'terminal — ~/proj' });
term.show(t);
let t1 = term.cmd(t, 'ansible-playbook -i inventory.ini site.yml');     // returns when typing ends
t1 = term.input(t, 'you >', 'Make it funnier.');                        // interactive input line
term.out(t1 + .3, lines, { gap: .15, cls: { 0: 'hi', 3: 'dim' } });     // 'hi' = accent line, 'dim' = muted
term.clear(t);   term.moveTo(t, { … });   term.hide(t)
```
Lines longer than the panel are truncated with "…"; overflow scrolls with an eased push.
Wrap long prose lines yourself before passing them if they should stay fully readable.

### Small pieces
`card(html, { x, y, cls: 'small'|'muted' })`, `chip(html, { x, y, cls: 'big' })` (mono pill),
`label(text, { x, y, cls: 'lbl'|'lbl ink'|'lbl src'|'word' })`. All start hidden: reveal with
`show()`. Tween `borderColor`/`color` to light them.

### segTitle(num, name, tIn, tOut?)
Top-left segment title: appears in the seam, then stays faint for orientation.

### retrieval(beatId, prompt, { keep: [els] })
After the question is spoken: veil (0.92) over the field, amber prompt, amber ring depleting
over the silent window, all cleared at the window's end. Elements in `keep` stay above the
veil (e.g. silhouettes the viewer must name). Hide labels yourself right before it; reveal the
answer in the next beat.

## 6. Layout conventions (stage 1920×1080, rendered at 2×)

- Safe margins ~60 px. Segment title top-left at (64, 44).
- Mini-map docked at `{ x: 205, y: 262, scale: 0.36 }` (for a ~500 px wide map); panels to the
  right of it start at x ≥ ~380.
- Single code panel: centre ~(1110–1130, 560), width 1280–1400, fs 23–26.
- Code + terminal side by side: code `moveTo({ x: 520, y: 620, scale: 0.55 })`, terminal
  `{ x: 1420, y: 620, width: 880 }`.
- Diagram centre (960, 560); ring radius ~250; labels 28 px.
- Cards/chips for chat or events in a column at the right (x ~1580) with 70–100 px spacing.

## 7. Recipes

**Build the cast one part at a time** (pre-training): `map.hideNow(map.all())`, then for each
part `map.fade(word(b, name), id, 1); map.state(..., 'live'); map.showLabels(..., id)` and
set the previous part to `'done'`.

**A diagram part travels into its code**: create an HTML outline div at the mini-map part's
stage position (`map.stageXY`), tween it to the code line's position, fade it as
`panel.focus()` lands on those lines.

**Loop in motion**: `map.travel()` legs cued to the verbs ("reads", "calls", "writes the
result back"), set each station `'live'` on arrival and back to `'done'` after.

**Analogy in the same layout**: fade the map parts to 0 (keep edges faint), place source
icons (lucide) at the same node positions in `C.source`, animate the source process with
`travel(..., C.source)`, then per pair: pulse source → fade it → fade the target part in and
set it `'live'` → `'done'`. For the break point, a dashed source-coloured card detaches upward
and fades while the true constraint lights.

**Retrieval with feedback**: hide labels at `B(q).v0`, `retrieval(q, 'short prompt')`; in the
answer beat show the likely wrong answer (dashed path / muted card) at `start`, fade it on the
answer's key word, then animate the right one.

**If–then cue**: `panel.mark(word(b, 'docstring'), a, b, B(next).v0)` — amber box on the trigger.

**Counter / score climbing**: tween a plain object, write text in a driver (see §2).

**Next-step cue at the close**: a dashed amber outline where the viewer's own work would go
("your agent · 3 cases", a ghost third hex = "add a tool of your own").

## 8. Review, render, verify

- Preview: `npm run dev` → `http://localhost:5199/?ep=ep1` (click/space to play, arrows ±5 s).
- Contact sheet: `node shot.mjs --ep ep1 <seconds…>` → `shots/sheet.jpg` (+ one jpg per time).
  Pick times near the end of each beat's voice (`v1 - 0.3`), mid-transitions, and inside each
  retrieval window. Read individual frames at full size when judging layout.
- Page errors: the shot tool prints console errors/warnings; a thrown error (e.g. an
  unregistered light) stops the build and `window.ready` never becomes true (timeout).
- Render: production build + preview server, `node render.mjs --ep ep1 [--workers 6] [--fps 30 for drafts] [--from 40 --to 55 --out part.mp4]`.
- Verify the output file: `ffprobe` (3840×2160, 60 fps, audio stream, expected duration),
  `ffmpeg -af volumedetect` (mean ≈ −18 dB, peak ≤ −1 dB), and sample a few frames with
  `ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.jpg` to confirm the render matches review.
- Flat vector graphics compress well: ~4–5 MB per minute at 4K60 CRF 18. Offer a 1080p copy
  (`-vf scale=1920:1080:flags=lanczos -c:a copy`) if the user needs smaller files.
