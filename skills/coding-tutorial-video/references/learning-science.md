# Learning science for coding tutorial videos

The rules below come from multimedia-learning research (Mayer's cognitive theory of
multimedia learning, Sweller's cognitive load theory, Paivio's dual coding), memory research
(Roediger & Karpicke on retrieval practice, Bjork on desirable difficulties, spacing
effects), analogy research (Gentner's structure mapping), animation research (Tversky;
Heer & Robertson on staged transitions) and video-attention studies (Guo et al. on video
length; Szpunar et al. on interpolated questions). Effects are real but modest; the biggest
reliable gains come from a clear explanation, retrieval practice, spacing and explicit
comparison. Polish comes last.

## Contents
1. The viewer's mind (why every rule exists)
2. Structure: ideas, segments, series
3. The cast of characters (pre-training) and the persistent diagram
4. Code on screen
5. Terminal on screen
6. Signaling and colour
7. Motion
8. Analogies
9. Retrieval, repetition, spacing
10. Priorities when rules compete

---

## 1. The viewer's mind

- **Two channels.** Pictures and speech are processed separately; words + relevant pictures
  beat either alone. So the video never "just talks" over static code and never shows
  silent motion that needs explaining.
- **Limited capacity.** A few elements per channel at once. Anything that doesn't build the
  mental model (decoration, music, jokes, a talking head) spends capacity.
- **Active processing.** Watching fluently isn't learning. The viewer must produce
  something: a prediction, an answer, a mapping.
- **Transience.** Video overwrites itself every frame. If pace outruns working memory the
  model collapses — so continuous motion must still be chunked, with holds.

Cognitive load: *eliminate* extraneous load (clutter, split attention, disorientation),
*manage* intrinsic load (pre-training, segmenting, pacing), *foster* germane load
(retrieval, comparison, prediction).

**Expertise reversal:** heavy signaling, pre-training and worked examples help novices and
can slow experts down. Decide the audience first; for experienced viewers shorten
pre-training and recaps.

## 2. Structure

- **Idea list first**: 5–9 core ideas per episode, each one plain sentence a viewer could
  repeat tomorrow. Two sentences = two ideas.
- **Budget**: one claim per ~20–40 s; a segment (60–120 s) = one idea + its example/analogy
  + one retrieval question.
- **Episode length**: ≤ ~6–7 min. Engagement drops sharply after ~6 min regardless of total
  length, so bigger topics become a series (e.g. "1 · first agent / 2 · subagent / 3 · UI
  protocol + evals", or "1 · inventory + ad-hoc commands / 2 · playbooks / 3 · roles +
  vault").
- **Spine of an episode**: hook (10–20 s: the problem in the viewer's world, stated in second
  person) → pre-train the parts (20–50 s) → segments → worked example → interleaved review →
  consolidation (organizer returns filled in, next-step cue). No intro longer than the first
  sentence of content, no logo sting, no end-card grid.
- **Narrative frame, not anecdotes**: "what's unresolved, what resolves it". A true
  production story is allowed when it *is* the lesson (e.g. "my first version called the
  critic nineteen times" teaching that feedback loops need exits).

## 3. The cast of characters and the persistent diagram

Before any system runs, introduce each part as a still, labeled, colour-consistent object
with its name and role, but not the full mechanism. Show them one at a time on the word
that names them. Those same objects then run the process, so pre-training and explanation
are one continuous world.

In this engine that's a `FlowMap`: nodes (parts), edges (flows), a token that travels along
edges (a request, a message, a task result). Keep it alive for the whole series:
- It **docks** as a small mini-map in the top-left while code is shown (visual momentum:
  the viewer never loses the map), and the relevant part lights when the code implementing
  it is discussed.
- A part **travels into the code** that implements it (e.g. the "model" node glides into the
  `GeminiModel(...)` lines; the "inventory" node into `inventory.ini`). This is the
  signature move: concept and code become one object.
- It **returns filled in** at the end as the organizer.

Show the whole system last: part → interaction → full run. Never the complete diagram on
frame one.

## 4. Code on screen

- **Real files, verbatim**, line numbers as in the file. Long files are shown as a window
  that scrolls to the focused block.
- **One focus at a time**: a focus band marks the lines being discussed; other lines dim to
  ~30%. Light individual tokens in the accent colour on the word that names them
  ("the **system prompt**" → `system_prompt` lights on "system").
- **Syntax colour stays quiet** (keywords a lighter neutral, comments muted). Rainbow
  highlighting competes with the accent, and single-colour cueing beats rainbow cueing.
- **Build code in the order you'd teach it**: minimal working version first, then one
  addition per step, each shown in the file that changed. Refactors (e.g. moving setup into
  a helper) are shown as a morph of the same lines into their new home.
- **What the reader of the code actually reads**: when a machine consumes something derived
  from code (a tool spec from a docstring, a compiled manifest), show the derived artifact
  next to the source with a connector, and light the corresponding pieces together.
- **Line length**: at 4K the stage is 1920×1080; ~24–26 px mono is comfortable. If a line
  doesn't fit, shrink the font slightly or widen the panel — never let lines clip.

## 5. Terminal on screen

- **Replay real output**, typed commands at a readable ~25–30 chars/s, output streaming in
  line groups timed to the narration ("see *Tool #1*?" lands as that line appears).
- **Highlight only the line being discussed.** If many lines are relevant (scores in a
  feedback loop), carry the signal in a separate element (score chips lighting in order)
  and keep terminal lines neutral.
- **Condense honestly**: filtering noise (SDK warnings, snapshot events) is fine when the
  panel says so ("snapshot events hidden") or the omission is immaterial; truncate long lines
  with "…"; never invent output.
- **Code and terminal side by side** when running: the code shrinks to the left as context,
  the terminal takes the right. The viewer sees cause and effect together.

## 6. Signaling and colour

Colour is a signaling system with fixed roles for the whole series:

| Role | Use |
|---|---|
| Ground | calm dark field, constant; never switch mid-series |
| Structure | neutral strokes for containers, idle parts, connectors |
| Ink | text and code |
| **Accent** (one saturated colour) | the ONE live element on screen right now |
| Done | accent at ~45% opacity: completed/context, available without competing |
| **Amber** (reserved) | retrieval windows, "your turn", warnings, if–then marks, next-step cue |
| Source | desaturated member of the accent family for analogy sources |

- One saturated accent on screen at a time. When the next thing lights, the previous one
  returns to neutral or "done".
- Link a spoken term to its visual by lighting it on the word.
- Never encode meaning by colour alone (pair with shape, label, position); keep text
  contrast ≥ 4.5:1.
- Labels sit on or beside the part they name, never in a legend. After pre-training,
  labels may fade once shape and position carry identity; they're hidden in retrieval.

## 7. Motion

Motion is justified only when it shows change, continuity or relationship.
- **Morph when it's the same or a related object** (part → its code, draft → revision,
  agent → tool). **Cut only at true boundaries** (segment seams, retrieval beats). Never
  morph unrelated things: a morph asserts a relation.
- **Ease everything that means something** (slow-in/slow-out). No bounce/elastic on claims.
- **Transitions 0.5–1 s**, staged (positions first, then shapes); at most 1–2 movers at once.
- **Holds are part of the animation**: ~1–2.5 s of stillness after each reveal. Nothing new
  starts while the previous idea is still moving.
- **Anticipation**: a small motion aims the eye 0.2–0.5 s before the voice names a thing.
- **Timing grammar per beat**: anticipation → statement + one transformation (4–12 s) →
  hold. Segment seams: motion settles, a small title of the next idea, 1.5–3 s.
- Background motion, particles, glow and "always moving" camera drift are seductive details:
  they lower learning. Leave them out.

## 8. Analogies

Analogies transfer *relational structure* (Gentner). They fail when only surface features
transfer.
1. Choose for structure: the source must share the causal relations (a chef reads the
   ticket, decides, uses the stove, tastes, repeats ↔ an agent reads messages, decides,
   calls a tool, reads the result, repeats).
2. Show the source completely first, in the SAME layout the target will use.
3. Map pairs one at a time: source part pulses, then becomes the target part in place,
   while the narration names both ("the ticket *is* the messages").
4. State the shared principle aloud ("decide, act, look at the result, decide again").
5. Name where it breaks, in one sentence, with the non-matching part visibly detaching and
   fading ("a chef remembers yesterday; the model only knows what's in the messages").
   Break points are often excellent teaching moments (they introduce the next idea).
6. One analogy per idea; retrieve the mapping, not the picture.

Useful sources for technical topics: kitchen (agent loops), writer/editor (review loops),
unit tests (evals), a playbook/recipe card (declarative config), a shipping manifest
(inventory), a relay race (pipelines), a building permit office (auth flows). Only use one
when its causal skeleton really matches.

## 9. Retrieval, repetition, spacing

Identical repetition creates false fluency. Build memory with varied encoding, retrieval and
spacing.
- **Retrieval beat per segment**: field simplifies (veil), labels hidden, a short amber
  prompt, a silent window of 5–8 s with a depleting amber ring, then feedback. Tell viewers
  they can pause. Interpolated questions roughly halve mind-wandering.
- **Production questions** suited to code: "where does the tool result go next?", "what does
  the model actually read to decide when to call this?", "what breaks if you create a new
  agent per message?", "which event tells the UI it's done?", "what stops this loop?",
  "which host gets this task if you run with `--limit web`?".
- **Feedback after the attempt**, ideally morphing the likely wrong answer into the right one
  (a dashed wrong path to "you" fades into the correct path back into messages).
- **Varied encodings of core ideas**: plain statement → why it matters → analogy → if–then
  cue ("if your agent ignores a tool, check the docstring first", with an amber mark landing
  on the trigger).
- **Interleaved review** near the end: earlier ideas return out of order as unlabeled
  silhouettes or code tokens; the viewer names them; labels then appear.
- **Spacing**: each later episode opens with a recall question on the previous one; the
  final episode tells viewers to come back in a week and try the reviews from memory.
  Never imply one viewing is enough.

## 10. Priorities when rules compete

1. Correct, clear explanation of the right ideas (and real, working code).
2. Managing transience: segmenting, holds, pacing, pre-training.
3. Retrieval and generative activity.
4. Signaling and contiguity (one live element; words synced to visuals).
5. Coherence (remove what doesn't teach).
6. Fluid polish and aesthetics.

Judge success by transfer: can a viewer build/run the thing on a new variant? If beauty and
transfer diverge, simplify the field, slow the voice on the new idea, add a harder
retrieval question.
