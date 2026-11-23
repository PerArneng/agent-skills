#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydantic>=2.7",
# ]
# ///
"""Import project icons and set friendly display names in Orca's profile-state.db.

What it does:
  Reads Orca's `repos` and `projects` documents from `profile-state.db`. For each
  matching repo, embeds `docs/icon/icon-64x64.png` as a base64 data URI
  (`source: "upload"`) unless `--no-icons` is passed, and optionally updates
  `displayName` in both `repos` and `projects` via `--friendly-names` and/or
  explicit `--rename OLD=NEW` mappings. Refuses to write while Orca is running
  unless `--force` is passed.

Output:
  stdout  Summary table of updated repos/projects, or JSON with `--json`. Plain
          output, not logging, so it can be piped (e.g. `| jq`).
  stderr  Log lines: "YYYY-MM-DD HH:MM LEVEL message key=value ...".
          Levels: DEBUG (only with -v), INFO, WARN, ERROR, FAIL.

Exit codes:
  0  success
  1  failure (a FAIL line on stderr says why)
  2  invalid command line (printed by argparse)

Side effects:
  Unless `--dry-run` is set, creates a timestamped `.bak.<epoch>` backup next to
  `profile-state.db` and updates the `repos` and `projects` rows in place. With
  `--render`, runs `docs/icon/render.sh` for repos missing `icon-64x64.png`.

Examples:
  ./import-to-orca.py --dry-run
  ./import-to-orca.py --render --friendly-names
  ./import-to-orca.py --no-icons --rename video-blideo="Video Blideo" --rename homeassistant="Home Assistant"
  ./import-to-orca.py --repo . --json | jq .

--help output:
[BEGIN HELP]
  $ import-to-orca.py --help
  usage: import-to-orca.py [-h] [-v] [--db PATH] [--profile ID] [--repo SELECTOR]
                           [--no-icons] [--render] [--friendly-names] [--rename OLD=NEW]
                           [--dry-run] [--force] [--json]

  Import project icons and set friendly display names in Orca's profile-state.db.

  options:
    -h, --help        show this help message and exit
    -v, --verbose     log DEBUG lines too (default: False)
    --db PATH         explicit path to Orca profile-state.db (default: None)
    --profile ID      Orca profile ID (auto-detected if omitted) (default: None)
    --repo SELECTOR   filter by repo displayName, folder name, or path (repeatable;
                      defaults to all) (default: [])
    --no-icons        skip importing docs/icon/icon-64x64.png (default: False)
    --render          run docs/icon/render.sh when icon-64x64.png is missing (default:
                      False)
    --friendly-names  auto-humanize slug/camelCase project display names (e.g. my-cool-
                      project -> My Cool Project) (default: False)
    --rename OLD=NEW  set an explicit display name for a repo matching OLD by name,
                      folder, or path (repeatable) (default: [])
    --dry-run         preview changes without modifying profile-state.db (default:
                      False)
    --force           write even if Orca appears to be running (not recommended)
                      (default: False)
    --json            print JSON instead of a table (default: False)
[END HELP]
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

log = logging.getLogger("import-to-orca")


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


class RepoIcon(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["image"] = "image"
    src: str
    source: Literal["upload"] = "upload"
    label: str


class DocumentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str
    payload: str
    domain_version: int
    revision: int


class ChangeItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    repo_id: str
    path: Path
    old_name: str
    new_name: str
    icon_png: Path | None
    icon_updated: bool
    name_updated: bool


class ImportResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    db_path: Path
    dry_run: bool
    backup_path: Path | None
    changes: list[ChangeItem]
    projects_updated: int
    skipped: list[str]


# --------------------------------------------------------------------------- pure core

_ACRONYMS = frozenset({
    "ai",
    "api",
    "cli",
    "cpu",
    "db",
    "dns",
    "gpu",
    "http",
    "https",
    "id",
    "io",
    "ip",
    "json",
    "lan",
    "llm",
    "mcp",
    "nas",
    "os",
    "png",
    "sdk",
    "sql",
    "ssh",
    "svg",
    "tcp",
    "tls",
    "ui",
    "url",
    "usb",
    "ux",
    "vm",
    "vpn",
    "wan",
})
_MINOR_WORDS = frozenset({"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"})
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SEP_RE = re.compile(r"[-_.\s]+")


def humanize_name(raw: str) -> str:
    """Convert a slug or camelCase project name into a friendly title-cased display name."""
    stripped = raw.strip()
    if not stripped or stripped == "~":
        return stripped
    spaced = _CAMEL_BOUNDARY_RE.sub(" ", stripped)
    tokens = [t for t in _SEP_RE.split(spaced) if t]
    if not tokens:
        return stripped

    words: list[str] = []
    last_idx = len(tokens) - 1
    for i, token in enumerate(tokens):
        low = token.lower()
        if low in _ACRONYMS:
            words.append(low.upper())
        elif 0 < i < last_idx and low in _MINOR_WORDS:
            words.append(low)
        else:
            words.append(token[:1].upper() + token[1:].lower())
    return " ".join(words)


def parse_rename_specs(specs: Iterable[str]) -> dict[str, str]:
    """Parse repeatable `OLD=NEW` rename specs into a mapping."""
    mapping: dict[str, str] = {}
    for spec in specs:
        if "=" not in spec:
            raise ScriptFailure(f"invalid --rename value {kv(value=spec)}; expected OLD=NEW")
        old, new = spec.split("=", 1)
        old = old.strip()
        new = new.strip()
        if not old or not new:
            raise ScriptFailure(f"invalid --rename value {kv(value=spec)}; both OLD and NEW must be non-empty")
        mapping[old] = new
    return mapping


def make_repo_icon(png_bytes: bytes, label: str) -> RepoIcon:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return RepoIcon(src=f"data:image/png;base64,{b64}", label=label)


def serialize_document(data: list[dict[str, Any]]) -> tuple[str, str]:
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return payload, content_hash


def _matches_repo_filter(
    name: str,
    repo_path: Path,
    filters: set[str],
    resolved_filters: set[str],
) -> bool:
    if not filters:
        return True
    return (
        name in filters
        or repo_path.name in filters
        or str(repo_path) in filters
        or str(repo_path) in resolved_filters
    )


def _resolve_new_name(
    old_name: str,
    repo_path: Path,
    friendly_names: bool,
    rename_map: dict[str, str],
) -> str:
    for key in (old_name, repo_path.name, str(repo_path)):
        if key in rename_map:
            return rename_map[key]
    if friendly_names:
        return humanize_name(old_name)
    return old_name


def plan_updates(
    repos_raw: list[dict[str, Any]],
    projects_raw: list[dict[str, Any]],
    *,
    import_icons: bool,
    friendly_names: bool,
    rename_map: dict[str, str],
    filters: set[str],
    resolved_filters: set[str],
    now_ms: int,
    find_png: Callable[[Path], Path | None],
    read_bytes: Callable[[Path], bytes],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[ChangeItem], int, list[str]]:
    """Compute updated `repos` and `projects` payloads without performing side effects."""
    repos_data = copy.deepcopy(repos_raw)
    projects_data = copy.deepcopy(projects_raw)

    updated_icons_by_id: dict[str, dict[str, Any]] = {}
    updated_names_by_id: dict[str, str] = {}
    changes: list[ChangeItem] = []
    skipped: list[str] = []

    for repo in repos_data:
        repo_id = str(repo.get("id") or "")
        old_name = str(repo.get("displayName") or "")
        raw_path = repo.get("path")
        if not raw_path:
            continue
        repo_path = Path(str(raw_path))
        if not _matches_repo_filter(old_name, repo_path, filters, resolved_filters):
            continue

        new_name = _resolve_new_name(old_name, repo_path, friendly_names, rename_map)
        name_updated = new_name != old_name

        icon_png: Path | None = None
        icon_updated = False
        if import_icons:
            icon_png = find_png(repo_path)
            if icon_png is None:
                log.debug("no icon png found, skipping icon %s", kv(repo=old_name, path=repo_path))
                if not name_updated:
                    skipped.append(f"{old_name} ({repo_path})")
                    continue
            else:
                try:
                    png_bytes = read_bytes(icon_png)
                except OSError as e:
                    log.error(
                        "cannot read icon png, skipping icon %s",
                        kv(repo=old_name, path=icon_png, error=type(e).__name__, detail=str(e)),
                    )
                    if not name_updated:
                        skipped.append(f"{old_name} ({repo_path})")
                        continue
                else:
                    existing_icon = repo.get("repoIcon") or {}
                    label = str(existing_icon.get("label") or new_name)
                    icon_dict = make_repo_icon(png_bytes, label).model_dump()
                    repo["repoIcon"] = icon_dict
                    updated_icons_by_id[repo_id] = icon_dict
                    icon_updated = True
                    log.debug("prepared icon %s", kv(repo=old_name, png=icon_png, bytes=len(png_bytes)))

        if name_updated:
            repo["displayName"] = new_name
            updated_names_by_id[repo_id] = new_name
            log.debug("prepared rename %s", kv(old=old_name, new=new_name))

        if icon_updated or name_updated:
            changes.append(
                ChangeItem(
                    repo_id=repo_id,
                    path=repo_path,
                    old_name=old_name,
                    new_name=new_name,
                    icon_png=icon_png if icon_updated else None,
                    icon_updated=icon_updated,
                    name_updated=name_updated,
                )
            )

    projects_updated = 0
    for proj in projects_data:
        source_ids = [str(rid) for rid in (proj.get("sourceRepoIds") or [])]
        touched = False
        for rid in source_ids:
            if rid in updated_icons_by_id:
                proj["repoIcon"] = updated_icons_by_id[rid]
                touched = True
            if rid in updated_names_by_id:
                proj["displayName"] = updated_names_by_id[rid]
                touched = True
        if touched:
            proj["updatedAt"] = now_ms
            projects_updated += 1

    return repos_data, projects_data, changes, projects_updated, skipped


def render_table(result: ImportResult) -> str:
    if not result.changes:
        return "No changes."
    old_w = max(len("OLD NAME"), *(len(c.old_name) for c in result.changes))
    new_w = max(len("NEW NAME"), *(len(c.new_name) for c in result.changes))
    rows = [f"{'OLD NAME':<{old_w}}  {'NEW NAME':<{new_w}}  {'ICON':<6}  {'NAME':<6}"]
    for c in result.changes:
        icon_col = "yes" if c.icon_updated else "-"
        name_col = "yes" if c.name_updated else "-"
        rows.append(f"{c.old_name:<{old_w}}  {c.new_name:<{new_w}}  {icon_col:<6}  {name_col:<6}")
    return "\n".join(rows)


# --------------------------------------------------------------------------- io edge


def default_orca_data_dir() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "orca"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "orca"


def resolve_profile_db(data_dir: Path, profile: str | None) -> Path:
    if profile:
        return data_dir / "profiles" / profile / "profile-state.db"

    index_path = data_dir / "orca-profile-index.json"
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            active = index.get("activeProfileId") or index.get("defaultProfileId")
            if isinstance(active, str) and active:
                candidate = data_dir / "profiles" / active / "profile-state.db"
                if candidate.is_file():
                    return candidate
        except (OSError, json.JSONDecodeError) as e:
            log.warning("could not read profile index, using local-default %s", kv(path=index_path, error=str(e)))

    return data_dir / "profiles" / "local-default" / "profile-state.db"


def is_orca_running() -> bool:
    if platform.system() == "Darwin":
        res = subprocess.run(["pgrep", "-ix", "Orca"], capture_output=True, text=True)
        return res.returncode == 0
    res = subprocess.run(["pgrep", "-f", "orca"], capture_output=True, text=True)
    if res.returncode != 0:
        return False
    my_pid = str(os.getpid())
    return any(p != my_pid for p in res.stdout.split())


def find_or_render_png(repo_path: Path, render_missing: bool) -> Path | None:
    icon_dir = repo_path / "docs" / "icon"
    png = icon_dir / "icon-64x64.png"
    if png.is_file():
        return png
    render_sh = icon_dir / "render.sh"
    if render_missing and render_sh.is_file():
        log.info("rendering missing png %s", kv(script=render_sh))
        res = subprocess.run(["bash", str(render_sh)], cwd=str(icon_dir), capture_output=True, text=True)
        if res.returncode == 0 and png.is_file():
            return png
        log.error("render.sh failed %s", kv(script=render_sh, code=res.returncode, stderr=res.stderr.strip()[:200]))
    return None


def read_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def read_profile_documents(db_path: Path) -> dict[str, DocumentRecord]:
    if not db_path.is_file():
        raise ScriptFailure(f"profile-state.db not found {kv(path=db_path)}; pass --db or --profile")
    con = sqlite3.connect(str(db_path))
    try:
        docs: dict[str, DocumentRecord] = {}
        for domain in ("repos", "projects"):
            row = con.execute(
                "SELECT payload, domain_version, revision FROM profile_state_documents WHERE domain=?",
                (domain,),
            ).fetchone()
            if row is None:
                raise ScriptFailure(f"domain missing from profile-state.db {kv(domain=domain, db=db_path)}")
            docs[domain] = DocumentRecord(
                domain=domain,
                payload=str(row[0]),
                domain_version=int(row[1]),
                revision=int(row[2]),
            )
        return docs
    finally:
        con.close()


def write_profile_documents(
    db_path: Path,
    updates: dict[str, tuple[str, int, str]],
    updated_at_ms: int,
) -> Path:
    backup_path = db_path.with_name(f"{db_path.name}.bak.{int(time.time())}")
    shutil.copy2(db_path, backup_path)
    log.info("created backup %s", kv(backup=backup_path))

    con = sqlite3.connect(str(db_path))
    try:
        with con:
            for domain, (payload, new_rev, content_hash) in updates.items():
                con.execute(
                    """
                    UPDATE profile_state_documents
                    SET payload = ?, revision = ?, updated_at = ?, content_hash = ?
                    WHERE domain = ?
                    """,
                    (payload, new_rev, updated_at_ms, content_hash, domain),
                )
    finally:
        con.close()
    return backup_path


# --------------------------------------------------------------------------- cli


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="log DEBUG lines too")
    parser.add_argument("--db", type=Path, metavar="PATH", help="explicit path to Orca profile-state.db")
    parser.add_argument("--profile", metavar="ID", help="Orca profile ID (auto-detected if omitted)")
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        default=[],
        metavar="SELECTOR",
        help="filter by repo displayName, folder name, or path (repeatable; defaults to all)",
    )
    parser.add_argument("--no-icons", action="store_true", help="skip importing docs/icon/icon-64x64.png")
    parser.add_argument(
        "--render",
        action="store_true",
        help="run docs/icon/render.sh when icon-64x64.png is missing",
    )
    parser.add_argument(
        "--friendly-names",
        action="store_true",
        help="auto-humanize slug/camelCase project display names (e.g. my-cool-project -> My Cool Project)",
    )
    parser.add_argument(
        "--rename",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="set an explicit display name for a repo matching OLD by name, folder, or path (repeatable)",
    )
    parser.add_argument("--dry-run", action="store_true", help="preview changes without modifying profile-state.db")
    parser.add_argument(
        "--force",
        action="store_true",
        help="write even if Orca appears to be running (not recommended)",
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    started = time.monotonic()

    db_path = args.db or resolve_profile_db(default_orca_data_dir(), args.profile)
    log.info(
        "starting %s",
        kv(
            db=db_path,
            import_icons=not args.no_icons,
            friendly_names=args.friendly_names,
            renames=len(args.rename),
            dry_run=args.dry_run,
        ),
    )

    try:
        rename_map = parse_rename_specs(args.rename)
        if not args.dry_run and not args.force and is_orca_running():
            raise ScriptFailure(
                "Orca appears to be running; quit Orca completely first (or pass --force) "
                "so its in-memory state does not overwrite profile-state.db"
            )

        docs = read_profile_documents(db_path)
        repos_raw: list[dict[str, Any]] = json.loads(docs["repos"].payload)
        projects_raw: list[dict[str, Any]] = json.loads(docs["projects"].payload)
        log.info("loaded profile state %s", kv(repos=len(repos_raw), projects=len(projects_raw)))

        filters = set(args.repos)
        resolved_filters = {str(Path(f).expanduser().resolve()) for f in filters}
        now_ms = int(time.time() * 1000)

        repos_next, projects_next, changes, projects_updated, skipped = plan_updates(
            repos_raw,
            projects_raw,
            import_icons=not args.no_icons,
            friendly_names=args.friendly_names,
            rename_map=rename_map,
            filters=filters,
            resolved_filters=resolved_filters,
            now_ms=now_ms,
            find_png=lambda p: find_or_render_png(p, render_missing=args.render),
            read_bytes=read_file_bytes,
        )

        backup_path: Path | None = None
        if changes and not args.dry_run:
            updates: dict[str, tuple[str, int, str]] = {}
            for domain, data in (("repos", repos_next), ("projects", projects_next)):
                payload, content_hash = serialize_document(data)
                updates[domain] = (payload, docs[domain].revision + 1, content_hash)
            backup_path = write_profile_documents(db_path, updates, now_ms)
        elif not changes:
            log.info("no matching changes to apply")
        else:
            log.info("dry run complete, database not modified")

        result = ImportResult(
            db_path=db_path,
            dry_run=args.dry_run,
            backup_path=backup_path,
            changes=changes,
            projects_updated=projects_updated,
            skipped=skipped,
        )
    except ScriptFailure as e:
        log.critical("%s", e)
        return 1

    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(render_table(result))

    log.info(
        "done %s",
        kv(
            repos_updated=len(result.changes),
            projects_updated=result.projects_updated,
            skipped=len(result.skipped),
            dry_run=result.dry_run,
            elapsed_s=time.monotonic() - started,
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
