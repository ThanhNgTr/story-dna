---
name: analyze-videos
description: |
  Extract narrative DNA from local video files. Runs ffmpeg to extract frames,
  then Claude Code reads frames directly (no external API needed) to analyze
  pacing, characters, tone, visual style, and narrative structure. Produces
  dna.json + dna.md for downstream skill generation. Triggers on: "analyze video",
  "extract DNA", "video analysis", "analyze frames", "narrative analysis".
  Input: local video file or directory. Output: manifest.json (frame paths),
  dna.json (structured DNA), dna.md (human-readable report).
---

# Video Analysis → Narrative DNA

## When to Use

Use when you have local reference videos and want to extract narrative patterns:
- Understand structure/pacing/tone from existing videos
- Build DNA to feed into skill generation
- Analyze shot composition, character archetypes, dialogue flow

**Input**: Local video file or directory (MP4, MOV, MKV, AVI)
**Output**: `manifest.json` + `dna.json` + `dna.md` + `frames/`

## Quick Start

```
/analyze-videos --input data/analyses/ep1.mp4 --max-frames 30
```

## How It Works

### Step 1 — Frame extraction (Python + ffmpeg)
Run `_analyze.py` to extract frames and write manifest:

```bash
cd /path/to/story-dna
python3 .claude/skills/analyze-videos/_analyze.py \
  --input data/analyses/ep1.mp4 \
  --max-frames 30 \
  --fps 1.0 \
  --output-dir data/analyses
```

Output: `data/analyses/<timestamp>/manifest.json` with all frame paths.

### Step 2 — Per-video analysis (subagent `video-analyst`, one per video)
Frame images must NOT be read in the main context (30 frames ≈ 45k tokens). For each entry in `manifest.json`, launch one `video-analyst` agent **in parallel** with:

```
frames_dir:  <videos[i].frames_dir>
filename:    <videos[i].filename>
duration_sec / fps_extracted / frames_extracted from the manifest
output_path: <run_dir>/dna/<stem>.dna.json
series_context: (optional) character visual signatures from earlier episodes
```

Each agent reads every frame, writes `<run_dir>/dna/<stem>.dna.json`, and returns a ≤250-word summary. Only the summaries enter the main context.

### Step 3 — Series merge (subagent `series-merger`)
After all analysts finish, launch one `series-merger` agent with:

```
dna_dir: <run_dir>/dna
run_dir: <run_dir>
```

It matches recurring characters across episodes by `visual_signature`, dedupes world rules, derives pacing/tone norms, and writes `<run_dir>/dna.json` + `<run_dir>/dna.md`. This series DNA is the input to `/skill-creator-from-dna`.

**No external API, no anthropic package needed** — agents read images natively.

## DNA Output Format

### `dna.json`
```json
{
  "analysis_timestamp": "2025-10-01T14:30:00Z",
  "videos_analyzed": [
    {
      "filename": "ep1.mp4",
      "duration_sec": 91.3,
      "frames_extracted": 30,
      "fps_extracted": 1.0
    }
  ],
  "narrative_structure": {
    "setup_duration_sec": 5,
    "setup_pct": 5,
    "climax_timing_pct": 70,
    "resolution_pct": 85,
    "ending_hook": "Subscribe CTA with enthusiasm"
  },
  "pacing": {
    "avg_shot_duration_sec": 6.1,
    "cut_rhythm": "medium",
    "transition_style": "straight cuts",
    "fastest_shot_sec": 2.0,
    "slowest_shot_sec": 12.0
  },
  "characters": [
    {
      "archetype": "Mentor/Expert",
      "count": 1,
      "screen_time_pct": 65,
      "dialogue_style": "conversational, energetic"
    },
    {
      "archetype": "Learner/Audience surrogate",
      "count": 1,
      "screen_time_pct": 35,
      "dialogue_style": "curious, off-camera questions"
    }
  ],
  "tone": {
    "overall": "educational but engaging",
    "formality": "casual",
    "energy": "high",
    "emotion": "inspiring"
  },
  "hooks": {
    "opening_0_3s": "Direct address + enthusiastic hook question",
    "midpoint": "Problem/objection raised + reassurance",
    "closing": "CTA: subscribe + next tutorial teaser"
  },
  "visual_style": {
    "color_palette": "warm professional tones",
    "camera_movement": "mix static + dynamic pans",
    "aspect_ratio": "16:9",
    "lighting": "professional studio/natural"
  },
  "audio": {
    "music_presence": true,
    "music_style": "upbeat contemporary",
    "voiceover": true,
    "dialogue": true,
    "sound_effects": true
  }
}
```

## Examples

### Single video
```bash
python3 .claude/skills/analyze-videos/_analyze.py --input data/analyses/ep1.mp4
```

### More frames (more detail)
```bash
python3 .claude/skills/analyze-videos/_analyze.py \
  --input data/analyses/ep1.mp4 \
  --max-frames 60 --fps 2.0
```

### Directory of videos
```bash
python3 .claude/skills/analyze-videos/_analyze.py --input data/samples/
```

## Notes

- Requires `ffmpeg` + `ffprobe` (check: `ffmpeg -version`)
- Does NOT require `anthropic` package or API key
- Frame extraction: ~5–15s per video
- Vision analysis: Claude Code reads frames inline — no extra cost beyond session
- All outputs reproducible in `data/analyses/<run-id>/`
