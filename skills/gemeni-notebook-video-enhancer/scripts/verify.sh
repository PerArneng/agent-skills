#!/usr/bin/env bash
# Check a rendered remake: format, duration vs source, audio, black frames, and a contact sheet
# sampled at the same interval as analyze.sh so it can be compared beat-for-beat with the source.
# usage: verify.sh <project_dir> [interval=2.5]
set -euo pipefail
PROJ="$1"; STEP="${2:-2.5}"
read -r OUT SRC < <(python3 -c "import json;c=json.load(open('$PROJ/config.json'));print(c['output'],c['source'])")
echo "== output";  ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate -of compact "$OUT"
echo "== source duration"; ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC"
echo "== black segments (none listed = good)"
ffmpeg -v info -i "$OUT" -vf "blackdetect=d=0.1:pix_th=0.03" -an -f null - 2>&1 | grep -o "black_start.*" || true
mkdir -p "$PROJ/analysis"; rm -f "$PROJ"/analysis/output_sheet_*.jpg
W=$(python3 -c "import json;c=json.load(open('$PROJ/config.json'));print(c['width'])"); H=$(python3 -c "import json;c=json.load(open('$PROJ/config.json'));print(c['height'])")
if [ "$H" -ge "$W" ]; then T="scale=-2:360,tile=8x5"; else T="scale=360:-2,tile=5x8"; fi
ffmpeg -v error -y -i "$OUT" -vf "fps=$(python3 -c "print(1/$STEP)"),$T" "$PROJ/analysis/output_sheet_%d.jpg"
echo "== contact sheets: $PROJ/analysis/output_sheet_*.jpg (40 tiles each, ${STEP}s apart, left→right, top→bottom)"
