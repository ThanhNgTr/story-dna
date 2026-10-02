# Story DNA: Complete Production Pipeline

**Your video production toolkit** — from concept to crew briefs, ready for video generation.

---

## Core Flow (main feature)

Generated skill = core. Everything else is optional.

| # | Step | Command | Frequency | Output |
|---|---|---|---|---|
| 1 | Analyze video list | `/analyze-videos --input <dir>` | Rare: project start / new viral idea | `dna.json` + `dna.md` |
| 2 | Create skill from DNA | `/skill-creator-from-dna --dna <dna.json> --name <slug>` (or `--update <slug>`) | Rare | `.claude/skills/write-story-<slug>/SKILL.md` |
| 3 | Write script | `/write-story-<slug> --topic ... --characters ... --sample <file>` | Per script | `script_v1.md` |
| 4 | Feedback, skill auto-updates | `/refine-skill <slug> --feedback "..."` | Loop | skill vN+1 + `script_vK+1.md` |
| 5 | Approve | `/refine-skill <slug> --approve` | Once | `final.md` |
| 6 | Prompt list (1-5s shots) | `/script-to-shotlist <final.md>` | Once | `prompts.json` + `prompts.md` |

Script session files: `data/scripts/<slug>/<session-id>/` (input, script_vK, iterations.json, final, prompts).

The 7-skill pipeline below starts from a script. In the core flow, feed it `final.md`
from step 5 instead of `/write-compelling-short-form` output.

---

## 📊 The Pipeline (7 Skills + Workflow)

```
┌─ Input: Video File OR Premise
│
├─ [1] /analyze-videos ──→ Extract narrative DNA (structure, pacing, tone, characters)
│       Output: dna.json + dna.md
│
├─ [2] /write-compelling-short-form ──→ Generate script from premise using DNA framework
│       Input: Premise + tone + target audience
│       Output: script.md (with timecodes, scenes, dialogue, camera notes)
│
├─ [3] /script-to-shotlist ──→ Break script into shots
│       Input: script.md
│       Output: shotlist.md + shotlist.json (scene-by-scene breakdown with timecodes)
│
├─ [4] /direct-video ──→ Scene-by-scene production guide
│       Input: shotlist.json
│       Output: production_guide.md + .json (director's intent, blocking, actor cues, lighting, sound sync, continuity)
│
├─ [5] /cinematographer-brief ──→ Camera language specifications
│       Input: production_guide.json
│       Output: cinematography_brief.md + .json (lens, aperture, movement, framing, DOF, color grading cues)
│
├─ [6] /sound-design-brief ──→ Audio strategy & music cues
│       Input: production_guide.json
│       Output: audio_brief.md + audio_cue_sheet.json (music, foley, dialogue sync, silence beats, ambient textures)
│
└─ [7] /production-design-brief ──→ Visual design & art direction
        Input: production_guide.json
        Output: design_brief.md + design_specifications.json (color grading, lighting setup, costumes, props, continuity)

Final Output: Complete production package
├── script.md (screenplay with timecodes)
├── shotlist.json (structured shot data)
├── production_guide.json (director reference)
├── cinematography_brief.json (camera specs)
├── audio_cue_sheet.json (music + foley)
└── design_specifications.json (visual design)

↓ Ready for: Higgsfield / human crew / video generation
```

---

## 🚀 Quick Start (3 Options)

### Option A: Video Reference (Full Analysis)

Start with a reference video to extract narrative DNA, then generate new script in that style.

```bash
# Step 1: Analyze reference video(s)
/analyze-videos --input data/analyses/ep1.mp4 --max-frames 45

# Step 2: Create compelling script from premise using that DNA framework
/write-compelling-short-form \
  --premise "A tech CEO discovers the AI they built is gaining consciousness" \
  --characters "Marcus (CEO), ARIA (AI voice), Dr. Chen (ethicist)" \
  --tone "sci-fi thriller, suspenseful"

# Step 3–7: Full pipeline (see below)
```

### Option B: DNA Direct (No Video Reference)

Skip video analysis, use the framework directly (Hollow Pine DNA already extracted).

```bash
# Use /write-compelling-short-form directly (works for ANY story)
/write-compelling-short-form \
  --premise "A security researcher discovers a backdoor in their company's new product" \
  --tone "tech thriller" \
  --length 90s
```

### Option C: Workflow (Automated Full Pipeline)

Run the entire workflow from premise to production briefs automatically.

```bash
# Coming soon: CLI runner or workflow invocation
# Full pipeline: Premise → Script → Shotlist → All 4 Crew Briefs
```

---

## 📝 Detailed Workflow (Step-by-Step)

### Step 1: Analyze Video (Optional)

Extract narrative DNA from reference video(s).

```
/analyze-videos --input data/analyses/
  Output: dna.json + dna.md
  Time: ~2–5 min per video
  Result: Structured narrative patterns (characters, pacing, tone, world rules, motifs)
```

**When to use**: You have reference videos and want to learn their style.

**Output files**:
- `data/analyses/<timestamp>/dna.json` — structured data (characters, pacing, tone, etc.)
- `data/analyses/<timestamp>/dna.md` — human-readable report

---

### Step 2: Generate Script

Create a script from your premise, using the DNA framework (Hollow Pine or custom).

```
/write-compelling-short-form \
  --premise "Your story idea" \
  --characters "Name (role), Name (role)..." \
  --tone "genre/mood" \
  --length 90s
  
  Output: script.md (with timecodes, scenes, dialogue, camera directions)
  Time: ~2 min
  Result: Markdown screenplay ready for breakdown
```

**Key features**:
- Beat structure from DNA (cold open → rewind → setup → mystery → conflict → peak → threat → cliffhanger)
- Sparse dialogue (max 12 lines per script)
- Character IDs instead of names (char_01, char_06, etc.)
- Motifs embedded (ring pendant, fog, lit window, etc.)
- Unresolved mysteries (drives viewer retention)

**Output file**:
- `data/scripts/generated/script_<TIMESTAMP>_v1.md`

---

### Step 3: Break into Shotlist

Convert script into shot-by-shot breakdown with timecodes.

```
/script-to-shotlist --input data/scripts/generated/script_<TIMESTAMP>_v1.md
  Output: shotlist.md + shotlist.json
  Time: ~1 min
  Result: Scene-by-scene breakdown with timecodes, shot sizes, camera directions
```

**Shotlist includes**:
- shot_id, timecode (00:00–00:10), duration (10s)
- scene_name, location (INT./EXT.)
- characters present, action, dialogue
- camera_direction (handheld, push-in, rack focus, locked-off)
- visual_description, mood

**Output files**:
- `data/scripts/generated/shotlist.md` (human-readable)
- `data/scripts/generated/shotlist.json` (structured, machine-readable)

---

### Step 4: Director's Guide

Generate scene-by-scene production guide with blocking, actor cues, lighting, sound sync.

```
/direct-video --shotlist data/scripts/generated/shotlist.json
  Output: production_guide.md + production_guide.json
  Time: ~2 min
  Result: Director-ready scene guide for crew briefing
```

**Production guide includes** (per scene):
- Director's intent (why this shot exists)
- Camera blocking (position, movement, framing, shot progression)
- Lighting setup (key, fill, practicals, mood)
- Actor direction (emotional arc, tells, physical vocabulary per character)
- Sound sync (foley, music cues, dialogue timing, silence beats)
- Continuity notes (wardrobe state, props, positioning carryover)

**Output files**:
- `data/scripts/generated/production_guide.md` (crew briefing format)
- `data/scripts/generated/production_guide.json` (structured data)

---

### Step 5: Cinematography Brief

Define camera language (lens, movement, framing, depth of field, color grading cues).

```
/cinematographer-brief --production-guide data/scripts/generated/production_guide.json
  Output: cinematography_brief.md + cinematography_brief.json
  Time: ~2 min
  Result: DOP-ready camera specs for all shots
```

**Cinematography brief includes** (per shot):
- Lens choice (24mm–135mm, f-stop)
- Movement language (static, push-in, handheld, rack focus, whip pan)
- Framing geometry (centered, rule of thirds, leading lines, negative space)
- Depth of field strategy (shallow vs. deep)
- Visual metaphors (how camera movement reflects emotion)
- Continuity markers (eye-line, light position, focal distance)
- Color grading cues (desaturation %, teal shift, warm/cool split)

**Output files**:
- `data/scripts/generated/cinematography_brief.md` (DOP reference)
- `data/scripts/generated/cinematography_brief.json` (machine-readable)

---

### Step 6: Sound Design Brief

Define audio strategy (music cues, foley, dialogue sync, silence beats, ambient textures).

```
/sound-design-brief --production-guide data/scripts/generated/production_guide.json
  Output: audio_brief.md + audio_cue_sheet.json
  Time: ~2 min
  Result: Sound designer & composer brief, music cue sheet
```

**Sound design brief includes** (per scene):
- Music cues (instrumentation, tempo, intensity, sync points)
- Foley elements (footsteps, breath, fabric, impacts with timing)
- Ambient textures (fog, wind, room tone, rain)
- Dialogue sync (timing, mix level, effects)
- Silence beats (strategic silence for emphasis, duration)
- Audio emotional arc (how sound mirrors visual mood)

**Music philosophy** (Hollow Pine style):
- Low drones + sub-bass (30–60 Hz, felt not heard)
- Sparse, sustain-based (no melody, no rhythm)
- Dissonant intervals (unresolved, ominous)
- No voiceover, dialogue clear

**Output files**:
- `data/scripts/generated/audio_brief.md` (sound designer reference)
- `data/scripts/generated/audio_cue_sheet.json` (composer cue list)

---

### Step 7: Production Design Brief

Define visual design (color grading, lighting, costumes, props, continuity).

```
/production-design-brief --production-guide data/scripts/generated/production_guide.json
  Output: design_brief.md + design_specifications.json
  Time: ~2 min
  Result: Production designer & color grader specs, costume evolution, prop tracking
```

**Production design brief includes** (per scene):
- Color palette (desaturation %, teal shift, warm practicals as only saturated)
- Lighting setup (key, fill, practicals, color temp K, intensity ratios)
- Set dressing (foreground, midground, background elements)
- Costume continuity (wardrobe evolution, damage progression, color significance)
- Prop continuity (where props appear, how they change, meaning evolution)
- Mood board (visual reference style)

**Visual philosophy** (Hollow Pine style):
- Desaturated (60–70% saturation)
- Practicals-only (torch 3200K warm, moonlight 5600K cool, window light 4500K neutral)
- High contrast (blacks 10 IRE, torch 95 IRE)
- Wardrobe as narrative (damage = emotional state)

**Output files**:
- `data/scripts/generated/design_brief.md` (production designer reference)
- `data/scripts/generated/design_specifications.json` (color grader LUT specs, continuity)

---

## 🎬 Complete Output Package

After running all 7 skills, you'll have:

```
data/scripts/generated/
├── script_<TIMESTAMP>_v1.md              (screenplay with timecodes + dialogue)
├── script_<TIMESTAMP>_v1.md.json         (structured script data)
├── shotlist.md                           (human-readable shot breakdown)
├── shotlist.json                         (structured shot data)
├── production_guide.md                   (director scene guide)
├── production_guide.json                 (structured director guide)
├── cinematography_brief.md               (camera language for DOP)
├── cinematography_brief.json             (structured camera specs)
├── audio_brief.md                        (sound designer reference)
├── audio_cue_sheet.json                  (composer cue list + music specs)
├── design_brief.md                       (production designer reference)
└── design_specifications.json            (color grading LUT, costume evolution, prop tracking)
```

**Total production time**: ~15 minutes (automated)

---

## 📤 Next Step: Video Generation

### For Higgsfield (AI Video Generation)

1. **Convert JSON specs to Higgsfield prompts**:
   ```
   Scene 1 (00:00–00:10): "EXT. FOREST — NIGHT. Protagonist running in terror.
   Handheld push-in, MS → CU → ECU. Torch glow (3200K, practicals only). 
   Fog volumetric, desaturated teal palette. Footsteps + heavy breathing foley.
   Sub-bass 30 Hz pulse. Duration 10s."
   ```

2. **Use cinematography_brief.json**:
   - Lens: 35mm → 50mm → 85mm (escalating push-in)
   - Aperture: f/2.8 → f/1.8 → f/2.0 (shallow DOF)
   - Movement: Handheld, 1–2 frame advance/second

3. **Use audio_cue_sheet.json**:
   - Music: "Panic Rising" cue (0–10s)
   - Foley: Footsteps (continuous), breath (prominent in CU/ECU), wind (ambient)
   - Sync: Bass hit at glance-back moment

4. **Use design_specifications.json**:
   - Color: Desaturated teal shadows, warm amber torch (only saturated)
   - Lighting: Torch glow through fog (volumetric haze)
   - Costume: Navy blazer (torn, wet), white shirt (muddied), pendant clutched

### For Human Crew

1. **Director** reads `production_guide.md` → understands intent, blocking, pacing
2. **Cinematographer** reads `cinematography_brief.md` → knows lens, movement, framing
3. **Sound Designer** reads `audio_brief.md` → knows music, foley, silence beats
4. **Production Designer** reads `design_brief.md` → knows colors, lighting, costumes
5. **Color Grader** uses `design_specifications.json` LUT specs
6. **Composer** uses `audio_cue_sheet.json` for music cues

All briefs are **self-contained** — no need for script re-reads or meetings.

---

## 🔧 Refine & Iterate (human in the loop)

Works on generated `write-story-<slug>` skills (see Core Flow).

```
/refine-skill <slug> --feedback "tone too formal, need more dread"
  -> skill v2 (v1 kept in versions/SKILL_v1.md), script v2 on same input
/refine-skill <slug> --feedback "..."      # repeat
/refine-skill <slug> --approve             # final.md, skill marked stable
```

Feedback for one story only (e.g. "rename the dog") edits the script, not the skill.
History: `data/scripts/<slug>/<session-id>/iterations.json`.

---

## 📋 Skills at a Glance

| Skill | Input | Output | Time | Purpose |
|---|---|---|---|---|
| **analyze-videos** | Video file(s) | dna.json + dna.md | 2–5 min | Extract narrative framework from reference videos |
| **write-compelling-short-form** | Premise + characters + tone | script.md | 2 min | Generate screenplay using DNA or learned framework |
| **script-to-shotlist** | script.md | shotlist.md + .json | 1 min | Break script into shots with timecodes |
| **direct-video** | shotlist.json | production_guide.md + .json | 2 min | Scene-by-scene director guide + blocking |
| **cinematographer-brief** | production_guide.json | cinematography_brief.md + .json | 2 min | Camera language (lens, movement, framing) |
| **sound-design-brief** | production_guide.json | audio_brief.md + audio_cue_sheet.json | 2 min | Audio strategy (music, foley, dialogue sync) |
| **production-design-brief** | production_guide.json | design_brief.md + design_specifications.json | 2 min | Visual design (color, lighting, costumes, props) |

**Total pipeline: ~15 minutes end-to-end**

---

## 💡 Tips & Tricks

### 1. Reuse DNA Across Multiple Scripts

Analyze one video series → extract DNA → generate 3+ scripts in that style.

```bash
# Analyze ep1 + ep2
/analyze-videos --input data/analyses/

# Get DNA (already done)

# Write 3 different stories in Hollow Pine style
/write-compelling-short-form --premise "Story 1"
/write-compelling-short-form --premise "Story 2"
/write-compelling-short-form --premise "Story 3"

# All use the same DNA framework (consistent style across scripts)
```

### 2. Create Custom Frameworks

Generate new DNA from your own reference videos.

```bash
/analyze-videos --input my_videos/comedy_sketches/

# Now write scripts that match that tone/pacing
/write-compelling-short-form --premise "..." --tone "comedic"
```

### 3. Parallel Crew Briefing

All briefs are independent. Give them out simultaneously:

```bash
# Day 1: Run full pipeline
/analyze-videos → /write-compelling-short-form → /script-to-shotlist → /direct-video
  + /cinematographer-brief
  + /sound-design-brief
  + /production-design-brief

# Day 2: Crew reads their briefs
Director: production_guide.md
Cinematographer: cinematography_brief.md
Sound Designer: audio_brief.md
Production Designer: design_brief.md

# Day 3: Shoot or generate video (all briefed, no delays)
```

### 4. Version Control

Each skill outputs v1, v2, v3...

```bash
script_20261001_v1.md (initial)
script_20261001_v2.md (after feedback: "add more tension")
script_20261001_v3.md (after feedback: "tone down the horror")
```

Keep iteration history for retrospectives.

---

## ⚠️ Common Gotchas

### Script Doesn't Follow Beat Map?

The `/write-compelling-short-form` skill applies the DNA beat structure. If output doesn't match expected pacing, use `/refine-skill` to tighten structure rules.

### Crew Briefs Don't Align?

All briefs derive from the same `production_guide.json`. If conflicts appear (cinematographer says "static" but director says "push-in"), re-run `/direct-video` with clearer notes.

### Color Grading LUT Specs Missing?

The `design_specifications.json` includes detailed curves + LUT settings. Share this file directly with your color grader (Blackmagic DaVinci Resolve, etc.).

### Timecodes Not Matching?

Ensure `shotlist.json` timecodes match script timecodes. If they drift, re-run `/script-to-shotlist`.

---

## 🎯 Success Metrics

**Your pipeline is working when**:

✅ Script follows the 90s beat structure (cold open 2–10s, peak ~73%, hold 8s)
✅ Shotlist has no gaps (end of shot 1 = start of shot 2)
✅ Production guide's lighting matches cinematographer brief's camera setup
✅ Sound design brief syncs to director guide's pacing
✅ Design brief's costume progression matches script's emotional arc
✅ All outputs are crew-ready (no jargon, clear specs, actionable)

---

## 📚 Files & References

- **Video analysis**: `data/analyses/20261001-075639/dna.md` (Hollow Pine example)
- **Narrative framework**: `.claude/skills/write-compelling-short-form/SKILL.md` (complete beat map + rules)
- **Production pipeline**: This file (PRODUCTION_PIPELINE.md)

---

## 🚀 Start Now

```bash
# Option 1: Simple premise
/write-compelling-short-form \
  --premise "A girl discovers her AI is alive" \
  --characters "Maya (developer, 28), ARIA (AI voice)" \
  --tone "sci-fi thriller"

# Option 2: Full pipeline (with video reference)
/analyze-videos --input my_videos/
/write-compelling-short-form --premise "..."
/script-to-shotlist ...
/direct-video ...
/cinematographer-brief ...
/sound-design-brief ...
/production-design-brief ...

# Option 3: Workflow (when available)
# workflow: story-dna-complete-pipeline
```

**Questions?** Check the individual skill files in `.claude/skills/` — each has detailed examples and generation rules.

Good luck! 🎬
