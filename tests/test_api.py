"""JSON API used by the React UI: payload shape and the guards around finalize / video prompts."""

import json

import pytest
from fastapi.testclient import TestClient

from test_series_package import age, finalize
from conftest import episode, write


@pytest.fixture
def client(session, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "SERIES", session.parents[1])
    from app.main import app
    return TestClient(app), session


def test_project_payload_has_fields_the_ui_reads(client):
    c, _ = client
    r = c.get("/api/projects/demo/S1")
    assert r.status_code == 200
    p = r.json()
    for key in ("final_stale", "final_complete", "settings", "cost_usd", "story_check", "editor", "episodes"):
        assert key in p, key
    assert p["settings"] == {"auto_editor_outline": True, "auto_editor_episodes": False}
    assert {"has_prompts", "prompts_stale", "in_final"} <= set(p["episodes"][0])


def test_settings_roundtrip(client):
    c, _ = client
    assert c.put("/api/projects/demo/S1/settings", json={"auto_editor_outline": False}).json()["auto_editor_outline"] is False
    assert c.get("/api/projects/demo/S1").json()["settings"]["auto_editor_outline"] is False


def test_stale_final_blocks_prompts_until_refreshed(client):
    c, d = client
    finalize(d)
    for f in (d / "final").glob("*"):
        age(f)
    write(d / "episodes" / "ep02_v2.json", episode(2, [("char_01", "Câu mới hơn hẳn.", False)] * 4))
    write(d / "episodes" / "ep02_v2.md", "# v2")
    p = c.get("/api/projects/demo/S1").json()
    assert p["final_stale"] == [2] and p["stage"]["label"] == "Có sửa sau khi chốt"
    r = c.post("/api/projects/demo/S1/shotlist", json={"episodes": [2]})
    assert r.status_code == 400 and "Chốt lại" in r.json()["detail"]
    r = c.post("/api/projects/demo/S1/final/refresh")
    assert r.status_code == 200 and "final/ep02.json" in r.json()["copied"]
    assert c.get("/api/projects/demo/S1").json()["final_stale"] == []
    assert c.post("/api/projects/demo/S1/final/refresh").status_code == 400  # nothing left to refresh


def test_continue_validation(client):
    c, _ = client
    r = c.post("/api/continue", json={"slug": "nope", "sid": "S1", "canon_mode": "none"})
    assert r.status_code == 400
    r = c.post("/api/continue", json={"slug": "demo", "sid": "", "canon_mode": "none"})
    assert r.status_code == 400 and "ngoài app" in r.json()["detail"]


def test_old_continue_page_redirects(client):
    c, _ = client
    r = c.get("/series/continue?slug=demo&sid=S1", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/ui/continue?slug=demo&sid=S1"


@pytest.fixture
def hide_env(client, tmp_path, monkeypatch):
    """Hide/restore against throwaway dirs: never touches data/ui_state.json or .claude/skills."""
    from app import config, hidden
    monkeypatch.setattr(hidden, "STATE", tmp_path / "ui_state.json")
    monkeypatch.setattr(hidden, "SKILL_ARCHIVE", tmp_path / "archive" / "skills")
    monkeypatch.setattr(config, "SKILLS", tmp_path / "skills")
    write(tmp_path / "skills" / "write-series-demo" / "SKILL.md", "---\nname: write-series-demo\n---\n")
    return client[0], tmp_path


def test_hide_and_restore_skill(hide_env):
    c, tmp = hide_env
    assert c.post("/api/hide", json={"kind": "skills", "item": "demo"}).status_code == 200
    assert not (tmp / "skills" / "write-series-demo").exists()
    assert (tmp / "archive" / "skills" / "write-series-demo" / "SKILL.md").exists()
    assert c.get("/api/hidden").json()["skills"] == ["demo"]
    assert c.post("/api/unhide", json={"kind": "skills", "item": "demo"}).status_code == 200
    assert (tmp / "skills" / "write-series-demo" / "SKILL.md").exists()
    assert c.get("/api/hidden").json()["skills"] == []


def test_hide_and_restore_series(hide_env):
    c, _ = hide_env
    assert any(p["session_id"] == "S1" for p in c.get("/api/projects").json())
    c.post("/api/hide", json={"kind": "series", "item": "demo/S1"})
    assert not any(p["session_id"] == "S1" for p in c.get("/api/projects").json())
    c.post("/api/unhide", json={"kind": "series", "item": "demo/S1"})
    assert any(p["session_id"] == "S1" for p in c.get("/api/projects").json())


def test_hide_rejects_unknown_kind_and_missing_skill(hide_env):
    c, _ = hide_env
    assert c.post("/api/hide", json={"kind": "nope", "item": "x"}).status_code == 400
    assert c.post("/api/hide", json={"kind": "skills", "item": "missing"}).status_code == 400


def test_archive_endpoint(client):
    c, d = client
    r = c.post("/api/projects/demo/S1/episodes/archive", json={"episodes": [5, 6]})
    assert r.status_code == 200 and r.json()["archived"] == [5, 6]
    assert c.get("/api/projects/demo/S1").json()["missing"] == [5, 6]
    assert c.post("/api/projects/demo/S1/episodes/archive", json={"episodes": [9]}).status_code == 400


def test_headless_prompt_keeps_subagents_in_foreground():
    from app import claude_runner
    assert "run_in_background: false" in claude_runner.HEADLESS_NOTE


def test_prompts_endpoint(client):
    c, d = client
    assert c.get("/api/projects/demo/S1/episodes/1/prompts").status_code == 404
    img = write(d / "assets" / "characters" / "char_01" / "char_01_sheet_v1.png", "PNG")
    write(d / "assets" / "images.json", {"items": {"char_01": {"kind": "character", "images": [
        {"file": "characters/char_01/char_01_sheet_v1.png", "status": "approved"}]}}})
    write(d / "final" / "shots" / "ep01" / "prompts.json", {"unit": "clip", "aspect_ratio": "9:16", "shots": [
        {"shot_number": 1, "start_sec": 0, "end_sec": 3, "characters": ["char_01"], "refs": [],
         "dialogue": [{"character": "char_02", "line": "Anh đi đâu?", "voiceover": True}], "video_prompt": "P1"}]})
    r = c.get("/api/projects/demo/S1/episodes/1/prompts")
    assert r.status_code == 200
    v = r.json()
    s = v["shots"][0]
    assert s["video_prompt"] == "P1" and s["refs"] == ["characters/char_01/char_01_sheet_v1.png"]
    assert v["names"]["char_02"] == "Nhân vật 2"  # off-screen speakers get their bible name
    assert img.exists()


def test_routes_that_start_jobs_are_async(client):
    """jobs.start needs the event loop: a sync route runs in a thread pool and its job never starts."""
    import inspect
    from app.main import app
    bad = [r.path for r in app.routes if getattr(r, "endpoint", None) and "jobs.start(" in inspect.getsource(r.endpoint)
           and not inspect.iscoroutinefunction(r.endpoint)]
    assert bad == []


def test_job_start_without_event_loop_fails_before_saving(tmp_path, monkeypatch):
    from app import config, jobs
    monkeypatch.setattr(config, "JOBS", tmp_path)
    m = jobs.JobManager()
    with pytest.raises(RuntimeError):
        m.start("x", "t", {}, lambda j: None)
    assert list(tmp_path.glob("*.json")) == []


@pytest.mark.parametrize("language,note", [("en", "in English"), ("", "language of the idea")])
def test_new_series_language(client, monkeypatch, language, note):
    c, d = client
    from app import main
    from app.jobs import Job
    from app.pipeline import series
    started = {}

    def fake_start(kind, title, params, fn, job=None):
        started.update(params)
        return Job({"id": "J1", "kind": kind, "title": title, "params": params, "status": "running",
                    "created_at": "2026-10-13T00:00:00Z", "steps": {}, "cost_usd": 0.0, "result": {}})

    monkeypatch.setattr(series, "list_series_skills", lambda: ["demo"])
    monkeypatch.setattr(main.jobs, "start", fake_start)
    r = c.post("/api/projects", json={"slug": "demo", "idea": "Một anh phụ hồ cứu con gái ông chủ thầu.",
                                      "language": language})
    assert r.status_code == 200, r.text
    inp = json.loads((d.parent / r.json()["session_id"] / "input.json").read_text())
    assert inp.get("language", "") == language and started["language"] == language
    assert note in series.language_note(language)


def test_new_series_rejects_unknown_language(client, monkeypatch):
    c, _ = client
    from app.pipeline import series
    monkeypatch.setattr(series, "list_series_skills", lambda: ["demo"])
    r = c.post("/api/projects", json={"slug": "demo", "idea": "Một anh phụ hồ cứu con gái ông chủ thầu.",
                                      "language": "fr"})
    assert r.status_code == 400
