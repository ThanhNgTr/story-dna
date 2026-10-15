---
name: action-polish
description: |
  Add and sharpen what characters physically DO in every shot of a series session: per beat, for
  every visible character (listener included), the body and hand action, the face, and what is in
  their hands (tay run run rot tra, cam am tra, siet vat ao), plus each scene's blocking (who stands
  where). Keeps objects in hand from beat to beat. Changes ONLY action / acting / blocking, never
  dialogue, timing, shots or IDs; writes the next episode versions plus a change list. Triggers on:
  "add acting", "action lines", "bo sung dien xuat", "nhan vat dang lam gi", "mieu ta hanh dong",
  "tay chan nhan vat", "chua co hanh dong". Input: --session <dir> [--episodes 3,4].
---

# Action Polish

Guide: `references/screen-action.md` (read it first, every time). Episodes then carry, per beat,
`acting: [{character, does, face, holds}]` and, per scene, `blocking`.

```bash
/action-polish --session data/series/<slug>/<session-id>                # every episode
/action-polish --session data/series/<slug>/<session-id> --episodes 3,4
```

## Steps

1. Read: `references/screen-action.md` and `.claude/skills/story-contract/references/minors-on-screen.md` (a child on screen:
   no sleep, bed, touching, mouth habit, secret phone; `minor_risk` must reach 0); latest bible (`cast[]`: role, `tell`, `flaw`, `secret`,
   relationships); latest outline (what each episode turns on); the style skill
   `write-series-<slug>/SKILL.md` (body tells, character building, camera / shot sizes); the latest
   `assets/assets_vN.json` if it exists (props with names, locations with fixed elements: that is
   what hands can touch).
2. `python3 .claude/skills/action-polish/_action_lint.py lint <session> [N...]` -> flagged beats and
   coverage per episode. The lint is a hint list; also fix unflagged acting that fails the guide's
   one test.
3. For each episode (latest version; `final/epNN.json` if newer; skip produced/canon episodes):
   - Add `blocking` to every scene with 2+ characters on screen, and `acting` to every beat, one
     entry per visible character (beat `characters` in scene `cast`). Rewrite existing `acting` that
     fails the guide.
   - `action` may be tightened so it holds the frame / event only and does not repeat `acting`; it
     keeps every story fact it had (who enters, what is shown, text on a screen).
   - Never change: `dialogue` (lines, delivery, speaker, `voiceover`), times, shot sizes, `camera`,
     `lighting_color`, `sound`, `characters`, scene IDs, `loc_id`, `variant_id`, `cast`, `props`,
     ledger. Do not add or remove beats or scenes.
   - The action plays the line's subtext, never a new plot fact: a hidden secret stays hidden (a
     character may hide a thing, not reveal it early).
   - Objects: use the scene `props` and the location's fixed elements first. An everyday object that
     fits the place (chén trà, khay, chổi) may be added in `holds` / `does` as plain words; a NEW
     story-relevant prop goes in `new_assets` with `prop_new_N` (episode-contract.md).
   - Keep held objects continuous through the scene (guide rule 5); carry the state of a body or an
     outfit (ướt, trầy tay) only where the script already set it.
   - Write `episodes/epNN_vK+1.json` with `"edited": {"by": "action-polish", "at": ISO, "from_version": K}`,
     then `python3 -m app.pipeline.screenplay render <session> <NN>` writes the matching `.md`.
   - More than 4 episodes: one general-purpose subagent per 3-4 episodes, in parallel; give each this
     SKILL.md path, the guide path, the bible / outline / registry paths and its episode numbers.
4. Re-run the lint: `missing`, `prop_vanish`, `no_blocking` = 0 for the episodes written. Then
   `python3 .claude/skills/story-contract/_story_check.py <session>` and, when `assets/` exists,
   `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>` -> 0 errors.
5. Write `action/polish_vN.json` (N = next free): `{"created_at", "episodes": [3, 4],
   "files_written": [...], "coverage_before": {"3": 0}, "coverage_after": {"3": 100},
   "examples": [{"episode": 3, "scene": "SC2", "beat": 4, "character": "char_01",
   "line": "<the line said in that beat, or null>", "before": "<old action>", "after": {"does", "face", "holds"}}]}`
   with 5-10 representative examples per episode.
6. Log the round (`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to
   `rounds` (older sessions hold a plain list: append to that list; never replace the file's other
   rounds)): `{"round", "timestamp", "stage": "action_polish", "feedback_raw": "bổ sung diễn xuất tập ...",
   "files_written", "status": "awaiting_review"}`. Update `series.md` if it exists.
7. Reply: coverage before -> after per episode, 5 representative beats (line + what the hands / face do).
