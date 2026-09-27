#!/usr/bin/env bash
# Create a tutorial-video workspace inside a project.
# usage: scaffold.sh [target_dir]        (default: ./video)
# Result: <target>/ with the narration pipeline (Python, own uv project) and <target>/web
# (the GSAP + Playwright renderer), dependencies installed, and the example lesson ready
# for a storyboard render:  cd <target> && uv run python assemble.py --estimate ep1
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-video}"
if [ -e "$TARGET/script.py" ]; then echo "refusing: $TARGET already has a tutorial workspace (edit it instead)"; exit 1; fi
mkdir -p "$TARGET"
cp -R "$SKILL_DIR/assets/template/pipeline/." "$TARGET/"
mkdir -p "$TARGET/web"
cp -R "$SKILL_DIR/assets/template/web/." "$TARGET/web/"
cp "$SKILL_DIR/assets/template/gitignore" "$TARGET/.gitignore"
cd "$TARGET"

for tool in uv node npm ffmpeg; do
  command -v "$tool" >/dev/null || { echo "missing dependency: $tool"; exit 1; }
done

uv sync -q
(cd web && npm install --silent --no-audit --no-fund && npx playwright install chromium >/dev/null)

# real output for the example lesson (replace with captures of your own project)
python3 example/hello.py Ada > captures/hello.txt

echo
echo "workspace ready: $(pwd)"
echo "API key: put GEMINI_API_KEY in $(pwd)/.env or the project's .env (used for narration only)"
echo "next: edit script.py (the lesson) and web/src/episodes/ep1.js (the visuals)"
