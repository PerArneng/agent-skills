# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile", "matplotlib"]
# ///
"""Lyric timing review: vocal loudness (isolated stem) with every lyric phrase start marked.

  uv run lyric_timing_chart.py [--words] [--stem ...] [--lyrics ...] [--out-dir video/contact-sheets]
  → <out-dir>/lyric-timing-NN.png, one per 24 s; Read them and check every marker.

A phrase marker should sit right where the vocal curve rises. Markers in a flat (silent) stretch = early.
--words also marks individual word starts (thin ticks). Labels are prefixed with the phrase index (#n) for
curate_lyrics.py --nudge.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument("--stem", default="assets/audio-analysis/vocals.wav")
ap.add_argument("--lyrics", default="assets/overlay/lyrics.json")
ap.add_argument("--word-file", default="assets/audio-analysis/lyrics-words.json")
ap.add_argument("--out-dir", default="video/contact-sheets")
ap.add_argument("--words", action="store_true", help="also tick individual word starts")
args = ap.parse_args()
wav, sr = sf.read(args.stem, dtype="float32", always_2d=True)
mono = wav.mean(axis=1)
hop = int(sr * 0.01)
rms = np.sqrt(np.convolve(mono ** 2, np.ones(hop * 3) / (hop * 3), mode="same")[::hop])
rms = rms / np.percentile(rms, 99)
tt = np.arange(len(rms)) * 0.01
phr = json.loads(Path(args.lyrics).read_text())
words = json.loads(Path(args.word_file).read_text()) if Path(args.word_file).exists() else []
SPAN = 24.0
out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
n = int(np.ceil(tt[-1] / SPAN))
for i in range(n):
    a, b = i * SPAN, (i + 1) * SPAN
    if not any(a <= p["t"] < b for p in phr):
        continue
    fig, ax = plt.subplots(figsize=(22, 3.2), dpi=90)
    m = (tt >= a) & (tt < b)
    ax.fill_between(tt[m], 0, rms[m], color="#3fb8a0", lw=0)
    if args.words:
        for w in words:
            if a <= w["start"] < b:
                ax.axvline(w["start"], color="#888", lw=0.6, ymax=0.5)
    for idx, p in enumerate(phr):
        if a <= p["t"] < b:
            ax.axvline(p["t"], color="#ff3b3b", lw=1.6)
            ax.axvspan(p["t"], p["end"], color="#ffb25a", alpha=0.12)
            ax.text(p["t"] + 0.05, 1.02, f"#{idx} {p['text']}", rotation=25, fontsize=9, va="bottom")
    ax.set_xlim(a, b); ax.set_ylim(0, 1.6); ax.set_xticks(np.arange(a, b + 0.01, 1)); ax.tick_params(labelsize=7)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / f"lyric-timing-{i:02d}.png")
    plt.close(fig)
print(f"wrote lyric timing charts to {out}")
