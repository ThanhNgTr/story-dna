"""App side: final/ staleness + re-finalize, per-series settings, and the video package zip."""

import json
import os
import time
import zipfile

import pytest

from conftest import episode, write


@pytest.fixture
def app_session(session, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "SERIES", session.parents[1])
    from app.pipeline import series
    return series, session


def finalize(d):
    """What /refine-skill --approve leaves behind: copies of the latest files in final/."""
    for src, dst in [("bible_v1.json", "bible.json"), ("outline_v1.json", "outline.json")] + \
                    [(f"episodes/ep{e:02d}_v1.json", f"ep{e:02d}.json") for e in range(1, 7)] + \
                    [(f"episodes/ep{e:02d}_v1.md", f"ep{e:02d}.md") for e in range(1, 7)]:
        write(d / "final" / dst, (d / src).read_text(encoding="utf-8"))


def age(path, sec=60):
    t = time.time() - sec
    os.utime(path, (t, t))


def test_final_is_current_right_after_approve(app_session):
    series, d = app_session
    finalize(d)
    st = series.session_state("demo", "S1")
    assert st["final_stale"] == [] and st["final_complete"]


def test_edit_after_final_is_detected_and_refinalized(app_session):
    series, d = app_session
    finalize(d)
    for f in (d / "final").glob("*"):
        age(f)
    write(d / "episodes" / "ep03_v2.json", episode(3, [("char_01", "Câu mới hơn hẳn.", False)] * 4))
    write(d / "episodes" / "ep03_v2.md", "# EP03 v2")
    st = series.session_state("demo", "S1")
    assert st["final_stale"] == [3] and not st["final_complete"]
    out = series.refinalize("demo", "S1")
    assert "final/ep03.json" in out["copied"]
    st = series.session_state("demo", "S1")
    assert st["final_stale"] == [] and st["final_complete"]
    assert st["iterations"][-1]["stage"] == "final"


def test_touch_without_change_is_not_stale(app_session):
    series, d = app_session
    finalize(d)
    for f in (d / "final").glob("*"):
        age(f)
    (d / "episodes" / "ep02_v1.json").touch()  # newer mtime, same bytes
    assert series.session_state("demo", "S1")["final_stale"] == []


def test_settings_defaults_and_save(app_session):
    series, d = app_session
    assert series.session_settings(d) == {"auto_editor_outline": True, "auto_editor_episodes": False}
    series.save_settings(d, {"auto_editor_episodes": True, "unknown": True})
    assert series.session_settings(d)["auto_editor_episodes"] is True
    assert "unknown" not in json.loads((d / "input.json").read_text())["settings"]


def test_outline_approved_needs_a_real_approval(app_session):
    series, d = app_session
    for f in (d / "episodes").glob("*"):
        f.unlink()
    write(d / "iterations.json", [{"round": 1, "stage": "story_editor", "feedback_raw": "outline fixes",
                                   "status": "approved"}])
    assert not series.session_state("demo", "S1")["outline_approved"]
    write(d / "iterations.json", [{"round": 1, "stage": "outline", "feedback_raw": "approve outline"}])
    assert series.session_state("demo", "S1")["outline_approved"]


def test_video_package(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    img = write(d / "assets" / "characters" / "char_01" / "char_01_sheet_v1.png", "PNG" * 400)
    write(d / "assets" / "images.json", {"items": {"char_01": {"kind": "character", "images": [
        {"file": str(img.relative_to(d / "assets")), "status": "approved"}]}}})
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 3, "characters": ["char_01"], "refs": [],
         "dialogue": [{"character": "char_01", "line": "Anh đi đâu đấy?"}], "video_prompt": "PROMPT ONE"},
        {"shot_number": 2, "start_sec": 3, "end_sec": 5, "characters": [], "dialogue": [], "video_prompt": "PROMPT TWO"}]})
    assert not package.prompts_stale(d, 1)
    path, name = package.build_episode_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        names = z.namelist()
        root = names[0].split("/")[0]
        assert name.endswith("_higgsfield.zip")
        assert f"{root}/refs/char_01_vu_sheet_v1.png" in names
        shot1 = z.read(f"{root}/prompts/clip_01.txt").decode()
        assert "PROMPT ONE" in shot1 and "refs/char_01_vu_sheet_v1.png" in shot1
        assert "Anh đi đâu đấy?" in z.read(f"{root}/subtitles.srt").decode()
        assert "clip_02.mp4" in z.read(f"{root}/edit_list.csv").decode("utf-8-sig")
    finally:
        path.unlink()


def test_prompts_go_stale_after_refinalize(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    for f in (d / "final").glob("*"):
        age(f, 120)
    p = write(d / "final" / "shots" / "ep03" / "prompts.json", {"unit": "clip", "shots": []})
    age(p, 60)
    write(d / "episodes" / "ep03_v2.json", episode(3, [("char_01", "Câu mới hơn hẳn.", False)] * 4))
    write(d / "episodes" / "ep03_v2.md", "# v2")
    age(d / "episodes" / "ep03_v2.json", 30)
    assert not package.prompts_stale(d, 3)
    series.refinalize("demo", "S1")
    assert package.prompts_stale(d, 3)


def test_assets_rebuilt_after_final_are_stale_and_refinalized(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    write(d / "assets" / "assets_v1.json", {"characters": [{"id": "char_01", "outfit": "xám"}]})
    write(d / "final" / "assets.json", (d / "assets" / "assets_v1.json").read_text(encoding="utf-8"))
    for f in (d / "final").glob("*"):
        age(f, 120)
    p = write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "shots": []})
    age(p, 60)
    write(d / "assets" / "assets_v2.json", {"characters": [{"id": "char_01", "outfit": "đỏ"}]})
    write(d / "assets" / "assets_v2.md", "# looks v2")
    age(d / "assets" / "assets_v2.json", 30)
    st = series.session_state("demo", "S1")
    assert st["final_stale"] == ["assets"] and not st["final_complete"]
    out = series.refinalize("demo", "S1")
    assert {"final/assets.json", "final/assets.md", "final/series.md"} <= set(out["copied"])
    assert "đỏ" in (d / "final" / "assets.json").read_text(encoding="utf-8")
    assert series.session_state("demo", "S1")["final_stale"] == []
    assert package.prompts_stale(d, 1)  # prompts used the old looks


def test_refinalize_rebuilds_series_index(app_session):
    series, d = app_session
    finalize(d)
    write(d / "final" / "series.md", "OLD INDEX")
    for f in (d / "final").glob("*"):
        age(f)
    write(d / "episodes" / "ep03_v2.json", episode(3, [("char_01", "Câu mới hơn hẳn.", False)] * 4))
    write(d / "episodes" / "ep03_v2.md", "# EP03 BẢN MỚI")
    series.refinalize("demo", "S1")
    idx = (d / "final" / "series.md").read_text(encoding="utf-8")
    assert "OLD INDEX" not in idx and "# EP03 BẢN MỚI" in idx and "[ep06.md](ep06.md)" in idx


def test_saved_report_is_dropped_when_the_checker_changes(app_session, tmp_path):
    series, d = app_session
    checker = write(tmp_path / "_check.py", "# checker")
    rep = write(d / "story_check.json", {"ok": True, "stage": "episodes"})
    age(checker, 30)
    assert series._report_current(rep, d, checker, "episodes") == {"ok": True, "stage": "episodes"}
    checker.touch()
    assert series._report_current(rep, d, checker, "episodes") is None


def test_outline_not_marked_approved_when_nothing_to_write(app_session):
    import asyncio
    from types import SimpleNamespace
    series, d = app_session
    job = SimpleNamespace(data={"params": {"slug": "demo", "session_id": "S1", "approve": "outline"}})
    with pytest.raises(Exception):
        asyncio.run(series.refine(job))
    assert "outline_approved_at" not in json.loads((d / "input.json").read_text())


def test_archive_episodes_moves_drafts_and_logs(app_session):
    series, d = app_session
    write(d / "episodes" / "ep02_v2.json", episode(2))  # every version goes, json-only drafts too
    out = series.archive_episodes("demo", "S1")
    assert out["archived"] == [1, 2, 3, 4, 5, 6]
    st = series.session_state("demo", "S1")
    assert st["episodes"] == {} and st["missing"] == [1, 2, 3, 4, 5, 6]
    arch = d / out["dir"]
    assert (arch / "ep02_v2.json").exists() and (arch / "ep01_v1.md").exists()
    assert st["iterations"][-1]["status"] == "archived"


def test_archive_refuses_produced_and_final(app_session):
    series, d = app_session
    finalize(d)
    with pytest.raises(RuntimeError, match="chốt"):
        series.archive_episodes("demo", "S1", [2])
    (d / "final" / "ep02.json").unlink()
    inp = json.loads((d / "input.json").read_text())
    write(d / "input.json", {**inp, "produced_upto": 2})
    with pytest.raises(RuntimeError, match="canon"):
        series.archive_episodes("demo", "S1", [2])
    assert (d / "episodes" / "ep02_v1.json").exists()


def test_old_per_shot_prompts_must_be_remade(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"aspect_ratio": "9:16", "shots": []})
    assert package.prompts_stale(d, 1)  # 1-5s per-shot prompts drift: always offer to remake them


def test_clip_package_uses_line_times_and_cuts(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    line = {"character": "char_01", "line": "Anh đi đâu đấy?", "voiceover": False, "start_sec": 3.2, "end_sec": 5.0}
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 12, "characters": ["char_01"], "dialogue": [line],
         "continuity_in": "", "video_prompt": "CLIP ONE",
         "cuts": [{"cut": 1, "start_sec": 0, "end_sec": 3, "camera": "WS", "action": "walks in"},
                  {"cut": 2, "start_sec": 3, "end_sec": 12, "camera": "CU", "action": "asks", "dialogue": [line]}]}]})
    path, _ = package.build_episode_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        root = z.namelist()[0].split("/")[0]
        txt = z.read(f"{root}/prompts/clip_01.txt").decode()
        assert "CLIP 01" in txt and "Các cảnh cắt" in txt and "CLIP ONE" in txt
        assert "00:00:03,200 --> 00:00:05,000" in z.read(f"{root}/subtitles.srt").decode()
    finally:
        path.unlink()


def _clip(no, a, b, scene, lines=()):
    return {"shot_number": no, "scene": scene, "start_sec": a, "end_sec": b, "video_prompt": "p",
            "dialogue": [{"character": "char_01", "line": l, "start_sec": s0, "end_sec": s1} for l, s0, s1 in lines]}


def test_check_clips_one_scene_per_clip(app_session):
    series, d = app_session
    from app.pipeline import package
    ep = episode(1)
    # Same villa (loc_04), two rooms: two conversations, two scenes
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 8, "loc_id": "loc_04", "heading": "phòng ăn", "beats": []},
                    {"id": "SC2", "start_sec": 8, "end_sec": 20, "loc_id": "loc_04", "heading": "vườn sau", "beats": []}]
    write(d / "final" / "ep01.json", ep)
    pf = d / "final" / "shots" / "ep01" / "prompts.json"
    write(pf, {"unit": "clip", "total_duration_sec": 20, "shots": [_clip(1, 0, 12, "SC1"), _clip(2, 12, 20, "SC2")]})
    errs, _ = package.check_clips(d, 1)
    assert any("spans 2 scenes" in e for e in errs)
    write(pf, {"unit": "clip", "total_duration_sec": 20, "shots": [
        _clip(1, 0, 8, "SC1", [("Anh đi đâu?", 1, 2.5)]), _clip(2, 8, 20, "SC2", [("Ra vườn.", 21, 22)])]})
    errs, _ = package.check_clips(d, 1)
    assert errs == ["clip 2 [8.0-20.0]: line 21-22 is outside the clip: Ra vườn."]


def test_check_clips_length_and_gaps(app_session):
    series, d = app_session
    from app.pipeline import package
    ep = episode(1)
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 40, "beats": []}]
    write(d / "final" / "ep01.json", ep)
    write(d / "final" / "shots" / "ep01" / "prompts.json",
          {"unit": "clip", "total_duration_sec": 40, "shots": [_clip(1, 0, 20, "SC1"), _clip(2, 21, 40, "SC1")]})
    errs, _ = package.check_clips(d, 1)
    assert any("max 15s" in e for e in errs) and any("contiguous" in e for e in errs)


def _fmt2_clip(no, a, b, scene="SC1", cuts=None, parts=None, lines=()):
    prompt = "Opening: x. Shot 1 ... Ending: y. Rules: ... No subtitles, captions ..."
    c = _clip(no, a, b, scene, lines)
    c.update({"video_prompt": prompt, "opening_state": "x", "closing_state": "y", "performance": "z",
              "on_screen_text": [], "cuts": cuts or [], "veo_parts": parts or []})
    return c


def _write_fmt2(d, clips, total):
    ep = episode(1)
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": total, "loc_id": "loc_01", "beats": []}]
    write(d / "final" / "ep01.json", ep)
    write(d / "final" / "shots" / "ep01" / "prompts.json",
          {"unit": "clip", "prompt_format": 2, "total_duration_sec": total, "shots": clips})


def test_check_clips_format2_prompt_layout(app_session):
    series, d = app_session
    from app.pipeline import package
    good = _fmt2_clip(1, 0, 8, cuts=[{"cut": 1, "start_sec": 0, "end_sec": 8}],
                      parts=[{"part": 1, "start_sec": 0, "end_sec": 8, "video_prompt": "Opening: a Ending: b No subtitles"}])
    _write_fmt2(d, [good], 8)
    assert package.check_clips(d, 1) == ([], [])
    bad = {**good, "video_prompt": "Shot 1 only", "closing_state": ""}
    _write_fmt2(d, [bad], 8)
    errs, _ = package.check_clips(d, 1)
    assert any("Opening:, Ending:, No subtitles" in e for e in errs) and any("no closing_state" in e for e in errs)


def test_check_clips_veo_parts_and_cut_count(app_session):
    series, d = app_session
    from app.pipeline import package
    cuts = [{"cut": k, "start_sec": a, "end_sec": b} for k, (a, b) in enumerate([(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 12)], 1)]
    part = lambda k, a, b: {"part": k, "start_sec": a, "end_sec": b, "video_prompt": "Opening: a Ending: b No subtitles"}
    line = ("Anh đi đâu đấy?", 4.5, 5.8)
    _write_fmt2(d, [_fmt2_clip(1, 0, 12, cuts=cuts)], 12)
    errs, warns = package.check_clips(d, 1)
    assert any("no veo_parts" in e for e in errs) and any("6 cuts" in w for w in warns)
    _write_fmt2(d, [_fmt2_clip(1, 0, 12, cuts=cuts, parts=[part(1, 0, 6), part(2, 6, 12)], lines=[line])], 12)
    assert package.check_clips(d, 1)[0] == []
    # 9s part, split inside a cut and inside a line
    _write_fmt2(d, [_fmt2_clip(1, 0, 12, cuts=cuts, parts=[part(1, 0, 3), part(2, 3, 12)])], 12)
    errs, _ = package.check_clips(d, 1)
    assert any("ends inside a cut" in e for e in errs) and any("9.0s, max 8s" in e for e in errs)
    _write_fmt2(d, [_fmt2_clip(1, 0, 12, cuts=cuts, parts=[part(1, 0, 6), part(2, 6, 12)], lines=[("Dài.", 5, 7)])], 12)
    assert any("splits the line" in e for e in package.check_clips(d, 1)[0])


def test_check_clips_flags_old_format(app_session):
    series, d = app_session
    from app.pipeline import package
    ep = episode(1)
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 10, "beats": []}]
    write(d / "final" / "ep01.json", ep)
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "total_duration_sec": 10, "shots": [_clip(1, 0, 10, "SC1")]})
    errs, warns = package.check_clips(d, 1)
    assert errs == [] and any("older prompt format" in w for w in warns)


def test_old_prompt_format_is_outdated_not_stale(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    pf = d / "final" / "shots" / "ep01" / "prompts.json"
    write(pf, {"unit": "clip", "shots": []})
    assert package.prompts_outdated(d, 1) and not package.prompts_stale(d, 1)
    write(pf, {"unit": "clip", "prompt_format": 2, "shots": []})
    assert not package.prompts_outdated(d, 1)


def test_check_clips_every_clip_needs_a_flow_version(app_session):
    series, d = app_session
    from app.pipeline import package
    _write_fmt2(d, [_fmt2_clip(1, 0, 6, cuts=[{"cut": 1, "start_sec": 0, "end_sec": 6}])], 6)
    assert any("no veo_parts" in e for e in package.check_clips(d, 1)[0])


def test_flow_warnings_names_and_faces():
    from app.pipeline import package
    names = {"char_01": "Phong", "char_03": "Ông Hữu"}
    part = {"video_prompt": 'Cast: Mr. Huu: man, 50s. The worker says: "Phong ơi, ra đây."',
            "refs": ["assets/characters/char_01/a.png", "assets/characters/char_03/b.png", "assets/locations/x.png"]}
    w = package.flow_warnings("p1", part, names)
    assert any("Ông Hữu" in x and "Phong" not in x for x in w)  # name in dialogue is fine, "Huu" is not
    assert any("2 character images" in x for x in w)
    ok = {"video_prompt": 'The businessman points up. The worker: "Phong đây."', "refs": ["assets/characters/char_01/a.png"]}
    assert package.flow_warnings("p1", ok, names) == []


def test_dialogue_tags_catch_lip_synced_thoughts_and_wrong_speakers():
    from app.pipeline import package
    lines = [{"character": "char_02", "line": "Tay mày sao rồi?", "start_sec": 0.1},
             {"character": "char_01", "line": "Khóa thật nặng gấp đôi.", "voiceover": True, "start_sec": 3.9},
             {"character": "char_09", "line": "Ai nhặt được thì đem nộp!", "start_sec": 6.7}]
    on = {"char_01", "char_02"}
    good = ('Voices: ... Shot 1: SPEAKS (lip-synced): Tam (left, bucket hat), worried, 0.1-1.8s: "Tay mày sao rồi?" '
            'VOICE-OVER (inner voice, nobody\'s lips move): Phong, cold, 3.9-6.4s; Phong keeps his mouth closed: '
            '"Khóa thật nặng gấp đôi." OFF-SCREEN VOICE (not in frame): the foreman, through a loudspeaker: '
            '"Ai nhặt được thì đem nộp!"')
    assert package.dialogue_tag_warnings("c7", good, lines, on) == []
    # the old style: VO written as "off screen, not lip-synced" after a lip-synced line -> wrong tag
    old = ('Tam says in Vietnamese, SPEAKS (lip-synced): "Tay mày sao rồi?" Then Phong (voice-over, off screen, '
           'not lip-synced): "Khóa thật nặng gấp đôi." The Foreman: "Ai nhặt được thì đem nộp!"')
    w = package.dialogue_tag_warnings("c7", old, lines, on)
    assert any("Khóa" in x and "has no VOICE-OVER tag" in x for x in w)  # untagged inner thought
    assert any("Ai nhặt" in x and "has no OFF-SCREEN VOICE tag" in x for x in w)
    mixed = 'SPEAKS (lip-synced): Phong: "Khóa thật nặng gấp đôi."'  # a thought tagged as speech
    assert any("tagged SPEAKS (lip-synced), should be VOICE-OVER" in x
               for x in package.dialogue_tag_warnings("c7", mixed, lines[1:2], on))
    assert any("not quoted word for word" in x for x in package.dialogue_tag_warnings("c7", "nothing", lines[:1], on))


USER_PART = ('Shot 1 (0-1.4s): extreme close-up; the hand hides. No one speaks on screen. The young worker keeps his '
             'mouth closed. VOICE-OVER (inner voice, nobody\'s lips move): the young worker, low, in Vietnamese, '
             '0.05-2.9s: "Tôi suýt kể cho cô ấy nghe chuyện hồi đi học, rồi lại nuốt vào." Shot 2 (1.4-3.2s): '
             'the bangle flashes. No dialogue. Shot 3 (3.2-5.25s): he draws a breath as if to ask, then looks down. '
             'VOICE-OVER (inner voice, nobody\'s lips move): the young worker, slow, 2.95-5.23s: "Ba tuần rồi."')


def test_shot_dialogue_warnings_on_a_real_flow_part():
    from app.pipeline import package
    w = package.shot_dialogue_warnings("p", USER_PART)
    assert any("1.4-3.2s says \"No dialogue\"" in x for x in w)
    assert any("as if to ask" in x for x in w)
    fixed = (USER_PART.replace("No dialogue.", "No one speaks on screen; the young worker's voice-over continues.")
             .replace("he draws a breath as if to ask", "his lips part, then press shut"))
    assert package.shot_dialogue_warnings("p", fixed) == []


def test_pace_warnings_count_vietnamese_syllables():
    from app.pipeline import package
    fast = {"line": "Tôi suýt kể cho cô ấy nghe chuyện hồi đi học, rồi lại nuốt vào.", "start_sec": 0.05, "end_sec": 2.9}
    ok = {"line": "Tôi suýt kể chuyện hồi đi học, rồi lại thôi.", "start_sec": 0.05, "end_sec": 2.9}
    assert "15 syllables" in package.pace_warnings("c", [fast])[0]
    assert package.pace_warnings("c", [ok]) == []
