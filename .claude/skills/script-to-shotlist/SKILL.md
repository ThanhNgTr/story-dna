---
name: script-to-shotlist
description: |
  Break a finished script into 1–5s shots (cuts) with timecode, visuals,
  dialogue and camera directions, then group them into 10-15s CLIPS: one
  video generation per clip, several cuts inside it, so faces, outfits,
  light and long dialogue stay consistent. Generates shotlist.json/.md
  (cuts) and prompts.json/.md (clips) for video generation. Triggers on: "break 
  into shots", "create shotlist", "shot breakdown", "shot list", 
  "scene breakdown", "storyboard script", "prompt list", "video prompts".
  Input: approved script Markdown. Output: shotlist.json/.md + prompts.json/.md
  (one self-contained multi-shot video prompt per 10-15s clip: who says what, does what, cut by cut).
---

# Script → Shot Breakdown

## When to Use This Skill

Use after a series is approved (`/write-series-<slug>` + `/refine-skill <slug> --approve`).
Input: one episode screenplay (`data/series/<slug>/<session-id>/final/epNN.md` + `.json`), or the
whole `final/` dir -> each episode is processed separately, outputs go to `final/shots/epNN/`.
Characters stay identical across episodes: build the character anchors once from the series bible
(`final/bible.md`) and reuse them for every episode.

What it does:
- Break script into discrete 1–5s shots (cuts), then group them into 10-15s clips (one prompt each)
- Create structured data for video generation (image/video AI)
- Generate visual descriptions for each shot
- Assign dialogue, actions, camera directions to shots
- Produce storyboard-like Markdown for review

**Input**: Finished script (Markdown)
**Output**: `shotlist.json` + `shotlist.md` with 1–5s shot breakdown (the cuts, for editing), and
`prompts.json` + `prompts.md` with one prompt per 10-15s clip (the unit sent to the video model)

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
- Break scenes into individual shots (1–5s each; up to ~6s when the style's longest shot allows it)
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

## Step 5: Prompt List (final output of the pipeline): 10-15s clips

Input should be an APPROVED episode (`data/series/<slug>/<session-id>/final/epNN.md` from
`/refine-skill --approve`). Draft episode (`episodes/epNN_vK.md`) -> warn user, continue only if they confirm
(headless: do not continue on a draft; say the episode must be finalized first).

Write to `final/shots/epNN/`:
- `prompts.json` - one entry per CLIP (10-15s, one video generation), for video gen tools / agents
- `prompts.md` - numbered list for humans

Why clips: a 1-2s prompt per shot means 30-40 separate generations per episode; faces, outfits,
light and voices drift between them, and a dialogue exchange gets cut into pieces that never match.
Current video models (Seedance 2, Kling, Veo) take one prompt with several timed cuts and keep the
same people and place inside it. The style's fast cutting stays: it lives INSIDE the clip.

### Grouping shots into clips
- One clip = all or part of ONE scene of the script (a scene is one place at one time). A clip never
  crosses a scene boundary, even when both scenes share a `loc_id` (the dining room and the back
  garden of the same villa are two settings): two conversations in two places are two clips.
- Clip length 10-15s (aim ~12s). A scene shorter than 10s is its own shorter clip (do not borrow
  time from the next scene). A scene longer than 15s is split into clips of 10-15s.
- Phone calls / intercut scenes (lines alternate between two places): one clip per place, holding
  that side's lines lip-synced; the other side is an off-screen voice in the same clip. The editor
  intercuts the two clips afterwards (say so in `continuity_in`).
- Never split a dialogue line. Keep a whole exchange in one clip; when an exchange runs past 15s,
  split at a speaker change, and the next clip opens on the same framing (`continuity_in`).
- Cuts inside a clip follow the style's pacing (cuts/min, shot sizes); each cut 1-5s.
- Clips are contiguous: `end_sec` of clip N = `start_sec` of clip N+1; last `end_sec` = episode length.
- Check before reporting done: `python3 -m app.pipeline.package check <session-dir> <episode>` ->
  0 errors (clip inside one scene, 15s max, contiguous, every line timed inside its clip). Fix and re-run.

### Character, outfit and location anchors
Source of looks, first that exists: `final/assets.json`, else the latest `assets/assets_vN.json`
(asset registry from `/series-assets`), else the bible (`final/bible.json` -> `visual_signature`).

With a registry:
- Character anchor = `characters[].prompt_en` (face/hair/body) + the outfit worn in this scene
  (`wardrobe[].prompt_en`; outfit from the episode scene `cast`, else the registry `scene_map`).
- Location anchor = `locations[].prompt_en` + the scene variant's `lighting`.
- Prop anchor = `props[].prompt_en` (text on props verbatim).
- Every prompt ends with `style.prompt_suffix_en`.
- Each clip lists `refs`: approved reference images from `assets/images.json` (status `approved`)
  for the characters on screen (outfit image if one exists for the worn outfit, else the character
  sheet; speaking characters first), then the location variant, then props; at most 6, as paths
  relative to the session. Empty when none is approved yet. Every clip also carries `loc_id`,
  `variant_id`, `props` and `outfits`, so the web app's "Tải gói video" zip (app/pipeline/package.py)
  can attach refs approved later.

Every clip prompt states each character's anchor ONCE, word-for-word, at the top (as "Cast"), then
refers to them by name in the cuts. Same character looks identical in every clip; the outfit changes
only where the scene `cast` changes it.

### `prompts.json`
```json
{
  "unit": "clip",
  "source_script": "data/series/<slug>/20261001-143000/final/ep01.md",
  "skill": "write-series-<slug>",
  "skill_version": "v3",
  "aspect_ratio": "9:16",
  "total_duration_sec": 90,
  "assets": "data/series/<slug>/20261001-143000/final/assets.json",
  "style_suffix": "vertical 9:16 frame, photoreal, ...",
  "characters": {"char_01": "teen girl, 16, dark wavy shoulder-length hair, navy blazer, white shirt, silver ring pendant"},
  "locations": {"loc_02": "foggy dead pine forest at night, ..."},
  "shots": [
    {
      "shot_number": 1,
      "scene": "SC1",
      "start_sec": 0, "end_sec": 12.5, "duration_sec": 12.5,
      "characters": ["char_01", "char_02"],
      "loc_id": "loc_02", "variant_id": "loc_02_night", "props": ["prop_03"],
      "outfits": {"char_01": "char_01_o1", "char_02": "char_02_o1"},
      "refs": ["assets/characters/char_01/char_01_sheet_v1.png", "assets/locations/loc_02/loc_02_night_v1.png"],
      "action": "Lan runs through the fog, stops when Minh blocks her path; they argue in whispers",
      "camera": "handheld; WS -> CU -> OTS -> CU",
      "sfx": "heavy breathing, snapping branches, wind",
      "cuts": [
        {"cut": 1, "start_sec": 0, "end_sec": 2.5, "camera": "handheld tracking WS, push-in",
         "action": "Lan runs toward camera through the fog, glances back", "dialogue": []},
        {"cut": 2, "start_sec": 2.5, "end_sec": 5, "camera": "static CU",
         "action": "Lan stops, out of breath",
         "dialogue": [{"character": "char_01", "line": "Nó vẫn còn ở đây.", "delivery": "thì thào, sợ",
                       "voiceover": false, "start_sec": 2.8, "end_sec": 4.6}]}
      ],
      "dialogue": [{"character": "char_01", "line": "Nó vẫn còn ở đây.", "delivery": "thì thào, sợ",
                    "voiceover": false, "start_sec": 2.8, "end_sec": 4.6}],
      "continuity_in": "",
      "pace_warning": [],
      "video_prompt": "12.5-second vertical 9:16 multi-shot clip, night, dense foggy pine forest (...location anchor...). Cast: Lan: teen girl, 16, ... ; Minh: ... . Shot 1 (0-2.5s): handheld tracking wide shot, Lan runs toward camera through the fog, glances back. Shot 2 (2.5-5s): static close-up on Lan, out of breath; she whispers in Vietnamese, lip-synced: \"Nó vẫn còn ở đây.\" (terrified). Shot 3 (...) ... Same faces, outfits and light in every shot. Sound: heavy breathing, snapping branches, wind. vertical 9:16 frame, photoreal, ..."
    }
  ]
}
```
`shots` is the list of clips (the key name is kept for the app). `cuts` are the clip's internal shots
(the same breakdown as `shotlist.json`, times absolute in the episode). Every dialogue line has its
own `start_sec`/`end_sec` (absolute): subtitles and lip-sync use them.

### `prompts.md`
```markdown
# <Title> - Video clips (90s, 8 clips / 32 cuts, skill <slug> v3)

## Characters
- char_01: teen girl, 16, dark wavy shoulder-length hair, navy blazer, ...

## Clips
1. [00:00-00:12.5] (12.5s) SC1 foggy forest. Cuts: WS run -> CU "Nó vẫn còn ở đây." -> OTS Minh -> CU.
   PROMPT: 12.5-second vertical 9:16 multi-shot clip, ...
```

### Prompt rules
- One prompt per clip of 10-15s (see Grouping). Inside it, numbered timed cuts: "Shot k (a-bs): size
  + movement, who does what, who says what".
- `video_prompt` is self-contained: clip length + aspect ratio + setting anchor + Cast anchors + timed
  cuts + dialogue in quotes with speaker, language and lip-sync (on screen) or "voice-over, off
  screen, not lip-synced" (VO) + light/color + sound + style suffix + "same faces, outfits and light in
  every shot". No "same as before".
- `continuity_in` (and the start of the prompt) describes how the clip opens when it continues the
  previous clip's scene (same framing, positions, light), so the two clips cut together.
- Dialogue rate: `.claude/skills/dialogue-polish/references/vi-dialogue.md` "Speech rate" (Vietnamese
  counted in syllables, hard limit 5.0/s; English 2.5 words/s). Time each line inside its clip. A VO line
  may run over the next cut (L-cut) without a warning; a lip-synced line may run over a cut only while
  the speaker stays on screen. Nothing runs past the clip's end. `pace_warning` ONLY for: a stretch over
  the hard limit, or a lip-synced line whose speaker is off screen while it is spoken.
- Language: prompts in English (video models), dialogue kept in the script's language.

## Integration with Video Tools

`shotlist.json` is ready to feed into:
- **Seedance** (Higgsfield) for video generation
- **Image generation AI** for visual reference frames
- **Storyboard software** for team collaboration
- **Teleprompter apps** for voiceover recording

## Notes

- Cut durations respect pacing from original DNA; prompts are per 10-15s clip
- Visual descriptions are detailed for AI image/video generation
- Camera directions include angle + movement + transitions
- Dialogue preserved exactly from script
- Mood/tone notes help maintain consistency across shots
- JSON format enables programmatic use (batch generation, etc.)
