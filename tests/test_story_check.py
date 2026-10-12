"""Story contract checker (.claude/skills/story-contract/_story_check.py)."""

import json

from conftest import load_script

sc = load_script("story-contract/_story_check.py")


def run(d, stage=None):
    report, _ = sc.run(d, stage)
    return report.errors


def edit(path, fn):
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_complete_session_passes(session):
    assert run(session) == []


def test_outline_stage_ignores_episodes(session):
    for f in (session / "episodes").glob("*.json"):
        f.unlink()
    assert run(session, "outline") == []


def test_missing_ending_is_r1(session):
    edit(session / "bible_v1.json", lambda b: b.pop("ending"))
    assert any(e.startswith("[R1]") for e in run(session))


def test_ending_must_be_happy_or_bad(session):
    edit(session / "bible_v1.json", lambda b: b["ending"].update(type="open"))
    assert any("happy or bad" in e for e in run(session))


def test_last_episode_must_resolve(session):
    def no_resolution(o):
        o["episodes"][-1]["cliffhanger_type"] = "reveal_cut_short"
    edit(session / "outline_v1.json", no_resolution)
    assert any("must be 'resolution'" in e for e in run(session))


def test_needs_two_supporting_characters(session):
    edit(session / "bible_v1.json", lambda b: b["cast"].pop())
    assert any(e.startswith("[R3]") and "supporting" in e for e in run(session))


def test_episode_without_dialogue_fails_r4(session):
    p = session / "episodes" / "ep03_v1.json"
    edit(p, lambda ep: ep["scenes"][0]["beats"][0].update(dialogue=[]))
    assert any(e.startswith("[R4]") and "ep03" in e for e in run(session))


def test_setting_must_change(session):
    edit(session / "bible_v1.json", lambda b: [r.update(change=None) for r in b["setting_timeline"]])
    assert any("setting changes only" in e for e in run(session))


def test_gap_without_climax_fails_r6(session):
    def spread(b):
        b["climaxes"] = [{"episode": 3, "level": "midpoint", "event": "e"}, {"episode": 5, "level": "final", "event": "e"}]
    edit(session / "bible_v1.json", spread)
    # outline must agree, otherwise R6 fires for the mismatch instead
    edit(session / "outline_v1.json", lambda o: o["episodes"][1].update(climax=None))
    errs = run(session)
    assert not any("max 3 episodes" in e for e in errs)  # ep1-2 is a gap of 2: allowed


def test_unanswered_central_question_fails_r7(session):
    edit(session / "bible_v1.json", lambda b: b.update(never_answered=["Q1"]))
    assert any("only a minor question may stay unanswered" in e for e in run(session))


def test_one_minor_sequel_hook_is_allowed(session):
    def hook(b):
        b["never_answered"] = ["Q3"]
    edit(session / "bible_v1.json", hook)
    for f in ("outline_v1.json",):
        edit(session / f, lambda o: o["episodes"][-1]["ledger"].update(answered=[]))
    edit(session / "episodes" / "ep06_v1.json", lambda ep: ep["ledger"].update(answered=[]))
    assert not any(e.startswith("[R7]") for e in run(session))


def test_clue_outside_open_answer_range(session):
    edit(session / "bible_v1.json", lambda b: b["ledger_plan"][1].update(clue_eps=[5]))
    assert any("clue ep5 outside" in e for e in run(session))


def test_older_field_names_are_accepted(session):
    def rename(b):
        b["characters"] = b.pop("cast")
        b["mystery_ledger"] = b.pop("ledger_plan")
    edit(session / "bible_v1.json", rename)
    assert run(session) == []
