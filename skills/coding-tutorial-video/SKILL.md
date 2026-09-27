---
name: coding-tutorial-video
description: Produce a narrated, 4K, fluid-motion tutorial video (or short series) that teaches a coding, CLI, DevOps or configuration task — building an agent with an SDK, setting up Ansible on a remote host, Dockerizing an app, a Terraform module, a Git workflow, anything technical. Builds and runs the real project first and shows only real code and real terminal output, designs the lesson with multimedia-learning science (segmenting, signaling, retrieval practice, analogies, pacing), narrates it with Gemini TTS, and renders it frame-accurately with web technology (GSAP + SVG/HTML, headless Chromium, ffmpeg). Use this whenever the user wants a tutorial video, explainer video, screencast, course lesson, onboarding video or "video that shows how to build/set up/deploy X", or asks to turn a repo, a README or a workflow into a video — even if they don't mention animation, learning science or 4K.
---

# Coding tutorial videos

This skill turns "teach people how to do X" into a finished video series where a viewer
can actually *do* X afterwards. Three things make it work, and all three matter:

1. **The real thing, built first.** You build and run the project the tutorial teaches,
   step by step, and capture real terminal output. Every code panel shows a real file and
   every terminal replays a real run. Viewers trust (and can reproduce) what they see, and
   building it first also surfaces the real pitfalls worth teaching.
2. **Learning science.** The lesson is designed for knowledge transfer, not for looking
   impressive: one idea at a time, visuals that change in the same second the voice names
   them, stillness to encode, retrieval questions, analogies with their break points,
   interleaved review. See `references/learning-science.md` before designing.
3. **A deterministic web renderer.** One paused GSAP timeline; `seek(t)` makes every frame a
   pure function of time; Playwright screenshots frames in parallel at 2× (true 3840×2160)
   and ffmpeg encodes them. Visuals are cued to Whisper word timings of the narration.

The engine and pipeline are bundled: `scripts/scaffold.sh` copies them into the project.
Your work is the creative and pedagogical part.

## Workflow

### 0. Frame the lesson (short conversation)

Establish, from the request and the repo, then state in a line or two rather than
interrogating the user:
- **Audience and prior knowledge.** E.g. "Python developers new to agents", "sysadmins who
  know SSH but not Ansible". This calibrates pre-training and pace (novices need more
  signaling and slower first passes; experts are slowed down by it — expertise reversal).
- **The transfer goal.** One sentence: "After this, the viewer can build and run X and do Y."
- **Scope → series.** Attention drops after ~6 minutes regardless of total length, so plan
  episodes of ~4–7 minutes and split bigger topics into a series.
- **Defaults** (mention, don't ask): 16:9, 3840×2160, 60 fps; calm dark palette with one
  teal accent and amber reserved for "your turn"; one warm Gemini voice; captions as a
  sidecar file. Ask only if something is genuinely the user's call (e.g. brand colours).

### 1. Build and capture the real project

Read `references/capture.md`. In short:
- Write the tutorial's code as a sequence of small, growing steps (`step1_…`, `step2_…`),
  each runnable on its own, the way you'll teach it. Refactor shared setup into a helper
  once the viewer has seen it in full.
- Run every step. Save real output to `video/captures/`. Where a run needs input, pipe it
  and type the inputs back on cue in the video.
- Things that fail or misbehave during this phase are gold: a real pitfall (a loop that
  never stops, a missing permission, a flaky quota) often becomes the most memorable beat.
- Never show secrets: mask keys in on-screen `.env` panels.

### 2. Design the lesson

Read `references/learning-science.md`, then write down (in your head or a scratch file):
- **5–9 core ideas per episode**, each statable in one plain sentence.
- **The cast of characters**: the 3–6 parts of the system (e.g. control node, inventory,
  SSH, managed host, playbook). They become `FlowMap` nodes, are introduced one at a time
  with name + role (pre-training), keep the same shape/position/colour all series, and
  later *travel into the code that implements them*.
- **One structural analogy per core idea** that needs one (source shown complete first,
  pairs mapped in the same layout, the shared principle said aloud, one sentence on where
  it breaks).
- **One retrieval question per segment** (production, not recognition: "where does the
  tool result go next?", not "what was it called?"), plus an interleaved review near the
  end and a spaced-recall question at the start of each later episode.
- **A worked example** in the same visual world: the real code, built step by step, with
  the terminal run right after.

### 3. Write the narration (`video/script.py`)

The only per-project Python file. Beats are sentence-sized: one beat = one sentence-sized
idea + one visual change + a hold. Rules that matter most (details in `references/narration.md`):
- Second person, conversational, short sentences; name what's on screen ("this line", "the
  amber mark"); the stressed word is the thing being highlighted.
- `ask(...)` beats for retrieval (a 5–8 s silent window follows; say "pause if you like").
- Put `pronounce` mappings in `PROJECT` for names TTS will mangle (AG-UI, kubectl, nginx…).
- End every episode with a concrete next-step cue ("tomorrow, from memory, add a second
  task…") and never with "thanks for watching".

### 4. Scaffold and storyboard (before spending TTS quota)

```bash
bash <skill>/scripts/scaffold.sh video        # once per project
cd video && uv run python assemble.py --estimate ep1     # timings estimated from word counts
cd web && npm run dev                         # http://localhost:5199/?ep=ep1 (click to play)
node shot.mjs --ep ep1 3.5 12 20.5 …          # contact sheet of chosen seconds → shots/sheet.jpg
```

Write `web/src/episodes/<ep>.js` (read `references/engine.md` first: API, determinism rules,
layout conventions, recipes). Place every change on the spoken word with
`word('beatId', 'word')`. Review contact sheets with the Read tool against the checklist
below, fix, re-shoot. Estimated timings shift once real audio exists, but layout problems
(overlaps, overflowing lines, two accents at once) are found cheaply here.

### 5. Narrate, verify, assemble

```bash
uv run python build_audio.py            # TTS in ~70 s takes, split by Whisper word alignment, paced
uv run python check_narration.py        # transcribe every beat and compare with the script
uv run python assemble.py ep1 ep2       # real timings + word-level cues for the renderer
```

`check_narration.py` is not optional: TTS occasionally misreads (in testing it said "run
finished" where the script said "run started", inverting the lesson) and a split can clip a
word. Reword a flagged beat in `script.py` and rebuild, or re-synthesize it unchanged with
`build_audio.py --retake <beat_id>`. Spelling-only differences (".env" vs "dot env") are fine.

### 6. Review with real timings, render, finalize

Re-shoot contact sheets (Whisper cues may move things), then:

```bash
cd web && npx vite build && (npx vite preview --port 5199 --strictPort &) && node render.mjs --ep ep1
cd .. && uv run python finalize.py      # chapters per segment, sidecar captions, joined series file
```

Render against the production build, never the dev server (it can reload mid-render).
A 4K60 render runs at ~25 fps on an M-series Mac (6 workers): a 6-minute episode ≈ 15 min.
Run renders in the background. Before reporting done, sample frames from the *output file*
(`ffmpeg -ss … -frames:v 1`) and check duration, audio stream and loudness.

### 7. Deliver

Tell the user: where the files are (`video/out/final/`), their length/size, the chapter
list, what each episode teaches, anything that is not real (e.g. filtered noise lines,
condensed streams) and how to preview (`npm run dev`) and re-render a changed scene.

## Review checklist (every contact sheet)

- **One live accent** in any paused frame; a stranger can point at "the thing to look at".
  Previous highlights return to neutral or to the 45%-opacity "done" state.
- **Amber only** for retrieval, "your turn" and warnings (if–then marks, next-step cue).
- **Labels on the part they name**, hidden during retrieval windows; no sentences on screen
  that duplicate the narration.
- **Nothing overlaps or clips**: code lines fit the panel (shrink `fs` or widen), side-by-side
  code + terminal have a gap, the mini-map doesn't collide with panels.
- **Temporal contiguity**: the change lands on the word; nothing starts while the previous
  idea is still moving; holds are actually still.
- **Morph only related things** (a part becomes its code, a draft becomes its revision).

## Quality gates (report pass/fail when presenting a plan or a finished video)

| Gate | Pass condition |
|---|---|
| Transfer | After watching, the viewer can build/run the thing; the code shown is complete enough to reproduce |
| Real | Every code panel is a real file; every terminal line comes from a real run (any filtering stated) |
| Ideas | 5–9 per episode, each one sentence; episodes ≤ ~7 min, segmented into 60–120 s chunks |
| Pre-training | System parts named and shown before they run |
| Signaling | One accent at a time; words and visuals change together |
| Retrieval | ≥1 production question per segment, labels hidden, silence given, feedback after; interleaved review; spaced recall in later episodes |
| Analogy | One structural source per idea that needs it; pairs mapped; break point named |
| Voice | One warm voice; ~130–155 wpm speech on new material; designed pauses; verified with check_narration |
| Coherence | No music under speech, no decorative motion, no logo stings or "thanks for watching" |
| Afterlife | Ends with a concrete next-step cue and when to revisit |

## Where web-motion habits conflict with learning science

Motion-graphics practice often says "keep something moving at all times", "glass and
glow", "never an empty frame". For teaching, stillness after a reveal is the encoding
window, decoration competes with the content for working memory, and a calm field makes
the one moving thing readable. Keep the flat, calm look; let motion mean something.

## References

- `references/learning-science.md` — the design rules and why (read before step 2)
- `references/engine.md` — renderer architecture, full API, layout conventions, recipes (read before step 4)
- `references/narration.md` — voice, pacing numbers, takes, verification, quotas (read before step 3/5)
- `references/capture.md` — building the real project and capturing honest output (read before step 1)
- `references/pitfalls.md` — failures met in production and their fixes (skim once)

If the `fluid-learning-video` skill is installed, its SKILL.md and `references/evidence.md`
go deeper on the research; this skill is self-contained without it.
