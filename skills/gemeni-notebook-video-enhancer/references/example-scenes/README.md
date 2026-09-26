# Worked example: "Top UX Patterns for AI Interfaces" (NotebookLM, 95 s)

These are the complete scene modules from a finished remake: a 406×720 NotebookLM video overview re-rendered at 1080×1920 and 60 fps. They import from `../lib.js` and `../shapes.js` exactly as a project scene does. Coordinates are hard-coded for the 1080×1920 stage; scale them for other sizes.

Use them to copy patterns, not to paste in whole: every talk needs its own metaphors.

| File | Time | Narration | What it shows | Techniques worth copying |
|---|---|---|---|---|
| `s1_intro.js` | 0–6.5 | "Modern AI is probabilistic… prone to hallucination, making human oversight mandatory" | bubble hero; `10 × 5 = 100` types in; "100" glitches red; scan beam; strike-through; MANDATORY stamp | staggered char entrance, glitch driver, `heroColor` + `bgTo` red shift, stamp slam (`power4.in` from scale 2.4) |
| `s2_fatigue.js` | 6.5–12.2 | "babysit algorithms all day… cognitive fatigue" | triangle hero; 72 alert cards swarm out; counter badge; avatar with "all day" clock ring; Focus meter drains | driver-owned swarm with accelerating spawn, jitter ramp, **converge handoff into the next scene's tiles**, DrawSVG ring |
| `s3_four.js` | 12.2–17.4 | "four UX patterns that integrate human judgment without overwhelming you" | rounded-square hero; 4 glass tiles; human node linked to each; calm pulse rings | exports `PATTERNS` reused by the outro; **tile 01 flies up and becomes the next title** |
| `s4_routing.js` | 17.5–30.5 | Selective routing: bombard → uncertainty-aware filtering escalates only low-confidence items | AI core → dashboard flooded (99+), cards blown away; funnel hero; green cards exit sideways to "Auto" counters, 3 amber ones drop into slots; badge turns green | two-phase driver stream with branching trajectories, arrival counting, bell shake |
| `s5_decomp.js` | 30.8–49.6 | Claim decomposition: text walls → blind accept → isolated clickable facts → verify each | document hero with 46 lines scrolling; "Accept all" clicked; flawed lines flash red; lines explode; hero → 4 pills; cursor verifies each fact (3 ✓, 1 ✕ "unsupported"); ghost "Accept all" struck out | explode driver, compound-path morph, `click()` sequence, shine sweep |
| `s6_friction.js` | 49.9–67.4 | Intentional friction: seamless → complacency; speed bumps; select reason for override; autopilot off; judgment | glossy "Auto-Approve All" orb with items streaming through; eye closes; orb → ball rolling over road bumps; override modal with dropdown; AUTOPILOT toggle flips OFF; brain + rays + star hero | **GSAP → driver handoff via a twin element**, `roadY` physics, dropdown UI story, text switched by a driver |
| `s7_trust.js` | 67.6–82.6 | Calibrated trust: black-box recommendations → logic paths, confidence meters, risk cards → when to take control | 3D "?" cube + "Surgery" card; cube explodes into a logic graph; risk tags; gauge hero with segments, needle and live %; needle drops → "Take control" | CSS 3D cube with `--z` tween, DrawSVG edges + flowing dashes, needle driven by a tweened object |
| `s8_outro.js` | 82.4–95.06 | "don't automate you away… elevate you from manual operator into a strategic decision-making partner" | human-silhouette hero dissolves into particles and reforms; pattern icons orbit; lift on a light pillar; "Manual operator" falls away; hero → ∞ with human and AI orbs; end card "Human + AI" | particles sampled inside a shape, depth-sorted orbit, `#heroG` lift, particles following `getPointAtLength` |

The whole video's hero chain: dot → bubble → triangle → rounded square → dashboard frame → funnel → document → 4 pills → circle → road → toggle frame → star4 → hexagon → graph frame → gauge arc → human → ∞.


# Worked example 2: "How Jeppesen ForeFlight Solved Aviation AI" (landscape, 4K, flat brand style, 97 s)

The source was a 720×1280 NotebookLM video with pseudo-3D art. The remake was built with `scaffold.sh --4k` (a 1920×1080 stage rendered ×2). The brand colours came from the product website (`brand-from-site.sh`), and the brand's SVG wordmark was animated letter by letter. It used `themes/flat-brand.css`, `themes/flat-chart-bg.js` and `themes/flat-title.js`, and the scenes use class names from `flat-brand.css` (`.eyebrow`, `.label`, `.node`, `.slot`, `.panel`, `.tag`, `.stamp`).

| File | Time | Narration | What it shows | Techniques worth copying |
|---|---|---|---|---|
| `landscape_stack.js` | 18.7–88 | "…secured by five structural layers. First… Second… Finally…" | 5 slots appear as a centred table of contents, fly into a right-hand rail (01 at the bottom, like a foundation), light up during their section and get a ✓ afterwards, return to the centre and light up bottom→top for the synthesis, then collapse into the logo | **one element tweened across the whole video** (TOC → rail → active → done → synthesis → collapse); tweening `width`/`height`/`fontSize` with em-based children; inset `boxShadow` as the highlight fill |
| `landscape_trail.js` | 46.3–59.2 | "Black-box AI is unacceptable… auditable causal trace… which inputs and constraints drove every recommendation" | black box with orbiting "?" and a ✕ stamp → 4-column chain Inputs → Constraints → Logic → Recommendation; rows fill on their words; a pulse travels the chain; AUDITABLE stamp | `svgLayer` + DrawSVG connectors with `flow()`; rows timed per word; a driver-owned pulse |
| `landscape_walls.js` | 59.4–71.8 | "plugs directly into the airline's safety management system… aren't just suggestions… walls the AI cannot bypass" | agent module slides into an SMS socket with a flash and a CONNECTED tag; "suggestion" notes fall away; hatched walls rise under a shield-shaped hero; an AI packet hits a wall, bounces back, BLOCKED | plug/socket handoff; `scaleY` walls with `transform-origin` at the bottom; a bounce driver; the flash on `boxShadow` so it doesn't fight `out()`'s filter |

Its hero chain: bubble → gauge arc → wide pill (cascade) → logo pill → TOC frame → circle (graph) → human → prompt card → badge frame → square (black box) → trace frame → SMS frame → shield → hexagon (memory) → stack frame → logo pill → ∞ (AI = human) → logo pill.
