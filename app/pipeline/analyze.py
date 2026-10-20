"""Analysis pipeline driven by the backend (same steps as the /analyze-videos skill).

1 shots + units + frames (_analyze.py)  2 transcript (_transcribe.py, ~10-min chunks)
3 video-analyst per unit (parallel)       4 story-merger (parts if > 8 units, then final)
5 film-analyst: text-only audit + why it works (film_analysis.md/.json)

Steps 2 and 3 overlap: a unit's analyst starts as soon as the chunk covering it is transcribed
(UnitGate), so the CPU transcribes while Claude analyzes.
Every step skips work whose output already exists, so a failed or interrupted job can resume.
Also runnable from the CLI:  .venv/bin/python -m app.pipeline.analyze --run data/analyses/<run-id>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Callable

from .. import config
from ..claude_runner import run_claude
from ..jobs import Job

MERGE_GROUP = 8


async def run_script(job: Job, args: list[str], on_line: Callable[[str], bool] | None = None) -> list[str]:
    """Run a helper script, logging its output. on_line(line) -> True means the line was a machine
    message it handled (not logged)."""
    proc = await asyncio.create_subprocess_exec(
        *args, cwd=str(config.ROOT), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        limit=2 ** 20)
    lines = []
    assert proc.stdout
    try:
        async for raw in proc.stdout:
            line = raw.decode(errors="replace").rstrip()
            lines.append(line)
            if on_line and on_line(line):
                continue
            # Skip noisy library warnings / progress bars
            if line and not any(x in line for x in ("Warning", "warn(", "%|", "torchcodec", "libav")):
                job.log(line[:200])
    except asyncio.CancelledError:
        proc.kill()
        raise
    if await proc.wait() != 0:
        raise RuntimeError(f"{Path(args[1]).name} failed (exit {proc.returncode})")
    return lines


def valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text())
        return True
    except Exception:
        return False


async def step_extract(job: Job) -> Path:
    p = job.data["params"]
    if p.get("run_dir") and (Path(p["run_dir"]) / "manifest.json").exists():
        job.step("extract", "skipped")
        return Path(p["run_dir"])
    job.step("extract", "running")
    lines = await run_script(job, ["python3", str(config.SCRIPTS / "_analyze.py"), "--input", p["video_path"],
                                   "--chunk-sec", str(p.get("chunk_sec", 120)),
                                   "--max-frames", str(p.get("max_frames", 40))]
                       + (["--audio-only"] if p.get("audio_only") else []))
    manifest = Path(lines[-1].strip())
    run_dir = (config.ROOT / manifest).parent if not manifest.is_absolute() else manifest.parent
    p["run_dir"] = str(run_dir)
    m = json.loads((run_dir / "manifest.json").read_text())
    job.step("extract", "done", units=len(m["units"]),
             shots=sum(s.get("pacing_measured", {}).get("shot_count", 0) for s in m["sources"]))
    return run_dir


def unit_has_audio_info(unit: dict) -> bool:
    return bool(unit.get("transcript_path")) or (unit.get("audio") or {}).get("has_audio") is False


class UnitGate:
    """Which units may start their analyst: transcript written (or no audio), or transcription not run.
    After a transcription crash the gate closes: units not started yet are skipped (resume redoes them)."""

    def __init__(self, units: list[dict]):
        self.events = {u["unit_id"]: asyncio.Event() for u in units}
        self.closed = False
        for u in units:
            if unit_has_audio_info(u):
                self.events[u["unit_id"]].set()

    def mark(self, unit_id: str):
        if unit_id in self.events:
            self.events[unit_id].set()

    def open_all(self):
        for ev in self.events.values():
            ev.set()

    def close(self):
        self.closed = True
        self.open_all()

    async def wait(self, unit_id: str) -> bool:
        await self.events[unit_id].wait()
        return not self.closed


async def step_transcribe(job: Job, run_dir: Path, gate: UnitGate | None = None):
    gate = gate or UnitGate([])
    m = json.loads((run_dir / "manifest.json").read_text())
    if all(unit_has_audio_info(u) for u in m["units"]):
        job.step("transcribe", "skipped")
        gate.open_all()
        return
    if not config.VENV_PY.exists():
        job.step("transcribe", "skipped", note="no .venv (WhisperX); dialogue will be inferred")
        gate.open_all()
        return
    p = job.data["params"]
    job.step("transcribe", "running")
    args = [str(config.VENV_PY), str(config.SCRIPTS / "_transcribe.py"), "--manifest", str(run_dir / "manifest.json"),
            "--diarize", p.get("diarize") or "auto"]
    if p.get("language"):
        args += ["--language", p["language"]]

    def on_line(line: str) -> bool:
        if line.startswith("UNIT_READY "):
            gate.mark(line.split(None, 1)[1].strip())
            return True
        if line.startswith("PROGRESS "):
            done, _, total = line.split(None, 1)[1].partition("/")
            if done.isdigit() and total.isdigit():
                job.step("transcribe", "running", done=int(done), total=int(total))
            return True
        return False

    await run_script(job, args, on_line)
    m = json.loads((run_dir / "manifest.json").read_text())
    audio = (m["sources"][0].get("audio") or {}) if m["sources"] else {}
    job.step("transcribe", "done", language=audio.get("language"), segments=audio.get("segments"),
             diarized=audio.get("diarized"))


def analyst_prompt(unit: dict, run_dir: Path) -> str:
    fields = {k: unit.get(k) for k in ("unit_id", "filename", "t_start", "t_end", "duration_sec", "chunk",
                                       "frames_dir", "shots_path", "transcript_path", "fps_extracted")}
    fields["output_path"] = str(run_dir / "dna" / f"{unit['unit_id']}.dna.json")
    lang = ((unit.get("audio") or {}).get("language")) or "unknown"
    return ("Analyze this unit and write its unit DNA JSON, following your agent instructions.\n\n"
            + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fields.items() if v is not None)
            + f"\n\nDialogue language: {lang}. Keep dialogue lines verbatim in that language; "
              "write all other fields in English.")


def current_unit(run_dir: Path, unit_id: str) -> dict:
    """The unit as the manifest has it now (transcript_path + language land while the job runs)."""
    m = json.loads((run_dir / "manifest.json").read_text())
    return next(u for u in m["units"] if u["unit_id"] == unit_id)


async def step_units(job: Job, run_dir: Path, gate: UnitGate | None = None):
    m = json.loads((run_dir / "manifest.json").read_text())
    units = m["units"]
    if gate is None:
        gate = UnitGate(units)
        gate.open_all()
    (run_dir / "dna").mkdir(exist_ok=True)
    todo = [u for u in units if not valid_json(run_dir / "dna" / f"{u['unit_id']}.dna.json")]
    done = len(units) - len(todo)
    job.step("units", "running", done=done, total=len(units), failed=[], note=None)
    sem = asyncio.Semaphore(config.CLAUDE_PARALLEL)

    skipped = []

    async def one(unit: dict):
        nonlocal done
        out = run_dir / "dna" / f"{unit['unit_id']}.dna.json"
        if not await gate.wait(unit["unit_id"]):
            skipped.append(unit["unit_id"])
            return
        async with sem:
            unit = current_unit(run_dir, unit["unit_id"])
            for attempt in (1, 2):
                job.log(f"[{unit['unit_id']}] video-analyst start (attempt {attempt})")
                res = await run_claude(analyst_prompt(unit, run_dir), agent="video-analyst",
                                       log=lambda s, u=unit["unit_id"]: job.log(f"[{u}] {s}"))
                job.add_cost(res.cost_usd)
                if res.ok and valid_json(out):
                    done += 1
                    job.log(f"[{unit['unit_id']}] done ({res.duration_ms // 1000}s, ${res.cost_usd:.2f})")
                    job.step("units", "running", done=done, total=len(units))
                    return
                job.log(f"[{unit['unit_id']}] failed: {res.error or 'no valid output file'}")
        job.data["steps"]["units"].setdefault("failed", []).append(unit["unit_id"])
        job.save()

    await asyncio.gather(*(one(u) for u in todo))
    if skipped:  # transcription crashed: these never started; step_transcribe raises the error
        job.step("units", "failed", done=done, total=len(units), note="chép lời bị lỗi, chạy tiếp để làm nốt")
        return
    failed = job.data["steps"]["units"].get("failed", [])
    if failed:
        job.step("units", "failed", done=done, total=len(units))
        raise RuntimeError(f"{len(failed)} unit(s) failed: {', '.join(failed)}. Resume to retry them.")
    job.step("units", "done", done=done, total=len(units))


async def step_merge(job: Job, run_dir: Path):
    if valid_json(run_dir / "dna.json") and (run_dir / "story.md").exists() \
            and not job.data["params"].get("force_merge"):
        job.step("merge", "skipped")
        return
    units = json.loads((run_dir / "manifest.json").read_text())["units"]
    unit_files = [str(run_dir / "dna" / f"{u['unit_id']}.dna.json") for u in units]
    inputs = unit_files
    if len(unit_files) > MERGE_GROUP:
        (run_dir / "parts").mkdir(exist_ok=True)
        groups = [unit_files[i:i + MERGE_GROUP] for i in range(0, len(unit_files), MERGE_GROUP)]
        parts = [run_dir / "parts" / f"part_{i + 1:02d}.json" for i in range(len(groups))]
        job.step("merge", "running", phase="parts", total=len(groups))
        sem = asyncio.Semaphore(config.CLAUDE_PARALLEL)

        async def part(i: int):
            if valid_json(parts[i]):
                return
            async with sem:
                prompt = (f"mode: part\ninputs: {json.dumps(groups[i])}\noutput: {parts[i]}\n"
                          "Follow your agent instructions for mode=part.")
                res = await run_claude(prompt, agent="story-merger",
                                       log=lambda s: job.log(f"[part {i + 1}] {s}"))
                job.add_cost(res.cost_usd)
                if not (res.ok and valid_json(parts[i])):
                    raise RuntimeError(f"part {i + 1} merge failed: {res.error or 'no output'}")

        await asyncio.gather(*(part(i) for i in range(len(groups))))
        inputs = [str(p) for p in parts]

    job.step("merge", "running", phase="final")
    prompt = (f"mode: final\ninputs: {json.dumps(inputs)}\noutput: {run_dir}\n"
              f"manifest_path: {run_dir / 'manifest.json'}\n"
              "Follow your agent instructions for mode=final. Write dna.json, dna.md and story.md.")
    res = await run_claude(prompt, agent="story-merger", log=lambda s: job.log(f"[final] {s}"))
    job.add_cost(res.cost_usd)
    if not (res.ok and valid_json(run_dir / "dna.json")):
        raise RuntimeError(f"final merge failed: {res.error or 'no dna.json'}")
    job.step("merge", "done")


async def step_review(job: Job, run_dir: Path):
    """film-analyst: text-only audit of the DNA + why the reference holds viewers (no frames, cheap)."""
    if valid_json(run_dir / "film_analysis.json") and (run_dir / "film_analysis.md").exists():
        job.step("review", "skipped")
        return
    job.step("review", "running")
    prompt = (f"run_dir: {run_dir}\noutput: {run_dir}\n"
              "Follow your agent instructions. Write film_analysis.json and film_analysis.md.")
    res = await run_claude(prompt, agent="film-analyst", log=lambda s: job.log(f"[review] {s}"))
    job.add_cost(res.cost_usd)
    if not (res.ok and valid_json(run_dir / "film_analysis.json")):
        raise RuntimeError(f"film analysis failed: {res.error or 'no film_analysis.json'}")
    job.step("review", "done")


async def step_summary(job: Job, run_dir: Path):
    """Vietnamese summary for the UI. Optional: a failure is logged, never fails the analysis."""
    from .summary import load, run_summary_path, summarize_run
    if load(run_summary_path(run_dir)):
        job.step("summary", "skipped")
        return
    job.step("summary", "running")
    ok = await summarize_run(job, run_dir)
    job.step("summary", "done" if ok else "failed")


async def transcribe_and_units(job: Job, run_dir: Path):
    """Steps 2 + 3 together: analysts start on each unit as soon as its transcript is written."""
    gate = UnitGate(json.loads((run_dir / "manifest.json").read_text())["units"])

    async def transcribe():
        try:
            await step_transcribe(job, run_dir, gate)
        except BaseException:
            gate.close()  # never leave analysts waiting on a crashed transcription
            raise
        gate.open_all()

    results = await asyncio.gather(transcribe(), step_units(job, run_dir, gate), return_exceptions=True)
    for r in results:
        if isinstance(r, BaseException):
            raise r


async def run_analysis(job: Job) -> dict:
    run_dir = await step_extract(job)
    job.data["result"]["run_dir"] = str(run_dir)
    job.save()
    await transcribe_and_units(job, run_dir)
    await step_merge(job, run_dir)
    await step_review(job, run_dir)
    await step_summary(job, run_dir)
    return {"run_dir": str(run_dir)}


if __name__ == "__main__":
    import argparse
    from ..jobs import JobManager

    ap = argparse.ArgumentParser(description="Run/resume the analysis pipeline without the web UI")
    ap.add_argument("--video", help="video path (new run)")
    ap.add_argument("--run", help="existing run dir to resume")
    ap.add_argument("--language")
    ap.add_argument("--diarize", choices=["auto", "on", "off"], default="auto")
    args = ap.parse_args()

    async def main():
        jm = JobManager()
        job = jm.start("analysis", f"CLI {args.run or args.video}",
                       {"video_path": args.video, "run_dir": args.run, "language": args.language,
                        "diarize": args.diarize}, run_analysis)
        print(f"job {job.id}, log: {job.log_path}", file=sys.stderr)
        await jm.tasks[job.id]
        print(json.dumps(jm.get(job.id).data, indent=2))

    asyncio.run(main())
