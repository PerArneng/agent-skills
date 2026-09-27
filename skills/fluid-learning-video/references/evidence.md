# Evidence Base for the Fluid Learning Video Rules

Use this file to justify a design choice, weigh a trade-off, or avoid overclaiming. Effect sizes vary by study and shrink as meta-analyses grow. Read the numbers as direction and rough magnitude, not guarantees.

## Contents
1. Core theories
2. Principles with effect sizes
3. Motion and perception studies
4. Attention, length and retrieval
5. Voice and audio
6. Memory, analogy and examples
7. Contested or weak areas
8. Where the source documents disagree (and how the skill resolved it)

---

## 1. Core theories

| Theory | Claim relevant to video | Source |
|---|---|---|
| Cognitive Theory of Multimedia Learning | Two channels (visual/verbal), limited capacity, active processing (select → organize → integrate) | Mayer; Mayer (2021) *Evidence-based principles for instructional video*, JARMAC |
| Cognitive Load Theory | Intrinsic, extraneous and germane load; eliminate extraneous, manage intrinsic, foster germane | Sweller |
| Dual coding | Verbal plus pictorial codes improve recall | Paivio |
| Working memory | Phonological loop plus visuospatial sketchpad | Baddeley |
| Transient information effect | Long stretches of transient animation or speech overload working memory, so animation and modality advantages can vanish or reverse; the fix is shorter segments | Wong, Leahy, Marcus & Sweller (2012) |
| Congruence and apprehension | Visual structure must match the concept; motion must be perceivable. Many animation advantages disappear when static and animated versions are informationally equivalent | Tversky, Morrison & Bétrancourt (2002) |
| Visual momentum | Cuts with no overlap force a mental reset; landmarks and overlap carry context across views | Woods |
| Event segmentation | People parse continuous input into events where predictable motion changes; cuts misaligned with event boundaries disrupt comprehension | Zacks et al.; continuity-editing studies |
| Structure-mapping | Analogy transfers relations, not surface features | Gentner |
| Desirable difficulties / testing effect | Effortful retrieval and spacing produce durable learning | Bjork; Roediger & Karpicke |
| Social agency | A conversational style and a human-like voice make learners treat the lesson as dialogue and invest more effort | Mayer |

## 2. Principles with effect sizes

| Principle | Effect | Notes / source |
|---|---|---|
| Temporal contiguity | d ≈ 1.30 | CTML summaries |
| Multimedia | d ≈ 0.85 | Mayer |
| Coherence | d ≈ 0.80 | Mayer |
| Seductive details (harm) | g = −0.33 | Sundararajan & Adesope (2020), 68 studies |
| Pre-training | d ≈ 0.78 | Mayer |
| Modality | d ≈ 0.72 | Holds for short segments; can reverse for long transient narration |
| Spatial contiguity | d ≈ 0.72; g = 0.74 | Noetel et al. (2022) overview |
| Personalization | d ≈ 0.52 | Supported meta-analytically |
| Signaling | g⁺ ≈ 0.53 retention, 0.33 transfer | Schneider, Beege, Nebel & Rey (2018), 103 studies, N = 12,201. Noetel (2022) pooled g < 0.2, so treat it as reliable but modest |
| Text–picture correspondence signals (e.g. color coding) | Positive, with boundary conditions | Richter, Scheiter & Eitel (2016), 27 studies |
| Segmenting | d ≈ 0.32 retention, 0.36 transfer, 0.23 lower load | Meta-analyses |
| Expertise reversal | Support helps novices (d ≈ 0.5) and can hurt experts (d ≈ −0.43) | Kalyuga, Ayres, Chandler & Sweller (2003) |
| Animation vs. static | d = 0.37 (CI 0.25–0.49); larger for representational (0.40), realistic (0.76), procedural-motor (1.06) content | Höffler & Leutner (2007), 26 studies |
| Animation vs. static (update) | g = 0.23 | Berney & Bétrancourt, 41 experiments, >7,000 participants; Castro-Alonso et al. (2019) similar |
| Video vs. other formats (higher ed) | g ≈ 0.80 | Noetel et al. (2021). This compares video with other formats, not fluid with static design |
| Color cueing in video lectures | Single-color, intentional cues beat both no-cue and multi-color on retention and transfer; multi-color raises load | 2024 color-cue study (PMC11274038) |
| Color-coded semantic mapping | Normalized gain 0.47 vs 0.03 in one study; shorter fixation latency | Color-coding studies cited in source PDF B |
| Luminance/opacity masking | Shorter fixations, smaller pupils, higher EEG alpha, which indicates lower extraneous load | Eye-tracking/EEG signaling studies |

## 3. Motion and perception studies

These measured perception and tracking, not long-term learning.

- **Heer & Robertson (2007):** animated transitions between statistical graphics significantly improved graphical perception. Design principles: preserve object constancy; never transform an object into an unrelated object (it "establishes a false relation"); group elements that change together (common fate); minimize occlusion; maximize predictability; stage complex transitions.
- **Robertson et al.:** simple transitions of about 1 s improved task time and satisfaction.
- **Dragicevic et al. (CHI 2011):** slow-in/slow-out easing beat constant speed, fast-in/fast-out and adaptive pacing for object tracking, because it gives more frames at the start and end of a movement.
- **Lowe & Boucheix:** static cues such as arrows often fail inside animations because they can't compete with the dynamic contrast of moving elements. Cues should themselves be dynamic.
- **De Koning et al.:** cues serve selection, organization and integration. Attention cues help most reliably; relational cues need careful design.
- **Twelve principles of animation** (timing, easing, anticipation, follow-through, arcs, secondary action): in a learning video these function as signaling rather than style.

## 4. Attention, length and retrieval

- **Guo, Kim & Rubin (2014):** 6.9 million sessions, 862 edX videos. Median engagement is at most ~6 min whatever the video length. Informal settings and Khan-style progressively drawn visuals engaged learners well. Caveat: this measures watching, not learning.
- **Szpunar, Khan & Schacter (2013, PNAS):** interpolated tests reduced mind-wandering (F(2,45) = 3.43, p = .041, η² = .16), roughly halving it. Note-taking roughly tripled and learning improved. At baseline, students were mind-wandering ~40% of the time when probed.
- **Brame (2016, CBE—Life Sciences Education):** keep videos short, signal, weed extraneous content, use conversational language, add interactive questions.
- **Learner control:** control over pace can overcome many drawbacks of animation (Tversky review).

## 5. Voice and audio

- **Speaking rate:** edX videos averaged ~156 wpm and YouTube tutorials ~145 wpm. Comprehension of compressed speech starts to decline around 275 wpm (Foulke & Sticht, 1969). Watching at 2× numerically reduced test scores, significantly so in one experiment (Chen et al., 2024). Engagement telemetry favors faster speakers (Guo), but that measures engagement, not comprehension of novel material.
- **Pauses:** pauses after a critical inference give working memory time to consolidate before new speech overwrites the phonological buffer. Source recommendations range from 1 to 2.5 s.
- **Prosody:** a monotone voice (small f0 variation) increases fatigue and lowers credibility and comprehension. Contrastive stress on key terms signals hierarchy.
- **Human vs. synthetic voice:** Mayer's original voice principle favored a human voice. Craig & Schroeder (2017, 2019) found modern TTS equal to or better than human for learning and credibility, though humans were rated higher on human-likeness and engagement. Netland et al. (2025; 447 participants) found AI-generated teaching videos produced equally high learning outcomes, and Xu et al. (2025) found comparable outcomes. One study found a "cute" synthesized voice hinders learning, and some 2024–26 studies report lower engagement with AI instructors.
- **Emotional tone:** positive instructors raise emotion, motivation and satisfaction (2024 meta-analysis). Horovitz & Mayer (2021) found happy instructors increased motivation but not learning. Liew et al. (2020) found a calm voice induced more germane load than an enthusiastic one. Conclusion: aim for calm enthusiasm.
- **Audio quality:** Newman & Schwarz (2018) presented identical content at low and high audio quality; listeners rated the research and researcher lower when the audio was poor. This measured credibility, not learning.
- **Background music:** under the coherence principle it is extraneous. Lehmann, Hamm & Seufert (2019) found a transfer benefit moderated by extraversion, and a 2023 meta-analysis found the literature heterogeneous.

## 6. Memory, analogy and examples

- **Testing effect:** Adesope, Trevisan & Sundararajan (2017), 272 effect sizes: practice tests g ≈ 0.61 overall and ≈ 0.51 against restudy. Rowland (2014): g = 0.50 against restudy, with larger effects for recall than recognition. Pan & Rickard (2018): d = 0.40 for transfer.
- **Test-potentiated learning:** a failed retrieval attempt still improves encoding of the subsequent answer.
- **Spacing:** Cepeda et al. (2008), >1,350 people. The optimal gap is ~20–40% of the retention interval for a 1-week test and ~5–10% for a 1-year test. For an exam 4–6 weeks away, revisit after ~1 week; for yearlong retention, revisit after ~3–5 weeks.
- **Interleaving:** strong evidence for mathematics and category learning, weaker for conceptual explanation videos.
- **Comparison:** Alfieri, Nokes-Malach & Schunn (2013), 57 experiments: case comparison d = 0.50 (CI 0.44–0.56), and stating the principle moderated the effect. Gentner, Loewenstein & Thompson (2003): comparing cases gave 48% transfer vs 19% when the same cases were studied separately, and only 16% of learners linked separate cases spontaneously.
- **Worked examples:** Barbieri et al. (2023), 55 studies: g = 0.48 in mathematics. Correct examples alone worked best; adding self-explanation prompts unexpectedly reversed the effect. Fade examples as expertise grows.
- **Concreteness fading:** Fyfe, McNeil, Son & Goldstone (2014) review; McNeil & Fyfe (2012) d = 0.83. No meta-analysis exists, and a 2024 physics study (N = 187) found no advantage over simultaneous presentation.
- **Narrative:** plausibly aids engagement, but learning-specific evidence is modest, and stories easily become seductive details.

## 7. Contested or weak areas (don't overclaim)

| Area | State of evidence |
|---|---|
| "Fluid design" as a package | **Untested.** No study compares morph-heavy motion graphics with cut-based animation on learning outcomes. The rules are inferred from animation meta-analyses, CLT experiments and perception studies. |
| Stacking design principles | A 2025 *Frontiers in Psychology* experiment combining several principles found no significant effect (F(2,126) = 0.52, p = .60). The authors call this "instructional equivalence": once content is sound, design refinements give diminishing returns. |
| Emotional design via color and shape | Um et al. (2012): warm colors and round shapes improved comprehension and transfer. Plass et al. (2014) replicated comprehension only. Brom et al. (2018) meta-analysis: retention d ≈ 0.39, comprehension 0.32, transfer 0.33, with weak affect effects. Several null replications, and a 2025 study found benefits only at medium difficulty. Weak to moderate. |
| Color psychology (red/blue) | Mehta & Zhu (2009): red aids detail-oriented tasks, blue aids creative tasks. A dosing tool, not a theme. |
| Cool colors and sustained attention | Plausible design convention; lower arousal than large red or orange fields. |
| Background music | Mixed. The skill's rule is conservative: none under speech. |
| Instructor face | Preference and engagement benefits without consistent learning gains (Kizilcec et al.); a face can compete with visuals. Gaze and pointing cues are the better-supported part. |
| Synthetic voice | Roughly equal for learning outcomes; possibly lower engagement and social connection. |
| Curiosity gaps and pattern interrupts | Consistent with generative-learning theory, but little direct evidence in educational video. Treat as heuristics and keep them content-relevant. |
| 6-minute rule | Engagement data from 2012 MOOCs, convergent with segmenting and transient-information research, but not a hard law. |
| Some figures | A few numbers (e.g. Adesope's g = 0.61, Noetel's pooled signaling) were verified through secondary sources in the original research. |

## 8. Where the source documents disagree

| Topic | Positions | Resolution in the skill |
|---|---|---|
| Speaking rate | Brief A: 120–135 wpm for new material. Framework B: 150–190 wpm (from Guo's engagement data). Review C: 130–160 wpm, ~150 typical. | Default 140–160 wpm; 125–140 for new or dense material; 110–125 for new terms and numbers; up to ~170 for recaps. Avoid long stretches below ~120 or above ~190. B's high rates reflect engagement, not comprehension. |
| Music | A: a very low non-melodic bed ducked under speech is allowed. B: exclude entirely. C: none under narration, stings at boundaries are fine. | None under narration; brief stings only at boundaries or wordless transitions. |
| Accent color | A: cool teal for the live idea, amber reserved for action. B: a single amber or cyan accent on a neutral 60-30-10 canvas. C: a warm primary accent with 3–4 semantic accents. | Specify by role: calm neutral or cool ground, one saturated live accent at a time, one reserved warm color for act/retrieve, ≤ 5 colors in total. The hues are the designer's choice. |
| Repetition | A: four passes (statement, benefit, image, if–then). C: three touches (preview, explain, retrieve), then re-retrieve next video. | Varied encodings (up to four, scaled to importance), plus retrieval, progressive recap, interleaved review and a cross-video re-retrieval. |
| Voice | Mayer: human voice. Newer studies: modern TTS is equivalent for outcomes. | Top-tier neural or human voice both acceptable; human is safer for engagement; never a novelty voice. |
| Pause length | A: 0.4–0.6 s after clauses, 0.8–1.2 s after definitions. B: 1.5–2.5 s after critical inferences. C: 1–2 s at boundaries. | Short pauses after clauses, 1–1.5 s after definitions or key inferences, 1–2.5 s holds after reveals and at boundaries, 3–10 s silence for retrieval. |
| Retrieval window | A: 4–8 s. B: 5 s. C: 5–10 s. | 3–10 s scaled to question difficulty, with an explicit invitation to pause. |
