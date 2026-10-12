"""Story editor review validator and the Vietnamese dialogue lint."""

import json

from conftest import episode, load_script, write

ed = load_script("story-editor/_editor.py")
dl = load_script("dialogue-polish/_dialogue_lint.py")


def review(**over):
    r = {"version": 1, "stage": "outline", "summary": "s", "theme_statement": "t",
         "scores": {d: {"score": 4, "why": "w", "evidence": ["x"]} for d in ed.DIMENSIONS},
         "average": 4.0, "verdict": "pass",
         "findings": [{"id": "F1", "dimension": "theme", "severity": "high", "where": {"file": "bible_v1.json"},
                       "evidence": "e", "problem": "p", "fix": "f"}],
         "strengths": ["a", "b"]}
    r.update(over)
    return r


def test_valid_review(tmp_path):
    assert ed.validate(write(tmp_path / "r.json", review())) == 0


def test_verdict_must_match_scores(tmp_path):
    r = review()
    r["scores"]["antagonist"]["score"] = 2  # one score under 3 -> revise
    r["average"] = round((4 * 8 + 2) / 9, 1)
    assert ed.validate(write(tmp_path / "r.json", r)) == 1
    r["verdict"] = "revise"
    assert ed.validate(write(tmp_path / "r.json", r)) == 0


def test_high_score_needs_evidence(tmp_path):
    r = review()
    r["scores"]["theme"]["evidence"] = []
    assert ed.validate(write(tmp_path / "r.json", r)) == 1


def test_next_and_latest_versions(tmp_path):
    assert ed.next_version(tmp_path) == 1
    write(tmp_path / "editor" / "review_v1.json", review())
    write(tmp_path / "editor" / "review_v3.json", review())
    assert ed.next_version(tmp_path) == 4
    assert ed.latest(tmp_path).name == "review_v3.json"


def lint_items(session, lines):
    write(session / "episodes" / "ep01_v2.json", episode(1, lines))
    dl.lint(session, set())
    rep = json.loads((session / "dialogue_check.json").read_text(encoding="utf-8"))
    return [it for it in rep["items"] if it["episode"] == 1]


def test_telegraphic_lines_are_flagged(session):
    items = lint_items(session, [("char_01", "Một tấm rèm. Sáu căn nhà trả.", True),
                                 ("char_02", "Chỉ vì một tấm rèm bị mở, cả sáu căn nhà phải chịu phạt.", False)])
    assert [it["line"] for it in items] == ["Một tấm rèm. Sáu căn nhà trả."]


def test_shouts_questions_and_machine_voices_are_not_flagged(session):
    items = lint_items(session, [("char_01", "Ra đây! Vũ!", False), ("char_02", "Ông nghe chưa? Đi đâu?", False),
                                 ("unknown_voice", "Phòng hai. Mất tín hiệu.", False)])
    assert items == []


def test_vo_pronoun_switch_is_flagged(session):
    items = lint_items(session, [("char_01", "Tôi biết nét chữ này rất rõ.", True),
                                 ("char_01", "Tao không tin cái nhà này.", True)])
    assert any("pronoun" in it["issues"] for it in items)


def test_clock_from_a_character(session):
    items = lint_items(session, [("char_02", "Hai mươi hai giờ thì đóng rèm lại nhé.", False)])
    assert any("clock" in it["issues"] for it in items)


def test_examples_collects_hand_edits(tmp_path, monkeypatch):
    d = tmp_path / "data" / "series" / "a" / "s1" / "episodes"
    write(d / "ep01_v1.json", episode(1, [("char_01", "Một tấm rèm. Sáu căn nhà trả.", True)]))
    edited = episode(1, [("char_01", "Chỉ vì một tấm rèm bị mở, cả sáu căn nhà phải chịu phạt.", True)])
    edited["edited"] = {"by": "manual", "from_version": 1, "at": "2026-10-09T05:00:00Z"}
    write(d / "ep01_v2.json", edited)
    monkeypatch.setattr(dl, "ROOT", tmp_path)
    dl.examples()
    ex = json.loads((tmp_path / "data" / "dialogue_examples.json").read_text(encoding="utf-8"))["examples"]
    assert len(ex) == 1 and ex[0]["before"].startswith("Một tấm rèm")


def _finding(fid, sev, file, affects):
    return {"id": fid, "dimension": "theme", "severity": sev, "where": {"file": file}, "evidence": "e",
            "problem": "p", "fix": "f", "affects": affects}


def test_apply_plan_resolves_files_and_packages(session):
    import os
    import time
    write(session / "editor" / "review_v1.json", review(findings=[
        _finding("F1", "high", "bible_v1.json", ["bible", "outline", "ep02", "ep05"]),
        _finding("F2", "medium", "episodes/ep05_v1.json", ["ep05", "ep06"]),
        _finding("F3", "low", "episodes/ep01_v1.json", ["ep01"]),
        _finding("F4", "medium", "episodes/ep01_v1.json", ["ep01"])]))
    write(session / "input.json", {"episodes": 6, "episode_sec": 60, "produced_upto": 1})
    fin = write(session / "final" / "ep02.json", episode(2))  # newer than the draft -> source
    t = time.time()
    os.utime(session / "episodes" / "ep02_v1.json", (t - 60, t - 60))
    os.utime(fin, (t, t))
    assert ed.plan(session) == 0  # default: high + medium
    p = json.loads((session / "editor" / "apply_plan.json").read_text())
    assert p["findings"] == ["F1", "F2", "F4"]
    assert p["docs"]["bible"] == {"source": "bible_v1.json", "target": "bible_v2.json", "findings": ["F1"]}
    assert p["episodes"]["2"] == {"source": "final/ep02.json", "target": "episodes/ep02_v2.json", "findings": ["F1"]}
    assert p["episodes"]["5"]["findings"] == ["F1", "F2"]
    assert "1" not in p["episodes"] and p["skipped"][0]["episode"] == 1  # produced = canon
    assert sorted(n for pk in p["packages"] for n in pk["episodes"]) == [2, 5, 6]
    assert 1 <= len(p["packages"]) <= ed.MAX_PACKAGES


def test_apply_plan_rejects_unknown_ids(session):
    write(session / "editor" / "review_v1.json", review())
    assert ed.plan(session, "F1,F9") == 1
    assert ed.plan(session, "all") == 0


def test_packages_are_capped_and_balanced():
    eps = {n: [f"F{n}"] * (8 if n == 10 else 1) for n in range(1, 11)}
    pks = ed._packages(eps)
    assert len(pks) == ed.MAX_PACKAGES
    assert [10] in [pk["episodes"] for pk in pks]  # the heavy episode gets its own writer
    assert sorted(n for pk in pks for n in pk["episodes"]) == list(range(1, 11))


def test_render_writes_md(session):
    p = session / "episodes" / "ep03_v1.json"
    assert ed.render([p]) == 0
    assert (session / "episodes" / "ep03_v1.md").read_text().startswith("# EP03")


def test_definition_lines_are_flagged(session):
    b = json.loads((session / "bible_v1.json").read_text())
    b["glossary"] = [{"term": "phiếu nhập vật tư", "plain": "tờ giấy ghi lô hàng"}]
    write(session / "bible_v1.json", b)
    items = lint_items(session, [
        ("char_01", "Giàn giáo là khung ống thép cho thợ đứng làm trên cao.", True),
        ("char_01", "Tôi làm phụ hồ, tức là trộn vữa cho thợ chính.", True),
        ("char_01", "Phiếu nhập vật tư là cái mà ai cũng phải ký.", True),
        # identity / plain speech is not a definition
        ("char_02", "Anh là người kéo tôi ra hôm qua mà.", False),
        ("char_02", "Bác Hữu chỉ cần một cuộc gọi là anh hết đường làm.", False)])
    flagged = [it["line"] for it in items if "definition" in it["issues"]]
    assert len(flagged) == 3 and not any(x.startswith(("Anh là", "Bác")) for x in flagged)


def test_vo_retelling_the_action_is_flagged(session):
    ep = episode(1, [("char_01", "Sáng hôm đó ông Hữu dẫn Vy đi qua bãi cát xem công trình.", True),
                     ("char_02", "Ông Hữu dẫn Vy đi qua bãi cát xem công trình.", False)])
    ep["scenes"][0]["beats"][0]["action"] = "Ông Hữu dẫn Vy đi qua bãi cát, công nhân dạt ra hai bên"
    write(session / "episodes" / "ep01_v2.json", ep)
    assert dl.lint(session, {1}) == 0
    items = json.loads((session / "dialogue_check.json").read_text())["items"]
    narr = [it for it in items if "narrates_action" in it["issues"]]
    assert len(narr) == 1 and narr[0]["voiceover"]  # spoken lines are judged by other rules
