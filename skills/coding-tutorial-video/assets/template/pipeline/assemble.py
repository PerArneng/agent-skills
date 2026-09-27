"""Build per-episode audio + data for the web renderer.

  python assemble.py ep1 [ep2 ...]           # from the synthesized narration (build_audio.py)
  python assemble.py --estimate ep1          # storyboard mode: no TTS, timings estimated from
                                             # word counts (~150 wpm), silent audio. Lay out and
                                             # screenshot scenes before spending TTS quota.

Writes, per episode:
  build/<ep>.wav            narration joined with settled seams, loudness-normalized (-16 LUFS)
  web/public/<ep>.m4a       the same audio for live preview
  web/src/data/<ep>.json    absolute beat times + word-level times (Whisper)
and web/src/data/source.json (the real code files + captured terminal output),
and web/config.json (stage size, fps, episode durations/audio/output paths).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from build_audio import LEAD, SR, chime, read_wav, write_wav  # noqa: E402
from script import EPISODES, PROJECT  # noqa: E402
from whisper_words import words  # noqa: E402

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
WEB = ROOT / "web"
DATA = WEB / "src" / "data"
SEAM = 1.8  # settled stillness + next segment title (must match web/src/lib.js)


def estimated_scene(sc) -> tuple[dict, np.ndarray]:
    beats, t = [], 0.0
    for bt in sc.beats:
        voice = len(bt.say.split()) / (150 / 60) + 0.3 * bt.say.count(".")
        total = LEAD + voice + bt.hold + bt.silence
        beats.append(dict(id=bt.id, say=bt.say, ask=bt.ask, start=t, lead=LEAD, voice=voice, hold=bt.hold,
                          silence=bt.silence, total=total))
        t += total
    return dict(id=sc.id, title=sc.title, total=t, beats=beats), np.zeros(int(t * SR), np.float32)


def build_episode(ep, scenes, timeline, estimate):
    parts, beats, seams, t = [], [], [], 0.0
    for k, sc in enumerate(scenes):
        if k > 0:
            gap = np.zeros(int(SEAM * SR), np.float32)
            c = chime([392, 587], dur=0.8, gain=0.035)  # quiet two-note seam earcon
            gap[: len(c)] += c
            parts.append(gap)
            seams.append(dict(scene=sc.id, title=sc.title, t=round(t, 3)))
            t += SEAM
        if estimate:
            info, audio = estimated_scene(sc)
        else:
            info, audio = timeline[sc.id], read_wav(BUILD / "audio" / f"{sc.id}.wav")
        for bt in info["beats"]:
            a = t + bt["start"]
            beats.append(dict(id=bt["id"], scene=sc.id, ask=bt["ask"], say=bt["say"], start=round(a, 3),
                              v0=round(a + bt["lead"], 3), v1=round(a + bt["lead"] + bt["voice"], 3),
                              end=round(a + bt["total"], 3), silence=bt["silence"]))
        parts.append(audio)
        t += len(audio) / SR
    parts.append(np.zeros(int(1.0 * SR), np.float32))  # settle to stillness at the end
    t += 1.0
    raw = BUILD / f"{ep}_raw.wav"
    write_wav(raw, np.concatenate(parts))
    out = BUILD / f"{ep}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", str(out)], check=True)
    (WEB / "public").mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:a", "aac", "-b:a", "192k",
                    str(WEB / "public" / f"{ep}.m4a")], check=True)
    heard = [] if estimate else words(raw)
    for bt in beats:
        bt["words"] = [dict(w=w, t=round(s, 3)) for w, s, _ in heard if bt["v0"] - 0.2 <= s <= bt["v1"] + 0.2]
    duration = round(t, 3)
    (DATA / f"{ep}.json").write_text(json.dumps(dict(duration=duration, estimated=estimate, seams=seams,
                                                     beats=beats), indent=1))
    print(f"{ep}: {duration:.1f}s, {len(beats)} beats{' (ESTIMATED timings)' if estimate else ''}")
    return duration


def main(argv):
    estimate = "--estimate" in argv
    only = [a for a in argv if not a.startswith("--")] or None
    DATA.mkdir(parents=True, exist_ok=True)
    code_dir = (ROOT / PROJECT["code_dir"]).resolve()
    cap_dir = (ROOT / PROJECT.get("captures_dir", "captures")).resolve()
    source = dict(code={f: (code_dir / f).read_text() for f in PROJECT.get("code_files", [])},
                  captures={f: (cap_dir / f).read_text() for f in PROJECT.get("capture_files", [])
                            if (cap_dir / f).exists()})
    (DATA / "source.json").write_text(json.dumps(source, indent=1))
    tl_path = BUILD / "timeline.json"
    timeline = json.loads(tl_path.read_text()) if tl_path.exists() else {}
    cfg_path = WEB / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    cfg.update(width=1920, height=1080, fps=cfg.get("fps", 60), scale=cfg.get("scale", 2))
    cfg.setdefault("episodes", {})
    for ep, scenes in EPISODES.items():
        if only and ep not in only:
            continue
        if not estimate and not all(sc.id in timeline for sc in scenes):
            print(f"{ep}: narration not built yet (run build_audio.py, or use --estimate)")
            continue
        dur = build_episode(ep, scenes, timeline, estimate)
        slug = re.sub(r"[^a-z0-9]+", "_", PROJECT.get("title", "tutorial").lower()).strip("_")
        cfg["episodes"][ep] = dict(duration=dur, audio=str(BUILD / f"{ep}.wav"),
                                   output=str(ROOT / "out" / f"{slug}_{ep}_4k.mp4"))
    cfg_path.write_text(json.dumps(cfg, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
