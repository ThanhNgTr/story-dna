---
name: direct-video
description: |
  Transform a shotlist into a scene-by-scene production guide. Takes structured
  shot breakdowns and outputs director's notes, camera blocking, actor emotional
  cues, lighting setups, and pacing directions. Ready for crew briefing or AI
  video generation. Triggers on: "direct video", "production guide", "director notes",
  "scene blocking", "video production plan".
---

# Direct Video: Production Guide Generator

## When to Use

Use this skill when you have a `shotlist.json` from `/script-to-shotlist` and need:
- Director's scene-by-scene notes
- Camera blocking + movement cues
- Actor emotional arc per shot
- Lighting setup per scene
- Pacing + rhythm notes
- Audio sync points

**Input**: `shotlist.json` (from `/script-to-shotlist`)
**Output**: `production_guide.md` + `production_guide.json` (ready for crew)

## Quick Start

```
/direct-video --shotlist data/scripts/generated/shotlist.json \
  --tone "gothic thriller" \
  --visual-reference "desaturated teal + warm amber practicals"
```

Output: Scene-by-scene production notes with blocking, lighting, actor cues.

## How It Works

### Input Format

The skill expects `shotlist.json` structured as:

```json
{
  "script_title": "Episode Title",
  "duration_sec": 90,
  "aspect_ratio": "9:16",
  "shots": [
    {
      "shot_id": "s01",
      "timecode": "00:00-00:10",
      "duration_sec": 10,
      "scene_name": "COLD OPEN",
      "location": "EXT. FOREST — NIGHT",
      "characters": ["char_01"],
      "action": "Protagonist running, terror",
      "dialogue": null,
      "camera_direction": "handheld, escalating MS → CU → ECU",
      "visual_description": "fog, pines, torch glow",
      "mood": "fear, adrenaline"
    },
    ...
  ]
}
```

### Processing

For each shot, the skill produces:

1. **Scene Header** — location, time of day, characters present
2. **Director's Intent** — emotional objective, pacing cue, narrative purpose
3. **Camera Blocking** — position, movement, framing (shot sizes)
4. **Actor Emotional Arc** — how each character feels in this shot, physical tells
5. **Lighting Setup** — key light, fill, practicals, mood lighting
6. **Sound Sync** — where audio cues land (music swell, dialogue, foley)
7. **Continuity Notes** — wardrobe, props, position carryover from prior shot

### Director's Intent

The skill annotates each shot with **why** it exists:
- **Hook**: "Stop scroll, raise question"
- **Exposition**: "Establish world without dialogue"
- **Build**: "Escalate tension"
- **Peak**: "Emotional climax"
- **Hold**: "Cliffhanger, defiant stare"

This guides the director (or AI) on *what to prioritize* in that shot.

---

## Output Format

### Production Guide (Markdown)

```markdown
# PRODUCTION GUIDE: Episode Title
**Format** 9:16 · **Duration** 90s · **Tone** gothic thriller

## SCENE 1: COLD OPEN (00:00–00:10, 10s)
**Location**: EXT. FOREST — NIGHT

### Director's Intent
Hook: Stop scroll, raise urgent question. Establish protagonist in physical terror without exposition.

### Camera Blocking
- Position: Handheld, close on protagonist face
- Movement: Escalating push-in; MS (medium shot) → CU (close-up) → ECU (extreme close-up)
- Framing: Off-center when running; center on face when paused
- Lens: 35mm handheld (organic, urgent feel)

### Lighting Setup
- Key: Torch glow (practicals only, warm amber)
- Fill: Moonlit fog (volumetric haze, cool rim light)
- Mood: Low-key, high contrast; shadows dominate
- Special: Muzzle flash effect (if applicable)

### Actor Direction
- **char_01 (protagonist)**: Terror, adrenaline. Eyes wide. Breath labored. Glances back frequently. Clutches pendant at throat. No dialogue. Physical vocabulary: running, stumbling, looking for escape.
- Emotional arc for shot: initial panic → determination to escape → realization of being hunted

### Sound Sync
- Foley: Footsteps on leaves/twigs, heavy breathing
- Music: Low drone, sub-bass hits on key moments (running start, look-back)
- Silence: Allow 1–2s of pure footsteps for tension
- No dialogue

### Continuity
- Wardrobe: Navy blazer (wet, torn), white shirt (dirty)
- Props: Ring pendant (visible in close-ups), no phone
- Entry Point: Emerges from darkness
- Exit Point: Disappears into fog
```

### Production Guide (JSON)

```json
{
  "production_timestamp": "2026-10-01T...",
  "script_title": "Episode Title",
  "total_scenes": 9,
  "scenes": [
    {
      "scene_id": "s01",
      "timecode": "00:00-00:10",
      "scene_name": "COLD OPEN",
      "location": "EXT. FOREST — NIGHT",
      "duration_sec": 10,
      "director_intent": "Hook; stop scroll, raise question",
      "characters_present": ["char_01"],
      "camera_blocking": {
        "position": "handheld, close on face",
        "movement": "escalating push-in",
        "shot_progression": ["MS", "CU", "ECU"],
        "lens_choice": "35mm",
        "framing_note": "off-center while running, center on face"
      },
      "lighting_setup": {
        "key_light": "torch glow (practicals)",
        "fill_light": "moonlit fog",
        "mood": "low-key, high contrast",
        "color_temp": "warm amber practicals, cool rim",
        "special_effects": ["volumetric haze", "muzzle flash (optional)"]
      },
      "actor_direction": {
        "char_01": {
          "emotion": "terror, adrenaline",
          "physical_tells": ["eyes wide", "breath labored", "glances back", "pendant clutch"],
          "dialogue": null,
          "physical_vocabulary": ["running", "stumbling", "looking for escape"],
          "emotional_arc": "panic → determination → hunted realization"
        }
      },
      "sound_sync": {
        "foley": ["footsteps on leaves", "heavy breathing"],
        "music": ["low drone", "sub-bass hits"],
        "silence_beats": 2,
        "dialogue": null,
        "special": "allow pure foley 1–2s"
      },
      "continuity": {
        "wardrobe": "navy blazer (wet/torn), white shirt (dirty)",
        "props": ["ring pendant (visible in CUs)"],
        "entry": "emerges from darkness",
        "exit": "disappears into fog"
      },
      "pacing_note": "fastest cutting in episode; 1–2s shot lengths"
    }
  ],
  "crew_notes": {
    "key_locations": ["EXT. FOREST", "INT. ASSEMBLY HALL", "INT. DORM", "COURTYARD FENCE"],
    "key_props": ["ring pendant", "ELI portrait", "phone crate", "RULES board"],
    "special_requirements": ["fog machine", "torch practicals", "window light rig"],
    "continuity_warnings": ["protagonist wardrobe damage progression", "window watcher position changes"]
  }
}
```

---

## Generation Rules

1. **Match tone and pacing** from the DNA. If tone is "grave, no humor," director's notes reflect that seriousness.
2. **Emotional continuity** — each shot's actor direction should connect to the prior shot's emotional end.
3. **Lighting should enhance mood** — desaturated palette + warm practicals = sophisticated, moody, premium.
4. **Actor tells from DNA** — if protagonist clutches pendant, ensure it appears in close-ups.
5. **Continuity tracking** — wardrobe damage, prop position, window position all carry through.
6. **Sound sync** — marry foley + music to key emotional beats.
7. **Crew readiness** — output should be distributable to cinematographer, lighting designer, sound designer without additional translation.

---

## Example: Full Scene

### Input Shot
```json
{
  "shot_id": "s07",
  "timecode": "01:07-01:27",
  "duration_sec": 20,
  "scene_name": "GROUP ARGUMENT",
  "location": "EXT. COURTYARD — NIGHT, FOG",
  "characters": ["char_01", "char_06", "char_07", "char_08", "char_09"],
  "action": "Students argue about escaping; protagonist and allies vs. agitators",
  "dialogue": "char_06: 'We have to get out.' char_08: 'That's crazy, we'll get caught.' char_01: (silent, watches)",
  "camera_direction": "handheld, fast cuts, 1–2s per cut",
  "visual_description": "fog, pines, night, group formation, torches",
  "mood": "tension, accusation, disagreement"
}
```

### Output Director Notes

```markdown
## SCENE 7: GROUP ARGUMENT (01:07–01:27, 20s)
**Location**: EXT. COURTYARD — NIGHT, FOG

### Director's Intent
Build: Escalate tension. Show student coalition fracturing. Protagonist is now observer/decision-maker (not just victim). Fast cuts mirror emotional chaos.

### Camera Blocking
- **Formation**: Group in loose semi-circle, protagonist slightly apart (observer position)
- **Handheld**: Fast, jerky pans between speakers (mimic conversation flow)
- **Shot rhythm**: 1–2s cuts; cut on each accusation or silence
- **Focus**: Rack focus to speaker when dialogue lands; blur periphery
- **Framing**: Protagonist centered in wider shots; crop others on reaction
- **Exit movement**: Characters move apart (fracture the group visually)

### Lighting Setup
- **Key**: Torch practicals only (character-held lights)
- **Fill**: Fog diffuses light, creates silhouettes
- **Mood**: Low-key, shadows dominate, amber torches as sole color contrast
- **Special**: Rim light from torches on faces; cold blue moonlight on fog
- **Direction**: Lights move as characters gesture (creates dynamic shadows)

### Actor Direction
- **char_01 (protagonist)**: Mostly silent. Watches. Eyes move between char_06 (ally, trusts) and char_08 (agitator, doubts). Nods slightly at key char_06 moments. Pendant clutch when char_08 speaks (fear). End on determined stare (I decide). Physical vocabulary: small, observant, then decisive.
- **char_06 (ally)**: Urgent, protective. Gestures toward gate/escape. Voice rising but controlled. Positioning: near protagonist, often turning to her for support. Arc: confident → frustrated → resigned to her choice.
- **char_08 (agitator)**: Accusatory, fast-talking. Points, argues. Voice high-pitched with anxiety. Positioning: opposite to char_06 (visual conflict). Arc: aggressive → fearful → backing down.
- **char_07, char_09**: Reactions. Quiet agreement or fear (no dialogue). Fill background, don't distract.

### Sound Sync
- **Dialogue**: char_06 line at 01:10, char_08 rebuttal at 01:13, silence 01:15–01:17 (protagonist's thinking moment)
- **Foley**: Footsteps as they move, fabric rustle, torch creaking/burning ambience
- **Music**: Build underlying tension (tonal swell); no score during dialogue, allow voices to dominate
- **Silence beat**: 01:15–01:17 (silence is most powerful; let fog ambience exist)
- **Sync point**: Music swell starts when protagonist nods (her decision moment)

### Continuity
- **Wardrobe**: All in uniforms (navy blazer, tie, etc.). Protagonist's blazer still wet from prior escape.
- **Props**: Torches (character-held), no phones, ring pendant visible in CU of char_01
- **Positioning carryover**: Char_06 exits toward gate; char_01 follows moments later
- **Emotional carryover**: Char_01 goes from fear (prior scene) → observation → determination (this scene) → action (next scene)
```

---

## Notes

- Output is **director-ready** — distributable to cinematography, lighting, sound, and acting teams
- **JSON format** enables automated crew briefings or AI video generation
- **Continuity tracking** prevents continuity errors in multi-take or AI production
- Each scene includes **actor emotional arc** (how they feel, physical tells) not just dialogue
- **Pacing notes** guide cut rhythm + shot length (supports editor)

## Usage Pipeline

```
/script-to-shotlist <script.md>
  ↓ (produces shotlist.json)
/direct-video --shotlist <shotlist.json>
  ↓ (produces production_guide.md + .json)
[Give to cinematographer, lighting, sound, actors for briefing]
```
