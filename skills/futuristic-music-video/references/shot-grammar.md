# Shot grammar and storyboard rules

## Three layers, always in this order
- **Plate** — a locked Gemini still or a 4–8 s Veo clip. Dark glass, phosphor, chrome, fog, one light. Used for chorus hits and the opening.
- **Machine** — code-drawn HUD, schematics, orbiting gimbal parts, fluid ribbon driven by loudness, lyric words springing in on the beat. **Most of the runtime.**
- **Glue** — wipes, scanlines, beat flashes, light leaks, 6-frame dissolves. Also code (overlay) or ffmpeg (dissolves).

## Cut rules
- Cuts are **1.5–4 s** and **snap to downbeats** from `beats.json`. Flashes and lyric pops land on onsets.
- A 3-minute song is roughly **50–70 cuts**; at most **6–8** of them use Veo.
- **One subject, one world, repeated.** The repetition is what makes it feel directed instead of shuffled.
- Chorus plates are **cropped and regraded, not regenerated**, the second and third time.
- Test: watch once with the sound off. If it still has rhythm, the picture is working.
- **Place everything on the measured grid.** Songs drift in tempo (ESCAPE VELOCITY accelerated from 131.5 to 133.9 BPM). Cuts snap to the tracked `downbeats` array, and overlay events to `beats`/`onsets`. Never compute positions as `n * 60 / bpm`; `bpm` is only a summary.
- **Two clips never start from the same frame.** When a plate is reused, give each use a different `offset` (and/or crop/flip), so no two cuts open on the same image.

## Board in chapters, with a through-line
- **Chapters are story beats** (6–10 for a 3–5 minute song), set on top of the song sections: e.g. boot-up, the layoffs, the hook, the crash, the bunker, the reckoning, shutdown, the utopia card. Each chapter gets a scene family and a palette lean. Chapters become the YouTube chapters.
- **One through-line device** recurs through the whole video and pays off at the climax. It's a single graphic that tracks the story:
  - ESCAPE VELOCITY: a split-flap board counting down "18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS" that finally flips to "THERE IS NO UNDERCLASS" as the catwalk lifts off;
  - Agents in the Loop: the "HUMANS IN THE LOOP %" readout falling to 0 at the terminal shutdown.

  Plan its states in the storyboard (where it appears, what it reads, the flip).

## The storyboard row
Each shot carries, at least:
- **lyric**: the words under it;
- **type mode**: which highlight card style, or none (`lyric-typography.md`);
- **plate prompt**: the scene, the declared empty area for type, and the style words (`prompts.md`);
- **camera**;
- **motion source**: Veo clip, still with 2.5D parallax or Ken Burns, or a code-only frame.

In this skill these live in `storyboard.json` (`source`, `motion`, `offset`, `overlay`), `video/plates.json` (prompts) and `assets/overlay/highlights.json` (type). `storyboard.md` is the human-readable board for the approval checkpoint: one row per shot with those columns, plus a contact sheet of the plates.

## Music events: cut on what the song does, not only on the grid
A steady downbeat grid makes every bar feel the same. `scripts/drops.py` finds the bars where the music changes, and the edit should change with it:

| Event (`drops.json`) | Heard as | Edit | Overlay |
|---|---|---|---|
| **drop** | kick + bass slam back in after a gap | hard cut (`transition: cut`) exactly on it; hero/performer plate; 2 one-bar cuts after it; no cut may span it | flash (< 40%), shock ring, edge pulse; a lyric starting within a beat slams in |
| **break** | the low end falls away | hold the shot ≥ 2 bars; a slow plate or one idea | hush: dark edge vignette for a bar, thinner HUD |
| **beat_change** up | drums double / come in | cuts shorten to 1 bar until the next event | scan line sweeps up |
| **beat_change** down | half-time, drums drop out | cut lengths double until the next event | scan line sweeps down |
| **build** | 4 bars of rising hats/risers into a drop | rising cut rate, push-ins (`crop` steps up), pre-drop black frame optional | edge ticks tighten toward the drop |
| **hit_run** (selected only) | 4+ hard, evenly spaced hits in a row: stabs, a "bum bum bum" chant, a snare fill | a new image on EVERY hit (≥ 6 frames each; skip hits if faster), hard cuts, varied crop/flip, a black frame in the mix; the interrupted shot resumes after | per-hit strobe: alternating 2-frame white/accent flashes, strobing border, hit counter, slice glitch |

Hit runs are the one place the edit goes faster than the bar grid, so ration them: `drops.py` ranks them by hits × hit strength and selects about one per minute, at least 8 bars apart. Don't strobe over the end card, a title or a lyric scene that has to be read.

Priority when rules collide: **drop > sung phrase > downbeat pattern.** Use the 3–5 strongest drops for the most important shots of the video (the first chorus hit, the hook image, the final chorus). Splices or section changes that land on a louder bar act as drops too.

## Vocals: the third clock
- Lyric timing comes from forced alignment (`align_lyrics.py`), never raw Whisper.
- A lyric-matched shot arrives **with** its phrase: split the cut on screen at the beat nearest the phrase start (downbeat preferred) rather than swapping the whole cut, which shows the image a bar early or late.
- Don't cut in the middle of a sung word unless a drop forces it; move the cut to the nearest free beat (vocal guard). Held notes and wall-to-wall vocals are the exception.
- A vocal entry after a break is a natural cut point even off the downbeat (a pickup), as long as it is on a beat.

## Section table
| Section | Length | Picture | Why |
|---|---|---|---|
| Intro | 4–8 s | Black, one line draws itself, first plate fades up under a ring | Hook before the vocal |
| Verse | 1.5–3 s cuts | Machine layer dominates, lyric word, plate masked: small PiP window or inside the negative space of big type | Cheap, fast, readable |
| Pre-chorus | building | Parts assemble, ribbon thickens with loudness, cut rate rises | Motion earns the drop |
| Chorus | 2–4 s | Hero plate full frame, overlay thins out (UI animates away) | Spend the Veo seconds here |
| Bridge | one idea | A schematic or one slow plate, fewer cuts | Rest, then return |
| Final chorus | same plates, new crop | Tighter type, faster flashes, same subject | Reuse, don't regenerate |
| Outro | ~4 s | Parts disassemble, last word, fade to black | Designed ending |

If `beats.json` section guesses look wrong (Suno songs often have long intros or tag endings), ask the user for timestamps or correct them by listening cues in the lyrics; the human picks which beats matter ("big gimbal rotation on the chorus downbeat at 64.2 s").

## Performer and lyric-matched shots
- **No lip-sync from Veo.** Veo never hears the song, so a "singing to camera" clip shows her singing other words, and viewers notice instantly. Performer shots are dancing, walking toward camera, hair whips, turning to camera, silhouettes against screens — prompt "mouth closed, she does not sing". (Real lip-sync needs a dedicated lip-sync model fed the song audio; offer it as an optional upgrade.)
- **Lyric cues.** Walk the lyrics and give every line with a concrete picture a matching plate ("a million workers fired" → workers carrying boxes out of the tower; "bunker doors sealing" → a vault door closing; "who buys the product" → an abandoned mall). Keep the mapping as data (`LYRIC_CUES`: phrase → plate) applied after the base cuts are built, so it follows lyric re-timing.
- **Spread the plates.** ~25 sources for ~90 cuts felt varied; one clip used 7× felt repetitive. Print a per-plate usage count from the generator.
- Pair each graphic scene (overlay) with a matching plate where possible — the plate tells it, the graphic quantifies it.

## storyboard.json schema
`scripts/assemble.py` reads this. Times in seconds, snapped to downbeats.
```json
{
  "song": "assets/original-music/Song.mp3",
  "fps": 30,
  "width": 1920, "height": 1080,
  "overlay_frames": "assets/overlay/frames",
  "dissolve_frames": 6,
  "grade": "default",
  "cuts": [
    {"start": 0.0, "end": 4.2, "section": "intro", "layer": "machine",
     "lyric": "", "visual": "black, one teal line draws across", "camera": "static",
     "source": null, "veo": false},
    {"start": 4.2, "end": 7.9, "section": "intro", "layer": "plate",
     "visual": "subject behind smoked glass", "camera": "slow push",
     "source": "assets/still-images/subject-ref.png", "motion": "kenburns-in", "veo": false},
    {"start": 30.1, "end": 33.8, "section": "chorus", "layer": "plate",
     "source": "assets/video-clips/chorus-a.mp4", "offset": 0.0, "crop": 1.0, "veo": true},
    {"start": 41.0, "end": 43.2, "section": "verse", "layer": "machine",
     "source": "assets/still-images/env-1.png", "pip": true, "veo": false}
  ]
}
```
Field notes:
- `width`/`height`: 3840 x 2160 for a 4K master (render the overlay with `render_overlay.mjs --scale 2`).
- `tail` (optional, top level): seconds of picture after the song ends, e.g. an end card; the audio is padded with silence.
- `song_map` / `markers` (optional, top level): named sections and fixed times the overlay can read (e.g. a shutdown or end-card time).
- `source: null` with `layer: machine|glue` → background is the bible `--bg` colour; overlay carries the shot.
- `source` image → Ken Burns move (`motion`: `kenburns-in|kenburns-out|drift-left|drift-right|static`).
- `source` video → trimmed from `offset`; loops if the cut is longer than the clip. `crop` > 1.0 zooms in (use 1.15–1.35 to make a repeated chorus plate feel new). `hflip: true` also helps reuse.
- `pip: true` → plate shown small in a framed window on `--bg` (verse treatment).
- `overlay` (optional): per-cut overlay control, e.g. `{"hide": ["gimbal"], "only": ["lyric","glue"], "density": 0.2}`. Use it for shot-specific fixes instead of code.
- `transition` (optional): `"cut"` for a hard cut into this shot instead of the default 6-frame dissolve. Use it for big hits — every drop cut gets one automatically.
- `drop` (optional, set by the generator): this cut starts on a bass drop.
- `flash` (optional, set by the generator): one of the rapid cuts inside a selected hit run.
- `markers.drops` (top level): the music events from `drops.json` (`{t, kind, strength, dir?, into?}`; hit runs add `end, hits[], spacing, selected`) — the overlay's `music` layer and lyric slam read them.
- `pip_side` (optional): `"left"` or `"right"` for PiP windows.
- `section` matters for the build too: `assemble.py` groups consecutive cuts with the same section into a cached chunk (max ~24 s). Chunk boundaries are hard cuts, which the overlay's section iris wipe covers. Use consistent section names (`intro, verse, pre, chorus, bridge, final, outro`).
- Gaps between cuts are filled with `--bg`. Cuts should be in time order; overlaps resolve with the later cut winning.

Also write `video/storyboard.md` as a human-readable table: `# | start | end | section | layer | lyric | visual | camera | source | veo`. Put the Veo count and estimated cost at the top.

## Failure modes
- **Identity drift** → always pass the locked subject still as reference, *and* paste the written canon plus a physical descriptor (age, skin tone, freckles) into every prompt. Neither words alone nor references alone hold it (`prompts.md`).
- **Clips come back grey or lifeless** → the input still was stylised (monochrome, halftone, dither). Feed colour, photographic stills; apply the look in post.
- **Text in the image** → video/image models spell badly. Ban text in prompts; burn lyrics in the overlay.
- **Mushy motion** → the Veo prompt asked for a new scene. Ask only for camera + one moving part.
- **Overlay fights the plate** → thin the overlay on chorus rows; full HUD on verses.
- **Cuts feel random** → the beat map was ignored. Snap every cut to a downbeat before judging taste.
- **Edit feels flat / the drop doesn't hit** → the cut pattern ignores the music events. Cut exactly on drops, hold on breaks, re-pace on beat changes (`drops.py` + example storyboard).
- **Too expensive** → count Veo seconds before the batch, not after.
- **Fake lip-sync** → a Veo singing clip. Replace with performance shots.
- **Same clip everywhere** → too few plates for the cut count; add lyric-matched plates or stills with Ken Burns.
