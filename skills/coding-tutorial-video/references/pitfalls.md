# Pitfalls met in production (and fixes)

| symptom | cause | fix |
|---|---|---|
| TTS audio stops mid-script | Gemini TTS caps a response at ~110 s of audio | takes ≤ ~70 s of speech (default); builder detects truncation and splits the take |
| Style instructions spoken aloud / take far too long | plain-prose style prefix | structured persona (AUDIO PROFILE / SCENE / DIRECTOR'S NOTES / TRANSCRIPT) |
| Narration says the opposite of the script | TTS misread | `check_narration.py` on every build; reword the beat |
| A beat starts mid-word | split cut too early | `build_audio.py --retake <id>` |
| Beats misaligned after splitting | silence-only splitting on long takes | Whisper word alignment (default) |
| Voice sounds different in part 3 | TTS model switched to dodge a quota | one model per series; enable billing instead |
| `word()` warnings "not heard" | Whisper merged or respelled a word ("e vals", "uvacorn", "5") | cue on the heard form or a neighbour; digits are matched automatically |
| Page never becomes ready in shot/render | a build-time exception (e.g. `light()` for an unregistered substring, quotes in a key) | read the printed pageerror; register lights in the constructor |
| Two accents in one frame | a chip/line left lit when the next thing lit | turn the previous element back to neutral/done at the next cue |
| Code line clipped | panel too narrow for the longest line | lower `fs`/`lh` or widen; check the longest line length first |
| Elements jump when scrubbing backwards | property written by both GSAP and a driver, or a callback | one owner per property; no callbacks |
| Render has glitches/reloads | rendered against the dev server | `vite build` + `vite preview`, then render |
| Series file chapters garbled | MP4 chapter durations > ~89 s overflow at 1/1000 timebase | 1/10 s chapter timebase (finalize.py) |
| Captions show by default | MP4 subtitle tracks report as enabled/default | ship captions as a sidecar `.srt` (off unless loaded) |
| Click/glitch where episodes join | concatenating AAC streams | re-encode series audio from the source WAVs (finalize.py) |
| Loop in the demo never ends | feedback loop without an exit | give it two exits (good enough + max rounds) — and teach that |
| Streaming request cancelled server-side while capturing | output piped into `head` closed the connection | capture the full stream to a file, then inspect |
| SDK retries never fire on 429/503 | provider maps only some error shapes to its throttling exception | wrap the model client to raise the SDK's throttling exception |
| Render takes long | 4K60 ≈ 25 fps with 6 workers | render in the background; draft at `--fps 30`; partial renders with `--from/--to` |
