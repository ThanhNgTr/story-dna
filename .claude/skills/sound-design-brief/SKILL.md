---
name: sound-design-brief
description: |
  Generate audio strategy from production guide. Defines music cues, foley elements,
  dialogue sync points, ambient sound textures, and emotional soundscapes per scene.
  Outputs detailed audio brief for sound designers, composers, and dialogue editors.
  Ready for audio production or Higgsfield audio generation. Triggers on: "sound design",
  "audio strategy", "music cues", "sound brief", "foley list".
---

# Sound Design Brief: Audio Strategy & Cues

## When to Use

Use this skill after `/direct-video` to create:
- Scene-by-scene music cues (tempo, instrumentation, intensity)
- Foley elements (footsteps, breathe, fabric, impacts)
- Ambient sound textures (fog, wind, indoor ambience)
- Dialogue sync points and emotional timing
- Silence beats (where to strip audio for maximum impact)
- Audio emotional arc (how sound mirrors visual mood)

**Input**: `production_guide.json` (from `/direct-video`)
**Output**: `audio_brief.md` + `audio_cue_sheet.json`

## Quick Start

```
/sound-design-brief --production-guide data/series/<slug>/<session-id>/final/shots/ep01/production_guide.json \
  --tone "gothic thriller" \
  --music-style "low drones + sub-bass + tonal swells"
```

## How It Works

### Audio Design Philosophy

**HOLLOW PINE audio strategy**:
- **No voiceover** — dialogue only, sparse (~10–12 lines per 90s)
- **Music is emotional underscore** — not catchy, not memorable, not recognizable
- **Foley is storytelling** — footsteps on leaves reveal location; rain on glass reveals threat
- **Silence is weapon** — strategic silence builds tension more than sound
- **Practicals drive mix** — torch crackle, window rain, wind in pines (on-scene sounds)

### Audio Frequency Zones

| Zone | Frequency | Elements | Emotional Impact |
|---|---|---|---|
| **Subsonic / Sub-bass** | 20–60 Hz | Ambient drones, heartbeat synth | Dread, physical unease (felt, not heard) |
| **Low** | 60–250 Hz | Footsteps, chest/throat sounds, bass synth | Grounding, presence, threat |
| **Mid** | 250–2 kHz | Dialogue, foley impacts, strings | Clarity, emotional directness |
| **High** | 2–8 kHz | Sibilance, rain, wind, strings | Tension, detail, presence |
| **Presence** | 8–20 kHz | Ambience texture, air | Intimacy, danger lurking |

**Sonic strategy**: Emphasize low end (dread) + clear dialogue midrange + high-frequency tension. Reduce mid-heavy instruments (no warmth, no comfort).

### Music Instrumentation (Don't Use)

❌ Piano (too intimate, hopeful)
❌ Strings with vibrato (too romantic)
❌ Bright synths (too modern, energetic)
❌ Percussion rhythms (too rhythmic, dance-like)
❌ Major keys (too happy)

### Music Instrumentation (DO Use)

✅ Sustained drones (pad, bowed cello, sine wave)
✅ Sub-bass pulses (felt more than heard, ~30–50 Hz)
✅ Tonal swells (slow fade-in/fade-out, no melody)
✅ Dissonant intervals (tritone, unresolved chords)
✅ Sparse, long-decay sounds (strings bowed slow, sustain pad)
✅ Metallic/industrial textures (distant bells, ring tones)
✅ Minor keys (unresolved, ominous)

---

## Output Format

### Audio Brief (Markdown)

```markdown
# AUDIO STRATEGY: Episode Title
**Tone** Gothic boarding-school thriller | **Tempo** Slow-burn dread
**Mix philosophy** Low drones + clear dialogue + strategic silence

---

## SCENE 1: COLD OPEN (00:00–00:10, 10s)

### Music Cue 1: "Panic Rising" (00:00–00:10, 10s)
- **Start**: 00:00 (with black frame)
- **Instrumentation**: Sub-bass pulse (30 Hz, heard as rhythm/heartbeat), sustained high drone (sine wave, 800 Hz)
- **Tempo**: ~90 BPM implied (heartbeat = urgency, not dance)
- **Intensity curve**: Start low (50% volume), crescendo to 100% at 00:10 (fade into title card)
- **Emotion**: Primal fear, adrenaline, hunted
- **Sync points**: Bass hits when protagonist glances back (fear spike); drone swells on ECU of eyes (terror maxed)
- **Fade out**: Music cuts to near-silence at 00:10 (shock), title card drops with sound (rewind sound effect: reversed/pitched)

### Foley Elements
| Sound | Timing | Source | Emotional Purpose |
|---|---|---|---|
| **Footsteps** | 00:02–00:10 (continuous) | Leaves/twigs crunching | Establishes location (forest), urgency (fast pace) |
| **Breath** | 00:02–00:10 (prominent in CU/ECU) | Heavy, labored breathing | Proximity to protagonist, panic state |
| **Wind** | 00:02–00:10 (ambient) | Pine branches, distant howl | Location, isolation, unseen danger |
| **Torch crackle** | 00:04, 00:08 (sparse) | Practical torch light (if visible) | Slight relief (light = hope), quickly lost |
| **Distant sound** | 00:06 (single hit) | Snapping branch behind her | Threat pursuing (makes her glance back) |

### Silence Strategy
- **None** — keep audio bed constant, no silence beats in cold open (silence = safety, here we want relentless dread)

### Dialogue
- **None** — no dialogue in cold open

### Continuity
- **Fade to title card**: Abrupt silence (shocking), then rewind sound effect (low-pitched whoosh, reversed), then title card music (tonal swell building).

---

## SCENE 7: GROUP ARGUMENT (01:07–01:27, 20s)

### Music Cue 2: "Fracture" (01:07–01:27, 20s)
- **Start**: 01:07 (establishing shot of group in fog)
- **Instrumentation**: Minimal sub-bass (very low, 40 Hz, almost inaudible), sustained unresolved drone (tritone interval), metallic high tone (ring/bell, sparse hits)
- **Tempo**: None (not rhythmic; tonal underscore)
- **Intensity curve**: Flat 60% volume (tension constant, not building; argument is internal, not external threat)
- **Emotion**: Conflict, doubt, fracture, watching
- **Sync points**: 
  - Metallic tone hits when char_08 speaks (accusatory, unsettling)
  - Sub-bass pulse slightly rises at char_01's nod (decision moment)
  - Drone swells at 01:18 when protagonist looks up (threat awareness)
- **Dialogue**: Music ducks under dialogue (~5 dB reduction; dialogue at -10 dB, music at -15 dB)
- **Silence beat**: 01:15–01:17 (2 seconds) — music OUT completely. Only foley (torch crackle, breathing, wind) and ambient. This silence = weight of her decision.
- **Fade**: Music slightly swells at 01:27 as scene transitions to next (building tension for next scene).

### Foley Elements
| Sound | Timing | Source | Emotional Purpose |
|---|---|---|---|
| **Footsteps** | 01:09, 01:15 (sparse, purposeful) | Gravel/boots on ground | Movement, intent, physicality |
| **Torch crackle** | 01:07–01:27 (continuous, background) | Practical torch fire | Warmth amid cold conflict, light = hope/confusion |
| **Breath** | 01:12, 01:20 (audible, tense) | Character breathing during silence/tension | Proximity, emotional state |
| **Fabric rustle** | 01:10, 01:16 (gestures) | Blazer, tie movement | Physical tension, gesture emphasis |
| **Wind in pines** | 01:07–01:27 (ambient, continuous) | Distant wind, branches | Location (forest), isolation, threat |
| **Rain drops** | 01:19 (sparse) | Single rain droplets | Shifting weather, approaching threat |

### Dialogue Sync
| Character | Timing | Dialogue | Audio Cue |
|---|---|---|---|
| char_06 | 01:10 | "We have to get out." | Music ducks 5 dB; dialogue clear at -10 dB; sub-bass hits under her conviction |
| char_08 | 01:13 | "That's crazy, we'll get caught." | Metallic tone hits; dialogue slightly higher pitch (anxiety); foley of his gestural movement |
| char_01 | 01:15–01:17 | (silence — internal debate) | Music completely OUT. Only foley + ambient. Heartbeat-like sub-bass reenters at 01:17 (decision made). |
| (Implied) | 01:18 | (nod, no words) | Drone swells; music volume rises 10 dB; confidence moment |

### Silence Strategy
- **01:15–01:17 (2s of silence)**: Protagonist's moment of decision. Strip all music. Leave only organic foley + ambient wind. This silence is **louder** than music.
- **Purpose**: Audience leans in (quiet forces attention). Silence = decision weight.

### Continuity
- **Torch light consistency**: Torch audio (crackle) stays in background at consistent level (torch hasn't moved).
- **Wind ambience**: Constant (location marker).
- **Transition**: At 01:27, music builds (tension for next scene); foley continues (group moves toward gate).

---

## SCENE 9: FINAL HOLD (01:23–01:31, 8s)

### Music Cue 3: "Watched" (01:23–01:31, 8s)
- **Start**: 01:23 (establishing her defiant stare)
- **Instrumentation**: Single sustained drone (cello bowed, long sustain), sub-bass pulse (60 Hz, felt), high sine wave (hovering, unresolved)
- **Tempo**: None (static, no change)
- **Intensity**: 70% (threat present, imminent; but this is hold, not climax)
- **Emotion**: Defiance amid threat, watched, trapped, unresolved
- **Sync points**: No sync — music is static throughout 8s
- **Dialogue**: None
- **Foley**: Minimal (breathing, distant ambience, rain)

### Foley Elements
| Sound | Timing | Source | Emotional Purpose |
|---|---|---|---|
| **Breath** | 01:24–01:27 (audible, controlled) | Protagonist's breathing (steady, not panicked) | She's in control despite being watched |
| **Rain on glass** | 01:25 (sparse) | Window rain (visible in frame) | Threat/isolation (rain = barrier) |
| **Wind** | 01:23–01:31 (ambient) | Distant wind, very quiet | Location (exterior), ongoing environment |
| **Footsteps** (others) | 01:29 (single step) | Behind-camera character movement | Reminder: not alone, classmates present |

### Silence Strategy
- **None** — hold is full of tension; silence would break power. Keep audio bed steady.

### Dialogue
- **None** — stare, no words. Defiance = silent.

### Continuity
- **Transition to black**: Music continues into darkness (unsettling), then hard cut to black at 01:31 (shock silence).
- **Audio emotional note**: The 8s hold should feel like *eternity* — sustained tones (drones, sub-bass) that feel like time is slowing down.

---

## AUDIO CONTINUITY ACROSS EPISODE

### Recurring Audio Elements (Motifs)

| Audio Motif | Function | Appearances |
|---|---|---|
| **Sub-bass pulse (30–60 Hz)** | Emotional heartbeat, dread anchor | Cold open, moments of threat, final hold |
| **Torch crackle (practical)** | Location marker, warmth amid darkness | Every outdoor/torch scene |
| **Wind in pines** | Location + isolation | Forest scenes, climactic moments |
| **Rain on glass** | Barrier, threat, isolation | Dorm scenes, threat moments |
| **Drone swell** | Emotional crescendo, revelation | Mystery object moment, threat reveal |
| **Silence beats (strategic)** | Decision weight, contemplation | Around protagonist's choices |

### Mix Hierarchy (Levels, Post-Production)

Suggested mix:
- **Dialogue**: -10 dB (clear, foreground)
- **Foley**: -13 dB (present, supporting)
- **Music**: -15 dB (ambient, underscore; except silence beats)
- **Ambient**: -18 dB (location texture, distant)

**During silence beats**: Foley + ambient rise to -10 dB (become foreground).

---

## Implementation Notes

### For Sound Designer
- Request musician to compose 3 main cues: "Panic Rising", "Fracture", "Watched"
- All underscore (no melody, no rhythm, no hooks)
- Sustain-based (drones, pads, bowed strings)
- Minor key or atonal (unresolved)
- Sub-bass emphasis (low end dread)

### For Foley Artist
- Prioritize: footsteps (location), breath (proximity), torch crackle (practical continuity), wind (location)
- Secondary: fabric rustle, rain, distant sounds
- Minimize: dialogue foley (breathing under dialogue can compete)

### For Dialogue Editor
- Dialogue sits at -10 dB (clear, foregrounded)
- Underscore ducks 5 dB when dialogue present
- Music OUT completely during silence beats (01:15–01:17, protagonist decision)

### For Composer
- 3 templates provided (Panic, Fracture, Watched)
- All use sub-bass (30–60 Hz) as emotional anchor
- All atonal or minor (no major chords, no warmth)
- All sustain-based (no rhythmic percussion, no tempo)
- Highest note ≤ 2 kHz (avoid presence/sibilance conflict with dialogue)

### For AI Audio Generation (Higgsfield, etc.)
- Provide frequency chart above
- Specify: "low drones, sub-bass hits, sparse high tones, no melody"
- Provide foley list (footsteps, breath, torch, wind)
- Silence beat timing: "2s of silence at 01:15–01:17 (dialogue + foley only)"
