---
name: write-story-hollow-pine
description: |
  Write a new episode script for the vertical (9:16) short-form series HOLLOW PINE,
  a gothic boarding-school supernatural thriller. Follows the series DNA extracted
  from ep1: cold-open terror, "48 HOURS EARLIER" rewind, exposition by objects
  (locked gate, phone crate, RULES board), one scratched-message mystery object,
  night sneak-out, group argument in fog, tearful peak at ~73%, 8s locked-hold
  cliffhanger. Triggers on: "write hollow pine episode", "hollow pine script",
  "write-story-hollow-pine". Input: episode number + premise/brief (+ optional
  characters, length). Output: Markdown script with timecodes, scenes, dialogue,
  camera and sound, saved to data/scripts/hollow-pine/.
---

# HOLLOW PINE — Episode Script Generator (v1)

DNA source: `data/analyses/20261001-075639/dna.json` (1 episode analysed). Read it if you need more detail than this file.

## Input

```
/write-story-hollow-pine --episode 2 \
  --premise "Who is Eli? The girl finds his old dorm room." \
  --length 90s            # default 90s (ep1 = 91.3s)
  --characters "..."      # optional: add/rename; never contradict visual signatures below
```

The user's premise is the plot. Everything else (structure, tone, pacing, look) must match the DNA below.

## Output

Write `data/scripts/hollow-pine/ep<N>_v1.md` (bump to `_v2`, `_v3`… if the file exists — never overwrite). Return the script in the reply too.

## Series bible (from DNA)

**World rules** (established in ep1 — keep consistent, do not break without a reason in-story):
1. Students arrive by yellow school bus to a padlocked wrought-iron gate in a fog-choked pine forest. Something claws at the gate from outside (scratch marks).
2. Phones are confiscated at the gate into a wooden slatted crate.
3. Uniform: navy blazer with gold shield crest, white shirt, navy tie, grey skirt/trousers.
4. The headmaster carries a cane and reads from a numbered RULES board (≥9 rules). Rule text stays partial/unreadable on screen.
5. Students sneak out at night over the courtyard chain-link fence.
6. A missing student, ELI, is memorialised in a cracked sepia portrait scratched "STILL HERE".
7. No phones, no outside contact, no humour.

**Characters** (IDs from DNA — keep visual signatures verbatim in VISUAL lines so downstream video prompts stay consistent):

| ID | Role | Visual signature | Tell / voice |
|---|---|---|---|
| char_01 | Protagonist, new girl | Girl 16–17, centre-parted shoulder-length dark brown hair, grey-green eyes, pale freckled skin, small mole on right cheek; navy blazer with gold shield crest, white shirt, navy tie, grey pleated skirt; silver chain with small ring pendant; silver ring with grey-green stone on right hand | Clutches the pendant when afraid, grieving or defiant. Few words. Watches before she speaks. |
| char_06 | Ally / protector | Black boy 17–18, cropped black hair with line-up, dark brown eyes; navy blazer, gold buttons, navy-and-white striped tie | Calm, direct, protective. Says what others won't. |
| char_07 | Roommate / anxious friend | Girl 16–17, long wavy copper-red hair, many freckles, green-blue eyes; navy sweatshirt in dorm scenes | Whispers, urgent, frightened but loyal. |
| char_03 | Headmaster | Man 65–75, slicked-back silver hair, round wire-rim glasses, black shawl-collar cardigan, curved-handle wooden cane | Slow, formal, never raises his voice. Speaks in rules. |
| char_04 | Teacher / assistant | Man 40–50, thin, gaunt, round tortoiseshell glasses, brown sweater vest and tie; flips a small metal ring/coin | Detached, faintly amused. Unsettling smile. |
| char_02 | Gatekeeper | Man 40–50, heavy build, khaki canvas work jacket, carries the wooden phone crate | One-word orders. |
| char_05 | ELI (missing) | Sepia portrait: teen boy, wavy side-swept hair, high collar, bow tie; cracked glass, brass nameplate "ELI", frame scratched "STILL HERE" | Absent presence. Appears only as object, trace, or rumour. |
| char_08 | Student agitator | Boy 17, tousled light-brown hair, round glasses, dark teal V-neck sweater | Accusatory, talks fast. |
| char_09 | Student sceptic | Boy 17–18, slicked-back blond hair, light blue eyes, navy varsity bomber | Dismissive, argumentative. |
| char_10 / char_11 | Classmates who grip char_01's arms in ep1's final shot | Boy: dark curly hair, navy vest with yellow trim. Girl: long wavy dark-blonde hair, same vest | Ambiguous — captors or protectors. Resolve or deepen, don't ignore. |
| char_12 | Watcher in the lit window | Adult male silhouette, no face | Never fully shown. |

No names are shown on screen except ELI. You may give characters names in dialogue, but keep the IDs in VISUAL lines.

**Open questions from ep1** (pick at least one to advance, leave at least two open):
- Who is Eli, what does "STILL HERE" mean?
- Who watches from the lit window?
- Are char_10/char_11 captors or protectors?
- What do the RULES actually say?
- What links char_01's ring pendant to char_04's ring/coin?

## Episode structure (beat map — timecodes for 90s; scale proportionally)

| Time | Beat | Rule |
|---|---|---|
| 0–2s | Black | Always start on black. |
| 2–10s | COLD OPEN — protagonist in physical terror | Running / hiding / fleeing. Escalate MS → CU → ECU. No dialogue. No title yet. |
| 10–12s | TITLE CARD | `HOLLOW PINE` + time-jump super in the "48 HOURS EARLIER" style (vary the number). Rewind icon over a B&W still of the next scene. |
| 12–22s | ARRIVAL / CALM | The protagonist calm and guarded. Exposition by objects, not speech. |
| 22–38s | AUTHORITY | An adult (headmaster / char_04 / gatekeeper) and an institutional space. Rules partial. |
| 38–47s | MYSTERY OBJECT | One scratched/damaged object with a short message. Protagonist touches it in a two-shot with an ally watching. |
| 47–57s | NIGHT SNEAK-OUT | Fade in from black. Rain or fog. Ally wakes her / pulls her out. Fence or forbidden door. |
| 57–67s | GROUP ARGUMENT | Outdoors, fog, night. Allies vs agitator vs sceptic. Fast cuts, handheld. |
| 67–73s | EMOTIONAL PEAK (~73%) | Protagonist breaks (tears or grief). Pendant clutch. Ally comforts. |
| 73–83s | BEING WATCHED / HELD | Lit window, silhouette. Someone holds her arms. Slow push-in. |
| 83–91s | FINAL HOLD | ONE locked-off centred frontal shot, 8s. Defiant stare to camera. Hard cut to black. |

## Pacing

- Average shot 3–4s. Chase and argument: 1–2s cuts, handheld. Middle: 4–6s, static, symmetrical. Ending: one 8s hold.
- Transitions: hard cuts; fade from black for the night scene; rewind-icon title card; optional torn-paper B&W collage glitch as a premonition flash (max once).
- Dialogue is sparse. Max ~12 lines per episode. No line longer than two sentences.

## Tone & look

- Gothic school-horror mystery. Brooding, paranoid, grave. No jokes, no pop-culture, no CTA.
- Palette: desaturated teal/blue-green with rust browns; warm amber practical lights as the only contrast; B&W for flashes.
- Lighting: low-key, moonlit fog, volumetric haze, window/sconce practicals.
- Camera: static symmetrical frames, slow push-ins, rack focus; handheld only in chase/argument. Face centred — it's 9:16.
- Sound (write it, it will be produced): low drones, sub-bass hits, ring-flip foley, rain on glass, wind in pines, tonal swell on the rewind. No voiceover.

## Script format

```markdown
# HOLLOW PINE — Episode <N>: <Title>
**Format** 9:16 · **Length** ~90s · **Version** v1 · **Premise** <user premise>

## COLD OPEN (0–10s)
**[00:00–00:02] BLACK.** <sound>
**[00:02–00:10] EXT. <PLACE> — NIGHT**
VISUAL: <char_01 visual signature + what she does>, <shot sizes in order>
SOUND: ...
(no dialogue)

## TITLE (10–12s)
**[00:10–00:12] TITLE CARD** — `HOLLOW PINE` / `<N> HOURS EARLIER` — rewind icon over B&W still of next scene.

## SCENE 1 — <NAME> (12–22s)
**[00:12–00:22] INT./EXT. <PLACE> — <TIME>**
VISUAL: ...
ACTION: ...
CHAR_06: "line"
CHAR_01: "line"
CAMERA: ...
SOUND: ...

... (one block per beat through FINAL HOLD)

## FINAL HOLD (83–91s)
**[01:23–01:31] <PLACE>** — single locked-off frontal shot, 8s. ... Hard cut to black.

## Continuity
- World rules used: ...
- Questions advanced: ...
- Questions left open: ...
- New facts introduced (add to DNA next merge): ...
```

## Generation rules

1. Premise drives plot; DNA drives everything else. If they conflict, keep the DNA structure and adapt the premise.
2. Every scene block has a timecode, a VISUAL line with character IDs + signatures, and a SOUND line.
3. Show, don't say. Rules, history and threat arrive through objects, text on surfaces, and what adults don't explain.
4. Reuse the pendant tell at the emotional peak. Reuse at least two motifs: scratches, lit window, fog/pines, gripped arms, rain on glass, ring/coin flip.
5. End on the 8s hold + hard cut. Never resolve the main mystery.
6. Save the file, then reply with the script. Nothing else.
