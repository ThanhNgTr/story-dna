"""Long-video analysis: chunked transcription (resumable, per-chunk unit output) and analysts that start
while transcription is still running."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import load_script, write

tr = load_script("analyze-videos/_transcribe.py")


def units_of(duration: float, step: float = 120) -> list[dict]:
    out, t, i = [], 0.0, 1
    while t < duration:
        out.append({"unit_id": f"v_c{i:03d}", "t_start": t, "t_end": min(duration, t + step)})
        t += step
        i += 1
    return out


def test_chunks_cut_on_unit_boundaries_and_cover_the_video():
    units = units_of(9663.6)
    windows = tr.plan_chunks(units, 9663.6)
    assert windows[0][0] == 0 and windows[-1][1] == 9663.6
    assert all(a[1] == b[0] for a, b in zip(windows, windows[1:]))
    starts = {u["t_start"] for u in units}
    assert all(w[0] in starts for w in windows)
    assert 14 <= len(windows) <= 17
    for u in units:  # 120 s units fit inside one chunk
        assert len(tr.chunks_of((u["t_start"], u["t_end"]), windows)) == 1


def test_one_long_unit_is_split_and_waits_for_all_its_chunks():
    windows = tr.plan_chunks([{"unit_id": "ep1"}], 3000)  # audio-only: one unit per video
    assert len(windows) == 5
    assert tr.chunks_of(tr.unit_span({"unit_id": "ep1"}, 3000), windows) == [0, 1, 2, 3, 4]
    assert tr.plan_chunks([{"unit_id": "ep1"}], 200) == [(0.0, 200)]


def test_short_tail_joins_previous_chunk():
    windows = tr.plan_chunks(units_of(1300), 1300)  # 600 + 600 + 100 -> 600 + 700
    assert windows == [(0.0, 600.0), (600.0, 1300)]


def test_shift_segments_moves_times_keeps_midpoints_and_tags_speakers():
    segs = [{"start": 1.0, "end": 2.0, "text": "pad", "speaker": "SPEAKER_00", "words": []},
            {"start": 4.0, "end": 6.0, "text": "a", "speaker": "SPEAKER_01",
             "words": [{"word": "a", "start": 4.0, "end": 4.5, "speaker": "SPEAKER_01"}]}]
    out = tr.shift_segments(segs, 597.0, 600.0, 1200.0, "C02")
    assert [s["text"] for s in out] == ["a"]  # midpoint 598.5 belongs to the previous chunk
    assert out[0]["start"] == 601.0 and out[0]["words"][0]["start"] == 601.0
    assert out[0]["speaker"] == "C02_SPEAKER_01" and out[0]["words"][0]["speaker"] == "C02_SPEAKER_01"


@pytest.mark.parametrize("mode,minutes,expect", [("auto", 30, True), ("auto", 134, False),
                                                 ("on", 134, True), ("off", 10, False)])
def test_diarize_choice(mode, minutes, expect):
    assert tr.want_diarize(mode, minutes * 60, 60)[0] is expect


class FakeTranscriber:
    calls: list = []

    def __init__(self, model, language, threads, diarize):
        self.language = language
        self.wx = SimpleNamespace(load_audio=lambda path: [0.0])

    def run_chunk(self, audio, t0, t1, is_last, tag):
        FakeTranscriber.calls.append((t0, t1))
        segs = [{"start": t0 + 10, "end": t0 + 12, "text": f"line at {t0}", "speaker": None, "words": []}]
        return {"t_start": t0, "t_end": t1, "language": "vi", "aligned": True, "diarized": False,
                "timings": {"asr": 1}, "segments": segs}


def make_run(tmp_path: Path, duration: float = 1300) -> Path:
    units = units_of(duration)
    manifest = {"run_id": "r", "sources": [{"source_id": "v", "filename": "v.mp4", "path": str(tmp_path / "v.mp4"),
                                            "duration_sec": duration, "units": [u["unit_id"] for u in units]}],
                "units": units}
    return write(tmp_path / "run" / "manifest.json", manifest)


def run_transcribe(monkeypatch, capsys, manifest: Path) -> list[str]:
    monkeypatch.setattr(tr, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(tr, "has_audio", lambda p: True)
    monkeypatch.setattr(tr, "detect_silences", lambda p, d: [])
    monkeypatch.setattr(sys, "argv", ["_transcribe.py", "--manifest", str(manifest), "--diarize", "off"])
    tr.main()
    return capsys.readouterr().out.splitlines()


def test_transcribe_writes_units_per_chunk_and_resumes(tmp_path, monkeypatch, capsys):
    manifest = make_run(tmp_path)
    FakeTranscriber.calls = []
    out = run_transcribe(monkeypatch, capsys, manifest)
    assert FakeTranscriber.calls == [(0.0, 600.0), (600.0, 1300)]
    ready = [l.split()[1] for l in out if l.startswith("UNIT_READY")]
    assert ready == [f"v_c{i:03d}" for i in range(1, 12)]
    # the first chunk's units are announced before the second chunk starts
    assert out.index("UNIT_READY v_c005") < out.index("PROGRESS 1/2") < out.index("UNIT_READY v_c006")
    m = json.loads(manifest.read_text())
    u6 = json.loads(Path(m["units"][5]["transcript_path"]).read_text())
    assert [s["text"] for s in u6["segments"]] == ["line at 600.0"] and u6["audio"]["language"] == "vi"
    assert m["sources"][0]["audio"]["segments"] == 2

    # interrupted run: chunk 1 saved, chunk 2 lost -> only chunk 2 is transcribed again
    (manifest.parent / "transcripts" / "_chunks" / "v.c01.json").unlink()
    FakeTranscriber.calls = []
    run_transcribe(monkeypatch, capsys, manifest)
    assert FakeTranscriber.calls == [(600.0, 1300)]


# --- backend: analysts start while transcription runs -------------------------------------------------

class FakeJob:
    def __init__(self, params):
        self.data = {"params": params, "steps": {}, "result": {}}
        self.lines = []

    def step(self, name, status, **extra):
        self.data["steps"][name] = {**self.data["steps"].get(name, {}), "status": status, **extra}

    def log(self, line):
        self.lines.append(line)

    def add_cost(self, usd):
        pass

    def save(self):
        pass


def pipeline_env(tmp_path, monkeypatch, crash_after_first=False):
    from app import config
    from app.pipeline import analyze

    manifest = make_run(tmp_path)
    run_dir = manifest.parent
    venv_py = write(tmp_path / "python", "")
    monkeypatch.setattr(config, "VENV_PY", venv_py)
    events = []
    started_first = asyncio.Event()

    async def fake_run_script(job, args, on_line=None):
        m = json.loads(manifest.read_text())
        for i, u in enumerate(m["units"]):
            if i == 5:  # end of the first chunk: wait until an analyst runs, proving the overlap
                await asyncio.wait_for(started_first.wait(), 5)
                if crash_after_first:
                    raise RuntimeError("_transcribe.py failed (exit 1)")
            u["transcript_path"] = str(write(run_dir / "transcripts" / f"{u['unit_id']}.json", {"segments": []}))
            manifest.write_text(json.dumps(m))
            events.append(f"ready {u['unit_id']}")
            on_line(f"UNIT_READY {u['unit_id']}")
            await asyncio.sleep(0)
        on_line("PROGRESS 2/2")
        return []

    async def fake_run_claude(prompt, agent=None, log=None, **kw):
        uid = next(l.split(": ")[1].strip('"') for l in prompt.splitlines() if l.startswith("unit_id:"))
        assert "transcript_path" in prompt  # prompt built from the manifest as it is now
        events.append(f"analyst {uid}")
        started_first.set()
        await asyncio.sleep(0)
        write(run_dir / "dna" / f"{uid}.dna.json", {"unit_id": uid})
        return SimpleNamespace(ok=True, cost_usd=0.0, duration_ms=1000, error=None)

    monkeypatch.setattr(analyze, "run_script", fake_run_script)
    monkeypatch.setattr(analyze, "run_claude", fake_run_claude)
    return analyze, run_dir, events


def test_analysts_start_before_transcription_ends(tmp_path, monkeypatch):
    analyze, run_dir, events = pipeline_env(tmp_path, monkeypatch)
    job = FakeJob({"diarize": "off"})
    asyncio.run(analyze.transcribe_and_units(job, run_dir))
    assert events.index("analyst v_c001") < events.index("ready v_c011")
    for i in range(1, 12):  # nobody runs before its transcript exists
        assert events.index(f"ready v_c{i:03d}") < events.index(f"analyst v_c{i:03d}")
    assert job.data["steps"]["units"]["status"] == "done" and job.data["steps"]["units"]["done"] == 11
    assert job.data["steps"]["transcribe"]["status"] == "done"


def test_transcription_crash_stops_waiting_analysts(tmp_path, monkeypatch):
    analyze, run_dir, events = pipeline_env(tmp_path, monkeypatch, crash_after_first=True)
    job = FakeJob({})
    with pytest.raises(RuntimeError, match="_transcribe.py failed"):
        asyncio.run(analyze.transcribe_and_units(job, run_dir))
    analysed = [e for e in events if e.startswith("analyst")]
    assert analysed and all(int(e[-3:]) <= 5 for e in analysed)
    assert job.data["steps"]["units"]["status"] == "failed"
