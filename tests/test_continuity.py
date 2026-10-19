"""Continuity checker (.claude/skills/story-continuity/_continuity.py)."""

import json

import pytest

from conftest import N, load_script, write

cc = load_script("story-continuity/_continuity.py")
LINES = {e: [f"Tập {e} mở bằng câu này", f"Tập {e} kết bằng câu kia"] for e in range(1, N + 1)}


def edit(path, fn):
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _episode(e: int) -> dict:
    """Two scenes: SC1 opens with LINES[e][0], SC2 ends with LINES[e][1]; char_01 + char_02 on screen."""
    def scene(sid, line, props):
        return {"id": sid, "location": "a", "time_of_day": "day", "cast": {"char_01": "o1", "char_02": "o1"},
                "props": props, "beats": [{"start_sec": 0, "end_sec": 4, "characters": ["char_01", "char_02"],
                                           "action": f"Vũ cầm chiếc chìa khóa đồng ({sid})",
                                           "dialogue": [{"character": "char_01", "line": line},
                                                        {"character": "char_02", "line": "Ừ, em nghe."}]}]}
    return {"episode": e, "title": f"Tập {e}", "characters": {"char_01": {}, "char_02": {}},
            "scenes": [scene("SC1", LINES[e][0], ["prop_01"]), scene("SC2", LINES[e][1], [])],
            "cliffhanger": f"Cửa bật mở ở tập {e}"}


def _state() -> dict:
    eps = {str(e): f"episodes/ep{e:02d}_v1.json" for e in range(1, N + 1)}
    return {
        "version": 1, "built_from": {"bible": "bible_v1.json", "outline": "outline_v1.json", "episodes": eps},
        "facts": [{"id": "F1", "text": "Vũ là con nuôi", "ep": 0, "kind": "backstory"},
                  {"id": "F2", "text": "chìa khóa mở kho", "ep": 2, "scene": "SC1", "quote": LINES[2][0]}],
        "knowledge": [{"character": "char_01", "fact": "F1", "ep": 0},
                      {"character": "char_02", "fact": "F1", "ep": 3, "scene": "SC2", "quote": LINES[3][1]}],
        "uses": [{"character": "char_02", "fact": "F1", "ep": 4, "scene": "SC1", "quote": LINES[4][0]}],
        "status": [], "props": [{"prop": "prop_01", "ep": 1, "scene": "SC1", "holder": "char_01", "status": "with",
                                 "quote": "chìa khóa đồng"}],
        "relations": [{"pair": ["char_01", "char_02"], "ep": 1, "scene": "SC1", "state": "lạ", "quote": LINES[1][0]},
                      {"pair": ["char_01", "char_02"], "ep": 3, "scene": "SC2", "state": "tin nhau",
                       "cause": "Linh nhận lỗi", "quote": LINES[3][1]}],
        "clock": [{"ep": e, "day": e, "time": "sáng"} for e in range(1, N + 1)],
        "clues": [{"question": q, "ep": c, "scene": "SC1", "clue": "c", "quote": LINES[c][0]}
                  for q, cs in (("Q1", [2, 3]), ("Q2", [2]), ("Q3", [5])) for c in cs],
        "setups": [{"id": "S1", "plant": "chìa khóa", "ep": 1, "scene": "SC1", "quote": "chìa khóa đồng",
                    "payoff": "mở kho", "payoff_ep": 5, "payoff_scene": "SC2", "payoff_quote": LINES[5][1]}],
        "seams": [{"ep": e, "cliffhanger_quote": LINES[e - 1][1], "opening_quote": LINES[e][0], "link": "continues"}
                  for e in range(2, N + 1)],
    }


@pytest.fixture
def cs(session):
    """The shared session plus a cause chain in the outline, two-scene episodes and a matching state ledger."""
    def chain(o):
        for row in o["episodes"]:
            e = row["episode"]
            row["events"] = [{"id": f"E{e}.1", "text": f"việc {e}"}]
            if e > 1:
                row["because"], row["opens_from"] = [f"E{e - 1}.1"], "tiếp ngay khung cuối"
    edit(session / "outline_v1.json", chain)
    for e in range(1, N + 1):
        p = session / "episodes" / f"ep{e:02d}_v1.json"
        edit(p, lambda ep, e=e: ep.update({k: v for k, v in _episode(e).items() if k != "characters"}))
    write(session / "continuity" / "state_v1.json", _state())
    return session


def run(d, stage=None):
    report, _ = cc.run(d, stage)
    return report.errors


def test_consistent_session_passes(cs):
    assert run(cs) == []


def test_story_contract_still_passes(cs):
    sc = load_script("story-contract/_story_check.py")
    assert sc.run(cs, None)[0].errors == []


def test_outline_needs_cause_chain(cs):
    edit(cs / "outline_v1.json", lambda o: o["episodes"][3].pop("because"))
    assert any("outline ep4: because is empty" in e for e in run(cs, "outline"))


def test_cause_must_be_an_earlier_event(cs):
    edit(cs / "outline_v1.json", lambda o: o["episodes"][2].update(because=["E5.1"]))
    assert any("ep3: because E5.1 is in ep5" in e for e in run(cs, "outline"))


def test_dead_end_episode_warns(cs):
    edit(cs / "outline_v1.json", lambda o: o["episodes"][2].update(because=["E1.1"]))
    report, _ = cc.run(cs, "outline")
    assert report.errors == [] and any("ep2: no later episode" in w for w in report.warns)


def test_outline_stage_needs_no_ledger(cs):
    (cs / "continuity" / "state_v1.json").unlink()
    assert run(cs, "outline") == []
    assert any(e.startswith("[C0]") for e in run(cs))


def test_ledger_must_cover_new_episode(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["built_from"]["episodes"].pop("6"))
    assert any("does not cover ep06" in e for e in run(cs))


def test_rewritten_episode_keeps_ledger_when_quotes_match(cs):
    write(cs / "episodes" / "ep03_v2.json", _episode(3))
    report, _ = cc.run(cs, None)
    assert report.errors == [] and any("ep03_v1.json, current is episodes/ep03_v2.json" in w for w in report.warns)


def test_quote_must_be_in_the_episode(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["uses"][0].update(quote="câu không có trong tập"))
    assert any(e.startswith("[C2]") and "not found in ep04.SC1" in e for e in run(cs))


def test_use_before_learning_is_an_error(cs):
    edit(cs / "continuity" / "state_v1.json",
         lambda s: s["uses"].append({"character": "char_02", "fact": "F1", "ep": 2, "scene": "SC2", "quote": LINES[2][1]}))
    assert any("char_02 uses F1 in ep02.SC2 before learning it in ep03" in e for e in run(cs))


def test_same_episode_scene_order_counts(cs):
    edit(cs / "continuity" / "state_v1.json",
         lambda s: s["uses"].append({"character": "char_02", "fact": "F1", "ep": 3, "scene": "SC1", "quote": LINES[3][0]}))
    assert any("before learning it in ep03" in e for e in run(cs))


def test_use_without_any_learning(cs):
    edit(cs / "continuity" / "state_v1.json",
         lambda s: s["uses"].append({"character": "char_01", "fact": "F2", "ep": 5, "scene": "SC1", "quote": LINES[5][0]}))
    assert any("char_01 uses F2 in ep05" in e and "never learns" in e for e in run(cs))


def test_gone_character_on_screen_without_return(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["status"].append(
        {"character": "char_02", "ep": 4, "scene": "SC2", "status": "gone", "quote": LINES[4][1]}))
    assert any("char_02 is gone since ep04 but on screen in ep05.SC1" in e for e in run(cs))


def test_return_row_and_flashback_clear_status(cs):
    def gone_and_back(s):
        s["status"] += [{"character": "char_02", "ep": 4, "scene": "SC2", "status": "gone", "quote": LINES[4][1]},
                        {"character": "char_02", "ep": 6, "scene": "SC1", "status": "back", "quote": LINES[6][0]}]
    edit(cs / "continuity" / "state_v1.json", gone_and_back)
    edit(cs / "episodes" / "ep05_v1.json", lambda ep: [sc.update(flashback=True) for sc in ep["scenes"]])
    assert run(cs) == []


def test_destroyed_prop_cannot_come_back(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["props"].append(
        {"prop": "prop_01", "ep": 3, "scene": "SC2", "holder": None, "status": "destroyed", "quote": LINES[3][1]}))
    assert any("prop_01 is destroyed since ep03 but in ep04.SC1 props" in e for e in run(cs))


def test_relation_change_needs_cause(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["relations"][1].pop("cause"))
    assert any(e.startswith("[C8]") for e in run(cs))


def test_clock_cannot_run_backwards(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["clock"][3].update(day=2))
    assert any("ep04 is day 2, before ep03" in e for e in run(cs))
    edit(cs / "continuity" / "state_v1.json", lambda s: s["clock"][3].update(flashback=True))
    assert not any("[C5]" in e for e in run(cs))


def test_clock_matches_setting_timeline_day(cs):
    edit(cs / "bible_v1.json", lambda b: b["setting_timeline"][1].update(time="ngày 5, tối"))
    assert any("ep02: bible setting_timeline says day 5" in e for e in run(cs))


def test_every_seam_is_tied(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["seams"].pop(2))
    assert any("no seam row for ep03 -> ep04" in e for e in run(cs))


def test_seam_quotes_come_from_the_right_scenes(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["seams"][0].update(opening_quote=LINES[2][1]))
    assert any("opening_quote" in e and "first scene of ep02" in e for e in run(cs))


def test_cut_away_cliffhanger_must_be_resolved(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["seams"][1].update(link="time_jump"))
    assert any("ep02 cliffhanger is cut away" in e for e in run(cs))
    edit(cs / "continuity" / "state_v1.json", lambda s: s["seams"][1].update(resolved_ep=3))
    assert run(cs) == []


def test_planned_clue_must_be_on_screen(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s.update(clues=[c for c in s["clues"] if c["ep"] != 3]))
    assert any("Q1: clue planned in ep03 is not on screen" in e for e in run(cs))


def test_plant_without_payoff(cs):
    edit(cs / "continuity" / "state_v1.json", lambda s: s["setups"][0].update(payoff_ep=None))
    assert any("setup S1" in e and "never paid off" in e for e in run(cs))
    edit(cs / "continuity" / "state_v1.json", lambda s: s["setups"][0].update(sequel_hook=True))
    assert run(cs) == []


def test_impact_lists_dependent_episodes(cs, capsys):
    assert cc.main(["impact", str(cs), "--episodes", "3"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    deps = out["depends"]
    assert any("char_02 uses F1" in w for w in deps["4"])      # learned F1 in ep03, uses it in ep04
    assert any("because E3.1" in w for w in deps["4"])
    assert any("seam with ep03" in w for w in deps["2"])
    assert any("answers Q1" in w for w in deps["5"])           # Q1 clued in ep03, answered in ep05
    assert "3" not in deps


def test_impact_by_fact(cs, capsys):
    assert cc.main(["impact", str(cs), "--facts", "F1"]) == 0
    deps = json.loads(capsys.readouterr().out.strip().splitlines()[-1])["depends"]
    assert set(deps) == {"3", "4"}


def test_check_writes_report_and_exit_code(cs):
    assert cc.main(["check", str(cs)]) == 0
    rep = json.loads((cs / "continuity_check.json").read_text())
    assert rep["ok"] and rep["state"] == "continuity/state_v1.json"
    edit(cs / "outline_v1.json", lambda o: o["episodes"][1].pop("opens_from"))
    assert cc.main(["check", str(cs)]) == 1


def test_next_render_and_validate(cs, capsys):
    assert cc.main(["next", str(cs), "state"]) == 0 and capsys.readouterr().out.strip() == "2"
    assert cc.main(["render", str(cs / "continuity" / "state_v1.json")]) == 0
    assert "## Who knows what" in (cs / "continuity" / "state_v1.md").read_text()
    review = {"stage": "episodes", "summary": "s", "verdict": "revise",
              "findings": [{"id": "L1", "kind": "coincidence", "severity": "high", "evidence": "\"...\"",
                            "problem": "p", "fix": "f", "where": {"file": "episodes/ep04_v1.json", "episode": 4}}]}
    p = write(cs / "continuity" / "logic_v1.json", review)
    assert cc.main(["validate", str(p)]) == 0
    review["verdict"] = "pass"
    write(p, review)
    assert cc.main(["validate", str(p)]) == 1


def test_editor_plan_takes_the_logic_review(cs):
    ed = load_script("story-editor/_editor.py")
    write(cs / "continuity" / "logic_v1.json", {"stage": "episodes", "summary": "s", "verdict": "revise", "findings": [
        {"id": "L1", "kind": "cause_missing", "severity": "high", "where": {"file": "episodes/ep04_v1.json", "episode": 4},
         "evidence": "e", "problem": "p", "fix": "f", "affects": ["ep03", "ep04", "outline"]}]})
    assert ed.main(["plan", str(cs), "all", "--review", str(cs / "continuity" / "logic_v1.json")]) == 0
    plan = json.loads((cs / "continuity" / "apply_plan.json").read_text())
    assert plan["review"] == "continuity/logic_v1.json" and plan["notes_file"] == "continuity/apply_notes.json"
    assert sorted(plan["episodes"]) == ["3", "4"] and plan["episodes"]["4"]["target"] == "episodes/ep04_v2.json"
    assert plan["docs"]["outline"]["target"] == "outline_v2.json"
    assert not (cs / "editor" / "apply_plan.json").exists()
