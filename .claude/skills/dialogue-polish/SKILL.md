---
name: dialogue-polish
description: |
  Rewrite the dialogue and voiceover of a series session so it is clear, natural spoken Vietnamese
  (or the screenplay's language): no riddle lines, no telegraphic noun fragments, fixed xung ho per
  character pair, lines that are speech (no word definitions, no VO retelling the shot), particles
  and rhythm of real speech. Changes ONLY
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
     shot, action, `acting`, `blocking`, `loc_id`, `cast`, character IDs, `voiceover` flags. Do not add or remove beats.
     A line may move to a neighbour beat of the same scene only when it no longer fits.
   - Description lines (`definition`, `narrates_action`, guide rules 14-16): the one exception to
     "keep speaker and flag". Such a line may be (a) rewritten as VO that says what the image cannot,
     (b) given to a character who is on screen in that scene (`cast`) as speech to someone there
     (`voiceover: false`), or (c) cut when the shot already shows it. Log the old and new speaker.
   - Fit: the guide's Speech rate (Vietnamese <= 5.0 syllables/s; on-screen lines fit their beat,
     VO may run over cuts inside the scene). `too_fast` lint flags must be 0.
     Keep the episode's total words within +-15% of before (cutting description lines may go lower).
   - Keep the meaning and the plot information of every line; clarity may ADD the missing piece
     (who / what / why) but never a new plot fact. Mystery answers stay hidden.
   - Same xung ho as `address_matrix` everywhere; VO one pronoun all season.
   - A child on screen (minors-on-screen.md "Dialogue"): the first line TO the child in a scene names her
     ("Na! Em nhắn hả?"), because her shots are generated apart from the adults' and cut in.
     A child's line never narrates her secretly using a device; the denial / joke stays (the device is
     shown on the adult side).
   - Write `episodes/epNN_vK+1.json` + `.md` (same md layout as the episode it replaces) with
     `"edited": {"by": "dialogue-polish", "at": ISO, "from_version": K}`.
5. Re-run the lint; then `python3 .claude/skills/story-contract/_story_check.py <session>` and, when
   `assets/` exists, `python3 .claude/skills/series-assets/_assets.py lint <session> <NN...>` -> 0 errors.
6. Write `dialogue/polish_vN.json` (N = next free): `{"created_at", "episodes": [3, 4],
   "files_written": [...], "changes": [{"episode": 3, "scene": "SC2", "character": "char_01",
   "voiceover": true, "before": "...", "after": "...", "why": "telegraphic | riddle | pronoun |
   term | calque | referent | clock | definition | narrates_action | other", "speaker_before"?: "char_01"}], "bible_added": ["address_matrix", "glossary"]}`.
7. Log the round (`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to `rounds` (older sessions hold a plain list: append to that list; never replace the file's other rounds)): `{"round", "timestamp", "stage": "dialogue_polish",
   "feedback_raw": "làm rõ thoại tập ...", "files_written", "status": "awaiting_review"}`.
   Update `series.md` if it exists.
8. Reply: lines changed per episode, 5 representative before/after pairs.
