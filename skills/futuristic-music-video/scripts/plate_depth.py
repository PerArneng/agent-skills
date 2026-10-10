# /// script
# requires-python = ">=3.10"
# dependencies = ["torch", "transformers", "pillow", "opencv-python", "numpy"]
# ///
"""Depth grids for the overlay's 3D wire meshes (the `mesh` layer in assets/overlay/overlay.html).

  uv run $SKILL/scripts/plate_depth.py assets/still-images/*.jpg assets/video-clips/*-fast.mp4   (cached; ~3 s per clip on M1)

Depth Anything V2 Small (MPS on Apple Silicon) -> relative depth, near = 1. Each plate gets
assets/plate-features/depth/<file stem>.json = {w, h, kind, duration, samples: [{t, d: base64 uint8 w*h}]}.
Videos are sampled every 0.2 s (same grid as plate_features.py, so the overlay interpolates both alike) and
normalised with clip-global percentiles so the mesh does not breathe between samples. Cached by file size+mtime.
"""
import base64
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

GW, GH, EVERY, VERSION = 64, 36, 0.2, 1
OUT = Path("assets/plate-features/depth")
dev = "mps" if torch.backends.mps.is_available() else "cpu"
proc = AutoImageProcessor.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")
model = AutoModelForDepthEstimation.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf").to(dev).eval()


def depth(img_rgb: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        x = proc(images=Image.fromarray(img_rgb), return_tensors="pt").to(dev)
        d = model(**x).predicted_depth[0].float().cpu().numpy()       # relative inverse depth: big = near
    return cv2.resize(d, (GW, GH), interpolation=cv2.INTER_AREA)


def frames(p: Path):
    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        yield 0.0, cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB), 0.0
        return
    cap = cv2.VideoCapture(str(p))
    fps, n = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = n / fps
    t = 0.0
    while t < dur - 1e-3:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, round(t * fps)))
        ok, fr = cap.read()
        if ok:
            yield round(t, 3), cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), dur
        t += EVERY


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sys.argv[1:]:
        p = Path(f)
        out = OUT / f"{p.stem}.json"
        sig = [p.stat().st_size, int(p.stat().st_mtime), VERSION]
        if out.exists() and json.loads(out.read_text()).get("sig") == sig:
            print(f"{p.name:28s} cached"); continue
        raw, ts, dur = [], [], 0.0
        for t, img, dur in frames(p):
            raw.append(depth(img)); ts.append(t)
        allv = np.stack(raw)
        lo, hi = np.percentile(allv, 2), np.percentile(allv, 98)
        samples = []
        for t, d in zip(ts, raw):
            q = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)
            samples.append({"t": t, "d": base64.b64encode((q * 255).astype(np.uint8).tobytes()).decode()})
        kind = "image" if dur == 0 else "video"
        out.write_text(json.dumps({"w": GW, "h": GH, "kind": kind, "duration": round(dur, 3), "sig": sig, "samples": samples}))
        print(f"{p.name:28s} {kind} {len(samples)} samples")


if __name__ == "__main__":
    main()
