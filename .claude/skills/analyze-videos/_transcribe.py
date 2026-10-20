#!/usr/bin/env python3
"""
Audio pass: transcript (WhisperX) + speaker labels (optional) + silence map.
Runs after _analyze.py and adds audio info to the same manifest.

Each SOURCE video is transcribed in ~10-min chunks cut on unit boundaries (shot cuts), each padded
by a few seconds so words at the seam are heard in full. Every finished chunk is saved
(transcripts/_chunks/), so an interrupted run resumes at the first missing chunk, and the units it
covers are written at once: the backend starts their video-analyst while the next chunk is still
being transcribed. Timestamps stay absolute.

Needs the project venv (WhisperX + CPU torch):
    ~/.local/bin/uv venv .venv --python 3.12
    ~/.local/bin/uv pip install --python .venv/bin/python whisperx \
        --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

Usage:
    .venv/bin/python .claude/skills/analyze-videos/_transcribe.py --manifest data/analyses/<run>/manifest.json \
        [--language vi] [--diarize auto|on|off] [--chunk-sec 600]

Speaker labels (diarization) need HF_TOKEN + the pyannote model terms accepted on Hugging Face.
--diarize auto (default) turns them on only when all audio in the manifest is <= --diarize-max-min
(default 60, env STORY_DNA_DIARIZE_MAX_MIN): on CPU diarization costs about as long as the ASR itself.
Labels are per chunk ("C03_SPEAKER_01"): the same person can carry another label in the next chunk.

Outputs:
    <run_dir>/transcripts/<stem>.json            - whole source: segments + silences + audio summary
    <run_dir>/transcripts/<unit_id>.json         - same, cut to one unit's [t_start, t_end)
    <run_dir>/transcripts/_chunks/<stem>.cNN.json - one finished chunk (resume checkpoint)
    manifest.json                                - sources[] and units[] get transcript_path + audio
Machine lines on stdout for the backend: "PROGRESS <done>/<total>", "UNIT_READY <unit_id>".
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

SILENCE_DB = -40       # below this = silence
SILENCE_MIN_SEC = 0.5  # shorter gaps are not reported
CHUNK_SEC = 600        # target chunk length
PAD_SEC = 3.0          # audio added on both sides of a chunk; segments are kept by midpoint
SAMPLE_RATE = 16000    # whisperx.load_audio


def log(msg: str):
    print(msg, file=sys.stderr, flush=True)


def emit(msg: str):
    print(msg, flush=True)


def has_audio(video_path: str) -> bool:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True, timeout=10)
    return bool(probe.stdout.strip())


def detect_silences(video_path: str, duration: float) -> list[dict]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video_path), "-vn",
           "-af", f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_MIN_SEC}", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=max(300, duration))
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", result.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", result.stderr)]
    if len(ends) < len(starts):  # silence runs to the end of the file
        ends.append(duration)
    return [{"start": round(s, 2), "end": round(e, 2), "duration_sec": round(e - s, 2)}
            for s, e in zip(starts, ends)]


def shot_lookup(shots_path: str | None):
    if not shots_path or not Path(shots_path).exists():
        return lambda t: None
    shots = json.loads(Path(shots_path).read_text())["shots"]

    def find(t: float):
        for s in shots:
            if s["t_start"] <= t < s["t_end"]:
                return s["shot_id"]
        return shots[-1]["shot_id"] if shots else None
    return find


def unit_span(unit: dict, duration: float) -> tuple[float, float]:
    return float(unit.get("t_start") or 0.0), float(unit.get("t_end") or duration)


def plan_chunks(units: list[dict], duration: float, target: float = CHUNK_SEC) -> list[tuple[float, float]]:
    """Windows of ~target s covering [0, duration]. Cuts fall on unit boundaries (real shot cuts); a short
    tail joins the previous window; a window longer than 1.5x target (one long unit) is split evenly."""
    if duration <= 0:
        return [(0.0, duration)]
    bounds = sorted({b for u in units for b in unit_span(u, duration) if 0 < b < duration})
    cuts, start = [], 0.0
    for b in bounds:
        if b - start >= target:
            cuts.append(b)
            start = b
    if cuts and duration - cuts[-1] < target / 3:
        cuts.pop()
    edges = [0.0, *cuts, duration]
    windows = []
    for s, e in zip(edges, edges[1:]):
        n = math.ceil((e - s) / target) if e - s > 1.5 * target else 1
        step = (e - s) / n
        windows += [(round(s + i * step, 2), round(e if i == n - 1 else s + (i + 1) * step, 2)) for i in range(n)]
    return windows


def chunks_of(span: tuple[float, float], windows: list[tuple[float, float]]) -> list[int]:
    s, e = span
    hit = [i for i, (ws, we) in enumerate(windows) if ws < e and we > s]
    return hit or [len(windows) - 1]


def want_diarize(mode: str, total_sec: float, max_min: float) -> tuple[bool, str]:
    if mode == "off":
        return False, "off (--diarize off)"
    if mode == "on":
        return True, "on (--diarize on)"
    if total_sec > max_min * 60:
        return False, (f"off (auto: {total_sec / 60:.0f} min of audio > {max_min:.0f} min; "
                       "pass --diarize on to force)")
    return True, "on (auto)"


def shift_segments(segments: list[dict], offset: float, t0: float, t1: float, tag: str) -> list[dict]:
    """Clip-relative WhisperX segments -> absolute times, kept when their midpoint is in [t0, t1);
    speaker labels get the chunk tag (labels from separate diarization runs are not the same people)."""
    out = []
    for seg in segments:
        start, end = seg["start"] + offset, seg["end"] + offset
        if not t0 <= (start + end) / 2 < t1:
            continue
        words = []
        for w in seg.get("words", []):
            w = dict(w)
            for k in ("start", "end"):
                if k in w:
                    w[k] = w[k] + offset
            if w.get("speaker"):
                w["speaker"] = f"{tag}_{w['speaker']}"
            words.append(w)
        spk = seg.get("speaker")
        out.append({"start": start, "end": end, "text": seg.get("text", ""),
                    "speaker": f"{tag}_{spk}" if spk else None, "words": words})
    return out


class Transcriber:
    """Loads models once, reuses them for every chunk and video."""

    def __init__(self, model_name: str, language: str | None, threads: int, diarize: bool):
        import whisperx
        self.wx = whisperx
        self.language = language
        log(f"Loading Whisper model '{model_name}' (CPU, int8)...")
        self.model = whisperx.load_model(model_name, "cpu", compute_type="int8", language=language,
                                         vad_method="silero", threads=threads)
        self.align_models = {}
        self.diarizer = None
        if diarize:
            try:
                from whisperx.diarize import DiarizationPipeline
                self.diarizer = DiarizationPipeline(token=os.environ["HF_TOKEN"], device="cpu")
            except Exception as e:
                log(f"Diarization: off ({str(e)[:200]})")

    def run_chunk(self, audio, t0: float, t1: float, is_last: bool, tag: str) -> dict:
        a0 = max(0.0, t0 - PAD_SEC)
        clip = audio[int(a0 * SAMPLE_RATE):int((t1 + PAD_SEC) * SAMPLE_RATE)]
        timings = {}
        t = time.time()
        result = self.model.transcribe(clip, batch_size=8, language=self.language)
        timings["asr"] = round(time.time() - t)
        language = result.get("language") or self.language
        if self.language is None and language:
            self.language = language  # detected on the first chunk; later chunks skip detection
            log(f"  Language: {language}")

        aligned = False
        if result["segments"]:
            t = time.time()
            try:
                if language not in self.align_models:
                    self.align_models[language] = self.wx.load_align_model(language_code=language, device="cpu")
                model_a, meta = self.align_models[language]
                result = self.wx.align(result["segments"], model_a, meta, clip, "cpu",
                                       return_char_alignments=False)
                aligned = True
            except Exception as e:
                log(f"  Word alignment skipped ({str(e)[:200]})")
            timings["align"] = round(time.time() - t)

        diarized = False
        if self.diarizer is not None and result["segments"]:
            t = time.time()
            try:
                result = self.wx.assign_word_speakers(self.diarizer(clip), result)
                diarized = True
            except Exception as e:
                log(f"  Diarization failed ({str(e)[:200]})")
            timings["diarize"] = round(time.time() - t)

        end = t1 + PAD_SEC if is_last else t1  # the last chunk keeps everything up to the end
        return {"t_start": t0, "t_end": t1, "language": language, "aligned": aligned, "diarized": diarized,
                "timings": timings, "segments": shift_segments(result["segments"], a0, t0, end, tag)}


def build_transcript(segments: list[dict], find_shot) -> list[dict]:
    out = []
    for seg in segments:
        words = [{"word": w.get("word"), "start": round(w["start"], 2) if "start" in w else None,
                  "end": round(w["end"], 2) if "end" in w else None, "speaker": w.get("speaker")}
                 for w in seg.get("words", [])]
        start, end = round(seg["start"], 2), round(seg["end"], 2)
        out.append({
            "start": start,
            "end": end,
            "text": seg["text"].strip(),
            "speaker": seg.get("speaker"),
            "shot_id": find_shot((start + end) / 2),
            "words": words,
        })
    return out


def summarize(segments: list[dict], silences: list[dict], t_start: float, t_end: float, raw: dict) -> dict:
    duration = t_end - t_start
    speech_sec = sum(s["end"] - s["start"] for s in segments)
    words = sum(len(s["text"].split()) for s in segments)
    speakers = sorted({s["speaker"] for s in segments if s["speaker"]})
    return {
        "has_audio": True,
        "language": raw["language"],
        "segments": len(segments),
        "words": words,
        "speech_sec": round(speech_sec, 1),
        "speech_pct": round(speech_sec / duration * 100, 1) if duration else None,
        "words_per_min": round(words / duration * 60, 1) if duration else None,
        "first_speech_sec": round(segments[0]["start"] - t_start, 2) if segments else None,
        "speakers": speakers,
        "diarized": raw["diarized"],
        "speaker_scope": "chunk" if raw["diarized"] else None,
        "word_aligned": raw["aligned"],
        "silence_count": len(silences),
        "silence_total_sec": round(sum(s["duration_sec"] for s in silences), 1),
    }


def write_json(path: Path, data) -> None:
    """Atomic: the backend reads the manifest while chunks are still being written."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(path)


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def write_transcript(path: Path, header: dict, audio: dict, segments: list, silences: list) -> str:
    write_json(path, {**header, "created_at": datetime.utcnow().isoformat() + "Z",
                      "audio": audio, "segments": segments, "silences": silences})
    return str(path.resolve())


def fmt_t(sec: float) -> str:
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add transcript + speaker labels to an analyze-videos manifest")
    parser.add_argument("--manifest", required=True, help="manifest.json from _analyze.py")
    parser.add_argument("--model", default="large-v3-turbo",
                        help="Whisper model (tiny, base, small, medium, large-v3, large-v3-turbo)")
    parser.add_argument("--language", default=None, help="Force language code (e.g. en, vi). Default: auto")
    parser.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--chunk-sec", type=float, default=CHUNK_SEC, help="Target chunk length (default 600)")
    parser.add_argument("--diarize", choices=["auto", "on", "off"], default="auto",
                        help="Speaker labels: auto = on when all audio <= --diarize-max-min")
    parser.add_argument("--diarize-max-min", type=float,
                        default=float(os.environ.get("STORY_DNA_DIARIZE_MAX_MIN", "60")))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())
    run_dir = manifest_path.parent
    out_dir = run_dir / "transcripts"
    ckpt_dir = out_dir / "_chunks"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    units_by_id = {u["unit_id"]: u for u in manifest["units"]}

    # Plan every source first: one progress bar over all chunks of all videos
    plans = []
    for source in manifest["sources"]:
        stem = source.get("source_id") or Path(source["filename"]).stem
        units = [units_by_id[uid] for uid in source["units"]]
        audio_ok = has_audio(source["path"])
        windows = plan_chunks(units, source["duration_sec"], args.chunk_sec) if audio_ok else []
        plans.append((source, stem, units, audio_ok, windows))
    total = sum(len(p[4]) for p in plans)
    total_sec = sum(p[0]["duration_sec"] for p in plans if p[3])

    diarize, why = want_diarize(args.diarize, total_sec, args.diarize_max_min)
    if diarize and not os.environ.get("HF_TOKEN"):
        diarize, why = False, "off (HF_TOKEN not set)"
    log(f"Diarization: {why}")
    log(f"{total} chunk(s) of ~{args.chunk_sec / 60:.0f} min over {total_sec / 60:.0f} min of audio")

    transcriber = None
    language = args.language  # fixed after the first chunk (detection only looks at its first 30 s)
    done = 0
    emit(f"PROGRESS 0/{total}")
    for source, stem, units, audio_ok, windows in plans:
        duration = source["duration_sec"]
        log(f"Processing {source['filename']}...")

        if not audio_ok:
            log("  No audio stream, skipping")
            for target in [source] + units:
                target["audio"] = {"has_audio": False}
                target["transcript_path"] = None
            write_json(manifest_path, manifest)
            for unit in units:
                emit(f"UNIT_READY {unit['unit_id']}")
            continue

        sil_path = ckpt_dir / f"{stem}.silences.json"
        silences = read_json(sil_path)
        if silences is None:
            silences = detect_silences(source["path"], duration)
            write_json(sil_path, silences)

        find_shot = shot_lookup(source.get("shots_path"))
        header = {"filename": source["filename"], "duration_sec": duration}
        unit_chunks = {u["unit_id"]: chunks_of(unit_span(u, duration), windows) for u in units}
        raws: dict[int, dict] = {}
        published: set[str] = set()
        emitted: set[str] = set()
        audio = None

        def audio_for(segs, sils, t_start, t_end, idx):
            parts = [raws[i] for i in idx]
            if any(p.get("failed") for p in parts):
                return {"has_audio": True, "transcribed": False, "silence_count": len(sils)}
            raw = {"language": parts[0]["language"], "aligned": all(p["aligned"] for p in parts),
                   "diarized": all(p["diarized"] for p in parts)}
            info = summarize(segs, sils, t_start, t_end, raw)
            info.update({"transcribed": True, "model": args.model})
            return info

        def publish():
            """Write every unit whose chunks are all done; the backend may start its analyst now."""
            segments = build_transcript([s for i in sorted(raws) for s in raws[i]["segments"]], find_shot)
            for unit in units:
                uid = unit["unit_id"]
                if uid in published or not all(i in raws for i in unit_chunks[uid]):
                    continue
                t_start, t_end = unit_span(unit, duration)
                if uid == stem:  # unchunked: the unit is the whole source
                    unit_segs, unit_sils = segments, silences
                else:
                    unit_segs = [s for s in segments if t_start <= (s["start"] + s["end"]) / 2 < t_end]
                    unit_sils = [s for s in silences if s["end"] > t_start and s["start"] < t_end]
                unit["audio"] = audio_for(unit_segs, unit_sils, t_start, t_end, unit_chunks[uid])
                unit["transcript_path"] = write_transcript(
                    out_dir / f"{uid}.json",
                    {**header, "unit_id": uid, "t_start": t_start, "t_end": t_end},
                    unit["audio"], unit_segs, unit_sils)
                published.add(uid)
            write_json(manifest_path, manifest)
            for uid in [u["unit_id"] for u in units if u["unit_id"] in published]:
                if uid not in emitted:
                    emitted.add(uid)
                    emit(f"UNIT_READY {uid}")
            return segments

        for i, (t0, t1) in enumerate(windows):
            ckpt = ckpt_dir / f"{stem}.c{i:02d}.json"
            raw = read_json(ckpt)
            if raw and raw.get("t_start") == t0 and raw.get("t_end") == t1:
                note = "saved earlier"
            else:
                try:
                    if transcriber is None:
                        transcriber = Transcriber(args.model, language, args.threads, diarize)
                    if audio is None:
                        audio = transcriber.wx.load_audio(str(source["path"]))
                    raw = transcriber.run_chunk(audio, t0, t1, i == len(windows) - 1, f"C{i + 1:02d}")
                    write_json(ckpt, raw)
                    note = ", ".join(f"{k} {v}s" for k, v in raw["timings"].items())
                except Exception as e:
                    # Not saved: a resume retries it. Agents fall back to visual-only dialogue for these units.
                    log(f"  Transcription failed ({str(e)[:300]})")
                    raw = {"t_start": t0, "t_end": t1, "language": language, "aligned": False,
                           "diarized": False, "failed": True, "segments": []}
                    note = "failed"
            if language is None and raw.get("language"):
                language = raw["language"]
                if transcriber is not None:
                    transcriber.language = language
            raws[i] = raw
            done += 1
            log(f"Chunk {done}/{total} [{fmt_t(t0)}-{fmt_t(t1)}]: {len(raw['segments'])} segments ({note})")
            publish()
            emit(f"PROGRESS {done}/{total}")

        segments = publish()
        source["audio"] = audio_for(segments, silences, 0.0, duration, list(range(len(windows))))
        source["transcript_path"] = write_transcript(out_dir / f"{stem}.json", header, source["audio"],
                                                     segments, silences)
        write_json(manifest_path, manifest)
        info = source["audio"]
        log(f"  {info.get('segments', 0)} segments, {info.get('words', 0)} words, "
            f"speakers: {len(info.get('speakers') or []) or 'n/a'}, {len(units)} unit(s)")

    write_json(manifest_path, manifest)
    print(f"Updated {manifest_path}", flush=True)


if __name__ == "__main__":
    main()
