---
name: analyze-videos
description: |
  Extract narrative DNA from local video files. Analyzes frame sequences, 
  audio, pacing, character patterns, and tone to produce structured DNA 
  reports that feed into script generation. Triggers on keywords like 
  "analyze video", "extract DNA", "video analysis", "analyze frames", 
  "video structure", "narrative analysis". Input: local video file or 
  directory. Output: DNA JSON + human-readable Markdown report + frame 
  images. POC uses Claude Vision (no external APIs). Essential first step 
  before skill generation.
---

# Video Analysis → Narrative DNA Extraction

## When to Use This Skill

Use this skill when you have local reference videos and need to understand their narrative patterns:
- Learn the structure/pacing/tone from existing videos
- Extract reusable narrative rules for skill generation
- Analyze shot composition, character archetypes, dialogue flow
- Build a foundation for creating similar content

**Input**: Local video file(s) or directory (MP4, MOV, etc.)
**Output**: `dna.json` (structured rules) + `dna.md` (report) + `frames/` (extracted images)

## Quick Start

```bash
/analyze-videos --input samples/ --max-frames 30
```

This will:
1. Extract up to 30 frames from each video
2. Call Claude Vision to analyze shot sequences
3. Extract audio (if present) and basic transcript
4. Analyze narrative structure (pacing, transitions, tone)
5. Output DNA + report to `data/analyses/<timestamp>/`

## How It Works

### Step 1: Frame Extraction
- Uses `ffmpeg` to extract frames @ 1 fps (default) or custom rate
- Capped at `--max-frames` (default 30) to control output size
- Saved as JPEG to `frames/`

### Step 2: Vision Analysis
- Groups frames into batches (e.g., 10 frames per call)
- Calls Claude Vision on each batch
- Extracts: shot descriptions, transitions, pacing, visual style

### Step 3: Audio & Transcript
- Extracts audio track using `ffmpeg`
- Attempts transcription (manual JSON fallback for POC)
- Segments by pauses/scene breaks

### Step 4: Structure Analysis
- Analyzes narrative timing: setup → conflict → resolution
- Detects pacing rhythm (fast cuts vs. long shots)
- Identifies character archetypes from visual patterns
- Extracts tone/mood cues (music, color, camera movement)

### Step 5: DNA Assembly
- Combines all analysis into `dna.json`
- Generates human-readable `dna.md`
- Stores per-video metadata in `videos_analyzed.json`

## Output Format

### `dna.json` (Structured)
```json
{
  "analysis_timestamp": "2025-10-01T14:30:00Z",
  "videos_analyzed": [
    {
      "filename": "sample.mp4",
      "duration_sec": 45.2,
      "frame_count": 30,
      "fps": 1.0
    }
  ],
  "narrative_structure": {
    "setup_duration_sec": 3.5,
    "setup_pct": 8,
    "climax_timing_pct": 75,
    "resolution_pct": 85,
    "ending_hook": "Strong CTA: 'Subscribe now'"
  },
  "pacing": {
    "avg_shot_duration_sec": 2.8,
    "cut_rhythm": "medium",
    "transition_style": "straight cuts + occasional dissolves",
    "fastest_shot_sec": 0.8,
    "slowest_shot_sec": 8.0
  },
  "characters": [
    {
      "archetype": "Mentor/Expert",
      "count": 1,
      "screen_time_pct": 60,
      "dialogue_style": "conversational, energetic"
    }
  ],
  "tone": {
    "overall": "conversational",
    "formality": "casual",
    "energy": "high",
    "emotion": "inspiring"
  },
  "hooks": {
    "opening_0_3s": "Question or visual surprise",
    "midpoint": "Problem statement or tension",
    "closing": "Strong call-to-action or teaser"
  },
  "visual_style": {
    "color_palette": "vibrant, high contrast",
    "camera_movement": "mix of static and dynamic pans",
    "aspect_ratio": "16:9",
    "lighting": "bright, well-lit studio or natural"
  },
  "audio": {
    "music_presence": true,
    "music_style": "upbeat, contemporary",
    "voiceover": true,
    "dialogue": true,
    "sound_effects": true
  }
}
```

### `dna.md` (Human-Readable)
```markdown
# Video Analysis Report

## Videos Analyzed
- sample.mp4 (45.2s, 30 frames)

## Narrative Structure
- Setup: 0–3.5s (8%)
- Rising Action: 3.5–33.8s (67%)
- Climax: 33.8s (75%)
- Resolution: 38.3–45.2s (15%)

**Hook**: "Question or visual surprise in opening 0–3s"
**CTA**: "Strong call-to-action at end: Subscribe now"

## Pacing & Rhythm
- Avg shot duration: 2.8s
- Rhythm: Medium (mix of quick cuts and longer shots)
- Fastest shot: 0.8s | Slowest shot: 8.0s
- Transitions: Straight cuts + occasional dissolves

## Characters
- 1 Mentor/Expert figure (60% screen time)
- Dialogue: Conversational, energetic tone
- Direct address to camera / high engagement

## Tone & Voice
- Overall: Conversational, casual, high-energy, inspiring
- Formality: Informal (feels like talking to a friend)
- Emotion: Positive, motivational

## Visual Style
- Colors: Vibrant, high-contrast palette
- Camera: Mix of static shots and dynamic pans
- Lighting: Bright, well-lit (studio or natural)
- Aspect: 16:9 widescreen

## Audio Design
- Music: Upbeat, contemporary (present throughout)
- Voiceover: Yes (conversational, no script read)
- Dialogue: Natural, includes Q&A or reactions
- Sound effects: Subtle (door slams, transitions)

## Key Insights for Script Generation
1. Keep opening hooks strong (visual + audio surprise)
2. Maintain medium pacing (not too fast, not too slow)
3. Use direct camera address to build connection
4. Balance talking head with B-roll / visual interest
5. End with clear CTA, not just fade out
```

### `videos_analyzed.json`
```json
{
  "sample.mp4": {
    "duration_sec": 45.2,
    "frame_count": 30,
    "fps": 1.0,
    "has_audio": true,
    "has_transcript": true,
    "frame_dir": "frames/sample_mp4/"
  }
}
```

## References

- `dna-schema.json` - Full DNA schema + field definitions
- `_analyze.py` - Frame extraction + Vision batching logic

## Examples

### Example 1: Analyze a single video
```bash
/analyze-videos --input video.mp4
# Output: data/analyses/20251001-120000/dna.json
```

### Example 2: Analyze a directory of videos
```bash
/analyze-videos --input samples/ --max-frames 15
# Combines DNA from all videos in samples/
```

### Example 3: Custom frame rate
```bash
/analyze-videos --input video.mp4 --fps 2 --max-frames 45
# Extract 2 frames per second, up to 45 total
```

## Notes

- Requires `ffmpeg` installed locally
- Frame extraction can take 1–2 minutes per video (use `--max-frames` to control)
- Claude Vision has context limits — frames are batched automatically
- No external APIs needed (uses Claude Vision + local ffmpeg)
- All outputs saved to `data/analyses/<timestamp>/` for reproducibility
