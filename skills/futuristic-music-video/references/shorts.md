# Vertical / YouTube Shorts versions

How to cut a finished 16:9 music video down to a 9:16 Short of about 1–2 minutes that loops. The worked
example is `youtube-shorts/` in the "Agents in the Loop" project. Copy its `video/tools/` as a starting point.

## Layout and folders
Use a sibling folder with the same structure (`assets/…`, `video/…`, `out/`) and its own build cache. Keep the
cost ledger shared. Everything below is data-driven like the main video, so fixes stay cheap.

## 1. Audio: cut the song, don't re-time it
- Write an `edit.json` of song-time ranges. Splice on downbeats.
  - If a vocal pickup crosses the downbeat, splice both sides at the **same beat phase** inside the bar (e.g. downbeat + 0.357 s) in a gap between words.
  - Check the word timings on both sides of every splice.
- Refine each splice by ±20 ms of waveform correlation, then join with a 30–80 ms equal-power crossfade. Score each seam on chroma similarity (aim for > 0.95) and RMS jump. A deliberate jump into a louder bar is fine; it works as a new drop.
- Render ±4 s previews of every seam and re-run `beatmap.py` on the edit. Beat spacing must stay constant across splices.
- **Loop tail:** start the Short a little into the song (e.g. 1.3 s). Append the song's opening 0 → 1.3 s as the last segment, with the final ring-out mixed under it. The file then ends on the sample where it starts, so a looping player has no seam.
- Produce an **edit map** (song time → Short time) and carry everything through it: lyric phrases, words, scenes (resolve lyric anchors on the full song first, then map to numbers), drops, downbeats and the song map. Never re-align lyrics.

## 2. Drops and beat changes
- Run `scripts/drops.py` on the original mp3 (the analysis is per bar: sub-150 Hz energy vs the two bars before → **drop** ≥ +3 dB / **break** ≤ −4 dB; percussive hit-rate change → **beat_change**; rising highs into a drop → **build**), then carry the events through the edit map like everything else.
- Use the drops to choose splice points too: a splice into a louder bar (or straight onto a drop) hides the edit and becomes a hit of its own.
- Drive the edit with drops:
  - a hard cut exactly on each drop, then 1-bar cuts for 2 bars;
  - longer holds during breaks;
  - overlay flash, shock ring and edge pulse;
  - a lyric "slam" (spring overshoot, shake, wider chromatic split) for phrases starting within a beat of a drop.

## 3. Pictures: recompose, don't crop
- Center-cropping a 16:9 plate to 9:16 keeps only 32% of its width and loses the subject. Regenerate each still with `gemini_still.py --aspect 9:16`, prepending a vertical bible section.
  - Pass refs in this order: the identity sheet first, then the original 16:9 still as the **look reference** ("the last reference image shows the established look… match it").
  - Composition notes: subject in the upper-middle, a quieter bottom third, the singer's whole figure inside the frame.
  - Nano Banana returns 768×1376.
- Lyrics: the same highlight rules as `lyric-typography.md`, slightly denser (the Short used 17 of 45 phrases). Every card stays inside the Shorts UI-safe area.
- Veo: `veo_batch.py --aspect 9:16 --plate-prefix short-`. Then run `plate_features.py` on the vertical clips (the same tracking pass: face reticle and brackets follow her as she dances). Lite 720p gives 720×1280; set `"sharpen": 0.6` on those cuts so `assemble.py` applies a light unsharp after upscaling.
- The contact-sheet tool letterboxes tall images into landscape tiles. Tile 9:16 stills in a portrait grid to review them.

## 4. Overlay: vertical fork
- `render_overlay.mjs --width 1080 --height 1920`. In the overlay, set `W=1080, H=1920`, and size the CSS to match.
- **Shorts UI safe area:**

  | Zone | What covers it |
  |---|---|
  | top ~140 px | search / menu |
  | bottom ~480 px | title, channel, description |
  | right ~140 px, from ~y 1000 | like / comment / share column |

  Keep all type out of these zones.
- Layout used:
  - HUD readouts in two rows under the top bar;
  - chart top-left, counter top-right, gimbal in the middle;
  - lyric scenes on a 940×920 stage at y 220. Landscape right-half scenes move there with one translate; full-frame scenes are rewritten.
  - Lyrics centered at y ~1265, wrapping to two balanced lines, with the subtitle under them;
  - ticker and tick rail just above the caption zone.
- Map the story clock (doom/mood) through the edit map, so the narrative arc follows the song even though sections were cut.

## 4b. 3D lines, panels and plate awareness in a vertical frame
- **Panels:** `stage` = the STAGE rect, `hud` = the top block (chart, counter, log, readouts). The tick rail, ticker and lyrics stay flat.
- **Ribbons and floor:** ribbons run at about 63% of the height. The 3D floor is about y 1400, under the lyric band, and gives way to the plate's own VP floor grid on corridor shots.
- **Contour text:** text along the singer's contour skips the lyric band (y ≈ LYR_Y −190 … +150), so it never fights the lyric.
- **Shutdown and loop:** after the shutdown the 3D layer is off. In the loop tail all 3D is gone and the panels are flat, so the last frame equals frame 0.

## 5. Making it loop
- Draw frame 0 as a strong hook: the title over the opening shot, with the HUD not built up yet.
- In the loop tail:
  - the end card glitches out;
  - a `REBOOT` line rewinds the timecode;
  - the title snaps in, so that the last frame equals frame 0 (`titleCard(-timeLeft)`).
- The loop-tail plate is the opening plate, offset to play the moments just before the opening cut's offset.
- Verify the first vs last frame (`ffmpeg … -lavfi ssim`, aim for > 0.95). Also build a clip of the last 3 s followed by the first 3 s, and watch and listen to it.
