"""Paths and tool locations for the local web app."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ANALYSES = DATA / "analyses"
SERIES = DATA / "series"
JOBS = DATA / "jobs"
INPUT = DATA / "input"
SKILLS = ROOT / ".claude" / "skills"
SCRIPTS = SKILLS / "analyze-videos"
VENV_PY = ROOT / ".venv" / "bin" / "python"

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

# Folder picker may browse under these roots only
BROWSE_ROOTS = [Path(p).expanduser().resolve()
                for p in os.environ.get("STORY_DNA_BROWSE_ROOTS", "~").split(os.pathsep)]

# Max Claude processes running at once (each video-analyst reads ~40 images)
CLAUDE_PARALLEL = int(os.environ.get("STORY_DNA_PARALLEL", "4"))

# Tools the headless Claude sessions may use without asking. acceptEdits covers file writes
# inside the project; Bash is limited to the commands the skills need.
CLAUDE_ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Skill", "Agent", "TodoWrite",
    "Bash(ls:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(cat:*)", "Bash(head:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(date:*)", "Bash(python3:*)", "Bash(.venv/bin/python:*)",
]
CLAUDE_PERMISSION_MODE = os.environ.get("STORY_DNA_PERMISSION_MODE", "acceptEdits")


def _version_key(path: Path) -> tuple:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", str(path))
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def find_claude_bin() -> str | None:
    """CLAUDE_BIN env, then PATH, then the newest bundled binary (VS Code extension / native installs)."""
    env = os.environ.get("CLAUDE_BIN")
    if env and Path(env).exists():
        return env
    on_path = shutil.which("claude")
    if on_path:
        return on_path
    home = Path.home()
    candidates = [c for pattern in (".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude",
                                    "snap/code/current/.local/share/claude/versions/*",
                                    ".local/share/claude/versions/*")
                  for c in home.glob(pattern) if c.is_file() and os.access(c, os.X_OK)]
    return str(max(candidates, key=_version_key)) if candidates else None


def check_environment() -> dict:
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "whisperx_venv": VENV_PY.exists(),
        "claude_bin": find_claude_bin(),
        "hf_token": bool(os.environ.get("HF_TOKEN")),
    }
