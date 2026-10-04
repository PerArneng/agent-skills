# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Modular, cached assembly: storyboard.json → segments → chunks → final mp4 on the original mp3.

  uv run assemble.py video/storyboard.json --out out/song.mp4            # builds only what changed
  uv run assemble.py video/storyboard.json --list                        # chunk table: which chunk covers which time
  uv run assemble.py video/storyboard.json --start 28 --end 50 --out out/preview.mp4   # only chunks overlapping 28–50 s

Why modular: a 4-minute video is ~7,000 frames. Fixing one plate or one lyric must not re-encode the whole thing.
The build is three cached levels under video/build/ (override with --build-dir):

  segments/<hash>.mp4  one per cut: bg colour | Ken Burns still | trimmed/looped video | PiP window.
                       Hash = render-relevant cut fields + exact frame length + source file size/mtime.
  chunks/<hash>.mp4    consecutive cuts grouped by storyboard `section` (max --chunk-max seconds), with the
                       6-frame dissolves inside, graded ONCE (before the overlay, so overlay tokens stay exact),
                       then the overlay PNG frames for that range composited on top, final-quality encode.
                       Hash = its segment hashes + timings + grade + overlay frame fingerprint (names, sizes, mtimes).
  4K: set width/height 3840x2160 in storyboard.json; plates are lanczos-upscaled, overlay frames come from
  render_overlay.mjs --scale 2. --jobs N builds segments/chunks in parallel. storyboard "tail": seconds of
  picture after the song ends (end card); the audio is padded with silence.
  final                concat of chunk files (stream copy, no re-encode) + the ORIGINAL mp3 → AAC 320k. Seconds.

So: replace a plate → only the segments that use it and their chunks rebuild. Re-render overlay frames for
12–18 s → only the chunk(s) covering 12–18 s rebuild. Chunk boundaries sit on section changes and are hard cuts
(the overlay's iris wipe covers them); cuts inside a chunk get dissolves.
video/build/manifest.json records each chunk's range, hash and whether it was rebuilt or cached.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GRADES = {
    "default": "curves=all='0/0.035 0.5/0.5 1/0.98',"
               "colorbalance=rs=-0.02:bs=0.03:rm=-0.05:gm=0.015:bm=0.04:rh=0.04:gh=0.01:bh=-0.03,"
               "eq=saturation=0.92",
    "none": "null",
}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
RENDER_KEYS = ("source", "motion", "crop", "hflip", "offset", "pip", "pip_side", "sharpen")


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{r.stderr[-3000:]}")


def probe_duration(p: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def h(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def file_sig(p: str | None) -> list | None:
    if not p or not Path(p).exists():
        return None
    st = Path(p).stat()
    return [p, st.st_size, int(st.st_mtime)]


# ---------------------------------------------------------------- segments
def render_segment(cut: dict, nframes: int, cfg: dict, out: Path) -> None:
    W, H, fps, bg = cfg["width"], cfg["height"], cfg["fps"], cfg["bg"]
    dur = nframes / fps
    enc = ["-frames:v", str(nframes), "-c:v", "libx264", "-crf", "12", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-color_range", "tv", "-r", str(fps), "-an"]
    src = cut.get("source")
    if src and not Path(src).exists():
        print(f"warning: missing source {src}; using bg", file=sys.stderr)
        src = None
    if not src:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={bg}:s={W}x{H}:r={fps}", *enc, str(out)])
        return
    zoom = float(cut.get("crop", 1.0))
    flip = ",hflip" if cut.get("hflip") else ""
    if Path(src).suffix.lower() in IMG_EXT:
        motion = cut.get("motion", "kenburns-in")
        z0, z1 = {"kenburns-in": (1.0, 1.12), "kenburns-out": (1.12, 1.0)}.get(motion, (1.06, 1.06))
        z0, z1 = z0 * zoom, z1 * zoom
        dx = {"drift-left": 1, "drift-right": -1}.get(motion, 0)
        # Upscale first so zoompan's integer crop doesn't jitter (2x at HD, 1.25x at 4K to keep it fast).
        ss = 2 if max(W, H) <= 1920 else 1.25
        SW, SH = int(W * ss) // 2 * 2, int(H * ss) // 2 * 2
        vf = (f"scale={SW}:{SH}:force_original_aspect_ratio=increase:flags=lanczos,crop={SW}:{SH}{flip},"
              f"zoompan=z='{z0}+({z1}-{z0})*on/{nframes}':x='iw/2-(iw/zoom/2)+{dx}*on/{nframes}*iw*0.04'"
              f":y='ih/2-(ih/zoom/2)':d={nframes}:s={W}x{H}:fps={fps}")
        inp = ["-loop", "1", "-framerate", str(fps), "-i", src]
    else:
        vf = (f"scale={int(W * zoom) // 2 * 2}:{int(H * zoom) // 2 * 2}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}{flip},"
              f"fps={fps}")
        if cut.get("sharpen"):   # light unsharp after upscaling a small plate (e.g. 720x1280 Veo Lite -> 1080x1920)
            vf += f",unsharp=5:5:{float(cut['sharpen']):.2f}:5:5:0"
        inp = ["-stream_loop", "-1", "-ss", str(cut.get("offset", 0.0)), "-i", src]
    # One colour range for every segment: stills come out of zoompan as full-range yuvj420p, Veo clips are
    # limited-range yuv420p. Mixed in one chunk, xfade converts them all to full range, so the video shots in
    # mixed chunks got darker/contrastier than in video-only chunks (visible as brightness jumps between chunks).
    vf += ",scale=out_range=tv,format=yuv420p"
    if cut.get("pip"):
        pw, ph = W * 2 // 5, H * 2 // 5
        right = cut.get("pip_side", "right" if int(cut["start"]) % 2 else "left") == "right"
        x, y = (W - pw - 96 if right else 96), (H - ph) // 2
        bw = max(2, W // 960)
        fc = (f"[0:v]{vf},scale={pw}:{ph}:flags=lanczos,pad={pw + 2 * bw}:{ph + 2 * bw}:{bw}:{bw}:color={cfg['line']}[p];"
              f"color=c={bg}:s={W}x{H}:r={fps}[b];[b][p]overlay={x}:{y}:shortest=1,format=yuv420p[o]")
        run(["ffmpeg", "-y", *inp, "-filter_complex", fc, "-map", "[o]", "-t", f"{dur + 1:.3f}", *enc, str(out)])
    else:
        run(["ffmpeg", "-y", *inp, "-vf", vf, "-t", f"{dur + 1:.3f}", *enc, str(out)])


# ---------------------------------------------------------------- overlay fingerprint
def overlay_sig(overlay_dir: str | None, f0: int, f1: int) -> list:
    if not overlay_dir or not Path(overlay_dir).is_dir():
        return ["no-overlay"]
    sig, missing = hashlib.sha1(), 0
    for f in range(f0, f1):
        p = Path(overlay_dir) / f"frame_{f:06d}.png"
        try:
            st = p.stat()
            sig.update(f"{f}:{st.st_size}:{st.st_mtime_ns};".encode())
        except FileNotFoundError:
            missing += 1
    return [sig.hexdigest(), missing]


# ---------------------------------------------------------------- chunk
def build_chunk(ch: dict, cfg: dict, seg_dir: Path, out: Path, overlay_dir: str | None) -> None:
    fps, dframes = cfg["fps"], cfg["dissolve_frames"]
    tmp = Path(tempfile.mkdtemp(prefix="fmv-chunk-"))
    try:
        cuts = ch["cuts"]
        inputs = []
        for c in cuts:
            inputs += ["-i", str(seg_dir / f"{c['_seg']}.mp4")]
        fc, prev = [], "[0:v]"
        for k in range(1, len(cuts)):
            off = (cuts[k]["_f0"] - ch["f0"]) / fps
            dur = (1 if cuts[k].get("transition") == "cut" else dframes) / fps
            fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={dur:.4f}:offset={off:.4f}[x{k}]")
            prev = f"[x{k}]"
        nframes = ch["f1"] - ch["f0"]
        fc.append(f"{prev}trim=end_frame={nframes},setpts=PTS-STARTPTS,{cfg['grade']},format=yuv420p[g]")
        last = "[g]"
        cmd = ["ffmpeg", "-y", *inputs]
        if overlay_dir and Path(overlay_dir).is_dir():
            cmd += ["-framerate", str(fps), "-start_number", str(ch["f0"]),
                    "-i", str(Path(overlay_dir) / "frame_%06d.png")]
            key = "chromakey=0x00FF00:0.30:0.10," if cfg["key"] == "green" else ""
            fc.append(f"[{len(cuts)}:v]{key}format=rgba[ov];[g][ov]overlay=eof_action=pass:format=auto,format=yuv420p[v]")
            last = "[v]"
        script = tmp / "fc.txt"
        script.write_text(";\n".join(fc))
        run(cmd + ["-/filter_complex", str(script), "-map", last, "-frames:v", str(nframes), "-r", str(fps),
                   *cfg["venc"], "-pix_fmt", "yuv420p",
                   "-video_track_timescale", str(fps * 512), "-an", str(out)])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--out")
    ap.add_argument("--song", help="override storyboard.song")
    ap.add_argument("--overlay", help="override storyboard.overlay_frames dir ('' to disable)")
    ap.add_argument("--key", choices=["alpha", "green"], default="alpha")
    ap.add_argument("--grade", help="default | none | raw ffmpeg filter (overrides storyboard.grade)")
    ap.add_argument("--start", type=float, default=0.0, help="preview: only chunks overlapping start..end")
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--bg", default="#07090C")
    ap.add_argument("--line", default="#7CFFE1", help="PiP frame colour")
    ap.add_argument("--audio-copy", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--chunk-max", type=float, default=24.0, help="max chunk length in seconds")
    ap.add_argument("--build-dir", default="video/build")
    ap.add_argument("--codec", choices=["h264", "hevc"], default="h264", help="final chunk codec (hevc = smaller 4K)")
    ap.add_argument("--preset", default="slow", help="x264/x265 preset for chunks")
    ap.add_argument("--jobs", type=int, default=3, help="parallel segment/chunk builds")
    ap.add_argument("--rebuild", action="store_true", help="ignore caches")
    ap.add_argument("--list", action="store_true", help="print the chunk table and exit")
    a = ap.parse_args()

    sb = json.loads(Path(a.storyboard).read_text())
    song = a.song or sb["song"]
    fps = int(sb.get("fps", 30))
    grade = a.grade or sb.get("grade", "default")
    cfg = {"width": int(sb.get("width", 1920)), "height": int(sb.get("height", 1080)), "fps": fps,
           "bg": a.bg.replace("#", "0x"), "line": a.line.replace("#", "0x"), "key": a.key, "crf": a.crf,
           "dissolve_frames": int(sb.get("dissolve_frames", 6)), "grade": GRADES.get(grade, grade)}
    cfg["venc"] = (["-c:v", "libx264", "-crf", str(a.crf), "-preset", a.preset] if a.codec == "h264" else
                   ["-c:v", "libx265", "-crf", str(a.crf + 2), "-preset", a.preset, "-tag:v", "hvc1",
                    "-x265-params", "log-level=error"])
    overlay_dir = sb.get("overlay_frames") if a.overlay is None else a.overlay
    tail = float(sb.get("tail", 0.0))
    total_f = round((probe_duration(song) + tail) * fps)

    # 1. Normalise cuts onto the frame grid; fill gaps with bg; later cuts win on overlap.
    timeline, cur = [], 0
    step = int(8 * fps)

    def fill(f0: int, f1: int, section: str | None) -> None:
        # bg gaps are split into <= 8 s pieces so long gaps don't become one giant chunk
        for s in range(f0, f1, step):
            timeline.append({"start": s / fps, "source": None, "section": section, "transition": "cut",
                             "_f0": s, "_f1": min(s + step, f1)})
    for c in sorted(sb["cuts"], key=lambda c: c["start"]):
        f0, f1 = max(round(c["start"] * fps), cur), min(round(c["end"] * fps), total_f)
        if f1 <= f0:
            continue
        if f0 > cur:
            fill(cur, f0, c.get("section"))
        item = dict(c, _f0=f0, _f1=f1)
        if f0 > round(c["start"] * fps) and c.get("source") and Path(c["source"]).suffix.lower() not in IMG_EXT:
            item["offset"] = c.get("offset", 0.0) + (f0 - round(c["start"] * fps)) / fps
        timeline.append(item)
        cur = f1
    if cur < total_f:
        fill(cur, total_f, "outro")

    # 2. Group into chunks at section changes (and at most chunk-max seconds).
    chunks: list[dict] = []
    for c in timeline:
        ch = chunks[-1] if chunks else None
        if ch is None or c.get("section") != ch["section"] or (c["_f1"] - ch["f0"]) / fps > a.chunk_max:
            chunks.append({"section": c.get("section"), "f0": c["_f0"], "cuts": []})
            ch = chunks[-1]
        ch["cuts"].append(c)
        ch["f1"] = c["_f1"]

    if a.list:
        for i, ch in enumerate(chunks):
            print(f"chunk {i:02d}  {ch['f0'] / fps:7.2f}-{ch['f1'] / fps:7.2f}s  {ch['section'] or '-':10} "
                  f"{len(ch['cuts'])} cuts")
        return
    if not a.out:
        ap.error("--out required")

    t0, t1 = a.start, a.end if a.end is not None else total_f / fps
    sel = [ch for ch in chunks if ch["f1"] / fps > t0 and ch["f0"] / fps < t1]

    build = Path(a.build_dir)
    seg_dir, chunk_dir = build / "segments", build / "chunks"
    seg_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    # 3. Segments (cached). Each segment carries extra dissolve tail except the last in its chunk.
    n_seg_built, todo = 0, {}
    for ch in sel:
        for k, c in enumerate(ch["cuts"]):
            tail = cfg["dissolve_frames"] if k < len(ch["cuts"]) - 1 else 0
            nframes = c["_f1"] - c["_f0"] + tail
            render = {key: c.get(key) for key in RENDER_KEYS}
            if c.get("pip") and "pip_side" not in c:
                render["pip_side"] = "right" if int(c["start"]) % 2 else "left"
            c["_seg"] = h("seg-v2", render, nframes, file_sig(c.get("source")),
                          {k2: cfg[k2] for k2 in ("width", "height", "fps", "bg", "line")})
            p = seg_dir / f"{c['_seg']}.mp4"
            if (a.rebuild or not p.exists()) and c["_seg"] not in todo:
                todo[c["_seg"]] = (c, nframes, p)
    with ThreadPoolExecutor(max(1, a.jobs)) as ex:
        list(ex.map(lambda job: render_segment(job[0], job[1], cfg, job[2]), todo.values()))
    n_seg_built = len(todo)

    # 4. Chunks (cached).
    manifest, n_chunk_built, jobs = [], 0, []
    for i, ch in enumerate(sel):
        osig = overlay_sig(overlay_dir, ch["f0"], ch["f1"])
        if osig[-1]:
            print(f"warning: chunk {ch['f0'] / fps:.2f}-{ch['f1'] / fps:.2f}s is missing {osig[-1]} overlay frames",
                  file=sys.stderr)
        ch["hash"] = h("chunk-v1", [(c["_seg"], c["_f0"], c.get("transition")) for c in ch["cuts"]],
                       ch["f0"], ch["f1"], cfg["grade"], cfg["key"], cfg["crf"], cfg["dissolve_frames"], osig)
        p = chunk_dir / f"{ch['hash']}.mp4"
        status = "cached"
        if a.rebuild or not p.exists():
            jobs.append((ch, p))
            status, n_chunk_built = "rebuilt", n_chunk_built + 1
        manifest.append({"start": ch["f0"] / fps, "end": ch["f1"] / fps, "section": ch["section"],
                         "cuts": len(ch["cuts"]), "hash": ch["hash"], "file": str(p), "status": status})
        print(f"  chunk {ch['f0'] / fps:7.2f}-{ch['f1'] / fps:7.2f}s {ch['section'] or '-':10} {status}", flush=True)
    with ThreadPoolExecutor(max(1, a.jobs)) as ex:
        list(ex.map(lambda job: build_chunk(job[0], cfg, seg_dir, job[1], overlay_dir), jobs))
    (build / "manifest.json").write_text(json.dumps(manifest, indent=1))

    # 5. Final: stream-copy concat + original audio.
    lst = build / "concat.txt"
    lst.write_text("".join(f"file '{Path(m['file']).resolve()}'\n" for m in manifest))
    a0 = sel[0]["f0"] / fps
    dur = (sel[-1]["f1"] - sel[0]["f0"]) / fps
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-ss", f"{a0:.4f}", "-i", song,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", *(["-af", "apad"] if tail else []),
         *(["-c:a", "copy"] if a.audio_copy and not tail else ["-c:a", "aac", "-b:a", "320k"]),
         "-t", f"{dur:.4f}", "-movflags", "+faststart", str(out)])
    print(f"segments built {n_seg_built}, chunks rebuilt {n_chunk_built}/{len(sel)}")
    print(f"wrote {out}  ({probe_duration(str(out)):.2f}s from {a0:.2f}s)")


if __name__ == "__main__":
    main()
