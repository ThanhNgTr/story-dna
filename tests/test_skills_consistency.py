"""Skills are code: frontmatter, commands and shared rules must stay consistent (no Claude needed)."""

import json
import re
from pathlib import Path

import yaml

from conftest import SKILLS, episode, load_script, write

SKILL_FILES = sorted(SKILLS.glob("*/SKILL.md"))
ROOT = SKILLS.parents[1]


def test_frontmatter_parses_and_name_matches_folder():
    assert SKILL_FILES
    for f in SKILL_FILES:
        fm = yaml.safe_load(f.read_text(encoding="utf-8").split("---")[1])
        assert fm["name"] == f.parent.name, f


def test_no_shell_variables_in_commands():
    """Headless runs allow only commands that start with python3; variables do not carry over."""
    for f in SKILL_FILES:
        text = f.read_text(encoding="utf-8")
        assert not re.search(r"`[^`]*(\$\(|\$[A-Z]\b)[^`]*`", text), f


def test_every_referenced_skill_script_exists():
    for f in [*SKILL_FILES, *SKILLS.glob("*/references/*.md")]:
        for rel in re.findall(r"\.claude/skills/[\w./-]+\.(?:py|md)", f.read_text(encoding="utf-8")):
            if "<" not in rel and "write-series-<slug>" not in rel:
                assert (ROOT / rel).exists(), f"{f}: {rel}"


def test_speech_rate_has_one_source():
    """Writers, polish and shotlist all point at vi-dialogue.md "Speech rate" (no stray words/sec caps)."""
    guide = (SKILLS / "dialogue-polish/references/vi-dialogue.md").read_text(encoding="utf-8")
    assert "## Speech rate" in guide and "5.0 syllables/s" in guide
    for name in ("dialogue-polish", "script-to-shotlist", "write-series-fantasy-romance-h"):
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert "Speech rate" in text, name
        for stale in ("max ~2.5 words/sec", "beat duration x 3.5", "~330 words per 90s (reference is TTS-read; the dialogue"):
            assert stale not in text, (name, stale)


def test_style_skill_maps_acts_to_the_contract():
    text = (SKILLS / "write-series-fantasy-romance-h/SKILL.md").read_text(encoding="utf-8")
    assert "Outline `act` field" in text
    for field in ('"logline"', '"story_beats"', '"cliffhanger_type"', '"outfits"'):
        assert field in text, field


def test_iterations_helper_keeps_history_in_both_shapes(tmp_path):
    from app.pipeline import iterations
    d = tmp_path / "slug" / "S1"
    d.mkdir(parents=True)
    write(d / "iterations.json", {"session": "S1", "slug": "slug", "rounds": [{"round": 1, "stage": "assets"}]})
    iterations.append(d, {"stage": "final"})
    doc = json.loads((d / "iterations.json").read_text())
    assert [r["round"] for r in doc["rounds"]] == [1, 2] and doc["slug"] == "slug"
    write(d / "iterations.json", [{"round": 4, "stage": "outline"}])
    iterations.append(d, {"stage": "episodes", "round": 99})
    assert [r["round"] for r in iterations.load(d)] == [4, 5]
    (d / "iterations.json").write_text("{broken")
    iterations.append(d, {"stage": "x"})
    assert list(d.glob("iterations.broken-*.json")) and len(iterations.load(d)) == 1


def test_archive_keeps_dict_history(session, monkeypatch):
    """Regression: archiving episodes once replaced a {"rounds": [...]} history with one round."""
    from app import config
    monkeypatch.setattr(config, "SERIES", session.parents[1])
    from app.pipeline import series
    write(session / "iterations.json", {"session": "S1", "slug": "demo", "rounds": [{"round": 1, "stage": "assets"},
                                                                                   {"round": 2, "stage": "outline"}]})
    assert len(series.session_state("demo", "S1")["iterations"]) == 2
    series.archive_episodes("demo", "S1", [6])
    rounds = json.loads((session / "iterations.json").read_text())["rounds"]
    assert [r["stage"] for r in rounds] == ["assets", "outline", "episodes"]


def test_too_fast_and_comma_episode_list(session):
    dl = load_script("dialogue-polish/_dialogue_lint.py")
    ep = episode(2, [("char_01", "Mày mời con gái ông chủ thiệt hả trời ơi chết tao rồi mày ơi là mày", False)])
    ep["scenes"][0]["beats"][0]["end_sec"] = 2
    write(session / "episodes" / "ep02_v2.json", ep)
    assert dl.main(["lint", str(session), "2,3"]) == 0
    items = json.loads((session / "dialogue_check.json").read_text())["items"]
    assert any("too_fast" in it["issues"] and it["episode"] == 2 for it in items)


def test_render_md_matches_skill_format():
    from app.pipeline.screenplay import render_md
    ep = episode(1)
    ep["scenes"][0].update({"int_ext": "INT", "location": "phòng ăn", "time_of_day": "night", "loc_id": "loc_04",
                            "variant_id": "loc_04_night", "cast": {"char_01": "char_01_o1"}, "props": ["prop_02"]})
    md = render_md(ep)
    assert "INT. PHÒNG ĂN — ĐÊM  {loc_04 · loc_04_night · char_01:o1}" in md
    assert "Props: prop_02" in md and "| Time | Shot |" in md and "| # |" not in md
