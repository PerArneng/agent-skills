#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydantic>=2.7",
# ]
# ///
"""Count lines, words and bytes in text files and report the largest ones.

What it does:
  Reads every file given on the command line (directories are walked recursively,
  filtered by --glob), computes per-file statistics and prints a table sorted by
  word count, largest first. Unreadable or non-UTF-8 files are logged as ERROR and
  skipped; the run fails (exit 1) only if no file could be read at all.

Output:
  stdout  The result table, or JSON with --json. This is plain output, not logging,
          so it can be piped (e.g. `| jq`).
  stderr  Log lines: "YYYY-MM-DD HH:MM LEVEL message key=value ...".
          Levels: DEBUG (only with -v), INFO, WARN, ERROR, FAIL.

Exit codes:
  0  success
  1  failure (a FAIL line on stderr says why)
  2  invalid command line (printed by argparse)

Side effects:
  None. Only reads the given files.

Examples:
  ./template.py README.md src/
  ./template.py src/ --glob '*.py' --top 5 --json | jq '.[0]'
  ./template.py -v notes/

--help output:
[BEGIN HELP]
  $ template.py --help
  usage: template.py [-h] [-v] [--glob PATTERN] [--top N] [--json] PATH [PATH ...]

  Count lines, words and bytes in text files and report the largest ones.

  positional arguments:
    PATH            files or directories to scan

  options:
    -h, --help      show this help message and exit
    -v, --verbose   log DEBUG lines too (default: False)
    --glob PATTERN  filename pattern used when walking directories (default: *)
    --top N         show only the N largest files (default: 10)
    --json          print JSON instead of a table (default: False)
[END HELP]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from pydantic import BaseModel, ConfigDict

log = logging.getLogger("template")


# --------------------------------------------------------------------------- logging

# Rename the stdlib levels to the four-letter house style.
logging.addLevelName(logging.WARNING, "WARN")
logging.addLevelName(logging.CRITICAL, "FAIL")

_RESET = "\033[0m"
_KEY_STYLE = "\033[1;97m"  # bold bright white
_TIME_STYLE = "\033[2m"  # dim
_LEVEL_STYLES = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;97;41m",  # bold white on red
}
# A `key=` token: start of message or after whitespace/punctuation that cannot be part of a key.
_KEY_RE = re.compile(r"(?<![\w.\-/=])([A-Za-z_][\w.\-]*)=")


class LogFormatter(logging.Formatter):
    """Formats `2021-01-12 15:56 INFO message key=value`, colored when writing to a TTY."""

    def __init__(self, color: bool) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        stamp = self.formatTime(record, self.datefmt)
        level = record.levelname
        message = record.getMessage()
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
    color = sys.stderr.isatty() and "NO_COLOR" not in os.environ
    handler.setFormatter(LogFormatter(color))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def kv(**fields: object) -> str:
    """Render fields as `key=value` pairs; strings with spaces or quotes are JSON-quoted."""
    return " ".join(f"{key}={_fmt_value(value)}" for key, value in fields.items())


def _fmt_value(value: object) -> str:
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str):
        needs_quotes = value == "" or any(c.isspace() or c in "\"'=" for c in value)
        return json.dumps(value, ensure_ascii=False) if needs_quotes else value
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple, set, frozenset)):
        return "[" + ",".join(_fmt_value(v) for v in value) + "]"
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    return str(value)


class ScriptFailure(Exception):
    """Raised for an expected, explainable failure. main() logs it as FAIL and exits 1."""


# --------------------------------------------------------------------------- models


class FileStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    lines: int
    words: int
    bytes: int


class Report(BaseModel):
    model_config = ConfigDict(frozen=True)

    files: list[FileStats]
    skipped: list[Path]
    total_words: int


# --------------------------------------------------------------------------- pure core


def compute_stats(path: Path, text: str) -> FileStats:
    return FileStats(
        path=path,
        lines=text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        words=len(text.split()),
        bytes=len(text.encode()),
    )


def build_report(
    paths: Iterable[Path],
    top: int,
    read_text: Callable[[Path], str],
) -> Report:
    """Pure apart from the injected `read_text`; tests pass a dict lookup instead."""
    stats: list[FileStats] = []
    skipped: list[Path] = []
    for path in paths:
        try:
            text = read_text(path)
        except (OSError, UnicodeDecodeError) as e:
            log.error("cannot read file, skipping %s", kv(path=path, error=type(e).__name__, detail=str(e)))
            skipped.append(path)
            continue
        item = compute_stats(path, text)
        log.debug("counted %s", kv(path=path, lines=item.lines, words=item.words, bytes=item.bytes))
        stats.append(item)

    if not stats:
        raise ScriptFailure(f"no readable files {kv(skipped=len(skipped))}; check the paths and --glob")

    ranked = sorted(stats, key=lambda s: s.words, reverse=True)
    return Report(files=ranked[:top], skipped=skipped, total_words=sum(s.words for s in stats))


def render_table(report: Report) -> str:
    width = max(len(str(s.path)) for s in report.files)
    rows = [f"{'PATH':<{width}}  {'LINES':>7}  {'WORDS':>7}  {'BYTES':>9}"]
    rows += [f"{str(s.path):<{width}}  {s.lines:>7}  {s.words:>7}  {s.bytes:>9}" for s in report.files]
    return "\n".join(rows)


# --------------------------------------------------------------------------- io edge


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def expand_paths(inputs: list[Path], glob: str) -> list[Path]:
    found: list[Path] = []
    for p in inputs:
        if p.is_dir():
            matched = sorted(f for f in p.rglob(glob) if f.is_file())
            log.debug("walked directory %s", kv(dir=p, glob=glob, matched=len(matched)))
            found.extend(matched)
        elif p.exists():
            found.append(p)
        else:
            log.warning("path does not exist, ignoring %s", kv(path=p, cwd=Path.cwd()))
    return found


# --------------------------------------------------------------------------- cli


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", type=Path, metavar="PATH", help="files or directories to scan")
    parser.add_argument("-v", "--verbose", action="store_true", help="log DEBUG lines too")
    parser.add_argument("--glob", default="*", metavar="PATTERN", help="filename pattern used when walking directories")
    parser.add_argument("--top", type=int, default=10, metavar="N", help="show only the N largest files")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    started = time.monotonic()
    log.info("starting %s", kv(inputs=[str(p) for p in args.paths], glob=args.glob, top=args.top, json=args.json))
    try:
        paths = expand_paths(args.paths, args.glob)
        log.info("resolved input files %s", kv(count=len(paths)))
        report = build_report(paths, args.top, read_text=read_text_file)
    except ScriptFailure as e:
        log.critical("%s", e)
        return 1

    # Plain stdout output: the script's product, deliberately not a log line.
    if args.json:
        print(json.dumps([s.model_dump(mode="json") for s in report.files], indent=2))
    else:
        print(render_table(report))

    log.info(
        "done %s",
        kv(files=len(report.files), skipped=len(report.skipped), total_words=report.total_words,
           elapsed_s=time.monotonic() - started),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
