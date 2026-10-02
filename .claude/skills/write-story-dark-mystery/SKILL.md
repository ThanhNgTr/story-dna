---
name: write-story-dark-mystery
version: v1
description: |
  Write ~90s vertical (9:16) serialized dark-mystery / thriller short scripts with
  any new world and characters, using craft learned from measured reference videos:
  character building, 9-scene episode structure, camera language, color and lighting,
  sound, pacing (avg shot 2.3s, ~25 cuts/min), hooks and cliffhangers. Use this skill
  whenever the user wants a short-form mystery, horror, thriller, secret, cult, boarding
  school, small town, missing person or "something is wrong here" story, a series episode
  with a cliffhanger, or a script that will be turned into AI video shots, even if they
  only give a one-line premise and do not name the genre. Input: topic (+ optional
  characters, sample script, length, previous episode). Output: script_v1.md + .json
  ready for /script-to-shotlist.
---

# Write Story: Dark Mystery Short

Craft rules learned from 2 reference episodes (9:16, ~90s, AI-generated serialized
thriller; source DNA `data/analyses/20261002-022148/dna.json`). The rules are
generic: apply them to ANY world and cast. Lines marked `Ref:` show how the reference
did it. They are illustrations, not content to copy.

Numbers under Pacing are measured from real cuts (78 shots). Everything about
sound is inferred from images only and is marked `INFERRED`.

## Quick Start

```
/write-story-dark-mystery --topic "A lighthouse keeper's daughter finds her mother's handwriting in a sealed room"
/write-story-dark-mystery --topic "..." --characters "Mai (protagonist), Tuan (ally)" --sample notes.md
/write-story-dark-mystery --topic "..." --continue data/scripts/dark-mystery/<session>/final.md
```

## Input

| Field | Required | Meaning |
|---|---|---|
| `--topic` | yes | Premise / what this episode is about |
| `--characters` | no | Names + roles. Missing -> cast from the role templates below |
| `--sample` | no | User's outline or script. Keep its beats and content; apply this style on top |
| `--length` | no | Default 90s. Scale scene times proportionally |
| `--continue` | no | Previous final script -> keep world, cast, visual signatures, open questions |

Session dir: `data/scripts/dark-mystery/<session-id>/` (`session-id` = UTC `YYYYMMDD-HHMMSS`).
Write `input.json` (the input above), `script_v1.md`, `script_v1.json`. `/refine-skill dark-mystery`
reads this dir, so keep the names exact.

## Workflow

1. Read input. If `--continue`, read the previous script and reuse its Story Bible, cast and
   visual signatures verbatim.
2. Build the world (Story Bible): pick the closed world, the entry loss, the rules, the forbidden
   place, the traces, the motif. Write them down before any scene.
3. Cast (Character Bible): map user characters onto role templates; fill missing roles.
4. Choose a structure template (A for a first episode, B for a continuation) and write the
   9-scene beat sheet with timecodes.
5. Write the shot-level script inside the pacing budget.
6. Run the Self-check. Fix what fails.
7. Save files (see Output Format). Reply with: logline, scene list, open questions, file paths.

## Story Bible (world-building template)

A short has no time to explain a world. These devices make the world legible in seconds and
create constant pressure. Use most of them; invent your own versions for the user's topic.

| Device | Why it works | Ref: |
|---|---|---|
| **Closed world** | Isolation means no outside help, so every problem must be faced | School deep in fog-bound pine forest, padlocked gate |
| **Entry ritual of loss** | Taking something away at arrival (phone, name, key) shows power and removes easy solutions | Phones dropped into a wooden crate at the gate |
| **Visible rules** | A written rule list tells the audience what breaking a rule will cost; every later scene can break one | Numbered RULES board in the assembly hall |
| **Forbidden place** | One place the protagonist must not go = the destination of the series | Restricted concrete building with a barred vent |
| **Physical traces of the past** | Marks left by someone before = proof the danger is real and old, without exposition | Claw scratches on the gate; portrait plaque "ELI" with "STILL HERE" carved in |
| **Motif object** | One object links the protagonist to the mystery; reappears at every emotional peak | Silver ring on a chain; a matching ring on the hand behind the grate |
| **Watchers** | Someone always sees; makes safe places unsafe | Silhouette in a lit window at the end |
| **Navigational markers** | Simple visual trail the audience can follow in 1-2s shots | White cloth strips tied to trees |

Plot rules per episode:
- Add 1-2 new world facts. Answer at most 1 old question. Open at least 2 new ones.
- Adults never explain. Menace comes from what they do and how they look at her, not what they say.
- No resolution inside one episode. The mystery grows.

## Character Bible (role templates)

About 9 people on screen per episode, 4-5 of them recurring. In 2s shots the audience must
recognize each person instantly, so every character gets ONE strong visual hook.

| Role | Screen time | Craft rules | Ref: |
|---|---|---|---|
| **Protagonist** | 55-75% | Defined by the motif object, not by talking. Reacts more than speaks. Covered in CU/MCU. Arc inside one episode moves from fear to resolve; ends on a decision face | Freckled girl, ring on chain. ep1: terrified -> stoic -> curious -> alarmed -> defiant. ep2: wary -> frightened -> grieving -> determined |
| **Loyal ally** | 15-20% | Shows loyalty with touch (grips her arm, comforts her), not speeches. Appears in the final shot beside her | Boy in crest blazer who grips her arm |
| **Secondary allies (1-2)** | 5-15% each | One instant visual trait each (hair color, glasses). Voice doubt or panic so the protagonist does not have to | Redhead roommate who wakes her; nervous boy in wire glasses |
| **Authority figures (3-4)** | 4-9% each | Each owns one prop or tic (cane, coin, crate, black high-collar dress). Calm, still, often smiling. Never explain their motives | Headmaster with cane; teacher flipping a silver coin; scowling gate guard; stern matron |
| **Mirror / victim** | 5-8% | Shares the protagonist's motif or fate, so the stakes become personal | Girl behind the grate wearing a matching ring |

Rules:
- Write a full `visual_signature` per character once (age, hair, eyes, clothing, prop, marks) and
  reuse it word for word in every beat. AI video drifts if wording changes.
- Uniform or dress code for the group, so the one person who breaks it stands out.
- Dialogue: short, under 8 words per line, whispers and fragments. Many beats have none.

## Narrative Structure

Both reference episodes use 9 scenes in ~90s (avg ~10s per scene). Climax position varies (73% vs
38%), so pick by template.

### Template A: Flash-forward (first episode, introduce the world)

| # | Time | Scene | Camera / look |
|---|---|---|---|
| 1 | 0-8s | Cold open: protagonist in peril in the future (running, hiding, injured) | Handheld, ECU/CU face, night |
| 2 | 8-11s | Title card + time-jump card ("48 HOURS EARLIER") | Graphic over black, B&W + grain |
| 3 | 11-19s | Entry ritual: arrival, something taken, lock shown | Static, slow push, ECU on the lock/trace |
| 4 | 19-38s | Institution + rules: authority figures introduced one by one | Symmetrical WS, push-ins on faces, warm practicals |
| 5 | 38-50s | Discovery: protagonist alone finds a trace | One long take 8-12s, slight push-in |
| 6 | 50-56s | Night disturbance: ally wakes her, something outside | Whip-pan transition, cold blue |
| 7 | 56-66s | Group gathering / argument | Static, slight handheld, fog backlight |
| 8 | 66-73s | Return to the cold-open moment = climax | Shallow DOF, terror and grief |
| 9 | 73-90s | Cliffhanger: allies flank her, a watcher appears, defiant stare | Long holds 6-10s, warm window accent in cold night |

### Template B: Continuation (later episode, deepen the mystery)

| # | Time | Scene |
|---|---|---|
| 1 | 0-14s | Cold open already in action (search, chase), following markers |
| 2 | 14-29s | Find a victim/mirror; allies argue; motif clutched in fist |
| 3 | 29-39s | Forbidden place revealed (low angles, macro on the trace) = climax ~38% |
| 4 | 39-43s | Cutaway: authority figure watching, smiling |
| 5 | 43-51s | Aftermath walk back (handheld, fast cuts, grey daylight fog) |
| 6 | 51-62s | Institution in silence (nobody mentions what happened) |
| 7 | 62-73s | Ally comforts her; she shows the motif = emotional core |
| 8 | 73-83s | Act of defiance (writes a note, keeps evidence) + authority intimidates her |
| 9 | 83-90s | Closing CU: resolve, unanswered question |

Shared: night or fog in at least half the runtime; a time cue (card or implied jump) between scenes 1-3; end with no resolution.

## Pacing Guidelines (measured)

| Metric | Value |
|---|---|
| Shots per 90s | 37-41 |
| Avg shot | 2.3s (range 2.1-2.5) |
| Median shot | 1.8s |
| Cuts per minute | ~25 |
| First cut | 2.5-3.5s |
| Shortest / longest | 0.5s / 12.5s |

Shot length mix (share of all shots): <1s 23%, 1-2s 32%, 2-4s 35%, 4-8s 8%, >=8s 3%.

Rules:
- Most shots 1-4s. Sub-1s shots only in bursts: panic, flashes, impacts, montage.
- At most 1-2 shots over 6s per episode, reserved for the discovery long take or the final hold.
  Long holds land harder because everything else is fast.
- Template A shape: fast start (avg ~1.5s in the first quarter), slows at the end (~4.8s in the last
  quarter). Template B stays even (~2s throughout).
- Budget check: sum of shot durations = target length. Count shots; ~40 per 90s.

## Visual Guidance

### Camera language

| Use | When | Why |
|---|---|---|
| Static or slow push-in | Default | Stillness = dread; push-in = pressure building on a face |
| Handheld | Only panic, chase, aftermath | Contrast with the static default makes chaos feel real |
| ECU / CU / MCU | Protagonist most of the time | Story is told through her reactions |
| Symmetrical WS | Institutions (hall, corridor) | Order and control; she is small inside it |
| Macro insert | Motif, traces, locks, notes | Clues must read in under 1s |
| Low angle | Forbidden places, authority | Power and threat |
| POV through window / OTS | Watchers, spying | Someone is always watching |
| Whip-pan | Scene transition into sudden events | Energy without a graphic |
| Shallow DOF, rack focus | Reveals | Hides then shows the threat |

### Color and lighting

- Base: teal / blue-green night, desaturated greens in fog. Daylight is overcast fog, never sunny.
- Accent: warm amber practicals (lanterns, sconces, one lit window). Warm = the institution or a
  watcher. It is never safety. Warm-inside vs cold-outside is the main contrast.
- Past or time jump: black and white + grain and dust.
- Group wears dark uniform tones (navy); white highlights (shirts, markers, flashlight beams) guide the eye.
- Low-key lighting, volumetric fog backlight, flashlight shafts. Faces are lit from one side.

### On-screen text

- Title card + time-jump card in clean white caps over black.
- Location super for institutions ("INT. ASSEMBLY HALL").
- Diegetic text (plaques, carved words, notes on skin) at 3 words or fewer. AI video garbles long
  text; short carved words read as clues.

## Sound Guidance (INFERRED, not yet verified from audio)

The reference was analyzed from images only. Treat this section as a starting guess and update it
after audio analysis.

- No voiceover. Dialogue sparse, short, often whispered.
- Music: low drones, tense strings or piano; impact hit on the title card; rewind SFX on a time jump.
- Ambience carries scenes: wind, fog, rain on glass, snapping branches, footsteps on gravel.
- Drop to near silence right before a reveal.

## Tone & Voice Guidelines

- Somber, serious, cinematic. No jokes, no winks to camera.
- Emotions in rotation: fear, suspicion, grief, resolve.
- Restraint: show the trace, cut away before explaining it.

## Hook Patterns

| Moment | Pattern | Ref: |
|---|---|---|
| 0-3s | Protagonist's face in peril or mid-search, no text, already moving | Bloodied girl running between pines, looks back |
| First cut 2.5-3.5s | Cut to a second angle of the same danger, not to context | |
| ~8-11s | Title / time cue gives a frame after the hook lands | "HOLLOW PINE / 48 HOURS EARLIER" |
| Midpoint | A physical trace or a forbidden place made visible | "STILL HERE" carved in a portrait; hand behind a grate |
| Ending | Held CU of a decision + one new unanswered question + watcher/motif | Friends grip her arms, silhouette in a lit window |

## Self-check (run before saving)

- [ ] 0-3s: protagonist on screen, in danger or searching. First cut 2.5-3.5s.
- [ ] 9 scenes (+-1), timecodes add up to target length.
- [ ] ~40 shots per 90s, avg 2-2.5s, at most 2 shots over 6s.
- [ ] At least 4 world devices from the Story Bible used.
- [ ] Every character has a visual_signature, reused verbatim.
- [ ] Motif object appears at the emotional peak and in the final scene.
- [ ] No adult explains the mystery. Nothing is resolved. 2+ new questions open.
- [ ] Teal/cold base with warm practical accents; handheld only in panic/chase/aftermath.
- [ ] Dialogue lines under 8 words; no voiceover.

## Output Format

### `script_v1.md`

```markdown
# <Title> - <Episode label> (90s, 9:16)
Logline: <one sentence>
Template: A | B

## Characters
- char_01 <Name> (protagonist): <visual_signature>

## Story Bible (this script)
- Closed world: ... / Entry loss: ... / Rules: ... / Forbidden place: ... / Traces: ... / Motif: ...

## Script
### S1 [00:00-00:08] EXT. <PLACE> - NIGHT
| Time | Shot | Action | Dialogue | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.5 | ECU | char_01 ... | - | handheld | teal moonlit fog | breath, branches |

## Open questions
- ...
```

### `script_v1.json` (read by /script-to-shotlist)

```json
{
  "skill": "write-story-dark-mystery",
  "skill_version": "v1",
  "title": "...",
  "aspect_ratio": "9:16",
  "total_duration_sec": 90,
  "template": "A",
  "characters": {"char_01": {"name": "...", "role": "protagonist", "visual_signature": "..."}},
  "story_bible": {"closed_world": "...", "entry_loss": "...", "rules": [], "forbidden_place": "...", "traces": [], "motif": "...", "watchers": "..."},
  "scenes": [
    {
      "id": "S1", "start_sec": 0, "end_sec": 8, "location": "...", "int_ext": "EXT", "time_of_day": "night",
      "beats": [
        {"start_sec": 0, "end_sec": 1.5, "shot_size": "ECU", "characters": ["char_01"],
         "action": "...", "dialogue": [], "camera": "handheld", "lighting_color": "...",
         "sound": "...", "on_screen_text": null}
      ]
    }
  ],
  "open_questions": []
}
```

## Data limits

- Learned from 2 episodes of one series. Rules are provisional; widen with more reference videos
  via `/skill-creator-from-dna --update dark-mystery`.
- Sound is inferred from images. Dialogue style is inferred from lips and context.
- Pacing numbers are measured (ffmpeg scene detection); fades may be merged into longer shots.

## Changelog

- v1 (2026-10-02T03:30:00Z): created from data/analyses/20261002-022148/dna.json (ep1, ep2) as a
  generic style skill (no series-specific world or cast). Pacing measured; sound inferred.
