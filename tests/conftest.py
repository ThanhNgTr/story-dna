"""Shared fixtures: load the skill scripts (they live in .claude/skills, not in a package) and build a
small series session that satisfies the story contract, so tests can break one thing at a time."""

from __future__ import annotations

import atexit
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
sys.path.insert(0, str(ROOT))

# Importing app.main starts a JobManager that marks "running" jobs in config.JOBS as interrupted: point it at
# a throwaway dir before anything imports the app, so tests never touch the real data/jobs/.
from app import config  # noqa: E402

config.JOBS = Path(tempfile.mkdtemp(prefix="story-dna-test-jobs-"))
atexit.register(shutil.rmtree, config.JOBS, ignore_errors=True)


def load_script(rel: str):
    path = SKILLS / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(p: Path, data) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data, encoding="utf-8")
    return p


N = 6
LEDGER = {1: {"opened": ["Q1", "Q2"]}, 3: {"answered": ["Q2"]}, 4: {"opened": ["Q3"]},
          5: {"answered": ["Q1"]}, 6: {"answered": ["Q3"]}}
CLIMAX = {2: "minor", 3: "midpoint", 5: "final"}


def _char(i: int, tier: str, **extra) -> dict:
    return {"character_id": f"char_0{i}", "name": f"Nhân vật {i}", "tier": tier, "want": "w", "need": "n",
            "arc": {"start": "a", "end": "b"}, "voice": {"style": "s", "sample_lines": ["Câu một.", "Câu hai."]}, **extra}


def bible() -> dict:
    return {
        "main_plot": {"central_question": "q", "protagonist_goal": "g", "opposition": "o", "stakes": "s",
                      "start_state": "a", "end_state": "b",
                      "inciting_incident": {"episode": 1, "event": "e"}, "midpoint": {"episode": 3, "event": "e"},
                      "lowest_point": {"episode": 4, "event": "e"}, "climax": {"episode": 5, "event": "e"},
                      "resolution": {"episode": 6, "event": "e"}},
        "ending": {"type": "happy", "episode": N, "what_happens": "x", "protagonist_fate": "x",
                   "central_question_answer": "x", "final_image": "x"},
        "cast": [_char(1, "main", secret="s", secret_reveal_ep=4), _char(2, "supporting", relation_to_main="r"),
                 _char(3, "supporting", relation_to_main="r")],
        "world": {"setting": {"place": "p", "era": "e", "time_span": "t"},
                  "locations": [{"id": "L1", "name": "a", "look": "l", "first_ep": 1},
                                {"id": "L2", "name": "b", "look": "l", "first_ep": 3}]},
        "setting_timeline": [{"episode": e, "locations": ["L1"] if e < 3 else ["L2"], "time": "d",
                              "change": "c" if e in (1, 3, 5) else None} for e in range(1, N + 1)],
        "climaxes": [{"episode": e, "level": lv, "event": "e"} for e, lv in CLIMAX.items()],
        "ledger_plan": [
            {"id": "Q1", "question": "q", "tier": "central", "open_ep": 1, "clue_eps": [2, 3], "answer_ep": 5, "answer": "a"},
            {"id": "Q2", "question": "q", "tier": "major", "open_ep": 1, "clue_eps": [2], "answer_ep": 3, "answer": "a"},
            {"id": "Q3", "question": "q", "tier": "minor", "open_ep": 4, "clue_eps": [5], "answer_ep": 6, "answer": "a"}],
        "never_answered": [],
    }


def outline(b: dict) -> dict:
    return {"episodes": [{"episode": e, "act": 1 if e < 2 else 2 if e < 5 else 3, "main_plot_step": "m",
                          "locations": b["setting_timeline"][e - 1]["locations"], "climax": CLIMAX.get(e),
                          "ledger": LEDGER.get(e, {}), "cliffhanger_type": "resolution" if e == N else "reveal",
                          "characters": ["char_01"], **({"ending": "happy"} if e == N else {})}
                         for e in range(1, N + 1)]}


def episode(e: int, lines: list[tuple[str, str, bool]] | None = None) -> dict:
    lines = lines or [("char_01", "Anh đi đâu đấy?", False), ("char_02", "Tôi ra cổng xem thử.", False)] * 2
    return {"episode": e, "title": f"Tập {e}", "characters": {"char_01": {"name": "Vũ"}, "char_02": {"name": "Linh"}},
            "scenes": [{"id": "SC1", "location": "a", "time_of_day": "night",
                        "beats": [{"start_sec": 0, "end_sec": 10,
                                   "dialogue": [{"character": c, "line": l, "voiceover": vo} for c, l, vo in lines]}]}],
            "ledger": LEDGER.get(e, {}),
            **({"ending": {"type": "happy", "central_question_answer": "x"}} if e == N else {})}


@pytest.fixture
def session(tmp_path: Path) -> Path:
    """A complete 6-episode session at <tmp>/series/demo/S1 that passes every check."""
    d = tmp_path / "series" / "demo" / "S1"
    b = bible()
    write(d / "input.json", {"episodes": N, "episode_sec": 60, "title": "Demo"})
    write(d / "bible_v1.json", b)
    write(d / "bible_v1.md", "# bible")
    write(d / "outline_v1.json", outline(b))
    write(d / "outline_v1.md", "# outline")
    for e in range(1, N + 1):
        write(d / "episodes" / f"ep{e:02d}_v1.json", episode(e))
        write(d / "episodes" / f"ep{e:02d}_v1.md", f"# EP{e:02d}")
    return d
