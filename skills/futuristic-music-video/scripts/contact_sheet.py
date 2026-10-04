# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tile frames into one review image (the contact-sheet critique loop).

  uv run contact_sheet.py video/contact-sheets/raw/*.png --out video/contact-sheets/sheet-01.png
  uv run contact_sheet.py --video out/song.mp4 --times 5,30,62,95,140,200 --out video/contact-sheets/final.png

Transparent overlay frames are flattened onto --bg (bible --bg colour) so they are readable.
Tiles are in input order, left-to-right, top-to-bottom; the order is printed so you can map tile → time.
"""
from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frames", nargs="*")
    ap.add_argument("--video", help="sample frames from a rendered video instead")
    ap.add_argument("--times", help="comma-separated seconds for --video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--tile-width", type=int, default=640)
    ap.add_argument("--bg", default="#07090C")
    a = ap.parse_args()

    tmp = Path(tempfile.mkdtemp())
    frames = [Path(f) for f in a.frames]
    if a.video:
        times = [float(x) for x in (a.times or "").split(",") if x]
        frames = []
        for i, t in enumerate(times):
            f = tmp / f"v{i:03d}.png"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1", str(f)], check=True)
            frames.append(f)
    if not frames:
        ap.error("no frames")

    tw, th = a.tile_width, a.tile_width * 9 // 16
    cols = min(a.cols, len(frames))
    rows = math.ceil(len(frames) / cols)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in frames:
        cmd += ["-i", str(f)]
    bg = a.bg.replace("#", "0x")
    parts, labels = [], []
    for i in range(len(frames)):
        parts.append(f"color=c={bg}:s={tw}x{th}:d=1[b{i}];[{i}:v]scale={tw}:{th},format=rgba[s{i}];"
                     f"[b{i}][s{i}]overlay=format=auto,pad={tw + 4}:{th + 4}:2:2:color=0x222222[t{i}]")
        labels.append(f"[t{i}]")
    # pad to a full grid with blank tiles
    for j in range(len(frames), rows * cols):
        parts.append(f"color=c=0x000000:s={tw + 4}x{th + 4}:d=1[t{j}]")
        labels.append(f"[t{j}]")
    layout = "|".join(f"{(k % cols) * (tw + 4)}_{(k // cols) * (th + 4)}" for k in range(rows * cols))
    fc = ";".join(parts) + ";" + "".join(labels) + f"xstack=inputs={rows * cols}:layout={layout}[o]"
    if rows * cols == 1:
        fc = ";".join(parts) + ";[t0]null[o]"
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd + ["-filter_complex", fc, "-map", "[o]", "-frames:v", "1", str(out)], check=True)
    for k, f in enumerate(frames):
        print(f"tile {k + 1}: {f.name}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
