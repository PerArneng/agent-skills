#!/usr/bin/env bash
# Extract a brand palette + fonts from a website's CSS so the remake can match it ("use the style of <url>").
# usage: brand-from-site.sh <url> [out_dir=./analysis]
# Writes <out_dir>/brand.txt: CSS custom properties that hold colours, font-family tokens, and the most used hex colours.
# Notes: sends a browser User-Agent (CDNs such as CloudFront often 403 curl's default UA), and follows linked
# stylesheets. WebFetch-style tools only see rendered text, not CSS — use this instead.
set -euo pipefail
URL="$1"; OUT="${2:-./analysis}"; mkdir -p "$OUT"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
curl -sL -A "$UA" "$URL" -o "$TMP/page.html"
ORIGIN="$(python3 -c "from urllib.parse import urlsplit as u;x=u('$URL');print(f'{x.scheme}://{x.netloc}')")"
: > "$TMP/all.css"
for c in $(grep -oE 'href="[^"]+\.css[^"]*"' "$TMP/page.html" | sed 's/href="//;s/"$//' | head -12); do
  case "$c" in http*) u="$c";; //*) u="https:$c";; /*) u="$ORIGIN$c";; *) u="$ORIGIN/$c";; esac
  curl -sL -A "$UA" "$u" >> "$TMP/all.css" || true
done
grep -oE '<style[^>]*>[^<]*' "$TMP/page.html" >> "$TMP/all.css" || true
{
  echo "# brand tokens from $URL   (html $(wc -c < "$TMP/page.html") bytes, css $(wc -c < "$TMP/all.css") bytes)"
  echo; echo "## colour custom properties"
  grep -oE -- '--[a-zA-Z0-9_-]+:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\)|var\([^)]*\))' "$TMP/all.css" | sort -u | head -150
  echo; echo "## font tokens / families"
  grep -oE -- '--[a-zA-Z0-9_-]*font[a-zA-Z0-9_-]*:[^;}]+' "$TMP/all.css" | sort -u | head -20
  grep -oE 'font-family:[^;}]+' "$TMP/all.css" | sort | uniq -c | sort -rn | head -10
  echo; echo "## most used hex colours"
  cat "$TMP/all.css" "$TMP/page.html" | grep -oE '#[0-9a-fA-F]{6}\b' | tr 'A-F' 'a-f' | sort | uniq -c | sort -rn | head -25
  echo; echo "## easing / motion tokens"
  grep -oE -- '--[a-zA-Z0-9_-]*(ease|duration)[a-zA-Z0-9_-]*:[^;}]+' "$TMP/all.css" | sort -u | head -10
} > "$OUT/brand.txt"
if [ "$(wc -c < "$TMP/all.css")" -lt 200 ]; then echo "warning: little or no CSS fetched (blocked or JS-rendered?) — try Chrome tools / a screenshot" >&2; fi
echo "wrote $OUT/brand.txt"
