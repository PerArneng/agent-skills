"""Verify every narration beat: transcribe what the voice actually said and compare it
to the script. TTS sometimes misreads (it once said "run finished" for "run started"),
and a split can clip a word. Flags beats below a similarity threshold.

  python check_narration.py            # all built scenes
  python check_narration.py e3         # scenes starting with e3

Fix a flagged beat by rewording it in script.py (then rebuild), or re-synthesize it
unchanged with: python build_audio.py --retake <beat_id>
Spelling-only differences (".env" vs "dot env", "1" vs "one") are fine.
"""

import difflib
import json
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from whisper_words import words  # noqa: E402

ROOT = Path(__file__).parent
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine", "10": "ten"}


def toks(s: str) -> list[str]:
    out = []
    for w in s.lower().replace("-", " ").replace(".", " dot ").split():
        w = "".join(ch for ch in w if ch.isalnum())
        if w:
            out.append(NUM.get(w, w))
    return out


def main(prefixes):
    tl = json.loads((ROOT / "build" / "timeline.json").read_text())
    flagged = total = 0
    for sid, info in tl.items():
        if prefixes and not any(sid.startswith(p) for p in prefixes):
            continue
        with wave.open(str(ROOT / "build" / "audio" / f"{sid}.wav")) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        for bt in info["beats"]:
            a = int((bt["start"] + bt["lead"]) * sr)
            e = int((bt["start"] + bt["lead"] + bt["voice"]) * sr)
            with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                with wave.open(f.name, "wb") as o:
                    o.setnchannels(1)
                    o.setsampwidth(2)
                    o.setframerate(sr)
                    o.writeframes(x[a:e].tobytes())
                heard = " ".join(w[0] for w in words(f.name))
            total += 1
            r = difflib.SequenceMatcher(a=toks(bt["say"]), b=toks(heard)).ratio()
            if r < 0.9:
                flagged += 1
                print(f"{bt['id']:10s} {r:.2f}\n   heard:  {heard}\n   script: {bt['say']}")
    print(f"checked {total} beats, {flagged} flagged (read each: spelling-only differences are fine)")


if __name__ == "__main__":
    main(sys.argv[1:])
