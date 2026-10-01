#!/usr/bin/env python3
"""
Frame extraction only — no external API dependencies.

Usage:
    python3 _analyze.py --input video.mp4 --max-frames 30 --fps 1.0

Outputs:
    data/analyses/<timestamp>/frames/        - extracted frames
    data/analyses/<timestamp>/manifest.json  - frame paths + video metadata

After this, Claude Code reads the frames directly and writes dna.json + dna.md.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


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


def extract_frames(video_path: str, output_dir: str, max_frames: int = 30, fps: float = 1.0) -> list[str]:
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = get_video_duration(str(video_path))
    # When the cap would truncate the video, lower fps so frames span the whole duration
    if duration > 0 and duration * fps > max_frames:
        fps = max_frames / duration
    frames_to_extract = min(max_frames, int(duration * fps)) if duration > 0 else max_frames

    # Remove existing frames to avoid mixing old + new
    for f in output_dir.glob("frame_*.jpg"):
        f.unlink()

    frame_pattern = str(output_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps:.6f}",
        "-frames:v", str(frames_to_extract),
        "-q:v", "2",
        frame_pattern
    ]

    print(f"  Extracting {frames_to_extract} frames at {fps:.3f} fps (covers full {duration:.1f}s)...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr.decode()[:500]}", file=sys.stderr)
        raise RuntimeError("ffmpeg failed")

    frames = sorted([str(f) for f in output_dir.glob("frame_*.jpg")])
    print(f"  Extracted {len(frames)} frames", file=sys.stderr)
    return frames, fps


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract frames for Claude Code Vision analysis")
    parser.add_argument("--input", required=True, help="Video file or directory")
    parser.add_argument("--max-frames", type=int, default=30, help="Max frames to extract")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames per second to extract")
    parser.add_argument("--output-dir", default="data/analyses", help="Output base directory")
    args = parser.parse_args()

    # Collect video files
    input_path = Path(args.input)
    if input_path.is_file():
        video_files = [str(input_path)]
    elif input_path.is_dir():
        exts = ["*.mp4", "*.mov", "*.mkv", "*.avi"]
        video_files = []
        for ext in exts:
            video_files.extend([str(f) for f in input_path.glob(ext)])
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

    # Extract frames per video
    manifest = {
        "run_id": run_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "videos": []
    }

    for video_file in video_files:
        name = Path(video_file).stem
        print(f"Processing {Path(video_file).name}...", file=sys.stderr)

        frames_dir = run_dir / "frames" / name
        frames, effective_fps = extract_frames(video_file, str(frames_dir), max_frames=args.max_frames, fps=args.fps)
        duration = get_video_duration(video_file)

        manifest["videos"].append({
            "filename": Path(video_file).name,
            "path": str(Path(video_file).resolve()),
            "duration_sec": round(duration, 1),
            "fps_extracted": round(effective_fps, 4),
            "sec_per_frame": round(1 / effective_fps, 2),
            "frames_extracted": len(frames),
            "frames_dir": str(frames_dir.resolve()),
            "frame_paths": frames,
        })

    # Write manifest
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone. {sum(len(v['frame_paths']) for v in manifest['videos'])} frames extracted.")
    print(f"Output: {run_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"\nNext step: Claude Code reads frames from manifest and writes dna.json")

    # Print manifest path to stdout for Claude Code to pick up
    print(str(manifest_path))


if __name__ == "__main__":
    main()
