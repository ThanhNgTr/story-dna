---
name: script-to-shotlist
description: |
  Break a finished script into individual 1–5s shots with timecode, 
  visuals, dialogue, and camera directions. Generates shotlist.json 
  (machine-readable) and shotlist.md (human-readable). Output ready 
  for video generation (image/video AI prompts). Triggers on: "break 
  into shots", "create shotlist", "shot breakdown", "shot list", 
  "scene breakdown", "storyboard script". Input: Script Markdown. 
  Output: JSON shotlist + Markdown storyboard.
---

# Script → Shot Breakdown

## When to Use This Skill

Use after finalizing a script with `/write-story-<slug>`:
- Break script into discrete 1–5s shots
- Create structured data for video generation (image/video AI)
- Generate visual descriptions for each shot
- Assign dialogue, actions, camera directions to shots
- Produce storyboard-like Markdown for review

**Input**: Finished script (Markdown)
**Output**: `shotlist.json` + `shotlist.md` with 1–5s shot breakdown

## Quick Start

```bash
/script-to-shotlist "# My Script\n\n## Scene 1\nAlice walks into the office..."
```

Or paste script Markdown and it will output:
- `shotlist.json` - Machine-readable (for downstream tools)
- `shotlist.md` - Human-readable storyboard

## How It Works

### Step 1: Parse Script
- Identify scenes, dialogue, action beats
- Extract character names, locations, tone cues
- Respect pacing from original DNA rules

### Step 2: Segment into Shots
- Break scenes into individual shots (1–5s each)
- Apply pacing rules:
  - Dialogue-heavy scenes: 2–3s per shot
  - Action-heavy scenes: 1.5–3s per shot
  - Establishing shots: 3–5s
- Distribute screen time among characters

### Step 3: Create Shot Descriptions
- For each shot, generate:
  - Visual description (for image/video generation)
  - Character actions
  - Dialogue (if any)
  - Camera direction (angle, movement, transition)
  - Audio cue (music, SFX, voiceover)
  - Mood/tone note

### Step 4: Generate Output Files
- `shotlist.json` - Structured for video gen tools
- `shotlist.md` - Storyboard for human review

## Output Format

### `shotlist.json` (Machine-Readable)
```json
{
  "script_title": "My Script",
  "total_duration_sec": 30,
  "total_shots": 11,
  "shots": [
    {
      "shot_number": 1,
      "timecode_start": "00:00:00",
      "timecode_end": "00:00:03",
      "duration_sec": 3,
      "shot_type": "establishing",
      "location": "Office",
      "characters": [],
      "dialogue": "",
      "action": "Wide shot of modern office, morning light",
      "visual_description": "Bright, modern office space. Large windows. Minimalist decor. Camera pulls back slowly.",
      "camera_direction": "Wide static shot, slow pull-back (dolly)",
      "camera_angle": "eye level",
      "audio_cue": "Upbeat instrumental music fades in",
      "mood": "energetic, professional",
      "notes": "Set the scene, establish mood"
    },
    {
      "shot_number": 2,
      "timecode_start": "00:00:03",
      "timecode_end": "00:00:06",
      "duration_sec": 3,
      "shot_type": "close-up",
      "location": "Office",
      "characters": ["Alice"],
      "dialogue": "Good morning, team.",
      "action": "Alice sits at her desk, looks at camera",
      "visual_description": "Tight shot of Alice smiling at camera. Professional attire. Natural light on face.",
      "camera_direction": "Close-up on face, slight pan right",
      "camera_angle": "slightly above eye level",
      "audio_cue": "Alice's voice, music continues softly",
      "mood": "confident, welcoming",
      "notes": "Direct address to camera builds connection"
    }
  ]
}
```

### `shotlist.md` (Human-Readable)
```markdown
# My Script — Shot Breakdown

**Total Duration**: 30s | **Total Shots**: 11

---

## Shot 1: ESTABLISHING
**Timecode**: 00:00:00 → 00:00:03 (3s)  
**Location**: Office

### Visual
Bright, modern office space. Large windows. Minimalist decor. Camera pulls back slowly.

### Action
Wide shot of modern office, morning light

### Camera
- Direction: Wide static shot, slow pull-back (dolly)
- Angle: Eye level

### Audio
Upbeat instrumental music fades in

### Mood
Energetic, professional

### Notes
Set the scene, establish mood

---

## Shot 2: CLOSE-UP
**Timecode**: 00:00:03 → 00:00:06 (3s)  
**Location**: Office  
**Character**: Alice

### Visual
Tight shot of Alice smiling at camera. Professional attire. Natural light on face.

### Dialogue
> Good morning, team.

### Action
Alice sits at her desk, looks at camera

### Camera
- Direction: Close-up on face, slight pan right
- Angle: Slightly above eye level

### Audio
Alice's voice, music continues softly

### Mood
Confident, welcoming

### Notes
Direct address to camera builds connection

---

[... more shots ...]
```

## Prompt Suggestions for Video Generation

Each shot in `shotlist.md` can be converted to a video generation prompt:

**Shot 1**: "Wide shot of bright modern office with large windows, morning light, camera pulls back slowly. Upbeat instrumental music. Professional atmosphere."

**Shot 2**: "Close-up of woman in professional attire at desk looking at camera, smiling, natural light on face. She says 'Good morning, team.' Confident, welcoming mood."

## Integration with Video Tools

`shotlist.json` is ready to feed into:
- **Seedance** (Higgsfield) for video generation
- **Image generation AI** for visual reference frames
- **Storyboard software** for team collaboration
- **Teleprompter apps** for voiceover recording

## Notes

- Shot durations respect pacing from original DNA
- Visual descriptions are detailed for AI image/video generation
- Camera directions include angle + movement + transitions
- Dialogue preserved exactly from script
- Mood/tone notes help maintain consistency across shots
- JSON format enables programmatic use (batch generation, etc.)
