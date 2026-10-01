---
name: skill-creator-from-dna
description: |
  Generate a reusable Claude script-writing skill from narrative DNA. 
  Takes DNA JSON from /analyze-videos, embeds rules into a new SKILL.md, 
  and registers it in .claude/skills/. The generated skill (e.g., 
  /write-story-promo) becomes immediately available for users to create 
  scripts. Triggers on: "generate skill", "create skill from DNA", 
  "skill from analysis", "skill generator". Input: dna.json path + skill 
  name. Output: New .claude/skills/write-story-<slug>/SKILL.md + metadata JSON.
---

# Skill Generation from Narrative DNA

## When to Use This Skill

Use this skill after analyzing reference videos with `/analyze-videos`:
- Convert DNA patterns into a reusable script-writing skill
- Embed character templates, pacing rules, tone guidelines into the skill
- Register the new skill so users can immediately call it
- Create multiple skills for different video types (promos, tutorials, testimonials)

**Input**: `dna.json` from `/analyze-videos` + desired skill name (slug)
**Output**: New skill registered at `.claude/skills/write-story-<slug>/SKILL.md`

## Quick Start

```bash
/skill-creator-from-dna --dna data/analyses/20251001-120000/dna.json --name demo-promo
```

This will:
1. Read DNA from `dna.json`
2. Generate a SKILL.md template with embedded DNA rules
3. Register it at `.claude/skills/write-story-demo-promo/`
4. Make `/write-story-demo-promo` immediately available

## How It Works

### Step 1: Parse DNA
- Reads `dna.json` from analyze-videos output
- Extracts narrative structure, pacing, tone, characters, visual rules

### Step 2: Generate SKILL.md
- Creates `.claude/skills/write-story-<slug>/SKILL.md`
- Embeds DNA rules into skill prompt:
  - Character archetype templates
  - Narrative structure guidelines (setup/conflict/resolution timing)
  - Pacing rules (shot duration, cut frequency)
  - Tone + voice guidelines
  - Visual style preferences
  - Hook patterns (opening, midpoint, closing)
- Includes examples from analyzed videos

### Step 3: Register Metadata
- Saves skill metadata to `data/skills-generated/write-story-<slug>_v1.json`
- Tracks DNA source + generation timestamp
- Stores character templates + tone examples for future refinement

### Step 4: Reload Skills
- Notifies Claude Code to reload `.claude/skills/`
- New skill becomes available immediately

## Output Format

### Generated SKILL.md Structure
```yaml
---
name: write-story-<slug>
description: |
  Generate scripts matching the <source> video style. 
  Follows structure: <setup duration>s setup → <climax %> climax → resolution. 
  Pacing: <avg shot duration>s avg shot, <cut rhythm> rhythm. 
  Characters: <character types>. Tone: <tone>. Use this to create <type> scripts.
---

# Script Generation: <Slug>

## When to Use This Skill
[Description matching the DNA style]

## Quick Start
`/write-story-<slug> --topic "Your topic" --characters "Names (roles)"`

## How It Works
[DNA-derived rules for structure, pacing, tone]

## Character Templates
[Archetypes from DNA with examples]

## Narrative Structure Template
[Setup/conflict/resolution timing from DNA]

## Pacing Guidelines
[Shot duration + rhythm rules]

## Tone & Voice Guidelines
[Language register, energy level, emotion]

## Visual Guidance
[Color palette, camera movement, lighting notes]

## Hook Patterns
[Opening, midpoint, closing examples]

## Examples
[Sample scripts from training videos]
```

### Metadata JSON (`data/skills-generated/write-story-<slug>_v1.json`)
```json
{
  "skill_name": "write-story-demo-promo",
  "slug": "demo-promo",
  "version": "v1",
  "created_timestamp": "2025-10-01T14:30:00Z",
  "dna_source": "data/analyses/20251001-120000/dna.json",
  "dna_videos": [
    "sample.mp4"
  ],
  "skill_path": ".claude/skills/write-story-demo-promo/SKILL.md",
  "characters_from_dna": [
    {
      "archetype": "Protagonist/Expert",
      "screen_time_pct": 70,
      "dialogue_style": "conversational"
    }
  ],
  "pacing_from_dna": {
    "avg_shot_duration_sec": 2.8,
    "cut_rhythm": "medium"
  },
  "tone_from_dna": {
    "overall": "conversational",
    "energy": "high"
  }
}
```

## Usage After Generation

Once generated, use the new skill like this:

```bash
/write-story-demo-promo --topic "Launch announcement for new app" \
  --characters "Alice (Product Manager), Bob (Engineer)" \
  --length 30s
```

Returns: Markdown script following the DNA structure, pacing, tone

## Refinement

After generating scripts and getting feedback, use `/refine-skill`:

```bash
/refine-skill demo-promo --feedback "tone too formal, need more energy"
```

This patches the SKILL.md and creates `write-story-demo-promo_v2.md`

## Notes

- Skill names are kebab-case (demo-promo, not Demo Promo)
- Versions are tracked (v1, v2, v3...) — don't overwrite
- Generated skills are stored in `.claude/skills/` and version-controlled
- Each skill embeds specific DNA (don't mix DNA from different videos)
- Use `/refine-skill` to iterate, not manual edits to SKILL.md
