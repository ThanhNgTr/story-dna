"""The ONE place that calls Claude.

Runs the Claude Code CLI headless (`claude -p`, stream-json) with the logged-in user's account,
inside the project dir so .claude/skills, .claude/agents and CLAUDE.md load as usual.
To switch to the Agent SDK + API key later, replace run_claude() only.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Callable

from . import config


@dataclass
class ClaudeResult:
    ok: bool
    text: str = ""
    session_id: str | None = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    turns: int = 0
    error: str | None = None
    tool_calls: list[str] = field(default_factory=list)


HEADLESS_NOTE = ("\n\nHEADLESS RUN: this process exits as soon as your turn ends. Run every Agent/subagent call in "
                 "the foreground (run_in_background: false; several Agent calls in ONE message still run in "
                 "parallel) and never end your turn while a subagent, background command or task is still "
                 "running: wait for all of them, check their files, then finish.")


def _describe_tool(block: dict) -> str:
    name = block.get("name", "?")
    inp = block.get("input") or {}
    detail = (inp.get("file_path") or inp.get("pattern") or inp.get("command")
              or inp.get("skill") or inp.get("description") or inp.get("subagent_type") or "")
    detail = str(detail).replace(str(config.ROOT) + "/", "")
    return f"{name} {detail}"[:160]


async def run_claude(prompt: str, *, agent: str | None = None, model: str | None = None,
                     log: Callable[[str], None] = print, timeout_sec: int = 3600) -> ClaudeResult:
    claude_bin = config.find_claude_bin()
    if not claude_bin:
        return ClaudeResult(ok=False, error="claude CLI not found (set CLAUDE_BIN)")

    # Headless: the process ends when the main turn ends, killing any subagent still running in the
    # background (a whole batch of episodes was lost that way). Keep every subagent in the foreground.
    prompt += HEADLESS_NOTE
    cmd = [claude_bin, "-p", prompt, "--output-format", "stream-json", "--verbose",
           # Token-level events, so long writes show a heartbeat instead of a frozen log
           "--include-partial-messages",
           "--permission-mode", config.CLAUDE_PERMISSION_MODE,
           # No MCP connectors (claude.ai Docs, etc.): they only add context and cost here
           "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
           "--allowedTools", *config.CLAUDE_ALLOWED_TOOLS]
    if agent:
        cmd += ["--agent", agent]
    if model:
        cmd += ["--model", model]

    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(config.ROOT), stdin=asyncio.subprocess.DEVNULL,
        env={**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"},
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, limit=16 * 1024 * 1024)

    result = ClaudeResult(ok=False)
    writing = {"chars": 0, "last_log": time.monotonic()}

    async def read_stream():
        assert proc.stdout
        async for raw in proc.stdout:
            line = raw.decode(errors="replace").strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = ev.get("type")
            if kind == "stream_event":
                inner = ev.get("event") or {}
                if inner.get("type") == "message_start":
                    writing["chars"] = 0
                delta = inner.get("delta") or {}
                writing["chars"] += len(delta.get("text") or delta.get("partial_json") or delta.get("thinking") or "")
                if writing["chars"] and time.monotonic() - writing["last_log"] >= 15:
                    sub = " [sub]" if ev.get("parent_tool_use_id") else ""
                    log(f"writing{sub}... {writing['chars']:,} chars so far")
                    writing["last_log"] = time.monotonic()
                continue
            if kind == "assistant":
                writing["last_log"] = time.monotonic()
            if kind == "system" and ev.get("subtype") == "init":
                result.session_id = ev.get("session_id")
            elif kind == "assistant":
                sub = " [sub]" if ev.get("parent_tool_use_id") else ""
                for block in (ev.get("message") or {}).get("content", []):
                    if block.get("type") == "tool_use":
                        desc = _describe_tool(block)
                        result.tool_calls.append(desc)
                        log(f"tool{sub}: {desc}")
                    elif block.get("type") == "text" and block.get("text", "").strip() and not sub:
                        log("claude: " + block["text"].strip().replace("\n", " ")[:200])
            elif kind == "result":
                result.ok = not ev.get("is_error", False) and ev.get("subtype") == "success"
                result.text = ev.get("result") or ""
                result.cost_usd = ev.get("total_cost_usd") or 0.0
                result.duration_ms = ev.get("duration_ms") or 0
                result.turns = ev.get("num_turns") or 0
                result.session_id = ev.get("session_id") or result.session_id
                if not result.ok:
                    result.error = ev.get("subtype") or "error"

    try:
        await asyncio.wait_for(read_stream(), timeout=timeout_sec)
        await proc.wait()
    except asyncio.TimeoutError:
        proc.kill()
        result.ok, result.error = False, f"timeout after {timeout_sec}s"
    except asyncio.CancelledError:
        proc.kill()
        raise
    if proc.returncode not in (0, None) and not result.error:
        stderr = (await proc.stderr.read()).decode(errors="replace") if proc.stderr else ""
        result.ok, result.error = False, f"exit {proc.returncode}: {stderr[-300:]}"
    return result
