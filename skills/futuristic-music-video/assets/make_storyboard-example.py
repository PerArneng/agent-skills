"""WORKED EXAMPLE from "Agents in the Loop" — copy to video/tools/make_storyboard.py and adapt SECTIONS, PLAN,
LYRIC_CUES and STILL_OF to the new song. (ROOT assumes the file lives at <project>/video/tools/.)

Generate video/storyboard.json + video/storyboard.md from a compact section plan, snapped to downbeats.

  python3 video/tools/make_storyboard.py

Two ways to adjust the edit:
  1. Broad changes (re-pace a section, swap which plates a section cycles through): edit PLAN below and re-run.
  2. Single-shot tweaks (crop, flip, offset, hard cut, overlay hide/density/lyric side): edit the cut directly in
     video/storyboard.json. NOTE: re-running this script overwrites hand edits, so put lasting
     per-cut tweaks in OVERRIDES (keyed by cut start time, rounded to 0.1 s) instead.

Source shorthands in PLAN:  "v:name" → assets/video-clips/name.mp4 (falls back to the matching still if the clip
is missing), "s:name" → assets/still-images/name.png, None → code-only machine shot on the bg colour.
Entry options: bars (cut length in bars), pip, motion, crop, hflip, lyric (overlay lyric side), hide, density, cut.

Music + vocal sync (applied on top of PLAN, in this order):
  1. MUSIC EVENTS (assets/audio-analysis/drops.json from scripts/drops.py):
     drop        -> a hard cut lands exactly on it, then BURST one-bar cuts; no cut ever runs across a drop
     break       -> the shot starting there is held (>= HOLD_BREAK bars): let the vocal / the space breathe
     beat_change -> "up" (drums double / come in): cuts shorten to 1 bar until the next event;
                    "down" (half-time / drums out): pattern lengths double until the next event
  2. LYRIC CUES: the matched shot arrives WITH the phrase - the cut on screen is split at the beat nearest the
     phrase start (downbeat preferred) instead of the matched plate appearing mid-shot or a bar early.
  3. VOCAL GUARD: a plain cut should not land inside a sung word (lyrics-words.json); it moves to the nearest beat
     outside any word (within half a bar). Drop cuts are exempt - the drop wins. Long held notes and wall-to-wall
     vocals leave no free beat; those cuts stay on the downbeat (the script reports how many it moved).
  4. HIT RUNS (selected hit_run events only): the picture flicks to a new image on every hard hit (RAPID pool,
     varied crop/flip, a code-only black frame mixed in), never shorter than MIN_FLASH frames, then the
     interrupted shot resumes. These override the vocal guard; only the few selected runs get it.
The events are also written to storyboard.markers.drops so the overlay can hit the same moments.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SONG = "assets/original-music/Agents in the Loop.mp3"
TAIL = 6.0                      # seconds of end card after the music ends
beats = json.loads((ROOT / "assets/audio-analysis/beats.json").read_text())
DB = beats["downbeats"]
BAR = 60 / beats["bpm"] * 4
BEATS = beats["beats"]
_drops = ROOT / "assets/audio-analysis/drops.json"
EVENTS = json.loads(_drops.read_text())["events"] if _drops.exists() else []   # run scripts/drops.py first
_words = ROOT / "assets/audio-analysis/lyrics-words.json"
WORDS = json.loads(_words.read_text()) if _words.exists() else []
WORDS = WORDS["words"] if isinstance(WORDS, dict) else WORDS
DROP_MIN = 0.3        # drops weaker than this (0..1) don't force cuts
BURST = 2             # one-bar cuts after a drop
HOLD_BREAK = 2        # minimum bars for the shot that starts on a strong break (strength >= 0.5)
NO_EVENTS = ("shutdown", "end")   # sections where music events don't re-pace the edit
# Rapid-cut pool for hit runs: strong, readable images (performer + hook plates). None = a black code-only frame
# that the overlay's hit-run graphics play on. Repeats are fine here: it is a flicker, not a shot.
RAPID = ["v:perf-red", "v:dc-aerial", None, "v:dance-servers", "v:chip-macro", "v:perf-walk", "v:greed-cash", "v:datacenter"]
MIN_FLASH = 6         # frames; shorter than ~0.2 s reads as strobing, not as cuts
# The biggest drops (strength >= HERO_MIN) get the performer: the hardest hit of the song shows her, not a prop.
# Drop > lyric cue (sync hierarchy), so this runs after the cues. Cycles through HERO; intro/end sections exempt.
HERO_MIN = 0.6
HERO = ["v:perf-red", "v:perf-hairwhip", "v:dance-servers", "v:perf-spin"]
HERO_SKIP = ("intro",) + NO_EVENTS

# Veo plate → still it was animated from (used as fallback, and for the storyboard table).
STILL_OF = {"dance-servers": "singer-servers", "dance-desk": "singer-desk", "sing-close": "singer-close-dc",
            "sing-red": "singer-close-red", "monitors": "env-monitors", "datacenter": "env-datacenter",
            "trading": "env-trading", "penthouse": "env-penthouse", "city": "env-city", "utopia": "env-utopia",
            "perf-walk": "singer-office", "perf-red": "singer-red-dance", "perf-screens": "singer-screens",
            "perf-rooftop": "singer-rooftop", "perf-racks": "singer-racks", "workers-leave": "env-workers",
            "desk-box": "env-deskbox", "lights-off": "env-office", "bunker": "env-bunker", "mall": "env-mall",
            "factory": "env-factory", "greed-cash": "env-cash", "boardroom-toast": "env-boardroom",
            "jobless-queue": "env-queue", "foreclosure": "env-foreclosure", "dc-aerial": "env-dc-aerial",
            "chip-macro": "env-chip"}

# Song map, boundaries on downbeat indices (see beats.json). Names drive the overlay HUD and mood.
SECTIONS = [  # name, start, end
    ("intro", 0.0, DB[18]), ("verse1", DB[18], DB[34]), ("pre", DB[34], DB[44]), ("chorus1", DB[44], DB[59]),
    ("post", DB[59], DB[63]), ("verse2", DB[63], DB[80]), ("chorus2", DB[80], DB[95]), ("bridge", DB[95], DB[113]),
    ("outro", DB[113], 216.642), ("shutdown", 216.642, DB[127]), ("end", DB[127], None),
]

L, R, C = {"lyric": "left"}, {"lyric": "right"}, {"lyric": "center"}
# Each section cycles through its pattern until the section is filled. bars = cut length in downbeats.
# Base edit per section: the singer performing (never singing — Veo can't lip-sync) alternating with
# machine shots. LYRIC_CUES below then swap in scenes that match the words being sung.
PLAN = {
    "intro": [
        dict(src=None, bars=1),
        dict(src="v:dc-aerial", bars=2),
        dict(src="v:monitors", bars=2, pip=True, pip_side="right"),
        dict(src="s:env-office", bars=2, motion="drift-left"),
        dict(src="v:chip-macro", bars=1),
        dict(src="v:datacenter", bars=2),
        dict(src="v:perf-screens", bars=2, lyric="right"),                 # title card 19.5–27.5
        dict(src="v:perf-racks", bars=2),
        dict(src="v:dance-servers", bars=1, cut=True), dict(src="v:monitors", bars=1, crop=1.25),
        dict(src="v:perf-red", bars=1, crop=1.05), dict(src="v:datacenter", bars=1, hflip=True),
    ],
    "verse1": [
        dict(src="v:perf-walk", bars=2, cut=True, **R), dict(src="v:monitors", bars=1, pip=True),
        dict(src="v:perf-racks", bars=2, **R), dict(src=None, bars=1),
        dict(src="v:dance-desk", bars=2), dict(src="v:datacenter", bars=1, pip=True),
    ],
    "pre": [
        dict(src="v:perf-red", bars=1, crop=1.05, **R), dict(src="v:chip-macro", bars=1),
        dict(src="v:dance-servers", bars=1), dict(src=None, bars=1),
        dict(src="v:perf-walk", bars=1, hflip=True, **R), dict(src="v:dance-desk", bars=1),
    ],
    "chorus1": [
        dict(src="v:dance-servers", bars=2, cut=True), dict(src="v:dc-aerial", bars=1),
        dict(src="v:dance-desk", bars=2), dict(src="v:greed-cash", bars=1),
        dict(src="v:perf-red", bars=1, crop=1.05), dict(src="v:factory", bars=1),
        dict(src="v:perf-rooftop", bars=2), dict(src="v:monitors", bars=1),
    ],
    "post": [
        dict(src="v:dance-desk", bars=1, crop=1.3, cut=True, **C), dict(src=None, bars=1, **C),
        dict(src="v:dance-servers", bars=1, crop=1.35, **C), dict(src="v:perf-red", bars=1, crop=1.3, **C),
    ],
    "verse2": [
        dict(src="v:bunker", bars=2, cut=True), dict(src="v:penthouse", bars=1, **R),
        dict(src="v:city", bars=2), dict(src="v:perf-red", bars=2, crop=1.05, **R),
        dict(src="v:boardroom-toast", bars=1), dict(src=None, bars=1),
        dict(src="v:perf-walk", bars=1, crop=1.2, **R), dict(src="v:trading", bars=2),
        dict(src="v:dance-servers", bars=1, crop=1.2, **R),
    ],
    "chorus2": [
        dict(src="v:perf-red", bars=2, cut=True, crop=1.1, **R), dict(src="v:dance-desk", bars=1, crop=1.2),
        dict(src="v:perf-walk", bars=1, crop=1.15), dict(src="v:dance-servers", bars=2, crop=1.25),
        dict(src="v:perf-rooftop", bars=1, crop=1.2), dict(src="v:datacenter", bars=1, hflip=True),
        dict(src="v:dance-desk", bars=2, hflip=True, crop=1.1), dict(src="v:perf-racks", bars=1, crop=1.2),
    ],
    "bridge": [   # one slow idea: the rooftop, the dying city, the lights going out
        dict(src="v:perf-rooftop", bars=3, cut=True, **L),
        dict(src="v:foreclosure", bars=2), dict(src="v:perf-walk", bars=2, **R),
        dict(src="v:lights-off", bars=2), dict(src=None, bars=2),
        dict(src="v:perf-screens", bars=2), dict(src="v:dc-aerial", bars=2),
        dict(src="v:perf-rooftop", bars=3, crop=1.2, hflip=True, **L),
    ],
    "outro": [
        dict(src="v:chip-macro", bars=1, cut=True), dict(src=None, bars=1),
        dict(src="v:datacenter", bars=2), dict(src="v:perf-racks", bars=2, **L),
        dict(src="v:dance-servers", bars=1, crop=1.3), dict(src=None, bars=1),
    ],
    "shutdown": [dict(src=None, bars=99)],
    "end": [dict(src="v:utopia", bars=4, cut=True), dict(src="s:env-utopia", bars=99, motion="kenburns-in")],
}

# Lyric-matched scenes: the cut that is on screen when this phrase is sung shows this plate.
# Keys are phrase text from assets/overlay/lyrics.json (prefix match, '#2' = 2nd occurrence), so they follow
# the lyric timing automatically. Value: a source shorthand, optionally with extra cut fields.
LYRIC_CUES = {
    "Silent server rooms": "v:datacenter",
    "Replacing the passion": "v:desk-box",
    "No coffee breaks": "v:monitors",
    "A million white-collar": "v:workers-leave",
    "LLMs locked": "v:chip-macro",
    "Parsing the ledger": "v:monitors",
    "A thirty-year career": "v:desk-box",
    "An algorithm turning": "v:trading",
    "with the zero-cost mind": "v:chip-macro",
    "leaving humans behind": "v:workers-leave",
    "Digital speed": "v:dc-aerial",
    "The market goes": "v:penthouse",
    "Agents in the loop": "v:dc-aerial",
    "Optimizing profit": "v:greed-cash",
    "No jobs for the mind": "v:factory",
    "The spiral begins": "v:jobless-queue",
    "across the whole land": "v:foreclosure",
    "profit over man": "v:boardroom-toast",
    "Economic collapse": "v:trading",
    "Bunker doors sealing": "v:bunker",
    "Billionaires hiding": "v:penthouse",
    "street groans": "v:city",
    "Civil unrest": "v:city",
    "Deep integration": "v:datacenter",
    "Watching the middle": "v:jobless-queue",
    "Automated trades": "v:trading",
    "Nobody left who can shop": "v:mall",
    "Agents in the loop#3": "v:perf-screens",
    "Optimizing profit#2": "v:boardroom-toast",
    "No jobs for the mind#2": "v:factory",
    "across the whole land#2": "v:foreclosure",
    "profit over man#2": "v:greed-cash",
    "Economic collapse#2": "v:city",
    "Who buys the product": "v:mall",
    "The death spiral": "v:lights-off",
    "No human advantage": "v:factory",
    "The transition is finished": "v:perf-screens",
    "The agents have won": "v:dc-aerial",
    "Hyper-automation": "v:chip-macro",
}
# Per-cut hand tweaks that survive regeneration. Key: cut start rounded to 0.1 s. Values merge into the cut.
OVERRIDES: dict[float, dict] = {}


def resolve(src):
    if not src:
        return None, False
    kind, name = src.split(":", 1)
    if kind == "v":
        p = f"assets/video-clips/{name}.mp4"
        fast = f"assets/video-clips/{name}-fast.mp4"          # polish upgrade wins when present
        if (ROOT / fast).exists():
            return fast, True
        if (ROOT / p).exists():
            return p, True
        return f"assets/still-images/{STILL_OF[name]}.png", False
    return f"assets/still-images/{name}.png", False


_LEN = {}
def clip_len(src):
    """duration of a video plate in seconds (ffprobe, cached)"""
    if src not in _LEN:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ROOT / src)],
                           capture_output=True, text=True)
        _LEN[src] = float(r.stdout.strip() or 8.0)
    return _LEN[src]


def near(t, arr, win):
    """closest value in arr within win seconds of t, else None"""
    best = min(arr, key=lambda x: abs(x - t), default=None)
    return best if best is not None and abs(best - t) <= win else None


def in_word(t, pad=0.05):
    return any(w["start"] + pad < t < w.get("end", w["start"]) - pad for w in WORDS)


def rapid_cuts(cuts, runs, fps=30):
    """Split the edit at every hit of each run; each piece shows the next RAPID image. Mutates cuts in place."""
    n = 0
    for r in runs:
        hits = list(r["hits"])
        step = max(1, -(-MIN_FLASH // max(1, round(r["spacing"] * fps))))   # skip hits that come too fast
        hits = hits[::step]
        end = hits[-1] + r["spacing"] * step
        host = next((c for c in cuts if c["start"] <= hits[0] < c["end"]), None)
        if host is None or host["section"] in NO_EVENTS:
            continue
        i = cuts.index(host)
        tail = next((c for c in cuts if c["start"] <= end < c["end"]), None)
        new = []
        if hits[0] - host["start"] >= MIN_FLASH / fps:
            new.append({**host, "end": round(hits[0], 3)})
        elif i > 0:                                  # a sliver before the first hit joins the previous shot
            cuts[i - 1]["end"] = round(hits[0], 3)
        around = {host["source"], tail["source"] if tail else None}
        pool = [x for x in RAPID if x is None or resolve(x)[0] not in around] or RAPID   # flashes differ from the shots around them
        for k, h in enumerate(hits):
            e = hits[k + 1] if k + 1 < len(hits) else end
            src, is_video = resolve(pool[(n + k) % len(pool)])
            fl = {"start": round(h, 3), "end": round(e, 3), "section": host["section"], "source": src,
                  "layer": "plate" if src else "machine", "veo": bool(is_video), "transition": "cut", "flash": True,
                  "crop": [1.0, 1.25, 1.1, 1.4][k % 4], "hflip": k % 2 == 1}
            if src and not is_video:
                fl["motion"] = "static"
            new.append(fl)
        j = cuts.index(tail) if tail else i
        if tail and tail["end"] - end >= MIN_FLASH / fps:
            new.append({**tail, "start": round(end, 3), "transition": "cut"})
        elif tail:                                   # a sliver after the run joins the last flash
            new[-1]["end"] = tail["end"]
        cuts[i:j + 1] = new
        n += len(hits)
    return n


def main():
    total = beats["duration"] + TAIL
    drops = sorted(e["t"] for e in EVENTS if e["kind"] == "drop" and e["strength"] >= DROP_MIN)
    breaks = sorted(e["t"] for e in EVENTS if e["kind"] == "break" and e["strength"] >= 0.5)
    grooves = sorted((e["t"], e["dir"]) for e in EVENTS if e["kind"] == "beat_change")
    cuts, use = [], {}
    for name, s0, s1 in SECTIONS:
        s1 = total if s1 is None else s1
        pat, k, t, burst = PLAN[name], 0, s0, 0
        react = name not in NO_EVENTS
        while t < s1 - 0.05:
            e = pat[k % len(pat)]; k += 1
            on_drop = react and near(t, drops, 0.08) is not None
            if on_drop:
                burst = BURST + 1
            g = [d for tt, d in grooves if tt <= t + 0.08]
            pace = {"up": 0.5, "down": 2.0}.get(g[-1], 1.0) if g and react else 1.0
            bars = 1 if burst > 0 else max(1, round(e["bars"] * pace))
            if react and near(t, breaks, 0.08) is not None:
                bars = max(bars, HOLD_BREAK)
            burst = max(0, burst - 1)
            # end on the downbeat `bars` later (or extrapolate past the last downbeat)
            later = [d for d in DB if d > t + 0.2]
            end = later[bars - 1] if len(later) >= bars else t + bars * BAR
            nxt = [d for d in drops if t + 0.2 < d < end] if react else []
            if nxt:                            # never run across a drop: the drop gets its own cut
                end = nxt[0]
            end = min(end, s1)
            if s1 - end < BAR * 0.6:          # don't leave a sliver at the section end
                end = s1
            src, is_video = resolve(e.get("src"))
            cut = {"start": round(t, 3), "end": round(end, 3), "section": name,
                   "layer": "plate" if src and not e.get("pip") else "machine", "source": src,
                   "veo": bool(is_video)}
            if is_video:
                n = use.get(src, 0); use[src] = n + 1
                cut["offset"] = round((n * 2.3) % 4.0, 2)      # vary the slice of a reused plate
            elif src:
                cut["motion"] = e.get("motion", "kenburns-in")
            for f in ("pip", "pip_side", "crop", "hflip"):
                if f in e: cut[f] = e[f]
            if e.get("cut") or on_drop: cut["transition"] = "cut"
            if on_drop: cut["drop"] = True
            ov = {f: e[f] for f in ("lyric", "hide", "density", "only") if f in e}
            if ov: cut["overlay"] = ov
            cut.update(OVERRIDES.get(round(t, 1), {}))
            cuts.append(cut)
            t = end
    # lyric cues: the matched shot arrives with the phrase. Split the cut on screen at the beat nearest the
    # phrase start (downbeat preferred) when that leaves both halves >= half a bar; else swap the whole cut.
    lyr = json.loads((ROOT / "assets/overlay/lyrics.json").read_text())
    def phrase_t(spec):
        txt, n = (spec.split("#") + ["1"])[:2]
        hits = [p for p in lyr if p["text"].lower().startswith(txt.lower())]
        return hits[int(n) - 1]["t"] if len(hits) >= int(n) else None
    for spec, src in LYRIC_CUES.items():
        t0 = phrase_t(spec)
        if t0 is None:
            print(f"  cue not found: {spec}"); continue
        i = next((i for i, c in enumerate(cuts) if c["start"] <= t0 + 0.15 < c["end"]), None)
        if i is None or cuts[i]["section"] in NO_EVENTS:
            continue
        c = cuts[i]
        path, is_video = resolve(src)
        if c["source"] == path:                # already showing it
            continue
        at = near(t0, DB, 0.25) or near(t0, BEATS, 0.15)
        if at and at - c["start"] >= BAR / 2 and c["end"] - at >= BAR / 2:
            tail = {**c, "start": round(at, 3), "transition": "cut"}    # hard cut on the vocal
            tail.pop("drop", None)
            c["end"] = round(at, 3)
            cuts.insert(i + 1, tail)
            c = tail
        c.update(source=path, veo=bool(is_video), layer="plate")
        for f in ("pip", "pip_side", "motion"):
            c.pop(f, None)
        if not is_video:
            c["motion"] = "kenburns-in"
        c.setdefault("overlay", {}).pop("lyric", None)
        if not c["overlay"]:
            del c["overlay"]
    # a cue can turn a neighbour into the same plate: merge those (same section, not across a drop)
    merged = [cuts[0]]
    for c in cuts[1:]:
        p = merged[-1]
        if c["source"] and c["source"] == p["source"] and c["section"] == p["section"] and not c.get("drop"):
            p["end"] = c["end"]
        else:
            merged.append(c)
    cuts[:] = merged
    # vocal guard: move a plain cut that lands inside a sung word to the nearest beat outside any word
    moved = 0
    for a_, b_ in zip(cuts, cuts[1:]):
        x = b_["start"]
        if b_.get("drop") or not in_word(x):
            continue
        cand = [bt for bt in BEATS if abs(bt - x) <= BAR / 2 and not in_word(bt)
                and bt - a_["start"] > BAR / 2 and b_["end"] - bt > BAR / 2]
        if cand:
            nb = round(min(cand, key=lambda bt: abs(bt - x)), 3)
            a_["end"] = b_["start"] = nb; moved += 1
    if moved:
        print(f"vocal guard: moved {moved} cut(s) off sung words")
    # hero shots on the biggest drops
    big = [e["t"] for e in EVENTS if e["kind"] == "drop" and e["strength"] >= HERO_MIN]
    hero_n = 0
    for c in cuts:
        if c.get("drop") and c["section"] not in HERO_SKIP and near(c["start"], big, 0.08) is not None:
            src, is_video = resolve(HERO[hero_n % len(HERO)]); hero_n += 1
            c.update(source=src, veo=is_video, layer="plate")
            if not is_video:
                c["motion"] = "kenburns-in"
            c.pop("pip", None)
    if hero_n:
        print(f"hero drops: {hero_n} cut(s) on the biggest drops show the performer")
    # hit runs: a new image on every hard hit, then the interrupted shot resumes
    n_flash = rapid_cuts(cuts, [e for e in EVENTS if e["kind"] == "hit_run" and e.get("selected")])
    if n_flash:
        print(f"hit runs: {n_flash} rapid cuts")
    # varied slices of reused clips
    use = {}
    for c in cuts:
        if c["veo"]:
            n = use.get(c["source"], 0); use[c["source"]] = n + 1
            # never loop back to the clip start mid-shot (trimmed clips are shorter than 8 s)
            room = max(0.0, clip_len(c["source"]) - (c["end"] - c["start"]) - 0.05)
            c["offset"] = round(min((n * 2.3) % 4.0, room), 2)
    counts = {}
    for c in cuts:
        if c["source"]:
            k = c["source"].split("/")[-1]; counts[k] = counts.get(k, 0) + 1
    print("plate usage:", ", ".join(f"{k.rsplit('.', 1)[0]}×{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
    sb = {"song": SONG, "fps": 30, "width": 3840, "height": 2160, "tail": TAIL,
          "overlay_frames": "assets/overlay/frames", "dissolve_frames": 5, "grade": "default",
          "markers": {"shutdown": 216.642, "end_card": DB[127],
                      "drops": [{k: e[k] for k in ("t", "kind", "strength", "dir", "into", "end", "hits", "spacing", "selected") if k in e} for e in EVENTS]},
          "song_map": [{"name": n, "start": round(a, 3), "end": round(total if b is None else b, 3)} for n, a, b in SECTIONS],
          "cuts": cuts}
    (ROOT / "video/storyboard.json").write_text(json.dumps(sb, indent=1))
    plates = sorted({c["source"] for c in cuts if c["veo"]})
    rows = [f"# Storyboard — Agents in the Loop\n",
            f"{len(cuts)} cuts · {sum(1 for c in cuts if c.get('drop'))} on drops · {len(plates)} Veo plates reused across "
            f"{sum(c['veo'] for c in cuts)} cuts · 4K master 3840x2160 · end card tail {TAIL}s\n",
            "| # | start | end | section | layer | source | crop/flip | lyric | music |", "|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(cuts):
        rows.append(f"| {i} | {c['start']:.2f} | {c['end']:.2f} | {c['section']} | {c['layer']}{' pip' if c.get('pip') else ''} | "
                    f"{(c['source'] or '—').split('/')[-1]} | {c.get('crop', '')}{' flip' if c.get('hflip') else ''} | "
                    f"{c.get('overlay', {}).get('lyric', '')} | {'DROP' if c.get('drop') else ''} |")
    (ROOT / "video/storyboard.md").write_text("\n".join(rows) + "\n")
    print(f"wrote video/storyboard.json ({len(cuts)} cuts, {len(plates)} video plates in use)")


if __name__ == "__main__":
    main()
