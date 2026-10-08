"""The ONE place that calls Codex (image generation).

Runs the Codex CLI headless (`codex exec`) with the user's ChatGPT login, asks its built-in
image_gen tool for one image and has Codex copy it to the target path. Reference images are
attached with `-i` (identity / same place). Tested: ~60s plain, ~160s with a reference.
"""

from __future__ import annotations

import asyncio
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import config

_slots = asyncio.Semaphore(config.CODEX_PARALLEL)
GENERATED = Path.home() / ".codex" / "generated_images"
_MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"RIFF")  # png, jpeg, webp


@dataclass
class CodexResult:
    ok: bool
    path: Path | None = None
    sec: float = 0.0
    message: str = ""
    error: str | None = None


def _is_image(p: Path) -> bool:
    try:
        with p.open("rb") as f:
            head = f.read(4)
        return p.stat().st_size > 1000 and any(head.startswith(m) for m in _MAGIC)
    except OSError:
        return False


def _newest_generated(since: float) -> Path | None:
    """Fallback when Codex generated but did not copy: newest image Codex saved after `since`."""
    if not GENERATED.exists():
        return None
    fresh = [p for p in GENERATED.rglob("*") if p.is_file() and p.stat().st_mtime >= since and _is_image(p)]
    return max(fresh, key=lambda p: p.stat().st_mtime) if fresh else None


def _instructions(prompt: str, out: Path, refs: list[Path]) -> str:
    ref_lines = "".join(f"Image {i}: reference ({r.name}).\n" for i, r in enumerate(refs, 1))
    return (
        "Use the built-in image_gen tool (not the CLI fallback, no OPENAI_API_KEY). Generate exactly ONE image.\n"
        + (f"Attached images are references, not edit targets:\n{ref_lines}" if refs else "")
        + f"\n{prompt.strip()}\n\n"
        f"After generating, copy the image file into the current directory as {out.name} "
        "(overwrite nothing else, create no other files). Reply only with the saved path."
    )


async def generate_image(prompt: str, out: Path, *, refs: list[Path] | None = None,
                         log: Callable[[str], None] = print,
                         timeout_sec: int | None = None) -> CodexResult:
    codex = config.find_codex_bin()
    if not codex:
        return CodexResult(ok=False, error="codex CLI not found (install the ChatGPT/Codex VS Code extension or set CODEX_BIN)")
    refs = [r for r in (refs or []) if r.exists()]
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return CodexResult(ok=False, error=f"{out} already exists (never overwrite)")
    last = out.parent / f".{out.stem}.last.txt"
    cmd = [codex, "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(out.parent),
           "--json", "-o", str(last)]
    for r in refs:
        cmd += ["-i", str(r)]
    cmd.append("-")  # prompt from stdin: `-i` takes several values and would swallow a positional prompt

    async with _slots:
        start = time.time()
        log(f"codex: {out.name}" + (f" (refs: {', '.join(r.name for r in refs)})" if refs else ""))
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, limit=16 * 1024 * 1024)
        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(_instructions(prompt, out, refs).encode()),
                timeout=timeout_sec or config.CODEX_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            proc.kill()
            return CodexResult(ok=False, sec=time.time() - start, error="timeout")
        except asyncio.CancelledError:
            proc.kill()
            raise
        sec = time.time() - start

    message = last.read_text(errors="replace").strip() if last.exists() else ""
    last.unlink(missing_ok=True)
    if proc.returncode != 0:
        return CodexResult(ok=False, sec=sec, message=message,
                           error=f"exit {proc.returncode}: {stderr.decode(errors='replace')[-300:]}")
    if not _is_image(out):
        fallback = _newest_generated(start)
        if not fallback:
            # Usually a refusal (content policy) or a plan limit: Codex explains in its last message
            return CodexResult(ok=False, sec=sec, message=message, error=f"no image produced: {message[:300]}")
        shutil.copy2(fallback, out)
        log(f"codex: copied {fallback.name} from ~/.codex/generated_images")
    log(f"codex: done {out.name} in {sec:.0f}s")
    return CodexResult(ok=True, path=out, sec=sec, message=message)
