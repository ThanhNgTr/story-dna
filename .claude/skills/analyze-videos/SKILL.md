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

### Step 1 — Shot detection + frame extraction (Python + ffmpeg)
Run `_analyze.py` to detect cuts, measure pacing, extract keyframes and write manifest:

```bash
cd /path/to/story-dna
python3 .claude/skills/analyze-videos/_analyze.py \
  --input data/analyses/ep1.mp4 \
  --max-frames 30 \
  --output-dir data/analyses
```

Default `--sampling shot`:
- ffmpeg scene score per frame, adaptive rule (cut = score ≥ 0.3, or ≥ `--scene-threshold` and 3× neighbor avg) → real cut timestamps
- Pacing computed by code from the cut list (`pacing_measured`), not guessed from frames
- 1 keyframe per shot (middle of shot); spare budget goes to long shots. If shots > `--max-frames`, hook shots (first 3s) are kept and the rest are spread evenly — pacing still covers ALL shots
- Detection fails → falls back to `--sampling uniform` (old behavior, `--fps`)

Output in `data/analyses/<timestamp>/`:
- `manifest.json`: per video `sampling`, `pacing_measured`, `shots_path`, `frames` (`path`, `t_sec`, `shot_id`)
- `shots/<stem>.json`: full shot list (`t_start`, `t_end`, `duration_sec`, `cut_score`, `has_frame`) + `pacing_measured`
- `frames/<stem>/frame_NNNN_tSSSS.SS_sNNN.jpg` (timestamp + shot id in filename)

Known limits: fades/dissolves are often missed (merged into one long shot); lightning/flash inside one shot can add a false cut. Fast-cut videos (avg < 2.5s) need `--max-frames 40`+ to keep one frame per shot.

### Step 1b — Audio: transcript + speakers (WhisperX, local CPU)
Adds real dialogue so agents stop lip-reading. Runs in the project venv (`.venv/`, gitignored):

```bash
# one-time setup (no sudo): uv + venv + whisperx (~2.5 GB)
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path
~/.local/bin/uv venv .venv --python 3.12
~/.local/bin/uv pip install --python .venv/bin/python whisperx \
  --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

# per run
.venv/bin/python .claude/skills/analyze-videos/_transcribe.py \
  --manifest data/analyses/<run>/manifest.json [--model large-v3-turbo] [--language en]
```

- Writes `transcripts/<stem>.json`: `segments[]` (`start`, `end`, `text`, `speaker`, `shot_id`, `words[]`), `silences[]` (ffmpeg silencedetect, < -40 dB for ≥ 0.5s), `audio` summary
- Adds `transcript_path` + `audio` to each manifest video
- Speaker labels (`SPEAKER_00`...) only when `HF_TOKEN` is set and the pyannote diarization model terms are accepted on Hugging Face; otherwise `speaker: null` and agents assign speakers from frames
- No audio stream → `audio.has_audio: false`, skipped. ASR fails → silences still saved, agents fall back to visual-only
- No venv → skip this step; pipeline still works (dialogue marked `inferred`)

### Step 2 — Per-video analysis (subagent `video-analyst`, one per video)
Frame images must NOT be read in the main context (30 frames ≈ 45k tokens). For each entry in `manifest.json`, launch one `video-analyst` agent **in parallel** with:

```
frames_dir:  <videos[i].frames_dir>
filename:    <videos[i].filename>
duration_sec / sampling / frames_extracted from the manifest
shots_path:  <videos[i].shots_path>  (shot mode only)
fps_extracted: <videos[i].fps_extracted>  (uniform mode only)
transcript_path: <videos[i].transcript_path>  (if Step 1b ran)
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

### Step 4 — Hand off
- First run / new series -> `/skill-creator-from-dna --dna <run_dir>/dna.json --name <slug>`
- New viral idea for an existing skill -> `/skill-creator-from-dna --dna <run_dir>/dna.json --update <slug>`

Check `.claude/skills/write-story-*` and suggest which one to the user.

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

### More frames (fast-cut video, keep 1 frame per shot)
```bash
python3 .claude/skills/analyze-videos/_analyze.py \
  --input data/analyses/ep1.mp4 --max-frames 45
```

### Too many / too few cuts detected
```bash
# fewer false cuts (bright, high-contrast footage)
--scene-threshold 0.2
# catch more cuts (dark, low-contrast footage)
--scene-threshold 0.08
```

### Old uniform sampling
```bash
python3 .claude/skills/analyze-videos/_analyze.py \
  --input data/analyses/ep1.mp4 --sampling uniform --max-frames 60 --fps 2.0
```

### Directory of videos
```bash
python3 .claude/skills/analyze-videos/_analyze.py --input data/samples/
```

## Notes

- Requires `ffmpeg` + `ffprobe` (check: `ffmpeg -version`)
- Does NOT require `anthropic` package or API key
- Shot detection + extraction: ~5–15s per 90s video (detection decodes the full video at 320px)
- Vision analysis: Claude Code reads frames inline — no extra cost beyond session
- All outputs reproducible in `data/analyses/<run-id>/`
