---
name: refine-skill
description: |
  Iterate on generated skills based on user feedback. Updates a 
  write-story-<slug> skill's rules (tone, pacing, characters) and 
  re-runs script generation to produce a new version. Triggers on: 
  "refine skill", "improve skill", "adjust tone", "update script skill", 
  "iterate on skill". Input: skill slug + feedback. Output: Updated 
  SKILL.md (v2, v3) + new script version. Part of the feedback loop.
---

# Skill Refinement & Iteration

## When to Use This Skill

Use after generating scripts with a skill (e.g., `/write-story-demo-promo`):
- User gives feedback: "tone too formal", "pacing too fast", "characters feel wrong"
- Update the skill's rules based on feedback
- Re-generate scripts using updated rules
- Version the skill (v1 → v2 → v3)

**Input**: Skill slug (e.g., `demo-promo`) + feedback text
**Output**: Updated SKILL.md (v2) + new script reflecting feedback

## Quick Start

```bash
/refine-skill demo-promo --feedback "tone too formal, make it conversational and energetic"
```

This will:
1. Load current `write-story-demo-promo/SKILL.md`
2. Parse feedback and identify issues (tone, pacing, characters)
3. Update rules in SKILL.md (create v2)
4. Re-generate script with updated rules
5. Save `write-story-demo-promo_v2.md` + metadata

## How It Works

### Step 1: Parse Feedback
- Analyze feedback text to identify categories:
  - **Tone**: formal/casual, energy level, emotion
  - **Pacing**: shot duration, cut frequency, rhythm
  - **Characters**: archetype, dialogue style, screen time
  - **Structure**: opening hook, climax timing, ending
  - **Visual**: colors, camera movement, lighting

### Step 2: Update SKILL.md
- Load current skill from `.claude/skills/write-story-<slug>/`
- Modify relevant sections based on feedback
- Increment version (v1 → v2)
- Save to same path (SKILL.md is live)
- Keep `SKILL_v1.md` backup for reference

### Step 3: Store Iteration Record
- Save feedback + changes to `data/iterations.json`:
  ```json
  {
    "skill": "demo-promo",
    "version": "v2",
    "feedback": "tone too formal",
    "changes": {
      "tone": {
        "formality": "formal → casual",
        "energy": "medium → high"
      }
    }
  }
  ```

### Step 4: Ready for Re-generation
- New skill is immediately available
- User can call `/write-story-demo-promo` again
- Script v2 will reflect feedback

## Feedback Categories & Mappings

| Feedback | Maps to | Default Adjustment |
|----------|---------|-------------------|
| "tone too formal" | `tone.formality` | formal → casual |
| "more energy" | `tone.energy` | medium → high |
| "tone too dark" | `tone.emotion` | sad → inspiring |
| "pacing too fast" | `pacing.cut_rhythm` | fast → medium |
| "shots too long" | `pacing.avg_shot_duration_sec` | +1 second |
| "add more dialog" | `characters[].dialogue_style` | add "(frequent dialog)" |
| "stronger opening" | `hooks.opening_0_3s` | emphasize visual hook |
| "better ending" | `hooks.closing` | strengthen CTA |

## Example Iteration

**Version 1**:
```yaml
tone:
  overall: "conversational"
  formality: "formal"
  energy: "medium"
```

**Feedback**: "tone too formal, need more energy"

**Version 2** (after refine):
```yaml
tone:
  overall: "conversational"
  formality: "casual"
  energy: "high"
```

**Script v2** now generated with:
- More contractions ("it's", "don't", "that's")
- Shorter sentences
- Exclamation points for emphasis
- Faster pacing options

## Multiple Iterations

You can refine multiple times:
```bash
/refine-skill demo-promo --feedback "v2 is better, but characters need more personality"
# → v3

/refine-skill demo-promo --feedback "v3 opening is slow, tighten first 3s"
# → v4
```

Each version is tracked in metadata + backed up.

## Notes

- Versions are immutable (don't overwrite v1 if you still need it)
- Feedback is free-form text (AI will parse the intent)
- Re-running same feedback twice might produce slightly different scripts (Claude is stochastic)
- Use `/script-to-shotlist` on final script version to break into shots
- Always test generated scripts before committing to final production
