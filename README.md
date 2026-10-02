# story-dna

Video → Script → DNA → Skill Pipeline (POC)

Analyze local videos to extract narrative DNA, auto-generate reusable Claude skills, and let users create scripts using those skills.

## Quick Start

1. **Analyze reference videos**:
   ```bash
   /analyze-videos --input samples/ --max-frames 30
   ```
   Produces: `dna.json`, `dna.md`, frames/

2. **Generate a skill from that DNA**:
   ```bash
   /skill-creator-from-dna --dna data/analyses/20251001-120000/dna.json --name demo-promo
   ```
   Creates: `.claude/skills/write-story-demo-promo/SKILL.md`

3. **Create a script using that skill** (optional sample script to follow):
   ```bash
   /write-story-demo-promo --topic "Launch a new app" --characters "Alex (CEO), Jordan (Developer)" --sample my_outline.md
   ```
   Returns: `data/scripts/demo-promo/<session-id>/script_v1.md`

4. **Feedback loop** (repeat until happy):
   ```bash
   /refine-skill demo-promo --feedback "tone too formal, make it conversational and energetic"
   ```
   Skill auto-patches (v2, v3...), script re-generated on same input

5. **Approve** -> final script:
   ```bash
   /refine-skill demo-promo --approve
   ```

6. **Prompt list** (final output):
   ```bash
   /script-to-shotlist data/scripts/demo-promo/<session-id>/final.md
   ```
   Returns: `prompts.json` + `prompts.md` - one video prompt per 1-5s shot (who says what, does what)

New viral idea later? Analyze the new videos, then `/skill-creator-from-dna --dna <new dna.json> --update demo-promo`.

## Directory Structure

```
.
├── .claude/
│   ├── CLAUDE.md                           # Project guide + footguns
│   └── skills/
│       ├── analyze-videos/                 # Extract narrative DNA
│       ├── skill-creator-from-dna/         # Generate skills
│       ├── refine-skill/                   # Update skills + scripts
│       └── script-to-shotlist/             # Break into shots
├── data/
│   ├── analyses/<timestamp>/               # Output from analyze-videos
│   └── skills-generated/<slug>_v1.json     # Skill metadata
├── .gitignore
└── README.md
```

## Features

- **Local video analysis**: Extract frames, summarize with Claude Vision
- **Narrative DNA extraction**: Identify structure, pacing, tone, characters
- **Auto skill generation**: Create Claude skills from DNA templates
- **Script generation**: Use generated skills to write scripts
- **Skill refinement**: Patch skills based on feedback (iterative)
- **Shot breakdown**: Convert scripts to shot lists for video generation

## Prerequisites

- Python 3.10+ (if analyzing videos locally)
- `ffmpeg` (for frame extraction)
- Claude API access (for Vision + text generation)
- Local video files (MP4, MOV, etc.)

## POC Roadmap

- [x] Setup repo structure + CLAUDE.md
- [ ] Skill 1: `analyze-videos` (extract DNA from videos)
- [ ] Skill 2: `skill-creator-from-dna` (generate skills)
- [ ] Skill 3: `refine-skill` (iterate on skills + scripts)
- [ ] Skill 4: `script-to-shotlist` (break into shots)
- [ ] Test end-to-end with sample videos
- [ ] (Future) Connect to Seedance/Higgsfield for video generation
- [ ] (Future) Build UI dashboard for skill versioning

## Notes

- All outputs go to `data/` for reproducibility
- Skills are versioned (v1, v2, v3...)
- No external APIs in POC (using Claude Vision + local ffmpeg)
- Markdown is the primary output format for humans
- JSON is the data interchange format for agents
