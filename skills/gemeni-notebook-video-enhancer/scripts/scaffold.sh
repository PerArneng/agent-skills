#!/usr/bin/env bash
# Create a motion-remake project for a presentation video.
# usage: scaffold.sh <video> <project_dir> [--landscape] [--4k] [--scale N] [--fps 60] [--output <file.mp4>]
#   default stage is 1080x1920 (9:16, YouTube Shorts / Reels / TikTok); --landscape gives 1920x1080.
#   --scale N renders at N× the stage (deviceScaleFactor); --4k = --landscape --scale 2 → 3840x2160.
# Result: <project_dir> with the engine, config.json, public/audio.m4a, node_modules, chromium,
#         a Python venv (.venv) with whisper, and analysis/ (contact sheets + transcript).
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; PROJ="$2"; shift 2
W=1080; H=1920; FPS=60; SCALE=1; OUTPUT=""
while [ $# -gt 0 ]; do case "$1" in
  --landscape) W=1920; H=1080;; --4k) W=1920; H=1080; SCALE=2;; --scale) SCALE="$2"; shift;; --fps) FPS="$2"; shift;; --output) OUTPUT="$2"; shift;; esac; shift; done
[ -z "$OUTPUT" ] && OUTPUT="$(dirname "$VIDEO")/$(basename "${VIDEO%.*}")_motion.mp4"

mkdir -p "$PROJ"; PROJ="$(cd "$PROJ" && pwd)"
if [ -f "$PROJ/package.json" ]; then echo "refusing: $PROJ already has a project (edit it instead)"; exit 1; fi
cp -R "$SKILL_DIR/assets/template/." "$PROJ/"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
cat > "$PROJ/config.json" <<JSON
{
  "source": "$VIDEO",
  "output": "$OUTPUT",
  "width": $W,
  "height": $H,
  "fps": $FPS,
  "scale": $SCALE,
  "duration": $(python3 -c "print(round($DUR, 3))")
}
JSON
ffmpeg -v error -y -i "$VIDEO" -vn -c:a aac -b:a 192k "$PROJ/public/audio.m4a"

cd "$PROJ"
npm install --silent --no-audit --no-fund
npx playwright install chromium >/dev/null

# whisper venv
python3 -m venv .venv
if [ "$(uname -s)-$(uname -m)" = "Darwin-arm64" ]; then .venv/bin/pip install -q mlx-whisper; else .venv/bin/pip install -q faster-whisper; fi

bash "$SKILL_DIR/scripts/analyze.sh" "$VIDEO" "$PROJ/analysis"
.venv/bin/python "$SKILL_DIR/scripts/transcribe.py" "$VIDEO" "$PROJ/analysis"
echo
echo "project ready: $PROJ   (stage ${W}x${H} ×${SCALE} @ ${FPS}fps, ${DUR}s)"
echo "next: read analysis/sheet_*.png with analysis/sheets.txt + analysis/transcript.txt and write analysis/beats.md"
