# Design playbook

This is how to turn a narrated explainer into motion that feels fluid and modern, not like animated slides.

## Principles

1. **One continuous flow.** A single hero outline (`#hero`) is on screen from the first frame to the last and morphs at every beat, e.g. bubble → triangle → grid → funnel → document → pills → orb → road → toggle → star → hexagon → gauge → human → ∞. Content lives inside or around it. The viewer should never see a cut.
2. **Handoffs, not fades.** The best transitions carry an object across: a swarm converges into the next scene's tiles; a tile flies up to become the scene title; an orb shrinks into a ball that rolls over speed bumps; a card becomes a node in a graph. Plan at least one handoff for each scene change.
3. **Show the verb.** When the narration says something *happens* ("bombards you", "breaks paragraphs into facts", "forces you to select a reason", "exposes logic paths"), the UI performs that action on screen at that word. Illustrations of nouns are weaker than animations of verbs.
4. **Problem → solution palette.** Show problems with warm or red colours, high `energy`, jitter, glitch, overload and a draining meter. Show solutions with cool teal or green colours, low energy, order, calm pulses and checkmarks. The palette change itself tells the story.
5. **Something is always moving.** Use idle floats, flowing dashes, rotating sheens, pulsing rings and the drifting camera. A still frame reads as "slide".
6. **Minimal text.** There are no subtitles and no sentences on screen. Use labels of 1–4 words, numbers and UI copy (button labels, chip text, a few realistic fake data items). Keep the text large: at least 30 px for labels and 44 px or more for headings on a 1080-wide stage. People watch Shorts on phones.

## Beat → scene structure

A typical NotebookLM/Gemini overview has this structure:

| Part | Share of video | What to do |
|---|---|---|
| Hook (problem statement) | 10–15% | a strong visual metaphor plus a glitch or overload moment |
| Stakes / pain | ~5–10% | escalation: swarm, meter draining, red shift |
| "Here are N …" | ~5% | a grid or list of N tiles. It doubles as a table of contents, and tile *k* flies up to become scene *k*'s title. |
| N sections ("First… Next… Third… Finally…") | ~65% | one scene each, with a numbered `sceneTitle`. Inside each, animate the bad version, then transform it into the good version on "but", "instead" or "fix this". |
| Outro / thesis | ~10% | symbolic synthesis (human + AI, ∞, orbiting icons of all N ideas) and an end card with the title and N keywords |

Scene length follows the narration. Put the scene's key visual change **on the stressed word**, and start the entrance 0.1–0.2 s early.

## Metaphor catalogue

These are starting points. Pick the one that fits what is *said*, and invent freely.

| Narrated idea | Motion idea |
|---|---|
| AI answer / chat | speech-bubble hero; equation or answer types in |
| error, hallucination, wrong | RGB-split glitch, turn red, warning icon pops, strike-through |
| oversight, review, checking | scanning beam sweeps; eye/scan icon chip; "REVIEW" stamp slams in |
| overload, too many alerts, noise | swarm of mini notification cards; counter badge racing up |
| fatigue, burnout, attention | battery or focus meter draining green → red; avatar desaturates; jitter |
| N patterns / steps / pillars | grid of N glass tiles with icon + number; center node linked to all |
| filtering, routing, triage | funnel hero; stream of cards; confident ones veer off with ✓, uncertain ones drop into the "you" panel |
| dashboard, inbox | glass panel with header, bell and counter; cards stack into slots |
| wall of text, dense summary | document hero with rows of line bars filling and scrolling fast |
| decompose, break into pieces | lines explode, then reassemble as separate fact chips (hero → `pills`) |
| verify each item | cursor clicks each chip → green ✓; one fails → red ✕ + shake + "unsupported" tag |
| blind acceptance, rubber-stamping | "Accept all" button clicked on autopilot; flaws flash afterwards |
| seamless, automatic, frictionless | glossy orb; items streaming through it; speed lines |
| complacency | eye closes; "z z z"; orb turns red while red items slip by |
| friction, speed bumps, slow down | hero → road with bumps; ball rolls and decelerates at each bump |
| justify / choose a reason | modal: dropdown opens → cursor picks option → submit enables → click |
| autopilot off, take control | big toggle ON → OFF; "Take control" button pulses |
| judgment, expertise, insight | brain or spark core with light rays; hero → `star4` |
| black box, opaque | rotating dark cube with "?"; question marks float |
| transparency, explain reasoning | cube explodes → node graph drawing itself (DrawSVG) with flowing dashes |
| confidence, certainty, risk | gauge hero (`arcBand`) + red/amber/green segments, needle sweep, live % counter; colored risk tags |
| human replaced vs. empowered | silhouette dissolves into particles, then reforms; icons orbit it; it rises on a light pillar |
| partnership, collaboration | hero → ∞ with the human orb and the AI orb in its loops; particles running along it |
| growth, improvement | chart line drawing itself; bars rising; counter |
| security, protection | shield hero; lock snapping shut; scan ring |
| speed, performance | streaks, motion blur, a stopwatch ring filling |
| cost, money | coins stacking, a price tag counter rolling |
| data flow, pipeline | nodes connected by flowing-dash edges; packets traveling |

## Layout and safe areas

**Portrait stage (1080×1920)**
- Keep important content between y ≈ 180 and y ≈ 1560, and x ≈ 60–1000.
- Shorts, Reels and TikTok cover the bottom ~20% with the title, channel and description, and the right edge (x > 960, y ≈ 900–1600) with buttons. Only put decoration there.
- The scene title chip sits at y ≈ 250. The main visual is centred around y ≈ 800–1000.

**Landscape stage (1920×1080):** keep a 5% margin on each side. Put the title at the top-left or top-centre. A layout that works well for sectioned talks:
- the title block sits top-left at x ≈ 100, y ≈ 90–190;
- the main visual is centred around (720, 590) in x ≈ 100–1340;
- a persistent side rail at x ≈ 1380–1820 holds the progress through the talk (the docked table of contents);
- a "problem" beat can span the full width (e.g. a cascade chain along y ≈ 880).

**General**
- Use no more than about 3 focal groups on screen at once. Clear the previous scene's elements (`out`) before or while the next scene's elements arrive.
- Z-order: shader background < hero outline (SVG) < `#ui` elements (set `z-index` inline where they overlap) < cursor.

## Colour

**Default: the focus dark palette.** Its `bgTo`/`heroColor` presets are in `themes/focus-palette.md`; confirm it with the user first (see SKILL.md). The presets below are for the **neon glass** alternative.

The shader takes three colours (deep, cool, warm) and an energy level. These presets worked well:

- **calm/intro:** `#1a0f5c #0a6fa8 #7c2bd0` at 0.5
- **error/danger:** `#3a0a2a #7a1236 #b3264a` at 0.9
- **warning/overload:** `#2a1406 #8a3b0a #6b1d5c` at 0.8
- **solution/cured:** `#06243a #0f766e #1e3a8a` at 0.35
- **black box/void:** `#07070f #1e1b4b #111827` at 0.4
- **finale:** `#1a0b52 #0e7490 #a21caf` at 0.9

Hero stroke colours follow the meaning of the moment: cyan/violet/pink by default, amber for warnings, red for errors, green for "fixed", grey for "off".

### Flat brand preset (the "professional 2D" look)

Use it when the user wants a corporate look, a brand match, or "no 3D".
- **Base:** the brand's darkest surface colour (e.g. navy `#001629`). Use the brand colours only as soft light pools (`references/themes/flat-chart-bg.js`). Energy 0.3–0.45 for calm beats; about 0.7 with the brand's warm accent for problem beats.
- **Materials:** `.panel` cards with 1.5 px borders at 16% white, and a radius of about 14 px. Highlight with an accent border rather than a glow. No backdrop blur, no bloom, grain at about 0.035.
- **Type:** a grotesk for headings; mono uppercase labels with wide letter spacing (brand sites often use these); numbers set in mono.
- **Hero:** a 2.5 px gradient stroke in the brand accent colours, glow opacity about 0.2, and a fill that is barely visible.
- **Motifs:** borrow them from the industry domain. For aviation, for example: gauges, route chains, chart contour lines, grids, NOTAM cards and badges. Brand-style hatch patterns work for walls and barriers.
- **Camera:** drift only, no rotation, so thin text and lines stay sharp.

## Quality checklist before rendering

- [ ] Every beat in `beats.md` has a visible key change within ±0.3 s of its word.
- [ ] No frame is empty: check the timestamps between scenes with `shot.mjs`, *and* the 1–3 s after each section title.
- [ ] No text is clipped at the stage edges, and nothing important is in the safe-area margins.
- [ ] Cursor clicks land on their buttons.
- [ ] The palette shifts for problem versus solution beats.
- [ ] The end card holds for 2 s or more, and the camera's slow push-in finishes the video.
