---
name: dialogue-polish
description: |
  Rewrite the dialogue and voiceover of a series session so it is clear, natural spoken Vietnamese
  (or the screenplay's language): no riddle lines, no telegraphic noun fragments, fixed xung ho per
  character pair, world terms explained once, particles and rhythm of real speech. Changes ONLY
  dialogue text (and delivery), never scenes, timing, actions or IDs; writes the next episode
  versions plus a before/after list. Learns from lines reviewers edited by hand
  (data/dialogue_examples.json). Triggers on: "polish dialogue", "lam ro thoai", "thoai kho hieu",
  "thoai toi nghia", "sua thoai", "dialogue unclear". Input: --session <dir> [--episodes 3,4].
---

# Dialogue Polish

Guide: `references/vi-dialogue.md` (read it first, every time). It overrides the style skill's
word caps and "ambiguous line" rules; it keeps the style's intent (tension, short lines, VO that
undercuts).

```bash
/dialogue-polish --session data/series/<slug>/<session-id>                # every episode
/dialogue-polish --session data/series/<slug>/<session-id> --episodes 3,4
```

## Steps

1. Read: `references/vi-dialogue.md`; latest bible (`cast[].voice`, `address_matrix`, `glossary`);
   outline; the style skill `write-series-<slug>/SKILL.md` (Tone & Voice section); and
   `data/dialogue_examples.json` if it exists: the newest 40 `before -> after` pairs are how THIS
   reviewer rewrites lines. Imitate their choices (word choice, length, particles, pronouns).
2. `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session> [N...]` -> flagged lines.
   The lint is a hint list; also fix unflagged lines that fail the guide's one test.
3. Bible first, only if missing: when the bible has no `address_matrix` or `glossary`, write
   `bible_vK+1` that adds them (and rewrites `voice.style` / `sample_lines` into the guide's terms).
   Nothing else in the bible changes.
4. For each episode (latest version; `final/epNN.json` if newer; skip produced/canon episodes):
   - Rewrite only `dialogue[].line` (and `delivery` if needed). Keep every scene, beat, time,
     shot, action, `loc_id`, `cast`, character IDs, `voiceover` flags. Do not add or remove beats.
     A line may move to a neighbour beat of the same scene only when it no longer fits.
   - Fit: spoken words <= beat duration x 3.5 (VO may run over the next beat of the same scene).
     Keep the episode's total words within +-15% of before.
   - Keep the meaning and the plot information of every line; clarity may ADD the missing piece
     (who / what / why) but never a new plot fact. Mystery answers stay hidden.
   - Same xung ho as `address_matrix` everywhere; VO one pronoun all season.
   - Write `episodes/epNN_vK+1.json` + `.md` (same md layout as the episode it replaces) with
     `"edited": {"by": "dialogue-polish", "at": ISO, "from_version": K}`.
5. Re-run the lint; then `python3 .claude/skills/story-contract/_story_check.py <session>` and, when
   `assets/` exists, `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>` -> 0 errors.
6. Write `dialogue/polish_vN.json` (N = next free): `{"created_at", "episodes": [3, 4],
   "files_written": [...], "changes": [{"episode": 3, "scene": "SC2", "character": "char_01",
   "voiceover": true, "before": "...", "after": "...", "why": "telegraphic | riddle | pronoun |
   term | calque | referent | clock | other"}], "bible_added": ["address_matrix", "glossary"]}`.
7. Append to `iterations.json`: `{"round", "timestamp", "stage": "dialogue_polish",
   "feedback_raw": "làm rõ thoại tập ...", "files_written", "status": "awaiting_review"}`.
   Update `series.md` if it exists.
8. Reply: lines changed per episode, 5 representative before/after pairs.
