# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["torch", "torchaudio<2.9", "soundfile", "numpy"]
# ///
"""Precise word timings: CTC forced alignment of the lyrics text against the isolated vocal stem.

  uv run align_lyrics.py --lyrics-text video/lyrics.txt
      [--stem assets/audio-analysis/vocals.wav] [--words assets/audio-analysis/lyrics-words.json]

Run AFTER `lyrics.py --separate --lyrics-text ...` (which writes the Whisper word timings and keeps the stem).
Why: Whisper's timestamps start words 0.3–1 s early after pauses, and words it misses are spread evenly
("interp"), so lyrics pop up before they're sung. Here the exact text is force-aligned to the vocal stem with
torchaudio's MMS_FA model. Lines are aligned in BLOCKS (lines between instrumental gaps, max ~28 s) in one pass:
per-line alignment on sung vocals lets a line slide onto its neighbour; a joint pass keeps lines in order.
Lines scoring below --min-score keep their Whisper timing (listed in the report) — the onset guard in
curate_lyrics.py then fixes their starts against the vocal energy.

Writes the refined words over --words (keeps the original as lyrics-words.whisper.json, reused on reruns).
Next: uv run curate_lyrics.py ...; check with uv run lyric_timing_chart.py
"""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio

ap = argparse.ArgumentParser()
ap.add_argument("--lyrics-text", required=True, help="same lyrics file passed to lyrics.py")
ap.add_argument("--stem", default="assets/audio-analysis/vocals.wav")
ap.add_argument("--words", default="assets/audio-analysis/lyrics-words.json")
ap.add_argument("--min-score", type=float, default=0.25, help="mean token probability below this keeps Whisper timing")
ap.add_argument("--gap", type=float, default=1.6, help="pause (s) that splits alignment blocks")
a = ap.parse_args()


def parse_lyrics(text: str) -> list[str]:          # same rules as lyrics.py, so line indices match
    out = []
    for line in text.splitlines():
        line = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", line).strip()
        if line:
            out.append(line)
    return out


lines = parse_lyrics(Path(a.lyrics_text).read_text())
words_p = Path(a.words)
src = words_p.with_name("lyrics-words.whisper.json")
if not src.exists():
    shutil.copy(words_p, src)
old = json.loads(src.read_text())
MIN_SCORE, GAP = a.min_score, a.gap
# old line spans
span = {}
for w in old:
    a, b = span.get(w["line"], (1e9, -1e9))
    span[w["line"]] = (min(a, w["start"]), max(b, w["end"]))

wav, sr = sf.read(a.stem, dtype="float32", always_2d=True)
wav = torch.from_numpy(wav.mean(axis=1))
wav = torchaudio.functional.resample(wav, sr, 16000)
SR = 16000
dur = wav.shape[0] / SR

bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model(with_star=False).eval()
tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
LABELS = set(bundle.get_labels())


def norm(word: str) -> str:
    return "".join(ch for ch in word.lower() if ch in LABELS and ch != "-")


# Group lines into vocal blocks (split where Whisper saw a > GAP s pause) and align each block in one pass:
# a joint alignment keeps lines in order, so a line can't slide onto its neighbour.
order = sorted(span)
blocks, cur = [], [order[0]]
for li in order[1:]:
    if span[li][0] - span[cur[-1]][1] > GAP or span[li][1] - span[cur[0]][0] > 28:
        blocks.append(cur); cur = [li]
    else:
        cur.append(li)
blocks.append(cur)

out, report = [], []
for bi, blk in enumerate(blocks):
    a, b = span[blk[0]][0], span[blk[-1]][1]
    prev_end = span[blocks[bi - 1][-1]][1] if bi else 0.0
    next_start = span[blocks[bi + 1][0]][0] if bi + 1 < len(blocks) else dur
    w0 = max(0.0, (prev_end + a) / 2, a - 4.0)
    w1 = min(dur, (b + next_start) / 2, b + 4.0)
    words = [(li, w) for li in blk for w in lines[li].split() if norm(w)]
    seg = wav[int(w0 * SR):int(w1 * SR)].unsqueeze(0)
    with torch.inference_mode():
        emission, _ = model(seg)
    try:
        spans = aligner(emission[0], tokenizer([norm(w) for _, w in words]))
    except Exception as e:  # noqa: BLE001
        spans = None
        print(f"block {bi}: alignment failed ({e})")
    ratio = seg.shape[1] / emission.shape[1] / SR
    for li in blk:
        idx = [k for k, (l2, _) in enumerate(words) if l2 == li]
        score = float(np.mean([s.score for k in idx for s in spans[k]])) if spans else 0.0
        if not spans or score < MIN_SCORE:
            report.append(f"  keep whisper  line {li:2d} score {score:.2f}  {lines[li]}")
            out += [dict(w, line=li) for w in old if w["line"] == li]
            continue
        for k in idx:
            ws = spans[k]
            out.append({"start": round(w0 + ws[0].start * ratio, 3), "end": round(w0 + ws[-1].end * ratio, 3),
                        "prob": round(float(np.mean([s.score for s in ws])), 3), "src": "ctc",
                        "text": words[k][1], "line": li})
        st = out[-len(idx)]["start"]
        report.append(f"  ctc {score:.2f}  blk {bi:2d} line {li:2d} start {span[li][0]:7.2f} -> {st:7.2f} ({st - span[li][0]:+.2f}s)  {lines[li]}")
out.sort(key=lambda w: (w["line"], w["start"]))

words_p.write_text(json.dumps(out, indent=1))
print("\n".join(report))
print(f"wrote {words_p} ({len(out)} words, {sum(w['src'] == 'ctc' for w in out)} force-aligned)")
