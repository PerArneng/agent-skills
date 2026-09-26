#!/usr/bin/env python3
"""Word-level transcript of a video's narration.

usage: transcribe.py <video> <outdir>
writes <outdir>/transcript.json  ({"text", "segments":[{s,e,text}], "words":[{w,s,e}]})
       <outdir>/transcript.txt   (one timed line per segment — the human-readable beat list)
       <outdir>/words.txt        (word@start … for picking exact cue times)

Uses mlx-whisper on Apple Silicon, faster-whisper elsewhere. Run it with a venv python
that has one of them installed (scripts/scaffold.sh sets that up in <project>/.venv).
"""
import json, os, subprocess, sys, tempfile

video, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
wav = os.path.join(tempfile.mkdtemp(), "audio.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)

segments, words = [], []
try:
    import mlx_whisper
    r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True)
    for seg in r["segments"]:
        segments.append({"s": round(seg["start"], 2), "e": round(seg["end"], 2), "text": seg["text"].strip()})
        words += [{"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)} for w in seg.get("words", [])]
except ImportError:
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3-turbo" if os.environ.get("WHISPER_BIG") else "small", compute_type="int8")
    segs, _ = model.transcribe(wav, word_timestamps=True)
    for seg in segs:
        segments.append({"s": round(seg.start, 2), "e": round(seg.end, 2), "text": seg.text.strip()})
        words += [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in seg.words or []]

text = " ".join(s["text"] for s in segments)
json.dump({"text": text, "segments": segments, "words": words}, open(os.path.join(out, "transcript.json"), "w"), indent=1)
with open(os.path.join(out, "transcript.txt"), "w") as f:
    for s in segments:
        f.write(f"{s['s']:7.2f}-{s['e']:7.2f}  {s['text']}\n")
with open(os.path.join(out, "words.txt"), "w") as f:
    f.write(" ".join(f"{w['w']}@{w['s']}" for w in words) + "\n")
print(open(os.path.join(out, "transcript.txt")).read())
