---
name: refine-skill
description: |
  Human-in-the-loop feedback loop for a generated write-series-<slug> skill and
  its series session (bible, season outline, episode screenplays). User reviews,
  gives feedback (any language); feedback that generalizes patches the skill
  (new version), story-only feedback edits just this series; affected outline or
  episodes are re-generated. Approve the outline to unlock episode writing,
  approve the season to finalize. Triggers on: "refine skill", "feedback on
  outline", "fix episode 3", "adjust tone", "sua tap", "approve outline",
  "approve series", "finalize". Input: slug + feedback, or --approve.
---

# Refinement Loop (Human in the Loop)

## When to Use

After `/write-series-<slug>` produced an outline or episodes and the user reviewed them.

```bash
/refine-skill <slug> --feedback "outline: twist comes too late, move the brother reveal to ep 7"
/refine-skill <slug> --approve outline        # unlocks Stage 3 (episodes)
/refine-skill <slug> --feedback "ep03: too much VO; all eps: cliffhangers too similar"
/refine-skill <slug> --approve                # season final
```

`--session <id>` picks a session; default = latest in `data/series/<slug>/`.

## Paths

```
.claude/skills/write-series-<slug>/
├── SKILL.md                      # live (frontmatter `version: vN`)
├── references/
└── versions/SKILL_vN.md          # immutable snapshots

data/series/<slug>/<session-id>/
├── input.json                    # user idea + options, reused every round
├── adaptation.md
├── bible_vK.md / .json
├── outline_vK.md / .json
├── canon_vK.md / .json           # /continue-series: produced videos reconciled with scripts
├── episodes/epNN_vK.md / .json   # each episode versioned on its own
├── assets/assets_vK.md / .json   # /series-assets: faces, outfits, locations, props, scene map
├── series.md                     # index of latest episode versions
├── iterations.json               # full feedback history
└── final/                        # on --approve: bible.md, outline.md, epNN.md/.json, series.md

data/skills-generated/write-series-<slug>_vN.json
```

## Loop

### Step 1 - Load state
- Live SKILL.md + version N; session files; `iterations.json`; stage (`outline` if no approved
  outline yet, else `episodes`).
- No session -> ask which one. Do not guess. (Headless/web runs always pass `--session`.)

### Step 2 - Classify feedback
Split into items. Each item gets a **scope** and a **target**:

| Scope | Meaning | Action |
|---|---|---|
| `rule` | Applies to every future series ("cliffhangers too similar", "less VO") | Patch SKILL.md AND re-generate targets |
| `story` | Only this series ("move the reveal to ep 7", "rename Tuan") | Edit bible/outline/episodes only |

Target: `bible` | `outline` | `epNN` | `all_episodes` | `assets`.

Looks feedback ("Linh's jacket is red", "the kitchen is its own room", "Vũ's face rounder") is
`story` scope, target `assets`: run `/series-assets --session <dir> --feedback "<items>"`, then
re-write only the episodes whose scenes the change touches (lint tells which).

Rule items -> SKILL.md section:

| Feedback | Section |
|---|---|
| season shape, reveal timing, act balance | Story Template |
| episode shape, length, hook/cliffhanger | Episode Template / Hook Patterns |
| world devices | Story Bible |
| characters, roles, screen share, voice | Character Bible |
| narration, exposition, POV | Storytelling Rules |
| shot length, rhythm | Pacing Guidelines |
| tone, dialogue | Tone & Voice Guidelines |
| camera, color | Visual Guidance |
| music, sfx, silence | Sound Guidance |

Ambiguous item -> one short question. Headless ("Run non-interactively"): pick the most reasonable
reading, apply it as `story` scope (never a rule change on a guess), and log the reading in the round's `items[].note`.

### Step 3 - Patch skill (only if any `rule` item)
1. Copy live SKILL.md -> `versions/SKILL_vN.md` (if missing).
2. Edit only the hit sections. Everything else byte-identical.
3. Bump `version: vN+1`; changelog line `- vN+1 (<ISO>): <one line per change>`.
4. Parse the YAML frontmatter to validate it.
5. Write `write-series-<slug>_vN+1.json` (vN metadata + `parent_version`, `changes`).

### Step 4 - Re-generate only what is affected
- Bible change -> update bible vK+1; flag episodes whose content depends on it.
- Outline change -> outline vK+1; list episodes whose beats moved; if episodes already exist,
  re-write only those (ask first if more than 5; headless: re-write them all and list them in the reply).
- Episode change -> epNN vK+1 for the targeted episodes; keep neighbors consistent (check the
  episode before and after for continuity).
- Every re-written episode follows `.claude/skills/series-assets/references/episode-contract.md`
  when the session has `assets/`: `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>`
  -> 0 errors. If an episode added `new_assets` or the bible changed a look, run `/series-assets`
  after the round (new assets version).
- Story contract (`.claude/skills/story-contract/references/story-contract.md`): every round
  ends with `python3 .claude/skills/story-contract/_story_check.py <session>` (`--stage outline`
  before episodes exist) -> 0 errors; fix what fails in the same round (next file versions).
  Feedback that would break the contract (e.g. "no ending", "leave everything open") -> apply it
  to episodes 1..N-1 only and say so in the change summary.
- Scenes with a minor on screen follow `.claude/skills/story-contract/references/minors-on-screen.md` (also when the
  feedback asks for a new scene); `_action_lint.py` `minor_risk` = 0.
- Rewritten beats keep or write `acting` / scene `blocking` per
  `.claude/skills/action-polish/references/screen-action.md` (a changed line gets matching hands and
  face; unchanged beats keep theirs); run `python3 .claude/skills/action-polish/_action_lint.py lint <session> <NN...>`.
- Rewritten dialogue follows `.claude/skills/dialogue-polish/references/vi-dialogue.md`; run
  `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session> <NN...>` on rewritten episodes.
- Run the skill's Self-check on everything re-generated. Update `series.md`.
- Show a change summary: file -> what changed -> which feedback item.

### Step 5 - Log
`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to `rounds` (older sessions hold a plain list: append to that list; never replace the file's other rounds). The round:
```json
{
  "round": 3, "timestamp": "ISO 8601", "stage": "episodes",
  "skill_version_before": "v1", "skill_version_after": "v2",
  "feedback_raw": "...",
  "items": [{"text": "...", "scope": "rule", "target": "all_episodes", "section": "Hook Patterns", "change": "..."}],
  "files_written": ["outline_v2.md", "episodes/ep07_v2.md"],
  "status": "awaiting_review"
}
```

### Step 6 - Ask for next review
```
Updated: <files>. Skill now vN (or unchanged).
Next: more feedback, `/refine-skill <slug> --approve outline` (stage outline), or `--approve` (season).
```

## Approve

- `--approve outline`: mark the latest outline approved in `iterations.json`; then run Stage 3 of
  `/write-series-<slug>` on this session (episodes). Write ONLY the episodes that have no file yet:
  episodes marked `PRODUCED (canon)` in the outline (series continued with `/continue-series`) and
  episodes already written are never rewritten. New episodes must match the latest `canon_vN.json`
  when one exists (characters as seen on screen, revealed facts, open threads).
- `--approve` (all episodes exist): run `_story_check.py <session>` first; errors -> fix them
  before finalizing. Then copy latest bible, outline, every episode (md + json) and
  series.md into `final/`, plus the latest `assets/assets_vN.json/.md` as `final/assets.json/.md`
  (run `/series-assets` first if it is missing or older than the latest episode); set `stable_version: vN` in SKILL.md frontmatter and `"stable": true` in
  the metadata JSON; log `{"status": "approved"}`. Next step (optional):
  `/script-to-shotlist data/series/<slug>/<session-id>/final/ep01.md` (or the whole `final/` dir).

## Rules

- Never overwrite `versions/SKILL_vN.md` or any `*_vK` file; always write vK+1.
- One patch per round; no stacked unreviewed changes.
- Feedback that contradicts the DNA -> apply, note the drift in the changelog.
- Story-only feedback never touches the skill.
- Feedback in any language; rules in SKILL.md in English; screenplay language = the user's idea language unless told otherwise.
