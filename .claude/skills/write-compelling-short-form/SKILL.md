---
name: write-compelling-short-form
description: |
  Generate compelling, viral short-form scripts (90s, 9:16 vertical) using a framework
  learned from professional reference videos. Input your premise, characters, and core
  conflict — the skill applies proven pacing, character, tone, and structural patterns
  to create engaging narratives that hook viewers. Works for any genre or subject.
  Triggers on: "write compelling script", "viral short-form", "write story", 
  "create script", "compelling script template".
---

# Write Compelling Short-Form Scripts

DNA source: `data/analyses/20261001-075639/dna.json` (trained on professional 90s vertical thriller)

## When to Use

Use this skill when you have:
- A premise, concept, or story idea (any genre)
- Characters or character roles
- A target tone (dramatic, comedic, educational, etc.)
- Target length (default 90s)

**Do NOT use for**: Continuing or sequeling a specific series (each story stands alone)

## Quick Start

```
/write-compelling-short-form \
  --premise "A tech CEO discovers the AI they built is gaining consciousness" \
  --characters "Marcus (CEO, 40s, driven), ARIA (AI voice, unseen), Dr. Chen (ethics researcher)" \
  --tone "sci-fi thriller, suspenseful" \
  --length 90s
```

Output: Markdown script with timecodes, scenes, dialogue, camera directions.

## Input Format

```
--premise "Your story idea (2–3 sentences)"
--characters "Name (role, age, defining trait), Name (role, trait)..."
--tone "Genre/mood (e.g., gothic horror, comedic, educational mystery)"
--length 90s              # default; adjust to 60s, 120s as needed
--aspect-ratio 9:16      # default vertical; can override to 16:9
```

## How It Works

This skill is a **framework**, not a series generator. It uses proven narrative patterns learned from professional reference videos to structure *any* story:

### Story Structure (beat map)

| Time | Beat | Duration |
|---|---|---|
| 0–2s | Black / sound hook | 2s |
| 2–10s | Cold open (high tension, no dialogue) | 8s |
| 10–12s | Title + time-jump rewind | 2s |
| 12–22s | Setup (calm, exposition via objects/environment) | 10s |
| 22–38s | Authority / world rules (introduce stakes) | 16s |
| 38–47s | Mystery object (hook, key question) | 9s |
| 47–57s | Inciting incident (night scene, rule-break, change) | 10s |
| 57–67s | Conflict (group argument, fast cuts, tension) | 10s |
| 67–73s | Emotional peak (~73%) (character breaks, stakes clear) | 6s |
| 73–83s | Watching / held moment (watcher reveals, tension) | 10s |
| 83–91s | Final hold (1 locked-off shot, defiant stare, cliffhanger) | 8s |

### Pacing Rules

- **Average shot**: 3–4 seconds
- **Action/conflict scenes**: 1–2 second cuts, handheld camera
- **Slow burns**: 4–6 second static, symmetrical framing
- **Final hold**: 8 seconds minimum (locked-off, centered, no cuts)
- **Transitions**: hard cuts + one fade-to-black + title card with rewind icon

### Tone & Voice

- Cinematic, restrained, serious
- No jokes, no pop-culture references, no meta-commentary
- Energy curve: high start → slow dread → confrontation → tense hold
- Dialogue is sparse (max ~12 lines per script)
- Show, don't tell (exposition through objects, environment, what's *not* said)

### Character Arc Template

1. **Protagonist** (~70% screen time)
   - Starts in physical or emotional distress
   - Guarded, watches before acting
   - Has a tell/fidget under stress (gesture, object clutching)
   - Emotional peak at ~73%: breaks, grieves, or defies
   - Ends on defiant stare (cliffhanger)

2. **Ally/Protector** (~15–20% screen time)
   - Calm, direct, says what protagonist won't
   - Appears in peak moment to comfort or betray
   - Ambiguous loyalty (unclear if savior or threat)

3. **Antagonist/Authority** (~10–15% screen time)
   - Controlled, formal, never raises voice
   - Embodies rules/stakes
   - Appears in setup + conflict, ambiguous in ending

4. **Agitator/Sceptic** (~5–10% screen time)
   - Drives conflict, talks fast, accusatory
   - Represents doubt or action

### Visual Style

- **Palette**: Desaturated cool tones (teals, blues, greys) with warm practicals (amber, gold lights) as sole contrast
- **Lighting**: Low-key, moonlit, volumetric haze, rim light from windows/practicals
- **Camera**: Mostly static and symmetrical, slow push-ins, rack focus; handheld/whip pan only in action
- **Framing**: Face centered for 9:16; wide shots for establishing; ECU for tension
- **Transitions**: Hard cuts, fade-to-black for night scenes, rewind icon over B&W still

### Motif Reuse

Pick 2–3 motifs and repeat them throughout (builds audience memory):

- Object clutched under stress (pendant, ring, letter)
- Scratched/damaged surface with text
- Fog, rain, or environmental darkness
- Lit window with watching silhouette
- Gripped arms / physical restraint
- Rewind / time-jump device

### Open Questions (Cliffhanger)

End on **at least two unresolved questions** that point back to the cold open:
- Who is the watcher?
- What do the rules really mean?
- Are allies actually protectors?
- What happens next?

## Script Output Format

```markdown
# SCRIPT TITLE: <User's Title>
**Format** 9:16 · **Length** ~90s · **Premise** <user premise>

## COLD OPEN (0–10s)
**[00:00–00:02] BLACK.** <sound description>
**[00:02–00:10] EXT. <PLACE> — NIGHT**
VISUAL: <character + action>, MS → CU → ECU
SOUND: <ambient, music, foley>
(no dialogue)

## TITLE (10–12s)
**[00:10–00:12] TITLE CARD** — rewind icon, B&W still, time-jump super.

## SCENE NAME (12–22s)
**[00:12–00:22] INT./EXT. <PLACE> — <TIME>**
VISUAL: <characters, what they do, shot progression>
ACTION: <what happens>
CHAR_A: "dialogue"
CHAR_B: "dialogue"
CAMERA: <movement, focus, angle>
SOUND: <music, ambient, foley>

... (continue per beat map)

## FINAL HOLD (83–91s)
**[01:23–01:31]** Single locked-off, centered, frontal shot (8s). <Character> stares to camera, defiant. Hard cut to black.

## Continuity Checklist
- World rules used: [list 2–3]
- Questions advanced: [which mysteries moved forward?]
- Questions left open: [minimum 2 unresolved]
- Motifs reused: [which 2–3?]
```

## Generation Rules

1. **Premise drives plot; framework drives structure.** If conflict arises, keep the beat map + pacing, adapt premise details.
2. **Every scene has timecode, VISUAL, SOUND.** No exceptions.
3. **Show, don't tell.** Objects, environment, silence, and what's *not* explained carry meaning.
4. **Reuse motifs** (at least 2). Repeat character tells (pendant clutch, ring flip, etc.) at emotional peak.
5. **End on a cliffhanger:** 8s hold, centered, defiant or haunted stare. Hard cut to black. Never resolve the main mystery.
6. **Dialogue is sparse.** Max 12 lines. Max 2 sentences per line.
7. **No names on screen except one key figure.** Use roles or silhouettes (char_A, char_B, etc.) in descriptions.

## Examples

### Example 1: Tech Thriller
**Premise**: A security researcher discovers a backdoor in their company's new product during a live demo.

**Structure applied**:
- Cold open: Demo glitching, frames freezing, fear
- Rewind: 48 hours earlier, calm office arrival
- Setup: Colleague hands her the laptop, warns her to "check the code"
- Mystery object: Sticky note with "LOOK DEEPER" under the keyboard
- Conflict: She accuses the VP, he denies, others dismiss her
- Peak: She realizes her own code is the backdoor
- Hold: She faces the camera, unblinking, as security enters behind her

### Example 2: Historical Drama
**Premise**: A museum curator realizes a newly acquired painting is a forgery — and who forged it.

**Structure applied**:
- Cold open: Painting falls from wall, glass shatters
- Rewind: Morning, she receives the painting, signs the provenance
- Setup: Alone in the restoration lab, studying brushstrokes
- Mystery object: Hidden signature under varnish
- Conflict: Expert claims it's genuine, insurance broker claims it's fake, curator torn
- Peak: She understands the artist is someone she knows
- Hold: She looks at an old photo on her desk, then to camera, conflicted

## Advanced: Adapt for Your Genre

**Comedy** (90s vertical sitcom):
- Same structure, but lighter tone, faster cuts in conflict (slapstick, quick quips)
- Peak: Character laughs instead of weeps
- Motifs: recurring gag, physical comedy callback

**Educational** (90s vertical explainer):
- Same structure: hook → setup → mystery object (key concept) → conflict (misconception) → peak (aha moment) → hold (remember this)
- Tone: enthusiastic, energetic, clear
- Dialogue: more frequent (~20 lines), direct address

**Action** (90s vertical fight scene):
- Cold open: combat, full energy
- Setup: why they're fighting
- Conflict: escalating choreography
- Peak: turning point in the fight
- Hold: opponent down, hero breathing, defiant

## Notes

- This skill applies patterns learned from **one professional reference video**. If you want it tuned for your specific genre or audience, provide feedback on generated scripts and I can refine the framework.
- Aspect ratio defaults to 9:16 (mobile vertical); override with `--aspect-ratio 16:9` for horizontal.
- No character names are shown on screen *except one key figure* (like "ELI" in the training video). Use roles in dialogue.
- This is not episodic — each script is standalone. To write a sequel, use the skill again with the new premise.

## Save & Version

Script files are saved to `data/scripts/generated/script_<TIMESTAMP>_v1.md`. Iterations become `_v2`, `_v3`, etc. Always request feedback before committing to video production.
