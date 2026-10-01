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

3. **Create scripts using that skill**:
   ```bash
   /write-story-demo-promo --topic "Launch a new app" --characters "Alex (CEO), Jordan (Developer)"
   ```
   Returns: Markdown script v1

4. **Refine the skill based on feedback**:
   ```bash
   /refine-skill demo-promo --feedback "tone too formal, make it conversational and energetic"
   ```
   Updates skill, returns new script version

5. **Break into shots**:
   ```bash
   /script-to-shotlist "# Script v3..."
   ```
   Returns: `shotlist.json` + `shotlist.md` with 1–5s shot breakdown

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
