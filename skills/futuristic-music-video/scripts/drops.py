# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["librosa>=0.10", "numpy", "soundfile", "matplotlib"]
# ///
"""Music events: bass drops, breaks, beat (groove) changes, builds and rapid hit runs.

  uv run drops.py "assets/original-music/Song.mp3" [--beats assets/audio-analysis/beats.json] \
      [--out assets/audio-analysis/drops.json] [--chart video/contact-sheets/drops.png]

beats.json only knows *where the bars are*; this says *what happens* at a bar line, which is what the edit and the
overlay should hit. Everything is measured per bar (downbeat to downbeat) and compared with the 2 bars before it:
  drop         sub/bass (<150 Hz) energy jumps up    -> hard cut ON the downbeat, burst of short cuts, FX hit
  break        the low end falls away                -> hold a shot, thin the overlay, let the vocal breathe
  beat_change  percussive hit density changes a lot  -> new cut rhythm (half-time / double-time / drums in or out)
               ("dir": "up" | "down")
  build        4 bars of rising high-band energy into a drop -> rising cut rate / zoom / riser graphics
Runs of consecutive bars that all qualify are merged into one event at the first bar (that is where the change
is heard); "strength" is 0..1 within each kind. Output also keeps the per-bar curves ("bars") for charts.

  hit_run      a run of >= --hit-min hard percussive hits in quick, EVEN succession (stabs, "bum bum bum", a snare
               fill): {t, end, hits[], spacing, per_beat, selected}. Hard = loud for the song AND for the 4 s around
               it. Only evenly spaced runs on the beat grid (1, 2 or 4 per beat) count - busy grooves and vocal
               consonants don't. Runs are ranked (hits x hit strength) and only the best --hit-runs, at least
               --hit-gap bars apart, get "selected": true. -> rapid cuts on every hit + strobe/flicker FX, but
               only on the selected ones: used everywhere it stops being special.
Read the chart: each red line should sit where you hear the bass hit; tune --drop-db / --break-db if not.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import librosa
import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp3")
    ap.add_argument("--beats", default="assets/audio-analysis/beats.json")
    ap.add_argument("--out", default="assets/audio-analysis/drops.json")
    ap.add_argument("--chart", default="video/contact-sheets/drops.png", help="'' to skip")
    ap.add_argument("--drop-db", type=float, default=3.0, help="bass rise vs previous 2 bars that counts as a drop")
    ap.add_argument("--break-db", type=float, default=-4.0, help="bass fall that counts as a break")
    ap.add_argument("--groove-ratio", type=float, default=1.6, help="percussive hit-rate ratio that counts as a beat change")
    ap.add_argument("--hit-min", type=int, default=4, help="minimum hard hits in a row for a hit run")
    ap.add_argument("--hit-runs", type=int, default=0, help="how many hit runs to select (0 = ~1 per minute, min 2)")
    ap.add_argument("--hit-gap", type=float, default=8, help="selected hit runs are at least this many bars apart")
    a = ap.parse_args()

    y, sr = librosa.load(a.mp3, sr=22050, mono=True)
    hop = 512
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=hop)) ** 2
    f = librosa.fft_frequencies(sr=sr, n_fft=4096)
    t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)
    db = lambda x: 10 * np.log10(x + 1e-10)  # noqa: E731
    bass, high = db(S[f < 150].sum(0)), db(S[f > 4000].sum(0))
    _, y_perc = librosa.effects.hpss(y)
    perc_on = librosa.onset.onset_detect(y=y_perc, sr=sr, hop_length=hop, units="time")

    B = json.loads(Path(a.beats).read_text())
    DB = list(B["downbeats"])
    bar_len = 60 / B["bpm"] * B.get("beats_per_bar", 4)
    DB.append(DB[-1] + bar_len)
    bars = []
    for i in range(len(DB) - 1):
        s, e = DB[i], DB[i + 1]
        m = (t >= s) & (t < e)
        if not m.any():
            continue
        n_hits = int(((perc_on >= s) & (perc_on < e)).sum())
        bars.append({"t": round(s, 3), "bass": float(bass[m].mean()), "high": float(high[m].mean()),
                     "hits": n_hits / (e - s)})

    raw = []
    for i in range(1, len(bars)):
        prev = bars[max(0, i - 2):i]
        jump = bars[i]["bass"] - np.mean([b["bass"] for b in prev])
        if jump >= a.drop_db:
            raw.append((i, "drop", jump, None))
        elif jump <= a.break_db:
            raw.append((i, "break", jump, None))
        ph = np.mean([b["hits"] for b in prev])
        r = (bars[i]["hits"] + 0.5) / (ph + 0.5)
        if (r >= a.groove_ratio or r <= 1 / a.groove_ratio) and abs(bars[i]["hits"] - ph) >= 1.0:
            raw.append((i, "beat_change", float(np.log2(r)), "up" if r > 1 else "down"))

    # merge runs of consecutive qualifying bars of the same kind (and direction) into the first bar
    events = []
    for kind in ("drop", "break", "beat_change"):
        ks = [x for x in raw if x[1] == kind]
        run = []
        for x in ks + [None]:
            if run and (x is None or x[0] != run[-1][0] + 1 or x[3] != run[-1][3]):
                first = run[0]
                ev = {"t": bars[first[0]]["t"], "kind": kind,
                      "db" if kind != "beat_change" else "log2_ratio": round(max((r[2] for r in run), key=abs), 2)}
                if first[3]:
                    ev["dir"] = first[3]
                events.append(ev)
                run = []
            if x is not None:
                run.append(x)
    # builds: 4 bars of rising high-band energy ending on a drop
    idx = {b["t"]: i for i, b in enumerate(bars)}
    for e in [e for e in events if e["kind"] == "drop"]:
        i = idx[e["t"]]
        if i >= 4 and all(np.diff([bars[k]["high"] for k in range(i - 4, i)]) > 0):
            events.append({"t": bars[i - 4]["t"], "kind": "build", "db": round(bars[i - 1]["high"] - bars[i - 4]["high"], 2),
                           "into": e["t"]})
    events += hit_runs(y_perc, sr, 60 / B["bpm"], bar_len, a, len(y) / sr)
    for kind in ("drop", "break", "beat_change", "build"):
        ks = [e for e in events if e["kind"] == kind]
        key = "log2_ratio" if kind == "beat_change" else "db"
        mx = max((abs(e[key]) for e in ks), default=1) or 1
        for e in ks:
            e["strength"] = round(abs(e[key]) / mx, 2)
    events.sort(key=lambda e: (e["t"], e["kind"]))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": str(a.mp3), "params": {"drop_db": a.drop_db, "break_db": a.break_db,
                               "groove_ratio": a.groove_ratio}, "events": events,
                               "bars": [{k: round(v, 2) for k, v in b.items()} for b in bars]}, indent=1))
    print(f"wrote {out}: " + ", ".join(f"{k} {sum(e['kind'] == k for e in events)}" for k in ("drop", "break", "beat_change", "build"))
          + f", hit_run {sum(e['kind'] == 'hit_run' for e in events)} ({sum(bool(e.get('selected')) for e in events)} selected)")
    for e in events:
        extra = e.get("dir", "") or (f"-> {e['into']:.2f}" if "into" in e else "")
        if e["kind"] == "hit_run":
            extra = f"-> {e['end']:.2f}  {len(e['hits'])} hits, {e['per_beat']}/beat{'  SELECTED' if e['selected'] else ''}"
        print(f"  {e['t']:8.2f}  {e['kind']:11s} s={e['strength']:.2f}  {extra}")

    if a.chart:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(24, 7), sharex=True)
        T = [b["t"] for b in bars]
        ax[0].plot(T, [b["bass"] for b in bars], color="#7a5cff", label="bass <150 Hz (bar mean dB)")
        ax[0].plot(T, [b["high"] - 10 for b in bars], color="#2ad1c9", alpha=.6, label="high >4 kHz (-10 dB)")
        ax[1].step(T, [b["hits"] for b in bars], where="post", color="#ffb25a", label="percussive hits / s")
        col = {"drop": "red", "break": "orange", "beat_change": "magenta", "build": "green", "hit_run": "blue"}
        for e in events:
            if e["kind"] == "hit_run":
                for x in ax:
                    x.axvspan(e["t"], e["end"] + 0.1, color="blue", alpha=0.35 if e["selected"] else 0.08)
                continue
            for x in ax:
                x.axvline(e["t"], color=col[e["kind"]], alpha=.6 * max(.3, e["strength"]))
            ax[0].text(e["t"], ax[0].get_ylim()[1], e["kind"], rotation=90, va="top", fontsize=7)
        for x in ax:
            x.grid(alpha=.2); x.legend(loc="lower right")
        ax[1].set_xticks(range(0, int(T[-1]) + 6, 5))
        Path(a.chart).parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout(); fig.savefig(a.chart, dpi=75)
        print(f"chart {a.chart}")


def hit_runs(y_perc, sr, beat, bar_len, a, duration):
    """Runs of hard, evenly spaced percussive hits; the best few are 'selected'."""
    hop = 256
    env = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=hop)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, units="frames")
    if len(on) < a.hit_min:
        return []
    t, s = librosa.frames_to_time(on, sr=sr, hop_length=hop), env[on]
    glob = np.quantile(s, 0.70)
    loc = np.array([np.median(s[(t > x - 4) & (t < x + 4)]) for x in t])
    hard = (s >= glob) & (s >= 1.3 * loc)
    ht, hs = t[hard], s[hard] / s.max()
    groups, cur = [], [0]
    for i in range(1, len(ht)):
        if ht[i] - ht[i - 1] <= beat * 1.05:
            cur.append(i)
        else:
            groups.append(cur); cur = [i]
    groups.append(cur)
    runs = []
    for g in groups:
        if len(g) < a.hit_min:
            continue
        times, gaps = ht[g], np.diff(ht[g])
        med = float(np.median(gaps))
        regular = float(np.std(gaps)) < max(0.04, 0.2 * med)
        on_grid = min(abs(med - beat * k) / (beat * k) for k in (1, 0.5, 0.25)) < 0.15
        if not (regular and on_grid):
            continue
        runs.append({"t": round(float(times[0]), 3), "end": round(float(times[-1]), 3), "kind": "hit_run",
                     "hits": [round(float(x), 3) for x in times], "spacing": round(med, 3),
                     "per_beat": round(beat / med, 1), "score": float(len(g) * hs[g].mean())})
    mx = max((r["score"] for r in runs), default=1)
    want = a.hit_runs or max(2, round(duration / 60))
    chosen = []
    for r in sorted(runs, key=lambda r: -r["score"]):
        r["strength"] = round(r.pop("score") / mx, 2)
        if len(chosen) < want and all(abs(r["t"] - c["t"]) >= a.hit_gap * bar_len for c in chosen):
            chosen.append(r)
    for r in runs:
        r["selected"] = r in chosen
    return runs


if __name__ == "__main__":
    main()
