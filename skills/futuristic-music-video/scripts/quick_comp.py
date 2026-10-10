"""Fast composite check at 1080p, without assembling: the plate frame at t (video cuts exact incl. offset/crop/hflip and
the `sat` ramp; stills cover-cropped with Ken Burns and punch-in ignored) + the overlay PNG rendered at scale 1.
~0.2 s per frame vs ~3 min per 50 s for a 4K assemble preview.

  node $SKILL/scripts/render_overlay.mjs --html assets/overlay/overlay.html --out <dir> --frames 12.5,45,82.3
  python3 $SKILL/scripts/quick_comp.py <dir> <out_dir> 12.5 45 82.3 [--storyboard video/storyboard.json]
  uv run $SKILL/scripts/contact_sheet.py <out_dir>/*.jpg --out video/contact-sheets/check.png
"""
import json, subprocess, sys
from pathlib import Path

args = sys.argv[1:]
sbp = "video/storyboard.json"
if "--storyboard" in args:
    i = args.index("--storyboard"); sbp = args[i + 1]; del args[i:i + 2]
ov, out, ts = Path(args[0]), Path(args[1]), [float(x) for x in args[2:]]
out.mkdir(parents=True, exist_ok=True)
sb = json.load(open(sbp)); fps = sb.get("fps", 30)
for t in ts:
    c = next(c for c in sb["cuts"] if c["start"] <= t < c["end"])
    f = ov / f"frame_{int(t * fps + 0.5):06d}.png"     # JS Math.round, not Python's banker's round()
    src, cr = c.get("source"), c.get("crop", 1)
    vf = f"scale=1920*{cr}:1080*{cr}:force_original_aspect_ratio=increase,crop=1920:1080" + (",hflip" if c.get("hflip") else "")
    if c.get("sat"):
        s0, s1, a0, a1 = c["sat"]; k = min(1, max(0, (t - c["start"] - a0) / max(0.01, a1 - a0)))
        vf += f",hue=s={s0 + (s1 - s0) * k:.3f}"
    if not src:
        inp, vf = ["-f", "lavfi", "-i", "color=c=0x07090C:s=1920x1080"], "null"
    elif src.endswith(".mp4"):
        inp = ["-ss", str(c.get("offset", 0) + t - c["start"]), "-i", src]
    else:
        inp = ["-i", src]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-i", str(f), "-filter_complex", f"[0]{vf}[b];[b][1]overlay",
                    "-frames:v", "1", str(out / f"c_{t:07.2f}.jpg")], check=True)
print(f"wrote {len(ts)} composites to {out}")
