"""Background jobs: one asyncio task per job, state + log persisted under data/jobs/."""

from __future__ import annotations

import asyncio
import json
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from . import config


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Job:
    def __init__(self, data: dict):
        self.data = data

    @property
    def id(self) -> str:
        return self.data["id"]

    @property
    def path(self) -> Path:
        return config.JOBS / f"{self.id}.json"

    @property
    def log_path(self) -> Path:
        return config.JOBS / f"{self.id}.log"

    def save(self):
        self.data["updated_at"] = now()
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def log(self, msg: str):
        with self.log_path.open("a") as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")

    def step(self, name: str, status: str, **extra):
        """Record progress of a named step (shown as a checklist in the UI)."""
        steps = self.data.setdefault("steps", {})
        steps[name] = {**steps.get(name, {}), "status": status, **extra, "at": now()}
        self.save()

    def add_cost(self, usd: float):
        self.data["cost_usd"] = round(self.data.get("cost_usd", 0.0) + (usd or 0.0), 4)
        self.save()

    def tail(self, n: int = 40) -> list[str]:
        if not self.log_path.exists():
            return []
        return self.log_path.read_text(errors="replace").splitlines()[-n:]


class JobManager:
    def __init__(self):
        config.JOBS.mkdir(parents=True, exist_ok=True)
        self.tasks: dict[str, asyncio.Task] = {}
        # Jobs that were running when the server stopped cannot continue in memory
        for job in self.list():
            if job.data["status"] in ("running", "queued"):
                job.data["status"] = "interrupted"
                job.save()

    def get(self, job_id: str) -> Job | None:
        p = config.JOBS / f"{job_id}.json"
        return Job(json.loads(p.read_text())) if p.exists() else None

    def list(self) -> list[Job]:
        jobs = [Job(json.loads(p.read_text())) for p in config.JOBS.glob("*.json")]
        return sorted(jobs, key=lambda j: j.data["created_at"], reverse=True)

    def start(self, kind: str, title: str, params: dict,
              fn: Callable[[Job], Awaitable[dict | None]], job: Job | None = None) -> Job:
        if job is None:
            job = Job({"id": datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4],
                       "kind": kind, "title": title, "params": params, "status": "queued",
                       "created_at": now(), "steps": {}, "cost_usd": 0.0, "result": {}})
        job.data["status"] = "running"
        job.data["started_at"] = now()
        job.data.pop("error", None)
        job.save()

        async def runner():
            try:
                result = await fn(job)
                job.data["result"] = {**job.data.get("result", {}), **(result or {})}
                job.data["status"] = "done"
            except asyncio.CancelledError:
                job.data["status"] = "cancelled"
                job.log("Cancelled by user")
            except Exception as e:
                job.data["status"] = "failed"
                job.data["error"] = f"{type(e).__name__}: {e}"
                job.log("ERROR " + traceback.format_exc()[-1500:])
            job.data["finished_at"] = now()
            job.save()

        self.tasks[job.id] = asyncio.create_task(runner())
        return job

    def cancel(self, job_id: str) -> bool:
        task = self.tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def is_running(self, job_id: str) -> bool:
        task = self.tasks.get(job_id)
        return bool(task and not task.done())
