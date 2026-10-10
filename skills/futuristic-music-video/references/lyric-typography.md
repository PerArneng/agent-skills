# Lyric typography: highlights, not subtitles

Read this at step 7, before writing the lyric layer. These are lessons from "Agents in the Loop": the YouTube Short v3 was the first video built this way, and the user called it "a very good addition". The worked implementation ships with the skill: `assets/examples/compile-the-future/overlay.html` + `highlights.json`. The API is summarised in `overlay-contract.md` → "Highlight lyrics".

## The principle
**Lyrics are punctuation, not subtitles.**
- Text on every line reads as captions. It competes with the scenes and gets monotonous.
- Choose the lines that carry the story and make each one a designed moment. The other lines get **no text at all**: the picture, the lyric scenes and the HUD carry them.
- The singer is heard; the text is there to *underline*, not to transcribe.

## How often
- **About 1 in 3 phrases** get text. The Short used 17 of 45; a 4-minute long form ≈ 30 of 85.
- **About one card every 6–8 s** on average. Leave real gaps: silence between cards is what makes the next one land.
- **Never more than ~2 consecutive phrases** with text, except the hook line.
- **Density follows the song:** sparse in verses, denser in choruses and around drops. Intros and breaks may have a single readout.
- **A Short can run slightly denser** than a long form: shorter attention span, fewer quiet passages.
- **Recurring hooks:** a hook that repeats ("Agents in the loop" ×3) gets text each time, but in a different position or style variant, so it doesn't feel like a template.

## Which lines get text
Give text to:
- **The hook / title line.**
- **Numbers, statuses, verdicts:** "24/7", "workers fired", "Zero. None.", "Economic collapse".
- **Machine voice:** readouts and system words ("Calculations… complete", "execute the plan", "System").
- **Questions and the emotional turn:** "Who buys the product?", "The transition is finished".
- **Lines about the human/performer:** "No union. No soul.", "leaving humans behind". These get anchored to her.
- **The phrase that lands on the biggest drop.**

Skip:
- connective halves ("in the dark", "across the whole land");
- lines whose image a scene already shows unmistakably. Or let the scene own the words (see "scene-owned" below).

## Style follows meaning
| Style | What it is | Use it for |
|---|---|---|
| `type` | Terminal readout in a mono face. Characters appear **one at a time on the sung syllables**, with a block cursor; the newest character flashes; a scan-glitch exit. | The machine's voice: readouts, system words, questions, cold statements. |
| `flap` | **Split-flap departure board.** Tiles flip through a few characters and fold down onto the right letter; each row settles on a chosen sung word. An optional title row ("LABOR BOARD · DEPARTURES"). | Numbers, statuses, verdicts, lists, anything with an arrivals/departures metaphor. |
| `slam` | Big condensed signage. Words land **one by one on their sung word**, with a spring, a chromatic split and a shake on a drop. | The hook and punchlines; the drop phrase. |
| `anchor` | Text pinned to the **tracked picture**: beside the face reticle (it follows her), along her silhouette, or along a tracked contour. | Lines about the human. It ties text to the performer. |
| scene-owned | The scene draws the words as part of its graphic. For example, "FADE AWAY" appears at the spiral's leading edge and is sucked into the core while the city lights die. | When a scene can *embody* the phrase. This is the strongest option when it fits. |

**Mix the styles.** No more than 2–3 cards of the same style in a row, and rotate positions. The same treatment every time becomes a new kind of monotony.

**Pick 3–4 type modes native to the video's world.** The four above suit a machine/infrastructure world (terminals, departure boards, signage). Another world brings its own:
- **fashion:** subtitle, coverline, masthead, strobe;
- **broadcast / news:** lower thirds, a ticker, a breaking-news slab;
- **retail:** price tags, receipts;
- **transit:** tickets, platform boards.

The test: would this piece of type exist in the world of the video?

**World-native graphic objects** are a fifth kind of card: a physical-looking object set with the words, or with the story's data. Examples:
- ESCAPE VELOCITY set each "Look N" as a model card and a garment tag;
- here, a boarding pass, an ID badge, a termination notice, a stock ticket.

Use one or two of them as recurring props.

**Explain the words.** The bar ESCAPE VELOCITY set: "motion graphics and motion design, not just animated lyrics but things that fit the words being said … almost explaining the words with visuals". A card states the line; a lyric scene (`overlay-contract.md` → Scenes) shows what it means, such as a joke's punchline, a number, or a process. Prefer one strong explaining graphic over more text.

## Timing (non-negotiable)
- **Character timing comes from the forced-aligned words** (`lyrics-words.json`, step 2b), never from phrase starts or Whisper.
  - A word's letters appear across `min(word duration, 0.4 s)`, starting exactly at the word's `start`. **Nothing appears before it is sung.**
- **Text overrides** (punctuation, "24/7" for "twenty-four seven") keep per-word sync when the token count equals the sung word count. Otherwise they spread over the phrase.
- **Flap rows** settle on a chosen sung word (`atWord`), with tiles staggered left to right (~40 ms each, 3–6 flips of ~3 frames).
- **Slam words** land on their word start. A phrase that starts on a drop slams harder.
- **Exit** about 0.25 s after the phrase ends: a fold to blank (flap), a scan-glitch (type), or letters fading one by one (scene-owned).

## Layout
- **No reserved lyric band.** Cards overlay the animation. Under a card the scene dims to ~70%, and a *local* blurred dark backing sits behind the card. The scene stays visible.
- **Give the freed space to the scenes:** scale the stage up a little (×1.06–1.08) and move it into the old band.
- **Vary card positions** (top / mid / low; left / centre / right) so the cards don't recreate a fixed band. In the Short, the first pass put most cards low and it read like the old band again.
- **Place cards opposite the performer** (her tracked box), or anchor them to her. Don't cover her face.
- **Respect the safe areas.** Shorts: top ~140 px, bottom ~480 px, and the right button column. 16:9: 96 px margins.
- **16:9 with a right-half scene stage** (the long form, v4):
  - typed readouts go in a left column (x = 96; rows at y 300 / 540 / 900, about 46 px);
  - flap boards and slams are centred at x ≈ 500 (left) or x ≈ 1420 (right), or on the frame centre, about 880 px wide at most beside a scene;
  - `side: auto` decides once per card, at its start: left of a right-half scene, else opposite the performer's tracked box, else centred. It must never jump mid-card;
  - a two-line slam balances its lines ("AGENTS IN / THE LOOP", not "AGENTS IN THE / LOOP");
  - the HUD readouts in the left column step back (×0.5) under a card, as well as the scene (×0.7).
- **Plate graphics** (text on contours, light reticles) skip only the active card's rectangle, not a whole band.

## Fonts
- **Bundle two OFL faces next to the overlay** and keep their licence files (the skill ships both in `assets/fonts/`; copy them to `assets/overlay/fonts/`):
  - a **condensed signage display** face for slams and flap tiles: Big Shoulders Display, which looks like corporate infrastructure and departure boards;
  - a **terminal mono** for typed readouts: Share Tech Mono.

  Choose per theme; the point is one display voice plus one machine voice. The HUD keeps its own small mono.
- **Loading:** `@font-face` with a relative `url()` (`render_overlay.mjs` serves files from disk), then `await document.fonts.load('900 100px <face>')` etc. in `load()` before the first frame. Otherwise early frames render in a fallback face.
- **For thumbnails:** embed the fonts as data URLs.

## Split-flap recipe
- **Tile:** a rounded rect with a vertical gradient (#1d2228 → #0b0d10), a dark hinge line at mid-height, and the character centred.
- **A flip from character A to B, at phase φ ∈ [0, 1]:**
  1. Draw the static halves: **B's top** (revealed behind) and **A's bottom** (not yet covered).
  2. The falling flap: while `cos(πφ) > 0` it is A's top, scaled by `scale(1, cos πφ)` about the hinge. After that it is B's bottom, scaled by `|cos πφ|`. Darken it as it turns.
- **Per tile:** 3–6 flips through hashed random characters, ~3 frames (0.09 s) each, then settle. Add a tiny white "clack" flash on settle.
- **Exit:** one fold to blank per tile, staggered. Not a burst of random characters: that read as a glitchy mess.
- **The housing:** a dark board with a thin outline and a small amber title row in the mono face.

## Anchored text
- Use the **tracked** features (`sampleAt`: face box, silhouette poly, contour ids; see "Tracking on video plates" in `overlay-contract.md`) so text follows the dancer.
- **Face:** the text block sits beside the reticle with a leader line, clamped inside the safe area.
- **Paths:** reveal characters along the path one pass (not repeating), and **reverse paths that run right to left**. Upside-down text is unreadable.
- **No feature on the cut** (no person, no long tracked edge): fall back to `type`. Never drop the card.

## Pitfalls we hit
- **Text along an arbitrary scene contour** looked like garbage (fragments, upside-down). Anchor to the performer or to a scene path you control.
- **Letters riding a steep spiral path** stacked into an unreadable column. Keep the word horizontal and move the whole word along the path, shrinking it.
- **The face label collided with the top HUD rows.** Flip it under the face when the face is high in the frame.
- **A slam duplicated text the scene already showed** ("24/7" in the loop scene plus a "24/7" flap). Acceptable once; avoid making it a pattern.

- **A phrase's end can overlap the next phrase's first word** in the aligned words ("Agents in the loop" ended after "twenty-four" started). Slice the card's words to the phrase's word count, or the token ↔ word match fails and the timing falls back to an even spread.
- **Anchor names that are prefixes of earlier phrases** ("System" also matched "system vein" at 0:52) resolve to the wrong phrase and produce a card that ends before it starts. Use `#n`, and check that every card resolved with t1 > t0.
- **Contour text** only reads when the path runs mostly left to right (≥85% of its length) and is long enough (>500 px). Otherwise fall back to `type`; reversing the endpoints alone left mirrored letters on a looping contour.

## Checks
- **A frame at every card** (t + ~0.6 s), composited over the plates. Read the sheet: spelling, safe areas, overlap with her face.
- **Consecutive frames** (0.1 s apart) through one `type` card and one `flap` card: characters on syllables, folds visible mid-flip.
- **The timing rule:** spot-check that the first character of a word appears at or after its `start`.
- **Silence:** a 1 s-step sheet over a verse shows text only inside card windows.
