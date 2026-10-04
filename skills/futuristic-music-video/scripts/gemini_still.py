# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai>=1.40", "pillow"]
# ///
"""Generate a still image with Gemini (Nano Banana family).

  uv run gemini_still.py --prompt-file p.txt --bible video/bible.md \
      --ref assets/still-images/subject-ref.png --out assets/still-images/env-1.png
  uv run gemini_still.py --list-models        # free; confirms current model ids
  uv run gemini_still.py ... --dry-run        # print request + cost, no call

The bible (if given) is prepended to the prompt. Reference images (--ref, repeatable) keep
the subject and world consistent: always pass the locked subject still after it exists.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cost_ledger as cl  # noqa: E402

MODELS = {
    "flash": "gemini-2.5-flash-image",
    "nb2": "gemini-3.1-flash-image",
    "pro": "gemini-3-pro-image",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--bible", help="bible.md to prepend")
    ap.add_argument("--ref", action="append", default=[], help="reference image (repeatable, max ~3 useful)")
    ap.add_argument("--tier", choices=MODELS, default="flash", help="flash (cheap drafts) | nb2 | pro (character sheets)")
    ap.add_argument("--model", help="override model id")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--out", help="output .png path")
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()

    from google import genai
    from google.genai import types

    if a.list_models:
        client = genai.Client(api_key=cl.load_api_key())
        for m in client.models.list():
            name = m.name.removeprefix("models/")
            if any(k in name for k in ("image", "veo", "imagen")):
                print(name, "-", getattr(m, "display_name", ""))
        return

    prompt = a.prompt or (Path(a.prompt_file).read_text() if a.prompt_file else None)
    if not prompt or not a.out:
        ap.error("--prompt/--prompt-file and --out are required")
    if a.bible:
        prompt = Path(a.bible).read_text().strip() + "\n\n" + prompt
    model = a.model or MODELS[a.tier]
    usd = cl.IMAGE_PER_STILL[a.tier]
    ledger = a.ledger or cl.default_ledger()

    print(f"model={model} aspect={a.aspect} refs={a.ref} est=${usd:.3f}")
    if a.dry_run:
        print("--- prompt ---\n" + prompt)
        return

    from PIL import Image

    client = genai.Client(api_key=cl.load_api_key())
    contents: list = [prompt] + [Image.open(r) for r in a.ref]
    resp = cl.with_backoff(lambda: client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=a.aspect),
        ),
    ))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for part in resp.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            out.write_bytes(part.inline_data.data)
            # Keep the prompt next to the image so stills can be regenerated or tweaked later.
            out.with_suffix(".prompt.txt").write_text(prompt + "\n\nrefs: " + ", ".join(a.ref) + f"\nmodel: {model}\n")
            cl.append(ledger, {"kind": "still", "model": model, "usd": usd, "out": str(out)})
            print(f"saved {out}")
            return
    text = " ".join(p.text for p in resp.candidates[0].content.parts if p.text)
    sys.exit(f"No image returned. Model said: {text[:500]}")


if __name__ == "__main__":
    main()
