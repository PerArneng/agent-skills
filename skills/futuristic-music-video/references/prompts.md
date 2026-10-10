# Reusable prompts

Every prompt starts with the full `video/bible.md` block. Brackets are filled per shot. Keep prompts short and concrete — one subject, one light, one motion.

## Three rules for every image prompt (from the ESCAPE VELOCITY case study)
1. **Character canon plus a physical descriptor, written out every time.**
   - Pasting the bible's `Canon` paragraph in every prompt that shows the performer keeps her consistent across shots: hair cut and colour, the one signature accent, each wardrobe piece, boots.
   - Add an explicit descriptor (age, skin tone, freckles, build).
   - Reference images alone are not enough: without the written descriptor, identity (even ethnicity) drifts from shot to shot. Keep passing `--ref` too.
2. **Declare the empty area for type.** Every plate states where the type will go ("the top half empty night sky", "negative space on the left third"). Highlight cards, HUD and scenes then have a clean place to sit.
3. **End with the video's style words, verbatim.** The bible's `Style words` line is one fixed family, appended to every plate:
   - palette with hex values;
   - one rule for the warm light ("one small red lamp as the only warm light");
   - grain ("fine silver grain");
   - finish ("cinematic 35mm film still");
   - always "no text, no letters, no logos".

   One consistent family is what keeps 100+ plates in one world.

**Keep inputs in full colour, and photographic.** Never generate stylised or degraded stills (monochrome, halftone, xerox, dither, bleach) to feed Veo: the clips come back grey and lifeless, and need recolouring. Apply the look in post (`look-bible.md` → Grade).

## Casting call (before locking the subject)
One batch of 2–3 look directions (e.g. three hair options), each rendered three ways:
- a turnaround;
- a walk toward camera in the video's main location;
- a face sheet.

Put them on one contact sheet and judge at **thumbnail size**: pick the silhouette that still reads small. Keep the signature colour a small accent, not the whole look. The winner's description becomes the `Canon` block.

## Director / storyboard (Claude does this itself; reuse the brief)
```
You are the editor of a fast futuristic music video. The song is finished. Do not generate video yet.
Read beats.json (bpm, downbeats, onsets, loudness, sections) and the lyrics.
Return a cut list of 1.5–4 s shots, every boundary on a downbeat.
At most [8] shots may be marked VEO; all others are CODE (machine/glue) or reuse a still/plate.
Repeat chorus plates (new crop/flip) instead of inventing new locations.
No on-screen captions in any image prompt — lyrics are burned in later by code.
Columns: start, end, section, layer, lyric, visual (one sentence), camera, source, veo yes/no.
```

## Subject reference still (lock this first)
```
[BIBLE]
Single frame, 16:9, photorealistic, no text, no watermark.
[subject] behind smoked glass, thin teal edge light from camera left, amber practical deep in the background,
shallow depth of field, anamorphic oval highlights, wet dark floor reflecting the edge light.
Leave the upper third emptier for type. Hands out of frame or relaxed and anatomically correct.
[CANON + DESCRIPTOR]. [STYLE WORDS]
```

## Character reference sheet (optional — when a person must stay consistent across many Veo plates)
```
[BIBLE]
Cinematic character reference sheet of [subject], against a flat neutral 18% grey background.
Soft Rembrandt light from top left. Three views in one image: full-body wide, medium profile, extreme close-up of the face.
Identical clothing geometry, facial proportions and textures in all three views. Photorealistic. No text, no labels.
```

## Environment / texture plate
```
[BIBLE]
Single frame, 16:9, no text, no people unless stated. [world location], [time/atmosphere].
One hard key light from [direction], fog layered in depth, [material] surfaces, thin phosphor lines.
Composition leaves negative space [left|right|top] for HUD overlay. Same world as the reference image.
[One small story detail: a white robotaxi turning into the nearest bay, one red aviation lamp]. [STYLE WORDS]
```
Example of the formula (ESCAPE VELOCITY):
> a vast low datacenter on a black plain at night, steam plumes rising from its roof, a row of loading bays lit white, one red aviation lamp, a small white robotaxi turning into the nearest bay, a passenger silhouette in its rear window, the top half empty night sky, blue-black #0f1216 and steel blue, one small red lamp as the only warm note, fine silver-gelatin grain, cinematic stillness, no text, no letters, no logos
Pass the subject ref (and an earlier environment) with `--ref` so the world stays coherent.

## Veo motion prompt (image-to-video on a locked still)
Prompt the **motion**, not a new scene.
```
Animate the reference image. [8] seconds.
Camera: [slow lateral track left | slow push in | 10-degree orbit right].
[One moving part: fog drifts left | a thin foreground ring rotates once | rain streaks on the glass | lights pulse once].
Keep the subject's face, wardrobe and the set unchanged. Do not add people, objects, text, signs or logos.
No whip pans, no cuts, no handheld shake. End on a frame that is easy to cut away from.
```

## Overlay brief (when customising overlay.html)
```
One HTML file, 1920x1080, transparent background, 30 fps, everything a pure function of t via window.seek(t).
Draw only: a rotating gimbal, a fluid ribbon whose thickness follows loudness from beats.json,
tick marks on downbeats, and one lyric word that springs in on each vocal onset.
Palette from the bible tokens. No timers, no Date.now, no requestAnimationFrame, no CSS transitions,
no unseeded Math.random (use rand(seed) from the template).
Thin the overlay on chorus rows, full HUD on verses.
```

## Performer shot (non-singing)
```
[BIBLE]
Single frame, 16:9, photorealistic cinematic film still, no text, no letters, no logos, no watermark.
The [subject] from the reference sheet, full body, [dancing with a hair-whip / walking toward camera / seen from behind facing a wall of screens], [location], [light].
CRITICAL: her [signature feature, e.g. hair is vivid violet-purple (#A46BFF)] exactly like the reference images — the most important detail of the image. Her mouth is closed — she is not singing.
```
Pass two refs (`--ref sheet --ref best-scene`) and use `--tier pro`. Motion prompt: `Camera: slow dolly back as she walks toward camera… Her mouth stays closed — she does not sing or talk.`

## Lyric-matched scene plate
```
[BIBLE]
Single frame, 16:9, photorealistic cinematic film still, no text, no letters, no logos, no watermark.
[The literal image of the lyric line: e.g. "office workers seen from behind carrying cardboard boxes out of a glass tower lobby at dusk, rain"].
Full-bleed 16:9 frame edge to edge — no black bars, no letterbox, no border. No readable signs.
```
If the scene contains screens, tickers or money, add "abstract shapes only, no numbers, no readable text".

## YouTube thumbnail (Nano Banana Pro, with subject refs)
```
YouTube thumbnail, 16:9, ultra high contrast, cinematic, photorealistic, designed to read at small size.
RIGHT HALF: the [subject] from the reference images in a tight close-up from the shoulders up, looking straight into the lens with a [fierce, defiant] expression, mouth closed. [Signature feature] is the most saturated thing in the image. Hard rim light, warm key on the face.
BACKGROUND: [one story element, e.g. a dark empty office with one giant red stock chart crashing].
LEFT HALF: large bold condensed sans-serif title text in two lines, perfectly spelled: "[LINE 1]" in white and "[LINE 2]" in [accent]. No other text anywhere. No watermark, no logos, no extra letters.
```
Read the result to check the spelling, then check it shrunk to ~246 px wide (search-result size).

## Negative phrasing that works
Models follow "Do not add text, signs or logos" better than a long list of everything banned. Keep the ban list in the bible, and in each prompt restate only: no text, no new people/objects, no style drift.

## Words that turn into objects (Veo)
Veo renders nouns literally and picks the most common reading. "cursor" became a white mouse-pointer hand moving across the lens; "screen" invites UI text; "signs of life" invites signage. Describe the visual form instead ("a solid rectangular text-cursor block that blinks"), then ban the misreading explicitly ("no mouse pointer, no arrow, no hand icon, no new shapes appear"). Re-check the clip after any noun that could be an icon.
