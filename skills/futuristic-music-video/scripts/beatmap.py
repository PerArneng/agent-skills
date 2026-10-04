# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["librosa>=0.10", "numpy", "soundfile"]
# ///
"""Beat map: the timeline every cut, flash and lyric pop is snapped to.

  uv run beatmap.py "assets/original-music/Song.mp3" --out assets/audio-analysis/beats.json

Output (seconds unless noted):
  duration, bpm, fps
  beats[]       every beat
  downbeats[]   estimated bar starts (every 4th beat, phase chosen by onset strength) — cut here
  onsets[]      percussive/vocal transients — flash / pop lyric words here
  strong_onsets[] top ~15% onsets by strength — big hits
  loudness[]    RMS per video frame, normalised 0..1 (len = ceil(duration*fps)) — drives the fluid ribbon
  sections[]    rough {start,end,label,energy} from novelty segmentation; label is a guess (low/mid/high energy)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import librosa
import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp3")
    ap.add_argument("--out", default="assets/audio-analysis/beats.json")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--sections", type=int, default=0, help="number of sections (0 = auto from duration)")
    a = ap.parse_args()

    y, sr = librosa.load(a.mp3, sr=22050, mono=True)
    duration = float(len(y) / sr)
    hop = 512

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop)
    tempo = float(np.atleast_1d(tempo)[0])
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)

    # Downbeats: choose the bar phase whose beats carry the most onset energy (low-end weighted).
    bpb = a.beats_per_bar
    y_low = librosa.effects.preemphasis(y, coef=-0.95)  # crude low-pass emphasis for kick weighting
    low_env = librosa.onset.onset_strength(y=y_low, sr=sr, hop_length=hop)
    strength = low_env[np.clip(beat_frames, 0, len(low_env) - 1)] if len(beat_frames) else np.array([])
    best_phase = 0
    if len(beats) >= bpb:
        scores = [strength[p::bpb].mean() for p in range(bpb)]
        best_phase = int(np.argmax(scores))
    downbeats = beats[best_phase::bpb]

    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop, backtrack=False)
    onsets = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)
    on_str = onset_env[onset_frames] if len(onset_frames) else np.array([])
    strong = onsets[on_str >= np.quantile(on_str, 0.85)] if len(on_str) else np.array([])

    # Loudness per video frame.
    n_frames = math.ceil(duration * a.fps)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    ft = np.arange(n_frames) / a.fps
    loud = np.interp(ft, rms_t, rms)
    loud_db = librosa.amplitude_to_db(loud + 1e-9, ref=np.max(loud) + 1e-9)
    loud_n = np.clip((loud_db + 40.0) / 40.0, 0, 1)  # -40 dB..0 dB → 0..1
    k = max(1, a.fps // 6)  # light smoothing (~166 ms) so the ribbon breathes instead of jitters
    loud_n = np.convolve(loud_n, np.ones(k) / k, mode="same")

    # Sections via agglomerative segmentation on chroma+mfcc, boundaries snapped to downbeats.
    n_sec = a.sections or int(np.clip(round(duration / 25), 4, 12))
    feat = np.vstack([
        librosa.util.normalize(librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop), axis=1),
        librosa.util.normalize(librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13), axis=1),
    ])
    bounds = librosa.segment.agglomerative(feat, n_sec)
    bt = list(librosa.frames_to_time(bounds, sr=sr, hop_length=hop)) + [duration]
    if len(downbeats):
        bt = [0.0] + [float(downbeats[np.argmin(np.abs(downbeats - b))]) for b in bt[1:-1]] + [duration]
    bt = sorted(set(round(b, 3) for b in bt))
    sections = []
    for s, e in zip(bt[:-1], bt[1:]):
        if e - s < 1.0:
            continue
        seg = loud_n[int(s * a.fps):max(int(s * a.fps) + 1, int(e * a.fps))]
        sections.append({"start": s, "end": e, "energy": round(float(seg.mean()), 3)})
    if sections:
        en = np.array([x["energy"] for x in sections])
        lo, hi = np.quantile(en, 0.33), np.quantile(en, 0.66)
        for x in sections:
            x["label"] = "high" if x["energy"] >= hi else "low" if x["energy"] <= lo else "mid"

    r3 = lambda arr: [round(float(v), 3) for v in arr]  # noqa: E731
    out = {
        "source": str(a.mp3),
        "duration": round(duration, 3),
        "bpm": round(tempo, 2),
        "fps": a.fps,
        "beats_per_bar": bpb,
        "beats": r3(beats),
        "downbeats": r3(downbeats),
        "onsets": r3(onsets),
        "strong_onsets": r3(strong),
        "loudness": [round(float(v), 3) for v in loud_n],
        "sections": sections,
    }
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out))
    bar = 60.0 / tempo * bpb if tempo else 0
    print(f"wrote {p}")
    print(f"duration {duration:.1f}s  bpm {tempo:.1f}  bar {bar:.2f}s  beats {len(beats)}  downbeats {len(downbeats)}  "
          f"onsets {len(onsets)} (strong {len(strong)})")
    for x in sections:
        print(f"  {x['start']:7.2f} - {x['end']:7.2f}  {x['label']:4}  energy {x['energy']}")


if __name__ == "__main__":
    main()
