#!/usr/bin/env python3
"""
Audio pass: transcript (WhisperX) + speaker labels (optional) + silence map.
Runs after _analyze.py and adds audio info to the same manifest.

Each SOURCE video is transcribed once (full context helps ASR), then segments are
split into the analysis units (chunks) by time. Timestamps stay absolute.

Needs the project venv (WhisperX + CPU torch):
    ~/.local/bin/uv venv .venv --python 3.12
    ~/.local/bin/uv pip install --python .venv/bin/python whisperx \
        --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

Usage:
    .venv/bin/python .claude/skills/analyze-videos/_transcribe.py --manifest data/analyses/<run>/manifest.json

Speaker labels (diarization) turn on when HF_TOKEN is set and the pyannote model
terms were accepted on Hugging Face. Without it: transcript only, speaker = null.

Outputs:
    <run_dir>/transcripts/<stem>.json     - whole source: segments + silences + audio summary
    <run_dir>/transcripts/<unit_id>.json  - same, cut to one unit's [t_start, t_end)
    manifest.json                         - sources[] and units[] get transcript_path + audio
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

SILENCE_DB = -40       # below this = silence
SILENCE_MIN_SEC = 0.5  # shorter gaps are not reported


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


class Transcriber:
    """Loads models once, reuses them for every video."""

    def __init__(self, model_name: str, language: str | None, threads: int):
        import whisperx
        self.wx = whisperx
        self.language = language
        print(f"Loading Whisper model '{model_name}' (CPU, int8)...", file=sys.stderr)
        self.model = whisperx.load_model(model_name, "cpu", compute_type="int8", language=language,
                                         vad_method="silero", threads=threads)
        self.align_models = {}
        self.diarizer = None
        token = os.environ.get("HF_TOKEN")
        if token:
            try:
                from whisperx.diarize import DiarizationPipeline
                self.diarizer = DiarizationPipeline(token=token, device="cpu")
                print("Diarization: on", file=sys.stderr)
            except Exception as e:
                print(f"Diarization: off ({str(e)[:200]})", file=sys.stderr)
        else:
            print("Diarization: off (HF_TOKEN not set)", file=sys.stderr)

    def run(self, video_path: str) -> dict:
        audio = self.wx.load_audio(str(video_path))
        result = self.model.transcribe(audio, batch_size=8)
        language = result.get("language", self.language)

        aligned = False
        try:
            if language not in self.align_models:
                self.align_models[language] = self.wx.load_align_model(language_code=language, device="cpu")
            model_a, meta = self.align_models[language]
            result = self.wx.align(result["segments"], model_a, meta, audio, "cpu",
                                   return_char_alignments=False)
            aligned = True
        except Exception as e:
            print(f"  Word alignment skipped ({str(e)[:200]})", file=sys.stderr)

        diarized = False
        if self.diarizer is not None:
            try:
                result = self.wx.assign_word_speakers(self.diarizer(audio), result)
                diarized = True
            except Exception as e:
                print(f"  Diarization failed ({str(e)[:200]})", file=sys.stderr)

        return {"language": language, "aligned": aligned, "diarized": diarized,
                "segments": result["segments"]}


def build_transcript(raw: dict, find_shot) -> list[dict]:
    segments = []
    for seg in raw["segments"]:
        words = [{"word": w.get("word"), "start": round(w["start"], 2) if "start" in w else None,
                  "end": round(w["end"], 2) if "end" in w else None, "speaker": w.get("speaker")}
                 for w in seg.get("words", [])]
        start, end = round(seg["start"], 2), round(seg["end"], 2)
        segments.append({
            "start": start,
            "end": end,
            "text": seg["text"].strip(),
            "speaker": seg.get("speaker"),
            "shot_id": find_shot((start + end) / 2),
            "words": words,
        })
    return segments


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
        "word_aligned": raw["aligned"],
        "silence_count": len(silences),
        "silence_total_sec": round(sum(s["duration_sec"] for s in silences), 1),
    }


def write_transcript(path: Path, header: dict, audio: dict, segments: list, silences: list) -> str:
    path.write_text(json.dumps({**header, "created_at": datetime.utcnow().isoformat() + "Z",
                                "audio": audio, "segments": segments, "silences": silences},
                               indent=2, ensure_ascii=False))
    return str(path.resolve())


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add transcript + speaker labels to an analyze-videos manifest")
    parser.add_argument("--manifest", required=True, help="manifest.json from _analyze.py")
    parser.add_argument("--model", default="large-v3-turbo",
                        help="Whisper model (tiny, base, small, medium, large-v3, large-v3-turbo)")
    parser.add_argument("--language", default=None, help="Force language code (e.g. en, vi). Default: auto")
    parser.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())
    run_dir = manifest_path.parent
    out_dir = run_dir / "transcripts"
    out_dir.mkdir(exist_ok=True)
    units_by_id = {u["unit_id"]: u for u in manifest["units"]}

    transcriber = None
    for source in manifest["sources"]:
        stem = source.get("source_id") or Path(source["filename"]).stem
        duration = source["duration_sec"]
        units = [units_by_id[uid] for uid in source["units"]]
        print(f"Processing {source['filename']}...", file=sys.stderr)

        if not has_audio(source["path"]):
            print("  No audio stream, skipping", file=sys.stderr)
            for target in [source] + units:
                target["audio"] = {"has_audio": False}
                target["transcript_path"] = None
            continue

        silences = detect_silences(source["path"], duration)
        try:
            if transcriber is None:
                transcriber = Transcriber(args.model, args.language, args.threads)
            raw = transcriber.run(source["path"])
        except Exception as e:
            # Keep the silence map even if ASR fails; agents fall back to visual-only dialogue
            print(f"  Transcription failed ({str(e)[:300]})", file=sys.stderr)
            raw = None

        segments = build_transcript(raw, shot_lookup(source.get("shots_path"))) if raw else []

        def audio_for(segs, sils, t_start, t_end):
            if not raw:
                return {"has_audio": True, "transcribed": False, "silence_count": len(sils)}
            audio = summarize(segs, sils, t_start, t_end, raw)
            audio.update({"transcribed": True, "model": args.model})
            return audio

        header = {"filename": source["filename"], "duration_sec": duration}
        source["audio"] = audio_for(segments, silences, 0.0, duration)
        source["transcript_path"] = write_transcript(out_dir / f"{stem}.json", header, source["audio"],
                                                     segments, silences)

        for unit in units:
            if unit["unit_id"] == stem:  # unchunked: same file
                unit["audio"], unit["transcript_path"] = source["audio"], source["transcript_path"]
                continue
            t_start, t_end = unit["t_start"], unit["t_end"]
            unit_segs = [s for s in segments if t_start <= (s["start"] + s["end"]) / 2 < t_end]
            unit_sils = [s for s in silences if s["end"] > t_start and s["start"] < t_end]
            unit["audio"] = audio_for(unit_segs, unit_sils, t_start, t_end)
            unit["transcript_path"] = write_transcript(
                out_dir / f"{unit['unit_id']}.json",
                {**header, "unit_id": unit["unit_id"], "t_start": t_start, "t_end": t_end},
                unit["audio"], unit_segs, unit_sils)

        audio = source["audio"]
        print(f"  {audio.get('segments', 0)} segments, {audio.get('words', 0)} words, "
              f"speakers: {audio.get('speakers') or 'n/a'}, {len(units)} unit(s)", file=sys.stderr)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Updated {manifest_path}")


if __name__ == "__main__":
    main()
