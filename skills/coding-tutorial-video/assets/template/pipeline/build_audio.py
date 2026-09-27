"""Synthesize, split, pace and time the narration → build/audio/<scene>.wav + build/timeline.json.

  python build_audio.py                 # everything (cached takes cost nothing)
  python build_audio.py e2 e3s1         # only scenes whose id starts with these prefixes
  python build_audio.py --retake ev9    # re-synthesize single beats (misread, clipped); persists

How it works
  * Beats are packed into takes of ~70 s of speech: one TTS request per take keeps the
    voice consistent and saves quota. Gemini TTS stops at ~110 s of audio, so takes stay
    well below that; a truncated take is detected (its last words are never heard).
  * Each take is split into beats by aligning Whisper word times to the script.
  * Pacing (fluid-learning rules): natural pauses are widened a little, any beat spoken
    faster than MAX_WPM is gently slowed, retrieval questions are slowed, and every beat
    gets an anticipation lead, a hold of stillness, and (for asks) a silent window.
"""

import difflib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from beats import Beat  # noqa: E402
from script import EPISODES, PROJECT  # noqa: E402
from tts import synth  # noqa: E402
from whisper_words import norm, words  # noqa: E402

SR = 24000
ROOT = Path(__file__).parent
BUILD = ROOT / "build"
LEAD = 0.35            # anticipation: motion aims the eye before the voice names the thing
TEMPO_ASK = 0.92       # retrieval questions a little slower
MAX_WPM = 155          # gently slow any beat spoken faster than this
TAKE_SECONDS = 70      # target speech per TTS request
SEP = "\n\n[long pause]\n\n"

BEATS = {bt.id: bt for scenes in EPISODES.values() for sc in scenes for bt in sc.beats}
SCENE_BEATS = {sc.id: [bt.id for bt in sc.beats] for scenes in EPISODES.values() for sc in scenes}
RETAKES = BUILD / "retakes.json"


def spoken(text: str) -> str:
    for pat, rep in PROJECT.get("pronounce", []):
        text = re.sub(pat, rep, text)
    return text


def voice_text(bt: Beat) -> str:
    return ("[slowly, curious] " if bt.ask else "") + spoken(bt.say)


# ------------------------------------------------------------------ audio utils
def read_wav(path) -> np.ndarray:
    with wave.open(str(path)) as wf:
        return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(path, x: np.ndarray, sr=SR):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def silent_runs(x: np.ndarray, min_len: float, thresh_db: float = -38):
    hop = int(0.01 * SR)
    n = len(x) // hop
    if n == 0:
        return []
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    quiet = 20 * np.log10(rms / np.percentile(rms, 95)) < thresh_db
    runs, start = [], None
    for i, q in enumerate(np.append(quiet, False)):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * 0.01 >= min_len:
                runs.append((start * hop, i * hop))
            start = None
    return runs


def trim(x: np.ndarray, pad=0.04) -> np.ndarray:
    runs = silent_runs(x, 0.01)
    s, e = 0, len(x)
    if runs and runs[0][0] == 0:
        s = max(0, runs[0][1] - int(pad * SR))
    if runs and runs[-1][1] >= len(x) - int(0.011 * SR):
        e = min(len(x), runs[-1][0] + int(pad * SR))
    return x[s:e]


def widen_pauses(x: np.ndarray) -> np.ndarray:
    """Sentence gaps → at least 0.42 s, clause gaps ×1.25: designed pauses, not dead air."""
    out, cur = [], 0
    for s, e in silent_runs(x, 0.12):
        gap = (e - s) / SR
        target = max(gap, 0.42) if gap >= 0.26 else gap * 1.25
        out += [x[cur:s], np.zeros(int(target * SR), np.float32)]
        cur = e
    out.append(x[cur:])
    return np.concatenate(out)


def tempo(x: np.ndarray, factor: float) -> np.ndarray:
    if abs(factor - 1.0) < 1e-3:
        return x
    tmp = BUILD / "tmp"
    a, b = tmp / "in.wav", tmp / "out.wav"
    write_wav(a, x)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(a), "-af", f"atempo={factor}", str(b)], check=True)
    return read_wav(b)


def chime(freqs, dur=0.5, gain=0.05) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 7) * np.minimum(1, t / 0.01)
    return sum(np.sin(2 * np.pi * f * t) for f in freqs) * env * gain / len(freqs)


# ------------------------------------------------------------------ takes
def pack_takes() -> list[list[str]]:
    """Consecutive beats of one episode, ~TAKE_SECONDS of speech (at ~150 wpm) per take."""
    takes = []
    for scenes in EPISODES.values():
        cur, secs = [], 0.0
        for sc in scenes:
            for bt in sc.beats:
                s = len(bt.say.split()) / 2.5
                if cur and secs + s > TAKE_SECONDS:
                    takes.append(cur)
                    cur, secs = [], 0.0
                cur.append(bt.id)
                secs += s
        if cur:
            takes.append(cur)
    return takes


def split_by_words(x: np.ndarray, beats: list[Beat], wav_path):
    """Cut a take between beats: align Whisper's words to the script, cut in each gap's quietest spot."""
    heard = words(wav_path)
    script_words, owner = [], []
    for k, bt in enumerate(beats):
        for w in spoken(bt.say).replace(".", " ").split():
            if norm(w):
                script_words.append(norm(w))
                owner.append(k)
    sm = difflib.SequenceMatcher(a=script_words, b=[h[0] for h in heard], autojunk=False)
    t_of = {}
    for blk in sm.get_matching_blocks():
        for i in range(blk.size):
            t_of[blk.a + i] = heard[blk.b + i]
    tail = [i for i in range(len(script_words)) if owner[i] == len(beats) - 1][-3:]
    if not any(i in t_of for i in tail):
        print("    take looks TRUNCATED: its last words were never heard", file=sys.stderr)
        return None
    cuts = []
    for k in range(len(beats) - 1):
        last = max((i for i in t_of if owner[i] == k), default=None)
        first = min((i for i in t_of if owner[i] == k + 1), default=None)
        if last is None or first is None:
            print(f"    could not locate the boundary after {beats[k].id}", file=sys.stderr)
            return None
        e, s0 = t_of[last][2], t_of[first][1]
        a, b = int(e * SR), int(max(s0, e + 0.01) * SR)
        seg = x[a:b]
        if len(seg) > int(0.05 * SR):
            hop = int(0.02 * SR)
            n = len(seg) // hop
            en = (seg[: n * hop].reshape(n, hop) ** 2).mean(axis=1)
            cuts.append(a + int(np.argmin(en)) * hop + hop // 2)
        else:
            cuts.append((a + b) // 2)
    if cuts != sorted(cuts):
        return None
    pts = [0] + cuts + [len(x)]
    return [x[pts[i]: pts[i + 1]] for i in range(len(beats))]


def build_take(ids: list[str]) -> dict:
    beats = [BEATS[i] for i in ids]
    path = synth(SEP.join(voice_text(bt) for bt in beats))
    pieces = split_by_words(read_wav(path), beats, path)
    if pieces is None:
        if len(ids) == 1:
            raise SystemExit(f"beat {ids[0]} failed to synthesize cleanly; try --retake {ids[0]}")
        half = len(ids) // 2  # truncated or unalignable: split the take in two and retry
        print(f"  take {ids[0]}..{ids[-1]} failed; retrying as two takes", file=sys.stderr)
        return {**build_take(ids[:half]), **build_take(ids[half:])}
    return dict(zip(ids, pieces))


def scene_info(scene, pieces) -> dict:
    track, beats, t = [], [], 0.0
    for bt, piece in zip(scene.beats, pieces):
        voice = widen_pauses(trim(piece))
        wpm = len(bt.say.split()) / (len(voice) / SR / 60)
        factor = TEMPO_ASK if bt.ask else (max(0.9, MAX_WPM / wpm) if wpm > MAX_WPM else 1.0)
        voice = tempo(voice, round(factor, 3))
        dur = len(voice) / SR
        window = np.zeros(int((bt.hold + bt.silence) * SR), np.float32)
        if bt.ask:  # soft two-note earcon marks the start of the retrieval window
            c = chime([660, 990])
            window[: len(c)] += c
        seg = np.concatenate([np.zeros(int(LEAD * SR), np.float32), voice, window])
        beats.append(dict(id=bt.id, say=bt.say, ask=bt.ask, start=round(t, 4), lead=LEAD, voice=round(dur, 4),
                          hold=bt.hold, silence=bt.silence, total=round(len(seg) / SR, 4),
                          wpm=round(len(bt.say.split()) / (dur / 60), 1)))
        track.append(seg)
        t += len(seg) / SR
    audio = np.concatenate(track)
    write_wav(BUILD / "audio" / f"{scene.id}.wav", audio)
    return dict(id=scene.id, title=scene.title, total=round(len(audio) / SR, 4), beats=beats)


def main(argv):
    retakes = json.loads(RETAKES.read_text()) if RETAKES.exists() else {}
    if "--retake" in argv:
        i = argv.index("--retake")
        for bid in argv[i + 1].split(","):
            if bid not in BEATS:
                raise SystemExit(f"unknown beat {bid}")
            retakes[bid] = retakes.get(bid, 0) + 1
        RETAKES.parent.mkdir(parents=True, exist_ok=True)
        RETAKES.write_text(json.dumps(retakes, indent=1))
        argv = argv[:i] + argv[i + 2:]
    only = argv or None
    wanted = [s for s in SCENE_BEATS if not only or any(s.startswith(o) for o in only)]
    wanted_beats = {b for s in wanted for b in SCENE_BEATS[s]}

    pieces = {}
    for take in pack_takes():
        if wanted_beats & set(take):
            pieces.update(build_take(take))
    for bid, n in retakes.items():  # single-beat takes override the take's piece
        if bid in wanted_beats:
            path = synth(voice_text(BEATS[bid]), nonce=n)
            pieces[bid] = read_wav(path)

    tl_path = BUILD / "timeline.json"
    timeline = json.loads(tl_path.read_text()) if tl_path.exists() else {}
    by_id = {sc.id: sc for scenes in EPISODES.values() for sc in scenes}
    for sid in wanted:
        sc = by_id[sid]
        info = scene_info(sc, [pieces[bt.id] for bt in sc.beats])
        timeline[sid] = info
        n_words = sum(len(x["say"].split()) for x in info["beats"])
        talk = info["total"] - sum(x["silence"] for x in info["beats"])
        voice = np.mean([x["wpm"] for x in info["beats"] if not x["ask"]] or [0])
        print(f"{sid}: {info['total']:6.1f}s  speech {voice:3.0f} wpm  with holds {n_words / (talk / 60):3.0f} wpm")
    tl_path.write_text(json.dumps(timeline, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
