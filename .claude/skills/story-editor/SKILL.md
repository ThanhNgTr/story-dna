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
3. `python3 .claude/skills/story-editor/_editor.py next <session>` prints N; write
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

Speed matters here: do not explore the session tree (`ls -R`, `iterations.json`, how files are
named). The plan script resolves every source and target file; read only what it names.

1. Plan: `python3 .claude/skills/story-editor/_editor.py plan <session> [F1,F3|all]` (none given =
   `high` + `medium`). It writes `editor/apply_plan.json`: chosen findings, `docs` (bible/outline:
   source -> target), `episodes` (n: source -> target + findings), `packages` (episode groups for
   subagents), `skipped` (produced/canon episodes, never rewritten). Read it and the review.
2. Docs + decisions (you, before any episode): read the bible/outline sources, write their targets
   (`bible_vK+1.json` + `.md`, `outline_vK+1.json` + `.md`; md = copy the previous md and edit the
   changed passages). Then write `editor/apply_notes.json`, the contract every episode writer follows:
   `{"F1": {"decision": "what changes in the story, concretely (names, facts, lines)",
   "episodes": {"8": "exact change in ep08: scene, beat, new line/action", "10": "..."}}, ...}`.
   Cross-episode facts (a clue planted in ep08 and paid off in ep10) are fixed HERE, word for word,
   so parallel writers stay consistent.
3. Episodes, in parallel: when `packages` has 2+ entries, send ONE message with one
   `general-purpose` Agent call per package (they run at the same time). Each prompt gives: the
   session dir, `editor/apply_plan.json` + its package number, `editor/apply_notes.json`, the
   review path, the NEW bible/outline paths, `.claude/skills/write-series-<slug>/SKILL.md`,
   `.claude/skills/series-assets/references/episode-contract.md`,
   `.claude/skills/dialogue-polish/references/vi-dialogue.md`,
   `.claude/skills/story-contract/references/minors-on-screen.md` (a fix never adds a night / sleep / touching / secret-phone scene with a child),
   `.claude/skills/action-polish/references/screen-action.md` (new or changed beats carry `acting`,
   scenes `blocking`), and the rules of step 4. Each writer:
   reads only its episodes' sources, applies only the notes for its episodes, writes the targets,
   renders md with `python3 .claude/skills/story-editor/_editor.py render <target.json>...`, runs
   `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session> <NN...>` and (when
   `assets/` exists) `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>`, fixes,
   and replies with one line per episode (what changed, lint result). One package: do it yourself.
4. Rules for every rewrite: write NEXT versions only (the plan's targets); never overwrite a
   `*_vK` file. Episodes in `final/` stay; the new draft is newer and the app shows it. Keep
   everything a finding does not touch identical in meaning (same scenes, timings, IDs). Episodes
   keep the style skill's rules, timecodes summing to the episode length, the episode contract
   (scene `loc_id`, `cast`...) and the dialogue rules. Produced episodes (canon) are never rewritten.
5. Check (you, after all writers replied): `python3 .claude/skills/story-contract/_story_check.py
   <session>` -> 0 errors, and when `assets/` exists `python3 .claude/skills/series-assets/_assets.py
   lint <session>` -> 0 errors. Fix what fails yourself (small edits to the targets, re-render md).
6. Write `editor/applied_vN.json`: `{"review": "review_vN.json", "applied": ["F1", ...],
   "skipped": [{"id": "F7", "reason": "..."}], "files_written": [...], "created_at": "..."}`
   (plus the plan's `skipped`).
7. Log the round (`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to `rounds` (older sessions hold a plain list: append to that list; never replace the file's other rounds)): `{"round", "timestamp", "stage": "story_editor", "feedback_raw":
   "apply F1,F2", "items": [{"text": <problem>, "scope": "story", "target": <file>, "change": <fix>}],
   "files_written", "status": "awaiting_review"}`.
8. Update `series.md` if episodes changed. Reply: what changed per file, what was skipped and why.

Editor findings are `story` scope (this series only). A finding that is really a style rule
problem goes in the reply as a suggestion for `/refine-skill`, not into the skill.
