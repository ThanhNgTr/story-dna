"""JSON API for the React UI (web/ -> app/static/ui/). Runs next to the old Jinja pages.

Read endpoints return plain dicts; long work starts a job (same JobManager as the old UI) and the
UI follows it through Server-Sent Events: /api/events (job list) and /api/jobs/{id}/events (one job).
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from . import config, eta, hidden
from .jobs import Job, JobManager
from .pipeline import assets as asset_images
from .pipeline import analyze, package, screenplay, series, summary

DOC_KINDS = ("adaptation", "bible", "outline", "canon")


def _ts(s: str | None) -> float | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def job_summary(job: Job, live: bool, rates: dict | None = None) -> dict:
    d = job.data
    start, end = _ts(d.get("started_at")), _ts(d.get("finished_at"))
    now = datetime.now(timezone.utc).timestamp()
    status = d["status"]
    if status == "running" and not live:
        status = "interrupted"  # the server restarted under it
    return {
        "id": job.id, "kind": d["kind"], "title": d["title"], "status": status,
        "steps": d.get("steps", {}), "error": d.get("error"), "cost_usd": d.get("cost_usd", 0.0),
        "created_at": d.get("created_at"), "started_at": d.get("started_at"), "finished_at": d.get("finished_at"),
        "elapsed_sec": round((end or now) - start) if start else None,
        "eta_sec": eta.eta_sec(job, rates) if rates is not None and status == "running" else None,
        "slug": d.get("params", {}).get("slug"), "session_id": d.get("params", {}).get("session_id"),
        "result": {k: v for k, v in (d.get("result") or {}).items() if k != "last_reply"},
    }


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _rel(p: Path | None, base: Path) -> str | None:
    return str(p.relative_to(base)) if p else None


def _episode_files(d: Path, n: int) -> list[Path]:
    """All versions of episode n, oldest first."""
    files = [p for p in (d / "episodes").glob(f"ep{n:02d}_v*.json")
             if re.fullmatch(rf"ep{n:02d}_v\d+\.json", p.name)]
    return sorted(files, key=series._version)


class RefineIn(BaseModel):
    feedback: str = ""
    target: str = ""
    approve: str | None = None


class CommentIn(BaseModel):
    episode: int
    version: int = 0
    scene: str | None = None
    beat: int | None = None
    time: float | None = None
    quote: str = ""
    text: str


class CommentPatch(BaseModel):
    text: str | None = None
    status: str | None = None


class SendCommentsIn(BaseModel):
    ids: list[str] = []
    general: str = ""


class ContinueIn(BaseModel):
    slug: str
    sid: str = ""              # empty = series produced outside the app
    title: str = ""
    episode_sec: int = 90
    canon_mode: str = "transcript"   # transcript | full | none
    source: str = "videos"           # videos | run
    video_path: str = ""
    run_id: str = ""
    language: str = ""
    produced_upto: int = 1
    new_episodes: int = 6
    direction: str = "follow"
    idea: str = ""
    notes: str = ""
    update_skill: bool = False


class NewProjectIn(BaseModel):
    slug: str
    title: str = ""
    idea: str
    episodes: int = 12
    episode_sec: int = 90
    language: str = ""          # "" = language of the idea; else a key of series.LANGUAGES


class HideIn(BaseModel):
    kind: str
    item: str


class ImagesIn(BaseModel):
    kinds: list[str] = []
    ids: list[str] = []
    force: bool = False


class ReviewIn(BaseModel):
    files: list[str]
    status: str


class AssetsBuildIn(BaseModel):
    feedback: str = ""


class EditorIn(BaseModel):
    mode: str = "review"
    ids: list[str] = []
    rereview: bool = False


class ContinuityIn(BaseModel):
    mode: str = "fix"
    ids: list[str] = []


class ArchiveIn(BaseModel):
    episodes: list[int] | None = None  # None = every drafted episode
    rewrite: bool = False              # then write the missing episodes again (same as approving the outline)


class SettingsIn(BaseModel):
    auto_editor_outline: bool | None = None
    auto_editor_episodes: bool | None = None


class PolishIn(BaseModel):
    episodes: list[int] = []


class ShotlistIn(BaseModel):
    episodes: list[int] = []
    force: bool = False


class AssetsEdit(BaseModel):
    base_file: str
    data: dict
    note: str = ""


class EpisodeEdit(BaseModel):
    base_version: int
    data: dict
    note: str = ""


class AnalyzeIn(BaseModel):
    video_path: str
    language: str = ""
    chunk_sec: int = 120
    max_frames: int = 40
    force: bool = False


class SkillIn(BaseModel):
    run_id: str
    slug: str
    update: bool = False


class SummaryIn(BaseModel):
    target: str
    id: str
    force: bool = True


UPLOAD_MAX = 8 * 1024 ** 3  # 8 GB per file


def _editor_summary(view: dict | None) -> dict | None:
    if not view:
        return None
    sev = [f.get("severity") for f in view.get("findings") or []]
    return {"file": view["file"], "stage": view.get("stage"), "verdict": view.get("verdict"),
            "average": view.get("average"), "stale": view.get("stale"),
            "scores": {k: v.get("score") for k, v in (view.get("scores") or {}).items()},
            "findings": {s: sev.count(s) for s in ("high", "medium", "low")},
            "applied": len(view.get("applied") or [])}


def _continuity_summary(view: dict | None) -> dict | None:
    if not view:
        return None
    logic = view.get("logic")
    sev = [f.get("severity") for f in (logic or {}).get("findings") or []]
    return {**{k: view.get(k) for k in ("ok", "stage", "checked_at", "errors", "warnings", "state")},
            "logic": {"file": logic["file"], "verdict": logic.get("verdict"), "stale": logic.get("stale"),
                      "findings": {s: sev.count(s) for s in ("high", "medium", "low")},
                      "applied": len(logic.get("applied") or [])} if logic else None}


def build_router(jobs: JobManager, job_funcs: dict, stage: Callable[[dict], tuple[str, str]],
                 list_runs: Callable[[], list[dict]], item_busy: Callable[[str, str], bool], video) -> APIRouter:
    """`video`: helpers from main (videos_in, duration, estimate, covering) shared with the old pages."""
    r = APIRouter(prefix="/api")

    def summaries(js: list[Job]) -> list[dict]:
        rates = eta.history(jobs.list())
        return [job_summary(j, jobs.is_running(j.id), rates) for j in js]

    def one(job: Job) -> dict:
        return summaries([job])[0]

    def running_for(sid: str) -> Job | None:
        for j in jobs.list():
            if j.data["status"] == "running" and jobs.is_running(j.id) and j.data["params"].get("session_id") == sid:
                return j
        return None

    def session_or_404(slug: str, sid: str) -> dict:
        st = series.session_state(slug, sid)
        if not st["dir"].exists():
            raise HTTPException(404, "Không tìm thấy series.")
        return st

    # ---------- environment ----------

    @r.get("/health")
    def health():
        env = config.check_environment()
        return {"ok": bool(env["claude_bin"]), "env": env}

    # ---------- projects (series sessions) ----------

    @r.get("/projects")
    def projects():
        hid = hidden.hidden("series")
        out = []
        for s in series.list_sessions():
            if f"{s['slug']}/{s['session_id']}" in hid:
                continue
            label, tone = stage(s)
            inp = series.session_state(s["slug"], s["session_id"])["input"]
            out.append({**s, "stage": {"label": label, "tone": tone}, "created_at": inp.get("created_at"),
                        "episode_sec": inp.get("episode_sec")})
        return out

    @r.post("/continue")
    async def continue_create(body: ContinueIn):
        """Continue a series from its produced videos (same job as the old /series/continue form)."""
        mode = body.canon_mode if body.canon_mode in ("none", "transcript", "full") else "transcript"
        source = body.source
        if mode == "none":
            if not body.sid:
                raise HTTPException(400, "Series làm ngoài app không có kịch bản: cần chọn video (mức Nhanh hoặc Kỹ).")
            source = "none"
        elif source == "videos":
            if not body.video_path or not video.videos_in(Path(body.video_path).expanduser()):
                raise HTTPException(400, "Chưa chọn video đã làm.")
        elif source == "run":
            if not body.run_id or not (config.ANALYSES / body.run_id).exists():
                raise HTTPException(400, "Chưa chọn bản phân tích.")
        else:
            raise HTTPException(400, "Nguồn video không hợp lệ.")
        if body.slug not in series.list_series_skills():
            raise HTTPException(400, "Không có phong cách này (có thể đang bị ẩn).")
        sid, direction = body.sid, body.direction if body.direction in ("follow", "new-arc") else "follow"
        produced, new = max(1, body.produced_upto), max(1, min(20, body.new_episodes))
        if sid:
            session_or_404(body.slug, sid)
            if running_for(sid):
                raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi viết tiếp.")
        else:  # produced elsewhere: a new session holds the canon, bible and the next episodes
            sid = series.new_session(body.slug, "(Series produced outside this app; continue from the produced videos.)",
                                     produced + new, max(60, min(120, body.episode_sec)),
                                     body.title.strip() or "Series viết tiếp")
            direction = "new-arc"
        job = jobs.start("continue", f"Viết tiếp từ video đã làm ({body.slug})",
                         {"slug": body.slug, "session_id": sid,
                          "video_path": body.video_path if source == "videos" else None,
                          "run_id": body.run_id if source == "run" else None, "language": body.language or None,
                          "chunk_sec": 120, "max_frames": 40, "produced_upto": produced, "new_episodes": new,
                          "direction": direction, "idea": body.idea, "notes": body.notes, "canon_mode": mode,
                          "update_skill": body.update_skill and mode == "full"}, job_funcs["continue"])
        return {"slug": body.slug, "session_id": sid, "job": one(job)}

    @r.post("/projects")
    async def project_create(body: NewProjectIn):
        if body.slug not in series.list_series_skills():
            raise HTTPException(400, "Không có phong cách này.")
        if body.slug in hidden.hidden("skills"):
            raise HTTPException(400, "Phong cách này đang bị ẩn.")
        idea = body.idea.strip()
        if len(idea) < 20:
            raise HTTPException(400, "Ý tưởng quá ngắn: viết thêm vài dòng về nhân vật, bối cảnh hoặc cảnh bạn muốn có.")
        episodes = max(10, min(20, body.episodes))
        episode_sec = max(60, min(120, body.episode_sec))
        if body.language and body.language not in series.LANGUAGES:
            raise HTTPException(400, "Ngôn ngữ không hỗ trợ.")
        sid = series.new_session(body.slug, idea, episodes, episode_sec, body.title.strip(), body.language)
        job = jobs.start("outline", f"Viết outline: {body.title.strip() or body.slug}",
                         {"slug": body.slug, "session_id": sid, "episodes": episodes, "episode_sec": episode_sec,
                          "language": body.language},
                         job_funcs["outline"])
        return {"slug": body.slug, "session_id": sid, "job": one(job)}

    # ---------- styles (skills) + reference videos (analyses) ----------

    @r.get("/skills")
    def skills():
        runs = {x["id"]: x for x in list_runs()}
        used: dict[str, int] = {}
        for s in series.list_sessions():
            used[s["slug"]] = used.get(s["slug"], 0) + 1
        out = []
        for slug in series.list_series_skills():
            info = series.skill_info(slug)
            run = runs.get(info.get("run_id") or "")
            sm = summary.load(summary.skill_summary_path(slug))
            out.append({**info, "projects": used.get(slug, 0), "tagline_vi": (sm or {}).get("tagline_vi"),
                        "reference": {"id": run["id"], "title": run["title"], "minutes": run["minutes"],
                                      "sources": run["sources"]} if run else None})
        return out

    @r.get("/analyses")
    def analyses():
        hid = hidden.hidden("runs")
        out = []
        for x in list_runs():
            if x["id"] in hid:
                continue
            job = x.pop("job", None)
            x.pop("paths", None)
            sm = summary.load(summary.run_summary_path(config.ANALYSES / x["id"])) or {}
            out.append({**x, "job": one(job) if job else None, "title_vi": sm.get("title_vi"), "genre_vi": sm.get("genre_vi")})
        return out

    @r.post("/hide")
    def hide(body: HideIn):
        if body.kind not in hidden.KINDS:
            raise HTTPException(400, "Loại không hợp lệ.")
        if item_busy(body.kind, body.item):
            raise HTTPException(409, "Mục này đang có việc chạy. Đợi xong rồi ẩn.")
        try:
            hidden.hide(body.kind, body.item)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True}

    @r.post("/unhide")
    def unhide(body: HideIn):
        if body.kind not in hidden.KINDS:
            raise HTTPException(400, "Loại không hợp lệ.")
        try:
            hidden.unhide(body.kind, body.item)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True}

    @r.get("/hidden")
    def hidden_list():
        return {k: sorted(hidden.hidden(k)) for k in hidden.KINDS}

    @r.get("/projects/{slug}/{sid}")
    def project(slug: str, sid: str):
        st = session_or_404(slug, sid)
        d = st["dir"]
        final_eps = {int(m.group(1)) for f in (d / "final").glob("ep*.json")
                     if (m := re.fullmatch(r"ep(\d+)\.json", f.name))}
        episodes = []
        for n in sorted(set(st["episodes"]) | final_eps):
            files = _episode_files(d, n)
            latest = files[-1] if files else d / "final" / f"ep{n:02d}.json"
            try:
                ep = json.loads(latest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                ep = {}
            episodes.append({
                "n": n, "versions": [series._version(f) for f in files], "in_final": n in final_eps,
                "title": ep.get("title"), "logline": ep.get("logline"),
                "duration_sec": ep.get("total_duration_sec"), "cliffhanger_type": ep.get("cliffhanger_type"),
                "produced": n <= st["produced_upto"],
                "has_prompts": package.prompts_file(d, n) is not None,
                "prompts_stale": package.prompts_stale(d, n),
                "prompts_outdated": package.prompts_outdated(d, n),
            })
        summary = {"session_id": sid, "episodes": len(st["episodes"]), "final": st["final_complete"],
                   "final_stale": st["final_stale"],
                   "has_outline": st["outline"] is not None, "missing": st["missing"], "produced": st["produced_upto"]}
        label, tone = stage(summary)
        av = asset_images.view_model(d)
        job = running_for(sid)
        inp = st["input"]
        return {
            "slug": slug, "session_id": sid, "title": inp.get("title") or sid,
            "skill": series.skill_info(slug),
            "input": {k: inp.get(k) for k in ("episodes", "episode_sec", "language", "created_at", "status")},
            "stage": {"label": label, "tone": tone},
            "planned": st["planned"], "produced_upto": st["produced_upto"], "missing": st["missing"],
            "outline_approved": st["outline_approved"], "final_complete": st["final_complete"],
            "final_stale": st["final_stale"],
            "settings": series.session_settings(d),
            "video_targets": list(config.VIDEO_TARGETS),
            "cost_usd": round(sum(float(j.data.get("cost_usd") or 0) for j in jobs.list()
                                  if (j.data.get("params") or {}).get("session_id") == sid), 2),
            "docs": {k: ([series._version(p) for p in st["versions"][k]] if k in st["versions"]
                         else ([0] if st[k] else [])) for k in DOC_KINDS},
            "episodes": episodes,
            "assets": {"file": av["file"], "counts": av["counts"], "issues": len(av["reg"].get("issues", []))} if av else None,
            "iterations": st["iterations"],
            "story_check": series.story_check_view(slug, sid) if not job else None,
            "editor": _editor_summary(series.editor_view(slug, sid)),
            "continuity": _continuity_summary(series.continuity_view(slug, sid)) if not job else None,
            "job": one(job) if job else None,
        }

    @r.get("/projects/{slug}/{sid}/docs/{kind}")
    def doc(slug: str, sid: str, kind: str, v: int = 0):
        if kind not in DOC_KINDS:
            raise HTTPException(404)
        st = session_or_404(slug, sid)
        d = st["dir"]
        if kind == "adaptation":
            md_path = st["adaptation"]
        else:
            versions = st["versions"].get(kind, [])
            md_path = next((p for p in versions if series._version(p) == v), None) if v else st[kind]
        if not md_path or not md_path.exists():
            raise HTTPException(404, "Chưa có tài liệu này.")
        js = md_path.with_suffix(".json")
        return {"kind": kind, "file": _rel(md_path, d), "version": series._version(md_path),
                "markdown": md_path.read_text(encoding="utf-8"),
                "data": json.loads(js.read_text(encoding="utf-8")) if js.exists() else None}

    @r.get("/projects/{slug}/{sid}/episodes/{n}")
    def episode(slug: str, sid: str, n: int, v: int = 0):
        st = session_or_404(slug, sid)
        d = st["dir"]
        files = _episode_files(d, n)
        if v:
            path = next((f for f in files if series._version(f) == v), None)
        else:
            path = files[-1] if files else (d / "final" / f"ep{n:02d}.json")
        if not path or not path.exists():
            raise HTTPException(404, "Chưa có tập này.")
        md = path.with_suffix(".md")
        return {"n": n, "file": _rel(path, d), "version": series._version(path) if path.parent.name == "episodes" else 0,
                "versions": [series._version(f) for f in files],
                "data": json.loads(path.read_text(encoding="utf-8")),
                "markdown": md.read_text(encoding="utf-8") if md.exists() else None}

    @r.post("/projects/{slug}/{sid}/refine")
    async def refine(slug: str, sid: str, body: RefineIn):
        session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi gửi tiếp.")
        if not body.approve and not body.feedback.strip():
            raise HTTPException(400, "Góp ý đang trống.")
        title = {"outline": "Duyệt outline → viết các tập", "final": "Chốt season"}.get(body.approve or "", "Góp ý")
        job = jobs.start("refine", f"{title} ({slug})",
                         {"slug": slug, "session_id": sid, "feedback": body.feedback.strip(),
                          "target": body.target, "approve": body.approve or None}, job_funcs["refine"])
        return one(job)

    # ---------- review comments + manual edits ----------

    @r.get("/projects/{slug}/{sid}/comments")
    def comments(slug: str, sid: str, episode: int | None = None):
        st = session_or_404(slug, sid)
        cs = screenplay.load_comments(st["dir"])
        return [c for c in cs if episode is None or c["episode"] == episode]

    @r.post("/projects/{slug}/{sid}/comments")
    def comment_add(slug: str, sid: str, body: CommentIn):
        if not body.text.strip():
            raise HTTPException(400, "Góp ý đang trống.")
        return screenplay.add_comment(session_or_404(slug, sid)["dir"], body.model_dump())

    @r.patch("/projects/{slug}/{sid}/comments/{cid}")
    def comment_patch(slug: str, sid: str, cid: str, body: CommentPatch):
        try:
            return screenplay.update_comment(session_or_404(slug, sid)["dir"], cid, body.model_dump())
        except KeyError:
            raise HTTPException(404)

    @r.delete("/projects/{slug}/{sid}/comments/{cid}")
    def comment_delete(slug: str, sid: str, cid: str):
        try:
            screenplay.delete_comment(session_or_404(slug, sid)["dir"], cid)
        except KeyError:
            raise HTTPException(404)
        return {"ok": True}

    @r.post("/projects/{slug}/{sid}/comments/send")
    async def comments_send(slug: str, sid: str, body: SendCommentsIn):
        d = session_or_404(slug, sid)["dir"]
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi gửi tiếp.")
        open_ = [c for c in screenplay.load_comments(d) if c["status"] == "open" and (not body.ids or c["id"] in body.ids)]
        if not open_:
            raise HTTPException(400, "Không có góp ý nào đang mở để gửi.")
        text, target = screenplay.feedback_from_comments(open_, body.general)
        job = jobs.start("refine", f"Góp ý {len(open_)} điểm ({slug})",
                         {"slug": slug, "session_id": sid, "feedback": text, "target": target, "approve": None},
                         job_funcs["refine"])
        screenplay.mark_sent(d, [c["id"] for c in open_], job.id)
        return one(job)

    @r.put("/projects/{slug}/{sid}/episodes/{n}")
    def episode_save(slug: str, sid: str, n: int, body: EpisodeEdit):
        d = session_or_404(slug, sid)["dir"]
        if running_for(sid):
            raise HTTPException(409, "Claude đang làm việc với series này. Đợi xong rồi lưu, để không ghi đè lên nhau.")
        try:
            out = screenplay.save_manual(d, n, body.data, body.base_version, body.note)
            series.refresh_dialogue_examples()  # hand-edited lines teach the next writing rounds
            return out
        except ValueError as e:
            raise HTTPException(409 if "phiên bản mới" in str(e) else 400, str(e))

    # ---------- looks: asset registry + reference images ----------

    @r.get("/projects/{slug}/{sid}/assets")
    def assets_view(slug: str, sid: str):
        d = session_or_404(slug, sid)["dir"]
        vm = asset_images.view_model(d)
        return {"registry": vm, "codex": bool(config.find_codex_bin()),
                "base": f"/series/{slug}/{sid}/assets"}

    @r.post("/projects/{slug}/{sid}/assets/images")
    async def assets_images(slug: str, sid: str, body: ImagesIn):
        d = session_or_404(slug, sid)["dir"]
        try:
            asset_images.latest_registry(d)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        if not config.find_codex_bin():
            raise HTTPException(400, "Không tìm thấy Codex CLI (cài extension ChatGPT/Codex hoặc đặt CODEX_BIN).")
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi tạo ảnh.")
        kinds = [k for k in body.kinds if k in asset_images.KINDS] or list(asset_images.DEFAULT_KINDS)
        if not asset_images.plan(d, tuple(kinds), set(body.ids) or None, body.force):
            raise HTTPException(400, "Không còn ảnh nào cần tạo cho lựa chọn này.")
        job = jobs.start("images", f"Tạo ảnh tham chiếu ({slug})",
                         {"slug": slug, "session_id": sid, "kinds": kinds, "ids": body.ids, "force": body.force},
                         job_funcs["images"])
        return one(job)

    @r.post("/projects/{slug}/{sid}/assets/review")
    def assets_review(slug: str, sid: str, body: ReviewIn):
        if body.status not in ("approved", "rejected", "draft"):
            raise HTTPException(400, "Trạng thái không hợp lệ.")
        n = asset_images.set_status_many(session_or_404(slug, sid)["dir"], body.files, body.status)
        return {"updated": n}

    @r.get("/projects/{slug}/{sid}/editor")
    def editor(slug: str, sid: str):
        session_or_404(slug, sid)
        view = series.editor_view(slug, sid)
        if not view:
            raise HTTPException(404, "Chưa có bản biên tập.")
        md = series.session_dir(slug, sid) / "editor" / view["file"].replace(".json", ".md")
        return {**view, "markdown": md.read_text(encoding="utf-8") if md.exists() else None}

    @r.post("/projects/{slug}/{sid}/editor")
    async def editor_run(slug: str, sid: str, body: EditorIn):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi biên tập.")
        if st["outline"] is None:
            raise HTTPException(400, "Chưa có outline để biên tập.")
        if body.mode == "apply":
            if not series.editor_view(slug, sid):
                raise HTTPException(400, "Chưa có bản biên tập.")
            if not body.ids:
                raise HTTPException(400, "Chọn ít nhất một điểm cần sửa.")
            title = f"Áp dụng {len(body.ids)} sửa của biên tập"
        else:
            title = "Biên tập kịch bản"
        job = jobs.start("editor", f"{title} ({slug})",
                         {"slug": slug, "session_id": sid, "mode": "apply" if body.mode == "apply" else "review",
                          "ids": body.ids, "rereview": body.rereview}, job_funcs["editor"])
        return one(job)

    @r.get("/projects/{slug}/{sid}/dialogue")
    def dialogue(slug: str, sid: str):
        session_or_404(slug, sid)
        view = series.dialogue_view(slug, sid)
        if view is None:
            raise HTTPException(404, "Chưa có tập nào.")
        return view

    @r.post("/projects/{slug}/{sid}/dialogue/polish")
    async def dialogue_polish(slug: str, sid: str, body: PolishIn):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi làm rõ thoại.")
        if not st["episodes"]:
            raise HTTPException(400, "Chưa có tập nào.")
        what = f"tập {', '.join(map(str, body.episodes))}" if body.episodes else "tất cả các tập"
        job = jobs.start("dialogue", f"Làm rõ thoại {what} ({slug})",
                         {"slug": slug, "session_id": sid, "episodes": body.episodes}, job_funcs["dialogue"])
        return one(job)

    @r.post("/projects/{slug}/{sid}/action/polish")
    async def action_polish(slug: str, sid: str, body: PolishIn):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi bổ sung diễn xuất.")
        if not st["episodes"]:
            raise HTTPException(400, "Chưa có tập nào.")
        what = f"tập {', '.join(map(str, body.episodes))}" if body.episodes else "tất cả các tập"
        job = jobs.start("action", f"Bổ sung diễn xuất {what} ({slug})",
                         {"slug": slug, "session_id": sid, "episodes": body.episodes}, job_funcs["action"])
        return one(job)

    @r.put("/projects/{slug}/{sid}/settings")
    def settings_save(slug: str, sid: str, body: SettingsIn):
        d = session_or_404(slug, sid)["dir"]
        return series.save_settings(d, {k: v for k, v in body.model_dump().items() if v is not None})

    @r.post("/projects/{slug}/{sid}/episodes/archive")
    async def episodes_archive(slug: str, sid: str, body: ArchiveIn):  # async: jobs.start needs the event loop
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi xóa tập.")
        if body.rewrite and st["outline"] is None:
            raise HTTPException(400, "Chưa có outline để viết lại các tập.")
        try:
            out = series.archive_episodes(slug, sid, body.episodes)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        if body.rewrite:
            job = jobs.start("refine", f"Viết lại các tập ({slug})",
                             {"slug": slug, "session_id": sid, "feedback": "", "target": "", "approve": "outline"},
                             job_funcs["refine"])
            out["job"] = one(job)
        return out

    @r.post("/projects/{slug}/{sid}/final/refresh")
    def final_refresh(slug: str, sid: str):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi chốt lại.")
        if not st["final_stale"]:
            raise HTTPException(400, "Bản chốt đã là bản mới nhất.")
        return series.refinalize(slug, sid)

    @r.post("/projects/{slug}/{sid}/shotlist")
    async def shotlist(slug: str, sid: str, body: ShotlistIn):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi tạo prompt.")
        if not (st["dir"] / "final").exists():
            raise HTTPException(400, "Chốt season trước: prompt video được tạo từ bản cuối (final/).")
        if "assets" in st["final_stale"]:
            raise HTTPException(400, "Bộ ngoại hình có sửa sau khi chốt: bấm “Chốt lại” ở trang Tổng quan trước, "
                                     "để prompt video dùng trang phục, bối cảnh mới nhất.")
        stale = [x for x in st["final_stale"] if isinstance(x, int) and (not body.episodes or x in body.episodes)]
        if stale:
            raise HTTPException(400, f"Tập {', '.join(map(str, stale))} có sửa sau khi chốt: bấm “Chốt lại” ở trang Tổng quan "
                                     "trước, để prompt video dùng bản mới nhất.")
        what = f"tập {', '.join(map(str, body.episodes))}" if body.episodes else "các tập chưa có prompt"
        job = jobs.start("shotlist", f"Tạo prompt video {what} ({slug})",
                         {"slug": slug, "session_id": sid, "episodes": body.episodes, "force": body.force},
                         job_funcs["shotlist"])
        return one(job)

    @r.get("/projects/{slug}/{sid}/episodes/{n}/prompts")
    def episode_prompts(slug: str, sid: str, n: int):
        view = package.prompts_view(session_or_404(slug, sid)["dir"], n)
        if view is None:
            raise HTTPException(404, f"Tập {n} chưa có prompt video.")
        return view

    @r.get("/projects/{slug}/{sid}/episodes/{n}/package")
    def episode_package(slug: str, sid: str, n: int, background: BackgroundTasks, target: str = "higgsfield"):
        st = session_or_404(slug, sid)
        build = package.build_flow_package if target == "flow" else package.build_episode_package
        try:
            path, name = build(st["dir"], n, st["input"].get("title") or "")
        except FileNotFoundError as e:
            raise HTTPException(404, str(e))
        background.add_task(path.unlink, missing_ok=True)
        return FileResponse(path, media_type="application/zip", filename=name)

    @r.post("/projects/{slug}/{sid}/story/fix")
    async def story_fix(slug: str, sid: str):
        session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi sửa.")
        job = jobs.start("story", f"Sửa cốt truyện theo yêu cầu bắt buộc ({slug})",
                         {"slug": slug, "session_id": sid}, job_funcs["story"])
        return one(job)

    @r.get("/projects/{slug}/{sid}/continuity")
    def continuity(slug: str, sid: str):
        session_or_404(slug, sid)
        view = series.continuity_view(slug, sid)
        if view is None:
            raise HTTPException(404, "Chưa có outline.")
        logic = view.get("logic")
        if logic:
            md = series.session_dir(slug, sid) / "continuity" / logic["file"].replace(".json", ".md")
            view["logic"] = {**logic, "markdown": md.read_text(encoding="utf-8") if md.exists() else None}
        return view

    @r.post("/projects/{slug}/{sid}/continuity")
    async def continuity_run(slug: str, sid: str, body: ContinuityIn):
        st = session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi kiểm tra.")
        if st["outline"] is None:
            raise HTTPException(400, "Chưa có outline để kiểm tra.")
        if body.mode not in ("fix", "review", "apply"):
            raise HTTPException(400, "Chế độ không hợp lệ.")
        if body.mode == "apply":
            if not series.logic_view(st["dir"]):
                raise HTTPException(400, "Chưa có bản rà logic.")
            if not body.ids:
                raise HTTPException(400, "Chọn ít nhất một lỗi logic cần sửa.")
        title = {"fix": "Sửa liên mạch giữa các tập", "review": "Rà logic toàn mùa",
                 "apply": f"Áp dụng {len(body.ids)} sửa logic"}[body.mode]
        job = jobs.start("continuity", f"{title} ({slug})",
                         {"slug": slug, "session_id": sid, "mode": body.mode, "ids": body.ids}, job_funcs["continuity"])
        return one(job)

    @r.post("/projects/{slug}/{sid}/assets/build")
    async def assets_build(slug: str, sid: str, body: AssetsBuildIn):
        session_or_404(slug, sid)
        if running_for(sid):
            raise HTTPException(409, "Series này đang có việc chạy. Đợi xong rồi cập nhật kho.")
        title = "Sửa ngoại hình" if body.feedback.strip() else "Lập / cập nhật kho nhân vật & bối cảnh"
        job = jobs.start("assets", f"{title} ({slug})",
                         {"slug": slug, "session_id": sid, "feedback": body.feedback.strip()}, job_funcs["assets"])
        return one(job)

    @r.put("/projects/{slug}/{sid}/assets")
    def assets_save(slug: str, sid: str, body: AssetsEdit):
        d = session_or_404(slug, sid)["dir"]
        if running_for(sid):
            raise HTTPException(409, "Đang có việc chạy cho series này. Đợi xong rồi lưu.")
        try:
            return asset_images.save_registry_edit(d, body.base_file, body.data, body.note)
        except ValueError as e:
            raise HTTPException(409 if "phiên bản mới" in str(e) else 400, str(e))

    # ---------- reference videos: pick, upload, analyze, read ----------

    def in_roots(p: Path) -> bool:
        return any(p == r or r in p.parents for r in config.BROWSE_ROOTS)

    @r.get("/browse")
    def browse(path: str = ""):
        p = Path(path).expanduser().resolve() if path else config.INPUT.resolve()
        if not in_roots(p) or not p.is_dir():
            p = config.INPUT.resolve() if config.INPUT.exists() else config.BROWSE_ROOTS[0]
        entries = []
        try:
            for c in sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
                if c.name.startswith("."):
                    continue
                if c.is_dir():
                    entries.append({"name": c.name, "path": str(c), "dir": True})
                elif c.suffix.lower() in config.VIDEO_EXTS:
                    entries.append({"name": c.name, "path": str(c), "dir": False, "size_mb": round(c.stat().st_size / 1e6)})
        except PermissionError:
            pass
        parent = p.parent if p.parent != p and in_roots(p.parent) else None
        n_videos = sum(1 for e in entries if not e["dir"]) if p == Path.home() else len(video.videos_in(p))
        return {"cwd": str(p), "parent": str(parent) if parent else None, "entries": entries, "n_videos": n_videos,
                "input_dir": str(config.INPUT)}

    @r.get("/probe")
    def probe(path: str):
        vp = Path(path).expanduser()
        if not in_roots(vp.resolve()):
            raise HTTPException(400, "Đường dẫn nằm ngoài các thư mục được phép.")
        vids = video.videos_in(vp) if vp.exists() else []
        items = [{"name": str(v.relative_to(vp)) if vp.is_dir() else v.name, "duration_sec": video.duration(v)} for v in vids]
        durs = [i["duration_sec"] for i in items if i["duration_sec"]]
        return {"path": str(vp), "is_dir": vp.is_dir(), "items": items, "minutes": round(sum(durs) / 60, 1),
                "estimate": video.estimate(durs) if durs else None,
                "existing": [{k: x[k] for k in ("id", "title", "sources", "done", "analyzed", "units")} for x in video.covering(vids)]}

    @r.post("/uploads")
    async def upload(request: Request, name: str, folder: str = ""):
        """Stream one video into data/input/<folder>/ (the browser sends the raw file as the body)."""
        fname = Path(name).name
        if Path(fname).suffix.lower() not in config.VIDEO_EXTS:
            raise HTTPException(400, f"Chỉ nhận video: {', '.join(sorted(config.VIDEO_EXTS))}")
        sub = series.slugify(folder) if folder else ""
        dest_dir = (config.INPUT / sub) if sub else config.INPUT
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fname
        if dest.exists():
            raise HTTPException(409, f"Đã có {dest.name} trong {dest_dir}. Đổi tên file hoặc chọn nó ở tab Trên máy này.")
        part = dest.with_suffix(dest.suffix + ".part")
        size = 0
        try:
            with part.open("wb") as f:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > UPLOAD_MAX:
                        raise HTTPException(413, "File quá lớn (tối đa 8 GB).")
                    f.write(chunk)
            part.rename(dest)
        finally:
            part.unlink(missing_ok=True)
        return {"path": str(dest), "folder": str(dest_dir), "size_mb": round(size / 1e6)}

    @r.post("/analyses")
    async def analyze_start(body: AnalyzeIn):
        vp = Path(body.video_path).expanduser()
        if not in_roots(vp.resolve()):
            raise HTTPException(400, "Đường dẫn nằm ngoài các thư mục được phép.")
        vids = video.videos_in(vp) if vp.exists() else []
        if not vids:
            raise HTTPException(400, f"Không tìm thấy video nào ở: {vp}")
        existing = video.covering(vids)
        if existing and not body.force:
            wanted = {str(v.resolve()) for v in vids}
            full = [x for x in existing if wanted <= set(x["paths"])]
            raise HTTPException(409, {"message": "Đã từng học các video này.", "partial": not full,
                                      "existing": [{k: x[k] for k in ("id", "title", "sources", "done")} for x in (full or existing)]})
        label = f"{vp.name}/ ({len(vids)} video)" if vp.is_dir() else vp.name
        job = jobs.start("analysis", f"Học video: {label}",
                         {"video_path": str(vp), "language": body.language or None, "chunk_sec": body.chunk_sec,
                          "max_frames": body.max_frames}, analyze.run_analysis)
        return one(job)

    def run_or_404(run_id: str) -> Path:
        d = config.ANALYSES / run_id
        if not re.fullmatch(r"[\w.-]+", run_id) or not (d / "manifest.json").exists():
            raise HTTPException(404, "Không tìm thấy bản phân tích.")
        return d

    @r.get("/analyses/{run_id}")
    def analysis(run_id: str):
        d = run_or_404(run_id)
        m = json.loads((d / "manifest.json").read_text())
        dna = summary.load(d / "dna.json") or {}
        units = [{"id": u["unit_id"], "start": u["t_start"], "end": u["t_end"], "source": u.get("source"),
                  "done": (d / "dna" / f"{u['unit_id']}.dna.json").exists()} for u in m.get("units", [])]
        run = next((x for x in list_runs() if x["id"] == run_id), {})
        job = run.get("job")
        suggested = "-".join(series.slugify(dna.get("title") or dna.get("genre") or "series").split("-")[:3])
        return {
            "id": run_id, "title": dna.get("title"), "genre": dna.get("genre"), "logline": dna.get("logline"),
            "sources": [{"filename": x.get("filename"), "duration_sec": x.get("duration_sec")} for x in m.get("sources", [])],
            "minutes": run.get("minutes"), "language": run.get("language"), "units": units,
            "done": run.get("done", False), "skills": run.get("skills", []),
            "docs": {k: (d / f).exists() for k, f in (("story", "story.md"), ("dna", "dna.md"), ("analysis", "film_analysis.md"))},
            "characters": [{"name": c.get("name"), "tier": c.get("tier")} for c in dna.get("characters", []) if isinstance(c, dict)],
            "summary_vi": summary.load(summary.run_summary_path(d)),
            "suggested_slug": suggested, "job": one(job) if job else None,
        }

    @r.get("/analyses/{run_id}/doc/{kind}")
    def analysis_doc(run_id: str, kind: str):
        d = run_or_404(run_id)
        f = {"story": "story.md", "dna": "dna.md", "analysis": "film_analysis.md"}.get(kind)
        if not f or not (d / f).exists():
            raise HTTPException(404, "Chưa có tài liệu này.")
        return {"kind": kind, "markdown": (d / f).read_text(encoding="utf-8")}

    @r.post("/analyses/{run_id}/resume")
    async def analysis_resume(run_id: str):
        d = run_or_404(run_id)
        if item_busy("runs", run_id):
            raise HTTPException(409, "Bản phân tích này đang chạy.")
        return one(jobs.start("analysis", f"Chạy tiếp phân tích {run_id}", {"run_dir": str(d)}, analyze.run_analysis))

    # ---------- writing styles (skills) ----------

    @r.post("/skills")
    async def skill_create(body: SkillIn):
        run_or_404(body.run_id)
        slug = series.slugify(body.slug)
        if not slug:
            raise HTTPException(400, "Tên phong cách không hợp lệ.")
        if series.skill_dir(slug).exists() and not body.update:
            raise HTTPException(409, f"Phong cách {slug} đã có. Đổi tên hoặc chọn cập nhật phong cách có sẵn.")
        if item_busy("skills", slug):
            raise HTTPException(409, "Phong cách này đang được tạo / cập nhật.")
        job = jobs.start("skill", f"{'Cập nhật' if body.update else 'Tạo'} phong cách {slug}",
                         {"run_dir": str(config.ANALYSES / body.run_id), "slug": slug, "update": body.update}, job_funcs["skill"])
        return one(job)

    @r.get("/skills/{slug}")
    def skill_detail(slug: str):
        if slug not in series.list_series_skills():
            raise HTTPException(404, "Không có phong cách này.")
        info = series.skill_info(slug)
        versions = []
        for f in sorted(config.DATA.glob(f"skills-generated/write-series-{slug}_v*.json"), key=series._version):
            m = summary.load(f) or {}
            versions.append({"version": m.get("version") or f"v{series._version(f)}",
                             "created": m.get("created_timestamp") or m.get("created_at"),
                             "changes": m.get("changes") or [], "stable": bool(m.get("stable"))})
        runs = {x["id"]: x for x in list_runs()}
        run = runs.get(info.get("run_id") or "")
        projects = [{"slug": x["slug"], "session_id": x["session_id"], "title": x["title"]}
                    for x in series.list_sessions() if x["slug"] == slug]
        sm = summary.load(summary.skill_summary_path(slug))
        return {**info, "versions": versions, "projects": projects,
                "reference": {"id": run["id"], "title": run["title"], "minutes": run["minutes"]} if run else None,
                "summary_vi": sm, "summary_stale": bool(sm and sm.get("version") != info.get("version")),
                "skill_md": (series.skill_dir(slug) / "SKILL.md").read_text(encoding="utf-8")}

    @r.post("/summaries")
    async def summary_start(body: SummaryIn):
        if body.target == "run":
            run_or_404(body.id)
        elif body.target != "skill" or body.id not in series.list_series_skills():
            raise HTTPException(400, "Không rõ cần tóm tắt cái gì.")
        title = f"Tóm tắt tiếng Việt: {body.id}"
        return one(jobs.start("summary", title, body.model_dump(), job_funcs["summary"]))

    # ---------- jobs ----------

    @r.get("/jobs")
    def job_list(limit: int = 30):
        return summaries(jobs.list()[:limit])

    @r.get("/jobs/{job_id}")
    def job_get(job_id: str, tail: int = 200):
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404)
        return {**one(job), "log": job.tail(tail),
                "last_reply": (job.data.get("result") or {}).get("last_reply")}

    @r.post("/jobs/{job_id}/cancel")
    async def job_cancel(job_id: str):
        if not jobs.cancel(job_id):
            raise HTTPException(409, "Việc này không còn chạy.")
        return {"ok": True}

    @r.post("/jobs/{job_id}/resume")
    async def job_resume(job_id: str):
        job = jobs.get(job_id)
        if not job or jobs.is_running(job_id) or job.data["kind"] not in job_funcs:
            raise HTTPException(409, "Không chạy tiếp được việc này.")
        jobs.start(job.data["kind"], job.data["title"], job.data["params"], job_funcs[job.data["kind"]], job=job)
        return one(job)

    @r.get("/events")
    async def events():
        """Active + recent jobs, pushed whenever anything changes (job center, page refreshes)."""
        async def gen():
            last, pushed = None, 0.0
            while True:
                snap = summaries(jobs.list()[:15])
                # eta changes every tick; push it at most every ~30s unless something else changed
                key = json.dumps([(s["id"], s["status"], s["steps"]) for s in snap])
                if key == last and time.monotonic() - pushed > 30:
                    last = None
                if key != last:
                    last, pushed = key, time.monotonic()
                    yield _sse("jobs", snap)
                else:
                    yield ": ping\n\n"
                await asyncio.sleep(2)
        return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    @r.get("/jobs/{job_id}/events")
    async def job_events(job_id: str):
        """One job: state on change + new log lines; ends after the job finishes."""
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404)

        async def gen():
            last_key, log_pos = None, 0
            while True:
                j = jobs.get(job_id)
                live = jobs.is_running(job_id)
                s = one(j)
                key = json.dumps([s["status"], s["steps"], s["error"]])
                if key != last_key:
                    last_key = key
                    yield _sse("job", s)
                if j.log_path.exists():
                    with j.log_path.open("rb") as f:
                        f.seek(log_pos)
                        chunk = f.read()
                        log_pos = f.tell()
                    lines = chunk.decode(errors="replace").splitlines()
                    if lines:
                        yield _sse("log", lines)
                if not live and s["status"] != "running":
                    yield _sse("end", {"status": s["status"]})
                    return
                await asyncio.sleep(1)
        return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    return r
