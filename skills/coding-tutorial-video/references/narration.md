# Narration: script, voice, pacing, verification

## Writing beats (`script.py`)

- One beat = one sentence-sized idea + one visual change + a hold. If a sentence can't be
  said in one breath, split it into two beats.
- Second person and "we/let's"; concrete verbs; name what's visible ("this line", "the amber
  box", "the critic"). The stressed word is the one the visual lights on that word.
- A segment (Scene) is 60–120 s; its first beat can carry the title's idea.
- Pre-training beats: "First, the model. It reads everything and decides what to do next."
- Code beats follow the order of the lines being lit.
- Retrieval: `ask("q1", "Your turn. <production question>? Pause if you like.", silence)`
  followed by an answer beat that gives feedback. Silence 5–8 s (8 for multi-part reviews).
- Analogy beats: source first ("Think of a chef…"), mapping ("The ticket is the messages.
  The chef is the model…"), principle, break ("Here's where the picture breaks…").
- Close: "You can now …" + a concrete next-step cue + (in a series) a preview of the next
  episode. No "thanks for watching".
- Never write narration that reads on-screen paragraphs aloud, apologizes, stacks metaphors,
  or says "as you can clearly see" while things still move.
- Keep numbers that the viewer must match on screen consistent with the real run (write
  result beats *after* capturing the real output).

## Voice

- One voice for the whole series (and one TTS model: the same voice name sounds different
  across models). Warm, mid-register, calm enthusiasm; never monotone, never hype, never a
  novelty voice. Monotone is worse for comprehension even though it feels "neutral".
- Gemini TTS voices that fit a mentor: `Sulafat` (warm, default), `Achird` (friendly),
  `Charon` / `Rasalgethi` (informative), `Vindemiatrix` (gentle).
- The `persona` prompt in `PROJECT` uses Gemini's structured format (AUDIO PROFILE, THE SCENE,
  DIRECTOR'S NOTES, TRANSCRIPT). A plain "Say: …" prefix with style prose can get read aloud;
  the structured form doesn't. Pacing instructions in the prompt only nudge speed a little,
  which is why pacing is also enforced in post (below).
- Test the voice once with `uv run python tts.py "One sentence of the script."`.

## Pacing (enforced by build_audio.py)

| material | target |
|---|---|
| hook / orientation | ~150–165 wpm |
| new mechanism, first pass | ~125–145 wpm with 0.4–0.6 s pauses after clauses |
| worked-example steps | ~120–135 wpm, a pause between steps |
| recap | up to ~170 wpm |
| retrieval question | slower (tempo 0.92), then silence |

Gemini TTS speaks ~150–185 wpm. The pipeline: trims edges, widens sentence gaps to ≥ 0.42 s
and clause gaps ×1.25, slows any beat above 155 wpm (pitch-preserving, never below 0.9×),
adds a 0.35 s anticipation lead and the beat's hold (default 0.7 s; give definitions and
key inferences 1.2–1.8 s), then the silent window for asks. `build_audio.py` prints per scene
"speech wpm" (the voice) and "with holds wpm" (including stillness); for new material aim
for speech ~130–155 and with-holds ~110–125. Don't chase the with-holds number upward by
cutting holds: the holds are the encoding windows.

## Takes, splitting, truncation

- `build_audio.py` packs consecutive beats into takes of ~70 s of speech and sends one TTS
  request per take, with `[long pause]` between beats. Fewer requests (free tier: 10/day per
  TTS model) and more consistent prosody.
- Gemini TTS stops generating at ~110 s of audio. A truncated take is detected because its
  last words are never heard; the builder then retries it as two smaller takes.
- Splitting uses Whisper word timestamps aligned to the script (difflib over normalized
  words), cutting in the quietest 20 ms of each inter-beat gap. A silence-only splitter was
  tried first and misaligned on long takes.
- Cache: every take/beat is cached by (model, voice, persona, text, nonce). Re-running costs
  nothing unless text changed. Changing the persona re-synthesizes everything.

## Verification (always)

`uv run python check_narration.py` transcribes each beat and compares it with the script.
Read every flagged line:
- Spelling-only differences ("dot env" ↔ ".env", "one" ↔ "1", "sub-agent") are fine.
- **Misreads that change meaning** (it once said "run finished" for "run started" in the one
  beat whose point was the order of events) must be fixed: reword the beat slightly (which
  also forces a fresh take) and rebuild.
- **Clipped words** ("want it" for "Run it."): `build_audio.py --retake <beat_id>` makes a
  fresh single-beat take that overrides the split piece.
- Mispronounced names: add a `pronounce` mapping and rebuild the affected scenes.

## Quotas and cost

- Free tier (at the time of writing): TTS 10 requests/day per model; text models 20/day and
  5/minute per model. Quotas reset at midnight Pacific.
- A 15-minute series needs ~12–15 TTS requests plus a few retakes. With billing enabled this
  costs well under a dollar; suggest the user enable billing on the key's Google Cloud
  project (AI Studio → API keys → Set up billing) rather than contorting the pipeline.
- Never switch TTS models mid-series to dodge a quota: the voice changes.
