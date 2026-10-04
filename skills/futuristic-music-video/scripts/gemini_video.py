# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.40", "pillow"]
# ///
"""Generate a Veo 3.1 plate from a locked still (image-to-video) or from reference images (ingredients).

  uv run gemini_video.py --plate chorus-a --image assets/still-images/subject-ref.png \
      --prompt-file video/prompts/chorus-a.txt --out assets/video-clips/chorus-a.mp4
  uv run gemini_video.py ... --dry-run     # cost + request only

Defaults: Lite, 720p, 8 s, 16:9. Upgrade a keeper with --tier fast --res 1080p only after its motion is approved.
Veo's own audio is stripped from the saved file: the Suno master is the only soundtrack.
Caps (cost_ledger.py): 8 Veo calls per session, 2 retries per plate; --force overrides (ask the user first).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cost_ledger as cl  # noqa: E402

MODELS = {
    "lite": "veo-3.1-lite-generate-preview",
    "fast": "veo-3.1-fast-generate-preview",
    "standard": "veo-3.1-generate-preview",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plate", required=True, help="plate name, used for retry counting (e.g. chorus-a)")
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--image", help="locked still to animate (first frame)")
    ap.add_argument("--ref", action="append", default=[], help="ingredient reference image (max 3), used when no --image")
    ap.add_argument("--tier", choices=MODELS, default="lite")
    ap.add_argument("--model", help="override model id")
    ap.add_argument("--res", choices=["720p", "1080p", "4k"], default="720p")
    ap.add_argument("--duration", type=int, choices=[4, 6, 8], default=8)
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--negative", default="text, captions, logos, signs, watermark, extra people, whip pan, handheld shake")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--force", action="store_true", help="bypass call/retry caps (only with user approval)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    prompt = a.prompt or (Path(a.prompt_file).read_text() if a.prompt_file else None)
    if not prompt:
        ap.error("--prompt or --prompt-file required")
    if not a.image and not a.ref:
        print("warning: text-only Veo call. The skill expects plates built on a locked still (--image).", file=sys.stderr)
    price = cl.VEO_PER_SECOND[a.tier].get(a.res)
    if price is None:
        sys.exit(f"{a.tier} does not offer {a.res}")
    usd = price * a.duration
    model = a.model or MODELS[a.tier]
    ledger = a.ledger or cl.default_ledger()

    print(f"model={model} {a.res} {a.duration}s image={a.image} refs={a.ref} est=${usd:.2f} "
          f"(session so far ${cl.total(ledger):.2f})")
    if a.dry_run:
        print("--- prompt ---\n" + prompt)
        return
    cl.check_veo_caps(ledger, a.plate, a.force)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=cl.load_api_key())

    def img(path: str) -> types.Image:
        p = Path(path)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return types.Image(image_bytes=p.read_bytes(), mime_type=mime)

    cfg = dict(
        aspect_ratio=a.aspect,
        resolution=a.res,
        duration_seconds=a.duration,
        number_of_videos=1,
    )
    # Veo Lite rejects negativePrompt; fold the negatives into the prompt text there instead.
    if "lite" in model:
        prompt = f"{prompt}\nAvoid: {a.negative}." if a.negative else prompt
    elif a.negative:
        cfg["negative_prompt"] = a.negative
    if a.ref and not a.image:
        cfg["reference_images"] = [
            types.VideoGenerationReferenceImage(image=img(r), reference_type="asset") for r in a.ref[:3]
        ]
    kwargs = dict(model=model, prompt=prompt, config=types.GenerateVideosConfig(**cfg))
    if a.image:
        kwargs["image"] = img(a.image)

    op = cl.with_backoff(lambda: client.models.generate_videos(**kwargs))
    t0 = time.time()
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
        print(f"  waiting... {time.time() - t0:.0f}s", flush=True)
    if op.error:
        sys.exit(f"Veo error: {op.error}")
    vids = (op.response.generated_videos if op.response else None) or []
    if not vids:
        sys.exit(f"Veo returned no video (possibly filtered): {op.response}")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".veo-raw.mp4")
    client.files.download(file=vids[0].video)
    vids[0].video.save(str(raw))
    # Strip Veo's audio; keep video stream untouched.
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-an", "-c:v", "copy", str(out)], check=True)
        raw.unlink()
    else:
        raw.rename(out)
    out.with_suffix(".prompt.txt").write_text(prompt + f"\n\nimage: {a.image}\nrefs: {a.ref}\nmodel: {model} {a.res} {a.duration}s\n")
    cl.append(ledger, {"kind": "veo", "plate": a.plate, "model": model, "res": a.res,
                       "seconds": a.duration, "usd": round(usd, 3), "out": str(out)})
    print(f"saved {out}")


if __name__ == "__main__":
    main()
