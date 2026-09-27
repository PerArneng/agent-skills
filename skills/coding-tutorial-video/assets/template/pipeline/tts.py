"""Gemini TTS with a content-addressed cache (re-runs only synthesize changed text).

The provider is isolated here: to use another TTS, keep `synth(text, nonce) -> wav path`.
"""

import hashlib
import os
import sys
import time
import wave
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from script import PROJECT  # noqa: E402

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

MODEL = os.getenv("TTS_MODEL", PROJECT.get("tts_model", "gemini-3.1-flash-tts-preview"))
VOICE = os.getenv("TTS_VOICE", PROJECT.get("voice", "Sulafat"))
STYLE = PROJECT.get("persona", "")
CACHE = ROOT / "build" / "tts_cache"


def synth(text: str, nonce: int = 0) -> Path:
    """Speak `text` (the persona prompt is prepended). `nonce` forces a fresh take."""
    from google import genai
    from google.genai import errors, types

    key = hashlib.sha1(f"{MODEL}|{VOICE}|{STYLE}|{text}|{nonce}".encode()).hexdigest()[:16]
    out = CACHE / f"{key}.wav"
    if out.exists():
        return out
    CACHE.mkdir(parents=True, exist_ok=True)
    client = genai.Client()
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE))))
    for attempt in range(6):
        try:
            resp = client.models.generate_content(model=MODEL, contents=f"{STYLE}{text}", config=cfg)
            pcm = resp.candidates[0].content.parts[0].inline_data.data
            break
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or "PerDay" in str(e):
                raise  # a daily quota won't recover by waiting (free tier: 10 TTS requests/day/model)
            wait = 20 * (attempt + 1)
            print(f"  tts {MODEL} {e.code}; waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
    else:
        raise RuntimeError(f"TTS failed for: {text[:60]}")
    with wave.open(str(out), "wb") as wf:  # Gemini TTS returns 24 kHz 16-bit mono PCM
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    return out


if __name__ == "__main__":  # quick voice test: python tts.py "Some sentence."
    p = synth(" ".join(sys.argv[1:]))
    with wave.open(str(p)) as wf:
        d = wf.getnframes() / wf.getframerate()
    print(f"{p}  {d:.2f}s  {len(sys.argv[1:]) and len(' '.join(sys.argv[1:]).split()) / d * 60:.0f} wpm")
