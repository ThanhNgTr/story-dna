"""JSON API for the React UI (web/ -> app/static/ui/). Runs next to the old Jinja pages.

Read endpoints return plain dicts; long work starts a job (same JobManager as the old UI) and the
UI follows it through Server-Sent Events: /api/events (job list) and /api/jobs/{id}/events (one job).
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import config
from .jobs import Job, JobManager
from .pipeline import assets as asset_images
from .pipeline import screenplay, series

DOC_KINDS = ("adaptation", "bible", "outline", "canon")


def _ts(s: str | None) -> float | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def job_summary(job: Job, live: bool) -> dict:
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


class EpisodeEdit(BaseModel):
    base_version: int
    data: dict
    note: str = ""


def build_router(jobs: JobManager, job_funcs: dict, stage: Callable[[dict], tuple[str, str]]) -> APIRouter:
    r = APIRouter(prefix="/api")

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
        out = []
        for s in series.list_sessions():
            label, tone = stage(s)
            out.append({**s, "stage": {"label": label, "tone": tone}})
        return out

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
            })
        summary = {"session_id": sid, "episodes": len(st["episodes"]), "final": st["final_complete"],
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
            "docs": {k: ([series._version(p) for p in st["versions"][k]] if k in st["versions"]
                         else ([0] if st[k] else [])) for k in DOC_KINDS},
            "episodes": episodes,
            "assets": {"file": av["file"], "counts": av["counts"], "issues": len(av["reg"].get("issues", []))} if av else None,
            "iterations": st["iterations"],
            "job": job_summary(job, True) if job else None,
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
        return job_summary(job, True)

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
        return job_summary(job, True)

    @r.put("/projects/{slug}/{sid}/episodes/{n}")
    def episode_save(slug: str, sid: str, n: int, body: EpisodeEdit):
        d = session_or_404(slug, sid)["dir"]
        if running_for(sid):
            raise HTTPException(409, "Claude đang làm việc với series này. Đợi xong rồi lưu, để không ghi đè lên nhau.")
        try:
            return screenplay.save_manual(d, n, body.data, body.base_version, body.note)
        except ValueError as e:
            raise HTTPException(409 if "phiên bản mới" in str(e) else 400, str(e))

    # ---------- jobs ----------

    @r.get("/jobs")
    def job_list(limit: int = 30):
        return [job_summary(j, jobs.is_running(j.id)) for j in jobs.list()[:limit]]

    @r.get("/jobs/{job_id}")
    def job_get(job_id: str, tail: int = 200):
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404)
        return {**job_summary(job, jobs.is_running(job_id)), "log": job.tail(tail),
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
        return job_summary(job, True)

    @r.get("/events")
    async def events():
        """Active + recent jobs, pushed whenever anything changes (job center, page refreshes)."""
        async def gen():
            last = None
            while True:
                snap = [job_summary(j, jobs.is_running(j.id)) for j in jobs.list()[:15]]
                key = json.dumps([(s["id"], s["status"], s["steps"]) for s in snap])
                if key != last:
                    last = key
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
                s = job_summary(j, live)
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
