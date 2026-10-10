"""Storyboard generator for "Compile the Future" (adapted from the skill's make_storyboard-example.py).

  python3 video/tools/make_storyboard.py

One source of truth for the edit AND the plates. Writes:
  video/storyboard.json   cut list for assemble.py (downbeat-snapped, drops/hit runs/lyric cues/vocal guard applied)
  video/storyboard.md     human-readable board (chapter, lyric, type mode, plate, camera, motion source)
  video/storyboard.html   the same board as a dark-mode review page
  video/stills.json       still manifest: name -> {prompt, refs}   (prompts in video/prompts/<name>.txt)
  video/plates.json       Veo manifest for veo_batch.py: name -> {image, prompt}  (video/prompts/<name>-motion.txt)

Adjust: PLATES (what each picture is), PLAN (section patterns), LYRIC_CUES (phrase -> plate), HERO_AT (drop -> plate).
Per-cut hand tweaks go in OVERRIDES (keyed by cut start rounded to 0.1 s) so they survive regeneration.
Source shorthand: "v:name" = Veo plate (falls back to its still), "s:name" = still only (Ken Burns), None = code-only.
"""
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SONG = "assets/original-music/Compile the Future.mp3"
TAIL = 12.0          # 297.1 end card, then the Ethical Acceleration section on the dawn plate
beats = json.loads((ROOT / "assets/audio-analysis/beats.json").read_text())
DB, BEATS = beats["downbeats"], beats["beats"]
BAR = 60 / beats["bpm"] * 4
EVENTS = json.loads((ROOT / "assets/audio-analysis/drops.json").read_text())["events"]
# Hand-marked: the final chorus is weak in the detector (the bass never leaves) but it is the song's climax.
EXTRA_DROPS = [{"t": DB[140], "kind": "drop", "strength": 0.8, "manual": True}]
EVENTS = sorted(EVENTS + EXTRA_DROPS, key=lambda e: e["t"])
WORDS = json.loads((ROOT / "assets/audio-analysis/lyrics-words.json").read_text())
LYR = json.loads((ROOT / "assets/overlay/lyrics.json").read_text())
DROP_MIN, BURST, HOLD_BREAK, MIN_FLASH, GROOVE_MIN = 0.3, 2, 2, 6, 0.9
NO_EVENTS = ()

# ------------------------------------------------------------------------------------------------------------------
# PEOPLE + STYLE come from the locked casting and the bible
CAST = {p["id"]: p for g in json.loads((ROOT / "assets/casting/casting.json").read_text())["groups"] for p in g["people"]}
WHO = {"coder": "lead-d", "architect": "crew-architect", "orchestrator": "crew-orchestrator",
       "principal": "crew-principal", "fixer": "crew-fixer"}
LABEL = {"coder": "THE CODER", "architect": "THE ARCHITECT", "orchestrator": "THE ORCHESTRATOR",
         "principal": "THE PRINCIPAL", "fixer": "THE FIXER"}
bible = (ROOT / "video/bible.md").read_text()
STYLE = " ".join(re.search(r"Style words \(appended verbatim to every image prompt\):\n(.*?)\nWorld:", bible, re.S)
                 .group(1).split())
BAN = ("Mouths closed — nobody sings or talks. Anatomically correct hands. No readable text, letters, numbers, signs "
       "or logos anywhere. No new characters beyond those described.")

# ------------------------------------------------------------------------------------------------------------------
# PLATES: every picture in the video. veo=True -> an 8 s Veo clip animated from the still; False -> still only.
# scene: the picture; space: the declared empty area for type; camera+motion: the Veo prompt (one camera move,
# one moving part). desc: one line for the board.
P = dict
PLATES = {
    # --- the Coder ---------------------------------------------------------------------------------------------
    "c-desk": P(who=["coder"], veo=True, desc="Coder at his desk, 3 a.m., three monitors",
        scene="He sits at his desk in his dark high-rise apartment at 3 a.m., leaning in toward three glowing monitors "
              "of abstract code, fingers on a mechanical keyboard, an empty coffee mug and tangled cables; floor-to-"
              "ceiling glass behind him shows the city lights far below. Medium shot from the side at desk height.",
        space="the left third is dark wall (empty for type)", camera="slow push in",
        motion="he types steadily with a slight rhythmic head nod; scrolling code light moves across his face and lens"),
    "c-lens": P(who=["coder"], veo=True, desc="HOOK: one cyan cursor reflected in the rainbow lens",
        scene="Extreme close-up of his face in three-quarter view, the shield sunglasses filling the frame: the rainbow "
              "lens reflects a single glowing cyan cursor block from a dark screen. Everything else falls to black.",
        space="the right third is black (empty for type)", camera="very slow push in",
        motion="the reflected cyan text-cursor block (a solid vertical rectangle) blinks steadily in the lens and a faint "
               "shimmer moves across the rainbow coating; he stays still. No mouse pointer, no arrow, no hand icon, "
               "no new shapes appear in the lens"),
    "c-walk": P(who=["coder"], veo=True, desc="Coder walks toward camera through the apartment",
        scene="He walks toward camera through his dark apartment past the glowing desk, city lights through the glass "
              "behind him, hands in his jacket pockets. Medium-wide, eye level.",
        space="the upper third is emptier", camera="slow dolly back as he walks toward camera",
        motion="his loose jacket and baggy trousers sway with each step"),
    "c-window": P(who=["coder"], veo=True, desc="Coder at the window, back to camera, city below",
        scene="He stands at the floor-to-ceiling window with his back to camera, a dark silhouette against the city "
              "lights far below, the three monitors glowing cyan and magenta behind him. Wide shot.",
        space="the top half is night sky", camera="slow lateral track right",
        motion="the city lights twinkle and the monitor glow pulses softly on his back"),
    "c-conduct": P(who=["coder"], veo=True, desc="Coder conducts: agent light streams branch out of his monitors",
        scene="He stands at his desk with both arms raised like a conductor; dozens of glowing cyan and magenta agent "
              "windows and light streams branch out of his three monitors into the dark room around him. Low angle, wide.",
        space="the upper corners are dark", camera="slow push in from a low angle",
        motion="he sweeps his hands slowly and the light streams branch and flow outward, following his hands"),
    "c-hood": P(who=["coder"], veo=True, desc="Coder pulls the hood up, turns to camera (drop hero)",
        scene="Low-angle close-up as he pulls his hood up over his head and turns toward camera, monitor light on the "
              "rainbow lens, the dark apartment behind him. Intense, determined.",
        space="the left third is dark", camera="static, low angle",
        motion="he pulls the hood up and turns his head to camera in one smooth move"),
    "c-dance": P(who=["coder"], veo=True, desc="Coder dances alone in the monitor light (hip-hop groove)",
        scene="He dances alone in the middle of his dark apartment lit only by the three glowing monitors, mid-step in a "
              "loose hip-hop move, baggy cargo trousers swinging, city lights behind. Full body, wide.",
        space="the upper third is emptier", camera="slow 15-degree orbit right",
        motion="he dances a relaxed hip-hop groove: shoulder bounce, step and turn, loose arms"),
    # --- the crew ----------------------------------------------------------------------------------------------
    "a-wall": P(who=["architect"], veo=True, desc="Architect conducts the branching agent tree",
        scene="He stands at a huge curved wall of screens in a dark ops room, both arms raised conducting; dozens of "
              "small glowing agent windows branch out from his hands like a tree of cyan and magenta light. Low angle.",
        space="the top-left corner is dark", camera="slow push in",
        motion="new branches of light grow outward from his hands as he spreads his arms"),
    "o-lanes": P(who=["orchestrator"], veo=True, desc="Orchestrator runs parallel lanes of light",
        scene="She stands at the curved wall of screens in the dark ops room, one hand sweeping sideways, parallel lanes "
              "of magenta and cyan light streaming between many small agent windows. Three-quarter view from behind her shoulder.",
        space="the right third is darker", camera="slow lateral track left",
        motion="she sweeps her hand and the parallel light lanes stream faster across the wall; her braid swings"),
    "ao-duo": P(who=["architect", "orchestrator"], veo=True, desc="Architect + Orchestrator: agent to agent",
        scene="The two of them stand side by side at the curved wall of screens, arms raised, dozens of glowing agent "
              "windows branching between their hands and connecting in parallel streams of light. Wide, low angle.",
        space="the top third is dark", camera="slow push in",
        motion="they move their hands like conductors and the windows connect and branch between them"),
    "p-aisle": P(who=["principal"], veo=True, desc="Principal strides into the smoking data center",
        scene="He strides toward camera down a narrow smoky data-center aisle between towering server racks, calm and "
              "focused, scanning the racks; smoke billows, amber warning lights strobe, cyan LEDs everywhere. "
              "Extreme one-point perspective.",
        space="the top third is smoke", camera="slow dolly back, keeping pace with him",
        motion="smoke rolls past him and the amber strobes flash; he keeps walking steadily"),
    "p-trace": P(who=["principal"], veo=False, desc="Principal reads every trace (close-up)",
        scene="Close-up of him reading a rack-mounted screen of abstract cyan code lines, the code reflected in his eyes, "
              "smoke drifting behind him in a dark data-center aisle.",
        space="the right third is dark smoke"),
    "f-rack": P(who=["fixer"], veo=True, desc="Fixer kneels at a failing rack, tablet glowing",
        scene="She kneels at an open server rack in a smoky data-center aisle, the handheld tablet's cyan glow on her "
              "face, an amber warning light strobing behind her, haze curling around her. Medium shot.",
        space="the upper left is dark", camera="slow push in",
        motion="she swipes on the tablet while rack LEDs blink and the amber light strobes; haze drifts"),
    "pf-smoke": P(who=["principal", "fixer"], veo=True, desc="Principal + Fixer push through thick smoke",
        scene="The two of them move fast through thick smoke in the data center under strobing amber warning lights; "
              "she holds the glowing tablet, he points ahead down the aisle. Medium-wide.",
        space="the top third is smoke", camera="slow dolly back",
        motion="they walk fast toward camera through rolling smoke; the amber lights strobe"),
    "crew-all": P(who=["coder", "architect", "orchestrator"], veo=True,
        desc="The whole system: Coder with the crew at the screen wall, all lanes converge",
        scene="He stands in the middle of the dark ops room with the crew around him, all facing the curved screen "
              "wall where hundreds of agent lanes of cyan and magenta light converge into one bright point. "
              "Wide shot from behind and to the side. Two more crew members stand further back in shadow.",
        space="the top third is dark", camera="slow push in toward the bright point",
        motion="the light lanes flow and converge into the single bright point; nobody moves much"),
    # --- the world ---------------------------------------------------------------------------------------------
    "e-city": P(who=[], veo=True, desc="The city at night from above",
        scene="Aerial view of a dense city at night: thousands of lit windows in grey and white, a few windows glowing "
              "with cyan and magenta screen light, a river of moving lights. No people.",
        space="the top half is night sky", camera="slow aerial drift forward", motion="traffic lights stream along the avenues"),
    "e-city-lit": P(who=[], veo=True, desc="PAYOFF: every window lit in screen colour — a whole world in motion",
        scene="The same dense city at night from above, but now every single window glows with screen light in cyan, "
              "magenta and amber, as if everyone is building at once. Breathtaking, no people.",
        space="the top half is night sky", camera="slow aerial push in", motion="windows flicker on in waves across the city"),
    "e-dawn": P(who=[], veo=True, colour=True, refs=["assets/still-images/e-city-lit.jpg"],
        desc="ENDING: dawn over the same city, real colour returns (Ethical Acceleration)",
        scene="The same dense city seen from above at the very first minute of sunrise: a soft golden sun just clearing the "
              "horizon, warm peach and pale blue sky, gentle morning haze between the towers, river glinting gold, a few "
              "windows still glowing faint cyan from the night. Hopeful, calm, open. No people.",
        space="the upper-left third is open sky (empty for type)", camera="very slow aerial push in",
        motion="the sun rises a little and warm light spreads across the rooftops; haze drifts slowly"),
    "e-dc-ext": P(who=[], veo=True, desc="The data center smokes (exterior)",
        scene="A massive data-center building at night at the edge of the city, white smoke and steam billowing from its "
              "cooling towers, lit amber by warning lights, rows of tiny cyan LEDs along the walls. Wide, low angle.",
        space="the top third is smoke and sky", camera="slow push in", motion="the smoke billows upward and the amber lights pulse"),
    "e-dc-aisle": P(who=[], veo=True, desc="Empty smoking aisle, amber strobes",
        scene="An empty data-center aisle with racks at full load, thick smoke rolling along the floor, amber warning "
              "strobes, blinking cyan LEDs. Extreme one-point perspective.",
        space="the top third is smoke", camera="slow dolly forward", motion="smoke rolls toward camera and the strobes flash"),
    "e-leds": P(who=[], veo=True, desc="Macro: blinking rack LEDs, smoke curling",
        scene="Macro close-up of a server rack front: rows of blinking cyan and magenta status LEDs, a thin curl of "
              "smoke drifting across, black metal mesh. Shallow depth of field.",
        space="the left third is out-of-focus black", camera="very slow lateral track", motion="the LEDs blink in fast patterns and the smoke drifts"),
    "e-tree": P(who=[], veo=True, desc="Abstract: hundreds of agent windows branching like a tree",
        scene="A vast dark space filled with hundreds of small glowing agent windows connected by streams of cyan and "
              "magenta light, branching outward like a tree from one bright point. No people.",
        space="the corners are dark", camera="slow push in", motion="the tree grows new branches outward from the bright point"),
    "e-screen": P(who=[], veo=False, desc="Macro: a dark screen, one blinking cyan cursor",
        scene="Macro of a dark monitor in a dark room: a single glowing cyan cursor block and a few faint abstract lines "
              "of code. Silver dust on the glass.", space="most of the frame is empty dark screen"),
    "e-clock": P(who=[], veo=False, desc="The clock goes soft beyond the glass",
        scene="A minimal analog wall clock with no numerals, hands at three o'clock, seen soft and out of focus through "
              "a glass partition, city light bokeh around it, monitor glow on the glass.", space="the right half is soft bokeh"),
    "e-keys": P(who=["coder"], veo=False, desc="Macro: his hands on the keyboard",
        scene="Macro of his hands typing on a mechanical keyboard, the keys edge-lit by cyan monitor glow, the cuff of "
              "his khaki field jacket visible.", space="the top third is dark", hands_only=True),
    "e-mug": P(who=[], veo=False, desc="Cold coffee by the keyboard, 3 a.m.",
        scene="An empty coffee mug and a tangle of cables beside a mechanical keyboard, lit by cyan and magenta monitor "
              "glow, the city out of focus beyond the glass.", space="the left third is dark"),
}

# ------------------------------------------------------------------------------------------------------------------
# Song map on the downbeat grid, plus the story chapters on top of it.
SECTIONS = [  # name, start, end, chapter
    ("intro", 0.0, DB[16], "1 · Boot — one cursor in a quiet room"),
    ("verse1", DB[16], DB[24], "2 · One line — little minds awake"),
    ("pre1", DB[24], DB[32], "3 · Branching — agent to agent"),
    ("chorus1", DB[32], DB[49], "4 · Ship it — think fast, build clean"),
    ("drop1", DB[49], DB[64], "5 · Overdrive — the data center smokes"),
    ("inter1", DB[64], DB[72], "5 · Overdrive — the data center smokes"),
    ("verse2", DB[72], DB[88], "6 · The grind — run the suite, read every trace"),
    ("pre2", DB[88], DB[96], "7 · Under fire"),
    ("chorus2", DB[96], DB[116], "7 · Under fire"),
    ("breakdown", DB[116], DB[125], "8 · Convergence — one final green check"),
    ("build", DB[125], DB[140], "8 · Convergence — compile the dream"),
    ("final", DB[140], DB[156], "9 · Live — compiling the future in real time"),
    ("tag", DB[156], DB[174], "9 · Live — we come alive"),
    ("outro", DB[174], DB[181], "10 · A whole world in motion"),
    ("end", DB[181], None, "10 · A whole world in motion"),
]
CHAPTER = {s[0]: s[3] for s in SECTIONS}

PLAN = {
    "intro": [P(src=None, bars=1), P(src="s:e-screen", bars=2), P(src="v:c-lens", bars=3), P(src="v:e-city", bars=3),
              P(src="v:c-window", bars=2), P(src="v:c-desk", bars=2, cut=True)],
    "verse1": [P(src="v:c-desk", bars=2), P(src="s:e-keys", bars=1), P(src="s:e-clock", bars=1),
               P(src="v:c-lens", bars=1, crop=1.3), P(src="v:e-tree", bars=2), P(src="s:e-mug", bars=1)],
    "pre1": [P(src="v:ao-duo", bars=1), P(src="v:o-lanes", bars=1), P(src="v:a-wall", bars=1), P(src="v:e-tree", bars=1, crop=1.25),
             P(src="v:f-rack", bars=1), P(src="v:e-leds", bars=1), P(src="v:c-conduct", bars=1), P(src=None, bars=1)],
    "chorus1": [P(src="v:c-conduct", bars=2, cut=True), P(src="v:e-city", bars=1), P(src="v:c-walk", bars=2),
                P(src="v:ao-duo", bars=1), P(src="v:c-dance", bars=2), P(src="v:e-dc-ext", bars=1),
                P(src="v:c-desk", bars=1, crop=1.2), P(src="v:a-wall", bars=1), P(src="v:c-hood", bars=2), P(src="v:o-lanes", bars=1)],
    "drop1": [P(src="v:c-hood", bars=1, cut=True), P(src="v:e-dc-ext", bars=1), P(src="v:pf-smoke", bars=1), P(src="v:e-leds", bars=1),
              P(src="v:c-dance", bars=1), P(src=None, bars=1), P(src="v:p-aisle", bars=1), P(src="v:e-dc-aisle", bars=1), P(src="v:f-rack", bars=1)],
    "inter1": [P(src="v:c-dance", bars=2, cut=True, crop=1.15), P(src="v:e-city", bars=2, hflip=True), P(src="v:c-walk", bars=2, crop=1.2),
               P(src="v:e-tree", bars=2, hflip=True)],
    "verse2": [P(src="v:a-wall", bars=2), P(src="s:p-trace", bars=1), P(src="v:c-desk", bars=2, hflip=True), P(src="v:e-dc-aisle", bars=1),
               P(src="v:o-lanes", bars=2), P(src="s:e-keys", bars=1), P(src="v:p-aisle", bars=2), P(src="v:e-tree", bars=1)],
    "pre2": [P(src="v:ao-duo", bars=1, crop=1.2), P(src="v:o-lanes", bars=1, hflip=True), P(src="v:a-wall", bars=1, crop=1.2),
             P(src="v:e-leds", bars=1, hflip=True), P(src="v:f-rack", bars=1, crop=1.2), P(src="v:e-dc-aisle", bars=1),
             P(src="v:c-conduct", bars=1, crop=1.2), P(src=None, bars=1)],
    "chorus2": [P(src="v:c-conduct", bars=2, cut=True, crop=1.15), P(src="v:e-dc-ext", bars=1, crop=1.2), P(src="v:c-dance", bars=2, hflip=True),
                P(src="v:pf-smoke", bars=1), P(src="v:c-walk", bars=2, crop=1.2), P(src="v:e-leds", bars=1),
                P(src="v:ao-duo", bars=1, hflip=True), P(src="v:c-hood", bars=2, crop=1.15), P(src="v:p-aisle", bars=1, crop=1.2)],
    "breakdown": [P(src="v:c-window", bars=3, cut=True), P(src="v:crew-all", bars=3), P(src="v:e-tree", bars=2, crop=1.3), P(src="v:c-lens", bars=2)],
    "build": [P(src="v:f-rack", bars=1, hflip=True), P(src="s:p-trace", bars=1), P(src="v:c-lens", bars=1, crop=1.4), P(src="v:e-city", bars=1, crop=1.3),
              P(src="v:e-leds", bars=1), P(src="v:c-hood", bars=1, crop=1.3), P(src=None, bars=1), P(src="v:e-dc-aisle", bars=1, hflip=True)],
    "final": [P(src="v:c-conduct", bars=2, cut=True, crop=1.1), P(src="v:crew-all", bars=1), P(src="v:c-dance", bars=2),
              P(src="v:e-city-lit", bars=1), P(src="v:ao-duo", bars=1, crop=1.3), P(src="v:c-walk", bars=2, hflip=True),
              P(src="v:pf-smoke", bars=1, hflip=True), P(src="v:c-hood", bars=1, crop=1.25)],
    "tag": [P(src="v:c-dance", bars=1, cut=True, crop=1.25), P(src="v:e-leds", bars=1, crop=1.3), P(src="v:crew-all", bars=1, crop=1.2),
            P(src="v:c-hood", bars=1, hflip=True), P(src="v:e-dc-ext", bars=1, hflip=True), P(src=None, bars=1),
            P(src="v:o-lanes", bars=1, crop=1.25), P(src="v:a-wall", bars=1, hflip=True), P(src="v:c-conduct", bars=1, crop=1.3),
            P(src="v:p-aisle", bars=1, hflip=True)],
    "outro": [P(src="v:c-lens", bars=2, cut=True), P(src="v:e-leds", bars=1), P(src="v:e-city-lit", bars=4)],
    "end": [P(src="v:c-window", bars=2, crop=1.15), P(src="v:e-city-lit", bars=3, cut=True, crop=1.2), P(src=None, bars=99)],
}

# The intro is a slow hook: only its real drop (0:22, strength 0.86) forces a cut.
SECTION_DROP_MIN = {"intro": 0.6}
# Pattern length multiplier per section: verses and choruses breathe, pre-choruses / drops / tag stay fast.
PACE = {"verse1": 1.5, "chorus1": 1.6, "inter1": 1.0, "verse2": 1.5, "chorus2": 1.6, "breakdown": 1.0, "final": 1.6}

# The cut on screen when this phrase is sung shows this plate. Prefix match on lyrics.json; '#n' = n-th occurrence.
LYRIC_CUES = {
    "One cursor in a quiet room": "v:c-lens", "A blank command": "s:e-screen",
    "I pin the whole": "v:c-desk", "The clock goes": "s:e-clock", "One clean instruction": "s:e-keys",
    "Of little minds": "v:e-tree",
    "Agent to agent": "v:ao-duo", "Parallel hands on a blueprint": "v:o-lanes", "Test it": "v:f-rack",
    "Every return makes": "v:e-leds",
    "Think fast": "v:c-conduct", "Token by token": "s:e-screen", "We ship what": "v:e-city",
    "One bright thread": "v:a-wall", "No wasted motion": "v:c-walk", "We're compiling the future": "v:e-tree",
    "Token by token#2": "v:e-leds", "We come alive": "v:c-lens",
    "Context holds the shape": "v:a-wall", "Inference cuts through": "v:e-dc-aisle", "Modules click like": "s:e-keys",
    "Each abstraction earns": "v:o-lanes", "Run the suite": "s:p-trace", "Refactor down": "v:c-desk",
    "A thousand lanes": "v:e-tree", "Then one more": "v:p-aisle",
    "Agent to agent#2": "v:ao-duo", "Test it#2": "v:f-rack",
    "Think fast#3": "v:c-dance", "We ship what#2": "v:e-dc-ext", "One bright thread#2": "v:o-lanes",
    "We're compiling the future#2": "v:p-aisle",
    "Alone at the start": "v:c-window", "now the whole": "v:crew-all", "A thousand small": "v:e-tree",
    "No chaos in motion": "v:o-lanes", "One final green": "v:c-lens",
    "Check every edge": "v:f-rack", "Close every seam": "s:p-trace", "Hold that breath": "v:c-lens", "Compile the dream": "v:e-city",
    "Think fast#5": "v:c-conduct", "We ship what#3": "v:e-city-lit", "We're compiling the future#3": "v:crew-all",
    "We come alive#2": "v:crew-all",
    "One cursor#2": "v:c-lens", "one pulse": "v:e-leds", "A whole world": "v:e-city-lit",
}
# The hardest hits get a chosen plate (drop > lyric cue, so applied after the cues).
HERO_AT = {DB[12]: "v:c-desk", DB[49]: "v:c-hood", DB[64]: "v:c-dance", DB[140]: "v:c-conduct", DB[183]: "v:e-city-lit"}
RAPID = ["v:c-hood", "v:e-leds", None, "v:c-dance", "v:p-aisle", "v:e-dc-ext", "v:c-lens", "v:f-rack"]
OVERRIDES: dict[float, dict] = {}
# Hit runs: rapid cuts only on the strongest; the others (and the last bar of the builds into these drops) get a
# staggered punch-in zoom on the same shot instead.
RAPID_RUNS = [94.64]
ZOOM_RUNS = [31.37, 88.64, 184.28]
ZOOM_BUILDS = [DB[49], DB[140]]          # into drop1 (81.85) and the final drop (225.9)
# 3D wire meshes (overlay `mesh` layer, depth from video/tools/plate_depth.py): a few chosen shots only.
# target: person (inside the tracked silhouette) | near (foreground by depth) | all (whole plate, far fades)
# wave: ripple (from the face / centre) | sweep-right | sweep-down | sweep-up
MESH_AT = [(0.5, {"target": "person", "wave": "ripple"}), (22.2, {"target": "person", "wave": "sweep-right"}),
           (55.2, {"target": "person", "wave": "ripple"}), (82.0, {"target": "person", "wave": "ripple"}),
           (93.3, {"target": "all", "wave": "sweep-down"}), (106.0, {"target": "person", "wave": "sweep-up"}),
           (126.8, {"target": "person", "wave": "sweep-right"}), (150.7, {"target": "near", "wave": "sweep-down"}),
           (226.0, {"target": "person", "wave": "ripple"}), (244.5, {"target": "person", "wave": "sweep-right"}),
           (273.2, {"target": "near", "wave": "ripple"}), (282.5, {"target": "all", "wave": "sweep-right"})]
FEAT = json.loads((ROOT / "assets/plate-features/index.json").read_text()) if (ROOT / "assets/plate-features/index.json").exists() else {}
# Veo clips with a bad tail (in-clip jump cut or an artefact): cuts stay inside the first N seconds.
USABLE = {"c-lens": 7.3, "pf-smoke": 6.7, "c-dance": 6.9, "c-hood": 7.1, "crew-all": 6.4}

# Highlight-lyric plan (type modes, ~1 in 3 phrases; refined at the overlay step). Prefix match, all occurrences.
TYPE = {"One cursor in a quiet room": "type", "I pin the whole": "type", "Of little minds": "flap", "Agent to agent": "flap",
        "Test it": "type", "Think fast": "slam", "build clean": "slam", "Build clean": "slam", "Token by token": "type",
        "We're compiling the future": "flap", "in real time": "slam", "In real time": "slam", "We come alive": "slam",
        "Context holds the shape": "type", "Run the suite": "type", "A thousand lanes": "flap", "Alone at the start": "anchor",
        "One final green": "flap · GREEN", "Check every edge": "slam", "Close every seam": "slam", "Hold that breath": "slam",
        "Compile the dream": "slam", "One cursor": "type", "A whole world": "anchor"}
# Through-line device: THE BUILD pipeline status, per section.
BUILD = {"intro": "QUEUED · 1 job", "verse1": "RUNNING · 1 agent", "pre1": "BRANCHING · 2 → 64 agents",
         "chorus1": "RUNNING · 1,024 agents · 37%", "drop1": "WARN · thermal amber · 58%", "inter1": "RUNNING · 61%",
         "verse2": "TESTS · 4,096 passing · 3 failing", "pre2": "RETRY · 2 failing", "chorus2": "FAIL red · OVERHEAT · 88%",
         "breakdown": "CONVERGING → ✔ the only GREEN (One final green check)", "build": "GREEN · deploying…",
         "final": "LIVE · 100%", "tag": "LIVE · scaling", "outro": "LIVE · 1 world", "end": "end card"}


def resolve(src):
    if not src:
        return None, False
    kind, name = src.split(":", 1)
    still = f"assets/still-images/{name}.jpg"
    if kind == "v":
        for p in (f"assets/video-clips/{name}-fast.mp4", f"assets/video-clips/{name}.mp4"):
            if (ROOT / p).exists():
                return p, True
    return still, False


_LEN = {}
def clip_len(src):
    if src not in _LEN:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ROOT / src)],
                           capture_output=True, text=True)
        _LEN[src] = float(r.stdout.strip() or 8.0)
    return _LEN[src]


def near(t, arr, win):
    best = min(arr, key=lambda x: abs(x - t), default=None)
    return best if best is not None and abs(best - t) <= win else None


def in_word(t, pad=0.05):
    return any(w["start"] + pad < t < w.get("end", w["start"]) - pad for w in WORDS)


def plate_of(path):
    return Path(path).stem.removesuffix("-fast") if path else None


def rapid_cuts(cuts, runs, fps=30):
    n = 0
    for r in runs:
        hits = list(r["hits"])
        step = max(1, -(-MIN_FLASH // max(1, round(r["spacing"] * fps))))
        hits = hits[::step]
        end = hits[-1] + r["spacing"] * step
        host = next((c for c in cuts if c["start"] <= hits[0] < c["end"]), None)
        if host is None:
            continue
        i = cuts.index(host)
        tail = next((c for c in cuts if c["start"] <= end < c["end"]), None)
        new = []
        if hits[0] - host["start"] >= MIN_FLASH / fps:
            new.append({**host, "end": round(hits[0], 3)})
        elif i > 0:
            cuts[i - 1]["end"] = round(hits[0], 3)
        around = {host["source"], tail["source"] if tail else None}
        pool = [x for x in RAPID if x is None or resolve(x)[0] not in around] or RAPID
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
        elif tail:
            new[-1]["end"] = tail["end"]
        cuts[i:j + 1] = new
        n += len(hits)
    return n


def focus_of(c, rel):
    """Screen-normalised point the punch-in zooms toward: the tracked face (else the person box), else centre."""
    F = FEAT.get(c["source"])
    if not F:
        return [0.5, 0.45]
    smp = F["samples"][0]
    if F["kind"] == "video":
        st = c.get("offset", 0) + rel
        smp = min(F["samples"], key=lambda x: abs(x["t"] - st))
    P = smp.get("person")
    if not P:
        return [0.5, 0.45]
    b = P.get("face") or P["bbox"]
    nx, ny = b[0] + b[2] / 2, b[1] + b[3] / 2
    iw, ih, OW, OH, cr = F["w"], F["h"], 1920, 1080, c.get("crop", 1)
    sc = max(OW * cr / iw, OH * cr / ih)
    x, y = nx * iw * sc - (iw * sc - OW) / 2, ny * ih * sc - (ih * sc - OH) / 2
    if c.get("hflip"):
        x = OW - x
    return [round(min(0.8, max(0.2, x / OW)), 3), round(min(0.75, max(0.25, y / OH)), 3)]


def stagger_zoom(cuts, hits, fps=30):
    """One shot holds through the hits and punches in a step on each one (no cut). Absorbs cuts that start inside."""
    if not hits:
        return
    host = next((c for c in cuts if c["start"] <= hits[0] < c["end"]), None)
    if host is not None and not host.get("source"):          # a code-only frame: the plate before it holds instead
        j = cuts.index(host)
        if j > 0 and cuts[j - 1].get("source") and not host.get("drop"):
            cuts[j - 1]["end"] = host["end"]; cuts.pop(j); host = cuts[j - 1]
    if host is None or not host.get("source"):
        print(f"  stagger: no plate under {hits[0]:.2f}"); return
    end = hits[-1] + max(0.25, (hits[-1] - hits[0]) / max(1, len(hits) - 1))
    i = cuts.index(host)
    while i + 1 < len(cuts) and cuts[i + 1]["start"] < end and not cuts[i + 1].get("drop"):
        nxt = cuts.pop(i + 1)
        if nxt["end"] > end:                      # keep the rest of the swallowed shot after the zoom
            cuts.insert(i + 1, {**nxt, "start": round(end, 3), "transition": "cut"})
            host["end"] = round(end, 3)
            break
        host["end"] = nxt["end"]
    rel = [round(h - host["start"], 3) for h in hits if h < host["end"]]
    total = 0.2 if host.get("plate") in ("c-dance", "c-walk") else 0.28      # people walking out of frame: gentler
    host["stagger"] = {"at": rel, "step": round(total / len(rel), 3), "dur": 0.08}
    host["focus"] = focus_of(host, rel[0])
    host.pop("flash", None)
    if not host["veo"]:
        host["motion"] = "static"
    print(f"  stagger zoom: {len(rel)} steps at {hits[0]:.2f} on {host.get('plate')}")


def build_cuts():
    total = beats["duration"] + TAIL
    drops = sorted(e["t"] for e in EVENTS if e["kind"] == "drop" and e["strength"] >= DROP_MIN)
    breaks = sorted(e["t"] for e in EVENTS if e["kind"] == "break" and e["strength"] >= 0.5)
    # Beat changes in this song are weak (0.2-0.5) and would halve/double the whole edit until the next one,
    # so they only re-pace when strong; the overlay still gets all of them via markers.drops.
    grooves = sorted((e["t"], e["dir"]) for e in EVENTS if e["kind"] == "beat_change" and e["strength"] >= GROOVE_MIN)
    cuts = []
    for name, s0, s1, _ in SECTIONS:
        s1 = total if s1 is None else s1
        pat, k, t, burst = PLAN[name], 0, s0, 0
        while t < s1 - 0.05:
            e = pat[k % len(pat)]; k += 1
            sec_drops = [x["t"] for x in EVENTS if x["kind"] == "drop" and x["strength"] >= SECTION_DROP_MIN.get(name, DROP_MIN)]
            on_drop = near(t, sec_drops, 0.08) is not None
            if on_drop:
                burst = BURST + 1
            g = [d for tt, d in grooves if tt <= t + 0.08]
            pace = {"up": 0.5, "down": 2.0}.get(g[-1], 1.0) if g else 1.0
            bars = 1 if burst > 0 else max(1, int(e["bars"] * pace * PACE.get(name, 1.0) + 0.5))
            if near(t, breaks, 0.08) is not None:
                bars = max(bars, HOLD_BREAK)
            burst = max(0, burst - 1)
            later = [d for d in DB if d > t + 0.2]
            end = later[bars - 1] if len(later) >= bars else t + bars * BAR
            nxt = [d for d in sec_drops if t + 0.2 < d < end]
            if nxt:
                end = nxt[0]
            end = min(end, s1)
            if s1 - end < BAR * 0.6:
                end = s1
            src, is_video = resolve(e.get("src"))
            cut = {"start": round(t, 3), "end": round(end, 3), "section": name,
                   "layer": "plate" if src else "machine", "source": src, "veo": bool(is_video), "plate": plate_of(src)}
            if src and not is_video:
                cut["motion"] = e.get("motion", "kenburns-in")
            for f in ("crop", "hflip"):
                if f in e:
                    cut[f] = e[f]
            if e.get("cut") or on_drop:
                cut["transition"] = "cut"
            if on_drop:
                cut["drop"] = True
            cut.update(OVERRIDES.get(round(t, 1), {}))
            cuts.append(cut)
            t = end

    def phrase_t(spec):
        txt, n = (spec.split("#") + ["1"])[:2]
        hits = [p for p in LYR if p["text"].lower().startswith(txt.lower())]
        return hits[int(n) - 1]["t"] if len(hits) >= int(n) else None

    missing = []
    for spec, src in LYRIC_CUES.items():
        t0 = phrase_t(spec)
        if t0 is None:
            missing.append(spec); continue
        i = next((i for i, c in enumerate(cuts) if c["start"] <= t0 + 0.15 < c["end"]), None)
        if i is None:
            continue
        c = cuts[i]
        path, is_video = resolve(src)
        if c["source"] == path:
            continue
        at = near(t0, DB, 0.25) or near(t0, BEATS, 0.15)
        if at and at - c["start"] >= BAR / 2 and c["end"] - at >= BAR / 2:
            tail = {**c, "start": round(at, 3), "transition": "cut"}
            tail.pop("drop", None)
            c["end"] = round(at, 3)
            cuts.insert(i + 1, tail)
            c = tail
        c.update(source=path, veo=bool(is_video), layer="plate", plate=plate_of(path), cue=spec.split("#")[0])
        c.pop("motion", None)
        if not is_video:
            c["motion"] = "kenburns-in"
    if missing:
        print("cues not found:", missing)
    merged = [cuts[0]]
    for c in cuts[1:]:
        p = merged[-1]
        if c["source"] and c["source"] == p["source"] and c["section"] == p["section"] and not c.get("drop"):
            p["end"] = c["end"]
        else:
            merged.append(c)
    cuts[:] = merged
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
    print(f"vocal guard: moved {moved} cut(s) off sung words")
    for t, src in HERO_AT.items():
        c = next((c for c in cuts if abs(c["start"] - t) < 0.1), None)
        if c is None:
            print(f"  hero: no cut starts at {t:.2f}"); continue
        path, is_video = resolve(src)
        c.update(source=path, veo=is_video, layer="plate", plate=plate_of(path), hero=True, transition="cut")
        c.pop("motion", None)
        if not is_video:
            c["motion"] = "kenburns-in"
    runs = [e for e in EVENTS if e["kind"] == "hit_run"]
    n_flash = rapid_cuts(cuts, [e for e in runs if e.get("selected") and any(abs(e["t"] - x) < 0.5 for x in RAPID_RUNS)])
    print(f"hit runs: {n_flash} rapid cuts")
    # the other hit runs + the last bar of the builds into the big drops: a staggered punch-in instead
    zr = [list(e["hits"]) for e in runs if any(abs(e["t"] - x) < 0.5 for x in ZOOM_RUNS)]
    for d in ZOOM_BUILDS:
        zr.append([b for b in BEATS if d - BAR - 0.05 <= b < d - 0.05])
    for hits in zr:
        stagger_zoom(cuts, hits)
    for t0, mesh in MESH_AT:
        c = next((c for c in cuts if c["start"] <= t0 < c["end"]), None)
        if c and c.get("source"):
            c.setdefault("overlay", {})["mesh"] = mesh
    use = {}
    for c in cuts:
        c["plate"] = plate_of(c["source"])
        if c["veo"]:
            n = use.get(c["source"], 0); use[c["source"]] = n + 1
            usable = min(clip_len(c["source"]), USABLE.get(c["plate"], 99))
            room = max(0.0, usable - (c["end"] - c["start"]) - 0.05)
            c["offset"] = round(min((n * 2.3) % 4.0, room), 2)
    return cuts, total


def write_plates():
    (ROOT / "video/prompts").mkdir(parents=True, exist_ok=True)
    stills, veo = {}, {}
    for name, p in PLATES.items():
        people = [f"{LABEL[w]}: {CAST[WHO[w]]['canon']}." for w in p["who"]]
        crit = [CAST[WHO[w]]["critical"] for w in p["who"] if CAST[WHO[w]].get("critical")]
        if p.get("hands_only"):
            people, crit = [f"Only his hands and jacket cuff are visible (THE CODER: khaki field jacket)."], []
        style, extra = STYLE, ""
        if p.get("colour"):      # the ending: natural colour (the edit ramps it in from greyscale, see cut "sat")
            style = ("Style: natural-colour cinematic 35mm film photograph, soft golden dawn light, gentle haze, fine film "
                     "grain, Leica feel. Full natural colour. Full-bleed 16:9, no black bars, no borders. No readable text, "
                     "no letters, no numbers, no logos, no watermarks.")
            extra = "No people at all — an empty scene, no figures, no silhouettes."
        elif "coder" not in p["who"] or p.get("hands_only"):
            # the rainbow-lens exception only belongs in prompts that show the Coder; elsewhere it leaks onto others
            style = style.replace(" except the iridescent rainbow sheen of the shield sunglasses lens", "")
            extra = "Nobody wears sunglasses or goggles." if p["who"] else "No people at all — an empty scene, no figures, no silhouettes."
        prompt = "\n\n".join(filter(None, [
            "Single cinematic film still, 16:9, photorealistic.",
            "\n".join(people), p["scene"], f"Composition: {p['space']}.", BAN, extra, style, "\n".join(crit)]))
        (ROOT / f"video/prompts/{name}.txt").write_text(prompt + "\n")
        refs = list(p.get("refs", []))
        for w in p["who"][:3] if not p.get("hands_only") else []:
            refs.append(f"assets/casting/img/{WHO[w]}-turnaround.jpg")
            if len(p["who"]) == 1:
                refs.append(f"assets/casting/img/{WHO[w]}-face.jpg")
        stills[name] = {"prompt": f"video/prompts/{name}.txt", "refs": refs, "out": f"assets/still-images/{name}.jpg",
                        "veo": p["veo"], "desc": p["desc"]}
        if p["veo"]:
            mp = (f"Animate the reference image. 8 seconds.\nCamera: {p['camera']}.\nMotion: {p['motion']}.\n"
                  + ("Keep the natural colour, the light and the city unchanged" if p.get("colour") else
                  "Keep every face, the clothes, the black-and-white look with colour only in the screen light"
                  + (" and the rainbow sunglasses lens" if "coder" in p["who"] else "")) +
                  ", and the set unchanged. Mouths stay closed — nobody talks or sings. Do not add people, objects, "
                  "text, signs or logos. No whip pans, no cuts, no handheld shake. End on a frame that is easy to cut away from.\n")
            (ROOT / f"video/prompts/{name}-motion.txt").write_text(mp)
            veo[name] = {"image": f"assets/still-images/{name}.jpg", "prompt": f"video/prompts/{name}-motion.txt"}
    (ROOT / "video/stills.json").write_text(json.dumps(stills, indent=1))
    (ROOT / "video/plates.json").write_text(json.dumps(veo, indent=1))
    return stills, veo


def lyric_in(c):
    return [p for p in LYR if c["start"] - 0.05 <= p["t"] < c["end"] - 0.05]


def type_of(text):
    for k, v in TYPE.items():
        if text.startswith(k):
            return v
    return ""


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def write_board(cuts, total, stills, veo):
    counts = {}
    for c in cuts:
        if c["plate"]:
            counts[c["plate"]] = counts.get(c["plate"], 0) + 1
    rows_md, rows_html = [], []
    chapter = None
    for i, c in enumerate(cuts):
        ph = lyric_in(c)
        lyric = " / ".join(p["text"] for p in ph)
        types = sorted({type_of(p["text"]) for p in ph} - {""})
        pl = c["plate"]
        info = PLATES.get(pl, {})
        if pl is None:
            visual, cam, src = "code-only frame (HUD / lyric scene / BUILD status)", "—", "code"
        else:
            visual = info.get("desc", pl)
            cam = info.get("camera", "Ken Burns") if info.get("veo") else "Ken Burns push"
            src = "Veo" if info.get("veo") else "still"
        mods = " ".join(filter(None, [f"crop {c['crop']}" if c.get("crop") else "", "flip" if c.get("hflip") else ""]))
        notes = " ".join(filter(None, ["**DROP**" if c.get("drop") else "", "hero" if c.get("hero") else "",
                                       "⚡flash" if c.get("flash") else "", f"cue: {c['cue']}" if c.get("cue") else "",
                                       "hard cut" if c.get("transition") == "cut" and not c.get("drop") and not c.get("flash") else ""]))
        if CHAPTER[c["section"]] != chapter:
            chapter = CHAPTER[c["section"]]
            rows_md.append(f"| | **{chapter}** | | | | | | | BUILD: {BUILD[c['section']]} |")
            rows_html.append(f'<tr class="ch"><td colspan="9">{html.escape(chapter)} <span>BUILD: {html.escape(BUILD[c["section"]])}</span></td></tr>')
        rows_md.append(f"| {i} | {fmt(c['start'])}–{fmt(c['end'])} | {c['section']} | {lyric} | {', '.join(types)} | "
                       f"{pl or '—'} {mods} | {visual} | {cam} | {src} {notes} |")
        thumb = f'<img src="../{stills[pl]["out"]}" onerror="this.remove()">' if pl in stills else ""
        rows_html.append(
            f'<tr class="{"drop" if c.get("drop") else ""}{" flash" if c.get("flash") else ""}"><td>{i}</td><td>{fmt(c["start"])}<br><small>{c["end"] - c["start"]:.1f}s</small></td>'
            f'<td>{c["section"]}</td><td class="ly">{html.escape(lyric)}</td><td>{html.escape(", ".join(types))}</td>'
            f'<td>{thumb}<b>{html.escape(pl or "—")}</b> <small>{mods}</small></td><td>{html.escape(visual)}</td>'
            f'<td>{html.escape(cam)}</td><td><span class="src {src}">{src}</span> {html.escape(notes.replace("**", ""))}</td></tr>')
    n_veo_cuts = sum(1 for c in cuts if PLATES.get(c["plate"], {}).get("veo"))
    head = (f"{len(cuts)} cuts · {sum(1 for c in cuts if c.get('drop'))} on drops · {sum(1 for c in cuts if c.get('flash'))} hit-run flashes · "
            f"{sum(1 for c in cuts if c['plate'] is None)} code-only · {len(stills)} stills · {len(veo)} Veo plates (8 s) used in {n_veo_cuts} cuts")
    cost = (f"Stills: {len(stills)} × Nano Banana 2 ≈ ${len(stills) * 0.067:.2f} (+ retries). "
            f"Veo: Lite 720p ≈ ${len(veo) * 8 * 0.05:.2f} · Fast 1080p ≈ ${len(veo) * 8 * 0.12:.2f}.")
    usage = ", ".join(f"{k}×{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
    md = [f"# Storyboard — Compile the Future\n", head + "  ", cost + "  ", f"Plate usage: {usage}\n",
          "Type modes: type = terminal typing, flap = split-flap board, slam = hook words on the beat, anchor = pinned to a person. "
          "BUILD = the through-line pipeline status (HUD).\n",
          "| # | time | section | lyric | type | plate | visual | camera | source / notes |", "|---|---|---|---|---|---|---|---|---|", *rows_md]
    (ROOT / "video/storyboard.md").write_text("\n".join(md) + "\n")
    plate_cards = "".join(
        f'<div class="pc"><img src="../{s["out"]}" onerror="this.replaceWith(Object.assign(document.createElement(\'div\'),{{className:\'ph\',textContent:\'still not generated\'}}))">'
        f'<b>{html.escape(n)}</b> <span class="src {"Veo" if s["veo"] else "still"}">{"Veo" if s["veo"] else "still"}</span> <small>×{counts.get(n, 0)}</small><p>{html.escape(s["desc"])}</p></div>'
        for n, s in stills.items())
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard</title>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@900&family=Share+Tech+Mono&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#07080b; --panel:#0e1016; --line:#1d2130; --fg:#e8eaf0; --dim:#8a90a2; --accent:#3ef0ff; --hot:#ff3ea5; --amber:#ffb25a; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--fg); font:14px/1.45 Inter,system-ui,sans-serif; }}
main {{ max-width:1700px; margin:auto; padding:24px; }}
h1 {{ margin:0 0 8px; font:900 34px/1 "Big Shoulders Display",sans-serif; text-transform:uppercase; letter-spacing:.05em; }} h1 em {{ font-style:normal; color:var(--accent); }}
h2 {{ font:900 24px/1 "Big Shoulders Display",sans-serif; text-transform:uppercase; margin:30px 0 12px; color:var(--accent); }}
.meta {{ color:var(--dim); margin:2px 0; }} .meta b {{ color:var(--fg); font-weight:500; }}
.plates {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:10px; }}
.pc {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:8px; }}
.pc img, .ph {{ width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:4px; display:grid; place-items:center; background:#000; color:var(--dim); font:12px "Share Tech Mono",monospace; }}
.pc p {{ margin:4px 0 0; color:var(--dim); font-size:12px; }}
.wrap {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:1100px; }}
td {{ border-bottom:1px solid var(--line); padding:6px 8px; vertical-align:top; }}
td:nth-child(1), td:nth-child(2), td:nth-child(3) {{ font:12px "Share Tech Mono",monospace; color:var(--dim); white-space:nowrap; }}
td img {{ width:110px; display:block; border-radius:3px; margin-bottom:3px; }}
td.ly {{ color:var(--fg); font-weight:500; max-width:240px; }}
tr.ch td {{ background:var(--panel); font:900 18px "Big Shoulders Display",sans-serif; text-transform:uppercase; color:var(--accent); padding:10px 8px; }}
tr.ch span {{ font:12px "Share Tech Mono",monospace; color:var(--amber); margin-left:14px; text-transform:none; }}
tr.drop td {{ box-shadow:inset 3px 0 0 var(--hot); }} tr.flash td {{ background:#140a12; }}
.src {{ font:11px "Share Tech Mono",monospace; padding:1px 6px; border-radius:99px; border:1px solid var(--line); }}
.src.Veo {{ color:var(--accent); border-color:var(--accent); }} .src.still {{ color:var(--amber); border-color:var(--amber); }} .src.code {{ color:var(--hot); border-color:var(--hot); }}
@media (max-width:820px) {{ main {{ padding:16px; }} }}
</style></head><body><main>
<h1>Compile the Future · <em>Storyboard</em></h1>
<p class="meta"><b>{html.escape(head)}</b></p><p class="meta">{html.escape(cost)}</p>
<p class="meta">Type modes: type = terminal typing · flap = split-flap board · slam = hook words on the beat · anchor = pinned to a person. Pink edge = cut on a bass drop; tinted rows = rapid hit-run flashes. Chapter rows show the BUILD status (the through-line).</p>
<h2>Plates</h2><div class="plates">{plate_cards}</div>
<h2>Cut list</h2><div class="wrap"><table>{''.join(rows_html)}</table></div>
</main></body></html>"""
    (ROOT / "video/storyboard.html").write_text(page)
    print("plate usage:", usage)


ETH_AT = 4.3       # seconds after the end card: the Ethical Acceleration section starts (dawn, colour returns)


def ethics_ending(cuts, total):
    """The ending after the end card: one long shot of the city at dawn. It starts in Noir Signal greyscale and the
    real colour of the world ramps in (sat: [from, to, t0, t1] in seconds from the cut start) under the release card."""
    t0 = round(DB[186] + ETH_AT, 3)
    keep = [c for c in cuts if c["start"] < t0]
    keep[-1]["end"] = t0
    src, is_video = resolve("v:e-dawn")
    keep.append({"start": t0, "end": round(total, 3), "section": "end", "layer": "plate", "source": src, "veo": is_video,
                 "plate": "e-dawn", "transition": "dissolve", "sat": [0.0, 1.0, 0.8, 6.5],
                 **({} if is_video else {"motion": "kenburns-in"})})
    return keep, t0


def main():
    stills, veo = write_plates()
    cuts, total = build_cuts()
    cuts, eth_t = ethics_ending(cuts, total)
    sb = {"song": SONG, "fps": 30, "width": 3840, "height": 2160, "tail": TAIL,
          "overlay_frames": "assets/overlay/frames", "dissolve_frames": 5, "grade": "none",
          "markers": {"end_card": DB[186], "ethics": eth_t, "green_check": next(p["t"] for p in LYR if p["text"].startswith("One final green")),
                      "drops": [{k: e[k] for k in ("t", "kind", "strength", "dir", "into", "end", "hits", "spacing", "selected", "manual") if k in e} for e in EVENTS]},
          "song_map": [{"name": n, "start": round(a, 3), "end": round(total if b is None else b, 3), "chapter": ch} for n, a, b, ch in SECTIONS],
          "cuts": cuts}
    (ROOT / "video/storyboard.json").write_text(json.dumps(sb, indent=1))
    write_board(cuts, total, stills, veo)
    print(f"wrote storyboard ({len(cuts)} cuts), {len(stills)} stills, {len(veo)} Veo plates")


if __name__ == "__main__":
    main()
