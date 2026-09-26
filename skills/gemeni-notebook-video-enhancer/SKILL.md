---
name: gemeni-notebook-video-enhancer
description: Remake a dull narrated presentation/explainer video (Google Gemini / NotebookLM "video overviews", slide-deck recordings, static-image explainers) into a fluid, hyper-modern motion-graphics video, keeping the original voice-over. Samples the video into timestamped contact sheets, transcribes it with word-level timing, designs a continuously morphing animation per narrative beat in web tech (GSAP + Three.js shader + glass UI), renders it frame-accurately with headless Chromium + ffmpeg, and outputs 9:16 (YouTube Shorts/Reels/TikTok), 16:9 1080p or true 4K. Can match a brand's website colours/fonts and animate a supplied SVG logo, defaults to a calm, low-glare "focus dark" palette (confirmed with the user first), with neon-glass and flat brand styles as alternatives. Use this whenever the user has an mp4 of a presentation/explainer whose audio is fine but visuals are boring and wants it "enhanced", "remade", "animated", "turned into motion graphics", "made cooler", or converted to Shorts — even if they don't mention NotebookLM or Gemini by name.
---

# Gemini / NotebookLM video enhancer

Turns a narrated presentation video into a new motion-graphics video: **same audio, all-new visuals** that are synced to the spoken words and flow as one continuous animation (no hard cuts).

**How it works.** A web page holds one paused GSAP timeline that covers the whole video. `window.seek(t)` sets every element to its state at time `t`. Playwright then screenshots every frame at 60 fps, and ffmpeg encodes the frames and adds the original audio back in. Because each frame is rendered on its own rather than screen-recorded, there are no dropped frames, and re-renders are deterministic.

The engine is already built. It lives in `assets/template/` and is copied into a new project by `scripts/scaffold.sh`. **Your job is the creative part:** understand the talk, design a scene for each beat, write the scene modules, review them visually, and render.

## Default choices

Apply these unless the user says otherwise. Mention the defaults in one line; don't ask about them up front. **The colour palette is the one exception:** always confirm it (see below).

- **Colour palette: default to the focus dark palette, but ask first.** It uses a soft charcoal base `#121418`, off-white text `#E8EAED`, desaturated amber `#F2B45A` for attention and the human, periwinkle `#8AB4F8` for the system and AI, coral `#F28B82` for danger, and sage/mint `#81C995`/`#78D9C8` for the solution. It follows common dark-mode readability guidance and is calmer and lower-glare than saturated neon. **Before building any scenes**, unless the prompt already names a palette, brand or style, ask the user once with AskUserQuestion. Keep it to one question, and list "Focus dark (Recommended)" first. The alternatives are:
  - neon glass (the template's original look);
  - the source video's own colours;
  - a brand or website match.

  Ask it in the same message as the scaffold, so the installs keep running while the user answers. Full tokens, set-up steps and `bgTo`/`heroColor` presets are in `references/themes/focus-palette.md`, and the drop-in stylesheet is `references/themes/focus-dark.css`.

- **Output format:** 1080×1920, 60 fps. Use `--landscape` for 1920×1080. Use `--4k` for 3840×2160: the stage stays 1920×1080, so all coordinates and examples still apply, and it renders at deviceScaleFactor 2 for true 4K. `--scale N` sets any multiple. The source's aspect ratio doesn't matter; a portrait NotebookLM video can become a 16:9 remake.
- **Output file:** `<video>_motion.mp4`, written next to the source video.
- **No subtitles or captions.** The narration carries the words. The original's caption strip is not reproduced, and text on screen is limited to short labels that belong to the graphics ("01 Selective Routing", "Auto-Approve All", "87% confidence"). A user asked for this explicitly before: burned-in captions compete with the motion and make it look like the old video again.
- **Visual style:** by default it is flat 2D in the focus dark palette. That means flat `.panel` cards, the calm chart background (`flat-chart-bg.js`), top-left titles (`flat-title.js`) and one hero outline that morphs from scene to scene. Keep the "continuous morph" idea, because that is what makes it feel fluid rather than like a slideshow. If the user picks **neon glass**, keep the template's own `style.css`/`bg.js` as scaffolded: a flowing shader, glass cards and gradient text. If the user names a brand or website, see *Brand matching* below. The morphing hero stays in every style; only the materials change.
- **Watermarks and branding:** drop the source's watermark and end-card branding (e.g. the NotebookLM logo). This is new artwork, not a copy.

## Brand matching (when the user names a website, brand or logo)

1. **Get the tokens from the site's CSS:** run `bash <skill>/scripts/brand-from-site.sh <url> motion/analysis`, which writes `brand.txt` (colour custom properties, font tokens, the most-used hex colours and easing tokens). Don't rely on WebFetch here: it sees only rendered text, not CSS. Also, CDNs often return 403 to curl's default user agent, which the script works around.
2. **Theme:** copy `references/themes/flat-brand.css` over `src/style.css` and replace its `:root` tokens with the brand's. If the brand font isn't free (Adobe or commercial), pick a close `@fontsource` match, e.g. Neue Haas Grotesk → Inter Tight, and tell the user about the swap.
3. **Background:** for a calm corporate look, copy `references/themes/flat-chart-bg.js` over `src/bg.js`. It gives a navy base with soft light pools, contour lines and a faint grid, rendered at full resolution. Use the brand's accents for `bgTo`/`heroColor` and set the gradient stops in `index.html`. Keep the hero stroke thin (about 2.5 px) and its glow faint.
4. **Titles:** in landscape, paste `references/themes/flat-title.js` into `lib.js`. It puts the title top-left with a mono label, the way many brand sites do.
5. **Logo:** copy the SVG into `src/assets/`, because Vite won't import files from outside the project. Then use `inlineSvg(raw, width)` from `lib.js`; it makes ids unique, strips inline transforms and returns `parts`. Wordmarks are often one group per letter, so stagger `parts` for a letter-by-letter reveal. Good places for it: when the narration names the product or company, a synthesis moment ("everything collapses into the logo"), and the end card. Render the SVG once with Playwright and look at it before planning, because its structure decides what can animate.

## Workflow

### 1. Scaffold and analyze (≈3–5 min, mostly installs)

```bash
bash <skill>/scripts/scaffold.sh "<video.mp4>" "<dir-next-to-video>/motion" [--landscape | --4k]
```

This does the following:
- copies the engine and writes `config.json` (source, output, size, fps, duration);
- extracts `public/audio.m4a`;
- runs `npm install` and installs Chromium;
- creates a whisper venv;
- runs `scripts/analyze.sh`, which samples a frame every 2.5 s into `analysis/sheet_*.png` and writes `analysis/sheets.txt`, a map of which tile is which timestamp;
- runs `scripts/transcribe.py`, which writes `analysis/transcript.txt` (timed sentences), `analysis/words.txt` (`word@start` for exact cue times) and `analysis/transcript.json`.

If any step fails, re-run just that script. Each one is standalone and its usage line is at the top of the file.

### 2. Understand the talk and write the beat map

Look at every contact sheet next to `sheets.txt` and `transcript.txt`. The images tell you what each moment is about: the metaphor the original illustrator chose, the objects, the numbered structure. The words tell you exactly *when* each moment happens.

Write `analysis/beats.md` with one row per beat (usually 6–12 beats, each 5–15 s):

| time | narration (short) | original visual | new motion idea | hero shape |
|---|---|---|---|---|

Useful things to look for:
- **Structure words:** "first / next / third / finally", "here are four…". These become numbered title chips, and often a grid that returns as a table of contents.
- **Contrast pairs:** "traditional systems do X, **but** Y does Z". Animate the bad state first, then transform it into the good state on the word "but".
- **Concrete nouns:** alerts, dashboards, text walls, buttons, gauges. Build them as UI and have them *do* the thing described.

Read `references/design-playbook.md` for the metaphor catalogue, pacing rules and layout safe areas. Read `references/example-scenes/README.md` for two worked examples. The first is a 95 s portrait NotebookLM video about UX patterns for AI, split into 8 scenes (neon style). The second is a 97 s landscape 4K remake in a brand style, organised around a "five layers" structure that persists through the whole video (flat style).

### 3. Build scenes

Write one module per beat in `motion/src/scenes/` and list them in `src/scenes/index.js`. Delete the starter `s1_example.js`. Take cue times from `words.txt` and place things **on the word**; start an entrance about 0.1–0.2 s before the word so it has landed by the time the word is heard.

**Read `references/engine.md` before writing scene code.** It documents the helpers (`morph`, `pop`, `out`, `sceneTitle`, `click`, `drive`, `bgTo`, `heroColor`, shape generators and icons). It also documents the determinism rules; breaking them produces flicker or elements in the wrong place when a frame is seeked. The example scenes are good to copy patterns from. The `s*_*.js` examples use 1080×1920 coordinates and the `landscape_*.js` ones use 1920×1080. Scale whichever set you copy from to fit your stage.

Rules of thumb:
- **Keep the hero shape on screen the whole time and morph it at every beat change.** It is what ties the video together.
- **Overlap scenes.** The next scene's entrance starts while the previous scene is still leaving (blur + scale + fade). Never leave an empty frame.
- **Keep something moving all the time.** Use floats, pulses, flowing dashes, counters and particles. A still frame reads as "slide".
- **Contrast pairs need a visible change of state:** a colour shift in `bgTo` and `heroColor`, and the UI transforming.
- **Show the section's main visual within about 1 s of its title.** Narrators often spend 2–3 s on "Fourth, AI-SMS integration" before describing anything, and a bare hero outline under a title reads as an empty frame. Bring in the setup UI early, then *act* on the later words.
- **For "N layers / pillars / steps" talks, carry one persistent structure through the video.** The list of N items appears as the table of contents, docks to a side rail, lights the current item in each section and ticks it off afterwards, then comes back to the centre for the synthesis. See `landscape_stack.js`.

### 4. Review visually and iterate

```bash
cd motion && (npm run dev > /tmp/vite.log 2>&1 &) && sleep 2
node shot.mjs 1 3.5 6 9 12.5 ...      # 15–30 timestamps: key words + mid-transitions
```

This writes `shots/sheet.jpg`, one tile per timestamp in the order given. Look at it with the Read tool and check the following:
- overlapping or clipped elements;
- text that runs off the stage;
- content in the safe areas (see the playbook);
- empty frames between scenes;
- cursor clicks that miss their targets;
- `pageerror` output in the console.

Fix, re-shoot, and repeat until each beat reads clearly at a glance. Also check a few timestamps *during* transitions, not only at rest.

### 5. Render and verify

```bash
pkill -f "vite --port 5199"; npx vite build && (npx vite preview --port 5199 --strictPort > /tmp/vite-preview.log 2>&1 &) && sleep 2
node render.mjs                        # M-series Mac, 6 workers: ≈30 fps at 1080p (~3–4 min per 90 s at 60 fps); ≈15 fps at 4K (~6.5 min per 97 s)
bash <skill>/scripts/verify.sh .       # format, duration, audio, black frames, output contact sheets
```

Render against the production build and never the dev server, because Vite can reload pages mid-render. For a quick draft, use `node render.mjs --fps 30`; to render part of the video, use `--from 40 --to 55 --out /tmp/part.mp4`.

Open the `analysis/output_sheet_*.jpg` files and compare each one with the source sheets. Every beat should land on the same tile as its narration. When you're done, stop the preview server, and tell the user:
- where the file is and its specs;
- a short list of what each scene shows;
- how to preview it live (`npm run dev` → http://localhost:5199, click to play, space/arrow keys to control);
- how to tweak a scene and re-render.

Output is CRF 18, which is large: about 3 MB/s at 1080p and 2.5 MB/s at 4K (a 97 s 4K video is about 245 MB). Offer a smaller copy. For a 1080p copy of a 4K render, keep the frame rate and copy the audio:

```bash
ffmpeg -i out.mp4 -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -tag:v avc1 -c:a copy -movflags +faststart out_1080p.mp4   # 97 s → ~63 MB
```

Add `-c:v libx265 -tag:v hvc1 -crf 22` for HEVC, which is about half the size again.

## Troubleshooting

- **Elements drift off-centre when scaled or rotated by a driver.** The CSS `scale`/`rotate` properties pivot around the element's *untransformed* box at (0,0). Set the whole `transform` string in the driver instead; `engine.md` explains how.
- **An element snaps back or jumps when you scrub backwards.** It is being written by both a GSAP tween and a driver, or a value is set in a callback. Give each property a single owner.
- **The page errors on an icon.** Check the lucide name at lucide.dev/icons. `icon('triangle-alert')` accepts any lucide name, plus the aliases listed in `lib.js`.
- **`ffmpeg: No such filter: drawtext`.** Homebrew's ffmpeg often has no freetype. None of the scripts need drawtext; that's why `analysis/sheets.txt` holds the timestamp legend instead.
- **A tween does nothing, or an exit blur never shows.** A driver writes the same CSS property every frame, e.g. `style.filter` for a glow flash while `out()` tweens `filter` blur. Move the driver's effect to another property (`boxShadow`, or a child element).
- **`backgroundColor` tweens are invisible on `.panel`/`.glass`.** Their `background` is a gradient that paints over the colour. Tween an inset `boxShadow` (`inset 0 0 0 300px rgba(…)`) instead, and set its start value with `gsap.set`.
- **Blur/filter exits look wrong on SVG groups.** Put the SVG drawing in its own `svgLayer()` and animate the `<svg>` element, not the inner `<g>`.
- **Vite refuses to import a logo from outside the project.** Copy it into `src/assets/` and import it with `?raw`.
- **Whisper is slow or missing.** mlx-whisper on Apple Silicon takes about 30 s for 90 s of audio. Elsewhere faster-whisper `small` runs on CPU; set `WHISPER_BIG=1` for better accuracy.
