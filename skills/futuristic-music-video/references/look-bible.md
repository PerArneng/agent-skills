# Look bible — default for the futuristic genre

The bible is the single source of visual truth for one video. Copy the template below to `video/bible.md`, fill the three brackets, merge the user's theme notes, and paste the finished block at the top of every Gemini prompt (stills, Veo, director). The overlay reads its colour tokens from the same file, so the photographic plates and the code layer agree.

## Why restraint
The futuristic read comes from **restraint plus moving parts**, not from more neon. A designed instrument panel that occasionally opens into a real shot looks expensive; purple gradient sludge with lens flares on every cut looks generated. Keep this in mind when merging user theme notes — they can change the palette and the world, but the ban list protects the genre.

## Template

```
STYLE BIBLE — [song title]
Aspect 16:9, 1920x1080 master, 30 fps.

Palette (tokens):
  --bg      #07090C   near-black, lifted a hair in the grade
  --cool    #7CFFE1   cold teal — primary line/HUD colour, teal in the mids
  --warn    #FFB25A   amber — warnings, peaks, chorus accents only
  --type    #EDEFF2   off-white type
  --dim     #3A4650   secondary lines, grids, inactive ticks

Materials: smoked glass, brushed metal, wet asphalt, thin phosphor lines, fog.
Light: one hard key light, motivated; teal edge light; amber practical deep in the background. No flat studio light.
Lens: shallow depth, anamorphic oval highlights, slight halation allowed on practicals only.
Motion language: lateral drift, slow orbit, iris wipe, scan. Camera never handheld-shaky. No whip pans.
Type (overlay only): condensed grotesk / mono for HUD labels, wide tracking, uppercase lyric words.

Subject for this song: [one person or one object]
Canon (pasted into every prompt that shows the subject):
  [hair cut + colour], [the one signature accent], [each wardrobe piece], [footwear],
  [explicit descriptor: age, skin tone, freckles, build]
Style words (appended verbatim to every image prompt):
  [palette with hex], one [colour] [lamp|light] as the only warm light, [grain], [finish, e.g. cinematic 35mm film still],
  no text, no letters, no logos
World: [one place]
Lyric hook to visualize: [one image]

Theme notes from the user: [merged here — see rules below]

BAN LIST (every image and video prompt):
  - readable text, captions, logos, brand names, random letters, signs, UI baked into images
  - stock cyberpunk alley with neon kanji
  - purple-blue gradient sludge, lens flares on every shot, bloom on everything
  - extra fingers / malformed hands in hero stills
  - centered title cards
  - new characters or locations not in the bible
```

## Merging user theme notes
The user adds styling per video ("chrome and rust, desert world", "pastel vaporwave but still fast", "red/black brutalist"). Merge rules:
- **User wins** on palette, materials, world, subject, type choice, lighting mood. Replace the token values; keep the token *names* (`--bg --cool --warn --type --dim`) so the overlay template keeps working. If they give more colours, add tokens (`--accent2`).
- **Genre stays**: high-paced cutting (1.5–4 s, downbeat-snapped), code-driven machine layer, few hero plates, text-free generated images. If the user explicitly wants to drop one of these, do it but say what it costs (e.g. "more Veo plates → ~$X").
- **Ban list stays** except where the user directly asks for a banned thing (e.g. they *want* neon kanji). Then remove only that line.
- Keep one accent colour reserved for peaks (amber by default). Peaks need somewhere to go.

## Grade (applied once at assembly)
Lift blacks slightly (never crush to 0), push teal into the mids, let amber appear only on peaks/highlights. Expressed as ffmpeg in `scripts/assemble.py` (`--grade default|none|<custom filter>`). If the user's palette differs strongly from teal/amber, pass a custom grade or `none`.

**The look lives in post, not in the plates.** A stylised finish (halftone, dither, xerox, risograph, bleach bypass, heavy grain) is applied after generation:
- as an ffmpeg grade;
- or as an overlay **print pass** (`overlay-contract.md`).

The stills and Veo inputs stay clean, in colour and photographic. ESCAPE VELOCITY's v1 fed monochrome start frames to the video model; the clips came back grey ("way too gray … loses the magic"). v2 kept colour inputs and moved the look into a print pass.
