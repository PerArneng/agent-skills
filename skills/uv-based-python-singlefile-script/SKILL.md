---
name: uv-based-python-singlefile-script
description: How to write a single-file Python script that runs with `uv run` - PEP 723 inline dependency header, full type hints, pure functions with IO injected as parameters, Pydantic models for any class, argparse with -h/--help, a header docstring that documents the script and embeds its real --help output for AI readers, and a fixed colored log format (`2021-01-12 15:56 INFO message key=value`, levels DEBUG/INFO/WARN/ERROR/FAIL). Use this whenever you create, scaffold, rewrite or review a standalone Python script, CLI tool, helper or automation script - including "write a script that...", "make a quick tool to...", files under scripts/ or tools/, `uv run` / `uv run --script` / PEP 723 / `# /// script` headers - even if the user does not mention uv or this skill. Not for multi-module packages with a pyproject.toml (use python-architecture for those).
---

# uv single-file Python scripts

One file is the whole program: dependencies, documentation, CLI, logic and logging. Someone who
has only this file and `uv` installed can run it, and an AI agent that reads only its header knows
what it does, how to call it and what it prints. Everything below serves those two goals.

Start from `assets/template.py`: it is a complete, working script that follows every rule here
(and passes `mypy --strict`). Copy it, then replace the example logic. Copying beats retyping
because the logging block is fiddly and must look identical across all scripts.

## 1. File layout

Keep this order so every script reads the same way:

1. Shebang `#!/usr/bin/env -S uv run --script`, then `chmod +x`, so `./tool.py` works directly.
2. PEP 723 block with `requires-python` and `dependencies`.
3. Header docstring (section 2).
4. Imports, then `log = logging.getLogger("<script-name>")`.
5. Logging block (copied from the template).
6. Pydantic models.
7. Pure core functions.
8. IO edge functions.
9. `parse_args()` and `main() -> int`, then `if __name__ == "__main__": sys.exit(main())`.

Section separators like `# ------------------------------------------------- pure core` help a
reader jump between the parts.

### PEP 723 header

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "pydantic>=2.7",
# ]
# ///
```

- List every third-party import, with a lower-bound version. Use an empty list `dependencies = []`
  when there are none, so the reader knows it was considered.
- Add dependencies with `uv add --script tool.py 'httpx>=0.27'` or edit the block by hand.
- Prefer the standard library when it does the job well, such as `argparse`, `pathlib`, `json` and
  `subprocess`. Every dependency is a download on first run.
- Run it with `uv run tool.py` or `./tool.py`. Never ask the user to `pip install` anything.

## 2. Header docstring: written for AI and humans

The module docstring is the script's manual. An agent deciding whether and how to call the script
should get everything from it without reading the code. Use these sections, in this order:

```
"""<One-line summary in the imperative. argparse reuses this as the description.>

What it does:
  A few sentences: inputs, processing, what it produces, notable behaviour on
  partial failure.

Output:
  stdout  What is printed there and in what format (table, JSON, nothing).
  stderr  Log lines: "YYYY-MM-DD HH:MM LEVEL message key=value ...".

Exit codes:
  0  success
  1  failure (a FAIL line on stderr says why)
  2  invalid command line (printed by argparse)

Side effects:
  Files written, network calls, devices touched, or "None. Read-only."

Examples:
  ./tool.py input.csv --limit 5
  ./tool.py sub --json | jq .

--help output:
[BEGIN HELP]
  (generated - see below)
[END HELP]
"""
```

The `--help output` block is real output, never hand-written. After any change to the arguments,
regenerate it:

```bash
uv run <skill-dir>/scripts/sync_help.py path/to/tool.py          # rewrite the block
uv run <skill-dir>/scripts/sync_help.py --check path/to/tool.py  # exit 1 if stale
```

`sync_help.py` runs the script's `--help` with colors off and a fixed width. It also detects
argparse subcommands and appends `tool.py <sub> --help` for each one. It then replaces the lines
between the markers. Build the parser description from the docstring's **first line only**
(`(__doc__ or "").splitlines()[0]`). If it used the whole docstring, the help block would contain
itself.

## 3. Pure core, IO at the edge, IO injected

Most of the script should be pure functions: same inputs, same output, no filesystem, network,
clock, environment or subprocess. Pure code is easy to reason about, easy to test with plain
values, and failures in it are reproducible.

Put every IO operation in a small, dedicated function at the edge (`read_text_file`,
`fetch_json`, `run_git`, `now`). These functions do one IO thing and contain no decisions.

When core logic needs IO, **inject the IO function as a parameter** instead of calling it
directly. `main()` wires the real implementations in, and a test passes a fake:

```python
def build_report(paths: Iterable[Path], read_text: Callable[[Path], str]) -> Report:
    ...  # decides, filters, aggregates - never opens a file itself

# main():   build_report(paths, read_text=read_text_file)
# test:     build_report([Path("a")], read_text={Path("a"): "x y"}.__getitem__)
```

Guidelines:
- Type injected functions precisely: `Callable[[Path], str]`, `Callable[[], datetime]`.
- For one or two IO dependencies, pass functions as keyword arguments. For many, group them in a
  `typing.Protocol` and pass one object.
- `main()` is the only place that knows about concrete IO. It parses args, sets up logging, wires
  dependencies, calls the core, prints the result and maps failures to exit codes.
- Logging is the one side effect allowed everywhere. It never changes a result, and it is how you
  troubleshoot the core.
- Do not chase purity into contortions. A 40-line script that reads one file can call
  `read_text_file` from `main()` and pass the string to the core. That still keeps IO at the edge.

## 4. Types and models

- Type-hint everything, including return types and `-> None`. Aim for `mypy --strict` to pass:
  `uvx --with pydantic mypy --strict tool.py`. Add `--with <dep>` for each dependency.
- Use `from __future__ import annotations` and modern syntax: `list[str]`, `X | None`.
- **Any class you define is a Pydantic model**, usually `model_config = ConfigDict(frozen=True)`.
  This gives validation, a readable repr for logs and `model_dump_json()` for `--json` output.
  Use them for parsed API responses, config, results and report rows. Validate external data at
  the edge with `Model.model_validate(raw)`, so the core only sees typed data.
- Exceptions are the exception to the rule: `class ScriptFailure(Exception)` stays a plain class.
- No mutable module-level state. Constants are fine, and so is the module `log`.

## 5. Command line

- Use an option-parsing library: `argparse` by default, since it is stdlib. Use `click` or `typer`
  only if the user asks for them. Every script supports `-h/--help`, and argparse provides it
  automatically.
- Give every argument a `help=` text, and a `metavar` where it reads better. Use
  `ArgumentDefaultsHelpFormatter` so defaults show up in `--help`.
- Use subcommands (`add_subparsers(dest="command", required=True)`) when the script has distinct
  verbs, such as `status | on | off`. Do not set a `metavar` on `add_subparsers`: `sync_help.py`
  finds subcommands through the `{status,on,off}` in the usage line.
- Always include `-v/--verbose`, which enables DEBUG logging.
- For scripts that change things, add `--dry-run`. It does all the validation and logs exactly
  what would be done, without doing it.
- Secrets come from environment variables or files, not flags, because flags end up in shell history.

## 6. Logging

### Format

Every log line looks exactly like this:

```
2021-01-12 15:56 INFO the temp right now is temp=23 unit=celsius
```

`YYYY-MM-DD HH:MM`, one space, the level, one space, the message. The levels are:

| Level   | Color              | Meaning |
|---------|--------------------|---------|
| `DEBUG` | cyan               | Detail for troubleshooting; shown only with `-v`. |
| `INFO`  | green              | Normal progress: start, milestones, summary. |
| `WARN`  | yellow             | Something unexpected that the script worked around. |
| `ERROR` | red                | One item failed and the script continues with the rest. |
| `FAIL`  | bold white on red  | The run failed. Logged once, just before exiting non-zero. |

In `key=value` pairs, the key is **bold white**, which makes values easy to spot. The timestamp is
dim. Colors are applied only when stderr is a TTY and `NO_COLOR` is unset, so piped logs and files
stay clean. The template's `LogFormatter` implements all of this. It renames `WARNING` to `WARN`
and `CRITICAL` to `FAIL`, and bolds keys by matching `key=`. Copy that block as-is.

Third-party libraries log through the same root logger. At DEBUG this floods the output with
their internals: httpcore logs TLS and socket events, and httpx logs full URLs, which may contain
ids. In `setup_logging`, raise them to WARNING, e.g.
`logging.getLogger("httpcore").setLevel(logging.WARNING)`. Then log the IO yourself, one line per
call, at the edge.

### Where output goes

- **Logs go to stderr.** **The script's product goes to stdout** via `print`: a table, JSON, a
  generated file's path. This keeps `./tool.py | jq` working while logs stay visible.
- The header docstring's `Output:` section must say explicitly what goes to stdout. Plain,
  unlogged output exists only where it is documented there. Everything else is a log line.
- Use `log.critical(...)` for FAIL. The usual pattern: core code raises `ScriptFailure("...")`,
  then `main()` catches it, logs it at FAIL and returns 1. Let truly unexpected exceptions crash
  with a traceback, which is more useful than a vague FAIL.

### What to log: be generous, and make values findable

The goal is that a log alone, without re-running anything, tells you what happened and why.
Don't hold back:

- **At start**, log the effective inputs: arguments after defaults, resolved paths, the selected
  target, and whether it is a dry run.
- **At every IO boundary**, log what was attempted and what came back: method, URL, status,
  elapsed time, item count and size. Use DEBUG for per-item detail and INFO for aggregates.
- **At every decision**, log why: "skipping, already on", "using cached token, expires_in_s=1830".
- **On failure**, log what was attempted, the values involved, the underlying error type and
  message, and a hint toward the fix.
- **At the end**, log a summary with counts and `elapsed_s`.

Put values in `key=value` form with the `kv()` helper from the template, rather than weaving them
into prose:

```python
log.info("the temp right now is %s", kv(temp=23, unit="celsius"))
# 2021-01-12 15:56 INFO the temp right now is temp=23 unit=celsius

log.error("request failed %s", kv(method="PUT", url=url, status=403, elapsed_ms=212, body=text[:200]))
log.critical("no readable files %s; check the paths and --glob", kv(skipped=3))
```

`kv()` JSON-quotes strings that contain spaces, quotes or `=`. It renders paths, lists and
Pydantic models compactly, and rounds floats to 3 decimals. Use clear key names in snake_case,
with units where they matter: `elapsed_ms`, `size_bytes`, `temp_c`.

**Never log secrets**, such as tokens, passwords, API keys or full auth headers. Log that a secret
was present, its length, its expiry, or a masked form like `abcd…wxyz`.

## 7. Checklist before handing over

1. `chmod +x tool.py`. `./tool.py --help` works and the first run installs its dependencies.
2. `uv run <skill-dir>/scripts/sync_help.py tool.py` has refreshed the `--help` block.
3. `uvx --with <deps> mypy --strict tool.py` passes, or remaining issues are justified.
4. You ran it at least once for real: the happy path, plus one failure path to see the FAIL line.
   For scripts that change things, start with `--dry-run`.
5. The docstring's `Output`, `Exit codes` and `Side effects` sections match what the script does.
