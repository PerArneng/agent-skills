# Agent Skills

A general-purpose collection of reusable [Claude Code](https://claude.com/claude-code) skills.

A skill is a single Markdown document that teaches an agent one focused thing - a convention, an
architecture, a workflow - and gets loaded into context when it is relevant. The skills here are
deliberately project-agnostic: drop any of them into any repository and it applies.

## Available skills

| Skill | Description |
|---|---|
| [`python-architecture`](skills/python-architecture/SKILL.md) | Interface-first, dependency-injected Python architecture: Protocols and Pydantic models in an `interfaces` package, implementations in a mirroring `modules` package, one class per file, IO confined to edge modules, fully testable in memory. |
| [`gemeni-notebook-video-enhancer`](skills/gemeni-notebook-video-enhancer/SKILL.md) | Remakes a narrated presentation video (NotebookLM / Gemini video overviews, slide recordings) as a fluid motion-graphics video with the original voice-over: word-timed scenes in GSAP + Three.js, rendered frame-accurately with headless Chromium + ffmpeg to 9:16, 1080p or 4K. Defaults to a calm "focus dark" palette (confirmed with the user first); neon-glass and brand-matched styles as alternatives. |
| [`fluid-learning-video`](skills/fluid-learning-video/SKILL.md) | Science-based rules for narrated fluid-motion learning videos built for maximum knowledge transfer: content architecture, morph-over-cut motion, easing and holds, color as a signaling code, voice pacing and script, retrieval and spacing, analogies, and a pre-ship checklist. Grounded in multimedia-learning research (Mayer, Sweller, Tversky, Gentner). |
| [`coding-tutorial-video`](skills/coding-tutorial-video/SKILL.md) | End-to-end production of narrated 4K tutorial videos for any coding, CLI or DevOps topic: builds and runs the real project first and shows only real code and terminal output, designs the lesson with learning science (pre-training, signaling, retrieval, analogies, pacing), narrates with Gemini TTS verified by Whisper, and renders word-synced motion with GSAP + headless Chromium + ffmpeg. Bundles the engine and a scaffold script. |
| [`futuristic-music-video`](skills/futuristic-music-video/SKILL.md) | Turns a finished song (any mp3, e.g. from Suno) into a beat-synced futuristic music video up to 4K: Gemini (Nano Banana stills, Veo clips) supplies the footage, a deterministic frame-by-frame HTML overlay adds the HUD, lyric-driven motion-graphic scenes, a 3D line layer and highlight lyric cards (typed readouts, split-flap boards, slams), and ffmpeg assembles it on the original audio. Cuts and graphics lock to the beat, bass drops and force-aligned sung words, and track the performer in the footage. Modular and cached; also makes a looping vertical Short and code-drawn A/B thumbnails. Run `npm install` in `scripts/` first. |

## Usage

Clone the repository:

```bash
git clone git@github.com:PerArneng/agent-skills.git
cd agent-skills
```

Then make a skill available, either globally for every project:

```bash
ln -s "$PWD/skills/python-architecture" ~/.claude/skills/python-architecture
```

or scoped to a single project:

```bash
mkdir -p /path/to/project/.claude/skills
cp -r skills/python-architecture /path/to/project/.claude/skills/
```

Symlinking keeps the skill up to date with `git pull`; copying pins it to the version you copied.
Claude picks a skill up automatically when the work matches its `description`, and you can always
invoke one explicitly with `/python-architecture`.

## Adding a skill

One directory per skill under `skills/`, containing a `SKILL.md` that starts with YAML frontmatter:

```markdown
---
name: my-skill
description: What it does, and when an agent should reach for it.
---

# My Skill

...
```

- `name` matches the directory name, in kebab-case.
- `description` is what decides whether the skill triggers, so write it for that job: say what the
  skill covers *and* the situations that should pull it in. It is the only part always in context.
- Keep the body reference-shaped - conventions, rules, examples - so it stays useful whether the
  reader is writing new code or reviewing existing code.
- Add a row to the table above.
