# Focus dark palette (the default)

This is the default palette for every remake, unless the user picks another one when asked (see SKILL.md → *Default choices*). It comes from the "Illusion of Safety" remake, whose user asked for "a dark mode colour palette that has been seen as optimal for focus and engagement".

It follows common dark-mode readability guidance, such as Material Design's dark theme. This is guidance, not a proven optimum, so describe it that way to users:
- **Background:** a soft neutral charcoal, never pure black or a saturated navy. This reduces halation around bright shapes.
- **Text:** off-white `#E8EAED`, never pure white. It's easier on the eyes over several minutes.
- **Accents:** desaturated pastel accents. Fully saturated colours "vibrate" on a dark background.
- **Colour meaning:** one warm colour means *attention*, and the viewer's eye follows it (the human figure, titles, key numbers). One calm, cool colour means *the system or AI*. Soft coral means danger and sage/mint means the solution, and they are used only for those meanings.

## Tokens

| role | token | hex |
|---|---|---|
| base / stage | `--navy` | `#121418` |
| raised surfaces | `--n-800` / `--n-700` / `--n-600` | `#1a1d23` / `#23272e` / `#3a3f48` |
| secondary text | `--n-400` / `--n-300` | `#9aa0a6` / `#c4c7cc` |
| primary text | `--ink` / `--fog` | `#e8eaed` |
| attention / human (warm) | `--glow` | `#f2b45a` (deep `#e0963a`, light `#f5d29a`) |
| system / AI (cool) | `--electric` / `--blue` | `#8ab4f8` / `#6e9cf0` |
| danger | `--red` | `#f28b82` |
| success | `--green` | `#81c995` |
| solution / calm | `--teal` | `#78d9c8` |

Pastel chips (the red, green and blue backgrounds) need **dark text** (`color:#121418`), not white.

## Set-up (after scaffold)

```bash
cd motion && npm i @fontsource-variable/inter-tight @fontsource-variable/oswald
cp <skill>/references/themes/focus-dark.css src/style.css
cp <skill>/references/themes/flat-chart-bg.js src/bg.js
# in src/bg.js: vec3 base = vec3(0.071, 0.078, 0.094);   (#121418)
# optionally tone the light pools down: the three smoothstep(...) * factors → 0.22 / 0.12 / 0.08
```

In `index.html`, set the hero stroke stops to `hs1 #f2b45a`, `hs2 #f5d29a` and `hs3 #8ab4f8`. Set the fill `hf1` to `#6e9cf0` at stop-opacity 0.07 and `hf2` to opacity 0. For thin text and lines to stay sharp in 2D, remove the camera `rotate()` in `main.js`. For titles in landscape, use `themes/flat-title.js`.

## Presets

`heroColor(t, …)`:
- human / focus: `'#f2b45a', '#f5d29a', '#8ab4f8'`
- system / AI: `'#8ab4f8', '#6e9cf0', '#f2b45a'`
- danger: `'#f28b82', '#f2b45a', '#f28b82'`
- solution: `'#81c995', '#8ab4f8', '#78d9c8'`

`bgTo(t, pool, accent, warm, energy)`. Keep the energy low, because the look is calm:
- calm / intro: `'#2a3f66', '#6e9cf0', '#f2b45a', 0.35`
- warning: `'#4a3418', '#e0963a', '#6e9cf0', 0.5`
- danger: `'#4a1f26', '#8c3a45', '#e0963a', 0.7–0.85`
- solution: `'#1e4a45', '#78d9c8', '#6e9cf0', 0.3`

## Alternatives to offer when asking

- **Neon glass:** the template's original look (violet, cyan and pink, glassy, high energy). Use it for Shorts that need to grab attention, or for playful topics.
- **Source-matched:** the source video's own colours in the focus-dark structure, e.g. the original NotebookLM orange `#ff9a3c` + electric blue `#5fc8ff` on navy `#0a1119`.
- **Brand match:** a named website, brand or logo (see *Brand matching* in SKILL.md).
