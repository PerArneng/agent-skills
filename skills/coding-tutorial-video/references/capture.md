# Building the real project and capturing honest output

The video only shows real code and real terminal output. That's what makes it trustworthy
and reproducible, and building first is also how you discover what's actually hard.

## Structure the project as the lesson

- Put the tutorial's code in its own folder (e.g. `tutorial/`, `ansible-demo/`) and list the
  files in `PROJECT["code_files"]` with `code_dir` relative to `video/`.
- Write it as growing steps, each runnable on its own, the way you'll teach:
  `step1_minimal.*` → `step2_add_X.*` → …; for config-heavy topics the steps are files that
  grow (`inventory.ini`, then `site.yml` with one task, then handlers, then a role).
- Shared setup that every step repeats is shown once in full, then moved into a helper
  (the refactor becomes a short beat).
- Keep lines short enough for a code panel (~85 chars at fs 23; wrap long strings).
- Use the latest stable versions and look them up (package indexes, official docs, MCP doc
  servers if available); read installed library source for exact signatures rather than
  guessing APIs.

## Run and capture

- Run every step and save output to `video/captures/<name>.txt`. Filter library noise that
  is irrelevant to the lesson (a deprecation warning printed on every call) and say so to
  the user; never edit meaningful output.
- Interactive programs: pipe the inputs (`printf 'first\nsecond\nexit\n' | cmd`) and type the
  same inputs back in the video with `term.input()` on the narration cue. Piped input isn't
  echoed, so the capture shows prompts without the typed text — the video restores it.
- Servers: start in the background, wait for readiness (poll a health endpoint), capture
  the startup log lines, exercise it with a real client (curl a real request file), capture
  the full response, stop the server. Don't pipe a streaming response into `head`: closing
  the pipe cancels the request server-side.
- Remote hosts (Ansible, SSH, cloud CLIs): capture from a real target (a VM, a container
  with sshd, a lab host). Mask hostnames/IPs if they're private; keep the structure of the
  output (`ok:`, `changed:`, `PLAY RECAP`) intact because it's what the viewer learns to read.
- Record exit codes. A failure you hit is a candidate teaching beat, and the retry/fix shown
  afterwards is the lesson.
- When a result appears in the narration ("all six checks pass", "score five, then seven"),
  capture first and write that beat afterwards so they match.

## Secrets

- Keys live in `.env` (gitignored); show `.env` on screen only with the value masked
  (`KEY=AQ.Ab8R••••••••`). Put `.env.template` in the repo.
- Scan captures for tokens, internal hostnames, emails and paths under a home directory
  before assembling (`grep -nE 'key|token|secret|@|/Users/' captures/*`).

## Free-tier API limits while capturing

- LLM-backed demos can hit per-model limits (e.g. 20 requests/day, 5/minute). Make the model
  id overridable by env var in the tutorial's code (default = the model shown on screen), so
  captures can be spread across models when necessary; tell the user if captures used a
  different model than the code shows. With billing enabled, capture with the default.
- Feedback loops and evals multiply requests (a writer + critic loop, 3 cases × several
  calls + a judge). Budget before running.
- Check that the SDK's retry actually fires for the provider's throttling errors; wrap the
  model client if it doesn't (seen: a provider that only mapped `RESOURCE_EXHAUSTED`, while
  streamed 429s arrived as "Too Many Requests" and 503s as a different exception type).

## Condensing long output honestly

- Long event streams: filter repetitive event types and label the panel ("snapshot events
  hidden"). Keep the order of what remains.
- Tables that don't fit: show the summary box plus one line per result that you print
  yourself from the report object (add the print to the real script and re-run, so it's
  still real output).
- Very long lines: the terminal truncates with "…"; wrap prose lines first if their end
  matters.
