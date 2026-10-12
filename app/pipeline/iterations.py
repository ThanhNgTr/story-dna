"""<session>/iterations.json: the log of every feedback / approval / edit round.

Canonical shape: {"session": ..., "slug": ..., "rounds": [ {round, timestamp, stage, ...}, ... ]}.
Older sessions hold a plain list of rounds. Read both; on write keep the shape the file already has
(a new file gets the canonical one) and write atomically, so a crash never leaves half a file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(session: Path):
    p = session / "iterations.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load(session: Path) -> list[dict]:
    """Every round, oldest first, whichever shape the file has."""
    doc = _read(session)
    rounds = doc.get("rounds") if isinstance(doc, dict) else doc
    return [r for r in rounds if isinstance(r, dict)] if isinstance(rounds, list) else []


def append(session: Path, entry: dict) -> dict:
    """Add one round (numbered after the last one) and return it."""
    p = session / "iterations.json"
    doc = _read(session)
    if p.exists() and doc is None:
        # Unreadable file: keep it for a human instead of replacing the history with one round
        p.rename(p.with_name(f"iterations.broken-{now().replace(':', '')}.json"))
    if isinstance(doc, dict):
        rounds = doc.setdefault("rounds", [])
    elif isinstance(doc, list):
        rounds = doc
    else:
        rounds = []
        doc = {"session": session.name, "slug": session.parent.name, "rounds": rounds}
    last = max((r.get("round") or 0 for r in rounds if isinstance(r, dict)), default=0)
    entry = {"round": int(last) + 1, "timestamp": now(), **{k: v for k, v in entry.items() if k != "round"}}
    rounds.append(entry)
    tmp = p.with_name(f".{p.name}.tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)
    return entry
