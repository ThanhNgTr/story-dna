#!/usr/bin/env python3
"""
Shot detection + chunking + frame extraction — no external API, only ffmpeg/ffprobe.

Usage:
    python3 _analyze.py --input long_video.mp4
    python3 _analyze.py --input videos/ --chunk-sec 120 --max-frames 40

A long video (>= --chunk-min-video sec) is split into analysis units of ~--chunk-sec,
each boundary placed on a real cut. Short videos are one unit each.
All timestamps and shot ids are ABSOLUTE in the source video, so units can be
stitched back into one timeline.

Sampling modes:
    shot (default) - detect real cuts with ffmpeg scene scores (adaptive), measure
                     pacing from the cut list, extract 1+ keyframe per shot
    uniform        - fallback: frames evenly spaced inside each unit

Outputs (data/analyses/<timestamp>/):
    manifest.json                    - sources (whole-video pacing) + units (frames, chunk window)
    shots/<stem>.json                - full cut list + pacing for the whole source video
    shots/<unit_id>.json             - cut list + pacing for one unit
    frames/<unit_id>/frame_NNNN_tSSSS.SS_sNNNN.jpg

Next: _transcribe.py (audio), then one video-analyst agent per unit.
"""

from __future__ import annotations

import json
import re
import statistics
import unicodedata
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime

# Adaptive cut rule (same idea as PySceneDetect detect-adaptive): a frame is a cut if
# its scene score is high outright, or clearly higher than its neighbors' average.
# Neighbor averaging keeps camera motion / grain from triggering cuts in dark footage.
SCENE_HARD = 0.3       # score >= this is always a cut
SCENE_RATIO = 3.0      # score / neighbor avg >= this is a cut (if score >= --scene-threshold)
SCENE_WINDOW_SEC = 1.0  # neighbor window on each side
MIN_EXTRA_FRAME_GAP_SEC = 1.0  # don't add a 2nd+ frame to a shot if frames would be closer than this
HOOK_WINDOW_SEC = 3.0
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def get_video_duration(video_path: str) -> float:
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(probe.stdout.strip())
    except:
        return 0.0


def scene_scores(video_path: str, duration: float) -> tuple[list[float], list[float]]:
    """Per-frame ffmpeg scene score (0..1). Downscaled first: much faster, same cuts."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(video_path), "-an", "-sn",
        "-vf", "scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=max(300, duration))
    if result.returncode != 0:
        raise RuntimeError(f"scene detection failed: {result.stderr[-500:]}")
    times = [float(x) for x in re.findall(r"pts_time:([\d.]+)", result.stderr)]
    scores = [float(x) for x in re.findall(r"lavfi\.scene_score=([\d.]+)", result.stderr)]
    if not times or len(times) != len(scores):
        raise RuntimeError(f"scene detection parse failed ({len(times)} times, {len(scores)} scores)")
    return times, scores


def detect_cuts(times: list[float], scores: list[float], low: float, min_shot: float) -> list[dict]:
    cuts = []
    j0 = j1 = 0
    for i, (t, s) in enumerate(zip(times, scores)):
        # Slide the neighbor window [t - W, t + W]
        while times[j0] < t - SCENE_WINDOW_SEC:
            j0 += 1
        while j1 + 1 < len(times) and times[j1 + 1] <= t + SCENE_WINDOW_SEC:
            j1 += 1
        if s < low or t < min_shot:
            continue
        neighbors = scores[j0:i] + scores[i + 1:j1 + 1]
        avg = sum(neighbors) / len(neighbors) if neighbors else 0.0
        if s < SCENE_HARD and s / (avg + 1e-3) < SCENE_RATIO:
            continue
        # Flash / strobe bursts: keep only the first cut within min_shot
        if cuts and t - cuts[-1]["t_sec"] < min_shot:
            continue
        cuts.append({"t_sec": round(t, 3), "score": round(s, 3)})
    return cuts


def build_shots(cuts: list[dict], duration: float) -> list[dict]:
    bounds = [0.0] + [c["t_sec"] for c in cuts] + [duration]
    shots = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        if end - start <= 0:
            continue
        shots.append({
            "shot_id": f"s{len(shots) + 1:04d}",
            "t_start": round(start, 2),
            "t_end": round(end, 2),
            "duration_sec": round(end - start, 2),
            "cut_score": cuts[i - 1]["score"] if i > 0 else None,
        })
    return shots


def measure_pacing(shots: list[dict], t_start: float, t_end: float) -> dict:
    """Pacing for the shots inside [t_start, t_end). Times relative to t_start."""
    duration = t_end - t_start
    durs = [s["duration_sec"] for s in shots]
    avg = sum(durs) / len(durs)
    buckets = {"<1s": 0, "1-2s": 0, "2-4s": 0, "4-8s": 0, ">=8s": 0}
    for d in durs:
        key = "<1s" if d < 1 else "1-2s" if d < 2 else "2-4s" if d < 4 else "4-8s" if d < 8 else ">=8s"
        buckets[key] += 1

    # Avg shot length per quarter of the runtime: shows where the edit speeds up / slows down
    by_quarter = []
    for q in range(4):
        q_start, q_end = t_start + duration * q / 4, t_start + duration * (q + 1) / 4
        in_q = [s["duration_sec"] for s in shots if q_start <= (s["t_start"] + s["t_end"]) / 2 < q_end]
        by_quarter.append(round(sum(in_q) / len(in_q), 2) if in_q else None)

    return {
        "measured": True,
        "method": "ffmpeg scene score, adaptive",
        "shot_count": len(shots),
        "avg_shot_duration_sec": round(avg, 2),
        "median_shot_duration_sec": round(statistics.median(durs), 2),
        "fastest_shot_sec": round(min(durs), 2),
        "slowest_shot_sec": round(max(durs), 2),
        "cuts_per_min": round((len(shots) - 1) / duration * 60, 1) if duration > 0 else None,
        "cut_rhythm": "fast" if avg < 2.5 else "medium" if avg < 5 else "slow",
        "first_cut_sec": round(shots[1]["t_start"] - t_start, 2) if len(shots) > 1 else None,
        "shots_in_first_3s": sum(1 for s in shots if s["t_start"] - t_start < HOOK_WINDOW_SEC),
        "shot_length_buckets": buckets,
        "avg_shot_sec_by_quarter": by_quarter,
    }


def plan_chunks(cut_times: list[float], duration: float, chunk_sec: float) -> list[tuple[float, float]]:
    """Split [0, duration] into ~chunk_sec windows, each boundary on the cut nearest the target."""
    bounds = [0.0]
    while duration - bounds[-1] > chunk_sec * 1.5:
        target = bounds[-1] + chunk_sec
        # Stay within 50% of the target so units keep a similar size
        options = [c for c in cut_times if bounds[-1] + chunk_sec * 0.5 <= c <= bounds[-1] + chunk_sec * 1.5]
        bounds.append(min(options, key=lambda c: abs(c - target)) if options else target)
    bounds.append(duration)
    return [(round(bounds[i], 2), round(bounds[i + 1], 2)) for i in range(len(bounds) - 1)]


def allocate_frames(shots: list[dict], max_frames: int) -> list[tuple[dict, float]]:
    """Pick (shot, timestamp) pairs: 1 frame per shot, extra frames to long shots."""
    if len(shots) > max_frames:
        # Too many shots: keep the opening shots, spread the rest evenly by index
        unit_start = shots[0]["t_start"]
        hook = [i for i, s in enumerate(shots) if s["t_start"] - unit_start < HOOK_WINDOW_SEC][:max_frames]
        rest = [i for i in range(len(shots)) if i not in hook]
        n = max_frames - len(hook)
        picked = [rest[round(k * (len(rest) - 1) / (n - 1))] for k in range(n)] if n > 1 else rest[:n]
        counts = {i: 1 for i in hook + picked}
    else:
        counts = {i: 1 for i in range(len(shots))}
        budget = max_frames - len(shots)
        while budget > 0:
            # Give the next frame to the shot with the longest gap between its frames
            i = max(counts, key=lambda k: shots[k]["duration_sec"] / (counts[k] + 1))
            if shots[i]["duration_sec"] / (counts[i] + 1) < MIN_EXTRA_FRAME_GAP_SEC:
                break
            counts[i] += 1
            budget -= 1

    picks = []
    for i in sorted(counts):
        s, k = shots[i], counts[i]
        for j in range(k):
            # Centers of k equal slices: never lands on a cut boundary
            picks.append((s, round(s["t_start"] + s["duration_sec"] * (j + 0.5) / k, 2)))
    return picks


def grab_frame(video_path: str, t: float, out: Path) -> bool:
    # Retry slightly earlier: timestamps at the very end of a file can land past the last frame
    for attempt_t in (t, max(0.0, t - 0.5), max(0.0, t - 1.5)):
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{attempt_t:.3f}", "-i", str(video_path),
               "-frames:v", "1", "-q:v", "2", "-y", str(out)]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return True
    print(f"  Frame grab failed at {t}s, skipped: {result.stderr.decode()[-200:]}", file=sys.stderr)
    return False


def extract_frames(video_path: str, output_dir: Path, picks: list[tuple[dict | None, float]]) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Remove existing frames to avoid mixing old + new
    for f in output_dir.glob("frame_*.jpg"):
        f.unlink()
    frame_info = []
    for n, (shot, t) in enumerate(picks, start=1):
        shot_id = shot["shot_id"] if shot else None
        path = output_dir / f"frame_{n:04d}_t{t:07.2f}_{shot_id or 'u'}.jpg"
        frame_info.append({"path": str(path), "t_sec": t, "shot_id": shot_id})
    with ThreadPoolExecutor(max_workers=4) as pool:
        ok = list(pool.map(lambda f: grab_frame(video_path, f["t_sec"], Path(f["path"])), frame_info))
    return [f for f, good in zip(frame_info, ok) if good]


def write_json(path: Path, data: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return str(path.resolve())


def safe_id(name: str) -> str:
    """ASCII id for folders/agents ("Tập 1" -> "Tap_1"): spaces and odd chars break globs and shell commands."""
    name = name.replace("đ", "d").replace("Đ", "D")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "video"


def natural_key(path: str) -> list:
    """Episode order: "Tap 2" before "Tap 10"."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path)]


def process_source(video_file: str, run_dir: Path, args) -> tuple[dict, list[dict]]:
    stem = safe_id(Path(video_file).stem)
    duration = get_video_duration(video_file)
    source = {
        "source_id": stem,
        "filename": Path(video_file).name,
        "path": str(Path(video_file).resolve()),
        "duration_sec": round(duration, 1),
    }
    long_video = duration >= args.chunk_min_video

    sampling = args.sampling
    if sampling == "shot" and duration <= 0:
        print("  Unknown duration, falling back to uniform sampling", file=sys.stderr)
        sampling = "uniform"

    shots = []
    if sampling == "shot":
        try:
            print("  Detecting shots...", file=sys.stderr)
            times, scores = scene_scores(video_file, duration)
            shots = build_shots(detect_cuts(times, scores, args.scene_threshold, args.min_shot), duration)
            pacing = measure_pacing(shots, 0.0, duration)
            print(f"  {len(shots)} shots, avg {pacing['avg_shot_duration_sec']}s", file=sys.stderr)
            source["pacing_measured"] = pacing
            source["shots_path"] = write_json(run_dir / "shots" / f"{stem}.json", {
                "filename": source["filename"],
                "duration_sec": source["duration_sec"],
                "params": {"scene_threshold": args.scene_threshold, "scene_hard": SCENE_HARD,
                           "scene_ratio": SCENE_RATIO, "min_shot_sec": args.min_shot},
                "pacing_measured": pacing,
                "shots": shots,
            })
        except RuntimeError as e:
            print(f"  {e}\n  Falling back to uniform sampling", file=sys.stderr)
            sampling = "uniform"
    source["sampling"] = sampling

    cut_times = [s["t_start"] for s in shots[1:]]
    windows = plan_chunks(cut_times, duration, args.chunk_sec) if long_video else [(0.0, round(duration, 2))]
    print(f"  {len(windows)} unit(s)", file=sys.stderr)

    units = []
    for idx, (t_start, t_end) in enumerate(windows, start=1):
        unit_id = f"{stem}_c{idx:02d}" if len(windows) > 1 else stem
        unit = {
            "unit_id": unit_id,
            "filename": source["filename"],
            "path": source["path"],
            "source_duration_sec": source["duration_sec"],
            "chunk": {"index": idx, "count": len(windows), "t_start": t_start, "t_end": t_end}
                     if len(windows) > 1 else None,
            "t_start": t_start,
            "t_end": t_end,
            "duration_sec": round(t_end - t_start, 1),
            "sampling": sampling,
        }
        if sampling == "shot":
            unit_shots = [s for s in shots if s["t_start"] >= t_start - 0.01 and s["t_end"] <= t_end + 0.01]
            picks = allocate_frames(unit_shots, args.max_frames)
            unit_pacing = measure_pacing(unit_shots, t_start, t_end)
            picked_ids = {s["shot_id"] for s, _ in picks}
            for s in unit_shots:
                s["has_frame"] = s["shot_id"] in picked_ids
            unit["pacing_measured"] = unit_pacing
            unit["shots_path"] = write_json(run_dir / "shots" / f"{unit_id}.json", {
                "unit_id": unit_id, "filename": source["filename"],
                "t_start": t_start, "t_end": t_end,
                "pacing_measured": unit_pacing, "shots": unit_shots,
            })
        else:
            n = max(1, min(args.max_frames, int((t_end - t_start) * args.fps)))
            picks = [(None, round(t_start + (k + 0.5) * (t_end - t_start) / n, 2)) for k in range(n)]
            unit["fps_extracted"] = round(n / (t_end - t_start), 4)

        print(f"  {unit_id}: {t_start:.1f}-{t_end:.1f}s, extracting {len(picks)} frames...", file=sys.stderr)
        frames = extract_frames(video_file, run_dir / "frames" / unit_id, picks)
        unit.update({
            "frames_extracted": len(frames),
            "frames_dir": str((run_dir / "frames" / unit_id).resolve()),
            "frames": frames,
            "frame_paths": [f["path"] for f in frames],
        })
        units.append(unit)

    source["units"] = [u["unit_id"] for u in units]
    return source, units


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Detect shots, split long videos, extract frames")
    parser.add_argument("--input", required=True, help="Video file or directory")
    parser.add_argument("--max-frames", type=int, default=40, help="Max frames per unit")
    parser.add_argument("--chunk-sec", type=float, default=120,
                        help="Target unit length for long videos (boundaries snap to cuts)")
    parser.add_argument("--chunk-min-video", type=float, default=240,
                        help="Videos at least this long get split into units")
    parser.add_argument("--sampling", choices=["shot", "uniform"], default="shot",
                        help="shot = keyframes per detected shot (default); uniform = evenly spaced")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames per second (uniform mode only)")
    parser.add_argument("--scene-threshold", type=float, default=0.12,
                        help="Min scene score for an adaptive cut (lower = more cuts; dark footage needs low)")
    parser.add_argument("--min-shot", type=float, default=0.5,
                        help="Min shot length in sec; merges flash/strobe bursts")
    parser.add_argument("--output-dir", default="data/analyses", help="Output base directory")
    args = parser.parse_args()

    # Collect video files
    input_path = Path(args.input)
    if input_path.is_file():
        video_files = [str(input_path)]
    elif input_path.is_dir():
        video_files = sorted((str(f) for f in input_path.rglob("*") if f.suffix.lower() in VIDEO_EXTS),
                             key=natural_key)
    else:
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    if not video_files:
        print("No video files found", file=sys.stderr)
        sys.exit(1)

    # Create run directory
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run: {run_dir}", file=sys.stderr)

    manifest = {
        "run_id": run_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "params": {"max_frames": args.max_frames, "chunk_sec": args.chunk_sec,
                   "chunk_min_video": args.chunk_min_video, "sampling": args.sampling},
        "sources": [],
        "units": [],
    }

    for video_file in video_files:
        print(f"Processing {Path(video_file).name}...", file=sys.stderr)
        source, units = process_source(video_file, run_dir, args)
        manifest["sources"].append(source)
        manifest["units"].extend(units)

    # Write manifest
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone. {len(manifest['units'])} unit(s), "
          f"{sum(u['frames_extracted'] for u in manifest['units'])} frames extracted.")
    print(f"Output: {run_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"\nNext step: _transcribe.py on the manifest, then one video-analyst per unit")

    # Print manifest path to stdout for Claude Code to pick up
    print(str(manifest_path))


if __name__ == "__main__":
    main()
