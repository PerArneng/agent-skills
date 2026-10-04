---
name: futuristic-music-video
description: Turn an existing song (any mp3, e.g. from Suno) into a beat-synced futuristic music video, up to 4K, where AI generates the pictures and code generates everything else. Gemini (Nano Banana stills, Veo clips) supplies the footage; a frame-by-frame HTML overlay adds the HUD, lyric scenes, a 3D line layer and lyric typography; ffmpeg assembles it on the original audio. Cuts and graphics lock to the beat, the bass drops and breaks, and the sung words (force-aligned lyrics), and track the performer in the footage. Lyrics become a few designed cards (typed readouts, split-flap boards, slams), not subtitles. Modular and cached, so one fix rebuilds seconds. Also makes a looping vertical Short and the YouTube package (A/B thumbnails, description, chapters). Use whenever the user wants a music video, lyric video, visualizer or motion-graphics video for a track, visuals for a Suno song, or a sci-fi, cyberpunk or high-paced video from an mp3, even if they never say "music video". Reusable for any song.
---

# Futuristic music video

**What it does:** you bring the song; the skill does the timing, design and assembly a motion-graphics editor would, and AI generates the footage. Gemini makes the pictures (stills of a recurring character and world, animated into short Veo clips). Code makes everything that must be precise: an overlay drawn frame by frame with HUD, lyric scenes, lyric typography, a 3D line layer and the end card. ffmpeg assembles it all on the untouched original audio, up to a 4K master. Cuts and graphics lock to the beat, the song's events (drops, breaks, builds, drum runs) and the sung words; the graphics track the performer in the footage; lyrics show up as a few designed cards instead of subtitles. The build is modular and cached, so fixing one shot rebuilds seconds of video. It also makes a looping vertical Short and the YouTube package.

Build a music video for an existing song with the hybrid method behind the late-2026 "Opus videos": **code owns the runtime, Gemini supplies the photographic plates, and ffmpeg locks everything to the beat.**

- **Plate** – a locked Gemini still or a 4–8 s Veo clip: the singer/subject performing, and scenes that show what the lyric is about.
- **3D, as line graphics** – a three.js layer (`assets/world3d.js`) drawing only lines and dots: line ribbons, a wire floor, a dot swarm and wireframe scenes. 2D **panels** (the scene stage, the HUD) can swing and tilt between flat 2D and 3D on music cues. No shaded objects.
- **Plate-aware** – `plate_features.py` finds each plate's edges, vanishing point, the performer's silhouette, face and joints, contours and lights. The overlay draws *with* the picture: lock-on brackets, a face reticle, text running along her outline, perspective guides out of the real vanishing point, and scans along real edges. On **video plates** it all **tracks**: features are sampled every 0.2 s, smoothed and optical-flow tracked offline, and `sampleAt` interpolates them, so the brackets and the face circle follow her as she dances and the contour traces ride the camera move.
- **Machine** – a code-drawn HUD as the base, plus **lyric scenes**: motion graphics that take over for a specific line ("workers fired" → 1,000 dots dropping out) and hand back to the HUD. **Highlight lyrics** on top: only the lines that carry the story get a designed card (see `references/lyric-typography.md`).
- **Glue** – scanlines, beat flashes, iris wipes and short dissolves.

## Sync hierarchy: what the picture locks to
1. **Beat grid** (`beats.json`): every cut sits on a downbeat; flashes and small pops land on onsets.
2. **Music events** (`drops.json`): what the song *does* at a bar line. A **bass drop** gets a hard cut exactly on it, a short burst of 1-bar cuts and an overlay hit. A **break** (bass out) holds a shot and hushes the frame. A **beat change** re-paces the edit (double-time → shorter cuts, half-time → longer). A **build** tightens toward its drop. A **hit run** (a few hard, evenly spaced hits in a row: stabs, "bum bum bum", a snare fill) gets a new image on every hit plus a strobe in the overlay, but only on the few strongest runs, picked by `drops.py`. Never let a cut run across a drop.
3. **Vocals** (`lyrics-words.json` / `lyrics.json`): lyric words appear exactly when sung; a lyric-matched shot arrives *with* its phrase (the cut is split at the beat nearest the phrase start); plain cuts avoid landing inside a sung word; a phrase starting on a drop slams in.
When two rules disagree: drop > vocal phrase > downbeat pattern.

Why this split: video models can't hold crisp type, geometry or sub-second sync, and they're the only expensive part. Code can do all three for free. A whole song in Veo costs $72–$150 and drifts; the hybrid costs $4–20 and looks more designed.

The skill is generic. The song, subject, world and theme notes are inputs, and each video gets its own bible, storyboard and assets.

## Build it modular: fixes must not trigger massive re-renders
A video goes through many rounds of "change that one shot". Every layer of this pipeline is split into small, independently rebuildable units, so a fix costs seconds, not a full re-render. Keep it that way when you customise anything:
- **Assets.** One file per still or plate, each with its `*.prompt.txt`. Replacing a plate means regenerating one file, never a batch. Plates are listed in `video/plates.json` (name → still + motion prompt).
- **Storyboard is data.** Cuts, crops, flips, plate reuse, transitions and per-cut overlay tweaks (`"overlay": {"hide": [...], "only": [...], "density": 0.2, "lyric": "right"}`) all live in `storyboard.json`. Prefer a data edit over a code edit. Generate it from a small script (`assets/make_storyboard-example.py`) with a section PLAN and `LYRIC_CUES` (phrase → plate), so re-pacing is one edit.
- **Overlay is layers + scenes.** Independent layer functions in a `LAYERS` registry, and lyric scenes in a `SCENES` registry timed by `assets/overlay/scenes.json` (anchored to lyric phrases, so they follow timing fixes). Frames are named by absolute frame index, so re-render only the affected range: `--ranges`, `--cuts` or `--sections`.
- **Assembly is cached.** `assemble.py` caches per-cut segments and per-section chunks under `video/build/`, keyed by content hashes. Only what changed is rebuilt; the final mp4 is a stream-copy concat plus audio. `--list` shows which chunk covers which time.
- **Missing plates degrade gracefully.** The storyboard resolves `v:name` to `<name>-fast.mp4` → `<name>.mp4` → its still (Ken Burns). A quota stop or a filtered clip never blocks a full render; regenerate later and only those shots rebuild.

The fix loop: identify the time or cut → edit the storyboard row, the scene/layer or the asset → re-render overlay frames for just that range if the overlay changed → re-run the same `assemble.py` command → check that only the expected chunks say `rebuilt`. Use `--rebuild` only when you deliberately change something global (grade, resolution).

## Bundled resources
- `scripts/beatmap.py` – librosa beat map → `beats.json`
- `scripts/drops.py` – music events → `drops.json`: bass **drops**, **breaks**, **beat changes** (percussive density up/down), **builds** and **hit runs** (rapid even hard hits; the best ~1 per minute are `selected`), strength-ranked, plus a chart to check them by ear
- `scripts/lyrics.py` – MLX Whisper (Apple Silicon; faster-whisper elsewhere) → word and line timings aligned to the user's lyrics text; `--separate` isolates vocals with Demucs and **keeps the stem** at `assets/audio-analysis/vocals.wav`
- `scripts/align_lyrics.py` – CTC forced alignment (torchaudio MMS_FA) of the lyric text to the vocal stem → precise word timings
- `scripts/curate_lyrics.py` – words → kinetic phrases + full-line subtitles, with a vocal-onset guard (no phrase starts in silence) → `assets/overlay/lyrics.json`
- `scripts/lyric_timing_chart.py` – vocal-loudness charts with every phrase start marked, for verifying sync by eye
- `scripts/gemini_still.py` – Nano Banana stills (`--ref` for consistency, `--dry-run`, `--list-models`)
- `scripts/gemini_video.py` – one Veo 3.1 plate (image-to-video or ingredients), audio stripped, cost-capped
- `scripts/veo_batch.py` – sequential plate batch from `video/plates.json`; skips finished plates, stops on the daily quota
- `scripts/cost_ledger.py` – ledger, caps and backoff (run it directly to print the spend)
- `scripts/render_overlay.mjs` – Playwright `seek(t)` → transparent PNG frames (`--scale 2` for 4K, `--ranges`/`--cuts`/`--sections` partial re-renders, `--frames` contact sheets, `--layers` to isolate layers, `--scenes`)
- `scripts/contact_sheet.py` – tiles frames or video timestamps into a review image
- `scripts/assemble.py` – cached build: storyboard.json → segments → section chunks → concat + original mp3 (`--jobs`, `--codec h264|hevc`, storyboard `tail` for an end card after the song)
- `assets/world3d.js` – the 3D layer (three.js, fat lines): line ribbons, wire floor, swarm, wireframe scenes (fired, crash, progress, won), and tiltable 2D panels. The overlay passes it a per-frame state from `direct3d(t)` + `panelPose(t)`
- `scripts/plate_features.py` – per-plate features for plate-aware graphics: line segments, vanishing point, person silhouette/face/joints (macOS Vision), contours, bright spots; videos sampled every 0.2 s with gap filling, smoothing, optical-flow tracked contours/lines (ids) and in-clip cut detection → `assets/plate-features/index.json`; `--debug-video DIR` draws the tracking on each clip
- `assets/overlay-template.html` – the starter overlay (seek(t) contract, DPR-aware for 4K, scene engine, lyric backing band)
- `assets/scenes-template.json` – starter lyric-scene timing file
- `assets/fonts/` – the two OFL faces used by highlight lyrics and thumbnails (Big Shoulders Display for signage/split-flap, Share Tech Mono for terminal readouts) with their licences; copy to `assets/overlay/fonts/`
- `assets/make_thumbnail-example.mjs` – code-drawn 16:9 YouTube thumbnails from video frames (lock-on reticle, agent mesh, split-flap or slam title, typed hook); several A/B variants in one run
- `assets/make_storyboard-example.py` – worked storyboard generator (sections → downbeat-snapped cuts, LYRIC_CUES, plate fallback, usage counts)
- `references/look-bible.md` – the default look, ban list and theme-merge rules. **Read at step 3.**
- `references/shot-grammar.md` – section grammar, cut rules, lyric-matched shots, storyboard.json schema, failure modes. **Read at step 4.**
- `references/prompts.md` – still, character-sheet, Veo motion, overlay and thumbnail prompts. **Read at steps 5–7 and 11.**
- `references/gemini-api.md` – models, prices, budget tiers, caps, quotas, filters. **Read before any paid call.**
- `references/shorts.md` – a vertical 9:16 YouTube Short (~1–2 min) cut from a finished video: audio edit with seamless splices, bass-drop detection driving cuts/FX, edit-map remapping of lyrics, 9:16 recomposed stills, Shorts UI safe area, and a seamless loop ending. **Read when the user wants a Short, Reel, TikTok or vertical version.**
- `references/overlay-contract.md` – the seek(t) rules, helper API and scenes. **Read at step 7.**
- `references/case-study-escape-velocity.md` – lessons from another Claude-made music video (Midjourney + Seedance stack): written character canon, casting call, plate prompt formula, colour in / look in post, storyboard row fields, through-line device, 2.5D parallax, art-director loop, multi-agent fan-out and its cost, and what doesn't transfer (audio-driven lip-sync). **Read at intake for a new video, and when planning a multi-agent run.**
- `references/lyric-typography.md` – highlight lyrics instead of subtitles: frequency, which lines, style ↔ meaning (type / split-flap / slam / anchored / scene-owned), per-character timing, layout, fonts, the split-flap recipe, pitfalls. **Read at step 7.**

In the commands below, `$SKILL` is this skill's directory. Run everything from the user's project root.

## Project layout (created in the user's cwd)
```
assets/original-music/<song>.mp3      the master audio (never re-encoded before the final mux)
assets/audio-analysis/beats.json, lyrics-words.json (+ .whisper.json backup), lyrics-lines.json, vocals.wav
assets/still-images/                  Gemini stills + *.prompt.txt
assets/video-clips/                   Veo plates (no audio): <name>.mp4 (lite), <name>-fast.mp4 (polish)
assets/overlay/overlay.html, lyrics.json, scenes.json, frames/
assets/thumbnail/                     YouTube thumbnail variants
assets/cost-ledger.json
video/bible.md, lyrics.txt, plates.json, storyboard.md, storyboard.json, prompts/, contact-sheets/, tools/
video/build/                          assembly cache; safe to delete, it just rebuilds
out/<song-slug>.mp4, out/lyric-check.mp4
```
If the folder already holds another video's assets, ask whether to use a per-song subfolder (`assets/still-images/<slug>/`, `video/<slug>/`, `assets/overlay/<slug>/`) so videos don't overwrite each other. Pass the matching paths to the scripts.

## Workflow

### 0. Intake
Ask for anything the user hasn't already given. Use AskUserQuestion where there are clear options:
1. **The mp3.** Look for candidates first (`assets/original-music/*.mp3`, `*.mp3` in cwd, recent files in `~/Downloads`) and offer them.
2. **Lyrics**: a file, pasted text, or "extract them". Pasted Suno lyrics give exact spelling; timing always comes from the audio (step 2b).
3. **Theme and styling notes**: palette, world, mood, references, any recurring character. These merge into the bible.
4. **Subject / world / hook image**: one subject, one place, one lyric picture. Offer to propose these from the lyrics.
5. **Resolution**: 1080p, or a **4K master** (overlay rendered at 2×, plates upscaled; needs ~20 GB free disk for a 4-minute song — check `df -h .`).
6. **Budget tier**: code-only (< $1), lean hybrid (≈ $4), polish (≈ $15–20 with ~20 plates on Veo Fast 1080p). See `references/gemini-api.md`.

**Checkpoints: the user directs with short notes.** One human with taste plus an agent production team works best when the human's attention goes to a few decisive notes, each made on something concrete. Stop for a note at:
1. **the casting call:** a contact sheet of 2–3 looks (step 5);
2. **the storyboard:** `storyboard.md`, with lyric, type mode, plate, camera and motion source per shot, plus the chapters and the through-line device (step 4);
3. **the stills:** a contact sheet, before any Veo spend;
4. **the first full render:** a sound-off contact sheet plus the lyric-check video.

Apply notes as data edits wherever possible. (Case study: `references/case-study-escape-velocity.md`.)

### 1. Setup check
```bash
ffmpeg -version | head -1; uv --version; node --version; df -h . | tail -1
(cd "$SKILL/scripts" && [ -d node_modules ] || (npm install && npx playwright install chromium))
uv run "$SKILL/scripts/gemini_still.py" --list-models   # free; confirms the key works and the model IDs exist
```
The key comes from `GEMINI_API_KEY` in the environment or any `.env` up the tree.

### 2. Beat map
```bash
uv run "$SKILL/scripts/beatmap.py" "assets/original-music/<song>.mp3" --out assets/audio-analysis/beats.json
```
Tell the user the BPM, bar length, duration and the section guesses. Section labels are energy guesses, not verse/chorus; map them to song structure with the lyric timings (vocal entries mark verses and choruses) and confirm with the user.

Then the music events — what happens at the bar lines:
```bash
uv run "$SKILL/scripts/drops.py" "assets/original-music/<song>.mp3"     # → assets/audio-analysis/drops.json + video/contact-sheets/drops.png
```
Read the chart: red = drops, orange = breaks, magenta = beat changes, green = builds, blue spans = hit runs (dark = selected). Each strong drop should sit where the bass/kick lands after a gap; if Suno's mix makes the detector too eager or too shy, re-run with `--drop-db` / `--break-db` / `--groove-ratio`. Tell the user the 3–5 biggest drops (these are the moments the video should hit hardest) and use breaks and drops to confirm the section map (a chorus usually *starts* on a drop, a pre-chorus or bridge on a break).

### 2b. Lyrics: text, then precise timing, then verification
Users notice immediately when a lyric pops up before it is sung. Whisper timestamps alone are not good enough: they start words 0.3–1 s early after pauses, and every word Whisper missed gets spread evenly ("interp"). So:
```bash
uv run "$SKILL/scripts/lyrics.py" "assets/original-music/<song>.mp3" --lyrics-text video/lyrics.txt --language en --separate
uv run "$SKILL/scripts/align_lyrics.py" --lyrics-text video/lyrics.txt          # forced alignment on vocals.wav
uv run "$SKILL/scripts/curate_lyrics.py" --lyrics-text video/lyrics.txt         # phrases + onset guard
uv run "$SKILL/scripts/lyric_timing_chart.py" --words                          # → video/contact-sheets/lyric-timing-NN.png
```
- No user lyrics? Run `lyrics.py` without `--lyrics-text` first, write the transcript to `video/lyrics.txt`, fix obvious mishearings, list your guesses for the user to proofread, then run the chain above.
- **Read every timing chart.** Each red phrase marker must sit on a rise of the vocal curve; a marker in a flat stretch is early. Fix stragglers with `curate_lyrics.py --nudge "idx:seconds"` (chart labels carry the index). Repeated robot/spoken intros are ambiguous — say which placement you chose.
- Make `out/lyric-check.mp4` (lyric + scene layers only over the song, ~1 min to render) so the user can confirm sync without waiting for a full build:
  `node render_overlay.mjs ... --scale 1 --layers lyric,scene --out <scratch>` then ffmpeg the PNGs over a colour bg with the mp3.

### 3. Bible
Read `references/look-bible.md`. Write `video/bible.md`: fill subject, world and hook, then merge the user's theme notes using the merge rules. Reserve one colour for the human subject if there is one (e.g. purple hair as the only purple). Copy the final tokens into the overlay's `:root` in step 7.

### 4. Storyboard
Read `references/shot-grammar.md`. Generate the cut list with a script (start from `assets/make_storyboard-example.py`, saved as `video/tools/make_storyboard.py`):
- 1.5–4 s cuts on downbeats; ~90 cuts for a 4-minute song.
- **Music events re-pace the base pattern** (the example script does this from `drops.json`): a hard cut on every drop with strength ≥ 0.3, then 2 one-bar cuts; never a cut running across a drop; hold ≥ 2 bars from a strong break; `beat_change` up → 1-bar cuts, down → doubled lengths until the next event. Put the hero/performer shots on the biggest drops (the example does it: `HERO` pool on drops with strength ≥ `HERO_MIN`, applied after the lyric cues because drop > vocal phrase).
- **Rapid cuts on selected hit runs**: the example's `rapid_cuts()` puts a new image on every hit (a `RAPID` pool of strong plates with varied crop/flip, plus a black code-only frame for the overlay to play on), never shorter than ~6 frames, then the interrupted shot resumes. Only the `selected` runs: rapid cutting on every fill turns into noise. If the best run is under the end card or a lyric scene that must stay readable, deselect it rather than strobe over text.
- **Vocal sync**: lyric-cue shots are split in so they arrive with the phrase; the vocal guard moves plain cuts off sung words. The events go to `storyboard.markers.drops` for the overlay.
- **The subject performs, never lip-syncs.** Veo can't hear the song, so any "singing" clip shows invented words and looks wrong. Use dancing, walking, turning, hair-whip and over-the-shoulder shots ("mouth closed" in prompts), recurring every 3–4 cuts.
- **Lyric-matched shots** (`LYRIC_CUES`): when a line has a concrete image ("workers fired", "bunker doors sealing", "nobody left to shop"), the cut on screen at that phrase shows it. This is what makes the video feel directed.
- Spread plates: aim for ≤ 3 uses per plate except the performer's dance clips; vary reused clips by `offset`, `crop`, `hflip`. The script prints a usage count.
- **Board in chapters and plan a through-line device:** one recurring graphic that tracks the story and pays off at the climax (`references/shot-grammar.md`). Two clips never start from the same frame.
- Write `video/storyboard.json` + `video/storyboard.md` (one row per shot: lyric, type mode, plate, camera, motion source) and `video/plates.json`.

Show the user: cut count, plates, stills, estimated cost. **Get approval before any paid call.**

### 5. Stills
Read `references/prompts.md`. For a person, start with a **casting call**: 2–3 look directions, each as a turnaround, a walk and a face sheet, judged at thumbnail size. Then write the winner into the bible's `Canon` block (with an explicit physical descriptor) and paste it into every prompt. Every plate prompt declares its empty area for type and ends with the bible's `Style words`. Keep inputs in full colour and photographic; the look is applied in post. Subject reference first (a Nano Banana **Pro** character sheet is worth it for a person), lock it, then every scene with `--ref` (two refs — the sheet plus a good scene of the subject — hold hair/wardrobe colour much better than one).
```bash
uv run "$SKILL/scripts/gemini_still.py" --bible video/bible.md --prompt-file video/prompts/env-1.txt \
  --ref assets/still-images/subject-ref.png --tier pro --out assets/still-images/env-1.png
```
Review every still on a contact sheet: baked-in text (screens/tickers in the scene invite it — say "no screens with numbers"), letterbox bars (say "full-bleed, no black bars"), colour drift of the subject's signature feature (hair went blond/grey in ~40% of first tries — add a "CRITICAL: …" line), hands. Regenerate rejects; generate 3–4 at a time in parallel.

### 6. Veo plates (skip on code-only)
Read `references/gemini-api.md`. Batch from the manifest, sequentially:
```bash
uv run "$SKILL/scripts/veo_batch.py" video/plates.json --tier lite --res 720p          # first pass
uv run "$SKILL/scripts/veo_batch.py" video/plates.json --tier fast --res 1080p name …  # polish keepers → name-fast.mp4
```
Prompt only the camera move and one moving part. Check every clip with `contact_sheet.py --video … --times 0.5,3,5.5,7.5`. Expect: occasional safety-filter rejections on realistic face close-ups (not charged — use a different still/framing), and a **daily request quota** (~10 Lite calls/day on a Tier 1 key, Fast has a separate quota; resets at midnight Pacific) — the batch stops cleanly; finish the render with still fallbacks and re-run the batch the next day. 402 = prepaid credits depleted.

### 7. Overlay
Read `references/overlay-contract.md`. Copy `$SKILL/assets/overlay-template.html` → `assets/overlay/overlay.html` and `$SKILL/assets/scenes-template.json` → `assets/overlay/scenes.json`, then:
- Set the `:root` tokens; put every non-lyric string in one `COPY` block and spell-check it.
- Restyle the base HUD for the theme as `LAYERS` entries (e.g. market ticker, agent log, counters).
- **Write lyric scenes.** Go through the lyrics line by line and give most lines with a concrete idea their own scene in `SCENES` + `scenes.json`. The HUD should be the base you return to, not something on screen the whole song (users find that monotonous). Scenes use the right half by default; the lyric stays left (`lyric` per scene).
- Keep everything a pure function of `t`.
- **Lyrics are highlights, not subtitles (default).** Read `references/lyric-typography.md`.
  - Give text to about 1 in 3 phrases (one card every ~6–8 s; the hook, numbers/verdicts, machine voice, lines about the human). The other lines get none.
  - Match the style to the meaning: `type` (terminal, per character on the sung syllables), `flap` (split-flap board), `slam` (hook words landing on the beat) or `anchor` (pinned to the tracked performer). Let a scene own a phrase when it can embody it.
  - Bundle two OFL fonts (a signage display face plus a terminal mono).
  - Cards overlay the animation; there is no reserved lyric band.
- **3D layer** (on by default when `world3d.js` sits next to the overlay; `?gl=off` disables it). Read the 3D and plate-awareness sections of `references/overlay-contract.md`. Use only lines, dots and wireframes, no shaded or "physical" objects. Balance three classes:
  - **always flat 2D:** lyrics, titles, end card and FX;
  - **2D that shifts into 3D:** the scene stage and HUD panels swing in on scene changes, kick on drops, snap on hit runs, drift in loud sections, and go flat on breaks;
  - **native 3D lines:** ribbons, floor, swarm and wire scenes. No hero sphere or object (rejected twice: chrome blob, dot globe).

  Adapt `direct3d(t)`/`panelPose(t)` per song: when ribbons, floor and swarm come in, the story colour, and which 3–5 scenes go wireframe.
- **Plate-aware graphics**: after the plates exist, run `uv run "$SKILL/scripts/plate_features.py" assets/still-images/*.png assets/video-clips/*.mp4`. For every performer clip, run it with `--debug-video video/contact-sheets/track` and Read a sheet of the result: the box, face circle and contours must stay on her through the motion (see "Tracking on video plates" in the contract). The template's `plateFX` layer then follows the picture, including the moving subject in video plates (`sampleAt` interpolation, face-anchored reticle, one tracked contour per cut). Re-run it after any clip is (re)generated: it is cached per file, so only new clips are analysed. Personalise its strings for the song. Keep the **contour budget**: most cuts get none, some get an animated trace, a few get text. Contours everywhere read as noise.
- **Hit the music events too**: the template's `music` layer reads `storyboard.markers.drops` (flash + shock ring + edge pulse on drops, a hush on breaks, a scan sweep on beat changes, ticks tightening during builds, and on selected hit runs a per-hit strobe: alternating 2-frame flashes, a strobing border, a hit counter, slice glitch), and `lyric` slams a phrase that starts on a drop. Scenes can use `lastEvent(t, 'drop')` / `eventNear(t, kind, win)` to time their own big moves (a counter jumping, doors slamming) to the drop rather than to an arbitrary second.

### 8. Contact-sheet critique loop (the art-director pass)
Review real rendered frames, never the code: render, look, write the fixes, apply them, re-render the same moments. For motion design, work chapter by chapter, and judge against the bar "does this graphic explain the words being sung?". Check 10–20 moments including several scenes, at scale 1 (fast):
```bash
node "$SKILL/scripts/render_overlay.mjs" --html assets/overlay/overlay.html --out video/contact-sheets/raw --frames 2,14.1,31.5,45,62.3,98,140,201,230
uv run "$SKILL/scripts/contact_sheet.py" video/contact-sheets/raw/*.png --out video/contact-sheets/overlay-01.png
```
Read the sheet: lyric overlapping a scene, graphics running off-frame, type outside the safe area, illegible lyrics. For a real composite, assemble a short window (`assemble.py … --start 81 --end 108 --out out/preview.mp4`) and sheet it — lyrics over bright fog/windows need the backing band.

### 9. Full render and assembly
```bash
node "$SKILL/scripts/render_overlay.mjs" --html assets/overlay/overlay.html --out assets/overlay/frames --scale 2 --workers 8 --end <duration+tail>
uv run "$SKILL/scripts/assemble.py" video/storyboard.json --out out/<song-slug>.mp4 --jobs 4
```
For 4K set `"width": 3840, "height": 2160` in storyboard.json and render with `--scale 2`. Measured on Apple Silicon for a 4-minute song: overlay ~50 fps (≈3 min, ~2.5 MB/frame ≈ 18 GB), full 4K assembly ≈ 17 min, final file ≈ 1–1.2 GB. Then follow the fix loop; `--start/--end` previews build only the overlapping chunks.

Sanity checks: `ffprobe` resolution/codec/duration (song + `tail`), then a "sound-off" contact sheet at ~12 timestamps that you Read. If the picture has rhythm and variety with no sound, it's working.

### 10. Report
Output path, cut and plate counts, plates still on still-fallback (and the command to finish them), spend (`uv run "$SKILL/scripts/cost_ledger.py"`), lyric lines you guessed, and next tweaks.

### 11. YouTube package (offer it)
- **Thumbnails for an A/B test** (YouTube Studio → Test & compare, up to 3): draw them in code from real frames of the video with its tracked features and the overlay's fonts, so every word is spelled right. Copy `assets/make_thumbnail-example.mjs` to `video/tools/` and edit its `VARIANTS` (clip, time, framing, hook, title as a split-flap `board` or a big `slam`). Test three different *concepts* (song title / shock headline / verdict), not three frames of one idea, and check them side by side at shelf size. Pick frames with the mouth closed and the face clear of hands.
- **Thumbnail (generated alternative)**: Nano Banana Pro with the subject refs. It renders a short title correctly — still Read the result and check spelling. What works: a tight face close-up with direct eye contact on one side, 2–4 words of title on the other, one story element behind (e.g. a crashing red chart). Generate 2–3 variants; if one comes back empty, retry once. Export 1920×1080 JPEG (< 2 MB) and check it at ~246 px wide. See `references/prompts.md`.
- **Description**: hook lines, what the song is about, chapters from the song map (first at 0:00, ≥ 3 chapters, each ≥ 10 s), credits (Suno, Gemini/Veo, code-driven motion graphics), 10–15 hashtags with the 3 most important first, and a reminder to tick YouTube's altered/synthetic content disclosure for realistic AI people.

## Optional: parallel exploration (only when the user opts in to multi-agent work)
ESCAPE VELOCITY fanned the creative steps out across agents:
- research with a fact-check verifier;
- 3 director agents boarding the song independently (different angles), then judges and a head director merging the best;
- one animator per chapter plus an art-director agent that renders and reviews frames, and a fixer.

It works, and it's expensive: about $626 of Claude usage at API prices for a 5-minute video, 48% of it animation agents, and 96% of all tokens were cache re-reads of long contexts. Offer it with those numbers, never start it unasked, and keep the main session lean (delegate render → review → fix loops). Details: `references/case-study-escape-velocity.md`.

## Reusing for the next song
Keep the bible's genre rules, the overlay vocabulary and the scene library (scenes are reusable — re-anchor them in scenes.json). Per song: new mp3 → beats.json → lyrics chain (2b) → subject/world/hook → storyboard script → stills → plates → scenes → render.

## Common failures
- **Lyrics appear before they're sung.** Whisper timing only. Run `align_lyrics.py` + `curate_lyrics.py` and Read the timing charts.
- **"She's singing something else."** A Veo singing/lip-sync clip. Replace it with a performance shot; real lip-sync needs a dedicated lip-sync model fed the song audio.
- **Lyrics feel like subtitles / monotonous.** Text on every line in one fixed band. Switch to highlight cards (≈1 in 3 phrases), mix the styles and positions, and drop the full-line caption (`references/lyric-typography.md`).
- **HUD on screen all the time.** Add lyric scenes; the HUD is the base you return to.
- **Identity or colour drift.** Pass the locked still(s) with `--ref`/`--image` every time; two refs + a "CRITICAL" line for the signature feature, plus the written `Canon` and an explicit physical descriptor in every prompt (references alone let identity drift).
- **Clips come back grey, flat or lifeless.** The input stills were stylised (monochrome, halftone, dither). Generate colour photographic plates and apply the look in post (grade or print pass).
- **The video has no arc.** The scenes are good but nothing builds. Add a through-line device that changes state across the chapters and pays off at the climax (`references/shot-grammar.md`).
- **Text or letterbox bars in generated images.** Ban both explicitly; Read every still.
- **Mushy Veo motion.** The prompt asked for a new scene. Ask only for camera movement plus one moving part.
- **Veo 429 / 402 / filtered.** Daily quota (wait), credits (top up), safety filter (reframe). The storyboard falls back to stills meanwhile.
- **Overlay renders at < 5 fps.** All workers sharing one browser serialise on its compositor. `render_overlay.mjs` now uses one browser per worker and reads the canvas directly — keep it that way.
- **3D layer is black, missing or slow.** `render_overlay.mjs` prints the GL renderer. "SwiftShader" means software rendering (~15 fps at 1080×1920): use `--gl gpu` on a Mac (Metal), or `--gl-scale 0.5`. A `pageerror` from three.js stops the render, so read it. With `?gl=off` the overlay falls back to 2D only.
- **Brackets or the face circle jump, lag or slide off the dancer on video plates.** The overlay snaps to samples instead of interpolating, or the features are stale (0.5 s, pre-tracking). Re-run `plate_features.py` (versioned cache), use `sampleAt` + the face box, and check with `--debug-video`.
- **Graphics float off the picture.** `plateAt(t)` must replicate `assemble.py`'s transform (cover-crop, Ken Burns `z0→z1` × `crop`, drift, `hflip`; video cover + crop, time = offset + age). If you change assemble's motion presets, change `KB` too.
- **3D lines invisible over bright plates.** WebGL lines are 1 px; `world3d.js` uses three's fat lines (`LineSegments2`) with widths in CSS px, so keep them, and raise the width rather than the opacity.
- **Blurry 4K overlay.** The canvas must be sized `W*devicePixelRatio` with `setTransform(DPR…)` in seek (the template does this).
- **Lyric unreadable over bright plates.** Keep the blurred backing band; limit lyric width during scenes.
- **Cuts feel random.** They're off the downbeats, so re-snap them in storyboard.json.
- **The drop doesn't land.** The bass hits mid-shot or a dissolve smears it. Run `drops.py`, regenerate the storyboard (hard cut + burst on drops), and make sure the overlay's `music` layer gets `markers.drops`.
- **Matched shot shows up a bar early / late.** The cue swapped a whole cut. Let the storyboard split the cut at the beat nearest the phrase start (example script), and check lyric timing first.
- **Non-deterministic frames.** A timer, CSS transition or `Math.random` got into the overlay. Re-read the contract.
- **Brightness jumps between chunks / the loop seam doesn't match.** Mixed colour ranges: stills came out full-range (`yuvj420p`) and video limited, and `xfade` converted mixed chunks to full range. `assemble.py` now forces every segment to limited-range `yuv420p` (segment cache `seg-v2`, so the first assemble after the update rebuilds all segments).
- **Everything rebuilds after a small fix.** Something global changed (grade, whole overlay re-rendered). Check `video/build/manifest.json`.
- **Disk full mid-render.** 4K overlay frames are ~18 GB per 4 minutes plus ~5 GB build cache; `video/build/` and old outputs are safe to delete.
- **Waiting on a background job.** Poll with `pgrep -f "[a]ssemble.py"` (bracket trick) — a plain `pgrep -f assemble.py` matches the waiting loop itself and never ends.
- **Overspending.** Count Veo seconds in the storyboard before the batch, not after.
