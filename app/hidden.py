"""Hide / restore items in the UI. Nothing is deleted.

runs, series, jobs: a flag in data/ui_state.json (files untouched).
skills: the skill folder moves to data/archive/skills/ so Claude no longer loads it either;
restoring moves it back into .claude/skills/.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import config

STATE = config.DATA / "ui_state.json"
SKILL_ARCHIVE = config.DATA / "archive" / "skills"
KINDS = ("runs", "series", "jobs", "skills")


def _load() -> dict:
    try:
        data = json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("hidden", {})
    for k in KINDS:
        data["hidden"].setdefault(k, [])
    return data


def _save(data: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def hidden(kind: str) -> set[str]:
    if kind == "skills":
        return {p.name.removeprefix("write-series-") for p in SKILL_ARCHIVE.glob("write-series-*")}
    return set(_load()["hidden"][kind])


def hide(kind: str, item: str):
    if kind == "skills":
        src = config.SKILLS / f"write-series-{item}"
        if not src.exists():
            raise ValueError(f"skill write-series-{item} not found")
        SKILL_ARCHIVE.mkdir(parents=True, exist_ok=True)
        dst = SKILL_ARCHIVE / src.name
        if dst.exists():
            raise ValueError(f"an archived copy of {src.name} already exists")
        shutil.move(str(src), str(dst))
        return
    data = _load()
    if item not in data["hidden"][kind]:
        data["hidden"][kind].append(item)
    _save(data)


def unhide(kind: str, item: str):
    if kind == "skills":
        src = SKILL_ARCHIVE / f"write-series-{item}"
        dst = config.SKILLS / src.name
        if dst.exists():
            raise ValueError(f"{dst.name} already exists in .claude/skills")
        shutil.move(str(src), str(dst))
        return
    data = _load()
    data["hidden"][kind] = [x for x in data["hidden"][kind] if x != item]
    _save(data)
