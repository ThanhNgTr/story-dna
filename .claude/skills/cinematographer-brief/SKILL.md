---
name: cinematographer-brief
description: |
  Generate camera language specifications from a production guide. Defines lens
  choices, movement language (pan, push-in, rack focus, handheld), framing
  geometry, and visual storytelling techniques per scene. Outputs detailed
  cinematography brief ready for DOP (director of photography) briefing or
  AI video generation. Triggers on: "cinematography", "camera language",
  "lens choice", "visual language", "camera specs".
---

# Cinematographer Brief: Camera Language Specification

## When to Use

Use this skill after `/direct-video` to generate:
- Lens + aperture specifications per shot
- Camera movement language (pan, push-in, rack focus, handheld vs. locked-off)
- Framing geometry (rule of thirds, centered, symmetrical, asymmetrical)
- Depth of field strategy (shallow vs. deep focus)
- Color grading cues (desaturated, warm/cool contrast)
- Visual metaphors (how camera movement reflects emotion)

**Input**: `production_guide.json` (from `/direct-video`)
**Output**: `cinematography_brief.md` + `cinematography_brief.json`

## Quick Start

```
/cinematographer-brief --production-guide data/scripts/generated/production_guide.json \
  --visual-style "desaturated teal + warm amber practicals" \
  --aspect-ratio "9:16"
```

## How It Works

### Camera Movement Language

The skill defines a vocabulary for *how* camera moves to *reflect emotion*:

| Movement | Emotional Meaning | Use Case |
|---|---|---|
| **Static, locked-off** | Control, authority, observation | Authority figures, cliffhangers, tense holds |
| **Slow push-in** | Emotional intensity, intimacy, dread | Close-ups, emotional peaks, threat revelation |
| **Handheld, jerky** | Chaos, adrenaline, danger | Chases, arguments, panic |
| **Rack focus** | Shifting attention, revelation | Noticing something new, emotional shift |
| **Whip pan** | Surprise, confusion, transition | Quick cuts between speakers, sudden threat |
| **Creep/slow pull back** | Isolation, helplessness, overwhelm | Character alone in space, realization of doom |

### Lens Philosophy

For 9:16 vertical:
- **Wide lens (24–35mm)**: Immersive, environmental, shows context
- **Standard lens (35–50mm)**: Neutral, natural eye-view, conversation
- **Telephoto (85–135mm)**: Compressed, intimate, isolating

**Vertical aspect ratio rule**: Favor longer lenses (85mm+) to compress space and keep face large.

### Framing Geometry

| Geometry | Emotional Effect | Use |
|---|---|---|
| **Centered, symmetrical** | Control, power, authority, strangeness | Headmaster, protagonist defiant, unsettling moments |
| **Rule of thirds, off-center** | Natural, observational, vulnerable | Conversation, fear, exploration |
| **Leading lines** | Direction, purpose, movement | Protagonist moving toward/away from threat |
| **Negative space** | Isolation, loneliness, smallness | Protagonist alone in large space, dwarfed |
| **Layered depth** | World-building, multiple threats | Characters in foreground, threat in background |

---

## Output Format

### Cinematography Brief (Markdown)

```markdown
# CINEMATOGRAPHY BRIEF: Episode Title
**Format** 9:16 vertical · **Visual language** Desaturated + warm practicals

## CAMERA PHILOSOPHY

### Primary Language
- **Static + Slow**: 70% of shots locked-off or slow push-in (premium, controlled, cinematic)
- **Handheld**: 20% during action/chaos (chases, arguments)
- **Locked Hold**: 10% for cliffhangers and emotional peaks (8s final hold)

### Aspect Ratio Strategy
9:16 is vertical-native (mobile). Favor **centered framing** and **face-large composition**:
- Face should occupy 50–70% of frame in close-ups
- Headroom: minimal (eyebrows near top of frame)
- Wide shots: use negative space above/below to show isolation

### Color Grading / LUT
- **Desaturation**: Reduce saturation to 60–70% (moody, sophisticated)
- **Teal shift**: Cool shadows (blue-green tint)
- **Warm practicals**: Torch, window lights isolated at 100% saturation (only warm element)
- **Contrast**: Lift shadows to 70 IRE (clean blacks), lower mids (moody)

---

## SCENE 1: COLD OPEN (00:00–00:10, 10s)

### Lens Strategy
- **Shot 1 (MS)**: 35mm, f/2.8 (shallow depth of field, blur background)
- **Shot 2 (CU)**: 50mm, f/1.8 (tighter, more intimate)
- **Shot 3 (ECU)**: 85mm, f/2.0 (compressed, isolated)

**Rationale**: Longer lenses for 9:16 keep face large while moving frame into tighter shots.

### Movement Language
- **MS**: Static, locked-off camera (observation point). Allow protagonist to move within frame (running toward/past camera).
- **CU**: Slow push-in (1–2 frame advance per second). Push-in mirrors her acceleration/panic.
- **ECU**: Locked push-in hold on eyes/face. No further movement. Intensity maxed.

### Framing Geometry
- **MS**: Protagonist off-center (left), leaving space in frame (running toward right edge). Negative space = sense of flight.
- **CU**: Center protagonist face. Tighter frame, no negative space (trapped feeling).
- **ECU**: Centered on eyes. Fill frame with face. Claustrophobic, intimate terror.

### Depth of Field
- **MS**: f/2.8, soft background. Foreground (fog) and protagonist sharp; pines blurred (context but not distraction).
- **CU**: f/1.8, shallower. Protagonist sharp; everything else bokeh (isolation).
- **ECU**: f/2.0, still shallow. Eyes razor-sharp; cheekbones/lips soft (focus hierarchy).

### Visual Metaphors
- **Push-in = escalation**: As we move from MS → CU → ECU, we move from "watching" to "inside her fear."
- **Fog = obscurity**: Fog occluding frame edges suggests danger beyond frame.
- **Torch glow (practicals)**: Only warm element; draws eye, shows path/escape.

---

## SCENE 7: GROUP ARGUMENT (01:07–01:27, 20s)

### Lens Strategy
- **Wide shots (establishing)**: 24mm, f/5.6 (deep focus, all characters in focus)
- **Medium shots (conversation)**: 35mm, f/2.8 (shallow, character isolation in a group)
- **Close-ups (speaker)**: 85mm, f/2.0 (compressed, face-large)
- **Reaction shots**: 50mm, f/2.2 (neutral, supporting)

**Rationale**: Variety in lens choice mirrors emotional chaos. Start wide (group unity), move tight (individual conflict), end on protagonist (her decision).

### Movement Language
- **Establishing**: Locked-off, static. Camera holds group formation (shows spatial relationships).
- **During dialogue**: Handheld, gentle pan between speakers. Light shake (organic, urgent). No jerky cuts, smooth pans.
- **Reaction shots**: Subtle handheld drift; let camera "breathe" (character breathing, camera breathing).
- **Protagonist shot**: Slow rack focus (from char_06 to protagonist) when she nods. Focus = attention shift (audience follows).

### Framing Geometry
- **Establishing**: Symmetrical, group in center. Characters roughly equal distance apart (stability).
- **Argument escalates**: Asymmetrical. Char_06 on one side, char_08 opposite. Protagonist between (visual conflict).
- **Char_06 close-up (speaking)**: Centered, confident. Positive space in front (direction of intent).
- **Char_08 close-up (arguing)**: Off-center, slightly lower in frame (subordinate, defensive).
- **Protagonist close-up (reaction)**: Centered, level eye-line. Neutral observation (she judges, not participates).

### Depth of Field
- **Establishing**: f/5.6, deep focus. All characters in focus (group dynamics, no one singled out).
- **Individual close-ups**: f/2.0–f/2.8, shallow. Speaker in focus; group blurred behind (psychological isolation within group).
- **Protagonist**: f/2.0, shallower still. She's isolated even when surrounded.

### Camera Sync to Dialogue
- **Char_06 speaks (01:10)**: Cut to her close-up, 85mm. Camera centered on confidence.
- **Char_08 rebuttal (01:13)**: Pan (handheld) to him, 85mm. Slightly jerky pan (his anxiety).
- **Silence (01:15–01:17)**: Hold on protagonist's face, gentle creep/push-in. Rack focus from char_06 (background) to her (focus). Emphasize her decision weight.
- **Protagonist nods (01:18)**: Quick rack focus back to char_06 (accepting her ally), then slow focus pull to window background (threat awareness). Reveals depth: ally in focus, threat in soft focus behind.

### Color Grading Cues
- **Torch light**: Isolated at 100% saturation (warm amber, ONLY color in scene)
- **Fog**: Diffused, neutral (reduces color information, increases contrast)
- **Faces**: Slight teal rim light (cool moonlight), warm front light (torch)
- **Contrast**: High contrast between torches (bright) and fog shadow (dark). Middle tones reduced (moody).

### Continuity Across Shots
- **Eye-line consistency**: When char_06 speaks to protagonist, camera height and angle match protagonist's sight-line (allow viewer to "see through her eyes").
- **Light consistency**: Torch positions stable across cuts (character A always front-lit by torch B).
- **Focal distance**: Protagonist stays roughly in-frame center across reaction shots (steady reference point).

---

## CAMERA RULES (Apply to All Shots)

1. **Vertical priority**: Face and action stay centered/top-heavy (9:16 mobile framing).
2. **Shallow depth of field preference**: Keep background soft; focus draws to primary subject.
3. **No unmotivated movement**: Every camera move reflects emotional/narrative purpose.
4. **Practicals only**: No key light from above; only torch, window, moonlight (practicals on-scene).
5. **Handheld = chaos; locked-off = control**: Use movement language to mirror emotion.
6. **Rack focus = revelation**: When protagonist realizes something, rack focus to emphasize attention shift.
7. **Symmetry = authority/uncanniness**: Headmaster and threat (window watcher) in symmetrical frames (powerful or eerie).
8. **Asymmetry = vulnerability**: Protagonist often off-center (vulnerable, observed).
9. **Foreground elements**: Fog, pines, architectural elements (bars, windows) in soft focus foreground; protagonist sharp behind. Creates layered depth.
10. **Final 8s hold**: Locked-off, centered, locked focus. No drift. Maximum intensity through stillness.

---

## Lens Kit (Recommended for Shoot/AI Generation)

| Focal Length | Primary Use | F-Stop Range |
|---|---|---|
| 24mm | Establishing, environmental | f/5.6–f/8.0 |
| 35mm | Medium, versatile | f/2.8–f/4.0 |
| 50mm | Conversation, neutral | f/2.2–f/4.0 |
| 85mm | Close-ups, isolation | f/1.8–f/2.8 |
| 135mm | Extreme close-up, compressed | f/2.0–f/2.8 |

**Vertical 9:16 note**: Avoid ultra-wide (14–20mm) as they distort faces in vertical frame. Stick to 24mm minimum.

---

## Movement Language Cheat Sheet

```
TERROR/PANIC → Handheld push-in (1–2 frame advance/sec) + shallow DOF
AUTHORITY → Static locked-off, symmetrical framing, deep focus
REALIZATION → Rack focus (shift attention to new element)
ISOLATION → Creep backward (reveal negative space), shallow DOF, off-center
INTIMACY → Slow push-in, f/1.8, centered, close-up
THREAT REVEAL → Whip pan or quick cut + push-in on threat
CLIFFHANGER → 8s static hold, locked focus, centered, defiant stare
```

---

## Implementation Notes

- **For human shoot**: Provide lens list + movement language to DOP. They interpret into blocking.
- **For AI video generation**: Use lens + f-stop in prompts (e.g., "85mm, f/2.0, slow push-in")
- **For editing**: Movement language guides cut rhythm (handheld = fast cuts; locked-off = slower pacing)
