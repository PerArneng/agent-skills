# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Generate Veo plates sequentially from a manifest. Re-runnable: finished plates are skipped.

  uv run veo_batch.py video/plates.json --tier lite --res 720p            # first pass, all plates
  uv run veo_batch.py video/plates.json --tier fast --res 1080p a b c     # polish pass → <name>-fast.mp4
  uv run veo_batch.py video/plates.json --list

Manifest (video/plates.json):
  {"dance-servers": {"image": "assets/still-images/singer-servers.png", "prompt": "video/prompts/dance-servers-motion.txt"},
   "utopia":        {"image": "assets/still-images/env-utopia.png",     "prompt": "video/prompts/utopia-motion.txt"}}
Outputs: assets/video-clips/<name>.mp4 (lite) or <name>-<tier>.mp4 (fast/standard). A storyboard that prefers
<name>-fast.mp4, then <name>.mp4, then the still (Ken Burns) degrades gracefully while plates are missing.

Stops after --max-quota-fails consecutive 429/RESOURCE_EXHAUSTED failures: that is the per-day request quota
(it hit after ~20 Veo calls/day on a Tier 1 key, on Fast AND Lite), and retrying only burns minutes. Safety-filter
rejections ("possibly filtered", not charged) are reported and the batch moves on. 402 = prepaid credits used up.
Caps: passes --force to gemini_video.py, so get the user's OK on the plate count/cost first.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("manifest")
ap.add_argument("names", nargs="*", help="subset of plates (default: all, manifest order)")
ap.add_argument("--tier", default="lite", choices=["lite", "fast", "standard"])
ap.add_argument("--res", default="720p", choices=["720p", "1080p", "4k"])
ap.add_argument("--out-dir", default="assets/video-clips")
ap.add_argument("--aspect", default="16:9", help="16:9 (default) or 9:16 for vertical Shorts")
ap.add_argument("--plate-prefix", default="", help="prefix for ledger plate names, e.g. 'short-' so a second video's plates count separately")
ap.add_argument("--max-quota-fails", type=int, default=2)
ap.add_argument("--list", action="store_true")
a = ap.parse_args()

plates = json.loads(Path(a.manifest).read_text())
names = a.names or list(plates)
suffix = "" if a.tier == "lite" else f"-{a.tier}"
if a.list:
    for n, p in plates.items():
        have = [s for s in ("", "-fast", "-standard") if (Path(a.out_dir) / f"{n}{s}.mp4").exists()]
        print(f"{n:20} {p['image']:45} have: {' '.join(s or 'lite' for s in have) or '-'}")
    sys.exit()

done, failed, quota = [], [], 0
for n in names:
    if n not in plates:
        print(f"unknown plate {n}"); failed.append(n); continue
    out = Path(a.out_dir) / f"{n}{suffix}.mp4"
    if out.exists():
        print(f"skip {out} (exists)"); continue
    cmd = ["uv", "run", str(HERE / "gemini_video.py"), "--plate", f"{a.plate_prefix}{n}{suffix}", "--image", plates[n]["image"],
           "--prompt-file", plates[n]["prompt"], "--tier", a.tier, "--res", a.res, "--aspect", a.aspect, "--force", "--out", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = r.stdout + r.stderr
    if r.returncode == 0 and out.exists():
        print(f"saved {out}"); done.append(n); quota = 0
        continue
    failed.append(n)
    if re.search(r"ClientError: 402|\b402 [A-Z_]{4,}|PAYMENT_REQUIRED", log):   # not a bare "402" (traceback line numbers)
        print("402: prepaid credits are used up — top up the Gemini billing account, then re-run."); break
    if "spending cap" in log or "spend cap" in log:          # also a 429, but waiting won't help
        print("429: the Gemini project hit its MONTHLY SPENDING CAP — raise it at https://ai.studio/spend, then re-run.")
        break
    if "429" in log or "RESOURCE_EXHAUSTED" in log:
        quota += 1
        print(f"{n}: quota error ({quota}/{a.max_quota_fails})")
        if quota >= a.max_quota_fails:
            print("stopping: Veo request quota (per-minute or per-day) reached. Re-run the same command later;"
                  " finished plates are skipped.\n" + log.strip().splitlines()[-1][:300])
            break
    elif "filtered" in log:
        print(f"{n}: rejected by the safety filter (not charged) — reword the motion prompt or use another still")
    else:
        print(f"{n}: failed\n{log[-800:]}")
print(f"done {len(done)}, failed {len(failed)}" + (f": {' '.join(failed)}" if failed else ""))
