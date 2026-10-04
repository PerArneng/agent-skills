# Case study: how ESCAPE VELOCITY was made

What we took from the making-of of *ESCAPE VELOCITY* (a 5:06 lyric music video; source: `how-escape-velocity-was-made.pdf`). It was made in about 19 hours of wall-clock time, with one human director giving about 50 short notes and Claude Code as the whole production team. The rules it produced are folded into the other references; this page lists them in one place, with where each one lives and which parts don't transfer to our tools.

## Their stack and ours
| Role | ESCAPE VELOCITY | This skill |
|---|---|---|
| Stills | Midjourney v8.2 (`--raw --hd`, the director's personal profile), 188 prompts → 636 images → 130 plates used | Nano Banana (Pro for references) with `--ref` |
| Moving shots | Seedance 2.5, 47 clips + 30 continuation clips, fed the song audio so she lip-syncs (≈ $93) | Veo 3.1, image-to-video, no audio input |
| Analysis | a home GPU box: stems, beat map, wav2vec2 word alignment, depth maps, Grounding DINO tracking, LatentSync | Apple Silicon: Demucs, librosa, MLX Whisper + CTC forced alignment, macOS Vision, optical flow |
| Motion design | a custom JS engine: canvas plus a WebGL print pass, every frame a pure function of time | the `seek(t)` overlay + world3d.js, ffmpeg assembly |
| Song | Suno v6, with custom lyrics written by agents | the user's finished mp3 |

The architecture is the same as ours: generated footage is the plate; everything carrying meaning (lyrics on the beat, explaining graphics, a through-line device) is drawn in code, so it's exact and on the beat.

## Lessons that transfer, and where they now live
1. **Written character canon plus an explicit physical descriptor in every prompt.**
   - Their tests: identity passes drifted from the look, and face sheets over-conditioned (a close-up-sized head on a distant figure). What worked was the canon written into every prompt, plus "a young Caucasian American woman with pale skin and light freckles". Without the descriptor, the model drifted her ethnicity from shot to shot.
   - For us: keep `--ref`, and also paste the canon and the descriptor (`prompts.md`, the bible's `Canon` block).
2. **Casting call first.**
   - Their first image batch was three hair directions, each as a turnaround, a catwalk shot and a face sheet. They picked the look whose silhouette reads at thumbnail size, and kept its signature colour as a small accent (`prompts.md`).
3. **Plate prompt formula** (`prompts.md`, the bible's `Style words`):
   - a concrete scene with one small story detail;
   - a **declared empty area for type**;
   - the video's fixed family of style words, appended verbatim: palette with hex values, "one red lamp as the only warm light", grain, finish, and "no text, no letters, no logos".
4. **Keep generation inputs in colour; apply the look in post.**
   - Their monochrome start frames came back grey from the video model, so v1 looked "way too gray" and lost the image magic. v2 recoloured the clips and moved the look into a print/halftone pass (`look-bible.md` → Grade, `overlay-contract.md` → Print pass).
5. **The storyboard row carries everything:** lyric, type mode, plate prompt, camera, and clip vs 2.5D (`shot-grammar.md`). The director reviewed a storyboard PDF and approved it in one line.
6. **Two clips never start from the same frame.** This was a director note at storyboard review (`shot-grammar.md`).
7. **A through-line device.** A split-flap board counts down "18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS" all video, until it flips to "THERE IS NO UNDERCLASS" and the catwalk lifts off (`shot-grammar.md`).
8. **Board in chapters.** 141 shots across 9 chapters: story beats, not just song sections (`shot-grammar.md`).
9. **Type modes native to the world.** A fashion show got subtitle / coverline / masthead / strobe, plus look cards set as model cards and garment tags (`lyric-typography.md`).
10. **Graphics that explain the words.** The director's bar: "motion graphics and motion design, not just animated lyrics but things that fit the words being said … almost explaining the words with visuals" (`lyric-typography.md`, SKILL.md step 7).
11. **2.5D parallax from depth maps** for the shots that don't get a video clip. It's cheaper than a clip and far livelier than a zoom. Repetitive 2.5D panels were later turned into pure motion design (`overlay-contract.md` → 2.5D depth parallax, a documented next step).
12. **An art-director loop on real frames.** One animator agent per chapter wrote its code; an art-director agent rendered it, reviewed the frames, and the animator applied the fixes (SKILL.md step 8).
13. **Tempo drifts.** Their song accelerated from 131.5 to 133.9 BPM, and everything was placed on the measured grid. Ours already snaps to the tracked `downbeats` array; never place cuts with `60 / bpm` arithmetic (`shot-grammar.md`).
14. **One human with taste, short notes at checkpoints.** The director spent attention on a handful of decisive notes, each at a checkpoint with something concrete to look at (SKILL.md → checkpoints).

## What doesn't transfer (and why)
- **Lip-sync.** Seedance took the plate as `@Image1` and the exact vocal window as `@Audio1`, with the sung words quoted in the prompt. Veo takes no audio, so our rule stays: the performer never lip-syncs. If a future tool accepts an audio reference, reuse their method:
  1. The model copies the reference audio into its own soundtrack, and the mouth follows *that* soundtrack.
  2. So compare the clip's returned soundtrack with the real vocal (spectral cross-similarity over time).
  3. Cut on the last eighth note before the match drops under a threshold.
  4. Continue with a clip generated from that frame.

  They verified about 86% of sung seconds this way, with LatentSync as the fallback.
- **The Midjourney personal profile** (their taste as a model parameter). Our nearest equivalent is the bible plus two reference images.
- **Exemplar-based video colourisation** (Deep Exemplar, using each shot's own still as the colour reference): a rescue for grey clips. Avoid needing it: feed Veo colour inputs.
- **Agent-written lyrics.** Four lyric writers from different angles, judges, a merger and a critic, with research facts checked by a verifier agent. Our input is a finished song, but the same fan-out works for storyboards (below).

## Multi-agent fan-out, and what it cost
- **The pattern:**
  - 3 director agents boarded the song independently (fashion film, meme density, narrative), 3 judges scored the boards, and a head director merged the best;
  - research went through a 31-agent workflow;
  - animation used an animator, an art director and a fixer per chapter.
- **The cost of the Claude work, at API prices:** about $626 and 1.4 billion tokens.
  - Animation agents: $301 (48%), across 40 agent runs and 3,145 tool calls.
  - Main session: $185 (30%).
  - Storyboard agents: $95 (15%).
  - Research and lyrics: $44 (7%).
- **96% of the tokens were cache re-reads:** every call re-reads the whole context. The main session sat around 565k tokens over 1,028 calls.
  - Images were a small share: 138 viewed images cost about $22 to re-read.
  - The lesson: keep the main context lean, and hand long render → review → fix loops to agents.
- **For us:** offer fan-out only when the user opts in to multi-agent work, and quote these numbers (SKILL.md → Optional: parallel exploration).
