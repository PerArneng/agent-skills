#!/usr/bin/env bash
# Probe a presentation video and sample it into labelled contact sheets for visual review.
# usage: analyze.sh <video> <outdir> [interval_seconds=2.5]
# writes: <outdir>/probe.txt, <outdir>/frames/f_###.png, <outdir>/sheet_#.png, <outdir>/sheets.txt (tile → timestamp map)
set -euo pipefail
VIDEO="$1"; OUT="$2"; STEP="${3:-2.5}"
mkdir -p "$OUT/frames"; rm -f "$OUT"/frames/f_*.png "$OUT"/sheet_*.png
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact "$VIDEO" | tee "$OUT/probe.txt"
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$VIDEO")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$VIDEO")
# thumbnails ~360px on the long edge
if [ "$H" -ge "$W" ]; then SCALE="-2:360"; COLS=8; ROWS=2; else SCALE="360:-2"; COLS=4; ROWS=4; fi
FPSV=$(python3 -c "print(1/$STEP)")
ffmpeg -v error -i "$VIDEO" -vf "fps=$FPSV,scale=$SCALE" "$OUT/frames/f_%03d.png"
N=$(ls "$OUT"/frames/f_*.png | wc -l | tr -d ' ')
PER=$((COLS*ROWS))
ffmpeg -v error -y -i "$OUT/frames/f_%03d.png" -vf "tile=${COLS}x${ROWS}" "$OUT/sheet_%d.png"
# legend: ffmpeg's fps filter emits frame k at t ≈ k*STEP
python3 - "$N" "$PER" "$COLS" "$STEP" > "$OUT/sheets.txt" <<'PY'
import sys
n, per, cols, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
for k in range(n):
    s, i = divmod(k, per)
    r, c = divmod(i, cols)
    print(f"sheet_{s+1}.png row {r+1} col {c+1}: t={k*step:.1f}s")
PY
echo "frames: $N  sheets: $(ls "$OUT"/sheet_*.png | wc -l | tr -d ' ')  (${COLS}x${ROWS} tiles, left→right, top→bottom, ${STEP}s apart)"
echo "legend: $OUT/sheets.txt"
