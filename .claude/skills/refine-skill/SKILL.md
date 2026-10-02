---
name: refine-skill
description: |
  Human-in-the-loop feedback loop for a generated write-story-<slug> skill.
  User reviews a script, gives feedback, skill auto-patches its rules (new
  version), re-generates the script, repeats until user approves. On approve:
  skill version marked stable + final script saved. Triggers on: "refine skill",
  "improve skill", "adjust tone", "update script skill", "iterate on skill",
  "feedback on script", "approve script", "finalize script". Input: skill slug +
  feedback (or "approve"). Output: SKILL.md vN+1 + script vN+1, or final script.
---

# Skill Refinement Loop (Human in the Loop)

## When to Use

After `/write-story-<slug>` produced a script and the user reviewed it.

- Feedback given -> patch skill rules -> new skill version -> re-generate script with SAME user input
- User says approve / ok / final -> finalize (no more patch)

**Input**: slug + feedback text, or slug + `--approve`
**Output**: patched skill vN+1 + script vN+1, or final script + stable skill

## Quick Start

```bash
/refine-skill hollow-pine --feedback "tone too formal, char_06 needs more lines"
# -> skill v2, script v2. Review, then:
/refine-skill hollow-pine --feedback "opening 0-3s still slow"
# -> skill v3, script v3. Review, then:
/refine-skill hollow-pine --approve
# -> skill v3 marked stable, script v3 saved as final.md
```

## Paths

```
.claude/skills/write-story-<slug>/
├── SKILL.md                    # live = latest version (frontmatter `version: vN`)
└── versions/
    ├── SKILL_v1.md             # immutable snapshots, never overwrite
    ├── SKILL_v2.md
    └── ...

data/scripts/<slug>/<session-id>/        # session-id = YYYYMMDD-HHMMSS of first script
├── input.json                  # user input (topic, characters, sample script) - reused every round
├── script_v1.md / .json
├── script_v2.md / .json
├── iterations.json             # full feedback history
└── final.md / final.json       # written on approve only

data/skills-generated/write-story-<slug>_vN.json   # metadata per version
```

## Loop

### Step 1 - Load state
- Read live `SKILL.md`, current version N (frontmatter).
- Read latest `data/scripts/<slug>/<session-id>/script_vK.md` + `input.json` + `iterations.json`.
- No session found -> ask user which script the feedback is about. Do not guess.

### Step 2 - Classify feedback
Split feedback into items. Each item gets a scope:

| Scope | Meaning | Action |
|---|---|---|
| `rule` | Generalizes to every future script ("tone too formal", "hook too slow") | Patch SKILL.md |
| `script` | Only this story ("rename the dog", "cut scene 3") | Do NOT patch skill. Apply as one-off edit when re-generating |

Rule-scope categories -> SKILL.md section:

| Feedback | Section | Example patch |
|---|---|---|
| tone / voice / energy | Tone & Voice | formality: formal -> casual |
| pacing / shot length / rhythm | Pacing Guidelines | avg shot 3.4s -> 2.5s |
| characters / dialogue / screen time | Character Bible | char_06: add 2-3 lines, sarcastic |
| world / context / setting | Story Bible / World Rules | add or fix world rule |
| structure / hook / ending | Narrative Structure / Hook Patterns | hook 0-3s: start on action |
| visual / camera / color | Visual Guidance | more handheld in chase beats |

Ambiguous item (unclear if rule or script) -> ask user, one short question.

### Step 3 - Snapshot + patch skill (only if any `rule` item)
1. Copy live SKILL.md -> `versions/SKILL_vN.md` (if not already there).
2. Edit only the sections hit by feedback. Keep everything else byte-identical.
3. Bump frontmatter `version: vN+1`. Add entry under `## Changelog` at bottom:
   ```
   - vN+1 (2026-10-01T14:30:00Z): <one line per rule change>
   ```
4. Validate YAML frontmatter (name, description, version). Bad YAML -> skill fails to load silently.
5. Write `data/skills-generated/write-story-<slug>_vN+1.json` (copy of vN metadata + `parent_version`, `changes`).

### Step 4 - Re-generate script
- Run the patched skill on the SAME `input.json` + the `script`-scope edits.
- Save `script_vK+1.md` + `.json`.
- Show user a diff summary: what changed vs vK and which feedback item caused it.

### Step 5 - Log iteration
Append to `iterations.json`:
```json
{
  "round": 2,
  "timestamp": "2026-10-01T14:30:00Z",
  "skill_version_before": "v1",
  "skill_version_after": "v2",
  "script_before": "script_v1.md",
  "script_after": "script_v2.md",
  "feedback_raw": "tone too formal, rename the dog to Max",
  "items": [
    {"text": "tone too formal", "scope": "rule", "section": "Tone & Voice", "change": "formality: formal -> casual"},
    {"text": "rename the dog to Max", "scope": "script", "change": "dog name -> Max"}
  ],
  "status": "awaiting_review"
}
```

### Step 6 - Ask for next review
End every round with:
```
Script vK+1 ready: data/scripts/<slug>/<session-id>/script_vK+1.md
Skill now vN+1.
Next: give feedback, or `/refine-skill <slug> --approve` to finalize.
```

## Finalize (`--approve`)

1. Copy latest script -> `final.md` + `final.json`.
2. Set `stable_version: vN` in live SKILL.md frontmatter and in `write-story-<slug>_vN.json` (`"stable": true`).
3. Append `{"round": ..., "status": "approved", "final_script": "final.md"}` to `iterations.json`.
4. Tell user next step:
   ```
   /script-to-shotlist data/scripts/<slug>/<session-id>/final.md
   ```

## Rules

- Never overwrite `versions/SKILL_vN.md` or `script_vK.md`.
- One patch per round. Do not stack unreviewed changes.
- Feedback that contradicts the DNA (e.g. "make it 16:9" on a 9:16 series) -> apply, but note the drift in changelog.
- Script-only feedback never touches the skill.
- Free-form feedback in any language (Vietnamese ok). Write rules into SKILL.md in English.
