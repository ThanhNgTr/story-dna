---
name: skill-creator-from-dna
description: |
  Generate a reusable series-writing skill from story DNA. Takes dna.json +
  story.md from /analyze-videos and builds .claude/skills/write-series-<slug>/:
  the reference plot as an abstract Story Template, character role templates
  (main/supporting), storytelling, camera, sound, color and pacing rules, and an
  adaptation workflow that turns a user's fragmented idea into a 10-20 episode
  series (1-2 min episodes). Also merges new reference DNA into an existing skill
  (--update). Triggers on: "generate skill", "create skill from DNA", "skill from
  analysis", "tao skill tu DNA". Output: write-series-<slug> skill + metadata JSON.
---

# Skill Generation from Story DNA

## When to Use

After `/analyze-videos` produced `dna.json` + `story.md`. Rare step: once per reference video.

```bash
/skill-creator-from-dna --dna data/analyses/<run-id>/dna.json --name <slug>
/skill-creator-from-dna --dna data/analyses/<run-id>/dna.json --update <slug>
```

## Modes

| Mode | When | Result |
|---|---|---|
| `create` (default) | Slug not in `.claude/skills/` | New `write-series-<slug>` v1 |
| `update` | More reference for an EXISTING skill | Same skill, vN+1, DNA merged |

Slug exists and no `--update` -> stop, ask: new slug or update. Never overwrite silently.

`update`:
1. Snapshot live SKILL.md -> `versions/SKILL_vN.md` (and `references/` -> `versions/references_vN/`).
2. Merge: keep rules both DNAs agree on; add new patterns/roles; on conflict prefer new DNA and log it.
3. Keep rules added by `/refine-skill` (see `## Changelog`) unless new DNA contradicts them -> ask user.
4. Bump version, changelog line, metadata `write-series-<slug>_vN+1.json` with `dna_sources: [old, new]`.

## What to Generate

```
.claude/skills/write-series-<slug>/
├── SKILL.md                         # rules + workflow (< 500 lines)
├── references/
│   ├── reference-story.md           # the learned plot: story.md + plot timeline + mystery ledger + arcs
│   └── reference-characters.md      # full character sheets with verbatim sample lines
└── versions/SKILL_v1.md             # immutable snapshot
data/skills-generated/write-series-<slug>_v1.json
```

### Core idea: learn the plot as FUNCTIONS, not content

The user's script is fragmented; they want THEIR idea told the way the reference story is told.
So the skill stores the reference plot twice:
- **Story Template (in SKILL.md)**: the plot abstracted into beat functions placed at % of the
  season ("protagonist enters a closed world and loses her means of escape — 0-5%"), with the
  reference event as a one-line example. This is what gets transplanted.
- **reference-story.md**: the concrete plot, for the writer to study rhythm, reveal spacing and
  how scenes earn emotion. Never copied: names, places, specific events stay in the reference.

Derive the Story Template from `story.acts`, `story.plot_timeline`, `story.mystery_ledger`,
`story.subplots`, `story.character_arcs`, `story.episode_break_candidates`. Express positions in %
of runtime so they scale to any season length (10-20 episodes).

Derive the Episode Template from `episode_break_candidates` spacing, `craft.storytelling.reveal_rhythm_sec`,
`craft.pacing`, and the strongest hook patterns. Target 60-120s episodes.

Every rule cites its DNA evidence in short (`Ref: t=255s`, a quoted line, or a field). Missing DNA
field -> write what IS there and mark `TODO (not in DNA)`. Do not invent.

### Generated SKILL.md template

Section names are fixed: `/refine-skill` patches by section.

````markdown
---
name: write-series-<slug>
version: v1
description: |
  Turn a rough or fragmented story idea into a <N>-episode vertical series (1-2 min
  episodes) told the way <reference title/genre> is told: <logline-level summary of
  the structure>, <character system>, <signature craft: VO, pacing, look>. Use whenever
  the user wants to develop an idea, notes, scattered scenes or a draft into a series,
  season outline, episode scripts, or screenplay in this style, even if they only paste
  fragments. Output: series bible + season outline + episode screenplays (md + json).
---

# Write Series: <Slug>

Learned from: <dna path>, <source files, total duration>. Reference plot: references/reference-story.md.

## Quick Start
/write-series-<slug> --idea "..." | --idea-file notes.md [--episodes 12] [--episode-sec 90]
                     [--characters "..."] [--sample draft.md] [--continue <session-dir>] [--auto]

## Input
| Field | Default | Meaning |
|---|---|---|
| `--idea` / `--idea-file` | required | User's idea: logline, scattered scenes, notes, any language |
| `--episodes` | 12 | 10-20 |
| `--episode-sec` | 90 | 60-120 |
| `--characters` | - | Names + roles; missing roles filled from Character Bible |
| `--sample` | - | User draft: keep its content, apply this style |
| `--continue` | - | Existing session dir: keep bible, extend or revise |
| `--auto` | off | Skip the outline approval stop |

## Workflow
Session dir: data/series/<slug>/<session-id>/ (session-id = UTC YYYYMMDD-HHMMSS). Save input.json first.

### Stage 1 — Adaptation map (adaptation.md)
1. Extract every element from the idea: premise, characters, places, scenes, lines, endings, themes.
2. Map each onto a Story Template beat and a Character Bible role (table: user element -> function -> reference analog).
3. Empty beats/roles: fill with an original invention for the user's world, marked [from template].
4. Conflicts: the user's idea wins; adjust the template and note why.

### Stage 2 — Bible + outline (bible_v1.md/.json, outline_v1.md/.json)
- Bible: title, logline, premise, theme, world rules, locations (with look), cast (tier, role, want/need/flaw/secret, visual_signature, voice + 2 sample lines), mystery ledger plan (question -> clue episodes -> answer episode), relationship arcs.
- Outline: one row per episode — title, logline, beats, which Story Template beat(s) it carries (% position), reveal/clue, cliffhanger type, characters.
- Spread: map Story Template % positions onto episodes (beat at p% -> episode ceil(p/100 * N)).
- STOP and show the outline unless --auto. User approves with /refine-skill <slug> --approve outline or gives feedback.

### Stage 3 — Episodes (episodes/epNN_v1.md/.json)
- Each episode follows the Episode Template and the rule sections below.
- N > 6: write in parallel with general-purpose subagents, 3-4 episodes each; give each the bible, outline, this SKILL.md path and its episode numbers.
- Continuity pass after all episodes: names, visual signatures (verbatim), ledger timing, callbacks, timecodes adding up.
- Write series.md (index + all episodes) and reply with: outline table, open threads, file paths.

## Story Template (season arc)
| % | Beat function | Why it works | Ref |
|---|---|---|---|
<one row per beat, 10-20 rows, from acts/plot_timeline/turning points>

### Mystery / reveal ledger pattern
<how many questions run at once, avg spacing open->clue->answer in %, what is never answered in season>

### Subplots
<function of each subplot pattern, where it is set up and paid off in %>

## Episode Template (<min>-<max>s)
| Time | Beat | Rule | Ref |
<hook 0-3s, setup, escalation, reveal, cliffhanger; from episode_break_candidates + reveal rhythm>

## Story Bible (world-building template)
<world devices the reference uses (closed world, rules, forbidden place, traces, motifs...) as reusable patterns with Ref>

## Character Bible (role templates)
<main / supporting / minor roles: plot function, screen share, how introduced, how made recognizable,
want vs need, voice pattern, arc pattern, Ref (name in reference)>

## Storytelling Rules
<devices, exposition method, narration/VO, POV, reveal rhythm, cliffhanger patterns>

## Pacing Guidelines
<measured numbers: avg/median shot, cuts/min, shots per episode-length, by act>

## Tone & Voice Guidelines
<tone; dialogue: speech share, wpm -> words per episode, line length, VO share; 3-5 reference lines as style examples>

## Visual Guidance
### Camera
<when/how table>
### Color and lighting
<palette, looks per mood/location, lighting>

## Sound Guidance
<speech density, VO, music (mark inferred), silence use, sfx>

## Hook Patterns
<0-3s, mid-episode, ending; season premiere and finale hooks>

## Output Format
<episode md + json: see skill-creator-from-dna "Episode output format"; bible/outline json shapes>

## Self-check
<8-12 checkboxes: structure %, ledger, hooks, durations, signatures verbatim, VO share, pacing>

## Data limits
<sources, what was inferred (music, speakers), sample size>

## Changelog
- v1 (<ISO>): generated from <dna path>
````

### Episode output format (put in generated skill's Output Format)

`epNN_vK.md`:
```markdown
# EP03 — <Title> (90s)
Logline: ... | Story beats: <template beats> | Cliffhanger: <type>

### SC1 [00:00-00:12] EXT. <PLACE> — NIGHT
| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.8 | ECU | char_01 ... | VO: "..." | handheld | teal fog | drone, breath |
```

`epNN_vK.json` (read by /script-to-shotlist):
```json
{
  "skill": "write-series-<slug>", "skill_version": "v1", "session": "<session-id>",
  "episode": 3, "title": "...", "total_duration_sec": 90, "aspect_ratio": "9:16",
  "characters": {"char_01": {"name": "...", "visual_signature": "..."}},
  "scenes": [{"id": "SC1", "start_sec": 0, "end_sec": 12, "location": "...", "int_ext": "EXT", "time_of_day": "night",
    "beats": [{"start_sec": 0, "end_sec": 1.8, "shot_size": "ECU", "characters": ["char_01"], "action": "...",
      "dialogue": [{"character": "char_01", "line": "...", "voiceover": true, "delivery": "whisper"}],
      "camera": "...", "lighting_color": "...", "sound": "..."}]}],
  "cliffhanger": "...", "ledger": {"opened": [], "clues": [], "answered": []}
}
```

## Steps

1. Read `dna.json`, `dna.md`, `story.md` (same run dir). Check `.claude/skills/` for the slug.
2. Write `references/reference-story.md` (story.md + act table + plot timeline + mystery ledger +
   arcs + episode break candidates) and `references/reference-characters.md`.
3. Write SKILL.md from the template. Keep it under 500 lines; push long tables to references/.
4. Validate YAML frontmatter (`name`, `version`, `description`) by parsing it. Bad YAML -> skill
   silently fails to load.
5. Snapshot `versions/SKILL_v1.md`. Write `data/skills-generated/write-series-<slug>_v1.json`:
   ```json
   {"skill_name": "write-series-<slug>", "slug": "<slug>", "version": "v1",
    "created_timestamp": "ISO 8601", "dna_sources": ["data/analyses/<run>/dna.json"],
    "reference_sources": [{"filename": "ref.mp4", "duration_sec": 1820}],
    "skill_path": ".claude/skills/write-series-<slug>/SKILL.md",
    "season_defaults": {"episodes": 12, "episode_sec": 90},
    "pacing_from_dna": {}, "audio_transcribed": true, "speakers_diarized": false}
   ```
6. Tell the user: skill name, what it learned (one line per section), data limits, and how to run it.

## Notes

- Kebab-case slugs. Never overwrite versions.
- Skills live in `.claude/skills/` and are version-controlled; generated skills are removed when
  the project is reset for a new reference.
- Iterate with `/refine-skill <slug>`, not manual edits.
