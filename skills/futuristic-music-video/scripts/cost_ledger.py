"""Shared helpers for paid Gemini calls: API key loading, price table, cost ledger with caps.

Every paid call is appended to <ledger> (default assets/cost-ledger.json in the cwd) so the
session total is always known, and Veo calls are refused past the cap unless --force is given.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# USD, Gemini API pricing page, Oct 2026. Recheck https://ai.google.dev/gemini-api/docs/pricing
VEO_PER_SECOND = {
    "lite": {"720p": 0.05, "1080p": 0.08},
    "fast": {"720p": 0.10, "1080p": 0.12, "4k": 0.30},
    "standard": {"720p": 0.40, "1080p": 0.40, "4k": 0.60},
}
IMAGE_PER_STILL = {
    "flash": 0.039,  # Gemini 2.5 Flash Image
    "nb2": 0.067,    # Nano Banana 2, 1K
    "pro": 0.134,    # Nano Banana Pro, 1K
}

VEO_CALL_CAP = 8
VEO_RETRIES_PER_PLATE = 2


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    for d in [Path.cwd(), *Path.cwd().parents]:
        env = d / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No GEMINI_API_KEY in environment or any .env up the tree.")


def default_ledger() -> Path:
    return Path.cwd() / "assets" / "cost-ledger.json"


def read(ledger: Path) -> list[dict]:
    if ledger.is_file():
        return json.loads(ledger.read_text())
    return []


def total(ledger: Path) -> float:
    return round(sum(e.get("usd", 0) for e in read(ledger)), 3)


def check_veo_caps(ledger: Path, plate: str, force: bool) -> None:
    entries = [e for e in read(ledger) if e.get("kind") == "veo"]
    same = [e for e in entries if e.get("plate") == plate]
    problems = []
    if len(entries) >= VEO_CALL_CAP:
        problems.append(f"session already has {len(entries)} Veo calls (cap {VEO_CALL_CAP})")
    if len(same) > VEO_RETRIES_PER_PLATE:
        problems.append(f"plate '{plate}' already tried {len(same)} times (1 + {VEO_RETRIES_PER_PLATE} retries)."
                        " Replace this shot with code instead")
    if problems and not force:
        sys.exit("Refusing Veo call: " + "; ".join(problems) + ". Pass --force only if the user approved.")


def append(ledger: Path, entry: dict) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    data = read(ledger)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
    data.append(entry)
    ledger.write_text(json.dumps(data, indent=2))
    print(f"ledger: +${entry.get('usd', 0):.3f} -> session total ${total(ledger):.2f} ({ledger})")


def with_backoff(fn, *, tries: int = 6, base: float = 2.0):
    """Retry on 429 / RESOURCE_EXHAUSTED / 503 with exponential backoff (Tier 1 has ~$10 per 10 min spend caps)."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # google.genai.errors.APIError and friends
            msg = str(e)
            if any(s in msg for s in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")) and i < tries - 1:
                wait = base * (2 ** i)
                print(f"rate limited ({msg[:80]}...), retrying in {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


if __name__ == "__main__":
    ledger = Path(sys.argv[1]) if len(sys.argv) > 1 else default_ledger()
    for e in read(ledger):
        print(f"{e['ts']}  {e.get('kind'):5}  ${e.get('usd', 0):.3f}  {e.get('out', '')}")
    print(f"total ${total(ledger):.2f}")
