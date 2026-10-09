---
name: story-editor
description: |
  Script editor pass over a series session (bible, outline, episodes): judges story DEPTH, not
  just structure — theme, protagonist wound/need/choices, supporting cast functions, antagonist
  motive, dialogue subtext and distinct voices, setup/payoff and fair twists, rising stakes,
  emotional moments and scene turns, originality vs cliches. Scores 9 dimensions 1-5 with quoted
  evidence, lists concrete findings with fixes (review mode), then applies the chosen fixes as
  new file versions (apply mode). Triggers on: "story editor", "bien tap kich ban", "chieu sau",
  "review the script", "make the story deeper", "nhan vat mong", "thoai nhat".
  Input: --session <dir> [--apply [F1,F3|all]].
---

# Story Editor

Rubric: `references/rubric.md` (read it first, every time).
Runs after the story contract (`.claude/skills/story-contract/`): the contract says the parts
exist, the editor says whether they work.

```bash
/story-editor --session data/series/<slug>/<session-id>                 # review
/story-editor --session data/series/<slug>/<session-id> --apply         # apply high + medium findings
/story-editor --session data/series/<slug>/<session-id> --apply F2,F5   # apply chosen findings
```

## Review mode (default)

1. Read: latest `bible_vK.json`, `outline_vK.json`, every latest episode (`episodes/epNN_vK.json`
   or `final/epNN.json` if newer), `input.json` + `idea.md` (the user's idea), `canon_vN.json` if
   any, `story_check.json`, and the style skill `write-series-<slug>/SKILL.md` (its rules are not
   flaws). Stage = `episodes` if episodes exist, else `outline` (judge the plan; dialogue from
   bible sample lines and outline beats, say so in `why`).
2. Score the 9 dimensions with evidence. Find 5-20 findings. Note 3-5 strengths.
3. `N=$(python3 .claude/skills/story-editor/_editor.py next <session>)`, write
   `<session>/editor/review_vN.json` (shape below) and `review_vN.md` (same content for humans:
   score table, findings grouped by severity, strengths).
4. `python3 .claude/skills/story-editor/_editor.py validate <session>/editor/review_vN.json` -> 0 errors.
5. Reply: verdict, average, the 3 most important findings.

Language: `summary`, `why`, `problem`, `fix`, `strengths` and the md in the language of the user's
idea; `evidence` quoted verbatim; keys and enum values in English.

```json
{
  "version": 1, "stage": "outline | episodes", "created_at": "ISO 8601",
  "language": "vi",
  "reviewed": {"bible": "bible_v2.json", "outline": "outline_v2.json", "episodes": {"1": "episodes/ep01_v1.json"}},
  "summary": "3-5 sentences: what the story is about underneath, what works, the one biggest weakness",
  "theme_statement": "the question the story argues, one line",
  "scores": {
    "theme":           {"score": 3, "why": "...", "evidence": ["bible.theme: ...", "ep10 SC3: \"...\""]},
    "protagonist":     {"score": 4, "why": "...", "evidence": []},
    "supporting_cast": {"score": 3, "why": "...", "evidence": []},
    "antagonist":      {"score": 2, "why": "...", "evidence": []},
    "dialogue":        {"score": 3, "why": "...", "evidence": []},
    "setup_payoff":    {"score": 3, "why": "...", "evidence": []},
    "stakes":          {"score": 4, "why": "...", "evidence": []},
    "emotion":         {"score": 3, "why": "...", "evidence": []},
    "originality":     {"score": 3, "why": "...", "evidence": []}
  },
  "average": 3.1, "verdict": "pass | revise",
  "setup_payoff_map": [{"plant": "...", "plant_ep": 2, "payoff": "... | null", "payoff_ep": 8}],
  "findings": [
    {"id": "F1", "dimension": "antagonist", "severity": "high",
     "where": {"file": "bible_v2.json", "episode": null, "scene": null, "field": "cast[char_04]"},
     "evidence": "motive: \"...\"", "problem": "...", "fix": "...",
     "affects": ["bible", "outline", "ep04", "ep09"]}
  ],
  "strengths": ["..."]
}
```

`average` = mean of the 9 scores (1 decimal). `verdict` = `pass` if every score >= 3 and
average >= 3.5, else `revise`. `affects` = files the fix would rewrite.

## Apply mode (`--apply`)

1. Load the latest `editor/review_vN.json`. Pick findings: the given ids, or `all` = every
   finding, or none given = `high` + `medium`.
2. Plan the edits by file. Bible first, then outline, then episodes. One finding may touch many
   files; several findings may touch one file — apply them together.
3. Write NEXT versions only (`bible_vK+1`, `outline_vK+1`, `episodes/epNN_vK+1`, md + json); never
   overwrite a `*_vK` file. Episodes in `final/` stay; the new draft is newer and the app shows it.
   Keep everything a finding does not touch byte-identical in meaning (same scenes, timings, IDs).
   Episodes keep the style skill's rules, timecodes summing to the episode length, and
   `.claude/skills/series-assets/references/episode-contract.md` (scene `loc_id`, `cast`...).
   Produced episodes (canon) are never rewritten.
3b. Rewritten dialogue follows `.claude/skills/dialogue-polish/references/vi-dialogue.md`
    (`_dialogue_lint.py lint <session> <NN...>`).
4. Check: `python3 .claude/skills/story-contract/_story_check.py <session>` -> 0 errors, and when
   `assets/` exists `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>` -> 0 errors.
5. Write `editor/applied_vN.json`: `{"review": "review_vN.json", "applied": ["F1", ...],
   "skipped": [{"id": "F7", "reason": "..."}], "files_written": [...], "created_at": "..."}`.
6. Append to `iterations.json`: `{"round", "timestamp", "stage": "story_editor", "feedback_raw":
   "apply F1,F2", "items": [{"text": <problem>, "scope": "story", "target": <file>, "change": <fix>}],
   "files_written", "status": "awaiting_review"}`.
7. Update `series.md` if episodes changed. Reply: what changed per file, what was skipped and why.

Editor findings are `story` scope (this series only). A finding that is really a style rule
problem goes in the reply as a suggestion for `/refine-skill`, not into the skill.
