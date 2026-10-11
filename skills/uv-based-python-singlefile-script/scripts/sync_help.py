#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Regenerate the --help block in a uv script's header docstring from its real output.

What it does:
  Runs `uv run --script SCRIPT --help` (and `SCRIPT <sub> --help` for every argparse
  subcommand found in the usage line) with colors off and a fixed 88-column width,
  then replaces everything between the `[BEGIN HELP]` and `[END HELP]` marker lines
  in SCRIPT with that output, indented two spaces. The rest of the file is untouched.
  With --check nothing is written; the exit code says whether the block is current.

Output:
  stdout  Nothing.
  stderr  Log lines: "YYYY-MM-DD HH:MM LEVEL message key=value ...".

Exit codes:
  0  block updated, or already current
  1  failure: markers missing, --help failed, or (with --check) the block is stale
  2  invalid command line

Side effects:
  Rewrites SCRIPT in place (unless --check). Executes SCRIPT with --help.

Examples:
  uv run sync_help.py scripts/my-tool.py
  uv run sync_help.py --check scripts/my-tool.py

--help output:
[BEGIN HELP]
  $ sync_help.py --help
  usage: sync_help.py [-h] [-v] [--check] SCRIPT

  Regenerate the --help block in a uv script's header docstring from its real output.

  positional arguments:
    SCRIPT         the uv script whose docstring should be updated

  options:
    -h, --help     show this help message and exit
    -v, --verbose  log DEBUG lines too
    --check        do not write; exit 1 if the block is out of date
[END HELP]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger("sync_help")

BEGIN = "[BEGIN HELP]"
END = "[END HELP]"
HELP_ENV = {"NO_COLOR": "1", "PYTHON_COLORS": "0", "FORCE_COLOR": "", "COLUMNS": "88", "TERM": "dumb"}

# --------------------------------------------------------------------------- logging

logging.addLevelName(logging.WARNING, "WARN")
logging.addLevelName(logging.CRITICAL, "FAIL")
_RESET, _KEY_STYLE, _TIME_STYLE = "\033[0m", "\033[1;97m", "\033[2m"
_LEVEL_STYLES = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;97;41m",
}
_KEY_RE = re.compile(r"(?<![\w.\-/=])([A-Za-z_][\w.\-]*)=")


class LogFormatter(logging.Formatter):
    def __init__(self, color: bool) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        stamp, level, message = self.formatTime(record, self.datefmt), record.levelname, record.getMessage()
        if self.color:
            stamp = f"{_TIME_STYLE}{stamp}{_RESET}"
            level = f"{_LEVEL_STYLES.get(record.levelno, '')}{level}{_RESET}"
            message = _KEY_RE.sub(rf"{_KEY_STYLE}\1{_RESET}=", message)
        line = f"{stamp} {level} {message}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def setup_logging(verbose: bool) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(LogFormatter(sys.stderr.isatty() and "NO_COLOR" not in os.environ))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def kv(**fields: object) -> str:
    def fmt(v: object) -> str:
        s = str(v)
        return json.dumps(s, ensure_ascii=False) if s == "" or any(c.isspace() or c in "\"'=" for c in s) else s

    return " ".join(f"{k}={fmt(v)}" for k, v in fields.items())


class ScriptFailure(Exception):
    pass


# --------------------------------------------------------------------------- pure core


def find_subcommands(help_text: str) -> list[str]:
    """argparse prints subcommands as `{a,b,c}` in the usage line."""
    usage = help_text.split("\n\n", 1)[0]
    match = re.search(r"\{([\w,\-]+)\}", usage)
    return match.group(1).split(",") if match else []


def render_block(sections: list[tuple[str, str]]) -> str:
    chunks = [f"$ {cmd}\n{out.rstrip()}" for cmd, out in sections]
    text = "\n\n".join(chunks)
    return "\n".join(("  " + line).rstrip() for line in text.splitlines())


def replace_block(source: str, block: str) -> str:
    lines = source.splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == BEGIN)
        end = next(i for i, line in enumerate(lines) if i > start and line.strip() == END)
    except StopIteration:
        hint = "add them inside the header docstring"
        raise ScriptFailure(f"markers not found {kv(begin=BEGIN, end=END)}; {hint}") from None
    return "".join(lines[: start + 1]) + block + "\n" + "".join(lines[end:])


def collect_help(name: str, run_help: Callable[[list[str]], str]) -> list[tuple[str, str]]:
    top = run_help([])
    sections = [(f"{name} --help", top)]
    subs = find_subcommands(top)
    log.info("found subcommands %s", kv(count=len(subs), names=",".join(subs) or "-"))
    sections += [(f"{name} {sub} --help", run_help([sub])) for sub in subs]
    return sections


# --------------------------------------------------------------------------- io edge


def make_help_runner(script: Path) -> Callable[[list[str]], str]:
    env = {**os.environ, **HELP_ENV}
    env.pop("FORCE_COLOR", None)

    def run_help(prefix: list[str]) -> str:
        cmd = ["uv", "run", "--quiet", "--script", str(script), *prefix, "--help"]
        log.debug("running %s", kv(cmd=" ".join(cmd)))
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=script.parent)
        if proc.returncode != 0:
            raise ScriptFailure(
                f"--help failed {kv(cmd=' '.join(cmd), exit=proc.returncode, stderr=proc.stderr.strip()[-500:])}"
            )
        log.debug("got help %s", kv(args=" ".join(prefix) or "-", lines=len(proc.stdout.splitlines())))
        return proc.stdout

    return run_help


# --------------------------------------------------------------------------- cli


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("script", type=Path, metavar="SCRIPT", help="the uv script whose docstring should be updated")
    parser.add_argument("-v", "--verbose", action="store_true", help="log DEBUG lines too")
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if the block is out of date")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    script: Path = args.script.resolve()
    log.info("syncing help block %s", kv(script=script, check=args.check))
    try:
        if not script.is_file():
            raise ScriptFailure(f"script not found {kv(path=script)}")
        source = script.read_text(encoding="utf-8")
        sections = collect_help(script.name, make_help_runner(script))
        updated = replace_block(source, render_block(sections))
    except ScriptFailure as e:
        log.critical("%s", e)
        return 1

    if updated == source:
        log.info("help block already current %s", kv(script=script.name))
        return 0
    if args.check:
        log.critical("help block is stale %s", kv(script=script.name, fix=f"uv run sync_help.py {args.script}"))
        return 1
    script.write_text(updated, encoding="utf-8")
    log.info("help block updated %s", kv(script=script.name, sections=len(sections)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
