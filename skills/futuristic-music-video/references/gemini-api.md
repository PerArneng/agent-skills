# Gemini API: models, cost and the rules that keep the bill small

Video seconds are the only expensive material, so spend them last. Never generate the whole song in Veo: a 3-minute Standard cut is about $72 before retries and $150+ with them, and it still drifts and breaks.

## Models (confirmed via `gemini_still.py --list-models`, Oct 2026; re-run it, since names change)
| Role | Script flag | Model id | Price (Oct 2026) |
|---|---|---|---|
| Draft stills, environments | `gemini_still.py --tier flash` | `gemini-2.5-flash-image` (Nano Banana) | ~$0.039 / still (~half in batch) |
| Better stills | `--tier nb2` | `gemini-3.1-flash-image` (Nano Banana 2) | ~$0.067 / 1K still |
| Character reference sheets | `--tier pro` | `gemini-3-pro-image` (Nano Banana Pro) | ~$0.134 / 1K still |
| Hero plates, first pass | `gemini_video.py --tier lite` | `veo-3.1-lite-generate-preview` | $0.05/s 720p, $0.08/s 1080p |
| Approved plates, polish | `--tier fast` | `veo-3.1-fast-generate-preview` | $0.10/s 720p, $0.12/s 1080p |
| Rarely | `--tier standard` | `veo-3.1-generate-preview` | $0.40/s, $0.60/s 4K |

Also available: `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite) for very cheap texture plates, used with `--model`. Recheck https://ai.google.dev/gemini-api/docs/pricing before a big batch. Veo bills per generated second, with audio included even when you discard it.

## Budget tiers (offer these at intake)
| Plan | Video seconds | Rough cost | When |
|---|---|---|---|
| Code only | 0 (stills optional) | < $1 | lyric visualizer, pure design |
| **Lean hybrid (default)** | 6 × 8 s Lite 720p | $2.40 + stills ≈ **$4** | most videos |
| Polish hybrid | the same plates re-run on Fast 1080p | $6–$8 | after the Lite motion is approved |
| Directed polish | ~20 plates (performer + lyric-matched scenes) on Fast 1080p + ~30 Pro stills | $15–$20 | lyric-matched edit, 4K master |
| Careless | 180 s Standard | $72–$150+ | never |

## Rules that hold the bill
- Cap the session at **8 Veo calls and 2 retries per plate** unless the user approved a bigger plate list (then `veo_batch.py` passes `--force`). `cost_ledger.py` enforces this; `--force` needs explicit user approval.
- **Lite 720p first.** Overlays hide resolution. Upscale a keeper rather than discovering the shot at 1080p.
- **One reference still per subject.** New locations are new bills.
- **Repeat chorus plates.** Crop, flip and regrade them in the storyboard instead of regenerating.
- If a plate fails twice, **replace the shot with code**. Don't try a third time.
- Show the estimated total and **get user approval before the first paid call**. Report the ledger total at the end (`uv run scripts/cost_ledger.py`).

## Observed limits (Agents in the Loop, Oct 2026, Tier 1 key)
- **Daily request quota**: `429 RESOURCE_EXHAUSTED … exceeded your current quota`. Observed per model on a Tier 1 key: ~10 Lite calls/day, and Fast has its **own** quota (on 2026-10-04, 6 Fast calls went through right after Lite was exhausted). It resets at midnight Pacific (09:00 CEST). Backoff doesn't help; `veo_batch.py` stops after 2 in a row. When Lite runs out, the hero plates can go straight to Fast instead of Lite-then-Fast. Plan big passes across days, or render with still fallbacks and swap clips in later.
- **Monthly spending cap** (a project setting in AI Studio): also `429 RESOURCE_EXHAUSTED`, with the message `Your project has exceeded its monthly spending cap`. It counts *all* usage on the key's project this month (other apps, text and TTS calls), not just this video's ledger, so it can trip at a low ledger total. Raise it at https://ai.studio/spend, or give the video its own project/key.
- **Cost of a finished long-form video (Compile the Future, 5:14):** 26 stills + 22 Veo Fast 1080p clips (incl. one regeneration) = $29.83 total.
- **402 vs 429:** don't grep a log for a bare "402" — Python tracebacks contain `line 402`. `veo_batch.py` matches `ClientError: 402` / `PAYMENT_REQUIRED` only; an earlier version misreported a quota stop as "credits used up".
- **402 "prepayment credits are depleted"**: prepaid billing ran out mid-batch. Top up and re-run (finished plates are skipped).
- **Safety filter** ("Veo returned no video (possibly filtered)", not charged): hit twice on a realistic close-up of the singer's face "singing to camera"; a different still and framing passed first time.
- **Veo Lite rejects `negativePrompt`** (400). `gemini_video.py` folds the negatives into the prompt text for Lite.
- **Fast re-runs are new generations**, not upscales of the Lite clip — the motion changes. Review every Fast clip again.
- **Nano Banana Pro occasionally returns no image** (`'NoneType' object is not iterable`); retry once.
- Real spend for a 4-minute 4K video with ~20 Fast plates + ~30 stills: ≈ $19.

## Veo specifics
- Clip lengths are 4, 6 or 8 s. Video extension exists, but repeated extending degrades fidelity, so make independent 8 s plates and let the cuts and overlay transition between them.
- **Image-to-video** (`--image`) animates a locked still as the first frame. This is the default because it gives the best control.
- **Ingredients to video** (`--ref`, up to 3, no `--image`) conditions on reference images such as a character sheet plus an environment. Use it when the subject must appear in a new composition and stay consistent.
- Prompt the motion only. See `prompts.md`. Text in prompts leads to garbled glyphs in the video.
- The script strips Veo audio, so the Suno master stays the only soundtrack.
- Every Veo frame carries an invisible SynthID watermark that survives editing. The API adds no visible watermark; the consumer apps do.

## Rate limits
Tier 1 accounts have spend-rate caps (roughly $10 per 10 minutes) and RPM limits. Both scripts retry 429 and 503 errors with exponential backoff (2, 4, 8… s). Run Veo calls **sequentially** rather than in parallel. Image calls can run 2–3 at a time.

## Image prompting notes
- Pass the locked subject still as `--ref` on every later still. Describing a face in words alone drifts.
- Ask for empty space where the overlay type will sit ("upper third emptier", "negative space left").
- "Do not animate a still you would not poster." Rejects are cheap at the still stage and expensive at the video stage.
- Each output saves its prompt next to it (`*.prompt.txt`), so a keeper can be regenerated or varied.
