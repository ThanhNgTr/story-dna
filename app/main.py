"""story-dna local web app (POC).

Run:  ./run_app.sh   (or .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765)
Open: http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import math
import subprocess
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

from . import api, config, hidden
from .jobs import JobManager
from .pipeline import analyze, series
from .pipeline import assets as asset_images
from .pipeline import package, summary

APP_DIR = Path(__file__).parent
app = FastAPI(title="story-dna")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
md = MarkdownIt("commonmark", {"html": False}).enable("table")
templates.env.filters["md"] = lambda text: md.render(text or "")
jobs = JobManager()

JOB_FUNCS = {"analysis": analyze.run_analysis, "skill": series.create_skill,
             "outline": series.write_outline, "refine": series.refine, "continue": series.continue_series,
             "images": asset_images.run_images_job, "assets": series.build_assets, "summary": summary.run_summary_job,
             "story": series.fix_story, "shotlist": package.run_shotlist_job,
             "editor": series.run_editor, "dialogue": series.run_polish,
             "action": series.run_action_polish, "continuity": series.run_continuity}

LANGUAGES = [("", "Tự nhận diện"), ("vi", "Tiếng Việt"), ("en", "Tiếng Anh"), ("zh", "Tiếng Trung"),
             ("ko", "Tiếng Hàn"), ("ja", "Tiếng Nhật"), ("th", "Tiếng Thái")]

STATUS = {"queued": ("Đang chờ", ""), "running": ("Đang chạy", "run"), "done": ("Xong", "ok"),
          "failed": ("Lỗi", "bad"), "interrupted": ("Bị gián đoạn", "warn"), "cancelled": ("Đã hủy", "muted"),
          "skipped": ("Bỏ qua (đã có)", "muted")}
STEPS = {"extract": "Dò cắt cảnh, chia đoạn, lấy khung hình", "transcribe": "Chép lời thoại (WhisperX)",
         "units": "Claude phân tích từng đoạn", "merge": "Gộp thành cốt truyện + DNA",
         "review": "Nhà phân tích phim: soát lỗi + vì sao video cuốn",
         "skill": "Tạo skill viết series", "outline": "Viết ghép ý tưởng, bible và outline",
         "episodes": "Viết các tập", "feedback": "Sửa theo góp ý", "final": "Chốt season",
         "canon_source": "Video đã làm (canon)", "continue": "Đối chiếu video + outline phần tiếp",
         "diff": "So lời thoại kịch bản với video (trên máy, không tốn Claude)",
         "images": "Tạo ảnh tham chiếu bằng Codex (nhân vật, trang phục, bối cảnh)",
         "assets": "Lập / cập nhật kho nhân vật, trang phục, bối cảnh",
         "summary": "Tóm tắt tiếng Việt",
         "dialogue": "Làm rõ lời thoại (giữ nguyên cảnh, thời lượng)",
         "action": "Bổ sung diễn xuất: tay, mặt, đồ cầm, vị trí (giữ nguyên thoại, thời lượng)",
         "editor": "Biên tập kịch bản: chấm chiều sâu, đề xuất sửa",
         "editor_apply": "Áp dụng các sửa của biên tập",
         "shotlist": "Tạo prompt video từng shot (script-to-shotlist)",
         "story_check": "Kiểm tra cốt truyện (mở đầu → kết, nhân vật, bối cảnh, cao trào, bí ẩn)",
         "continuity": "Kiểm tra liên mạch (nhân quả, ai biết gì, nối tập, manh mối)",
         "continuity_review": "Rà logic toàn mùa (lỗ hổng, trùng hợp, động cơ)",
         "continuity_apply": "Áp dụng sửa logic"}
STEP_FIELDS = {"units": "đoạn", "total": "tổng", "shots": "shot", "done": "xong", "language": "ngôn ngữ",
               "segments": "câu thoại", "phase": "giai đoạn", "skill": "skill", "version": "phiên bản",
               "failed": "lỗi", "note": "ghi chú"}
IMG_STATUS = {"draft": ("Chờ duyệt", "warn"), "approved": ("Đã duyệt", "ok"), "rejected": ("Đã bỏ", "muted")}
ASSET_VIEWS = {"chars": "Nhân vật & trang phục", "locs": "Bối cảnh", "props": "Đạo cụ", "issues": "Lỗi liên tục"}
templates.env.globals.update(STATUS=STATUS, STEPS=STEPS, STEP_FIELDS=STEP_FIELDS, IMG_STATUS=IMG_STATUS,
                             ASSET_VIEWS=ASSET_VIEWS)


def page(request: Request, name: str, **ctx) -> HTMLResponse:
    return templates.TemplateResponse(request, name, ctx)


def fmt_duration(sec: float) -> str:
    sec = int(max(0, sec))
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h} giờ {m} phút" if h else f"{m} phút {s} giây" if m else f"{s} giây"


def elapsed(data: dict) -> str | None:
    start = data.get("started_at")
    if not start:
        return None
    t0 = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    end = data.get("finished_at") if data.get("status") != "running" else None
    t1 = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) if end else datetime.now(timezone.utc)
    return fmt_duration((t1 - t0).total_seconds())


def estimate_analysis(durations: list[float], chunk_sec: int = 120) -> dict:
    # Same split rule as _analyze.py: videos >= 240 s are cut into ~chunk_sec units, shorter ones stay whole
    units = sum(max(1, math.ceil(d / chunk_sec)) if d >= 240 else 1 for d in durations)
    duration_sec = sum(durations)
    # CPU ASR + word alignment ~0.4x realtime; speaker labels (auto: up to DIARIZE_MAX_MIN) add ~0.3x
    rate = 0.4 + (0.3 if duration_sec <= config.DIARIZE_MAX_MIN * 60 else 0)
    transcribe = duration_sec * rate
    analysts = math.ceil(units / config.CLAUDE_PARALLEL) * 4.5 * 60
    merge = (18 if units > 8 else 6) * 60
    # Analysts start after the first ~10-min chunk is transcribed and run alongside the rest; the last
    # chunk's units still need one round after transcription ends
    first_chunk = min(duration_sec, 600) * rate
    overlap = max(transcribe + 4.5 * 60, first_chunk + analysts)
    return {"units": units, "transcribe": fmt_duration(transcribe), "analysts": fmt_duration(analysts),
            "merge": fmt_duration(merge), "total": fmt_duration(60 + overlap + merge)}


def videos_in(path: Path) -> list[Path]:
    """The videos an analysis of `path` would cover (same rules and order as _analyze.py)."""
    if path.is_file():
        return [path]
    import re as _re
    key = lambda p: [int(t) if t.isdigit() else t.lower() for t in _re.split(r"(\d+)", str(p))]
    return sorted((f for f in path.rglob("*") if f.suffix.lower() in config.VIDEO_EXTS and f.is_file()), key=key)


def video_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(path)], capture_output=True, text=True, timeout=15).stdout.strip()
        return float(out)
    except (ValueError, subprocess.TimeoutExpired):
        return None


def runs_covering(videos: list[Path]) -> list[dict]:
    """Analyses that already include any of these videos."""
    wanted = {str(v.resolve()) for v in videos}
    return [r for r in list_runs() if wanted & set(r["paths"])]


def all_skills() -> list[dict]:
    return [series.skill_info(s) for s in series.list_series_skills()]


def list_runs() -> list[dict]:
    skills_by_run: dict[str, list[str]] = {}
    for s in all_skills():
        if s["run_id"]:
            skills_by_run.setdefault(s["run_id"], []).append(s["slug"])
    for j in jobs.list():  # skills created by the app before metadata existed
        if j.data["kind"] == "skill" and j.data["status"] == "done":
            run = Path(j.data["params"]["run_dir"]).name
            slug = j.data["params"]["slug"]
            if series.skill_dir(slug).exists() and slug not in skills_by_run.get(run, []):
                skills_by_run.setdefault(run, []).append(slug)
    runs = []
    for d in sorted(config.ANALYSES.glob("*"), reverse=True):
        if not (d / "manifest.json").exists():
            continue
        m = json.loads((d / "manifest.json").read_text())
        dna = {}
        if (d / "dna.json").exists():
            try:
                dna = json.loads((d / "dna.json").read_text())
            except json.JSONDecodeError:
                pass
        sources = m.get("sources", [])
        runs.append({
            "id": d.name, "sources": [s["filename"] for s in sources], "paths": [s["path"] for s in sources],
            "minutes": round(sum(s.get("duration_sec", 0) for s in sources) / 60, 1),
            "language": ((sources[0].get("audio") or {}).get("language") if sources else None),
            "units": len(m.get("units", [])), "analyzed": len(list((d / "dna").glob("*.dna.json"))),
            "done": bool(dna) and (d / "story.md").exists(),
            "title": dna.get("title"), "logline": dna.get("logline"), "genre": dna.get("genre"),
            "skills": skills_by_run.get(d.name, []),
            "job": running_job_for("run_dir", str(d)),
        })
    return runs


def running_job_for(key: str, value: str):
    for j in jobs.list():
        if j.data["status"] == "running" and jobs.is_running(j.id) and \
                (j.data["params"].get(key) == value or j.data.get("result", {}).get(key) == value):
            return j
    return None


def ep_range(nums: list[int]) -> str:
    return f"tập {nums[0]}" if len(nums) == 1 else f"tập {nums[0]}–{nums[-1]}"


def series_stage(s: dict) -> tuple[str, str]:
    """(label, css) for where a series session is in the flow."""
    if running_job_for("session_id", s["session_id"]):
        return "Đang xử lý", "run"
    missing = s.get("missing") or []
    if s.get("final_stale"):
        return "Có sửa sau khi chốt", "warn"
    if s["final"]:
        return "Đã chốt", "ok"
    if missing and not s["episodes"] and not s.get("produced"):
        return ("Chờ duyệt outline", "warn") if s["has_outline"] else ("Chưa có outline", "muted")
    if missing:
        return f"Chờ duyệt phần tiếp ({ep_range(missing)})", "warn"
    return f"Đang góp ý ({s['episodes']} tập)", "warn"


# ---------- new React UI (web/ -> app/static/ui/) ----------

app.include_router(api.build_router(
    jobs, JOB_FUNCS, lambda s: series_stage(s), lambda: list_runs(), lambda kind, item: item_busy(kind, item),
    SimpleNamespace(videos_in=lambda p: videos_in(p), duration=lambda p: video_duration(p),
                    estimate=lambda d: estimate_analysis(d), covering=lambda v: runs_covering(v))))
UI_INDEX = APP_DIR / "static" / "ui" / "index.html"


@app.get("/ui", response_class=HTMLResponse)
@app.get("/ui/{rest:path}", response_class=HTMLResponse)
def ui(rest: str = ""):
    if not UI_INDEX.exists():
        raise HTTPException(404, "Giao diện mới chưa được build (cd web && npm install && npm run build).")
    return HTMLResponse(UI_INDEX.read_text(), headers={"Cache-Control": "no-cache"})


# ---------- dashboard ----------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    hid = {k: hidden.hidden(k) for k in hidden.KINDS}
    sessions = series.list_sessions()
    for s in sessions:
        s["key"] = f"{s['slug']}/{s['session_id']}"
        s["stage"] = series_stage(s)
    runs = list_runs()
    recent = [{**j.data, "elapsed": elapsed(j.data), "live": jobs.is_running(j.id)} for j in jobs.list()]
    shown_jobs = [j for j in recent if j["id"] not in hid["jobs"]][:8]
    archived = {
        "runs": [r for r in runs if r["id"] in hid["runs"]],
        "series": [s for s in sessions if s["key"] in hid["series"]],
        "skills": sorted(hid["skills"]),
        "jobs": [j for j in recent if j["id"] in hid["jobs"]],
    }
    return page(request, "index.html", env=config.check_environment(),
                runs=[r for r in runs if r["id"] not in hid["runs"]],
                skills=all_skills(), sessions=[s for s in sessions if s["key"] not in hid["series"]],
                jobs=shown_jobs, archived=archived, n_archived=sum(len(v) for v in archived.values()))


def item_busy(kind: str, item: str) -> bool:
    for j in jobs.list():
        if not jobs.is_running(j.id):
            continue
        p = j.data["params"]
        if (kind == "jobs" and j.id == item) or \
           (kind == "runs" and Path(p.get("run_dir") or j.data.get("result", {}).get("run_dir") or "x").name == item) or \
           (kind == "skills" and p.get("slug") == item) or \
           (kind == "series" and f"{p.get('slug')}/{p.get('session_id')}" == item):
            return True
    return False


@app.post("/hide")
async def hide_item(request: Request, kind: str = Form(...), item: str = Form(...)):
    if kind not in hidden.KINDS:
        raise HTTPException(400, "Loại không hợp lệ")
    if item_busy(kind, item):
        raise HTTPException(400, "Mục này đang có việc chạy. Đợi xong (hoặc dừng việc) rồi ẩn.")
    try:
        hidden.hide(kind, item)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(request.headers.get("referer") or "/", status_code=303)


@app.post("/unhide")
async def unhide_item(request: Request, kind: str = Form(...), item: str = Form(...)):
    if kind not in hidden.KINDS:
        raise HTTPException(400, "Loại không hợp lệ")
    try:
        hidden.unhide(kind, item)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(request.headers.get("referer") or "/", status_code=303)


# ---------- analysis ----------

@app.get("/analyze/new", response_class=HTMLResponse)
def analyze_new(request: Request):
    return page(request, "analyze_new.html", languages=LANGUAGES, start=str(config.INPUT))


@app.get("/browse", response_class=HTMLResponse)
def browse(request: Request, path: str = ""):
    p = Path(path).expanduser().resolve() if path else config.INPUT.resolve()
    if not any(p == r or r in p.parents for r in config.BROWSE_ROOTS) or not p.is_dir():
        p = config.BROWSE_ROOTS[0]
    entries = []
    try:
        for c in sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
            if c.name.startswith("."):
                continue
            if c.is_dir():
                entries.append({"name": c.name, "path": str(c), "dir": True})
            elif c.suffix.lower() in config.VIDEO_EXTS:
                entries.append({"name": c.name, "path": str(c), "dir": False,
                                "size_mb": round(c.stat().st_size / 1e6)})
    except PermissionError:
        pass
    can_up = any(p.parent == r or r in p.parent.parents for r in config.BROWSE_ROOTS) and p.parent != p
    n_videos = len(videos_in(p)) if p != Path.home() else sum(1 for e in entries if not e["dir"])
    return page(request, "_browse.html", cwd=str(p), parent=str(p.parent) if can_up else None, entries=entries,
                n_videos=n_videos)


@app.get("/probe", response_class=HTMLResponse)
def probe(request: Request, path: str):
    """What the pick covers: episodes + durations, time estimate, 'already analyzed' warning."""
    vp = Path(path).expanduser()
    videos = videos_in(vp) if vp.exists() else []
    items = [{"name": str(v.relative_to(vp)) if vp.is_dir() else v.name, "dur": video_duration(v)} for v in videos]
    durs = [i["dur"] for i in items if i["dur"]]
    info = {"ok": bool(durs), "is_dir": vp.is_dir(), "minutes": round(sum(durs) / 60, 1),
            "est": estimate_analysis(durs) if durs else None}
    return page(request, "_probe.html", info=info, items=items, existing=runs_covering(videos),
                filename=vp.name + ("/" if vp.is_dir() else ""))


@app.post("/analyze")
async def analyze_start(request: Request, video_path: str = Form(...), language: str = Form(""),
                        chunk_sec: int = Form(120), max_frames: int = Form(40), force: str = Form("")):
    vp = Path(video_path).expanduser()
    videos = videos_in(vp) if vp.exists() else []
    if not videos:
        raise HTTPException(400, f"Không tìm thấy video nào ở: {vp}")
    # Same video(s) already analyzed? Analysis is long and costly: confirm first.
    existing = runs_covering(videos)
    if existing and not force:
        wanted = {str(v.resolve()) for v in videos}
        full = [r for r in existing if wanted <= set(r["paths"])]
        return page(request, "analyze_confirm.html", existing=full or existing, partial=not full,
                    n_videos=len(videos), video_path=str(vp), language=language,
                    chunk_sec=chunk_sec, max_frames=max_frames)
    label = f"{vp.name}/ ({len(videos)} video)" if vp.is_dir() else vp.name
    job = jobs.start("analysis", f"Phân tích {label}",
                     {"video_path": str(vp), "language": language or None, "chunk_sec": chunk_sec,
                      "max_frames": max_frames}, analyze.run_analysis)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_view(request: Request, run_id: str, tab: str = "story"):
    d = config.ANALYSES / run_id
    if not (d / "manifest.json").exists():
        raise HTTPException(404)
    files = {"story": d / "story.md", "dna": d / "dna.md", "analysis": d / "film_analysis.md"}
    text = files[tab].read_text() if tab in files and files[tab].exists() else ""
    m = json.loads((d / "manifest.json").read_text())
    dna = json.loads((d / "dna.json").read_text()) if (d / "dna.json").exists() else None
    units = [{"id": u["unit_id"], "t": f"{u['t_start'] / 60:.1f}–{u['t_end'] / 60:.1f} phút",
              "done": (d / "dna" / f"{u['unit_id']}.dna.json").exists()} for u in m["units"]]
    run = next((r for r in list_runs() if r["id"] == run_id), {})
    # Prefer the on-screen title, then the genre; a run id makes a poor command name
    suggested = "-".join(series.slugify((dna or {}).get("title") or (dna or {}).get("genre") or "series").split("-")[:3])
    return page(request, "run.html", run_id=run_id, run=run, tab=tab, text=text, dna=dna, units=units,
                has_analysis=(d / "film_analysis.md").exists(),
                sources=m["sources"], suggested_slug=suggested, job=running_job_for("run_dir", str(d)))


@app.post("/runs/{run_id}/resume")
async def run_resume(run_id: str):
    d = config.ANALYSES / run_id
    job = jobs.start("analysis", f"Chạy tiếp phân tích {run_id}", {"run_dir": str(d)}, analyze.run_analysis)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.post("/skills")
async def skill_create(run_id: str = Form(...), slug: str = Form(...), update: str = Form("")):
    slug = series.slugify(slug)
    if series.skill_dir(slug).exists() and not update:
        raise HTTPException(400, f"Skill write-series-{slug} đã tồn tại. Chọn tên khác hoặc tick 'cập nhật skill có sẵn'.")
    job = jobs.start("skill", f"Tạo skill write-series-{slug}",
                     {"run_dir": str(config.ANALYSES / run_id), "slug": slug, "update": bool(update)},
                     series.create_skill)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


# ---------- series ----------

def series_tabs(active: str) -> list[tuple[str, str, bool]]:
    return [("Series mới", "/series/new", active == "new"), ("Viết tiếp series", "/series/continue", active == "continue")]


@app.get("/series/new", response_class=HTMLResponse)
def series_new(request: Request, slug: str = ""):
    return page(request, "series_new.html", skills=all_skills(), slug=slug, tabs=series_tabs("new"))


@app.post("/series")
async def series_start(slug: str = Form(...), title: str = Form(""), idea: str = Form(""),
                       idea_file: UploadFile | None = None, episodes: int = Form(12),
                       episode_sec: int = Form(90)):
    text = idea.strip()
    if idea_file and idea_file.filename:
        text = (text + "\n\n" if text else "") + (await idea_file.read()).decode(errors="replace")
    if not text:
        raise HTTPException(400, "Chưa có ý tưởng: hãy nhập vào ô hoặc tải file lên.")
    episodes = max(10, min(20, episodes))
    episode_sec = max(60, min(120, episode_sec))
    sid = series.new_session(slug, text, episodes, episode_sec, title.strip())
    job = jobs.start("outline", f"Viết outline: {title or slug}",
                     {"slug": slug, "session_id": sid, "episodes": episodes, "episode_sec": episode_sec},
                     series.write_outline)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.get("/series/{slug}/{sid}", response_class=HTMLResponse)
def series_view(request: Request, slug: str, sid: str, view: str = "", v: int = 0):
    st = series.session_state(slug, sid)
    if not st["dir"].exists():
        raise HTTPException(404)
    if not view:
        view = "outline" if st["outline"] else "adaptation"
    path = None
    if view in ("bible", "outline", "canon"):
        versions = st["versions"][view]
        path = next((p for p in versions if p.name == f"{view}_v{v}.md"), None) if v else st[view]
    elif view == "adaptation":
        path = st["adaptation"]
    elif view.startswith("ep") and view[2:].isdigit():
        path = st["episodes"].get(int(view[2:]))
    text = path.read_text() if path and path.exists() else ""
    eps = list(st["episodes"])
    cur_ep = int(view[2:]) if view.startswith("ep") and view[2:].isdigit() else None
    nav = {"prev": next((e for e in reversed(eps) if cur_ep and e < cur_ep), None),
           "next": next((e for e in eps if cur_ep and e > cur_ep), None)}
    info = {"session_id": sid, "episodes": len(eps), "planned": st["planned"], "final": st["final_complete"],
            "has_outline": st["outline"] is not None, "missing": st["missing"], "produced": st["produced_upto"]}
    job = running_job_for("session_id", sid)
    av = asset_images.view_model(st["dir"])
    if view in ASSET_VIEWS and not av:
        view = "outline"
    return page(request, "series.html", slug=slug, sid=sid, st=st, view=view, text=text, nav=nav,
                current=path.name if path else None, job=job, stage=series_stage(info),
                av=av, asset_base=f"/series/{slug}/{sid}/assets", codex=bool(config.find_codex_bin()),
                skill=series.skill_info(slug), skill_archived=slug in hidden.hidden("skills"),
                missing_label=ep_range(st["missing"]) if st["missing"] else "")


@app.post("/series/{slug}/{sid}/refine")
async def series_refine(slug: str, sid: str, feedback: str = Form(""), target: str = Form(""),
                        approve: str = Form("")):
    if not approve and not feedback.strip():
        raise HTTPException(400, "Góp ý đang trống.")
    title = {"outline": "Duyệt outline → viết các tập", "final": "Chốt season"}.get(approve, "Góp ý")
    job = jobs.start("refine", f"{title} ({slug})",
                     {"slug": slug, "session_id": sid, "feedback": feedback.strip(), "target": target,
                      "approve": approve or None}, series.refine)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.post("/series/{slug}/{sid}/images")
async def images_start(slug: str, sid: str, kinds: list[str] = Form([]), ids: str = Form(""),
                       force: str = Form("")):
    d = series.session_dir(slug, sid)
    try:
        asset_images.latest_registry(d)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    if not config.find_codex_bin():
        raise HTTPException(400, "Không tìm thấy Codex CLI (cài extension ChatGPT/Codex hoặc đặt CODEX_BIN).")
    params = {"slug": slug, "session_id": sid, "kinds": [k for k in kinds if k in asset_images.KINDS],
              "ids": [i.strip() for i in ids.split(",") if i.strip()], "force": bool(force)}
    job = jobs.start("images", f"Tạo ảnh tham chiếu ({slug})", params, asset_images.run_images_job)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.post("/series/{slug}/{sid}/images/review")
async def images_review(slug: str, sid: str, file: str = Form(...), status: str = Form(...),
                        back: str = Form("chars")):
    try:
        asset_images.set_status(series.session_dir(slug, sid), file, status)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    view, _, anchor = back.partition("#")
    view = view if view in ASSET_VIEWS else "chars"
    return RedirectResponse(f"/series/{slug}/{sid}?view={view}" + (f"#{anchor}" if anchor.isidentifier() else ""),
                            status_code=303)


@app.post("/series/{slug}/{sid}/assets")
async def assets_start(slug: str, sid: str, feedback: str = Form("")):
    job = jobs.start("assets", f"{'Sửa ngoại hình' if feedback.strip() else 'Lập kho nhân vật & bối cảnh'} ({slug})",
                     {"slug": slug, "session_id": sid, "feedback": feedback.strip()}, series.build_assets)
    return RedirectResponse(f"/jobs/{job.id}", status_code=303)


@app.get("/series/{slug}/{sid}/assets/{path:path}")
def asset_file(slug: str, sid: str, path: str, w: int = 0):
    base = (series.session_dir(slug, sid) / "assets").resolve()
    f = (base / path).resolve()
    if not f.is_relative_to(base) or not f.is_file() or f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(404)
    if w:
        f = asset_images.thumbnail(f, max(120, min(w, 1200)))
    return FileResponse(f)


@app.get("/series/continue")
def continue_form(slug: str = "", sid: str = "", target: str = ""):
    """Moved to the React UI (/ui/continue); old links land there with the same series selected."""
    if target and "/" in target:
        slug, sid = target.split("/", 1)
    q = f"?slug={quote(slug)}&sid={quote(sid)}" if slug and sid else ""
    return RedirectResponse(f"/ui/continue{q}", status_code=303)


@app.get("/series/{slug}/{sid}/export")
def series_export(slug: str, sid: str):
    out = series.export_screenplay(slug, sid)
    return FileResponse(out, media_type="text/markdown", filename=f"{slug}_{sid}_{out.stem}.md")


# ---------- jobs ----------

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_view(request: Request, job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404)
    return page(request, "job.html", job=job.data)


@app.get("/jobs/{job_id}/status", response_class=HTMLResponse)
def job_status(request: Request, job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404)
    return page(request, "_job_status.html", job=job.data, live=jobs.is_running(job_id),
                log=job.tail(80), links=job_links(job.data), elapsed=elapsed(job.data))


@app.get("/jobs/{job_id}/watch")
def job_watch(job_id: str):
    """Polled by pages showing a running job: tells htmx to reload the page once the job ends."""
    from fastapi import Response
    if jobs.is_running(job_id):
        return Response(status_code=204)
    return Response(status_code=200, headers={"HX-Refresh": "true"})


@app.post("/jobs/{job_id}/cancel")
async def job_cancel(job_id: str):
    jobs.cancel(job_id)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


@app.post("/jobs/{job_id}/resume")
async def job_resume(job_id: str):
    job = jobs.get(job_id)
    if not job or jobs.is_running(job_id):
        raise HTTPException(400, "Không tìm thấy job hoặc job vẫn đang chạy.")
    jobs.start(job.data["kind"], job.data["title"], job.data["params"], JOB_FUNCS[job.data["kind"]], job=job)
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)


def job_links(data: dict) -> list[tuple[str, str, bool]]:
    """(label, href, primary). The primary link is the obvious next step once the job is done."""
    p, r = data.get("params", {}), data.get("result", {})
    done = data["status"] == "done"
    links = []
    if data["kind"] == "skill" and done:
        links.append(("Viết series với skill này", f"/series/new?slug={p['slug']}", True))
    if p.get("session_id"):
        links.append(("Mở series" if done else "Trang series", f"/series/{p['slug']}/{p['session_id']}", done))
    run_dir = r.get("run_dir") or p.get("run_dir")
    if run_dir:
        links.append(("Xem kết quả phân tích" if data["kind"] == "analysis" else "Bản phân tích nguồn",
                      f"/runs/{Path(run_dir).name}", done and data["kind"] == "analysis"))
    return links
