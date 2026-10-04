# Overlay contract — the `seek(t)` program

The machine layer is one HTML file (`assets/overlay/overlay.html`, started from `assets/overlay-template.html` in this skill). Playwright loads it, calls `window.seek(t)` for every frame, and screenshots it with a transparent background. This is how the X-famous "Opus videos" were made: a picture written as a function of time.

## Why determinism matters
Frames are rendered out of order (contact sheets, re-rendering one bad section). If state depends on wall-clock or accumulated history, frame 1200 rendered alone won't match frame 1200 rendered in sequence, and a re-render produces a visible jump. So every visible property must be computable from `t` (and the static `beats.json`) alone.

## Hard rules
- Expose `window.seek(t)` (t in seconds, absolute song time). It must draw synchronously, then `return true` (or a resolved Promise) when the frame is complete.
- Expose `window.ready` (a Promise) that resolves when fonts, `beats.json`, lyrics and any images have loaded. The renderer awaits it.
- No `Date.now()`, `performance.now()`, `requestAnimationFrame` loops, `setTimeout/setInterval`, CSS transitions or CSS animations.
- No unseeded `Math.random()`. Use the template's `rand(seed)` / `hash(i, salt)` — seeded by index, beat number or a quantised time.
- Simulations (particles, fluid) must be **closed-form** in t, or re-simulated from 0 each seek (only if cheap). Prefer closed-form.
- Background transparent (`clearRect`, body `background: transparent`). Assembly composites with alpha. Fallback if alpha edges alias badly: set `?bg=green` → `#00FF00` and use `assemble.py --key green`.

## Beat-reactive helpers (in the template)
- `lastBeat(t, arr)` → `{i, time, age}` of the most recent event; `age` drives decays (`exp(-age*k)`).
- `loud(t)` → normalised loudness 0..1, interpolated from `beats.json.loudness` (sampled at `fps`).
- `section(t)` → current section label from `beats.json.sections` (overridable by storyboard).
- `cutAt(t)` → the storyboard cut at `t`, so the overlay can thin out on `layer: plate` + `section: chorus` rows.
- `lastEvent(t, kind, minStrength)` → `{e, age}` of the most recent music event (`drop|break|beat_change|build`) from `storyboard.markers.drops`; `eventNear(t0, kind, win)` → the event within `win` s of `t0`. Use these to time a scene's big move to the drop (doors slam, counter jumps) instead of to a hand-typed second.

## Music events (the `music` layer)
Beats drive small things (ticks, flashes on strong onsets); **music events drive big ones**. The template's `music` layer:
- **drop** → white flash < 3 frames and < 40%, a shock ring, a teal edge pulse; strength (0..1) scales all of it.
- **break** → a dark edge vignette swelling over one bar (the frame "holds its breath").
- **beat_change** → a scan line sweeping down (half-time) or up (double-time).
- **build** → edge ticks multiplying and lengthening until the drop it leads into.
- **hit_run** (selected only) → `hitRun()`: on every hit a 2-frame flash alternating white/accent (≤ 45%), a frame border that strobes thick/thin, a `HIT 03/11` counter with filling chips, and a slice glitch of the overlay for 2 frames. The plates flick at the same hits (storyboard rapid cuts), so the two lock together. Scenes can react too: `last(t, run.hits)` gives the hit index and age.
- **lyric slam** → a phrase starting within one beat of a drop springs in from 1.35× with overshoot, a few frames of shake and a wide chromatic split.
Keep the drop hit the strongest visual moment of its bar; don't stack the strong-onset flash on top (it is the same hit).

## Motion feel
- Entrances: ease-out `cubic-bezier(0.16, 1, 0.3, 1)` (template `easeOutExpo`-like `ease()`); exits faster than entrances.
- Stagger related elements by 3–6 frames.
- Springs for lyric words: closed-form damped spring `1 - exp(-z*w*a) * cos(wd*a)` with `a = age`.
- Never linear easing on anything a viewer tracks. One dominant action at a time; supporting parts stay small and thin.
- Hold resolved states long enough to read (≥ ~0.5 s for a lyric word at fast cut rates, ≥ 1 s for a title).
- Safe area: keep type inside 5% margins (96 px horizontal, 54 px vertical at 1080p).

## Default machine vocabulary (Machine + fluid style)
- **Gimbal** — 2–4 concentric rings with tick marks, rotating at different rates; a step-rotation kicks on downbeats.
- **Fluid ribbon** — layered sine/noise curves across the frame; thickness and amplitude follow `loud(t)`; the "fluid design" layer.
- **Downbeat ticks** — a timeline rail with ticks that flash on each downbeat.
- **Lyric words** — one word (or short phrase) at a time, spring-in on vocal onsets, uppercase, wide tracking.
- **HUD readouts** — small mono labels (BPM, timecode, section name, abstract coordinates). Text lives *here*, never in Gemini images.
- **Glue** — scanlines, a white/amber flash on strong onsets (keep it < 3 frames and < 40% opacity), iris wipe on section changes.

Swap or extend vocabulary to fit the user's theme (e.g. topographic contours for a desert world, waveform rings for a club track) — keep the contract.

## Layers (modularity)
The template draws through a `LAYERS` registry: `{ribbon, gimbal, tickRail, hud, lyric, introOutro, glue}`, drawn in order. Each layer is a self-contained `(t, d) => void` function, where `d` is the current density (0..1).
- **Add a part** by adding a layer. Don't grow an existing function into a monolith; small layers are easy to fix and to toggle.
- **Per-cut control is data** in `storyboard.json`: `"overlay": {"hide": ["gimbal"], "only": ["lyric", "glue"], "density": 0.2}`. A per-shot fix becomes a JSON edit plus a re-render of that cut's frames (`render_overlay.mjs --cuts 17`).
- **Debug one layer** with `?layers=ribbon` in the browser, or `render_overlay.mjs --layers ribbon --frames ...`.
- Keep layers independent of each other's state. Shared values come from helpers (`loud`, `last`, `cutAt`), never from another layer's variables.

## Scenes: lyric-driven graphics (the HUD is the base, not the whole show)
A HUD that sits on screen for the whole song reads as monotonous. The template has a `SCENES` registry: for a lyric line with a concrete idea, a scene takes over the frame (right half by default), the base HUD layers fade out, and when the scene ends the HUD returns.
- Timing lives in `assets/overlay/scenes.json` — `{"scene", "from", "to", "lyric"}` where from/to are seconds or **lyric phrase text** (`"Agents in the loop#2"`, `"phrase+1.5"`, `"+4"`), so scenes follow lyric re-timing automatically. `render_overlay.mjs` passes the file (`--scenes` to override).
- A scene is `(t, k, s)`: `k` is the fade envelope, `s.u` the 0..1 progress, `s.age` seconds since start. Drive the "story" of the graphic with `s.u` (a bar filling, dots dropping, a line falling) and the energy with beats/onsets.
- The lyric moves to the scene's `lyric` side and is width-limited during a scene so it never overlaps the stage.
- Proven scene ideas: icons flipping from human to agent, a dot grid draining with a counter, a timeline burning to ash particles, a cost curve plunging, a balance tipping, two diverging market/society lines, a candlestick crash + "circuit breaker", blast doors sliding shut, wealth bars with one breaking the ceiling, a city grid with spreading alerts, typed API calls, an ECG flatlining, an order book with "SHOPPERS: 0", a breaking economic loop diagram, a spiral with grid lights going out, capability bars, a progress bar to 100%, a grid flipping colour, a systems list going offline.

## 3D layer (three.js, `assets/world3d.js`): line graphics and panels
The overlay can draw a WebGL scene under its 2D layers. It uses the same contract: a pure function of `t`. Its look is **the HUD's own language with depth**: lines, ticks, rings, grids and dots, additive and in the palette. **No lit or shaded "physical" objects** (blobs, chrome, solid cubes): they read as a different film.

**Plumbing**
- Put `world3d.js` next to `overlay.html`.
- The template has the import map (`three` → `/__three/…`, `three/addons/` → `/__three_addons/…`), a hidden `<canvas id="gl">`, and the `world3d` layer first in `LAYERS`.
- `render_overlay.mjs` serves the page from `http://overlay.local/<abs path>` from disk (ES modules work, nothing comes from the network) and starts Chromium on the GPU (Metal on macOS).
- Lines are three's **fat lines** (`LineSegments2` / `LineMaterial`, width in CSS px). Native WebGL lines are 1 px and disappear over bright plates.
- Each frame: `direct3d(t)` builds a state object → `WORLD.seek(state)` → composite the GL canvas into the 2D canvas → draw the flat panels.

**The balance: three classes of element**

| Class | Elements | Rule |
|---|---|---|
| always flat 2D | lyrics + subtitle, title, end card, ticker, tick rail, FX, counters | type must stay crisp |
| 2D that shifts into 3D (**panels**) | the scene stage (all 2D lyric scenes), the HUD block | drawn into offscreen full-frame canvases. Flat pose = drawn directly (pixel-exact 2D); a tilted pose is a `CanvasTexture` plane in the 3D scene |
| native 3D lines/dots | ribbons, floor, swarm, wireframe scenes | depth, parallax, rotation |

**Panels and shift cues** (`panelPose(t)`)
- **Scenes:** they swing in like a door (about 65°) and swing away.
- **Drops:** a damped-spring kick of ±25° around Y.
- **Hit runs:** a new angle on every hit, then flat.
- **Loud sections:** a slow drift.
- **Breaks:** everything settles flat.

The pass order in `seek`: panel layers first (into their canvases, with `g` swapped), then `world3d` composites the 3D (tilted panels included) and draws flat panels, then the remaining 2D.

**Vocabulary** (state fields in brackets)
- **No hero object.** The user rejected both a chrome blob and a dot globe as the centrepiece: they read as a 3D *thing* pasted on the film. The 3D layer stays ambient (lines, dots, panels, wire scenes); the performer and the plates are the subject.
- **ribbons**: 3 bundles × 7 polylines twisting in depth. Amplitude follows loudness; they sag with `doom`.
- **floor**: a perspective wire grid. Height comes from loudness; a ripple ring runs out on drops (`ripple`); `collapse` sinks it.
- **swarm**: about 3k dots. `density`, `lock` (torus-knot loop) and `engulf` (gather into a cloud at `layout.swarmCenter`).
- **scenes (wireframe)**: `fired` (1,000 dots dropping), `crash` (a line candlestick chart that starts flat, tilts into perspective and plunges), `progress` (a tick ring tilting as it fills), `won` (square outlines flipping purple → teal). The 2D scene of the same name draws only its labels. Rack/server visuals stay a 2D schematic: a 3D wireframe rack fly-through read as ugly boxes.
- **camera**: a long lens. `shake` on drops/hits and `push` in builds. All other motion is in the objects.

**Determinism and performance**
- No clocks, mixers or simulations. Geometry is built once; positions, colours and transforms are set from the state.
- A frame rendered alone and in a batch is pixel-identical.
- About 110–120 fps at 1080×1920 with 8 workers on Apple Silicon. SwiftShader (no GPU) is about 15 fps per worker: use `--gl-scale 0.5` or `--gl off`.

## Plate awareness: drawing *with* the picture
`scripts/plate_features.py` analyses every still and clip (videos every 0.2 s, tracked, see below) into `assets/plate-features/index.json`, and `render_overlay.mjs` passes it to the page (`FEAT`). All coordinates are normalised to the source image:

| Feature | What it is |
|---|---|
| `lines` | LSD straight segments, longest first |
| `vp` | vanishing point plus the lines that support it, with a confidence |
| `person` | macOS Vision: silhouette polygon, bbox, **`face` box**, joints (`head`, `neck`, eyes, ears, hands, feet, shoulders, `root`), other `people` boxes |
| `contours` | long structural contours |
| `bright` | lights, LEDs, screens |

`plateAt(t)` returns the cut's features and a `map(nx, ny) → screen px` that replicates `assemble.py`'s transform for that cut and moment:
- **stills:** cover-crop → `hflip` → Ken Burns zoom `z0→z1` × `crop`, drift;
- **video:** cover × `crop` → crop → `hflip`, features from `sampleAt(F, offset + age)` (interpolated, see below).

A graphic drawn at a mapped feature stays on it while the plate zooms, and on a video plate while the subject and camera move.

## Tracking on video plates
On a Veo clip the dancer moves and the camera pushes, so graphics that snap to one sample per 0.5 s jump and lag behind her. Tracking works in two halves, and both keep the overlay a pure function of `t`:

**Offline, in `plate_features.py`** (all smoothing happens here, never as a stateful filter in the page):
- **Sample density:** every 0.2 s (`--every`), read at exact frame indices, plus the last frame before and the first after any hard cut **inside** the clip (Veo sometimes cuts mid-clip; stored in `cuts`, samples carry `seg`). Nothing is interpolated or tracked across such a cut.
- **Person:** detection gaps up to `--max-gap` 1 s are interpolated, and clip ends are held `--hold` 0.6 s (flagged `interp`). bbox, face, joints and silhouette get a centred [1,2,1] smoothing. The silhouette is resampled to 64 points, clockwise, and cyclically aligned to the previous sample, so it lerps point by point.
- **Contours, lines and bright spots are tracked** with Lucas-Kanade optical flow (forward-backward checked): a contour found at 1.0 s keeps its id and point count (48) while the camera moves; new detections join only if not already tracked. Ids sit in `cids` / `lids` / `bids` (parallel to `contours` / `lines` / `bright`), and `tracks.contours[id] = [t0, t1]` gives each track's life. `vp` is recomputed from the tracked lines and smoothed.
- **Contours are clean, single-pass structural edges:** boundaries of the big tonal regions at three thresholds, minus the frame border and the performer, smoothed and ranked against zigzags. (The old Canny-blob outlines doubled back on themselves and read as scribbles on video.)

**In the overlay:**
- `sampleAt(F, st)` brackets `st` between two samples. It uses Catmull-Rom for bbox, face and joints (smooth motion, no 5 Hz stepping), lerps the silhouette and same-id contours and lines point by point, lerps the vp, and never interpolates across a `seg` change.
- **Face anchor:** the reticle centres on the interpolated `face` box, with radius ≈ 0.75 × face height (minimum 26 px). The label and leader line ride with it and flip side near the right edge. If there is no face (back to camera), it falls back to the `head` joint, then the bbox top.
- **Brackets** follow the interpolated bbox; the lock-on contraction is still timed from the cut start.
- **Contour per cut:** `cutContour(cut, F)` picks the tracked contour alive at the cut's first frame that lasts longest into the cut, so the trace stays on the same real edge while the picture moves. When it dies, it fades with `calpha`.
- **Detection gaps fade, they don't pop:** `pA` (person alpha) ramps across a sample where she is missing.
- Label only the performer (match the plate name); other people in a shot get brackets at most.

**Check it before rendering.** Run `plate_features.py clip.mp4 --debug-video video/contact-sheets/track`. It draws the interpolated bbox, face circle, joints, silhouette and contour ids on every frame (the same interpolation as `sampleAt`). Sheet it with `contact_sheet.py --video … --times 0.3,1.1,2.1,3.3,4.5,5.4,6.6,7.6` and Read it. Then render a preview window and sheet consecutive frames 0.2–0.3 s apart over a dance cut.

**Failure modes:**
- *Graphics step or jitter at 2–5 Hz:* `sampleAt` is missing (nearest-sample snapping), or the features are from the old 0.5 s format; re-run `plate_features.py` (the cache is versioned).
- *Graphics drift off her:* `plateAt` doesn't mirror `assemble.py` (crop, hflip, offset); a loop past the clip end must use `% duration` like `-stream_loop`.
- *Lock lost for a beat:* Vision missed her (motion blur, back turned); widen `--max-gap`, or let the fade hide it.
- *A trace slides across the picture on a camera move:* it is a per-sample contour, not a tracked one; use `cutContour` and the ids.
- *Graphics smear across a jump cut inside the clip:* the clip's `cuts` weren't detected; check the `cuts [...]` that the run prints.
- *Stale features:* re-run `plate_features.py` whenever a clip is regenerated or upgraded (`-fast.mp4` is its own entry). The index is merged per run, and keys must match the storyboard `source` strings exactly.

**Contour budget (taste rule).** Tracing many contours with text and animation everywhere reads as noise. `contourMode(cut)` gives each cut, deterministically:
- about 45%: no contour work at all;
- about 35%: one animated trace, drawn on at the cut, then held faint, with one bright scan around it on a drop;
- about 20% of the longer cuts: text along a contour.

Only one contour per shot, and nothing on flash cuts. Performer shots get brackets and the head label, plus their trace or text when the mode allows, and nothing else.

`plateFX` (template vocabulary; keep it subtle, and below the lyrics):
- **performer:**
  - lock-on brackets that contract onto the silhouette box at the cut;
  - a face reticle with a label, tracked on video;
  - an outline scan (a bright dash running around the silhouette) on drops and cut-ins;
  - **text along her contour** (`textOnPath`, scrolling, glyphs skipped inside the lyric band);
  - small markers on hands and feet.
- **corridor / room with a vanishing point:**
  - perspective guides along the real edges, drawing on at the cut;
  - a floor grid converging on the real VP, which replaces the 3D floor on these shots;
  - a VP diamond.
- **any plate:** a scan segment running along the 3 longest real edges, once per beat; reticles locking onto the brightest lights, one more per beat.
- **empty shots:** text running along the main contour (a skyline, a desk edge, a chip trace).

To check the features, draw them on the stills once (lines, VP, silhouette, joints, contours, bright spots) and look before relying on them. Detection is good on clean AI stills; reject a VP below ~0.3 confidence.

## Highlight lyrics: implementation API
The guidelines (when, how often, which style, layout, fonts, pitfalls) are in `references/lyric-typography.md`. The worked code is the Agents in the Loop Short (`youtube-shorts/assets/overlay/overlay.html`).
- **Data:** `assets/overlay/highlights.json` holds `{cards: [{from, to?, style, text?, pos?, y?, rows?, title?, atWord?, anchor?, color?, size?, hold?}]}`. `from`/`to` are lyric-phrase prefixes (`#n` = nth occurrence), resolved against `lyrics.json` like `scenes.json`, so cards follow timing fixes. `load()` also fetches `../audio-analysis/lyrics-words.json`.
- **Resolution:** `resolveHighlights` gives each card `t0`/`t1`, its words, and `toks`/`tt`: the per-token [start, end], using the sung words when the counts match.
- **Timing:**
  - `charTimes(card, t)` → `[{ch, age, w}]`, with each character's age since it appeared (< 0 = not yet).
  - `wordAt(word, a, b)` finds a sung word's start, for scenes and flap rows.
- **Envelope and space:**
  - `cardAt` / `cardEnv` / `cardK(t)` give the active card and its envelope. Scenes multiply their `k` by `1 - 0.3·cardK`.
  - Each renderer sets `CARD_RECT`, and plate graphics skip only that rect (`inLyricBand`).
- **Renderers:** `typeCard`, `flapCard` (`flapTile` draws one tile mid-fold), `slamCard`, `anchorCard` (`charsOnPath` for path text).
- **Layer:** `highlight(t)` is registered as `lyric` in `LAYERS`, so `--layers lyric` keeps working for lyric-check renders.
- **Fonts:** `@font-face` with relative URLs, plus `await document.fonts.load(...)` before the first frame.

## 4K and legibility
- The canvas backing store must be `W*devicePixelRatio` and `seek` must start with `g.setTransform(DPR,0,0,DPR,0,0)`; render with `render_overlay.mjs --scale 2`. Lines and type are then natively sharp at 3840×2160.
- Lyrics over bright plates (fog, windows, sky): draw a dark band behind the type with `g.filter = 'blur(28px)'` (canvas filters are deterministic). Plain rectangles show hard edges.
- Keep every non-lyric string in one `COPY` block and spell-check it there.

## Print pass (the look in post)
A stylised finish goes on top, never into the generated plates (`look-bible.md` → Grade). Options:
- **an ffmpeg grade**, as a chunk filter in `assemble.py`;
- **an overlay layer last in `LAYERS`**: grain, a halftone/dither screen, misregistration. It must be deterministic: seed the noise by frame index, never `Math.random`.

A full-picture halftone needs the plate pixels, so do it in ffmpeg or in a WebGL post pass over the composite, not in the transparent overlay. ESCAPE VELOCITY ran its JS engine as canvas plus a WebGL print pass, and turned a "too gray" v1 into a colour-halftone v2.

## 2.5D depth parallax for stills (documented next step, not built yet)
The shots without a Veo clip (still fallbacks) currently get a flat Ken Burns zoom. ESCAPE VELOCITY animated them in code over a depth map: real near/far separation for the cost of one depth inference. When building it:
- **Depth:**
  - run Depth Anything V2 (small) on Apple Silicon (MPS) through `uv run --with torch --with transformers`;
  - write `<still>.depth.png` (16-bit, near = bright) next to each still;
  - cache by content hash, like `plate_features.py`.
- **Render:**
  - a new still motion type in `assemble.py` (e.g. `"motion": "parallax-dolly" | "parallax-orbit"`). Render it as a per-frame displacement: shift each pixel by `(depth − focus) × camera offset`, inpaint the small disocclusion gaps by edge stretch, and keep moves slow and small (a 2–4% dolly or a few degrees of orbit over the shot);
  - or render it as a WebGL mesh displaced by depth in Playwright.
- **Overlay:** `plateAt(t)` must replicate the same camera, so the tracked graphics stay locked to the picture (the same rule as for Ken Burns: change `KB`/the mapping together).
- **Budget:** use parallax on the 2–4 s still shots. Repetitive 2.5D panels read as a gimmick; ESCAPE VELOCITY converted some of them into pure motion design after review.

## Lyrics input
`assets/overlay/lyrics.json` is an array of `{ "t": seconds, "end": seconds, "text": "WORD", "line": "full lyric line" }` (written by `curate_lyrics.py`; `line` feeds the small subtitle); `start` is accepted as an alias for `t`. `scripts/lyrics.py` writes a word-level starter. MLX Whisper word timestamps come first; if the user supplied lyrics text, it aligns them to the audio. Curate the starter: at fast tempos keep hook words and short phrases rather than every word. Timing sources, best first: the user's lyrics aligned with `lyrics.py --lyrics-text`, then the raw `lyrics.py` transcript (add `--separate` for dense mixes), then hand-placed words on onsets/downbeats, then no lyrics (HUD only).

## Rendering
```
node scripts/render_overlay.mjs --html assets/overlay/overlay.html --out assets/overlay/frames \
  --start 0 --end 215.3 --fps 30          # full
node scripts/render_overlay.mjs --html ... --out video/contact-sheets/raw --frames 12.5,45,120.2,210
```
Frame files are `frame_000000.png`, numbered from the absolute frame index (`round(t*fps)`), so partial re-renders drop straight into the full sequence:
```
node scripts/render_overlay.mjs --html ... --out assets/overlay/frames --ranges 62-70,140.5-148
node scripts/render_overlay.mjs --html ... --out assets/overlay/frames --cuts 17,22-24
node scripts/render_overlay.mjs --html ... --out assets/overlay/frames --sections chorus
```
`assemble.py` fingerprints the frames per chunk, so only the chunks covering re-rendered frames are re-encoded.
