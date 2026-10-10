# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""Extract lyrics with word timings from the song (MLX Whisper on Apple Silicon, faster-whisper elsewhere).

  uv run lyrics.py "assets/original-music/Song.mp3"                          # transcribe only
  uv run lyrics.py "assets/original-music/Song.mp3" --lyrics-text lyrics.txt # align the user's lyrics to the audio
  uv run lyrics.py ... --separate                                            # isolate vocals with Demucs first (slower, more accurate)
                                                                             # keeps the stem at assets/audio-analysis/vocals.wav
Whisper's word timestamps are approximate (often 0.3–1 s early after a pause, and words it misses get spread
evenly → "interp"). For the overlay, refine with align_lyrics.py (forced alignment on the stem), then
curate_lyrics.py (phrases + vocal-onset guard), and check with lyric_timing_chart.py.

Writes (default dir assets/audio-analysis/):
  lyrics-words.json  [{start, end, text, prob, src}]  src: whisper | aligned | fuzzy | interp
  lyrics-lines.json  [{start, end, text}]
  assets/overlay/lyrics.json  [{t, end, text}] word-level starter for the overlay (only if missing, or with --overwrite-overlay)

If the user's lyrics are supplied, they are the source of truth for the text and Whisper is only used for timing:
words are matched by sequence alignment, and unmatched words are interpolated between their matched neighbours.
Suno section tags like [Verse] or [Chorus] are dropped. Always spot-check timings at a few lines (the contact sheet
shows the active lyric) — music transcription is good, not perfect.
"""
from __future__ import annotations

import argparse
import difflib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MLX_DEFAULT = "mlx-community/whisper-large-v3-turbo"
FW_DEFAULT = "large-v3-turbo"


def norm(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower()).strip("'")


def separate_vocals(mp3: str) -> str:
    """Demucs two-stem separation. Runs in its own uv env so torch stays out of this script's deps."""
    out = Path(tempfile.mkdtemp(prefix="demucs-"))
    print("separating vocals with demucs (first run downloads the model)...", flush=True)
    cmd = ["uvx", "--python", "3.12", "--from", "demucs", "--with", "torchaudio<2.9", "--with", "soundfile",
           "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(out), mp3]
    r = subprocess.run(cmd, capture_output=True, text=True)
    hits = list(out.rglob("vocals.wav"))
    if r.returncode or not hits:
        print(f"demucs failed, using the full mix instead:\n{r.stderr[-1500:]}", file=sys.stderr)
        return mp3
    return str(hits[0])


def transcribe(audio: str, model: str | None, language: str | None, prompt: str | None) -> list[dict]:
    words: list[dict] = []
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        import mlx_whisper

        res = mlx_whisper.transcribe(
            audio, path_or_hf_repo=model or MLX_DEFAULT, word_timestamps=True, language=language,
            initial_prompt=prompt, condition_on_previous_text=False, hallucination_silence_threshold=2.0,
            verbose=None,
        )
        for seg in res.get("segments", []):
            for w in seg.get("words", []):
                words.append({"start": w["start"], "end": w["end"], "text": w["word"].strip(), "prob": w.get("probability", 1.0)})
    else:
        from faster_whisper import WhisperModel

        m = WhisperModel(model or FW_DEFAULT, compute_type="auto")
        segs, _ = m.transcribe(audio, word_timestamps=True, language=language, initial_prompt=prompt,
                               condition_on_previous_text=False, vad_filter=True)
        for seg in segs:
            for w in seg.words or []:
                words.append({"start": w.start, "end": w.end, "text": w.word.strip(), "prob": w.probability})
    # Whisper splits "white-collar" into "white" + "-collar" and "30-year" into "30" + "-year": glue them back.
    merged: list[dict] = []
    for w in words:
        if merged and w["text"] and not w["text"][0].isalnum():
            m = merged[-1]
            m["text"] += w["text"]
            m["end"] = w["end"]
            m["prob"] = min(m["prob"], w["prob"])
        else:
            merged.append(dict(w))
    return [dict(w, src="whisper", start=round(w["start"], 3), end=round(w["end"], 3)) for w in merged if norm(w["text"])]


def parse_lyrics(text: str) -> list[list[str]]:
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", line).strip()  # drop [Chorus] tags and (ad-libs)
        if line:
            lines.append(line.split())
    return lines


def align(lines: list[list[str]], hyp: list[dict]) -> list[dict]:
    ref = [(li, w) for li, line in enumerate(lines) for w in line]
    a, b = [norm(w) for _, w in ref], [norm(h["text"]) for h in hyp]
    out: list[dict | None] = [None] * len(ref)
    # Global (Needleman-Wunsch) alignment. difflib's longest-block-first matching jumps between repeated
    # choruses: a cleanly heard 2nd chorus gets glued to the 1st in the text and everything between collapses.
    n, m = len(a), len(b)
    GAP = -1.0

    def sub(x: str, y: str) -> float:
        if x == y:
            return 2.0
        return 0.5 if difflib.SequenceMatcher(None, x, y).ratio() >= 0.5 else -0.5

    S = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        S[i][0] = i * GAP
    for j in range(1, m + 1):
        S[0][j] = j * GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            S[i][j] = max(S[i - 1][j - 1] + sub(a[i - 1], b[j - 1]), S[i - 1][j] + GAP, S[i][j - 1] + GAP)
    i, j = n, m
    while i > 0 and j > 0:
        if S[i][j] == S[i - 1][j - 1] + sub(a[i - 1], b[j - 1]):
            h = hyp[j - 1]
            out[i - 1] = {"start": h["start"], "end": h["end"], "prob": h["prob"],
                          "src": "aligned" if a[i - 1] == b[j - 1] else "fuzzy"}
            i, j = i - 1, j - 1
        elif S[i][j] == S[i - 1][j] + GAP:
            i -= 1
        else:
            j -= 1
    # interpolate unmatched runs between matched neighbours
    i = 0
    while i < len(out):
        if out[i] is not None:
            i += 1
            continue
        j = i
        while j < len(out) and out[j] is None:
            j += 1
        t0 = out[i - 1]["end"] if i > 0 else (out[j]["start"] - 0.4 * (j - i) if j < len(out) else 0.0)
        t1 = out[j]["start"] if j < len(out) else t0 + 0.4 * (j - i)
        step = max(0.05, (t1 - t0) / (j - i))
        for k in range(i, j):
            s = t0 + (k - i) * step
            out[k] = {"start": round(max(0.0, s), 3), "end": round(s + step * 0.9, 3), "prob": 0.0, "src": "interp"}
        i = j
    return [dict(o, text=w, line=li) for (li, w), o in zip(ref, out)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp3")
    ap.add_argument("--lyrics-text", help="user lyrics (plain text, Suno tags ok) — becomes the source of truth for words")
    ap.add_argument("--separate", action="store_true", help="isolate vocals with Demucs before transcribing")
    ap.add_argument("--model", help=f"whisper model (default {MLX_DEFAULT} on Apple Silicon, {FW_DEFAULT} elsewhere)")
    ap.add_argument("--language", default=None, help="e.g. en; auto-detect if omitted")
    ap.add_argument("--out-dir", default="assets/audio-analysis")
    ap.add_argument("--overlay-out", default="assets/overlay/lyrics.json")
    ap.add_argument("--overwrite-overlay", action="store_true")
    a = ap.parse_args()

    lines = parse_lyrics(Path(a.lyrics_text).read_text()) if a.lyrics_text else None
    prompt = " ".join(" ".join(l) for l in lines)[:600] if lines else None  # vocabulary hint, not forced text
    # The vocal stem is kept at <out-dir>/vocals.wav: align_lyrics.py and curate_lyrics.py need it, and reruns reuse it.
    stem = Path(a.out_dir) / "vocals.wav"
    if a.separate and stem.exists():
        print(f"reusing vocal stem {stem}")
        audio = str(stem)
    elif a.separate:
        audio = separate_vocals(a.mp3)
        if audio != a.mp3:
            stem.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(audio, stem)
            print(f"saved vocal stem {stem}")
            audio = str(stem)
    else:
        audio = a.mp3
    hyp = transcribe(audio, a.model, a.language, prompt)
    print(f"whisper: {len(hyp)} words")

    if lines:
        words = align(lines, hyp)
        n = len(words)
        stats = {s: sum(w["src"] == s for w in words) for s in ("aligned", "fuzzy", "interp")}
        print(f"aligned {n} lyric words: " + ", ".join(f"{k} {v}" for k, v in stats.items()))
        if n and stats["interp"] / n > 0.4:
            print("warning: >40% of words interpolated — try --separate, or check that the lyrics match this song",
                  file=sys.stderr)
        line_out = []
        for li, line in enumerate(lines):
            ws = [w for w in words if w["line"] == li]
            line_out.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(line)})
    else:
        words = hyp
        # lines from pauses: break when the gap to the next word is > 0.6 s or a line gets long
        line_out, cur = [], []
        for k, w in enumerate(words):
            cur.append(w)
            gap = words[k + 1]["start"] - w["end"] if k + 1 < len(words) else 9
            if gap > 0.6 or len(cur) >= 10:
                line_out.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["text"] for x in cur)})
                cur = []

    od = Path(a.out_dir)
    od.mkdir(parents=True, exist_ok=True)
    (od / "lyrics-words.json").write_text(json.dumps(words, indent=1))
    (od / "lyrics-lines.json").write_text(json.dumps(line_out, indent=1))
    print(f"wrote {od / 'lyrics-words.json'} and {od / 'lyrics-lines.json'} ({len(line_out)} lines)")

    ov = Path(a.overlay_out)
    if a.overlay_out and (a.overwrite_overlay or not ov.exists()):
        ov.parent.mkdir(parents=True, exist_ok=True)
        pops = []
        for k, w in enumerate(words):
            nxt = words[k + 1]["start"] if k + 1 < len(words) else w["end"] + 0.6
            pops.append({"t": w["start"], "end": round(min(nxt, w["start"] + 2.5), 3), "text": re.sub(r"[^\w' -]", "", w["text"])})
        ov.write_text(json.dumps(pops, indent=1))
        print(f"wrote {ov} (word-level starter — curate it: keep hook words, merge short words into phrases)")
    for l in line_out[:8]:
        print(f"  {l['start']:7.2f}  {l['text']}")
    if len(line_out) > 8:
        print(f"  ... {len(line_out) - 8} more lines")
    if shutil.which("ffmpeg") is None:
        print("note: ffmpeg not found — whisper needs it to decode mp3", file=sys.stderr)


if __name__ == "__main__":
    main()
