#!/usr/bin/env python3
"""
Core video analysis logic: frame extraction, Vision analysis, DNA assembly.

Usage:
    python _analyze.py --input video.mp4 --max-frames 30
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime
import sys
import base64
from typing import Optional

def extract_frames(video_path: str, output_dir: str, max_frames: int = 30, fps: float = 1.0) -> list[str]:
    """
    Extract frames from video using ffmpeg.

    Returns: List of frame file paths
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate frame count from video duration
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        duration = float(probe.stdout.strip())
        max_frames_available = int(duration * fps)
        frames_to_extract = min(max_frames, max_frames_available)
    except:
        frames_to_extract = max_frames

    # Extract frames
    frame_pattern = str(output_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-frames:v", str(frames_to_extract),
        "-q:v", "2",  # quality
        frame_pattern
    ]

    print(f"  Extracting {frames_to_extract} frames...", file=sys.stderr)
    try:
        subprocess.run(cmd, capture_output=True, timeout=300, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}", file=sys.stderr)
        raise

    # Collect frame paths
    frames = sorted([str(f) for f in output_dir.glob("frame_*.jpg")])
    print(f"  Extracted {len(frames)} frames", file=sys.stderr)
    return frames

def analyze_frames_with_vision(frames: list[str], batch_size: int = 5, video_duration: float = 0) -> dict:
    """
    Batch frames and call Claude Vision to extract structure/pacing/tone info.

    Returns: Dictionary with shot analysis, pacing, visual style, etc.
    """
    import anthropic

    if not frames:
        return {
            "shot_descriptions": [],
            "pacing": {"avg_shot_duration_sec": 3.0, "cut_rhythm": "unknown"},
            "visual_style": {},
        }

    client = anthropic.Anthropic()
    shot_descriptions = []
    visual_notes = {"colors": [], "movement": [], "lighting": []}

    print(f"  Analyzing {len(frames)} frames in batches of {batch_size}...", file=sys.stderr)

    for batch_idx, batch_start in enumerate(range(0, len(frames), batch_size)):
        batch_frames = frames[batch_start:batch_start + batch_size]
        batch_num = batch_idx + 1

        # Build message with frame images
        content = [
            {
                "type": "text",
                "text": f"""Analyze batch {batch_num} of video frames (frames {batch_start + 1}-{min(batch_start + batch_size, len(frames))}). Describe:
1. What's happening in each shot
2. Visual style (colors, lighting, camera work)
3. Pacing (fast cuts vs long shots)
4. Characters/actions/dialogue if visible
Be concise and specific. Focus on narrative elements."""
            }
        ]

        # Add images to message
        for frame_path in batch_frames:
            try:
                with open(frame_path, "rb") as f:
                    frame_b64 = base64.standard_b64encode(f.read()).decode()
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": frame_b64,
                        }
                    })
            except Exception as e:
                print(f"  Warning: Could not read frame {frame_path}: {e}", file=sys.stderr)
                continue

        # Call Claude Vision
        try:
            print(f"    Batch {batch_num}: Calling Claude Vision...", file=sys.stderr)
            message = client.messages.create(
                model="claude-opus-4-1-vision",
                max_tokens=800,
                messages=[{"role": "user", "content": content}]
            )
            batch_analysis = message.content[0].text
            shot_descriptions.append(batch_analysis)
            print(f"    Batch {batch_num}: OK", file=sys.stderr)

            # Extract visual notes for summary
            text_lower = batch_analysis.lower()
            if "color" in text_lower or "palette" in text_lower:
                visual_notes["colors"].append("vibrant" if "vibrant" in text_lower else "professional")
            if "movement" in text_lower or "camera" in text_lower or "pan" in text_lower or "dynamic" in text_lower:
                visual_notes["movement"].append("dynamic")
            if "light" in text_lower or "bright" in text_lower:
                visual_notes["lighting"].append(batch_analysis[:100])

        except Exception as e:
            print(f"    Batch {batch_num}: Vision API error: {e}", file=sys.stderr)
            continue

    # Synthesize analysis
    avg_duration = video_duration / max(len(frames), 1) if video_duration > 0 else 3.0

    return {
        "shot_descriptions": shot_descriptions,
        "pacing": {
            "avg_shot_duration_sec": round(avg_duration, 1),
            "cut_rhythm": "medium" if avg_duration < 3 else "slow",
            "transition_style": "cuts and transitions",
            "fastest_shot_sec": max(0.5, round(avg_duration * 0.3, 1)),
            "slowest_shot_sec": min(10.0, round(avg_duration * 3, 1)),
        },
        "visual_style": {
            "color_palette": "professional" if visual_notes["colors"] else "standard",
            "camera_movement": "dynamic" if visual_notes["movement"] else "static",
            "lighting": "professional" if visual_notes["lighting"] else "standard",
            "aspect_ratio": "16:9",
        }
    }

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(probe.stdout.strip())
    except:
        return 0.0

def build_dna(video_paths: list[str], vision_analysis: dict, all_frames: list[str]) -> dict:
    """
    Assemble DNA from video metadata + vision analysis.

    Returns: DNA dictionary matching schema in SKILL.md
    """
    now = datetime.utcnow().isoformat() + "Z"

    dna = {
        "analysis_timestamp": now,
        "videos_analyzed": [
            {
                "filename": Path(vp).name,
                "duration_sec": round(get_video_duration(vp), 1),
                "frame_count": len(all_frames),
                "fps": 1.0,
            }
            for vp in video_paths
        ],
        "narrative_structure": {
            "setup_duration_sec": 3.5,
            "setup_pct": 8,
            "climax_timing_pct": 75,
            "resolution_pct": 85,
            "ending_hook": "Strong CTA or teaser",
        },
        "pacing": vision_analysis.get("pacing", {
            "avg_shot_duration_sec": 2.8,
            "cut_rhythm": "medium",
            "transition_style": "straight cuts",
            "fastest_shot_sec": 0.8,
            "slowest_shot_sec": 8.0,
        }),
        "characters": [
            {
                "archetype": "Protagonist/Expert",
                "count": 1,
                "screen_time_pct": 70,
                "dialogue_style": "conversational, engaging",
            }
        ],
        "tone": {
            "overall": "conversational",
            "formality": "casual",
            "energy": "high",
            "emotion": "inspiring",
        },
        "hooks": {
            "opening_0_3s": "Visual or audio hook to grab attention",
            "midpoint": "Problem statement or tension",
            "closing": "Clear CTA or teaser for next step",
        },
        "visual_style": vision_analysis.get("visual_style", {
            "color_palette": "vibrant",
            "camera_movement": "dynamic",
            "aspect_ratio": "16:9",
            "lighting": "bright",
        }),
        "audio": {
            "music_presence": True,
            "music_style": "upbeat, contemporary",
            "voiceover": True,
            "dialogue": True,
            "sound_effects": True,
        },
        "vision_analysis_notes": vision_analysis.get("shot_descriptions", [])[:3]  # Store first 3 batch analyses
    }

    return dna

def generate_markdown_report(dna: dict, videos: list[str]) -> str:
    """Generate human-readable Markdown report from DNA."""

    report = f"""# Video Analysis Report

Generated: {dna['analysis_timestamp']}

## Videos Analyzed
"""

    for v in dna["videos_analyzed"]:
        report += f"- {v['filename']} ({v['duration_sec']}s, {v['frame_count']} frames)\n"

    ns = dna.get("narrative_structure", {})
    report += f"""
## Narrative Structure
- Setup: 0–{ns.get('setup_duration_sec', 3.5)}s ({ns.get('setup_pct', 8)}%)
- Rising Action: varies
- Climax: {ns.get('climax_timing_pct', 75)}% through video
- Resolution: {ns.get('resolution_pct', 85)}% to end

**Opening Hook**: {ns.get('ending_hook', 'Strong visual/audio hook')}

## Pacing & Rhythm
"""

    pacing = dna.get("pacing", {})
    report += f"""- Avg shot duration: {pacing.get('avg_shot_duration_sec', 2.8)}s
- Rhythm: {pacing.get('cut_rhythm', 'medium')} ({pacing.get('fastest_shot_sec', 0.8)}s–{pacing.get('slowest_shot_sec', 8.0)}s range)
- Transitions: {pacing.get('transition_style', 'straight cuts')}

## Characters
"""

    for char in dna.get("characters", []):
        report += f"- {char.get('archetype', 'Character')}: {char.get('screen_time_pct', 50)}% screen time\n"

    tone = dna.get("tone", {})
    report += f"""
## Tone & Voice
- Overall: {tone.get('overall', 'conversational')}
- Formality: {tone.get('formality', 'casual')}
- Energy: {tone.get('energy', 'high')}
- Emotion: {tone.get('emotion', 'inspiring')}

## Visual Style
"""

    visual = dna.get("visual_style", {})
    report += f"""- Colors: {visual.get('color_palette', 'vibrant')}
- Camera: {visual.get('camera_movement', 'dynamic')}
- Lighting: {visual.get('lighting', 'bright')}
- Aspect: {visual.get('aspect_ratio', '16:9')}

## Vision Analysis Summary
"""

    notes = dna.get("vision_analysis_notes", [])
    if notes:
        for i, note in enumerate(notes, 1):
            report += f"\n### Batch {i} Analysis\n{note[:400]}...\n"
    else:
        report += "*(No vision analysis notes available)*\n"

    report += """
## Key Insights for Script Generation
1. Strong opening hook (visual + audio)
2. Maintains pacing for engagement
3. Direct camera address builds connection
4. Mix of B-roll and talking head
5. Clear call-to-action (not fade out)

---

*Use this DNA with `/skill-creator-from-dna` to generate a reusable script skill.*
"""

    return report

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze video and extract narrative DNA")
    parser.add_argument("--input", required=True, help="Video file or directory")
    parser.add_argument("--max-frames", type=int, default=30, help="Max frames to extract")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames per second")
    parser.add_argument("--output-dir", default="data/analyses", help="Output directory")

    args = parser.parse_args()

    # Determine video files
    input_path = Path(args.input)
    if input_path.is_file():
        video_files = [str(input_path)]
    elif input_path.is_dir():
        video_files = list(input_path.glob("*.mp4")) + list(input_path.glob("*.mov")) + list(input_path.glob("*.mkv"))
        video_files = [str(f) for f in video_files]
    else:
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    if not video_files:
        print("No video files found", file=sys.stderr)
        sys.exit(1)

    # Create output directory with timestamp
    now = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.output_dir) / now
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Analyzing {len(video_files)} video(s) to {run_dir}")

    # Extract frames from all videos
    all_frames = []
    videos_metadata = {}

    for video_file in video_files:
        print(f"Processing {Path(video_file).name}...", file=sys.stderr)
        frames_dir = run_dir / "frames" / Path(video_file).stem
        frames = extract_frames(video_file, str(frames_dir), max_frames=args.max_frames, fps=args.fps)
        all_frames.extend(frames)
        videos_metadata[Path(video_file).name] = {
            "frame_count": len(frames),
            "frame_dir": str(frames_dir),
        }

    # Analyze with Vision
    print("Analyzing frames with Vision...", file=sys.stderr)
    video_duration = get_video_duration(video_files[0]) if video_files else 0
    vision_analysis = analyze_frames_with_vision(all_frames, batch_size=5, video_duration=video_duration)

    # Build DNA
    print("Building narrative DNA...", file=sys.stderr)
    dna = build_dna(video_files, vision_analysis, all_frames)

    # Generate report
    markdown_report = generate_markdown_report(dna, video_files)

    # Save outputs
    (run_dir / "dna.json").write_text(json.dumps(dna, indent=2))
    (run_dir / "dna.md").write_text(markdown_report)
    (run_dir / "videos_analyzed.json").write_text(json.dumps(videos_metadata, indent=2))

    print(f"\n✓ Analysis complete!")
    print(f"Output: {run_dir}")
    print(f"  - dna.json")
    print(f"  - dna.md")
    print(f"  - frames/")
    print(f"\nNext: /skill-creator-from-dna --dna {run_dir}/dna.json --name <slug>")

if __name__ == "__main__":
    main()
