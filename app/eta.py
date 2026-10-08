"""Time-left estimates for running jobs, learned from finished jobs on this machine.

A job's work is `units` of one `key` (e.g. refine:outline x 10 episodes, images x 25 images). The
rate is the median seconds per unit of the last finished jobs with the same key; with no history a
rough default is used. Estimates are shown as "about N minutes left", never as a promise.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone

from .jobs import Job

# Seconds per unit when this machine has no finished job of that key yet
DEFAULT_RATE = {
    "outline": 8 * 60, "refine:outline": 150, "refine:feedback": 6 * 60, "refine:final": 4 * 60,
    "images": 150, "assets": 6 * 60, "skill": 15 * 60, "continue": 15 * 60,
}


def _ts(s: str | None) -> float | None:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() if s else None


def key_of(job: Job) -> str:
    d = job.data
    if d["kind"] == "refine":
        return f"refine:{d['params'].get('approve') or 'feedback'}"
    return d["kind"]


def units_of(job: Job) -> int:
    d = job.data
    if d["kind"] == "refine" and d["params"].get("approve") == "outline":
        return max(1, len(d["params"].get("writing") or []) or 1)
    if d["kind"] == "images":
        return max(1, int((d.get("steps", {}).get("images") or {}).get("total") or 1))
    return 1


def history(jobs: list[Job]) -> dict[str, float]:
    """key -> median seconds per unit over the last 8 finished jobs of that key."""
    samples: dict[str, list[float]] = {}
    for j in jobs:
        d = j.data
        if d["status"] != "done":
            continue
        start, end = _ts(d.get("started_at")), _ts(d.get("finished_at"))
        if not start or not end or end <= start:
            continue
        samples.setdefault(key_of(j), []).append((end - start) / units_of(j))
    return {k: statistics.median(v[:8]) for k, v in samples.items()}


def eta_sec(job: Job, rates: dict[str, float]) -> int | None:
    """Seconds left for a running job, or None when there is nothing sensible to say (analysis)."""
    d = job.data
    if d["status"] != "running":
        return None
    key = key_of(job)
    rate = rates.get(key) or DEFAULT_RATE.get(key)
    start = _ts(d.get("started_at"))
    if not rate or not start:
        return None
    elapsed = datetime.now(timezone.utc).timestamp() - start
    if d["kind"] == "images":
        st = d.get("steps", {}).get("images") or {}
        left = max(0, int(st.get("total") or 0) - int(st.get("done") or 0) - int(st.get("failed") or 0))
        return int(left * rate) if left else 30
    total = rate * units_of(job)
    # Past the estimate: keep saying "a bit longer" instead of a negative number
    return int(max(total - elapsed, 60 if elapsed < total * 1.5 else 120))
