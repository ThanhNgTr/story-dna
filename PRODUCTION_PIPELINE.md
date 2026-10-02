# Production Pipeline (optional, after the series is approved)

The core flow ends with approved screenplays in `data/series/<slug>/<session-id>/final/`
(see [README.md](README.md)). This optional chain turns ONE approved episode into material for a
crew or an AI video tool. Run it per episode.

## Chain

```
final/epNN.md (+ .json)
  └─ [1] /script-to-shotlist ──▶ shotlist.md/.json + prompts.md/.json   (1-5s shots, one video prompt each)
       └─ [2] /direct-video ──▶ production_guide.md/.json               (blocking, actor cues, lighting, sound sync)
            ├─ [3] /cinematographer-brief ──▶ cinematography_brief.md/.json  (lens, movement, framing, DOF)
            ├─ [4] /sound-design-brief ──▶ audio_brief.md + audio_cue_sheet.json (music, foley, dialogue sync)
            └─ [5] /production-design-brief ──▶ design_brief.md + design_specifications.json (color, sets, costume, props)
```

Steps 3-5 only need the production guide and can run in parallel.

## Commands

```bash
E=data/series/<slug>/<session-id>/final
/script-to-shotlist $E/ep01.md                     # writes $E/shots/ep01/
/direct-video --shotlist $E/shots/ep01/shotlist.json
/cinematographer-brief --production-guide $E/shots/ep01/production_guide.json
/sound-design-brief --production-guide $E/shots/ep01/production_guide.json
/production-design-brief --production-guide $E/shots/ep01/production_guide.json
```

Whole season: `/script-to-shotlist $E/` processes every episode into `shots/epNN/`.

## Output per episode

```
final/shots/epNN/
├── shotlist.md / .json            shot breakdown with timecodes
├── prompts.md / .json             self-contained video-gen prompt per shot (characters word-for-word from bible)
├── production_guide.md / .json    director scene guide
├── cinematography_brief.md / .json
├── audio_brief.md + audio_cue_sheet.json
└── design_brief.md + design_specifications.json
```

## Consistency rules across a season

- Character look comes from `final/bible.json` `visual_signature`, repeated verbatim in every prompt
- Camera, color and sound defaults come from the series skill (`.claude/skills/write-series-<slug>/SKILL.md`
  Visual Guidance / Sound Guidance); briefs refine them per scene, never contradict them
- Shot durations respect the skill's Pacing Guidelines (measured from the reference)
