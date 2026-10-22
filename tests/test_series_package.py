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


def test_refs_zip_has_approved_and_draft_only(app_session):
    series, d = app_session
    from app.pipeline import package
    with pytest.raises(FileNotFoundError):
        package.build_refs_package(d, "Demo")
    a = write(d / "assets" / "characters" / "char_01" / "char_01_sheet_v1.png", "PNG" * 10)
    b = write(d / "assets" / "characters" / "char_01" / "char_01_sheet_v2.png", "PNG" * 10)
    c = write(d / "assets" / "props" / "prop_01_v1.png", "PNG" * 10)
    write(d / "assets" / "images.json", {"items": {
        "char_01": {"kind": "character", "images": [{"file": str(a.relative_to(d / "assets")), "status": "rejected"},
                                                    {"file": str(b.relative_to(d / "assets")), "status": "approved"}]},
        "prop_01": {"kind": "prop", "images": [{"file": str(c.relative_to(d / "assets")), "status": "draft"}]}}})
    path, name = package.build_refs_package(d, "Demo")
    try:
        names = zipfile.ZipFile(path).namelist()
        assert name == "anh_tham_chieu_demo.zip"
        assert "anh_tham_chieu_demo/da_duyet/nhan_vat/char_01_nhan_vat_1_sheet_v2.png" in names
        assert "anh_tham_chieu_demo/cho_duyet/dao_cu/prop_01_v1.png" in names
        assert not any("sheet_v1" in n for n in names)
        csv_text = zipfile.ZipFile(path).read("anh_tham_chieu_demo/danh_sach.csv").decode("utf-8-sig")
        assert "đã duyệt" in csv_text and "chờ duyệt" in csv_text
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
    errs, warns = package.check_clips(d, 1)
    assert errs == [] and len(warns) == 1 and "not stretched" in warns[0]
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
    assert package.prompts_outdated(d, 1)  # Veo parts without a Flow length (4/6/8s)
    write(pf, {"unit": "clip", "prompt_format": 3, "shots": []})
    assert package.prompts_outdated(d, 1)  # Flow parts not stretched, no minors rule
    write(pf, {"unit": "clip", "prompt_format": 4, "shots": []})
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
    assert w == []  # names are fine (tested 2026-10-15); 2 characters + location fit Flow's 3 images
    ok = {"video_prompt": 'The businessman points up. The worker: "Phong đây."', "characters": ["char_01", "char_03"],
          "refs": ["assets/characters/char_01/a.png", "assets/characters/char_03/b.png"]}
    assert package.flow_warnings("p1", ok, names) == []
    one = {**ok, "refs": ["assets/characters/char_01/a.png", "assets/locations/x.png"]}
    assert any("without an image (char_03)" in x for x in package.flow_warnings("p1", one, names))
    many = {**ok, "refs": ["assets/characters/char_01/a.png", "assets/characters/char_03/b.png", "c.png", "d.png"]}
    assert any("4 images, Flow takes 3" in x for x in package.flow_warnings("p1", many, names))


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


def test_flow_package_one_file_per_veo_part(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    img = write(d / "assets" / "characters" / "char_01" / "char_01_sheet_v1.png", "PNG" * 400)
    line = {"character": "char_01", "line": "Anh đi đâu đấy?", "voiceover": False, "start_sec": 9.0, "end_sec": 10.5}
    write(d / "final" / "shots" / "ep01" / "prompts.json", {
        "unit": "clip", "aspect_ratio": "9:16", "flow_labels": {"char_01": "the young worker"}, "shots": [
            {"shot_number": 1, "start_sec": 0, "end_sec": 12, "characters": ["char_01"], "dialogue": [line],
             "video_prompt": "SEEDANCE ONE", "veo_parts": [
                 {"part": 1, "start_sec": 0, "end_sec": 6.5, "characters": [], "refs": [], "video_prompt": "VEO ONE"},
                 {"part": 2, "start_sec": 6.5, "end_sec": 12, "characters": ["char_01"],
                  "refs": [str(img.relative_to(d))], "video_prompt": "VEO TWO: The young worker looks up."}]}]})
    path, name = package.build_flow_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        root = z.namelist()[0].split("/")[0]
        assert name.endswith("_flow.zip")
        p1, p2 = z.read(f"{root}/parts/clip_01_1.txt").decode(), z.read(f"{root}/parts/clip_01_2.txt").decode()
        assert "VEO ONE" in p1 and "Text to Video" in p1 and "SEEDANCE" not in p1
        assert "VEO TWO" in p2 and "Ingredients to Video" in p2 and "refs/char_01_vu_sheet_v1.png" in p2
        name = "Vũ"  # the episode's own cast name wins over the bible's
        assert f'{name}: "Anh đi đâu đấy?"' in p2 and "Anh đi đâu" not in p1
        assert f"VEO TWO: {name} looks up." in p2 and "young worker" not in p2  # old role labels -> names
        q = json.loads(z.read(f"{root}/flow_queue.json"))
        assert [r["save_as"] for r in q["parts"]] == ["clips/clip_01_1.mp4", "clips/clip_01_2.mp4"]
        assert q["parts"][1]["trim_to_sec"] == 5.5
        assert f"{root}/refs/char_01_vu_sheet_v1.png" in z.namelist()
    finally:
        path.unlink()


def test_flow_package_needs_veo_parts(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 12, "video_prompt": "p"}]})
    with pytest.raises(FileNotFoundError):
        package.build_flow_package(d, 1, "Demo")


def test_flow_duration_stretches_to_a_step():
    from app.pipeline import package
    # script seconds -> Flow length: ~1.3x, rounded up to 4/6/8/10 (4s -> 6s, 6s -> 8s, at most 10s)
    assert [package.flow_duration(x) for x in (3.0, 4.0, 4.7, 5.0, 6.0, 6.3, 7.5, 8.0, 10.5)] == [4, 6, 6, 8, 8, 10, 10, 10, None]
    assert [package.fit_duration(x) for x in (3.2, 4.1, 5.0, 8.1, 10.1, 10.2)] == [4, 4, 6, 8, 10, None]


def test_check_clips_flow_lengths(app_session):
    series, d = app_session
    from app.pipeline import package
    cuts = [{"cut": k, "start_sec": a, "end_sec": b} for k, (a, b) in enumerate([(0, 3), (3, 5.8), (5.8, 8.5), (8.5, 13.8)], 1)]
    part = lambda k, a, b, dur, text=None: {"part": k, "start_sec": a, "end_sec": b, "duration_sec": dur,
                                            "video_prompt": (text or f"{dur}-second clip") + " Opening: a Ending: b No subtitles"}

    def check(parts):
        ep = episode(1)
        ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 13.8, "loc_id": "loc_01", "beats": []}]
        write(d / "final" / "ep01.json", ep)
        write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "prompt_format": 4, "total_duration_sec": 13.8,
                                                                 "shots": [_fmt2_clip(1, 0, 13.8, cuts=cuts, parts=parts)]})
        return package.check_clips(d, 1)

    assert check([part(1, 0, 5.8, 8), part(2, 5.8, 13.8, 10)]) == ([], [])
    errs, _ = check([part(1, 0, 5.8, 5), part(2, 5.8, 13.8, 6)])
    assert any("not a Flow length" in e for e in errs) and any("does not fit duration_sec 6s" in e for e in errs)
    errs, _ = check([part(1, 0, 5.8, 8, "5.8-second clip"), part(2, 5.8, 13.8, 10)])
    assert any('must start with "8-second"' in e for e in errs)
    errs, warns = check([part(1, 0, 5.8, 10), part(2, 5.8, 13.8, 10)])
    assert errs == [] and any("5.8s of script -> 8s, duration_sec is 10s" in w for w in warns)
    errs, warns = check([part(1, 0, 3, 8), part(2, 3, 5.8, 4), part(3, 5.8, 13.8, 10)])
    assert errs == [] and any("plays too slow" in w for w in warns) and any("-> 4s, duration_sec is 4s" not in w for w in warns)


def test_minor_problems_flag_photos_and_risky_words(app_session):
    series, d = app_session
    from app.pipeline import package
    write(d / "assets" / "assets_v1.json", {"characters": [{"char_id": "char_01", "age": 26}, {"char_id": "char_05", "age": 10}]})
    kids = package.minor_ids(d)
    assert kids == {"char_05"}
    bad = {"characters": ["char_05", "char_01"], "refs": ["assets/characters/char_05/char_05_o2_v1.png"],
           "video_prompt": 'Late night. The little girl, small and skinny, barefoot in shorts, sits right beside the worker '
                           'in a tank top; he ruffles her hair. She says: "Anh ngủ đi."'}
    w = package.minor_problems("p1", bad, kids)
    assert any("photo of a minor" in x for x in w)
    risky = next(x for x in w if "risky words" in x)
    for word in ("barefoot", "shorts", "skinny", "small and", "tank top", "ruffles", "right beside", "late night"):
        assert word in risky, word
    ok = {"characters": ["char_05", "char_01"], "refs": ["assets/characters/char_01/a.png"],
          "video_prompt": "Evening. The younger sister, a 10-year-old schoolgirl in a white school shirt and navy trousers, "
                          "sits on the step an arm's length from her older brother."}
    assert package.minor_problems("p1", ok, kids) == []
    assert package.minor_problems("p1", {**bad, "characters": ["char_01"]}, kids) == []


def test_minor_problems_flag_a_device_and_two_adults(app_session):
    """ep06 clip 2 part 1 (refused 5 times): the sister twisting her phone strap beside her brother and his co-worker."""
    series, d = app_session
    from app.pipeline import package
    kids = {"char_05"}
    part = {"characters": ["char_05", "char_06", "char_01"], "refs": [],
            "video_prompt": "The younger sister stands inside the door, both hands twisting the strap of the red keypad "
                            "phone. Rules: No subtitles, captions, watermarks or on-screen text."}
    w = package.minor_problems("c2p1", part, kids)
    assert any("device (keypad, phone)" in x for x in w) and any("2 adults" in x for x in w)
    ok = {"characters": ["char_05", "char_01"], "refs": [],
          "video_prompt": "Na stands on the mat, arms crossed, and shrugs, then speaks her dialogue. Only the listed cast appear on screen; "
                          "no subtitles or on-screen text. OFF-SCREEN VOICE: none."}
    assert package.minor_problems("c2p1", ok, kids) == []


def test_flow_package_keeps_stretched_parts_and_retimes_subtitles(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    line = {"character": "char_01", "line": "Anh đi đâu đấy?", "voiceover": False, "start_sec": 7.0, "end_sec": 9.0}
    write(d / "final" / "shots" / "ep01" / "prompts.json", {
        "unit": "clip", "prompt_format": 4, "aspect_ratio": "9:16", "shots": [
            {"shot_number": 1, "start_sec": 0, "end_sec": 12, "characters": ["char_01"], "dialogue": [line],
             "video_prompt": "x", "veo_parts": [
                 {"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8, "characters": [], "video_prompt": "8-second A"},
                 {"part": 2, "start_sec": 6, "end_sec": 12, "duration_sec": 8, "characters": ["char_01"], "video_prompt": "8-second B"}]}]})
    path, _ = package.build_flow_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        root = z.namelist()[0].split("/")[0]
        q = json.loads(z.read(f"{root}/flow_queue.json"))["parts"]
        assert [(r["duration_sec"], r["trim_to_sec"], r["video_start"]) for r in q] == [(8, 8.0, 0.0), (8, 8.0, 8.0)]
        # line at script 7.0-9.0 = 1-3s into part 2, stretched x8/6 -> 1.33-4.0s, after 8s of part 1
        assert "00:00:09,330 --> 00:00:12,000" in z.read(f"{root}/subtitles.srt").decode()
        assert "giữ nguyên cả clip" in z.read(f"{root}/parts/clip_01_2.txt").decode()
        assert "video dựng xong khoảng 16s" in z.read(f"{root}/HUONG_DAN_FLOW.txt").decode()
    finally:
        path.unlink()


def test_flow_only_prompts_skip_clip_prompt_and_higgsfield_package(app_session):
    series, d = app_session
    from app import config
    from app.pipeline import package
    assert config.VIDEO_TARGETS == ("flow",)  # Flow only unless STORY_DNA_VIDEO_TARGETS says otherwise
    finalize(d)
    ep = episode(1)
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 6, "loc_id": "loc_01", "beats": []}]
    write(d / "final" / "ep01.json", ep)
    clip = _fmt2_clip(1, 0, 6, cuts=[{"cut": 1, "start_sec": 0, "end_sec": 6}],
                      parts=[{"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8,
                              "video_prompt": "8-second clip. Opening: a Ending: b No subtitles"}])
    clip["video_prompt"] = ""
    write(d / "final" / "shots" / "ep01" / "prompts.json",
          {"unit": "clip", "prompt_format": 4, "targets": ["flow"], "total_duration_sec": 6, "shots": [clip]})
    assert package.check_clips(d, 1) == ([], [])  # no "Opening:" error for the empty clip prompt
    assert package.prompts_view(d, 1)["targets"] == ["flow"]
    with pytest.raises(FileNotFoundError, match="chỉ có bản Google Flow"):
        package.build_episode_package(d, 1, "Demo")
    path, _ = package.build_flow_package(d, 1, "Demo")
    path.unlink()


def test_refs_follow_the_newest_approved_image(app_session):
    """An image made again (e.g. after a Flow refusal) replaces the old one in prompts and packages written earlier."""
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    for v in (1, 2):
        write(d / "assets" / "characters" / "char_01" / f"char_01_o2_v{v}.png", "PNG" * 400)
    write(d / "assets" / "images.json", {"items": {"char_01_o2": {"kind": "outfit", "images": [
        {"file": "characters/char_01/char_01_o2_v1.png", "status": "rejected"},
        {"file": "characters/char_01/char_01_o2_v2.png", "status": "approved"}]}}})
    old = "assets/characters/char_01/char_01_o2_v1.png"
    assert package.current_ref(d, old) == "characters/char_01/char_01_o2_v2.png"
    assert package.current_ref(d, "assets/locations/x/unknown.png") == "locations/x/unknown.png"
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "prompt_format": 4, "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 6, "characters": ["char_01"], "refs": [old], "video_prompt": "x",
         "veo_parts": [{"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8, "characters": ["char_01"],
                        "refs": [old], "video_prompt": "8-second x"}]}]})
    view = package.prompts_view(d, 1)
    assert view["shots"][0]["refs"] == ["characters/char_01/char_01_o2_v2.png"]
    assert view["shots"][0]["veo_parts"][0]["refs"] == ["characters/char_01/char_01_o2_v2.png"]
    path, _ = package.build_flow_package(d, 1, "Demo")
    try:
        names = zipfile.ZipFile(path).namelist()
        assert any(n.endswith("char_01_vu_o2_v2.png") for n in names) and not any("o2_v1" in n for n in names)
    finally:
        path.unlink()
    # every image of the item rejected: the old file is not attached
    write(d / "assets" / "images.json", {"items": {"char_01_o2": {"kind": "outfit", "images": [
        {"file": "characters/char_01/char_01_o2_v1.png", "status": "rejected"},
        {"file": "characters/char_01/char_01_o2_v2.png", "status": "rejected"}]}}})
    assert package.prompts_view(d, 1)["shots"][0]["veo_parts"][0]["refs"] == []


def test_flow_package_never_attaches_a_minor_photo(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    write(d / "assets" / "assets_v1.json", {"characters": [{"char_id": "char_02", "age": 10}]})
    kid = write(d / "assets" / "characters" / "char_02" / "char_02_sheet_v1.png", "PNG" * 400)
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "prompt_format": 4, "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 6, "video_prompt": "", "veo_parts": [
            {"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8, "characters": ["char_02"],
             "refs": [str(kid.relative_to(d))], "video_prompt": "8-second x"}]}]})
    path, _ = package.build_flow_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        assert not any("/refs/" in n for n in z.namelist())
        q = json.loads(z.read([n for n in z.namelist() if n.endswith("flow_queue.json")][0]))
        assert q["parts"][0]["images"] == [] and q["parts"][0]["mode"] == "Text to Video"
    finally:
        path.unlink()


def test_minor_problems_catch_a_sleeping_adult_and_the_childs_mouth():
    from app.pipeline import package
    kids = {"char_05"}
    part = {"characters": ["char_05", "char_01"], "continuity_in": "the young worker asleep off frame",
            "video_prompt": "The young worker rests his head on his arms, eyes closed; the younger sister checks he does "
                            "not stir, holds the strap between her teeth, eyes red-rimmed."}
    risky = package.minor_problems("p", part, kids)[0]
    for word in ("eyes closed", "stir", "teeth", "red-rimmed", "asleep"):
        assert word in risky, word
    ok = {"characters": ["char_05"], "video_prompt": "The younger sister twists the strap around one finger, jaw set, "
                                                     "blinking fast; her brother is inside at the sink, back to camera."}
    assert package.minor_problems("p", ok, kids) == []


def test_outfit_built_on_a_rejected_face_falls_back_to_the_new_sheet(app_session):
    """ep06: Flow refused a clip whose outfit image still carried the rejected idol-like face (sheet_v1)."""
    series, d = app_session
    from app.pipeline import assets, package
    sheet1, sheet2 = "characters/char_02/char_02_sheet_v1.png", "characters/char_02/char_02_sheet_v2.png"
    outfit = "characters/char_02/char_02_o3_v1.png"
    write(d / "assets" / "images.json", {"items": {
        "char_02": {"kind": "character", "images": [{"file": sheet1, "status": "rejected"},
                                                    {"file": sheet2, "status": "approved"}]},
        "char_02_o3": {"kind": "outfit", "images": [{"file": outfit, "status": "approved", "refs": [sheet1]}]}}})
    assert package.current_ref(d, "assets/" + outfit) == sheet2
    assert "char_02_o3" not in assets.approved_refs(d) and assets.approved_refs(d)["char_02"] == sheet2
    index = assets.load_index(d)
    index["items"]["char_02_o3"]["images"][0]["refs"] = [sheet2]
    assets.save_index(d, index)
    assert package.current_ref(d, "assets/" + outfit) == outfit


def test_seedance_twin_of_every_flow_part(app_session):
    series, d = app_session
    from app.pipeline import package, seedance
    finalize(d)
    ep = episode(1)
    ep["scenes"] = [{"id": "SC1", "start_sec": 0, "end_sec": 12, "loc_id": "loc_01", "beats": []}]
    write(d / "final" / "ep01.json", ep)
    say = {"character": "char_01", "line": "Where are you going?", "line_vi": "Anh đi đâu đấy?", "delivery_en": "cold",
           "voiceover": False, "mode": "speaks", "start_sec": 1.0, "end_sec": 3.0}
    think = {"character": "char_01", "line": "He knows.", "delivery_en": "soft", "voiceover": True,
             "mode": "voiceover", "start_sec": 7.0, "end_sec": 9.0}
    clip = _fmt2_clip(1, 0, 12, cuts=[{"cut": 1, "start_sec": 0, "end_sec": 6, "camera": "static close-up on Vu",
                                       "action": "Vu looks up", "dialogue": [say]},
                                      {"cut": 2, "start_sec": 6, "end_sec": 12, "camera": "static wide shot",
                                       "action": "Vu stands still", "dialogue": [think]}],
                      parts=[{"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8, "cuts": [1],
                              "characters": ["char_01"], "opening_state": "Vu seated.", "closing_state": "Vu looking up.",
                              "video_prompt": "8-second clip. Opening: a Ending: b No subtitles. Sound: a door creaks.\nvertical 9:16 frame, photoreal",
                              "seedance": {"scene": "INT. GATEHOUSE - NIGHT", "acting": ["Vu, tired, then alert"],
                                           "exclusions": "Linh is not visible yet."}},
                             {"part": 2, "start_sec": 6, "end_sec": 12, "duration_sec": 8, "cuts": [2],
                              "characters": ["char_01"], "opening_state": "Vu standing.", "closing_state": "Vu still.",
                              "video_prompt": "8-second clip. Opening: a Ending: b No subtitles"}])
    clip["dialogue"] = [say, think]
    clip["video_prompt"] = ""
    write(d / "final" / "shots" / "ep01" / "prompts.json",
          {"unit": "clip", "prompt_format": 4, "targets": ["flow"], "total_duration_sec": 12, "shots": [clip],
           "characters": {"char_01": "Vu, a young worker"}, "voices": {"char_01": "Vu: young man, low voice"}})
    assert seedance.build_episode(d, 1) == 2
    data = json.loads((d / "final" / "shots" / "ep01" / "prompts.json").read_text(encoding="utf-8"))
    p1, p2 = (vp["seedance_prompt"] for vp in data["shots"][0]["veo_parts"])
    assert "seedance" in data["targets"]
    assert p1.startswith("Create an 8-second narrative audio-video clip.")
    assert "CLIP EP01-C01-P1. Scene: INT. GATEHOUSE - NIGHT." in p1
    assert 'VŨ (cold): "Where are you going?"' in p1 and "Where are you going?" not in p2
    assert "0-8s: Vu, tired, then alert." in p1 and "Linh is not visible yet." in p1
    assert "Synchronous audio: A door creaks." in p1 and "Voice: young man, low voice." in p1
    assert "nobody's lips move" in p2 and "the only narration is the quoted voice-over" in p2
    assert "any title or end card is added in post" in p2 and p2.endswith("No text on screen.")
    errs, warns = package.check_clips(d, 1)
    assert errs == [] and not any("Seedance" in w for w in warns)
    del data["shots"][0]["veo_parts"][1]["seedance_prompt"]
    write(d / "final" / "shots" / "ep01" / "prompts.json", data)
    assert any("1 Flow part(s) without a Seedance prompt" in w for w in package.check_clips(d, 1)[1])
    data["shots"][0]["veo_parts"][1]["seedance_prompt"] = p2
    data["shots"][0]["veo_parts"][0]["seedance_prompt"] = p1.replace('"Where are you going?"', '"Where to?"')
    write(d / "final" / "shots" / "ep01" / "prompts.json", data)
    assert any("misses the line" in e for e in package.check_clips(d, 1)[0])
    path, _ = package.build_flow_package(d, 1, "Demo")
    try:
        z = zipfile.ZipFile(path)
        root = z.namelist()[0].split("/")[0]
        assert "He knows." in z.read(f"{root}/seedance/clip_01_2.txt").decode()
        assert "PROMPT SEEDANCE 2.0" in z.read(f"{root}/parts/clip_01_2.txt").decode()
        assert json.loads(z.read(f"{root}/flow_queue.json"))["parts"][1]["seedance_prompt"] == p2
    finally:
        path.unlink()


def test_dialogue_language_defaults_to_english_and_flags_old_prompts(app_session):
    series, d = app_session
    from app.pipeline import package
    finalize(d)
    assert package.dialogue_language(d) == "en-US"  # bible without production_language
    b = json.loads((d / "final" / "bible.json").read_text(encoding="utf-8"))
    write(d / "final" / "bible.json", {**b, "production_language": "vi"})
    assert package.dialogue_language(d) == "vi"
    write(d / "final" / "bible.json", b)
    vi = {"character": "char_01", "line": "Anh đi đâu đấy?", "start_sec": 1, "end_sec": 3}
    clip = _fmt2_clip(1, 0, 6, parts=[{"part": 1, "start_sec": 0, "end_sec": 6, "duration_sec": 8, "video_prompt": "x"}])
    clip["dialogue"] = [vi]
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "prompt_format": 4, "shots": [clip]})
    why = package.outdated_reasons(d, 1)
    assert package.prompts_outdated(d, 1) and any("tiếng Anh" in w for w in why) and any("Seedance" in w for w in why)
    clip["dialogue"] = [{**vi, "line": "Where are you going?", "line_vi": vi["line"]}]
    clip["veo_parts"][0]["seedance_prompt"] = "Create an 8-second ..."
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "prompt_format": 4, "shots": [clip]})
    assert package.outdated_reasons(d, 1) == []
