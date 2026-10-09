---
name: script-to-shotlist
description: |
  Break a finished script into individual 1–5s shots with timecode, 
  visuals, dialogue, and camera directions. Generates shotlist.json 
  (machine-readable) and shotlist.md (human-readable). Output ready 
  for video generation (image/video AI prompts). Triggers on: "break 
  into shots", "create shotlist", "shot breakdown", "shot list", 
  "scene breakdown", "storyboard script", "prompt list", "video prompts".
  Input: approved script Markdown. Output: shotlist.json/.md + prompts.json/.md
  (one self-contained video-gen prompt per 1-5s shot: who says what, does what).
---

# Script → Shot Breakdown

## When to Use This Skill

Use after a series is approved (`/write-series-<slug>` + `/refine-skill <slug> --approve`).
Input: one episode screenplay (`data/series/<slug>/<session-id>/final/epNN.md` + `.json`), or the
whole `final/` dir -> each episode is processed separately, outputs go to `final/shots/epNN/`.
Characters stay identical across episodes: build the character anchors once from the series bible
(`final/bible.md`) and reuse them for every episode.

What it does:
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
- `prompts.json` + `prompts.md` - Prompt list, see Step 5

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

## Step 5: Prompt List (final output of the pipeline)

Input should be an APPROVED episode (`data/series/<slug>/<session-id>/final/epNN.md` from
`/refine-skill --approve`). Draft episode (`episodes/epNN_vK.md`) -> warn user, continue only if they confirm.

Write to `final/shots/epNN/`:
- `prompts.json` - one entry per shot, for video gen tools / agents
- `prompts.md` - numbered list for humans

### Character, outfit and location anchors
Source of looks, first that exists: `final/assets.json`, else the latest `assets/assets_vN.json`
(asset registry from `/series-assets`), else the bible (`final/bible.json` -> `visual_signature`).

With a registry:
- Character anchor = `characters[].prompt_en` (face/hair/body) + the outfit worn in this scene
  (`wardrobe[].prompt_en`; outfit from the episode scene `cast`, else the registry `scene_map`).
- Location anchor = `locations[].prompt_en` + the scene variant's `lighting`.
- Prop anchor = `props[].prompt_en` (text on props verbatim).
- Every prompt ends with `style.prompt_suffix_en`.
- Each shot lists `refs`: approved reference images from `assets/images.json` (status `approved`)
  for the characters (outfit image if one exists for the worn outfit, else the character sheet),
  the location variant and the props in the shot, as paths relative to the session. Empty when
  none is approved yet. Every shot also carries `loc_id`, `variant_id` and `props` from its scene, so
  the web app's "Tải gói video" zip (app/pipeline/package.py) can attach refs approved later.

Every prompt that shows a character repeats its anchor text word-for-word. Same character must
look identical in every shot; the outfit changes only where the scene `cast` changes it.

### `prompts.json`
```json
{
  "source_script": "data/series/<slug>/20261001-143000/final/ep01.md",
  "skill": "write-series-<slug>",
  "skill_version": "v3",
  "aspect_ratio": "9:16",
  "total_duration_sec": 90,
  "assets": "data/series/<slug>/20261001-143000/final/assets.json",
  "characters": {
    "char_01": "teen girl, 16, dark wavy shoulder-length hair, navy blazer, white shirt, silver ring pendant"
  },
  "locations": {"loc_02": "foggy dead pine forest at night, ..."},
  "shots": [
    {
      "shot_number": 1,
      "start_sec": 0,
      "end_sec": 3,
      "duration_sec": 3,
      "characters": ["char_01"],
      "action": "char_01 runs through foggy forest, glances back over shoulder",
      "dialogue": [],
      "sfx": "heavy breathing, snapping branches",
      "camera": "handheld tracking MS, push-in",
      "loc_id": "loc_02", "variant_id": "loc_02_night", "props": [], "outfits": {"char_01": "char_01_o1"}, "refs": [],
      "video_prompt": "Night, dense foggy pine forest. teen girl, 16, dark wavy shoulder-length hair, navy blazer, white shirt, silver ring pendant, runs toward camera in panic, glances back over her shoulder. Handheld tracking medium shot, slow push-in. Torch light from behind, desaturated teal, volumetric fog. Sound: heavy breathing, snapping branches. 3 seconds, 9:16."
    },
    {
      "shot_number": 2,
      "start_sec": 3,
      "end_sec": 5,
      "duration_sec": 2,
      "characters": ["char_01"],
      "action": "char_01 stops, whispers",
      "dialogue": [{"character": "char_01", "line": "He's still here.", "delivery": "whisper, terrified"}],
      "sfx": "wind",
      "camera": "static CU",
      "video_prompt": "Close-up, teen girl, 16, dark wavy shoulder-length hair, navy blazer, white shirt, silver ring pendant, stops, out of breath, whispers \"He's still here.\" terrified. Static close-up, shallow depth of field, cold moonlight on face, fog behind. Sound: wind. 2 seconds, 9:16."
    }
  ]
}
```

### `prompts.md`
```markdown
# <Title> - Prompt List (90s, 32 shots, skill <slug> v3)

## Characters
- char_01: teen girl, 16, dark wavy shoulder-length hair, navy blazer, ...

## Shots
1. [00:00-00:03] (3s) char_01 runs, glances back. No dialogue.
   PROMPT: Night, dense foggy pine forest. teen girl, 16, ... 3 seconds, 9:16.
2. [00:03-00:05] (2s) char_01: "He's still here." (whisper)
   PROMPT: Close-up, teen girl, 16, ... 2 seconds, 9:16.
```

### Prompt rules
- Each shot 1-5s. Longer beat -> split into several shots.
- `video_prompt` is self-contained: setting + character anchor + action + dialogue in quotes + camera + light/color + sound + duration + aspect ratio. No "same as before".
- Dialogue: max ~2.5 words/sec of shot. Line too long -> split across shots.
- Shots contiguous: `end_sec` of shot N = `start_sec` of shot N+1. Last `end_sec` = script length.
- Language: prompts in English (video models), dialogue kept in the script's language.

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
