"""Word-level timestamps for narration audio (local Whisper, no API quota).

Uses mlx-whisper on Apple Silicon, faster-whisper elsewhere."""

import re

MLX_MODEL = "mlx-community/whisper-small.en-mlx"


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words(path) -> list[tuple[str, float, float]]:
    """[(normalized_word, start, end), ...] for a wav file."""
    try:
        import mlx_whisper
        res = mlx_whisper.transcribe(str(path), path_or_hf_repo=MLX_MODEL, word_timestamps=True, language="en")
        out = [(norm(w["word"]), w["start"], w["end"]) for sg in res["segments"] for w in sg.get("words", [])]
    except ImportError:
        from faster_whisper import WhisperModel
        segs, _ = WhisperModel("small.en", compute_type="int8").transcribe(str(path), word_timestamps=True, language="en")
        out = [(norm(w.word), w.start, w.end) for sg in segs for w in (sg.words or [])]
    return [w for w in out if w[0]]


def text(path) -> str:
    """Plain transcript (used to verify each narration beat)."""
    return " ".join(w[0] for w in words(path))
