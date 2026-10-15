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
# Video tools the prompts are written for: "flow" (Google Flow / Veo parts) and/or "higgsfield" (10-15s clip prompts
# for Seedance / Kling). Flow only for now; STORY_DNA_VIDEO_TARGETS=flow,higgsfield writes both (slower).
VIDEO_TARGETS = tuple(t.strip() for t in os.environ.get("STORY_DNA_VIDEO_TARGETS", "flow").split(",") if t.strip()) or ("flow",)

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


# Image generation goes through the Codex CLI (ChatGPT login, built-in image_gen; no API key).
# One image at a time: each takes ~1-3 min and counts against the ChatGPT plan's limits.
CODEX_PARALLEL = int(os.environ.get("STORY_DNA_CODEX_PARALLEL", "1"))
CODEX_TIMEOUT_SEC = int(os.environ.get("STORY_DNA_CODEX_TIMEOUT", "600"))


def find_codex_bin() -> str | None:
    """CODEX_BIN env, then PATH, then the newest binary bundled in the VS Code ChatGPT/Codex extension."""
    env = os.environ.get("CODEX_BIN")
    if env and Path(env).exists():
        return env
    on_path = shutil.which("codex")
    if on_path:
        return on_path
    candidates = [c for c in Path.home().glob(".vscode/extensions/openai.chatgpt-*/bin/*/codex")
                  if c.is_file() and os.access(c, os.X_OK)]
    return str(max(candidates, key=lambda c: c.stat().st_mtime)) if candidates else None


def check_environment() -> dict:
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "whisperx_venv": VENV_PY.exists(),
        "claude_bin": find_claude_bin(),
        "codex_bin": find_codex_bin(),
        "hf_token": bool(os.environ.get("HF_TOKEN")),
    }
