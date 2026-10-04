# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile"]
# ///
"""Curate the overlay's lyric phrases from word timings, locked to the actual vocal attacks.

  uv run curate_lyrics.py --lyrics-text video/lyrics.txt
      [--words assets/audio-analysis/lyrics-words.json] [--stem assets/audio-analysis/vocals.wav]
      [--out assets/overlay/lyrics.json] [--max-words 3] [--weak "point,zero"] [--nudge "0:3.25,17:-0.1"]

Output: [{t, end, text, line}] — `text` is the kinetic phrase (1–3 words, up to 5 to avoid bad breaks),
`line` is the full lyric line (the overlay shows it as a small subtitle).

Phrase rules (each one came from a real problem):
  - break at punctuation and every --max-words words, but never end on a weak word ("PRODUCT WHEN NO")
    and never leave one dangling word at the end of a line ("…ON AN EMPTY" / "FLOOR").
  - vocal-onset guard (needs the Demucs stem): a phrase may not start while the voice is silent — if it does,
    it jumps forward to the next vocal attack (≤3 s); otherwise it snaps to the nearest attack within ±0.3 s.
    This catches what forced alignment misses (low-confidence lines keep Whisper's early timestamps).
  - a phrase ends 0.45 s after the voice stops, so it doesn't linger through instrumental breaks.
  - --nudge index:seconds for the odd manual fix (indices are printed by lyric_timing_chart.py / this script).
Verify with: uv run lyric_timing_chart.py   (every phrase marker should sit on a rise of the vocal curve)
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument("--lyrics-text", required=True)
ap.add_argument("--words", default="assets/audio-analysis/lyrics-words.json")
ap.add_argument("--stem", default="assets/audio-analysis/vocals.wav")
ap.add_argument("--out", default="assets/overlay/lyrics.json")
ap.add_argument("--max-words", type=int, default=3)
ap.add_argument("--hold", type=float, default=0.55, help="seconds a phrase lingers after its last word if there's room")
ap.add_argument("--weak", default="", help='extra words a phrase must not end on, e.g. "point,zero"')
ap.add_argument("--nudge", default="", help='manual shifts, e.g. "0:3.25,17:-0.1" (phrase index: seconds)')
a = ap.parse_args()

WEAK = {"the", "a", "an", "no", "when", "to", "in", "of", "for", "as", "can", "who", "your", "my", "at", "on", "is",
        "and", "with", "while", "up", "one", "but", "or", "from", "by", "it's", "i", "we", "you"}
WEAK |= {w.strip().lower() for w in a.weak.split(",") if w.strip()}
NUDGE = {int(k): float(v) for k, v in (x.split(":") for x in a.nudge.split(",") if x.strip())}

lines = []
for line in Path(a.lyrics_text).read_text().splitlines():      # same rules as lyrics.py → line indices match
    line = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", line).strip()
    if line:
        lines.append(line)
words = json.loads(Path(a.words).read_text())

phrases, cur = [], []


def flush():
    if cur:
        phrases.append({"t": cur[0]["start"], "last": cur[-1]["end"],
                        "text": " ".join(w["text"] for w in cur).rstrip(",.;"),
                        "line": lines[cur[0]["line"]] if cur[0]["line"] < len(lines) else ""})
        cur.clear()


prev_line = None
for j, w in enumerate(words):
    if w["line"] != prev_line:
        flush(); prev_line = w["line"]
    cur.append(w)
    left = sum(1 for x in words[j + 1:] if x["line"] == w["line"])
    weak = w["text"].lower().strip(",.?!") in WEAK and len(cur) < 5
    if left == 1 and len(cur) < 6:
        continue
    if (w["text"][-1:] in ",.?!" and len(cur) > 1) or (len(cur) >= a.max_words and not weak):
        flush()
flush()

# vocal-onset guard
rms = None
if Path(a.stem).exists():
    wav, sr = sf.read(a.stem, dtype="float32", always_2d=True)
    mono = wav.mean(axis=1); hop = int(sr * 0.01)
    rms = np.sqrt(np.convolve(mono ** 2, np.ones(hop * 3) / (hop * 3), mode="same")[::hop])
    rms = rms / np.percentile(rms, 99)
else:
    print(f"warning: no vocal stem at {a.stem} — skipping the onset guard (run lyrics.py --separate)")
SILENT, VOICED = 0.06, 0.15


def fr(t):
    return int(np.clip(round(t * 100), 0, len(rms) - 1))


def onset_near(t):
    if rms is None:
        return t
    if rms[fr(t):fr(t + 0.25)].mean() < SILENT:
        nxt = np.nonzero(rms[fr(t):fr(t + 3.0)] > VOICED)[0]
        return t + nxt[0] / 100 - 0.03 if len(nxt) else t
    lo, hi = fr(t - 0.3), fr(t + 0.3)
    seg = rms[lo:hi]
    rises = [k for k in range(3, len(seg)) if seg[k] > VOICED and seg[k - 3:k].min() < SILENT * 1.5]
    if rises:
        k = min(rises, key=lambda k: abs(lo + k - fr(t)))
        return (lo + k) / 100 - 0.03
    return t


moved = 0
for i, p in enumerate(phrases):
    t2 = onset_near(p["t"])
    if abs(t2 - p["t"]) > 0.08:
        print(f"  onset guard #{i:3d}: {p['t']:7.2f} -> {t2:7.2f}  {p['text']}"); moved += 1
    p["last"] = max(p["last"], t2 + 0.3)
    p["t"] = round(t2 + NUDGE.get(i, 0.0), 3)
print(f"onset guard moved {moved} phrases")
for i, p in enumerate(phrases):
    nxt = phrases[i + 1]["t"] if i + 1 < len(phrases) else p["last"] + 2
    p["end"] = round(min(nxt, p["last"] + a.hold), 3) if nxt - p["last"] < 3 else round(p["last"] + 1.2, 3)
    if rms is not None:
        voiced = np.nonzero(rms[fr(p["t"]):fr(p["end"])] > SILENT)[0]
        if len(voiced):
            p["end"] = round(min(p["end"], p["t"] + voiced[-1] / 100 + 0.45), 3)
    del p["last"]
out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(phrases, indent=1, ensure_ascii=False))
print(f"wrote {out} ({len(phrases)} phrases)")
