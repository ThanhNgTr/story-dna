---
name: story-continuity
description: |
  Keep a series logical from the first episode to the last: every episode happens because of an
  earlier event, nobody acts on a fact before they learn it, the dead and the gone stay off screen,
  lost or broken props stay lost, days never run backwards, each episode picks up the previous
  cliffhanger, every planned clue is on screen and every plant is paid off. Builds a state ledger
  (continuity/state_vN.json: facts, who knows what, status, props, relations, clock, clues, setups,
  seams) from the written episodes, checks it with _continuity.py, repairs what breaks, runs a
  logic review (plot holes, coincidences, motives, easier paths) and applies its fixes. Triggers on:
  "continuity", "logic check", "plot hole", "tinh tiet logic", "lien mach", "kiem tra logic",
  "nhan qua", "ai biet gi". Input: --session <dir> [--stage outline|episodes] [--review] [--apply [L1,L3|all]].
---

# Story Continuity

Rules and the ledger shape: `references/continuity.md` (read it first, every time). Runs after the
story contract (`.claude/skills/story-contract/`): the contract says the parts exist, continuity
says they fit together episode after episode.

```bash
/story-continuity --session data/series/<slug>/<session-id>                    # build ledger, check, repair
/story-continuity --session data/series/<slug>/<session-id> --stage outline    # cause chain only
/story-continuity --session data/series/<slug>/<session-id> --review           # logic review
/story-continuity --session data/series/<slug>/<session-id> --apply L1,L4      # apply review findings
python3 .claude/skills/story-continuity/_continuity.py check <session> [--stage outline|episodes]
```

Speed: do not explore the session tree or read full episode JSON to learn the story; the
`digest` and `seams` commands print what you need. Open an episode JSON only to edit it.

## Check + repair (default)

1. `python3 .claude/skills/story-continuity/_continuity.py check <session>` (stage `outline` when
   no episode exists). It writes `<session>/continuity_check.json`; errors are `[Cn]` codes
   (references/continuity.md table).
2. C1 (outline cause chain): write `outline_vK+1.json` + `.md` with `events`, `because`,
   `opens_from` for every episode (md = copy the previous md, add one line per episode:
   "Vì: E3.1 ... -> E5.1 ..."). Fill them from the outline's own beats; when an episode has no
   earlier cause, that is a story problem: give it one (a choice or a discovery in an earlier
   episode) and change the beats of the two episodes so it is on screen. Episodes that exist and
   whose beats changed are rewritten too (step 5).
3. Stage episodes, C0 (no ledger, or it misses episodes): build the ledger.
   - `python3 .claude/skills/story-continuity/_continuity.py digest <session>`: every written
     episode with its file, scenes (time, `loc_id`, cast, props, flashback), actions, what hands
     hold, lines, cliffhanger. Read it once, in order, ep01 -> epN, keeping the state in mind.
   - Facts: every bible `secret`, every `ledger_plan` answer, every event that later scenes depend
     on (who did what, who is whose, world rules). Knowledge: when each character learns each fact
     ON SCREEN (owners of a secret: `ep: 0`). Uses: every line or act that shows a character
     knows a fact. Then status, props (story props only), relations (bible pairs), clock (one row
     per episode), clues (each `ledger_plan` clue_ep), setups (every plant the outline / bible or
     the scenes set up), seams (every written pair; `seams` command below).
   - Record what IS on screen, never what the plan intended. A missing clue gets no row: the
     check then says so and step 5 writes the clue into the episode.
   - `python3 .claude/skills/story-continuity/_continuity.py next <session> state` -> N; write
     `continuity/state_vN.json` (`built_from` = the files the digest names), then
     `python3 .claude/skills/story-continuity/_continuity.py render <session>/continuity/state_vN.json`.
4. Re-run the check. Quote errors (`quote ... not found`, wrong scene) are ledger mistakes: fix the
   row's quote / scene to the real text (next ledger version). Every other error is a STORY break.
   Never delete a `uses` row, move a `knowledge` row earlier or add a `back` / `with` row that no
   scene shows, just to silence the check.
5. Story breaks -> fix the episodes (next versions `epNN_vK+1.json`, md via
   `python3 .claude/skills/story-editor/_editor.py render <target.json>...`):
   - C2 knows too early: the character learns it on screen earlier (a scene or a beat), or the line
     / act moves after the learning, or the character only suspects (the line changes, the fact
     stays hidden).
   - C3 / C4: the scene is a flashback (`"flashback": true`), the return / find is shown, or the
     character / prop leaves the scene.
   - C5: fix the day in the episode that is wrong (scene text, `time_of_day`) and the bible
     `setting_timeline` when it is the plan that is wrong (next bible version).
   - C6 seam: rewrite the first scene of the later episode so its first seconds continue the
     exact moment, line or image of the previous cliffhanger (`seams` command below); a time jump
     is fine only when the cliffhanger's question is answered on screen in that episode.
   - C7: write the missing clue / payoff into the episode the plan names (one beat, a line or an
     object seen), keeping the timing.
   - C8: show the cause (a beat where it happens) or keep the old state.
   Keep everything a fix does not touch identical (scenes, timings, IDs). Episodes keep the style
   skill's rules, `.claude/skills/series-assets/references/episode-contract.md`,
   `.claude/skills/dialogue-polish/references/vi-dialogue.md`,
   `.claude/skills/action-polish/references/screen-action.md` and
   `.claude/skills/story-contract/references/minors-on-screen.md`. Produced episodes
   (`input.json` `produced_upto`, canon) are never rewritten: change the episodes after them.
6. Write the next ledger version for the rewritten episodes (rows and `built_from`), re-run the
   check until 0 errors (max 3 rounds; then list what is left and why). Then
   `python3 .claude/skills/story-contract/_story_check.py <session>` -> 0 errors, and when
   `assets/` exists `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>`.
7. Log the round (`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to
   `rounds` (older sessions hold a plain list: append to that list; never replace the file's other
   rounds)): `{"round", "timestamp", "stage": "continuity", "errors_before", "errors_after",
   "files_written", "status": "awaiting_review"}`. Update `series.md` if episodes changed.

### Seam pass

`python3 .claude/skills/story-continuity/_continuity.py seams <session> [N ...]` prints, for each
written pair, the last beats + cliffhanger of epN-1, the outline `opens_from` and the first beats of
epN. A seam is good when a viewer who just saw the cliffhanger recognises the same moment within
3 seconds (same place, same line or image, same people), or the time jump is named and the
cliffhanger's question is answered inside epN. Fix only the first scene of epN (or the last beat of
epN-1 when epN is produced).

## Logic review (`--review`)

The checker catches bookkeeping breaks; this pass catches what makes a viewer say "that makes no
sense". Read: the latest ledger md (`continuity/state_vN.md`), the `digest`, the bible (`cast`
motives, world rules, `ledger_plan`), the outline, `continuity_check.json`. For episodes not written
yet judge the outline (stage `outline`).

Ask, episode by episode:
- `contradiction`: two scenes say different things (a name, an age, a place, who was there).
- `knowledge`: a character acts as if they know (or forget) something against the ledger.
- `motive`: a choice no one in that position would make, given what they want and know.
- `easier_path`: the problem has an obvious easier solution the character ignores without reason.
- `coincidence`: chance solves a problem or brings people together at the moment the plot needs it.
- `timeline`: travel, healing or news faster or slower than the clock allows.
- `cause_missing`: an event with no cause on screen (the outline `because` points at nothing seen).
- `dropped_thread`: a promise, threat, injury or question raised and never mentioned again.
- `world_rule`: a world rule (bible) broken without a cost or a reason.

Write `continuity/logic_vN.json` (`_continuity.py next <session> logic`) and `logic_vN.md` (the same
for humans, findings by severity), then `_continuity.py validate <session>/continuity/logic_vN.json`
-> 0 errors. Language: `summary`, `problem`, `fix` in the language of the user's idea; `evidence`
quoted verbatim.

```json
{"version": 1, "stage": "episodes", "created_at": "ISO 8601", "language": "vi",
 "reviewed": {"state": "continuity/state_v2.json", "outline": "outline_v3.json", "episodes": {"1": "episodes/ep01_v2.json"}},
 "summary": "2-4 sentences: does the season hold together, the biggest hole",
 "verdict": "pass | revise",
 "findings": [{"id": "L1", "kind": "coincidence", "severity": "high",
               "where": {"file": "episodes/ep07_v1.json", "episode": 7, "scene": "SC2", "field": null},
               "evidence": "ep07 SC2: \"...\"", "problem": "...",
               "fix": "concrete: in ep05 SC3 Linh overhears the time; in ep07 she comes because of it",
               "affects": ["ep05", "ep07"]}]}
```

`verdict` = `revise` when any finding is `high` (breaks the main plot or the ending), else `pass`.
0-15 findings; prefer fewer, bigger fixes. A fix stays inside the user's idea, the style skill, the
story contract and canon. Reply: verdict, the 3 most important findings.

## Apply (`--apply`)

Same machinery as `/story-editor --apply` (read `.claude/skills/story-editor/SKILL.md` "Apply
mode", steps 2-5), on the logic review:
1. `python3 .claude/skills/story-editor/_editor.py plan <session> [L1,L3|all] --review <session>/continuity/logic_vN.json`
   (none given = `high` + `medium`) -> `continuity/apply_plan.json`.
2. Bible / outline targets and `continuity/apply_notes.json` first (cross-episode facts fixed word
   for word), then one `general-purpose` subagent per package in parallel; give each also
   `references/continuity.md` and the latest `continuity/state_vN.md`.
3. Then the default check + repair (steps 3-6 above: new ledger version for the rewritten episodes)
   and `_story_check.py` -> 0 errors.
4. Write `continuity/applied_vN.json`: `{"review": "logic_vN.json", "applied": ["L1"], "skipped":
   [{"id", "reason"}], "files_written", "created_at"}`; log the round (`"stage": "continuity_apply"`).
