"""Chapters + optional captions for rendered episodes, and one joined series file.

  out/<slug>_<ep>_4k.mp4 (from web/render.mjs)
  → out/final/<slug>_<ep>_4k.mp4       + chapters (one per segment)
  → out/final/captions_<ep>_en.srt     optional accessibility track, a SIDECAR so it stays
                                       off by default (MP4 has no reliable "available but
                                       off" flag; players may auto-show embedded subs)
  → out/final/<slug>_series_4k.mp4     all rendered episodes, chapters per segment

Chapter times use a 1/10 s timebase: with 1/1000, MP4 chapter durations over ~89 s
overflow a 32-bit field and players show garbage. The series audio is re-encoded from
the source WAVs because concatenating AAC streams glitches at the joins.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from script import EPISODE_TITLES, EPISODES, PROJECT  # noqa: E402

ROOT = Path(__file__).parent
DATA = ROOT / "web" / "src" / "data"
FINAL = ROOT / "out" / "final"


def ts(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def cues(data, off=0.0):
    return [(b["v0"] + off, b["v1"] + off, b["say"]) for b in data["beats"]]


def chapters(ep, data, off=0.0, prefix=""):
    first = EPISODES[ep][0].title
    return [(off, prefix + first)] + [(s["t"] + off, prefix + s["title"]) for s in data["seams"]]


def write_meta(path, marks, total):
    lines = [";FFMETADATA1"]
    for i, (t, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else total
        lines += ["[CHAPTER]", "TIMEBASE=1/10", f"START={round(t * 10)}", f"END={round(end * 10)}", f"title={title}"]
    path.write_text("\n".join(lines) + "\n")


def write_srt(path, cs):
    path.write_text("\n".join(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(cs)))


def remux(src, dst, meta, title, audio=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(meta)]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v", "-map", "2:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v", "-map", "0:a", "-c", "copy"]
    cmd += ["-map_metadata", "1", "-map_chapters", "1", "-metadata", f"title={title}", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / "web" / "config.json").read_text())
    done = []
    for ep in EPISODES:
        epc = cfg["episodes"].get(ep)
        if not epc or not Path(epc["output"]).exists():
            continue
        data = json.loads((DATA / f"{ep}.json").read_text())
        if data.get("estimated"):
            print(f"{ep}: skipped, rendered from ESTIMATED timings (storyboard)")
            continue
        src = Path(epc["output"])
        title = EPISODE_TITLES.get(ep, ep)
        meta = FINAL / f"{ep}.ffmeta"
        write_meta(meta, chapters(ep, data), data["duration"])
        write_srt(FINAL / f"captions_{ep}_en.srt", cues(data))
        remux(src, FINAL / src.name, meta, f"{PROJECT['title']} — {title}")
        done.append((ep, title, data, src, Path(epc["audio"])))
        print("finalized", FINAL / src.name)
    if len(done) < 2:
        return
    lst, wavs = FINAL / "concat.txt", FINAL / "wavs.txt"
    lst.write_text("".join(f"file '{d[3]}'\n" for d in done))
    wavs.write_text("".join(f"file '{d[4]}'\n" for d in done))
    joined, audio = FINAL / "joined.mp4", FINAL / "series.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(wavs), "-c", "copy", str(audio)], check=True)
    marks, cs, off = [], [], 0.0
    for ep, title, data, _, _ in done:
        marks += chapters(ep, data, off, prefix=f"{title.split('·')[0].strip()} · ")
        cs += cues(data, off)
        off += data["duration"]
    meta = FINAL / "series.ffmeta"
    write_meta(meta, marks, off)
    write_srt(FINAL / "captions_series_en.srt", cs)
    name = done[0][3].name.replace(f"_{done[0][0]}_", "_series_")
    remux(joined, FINAL / name, meta, f"{PROJECT['title']} — series", audio=audio)
    for tmp in (joined, audio, lst, wavs):
        tmp.unlink()
    print("finalized", FINAL / name)


if __name__ == "__main__":
    main()
