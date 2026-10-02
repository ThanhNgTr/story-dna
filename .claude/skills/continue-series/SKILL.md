---
name: continue-series
description: |
  Continue a series after some episodes were already produced as videos. Reads the
  analysis of the produced videos (dna.json + story.md from /analyze-videos) as
  CANON, reconciles it with the series' scripts when they exist (what is on screen
  wins), updates the series bible, and writes the outline for the next episodes in
  the style of a write-series-<slug> skill: either following the remaining old outline
  (adapted to what changed on screen) or as a new arc. Stops for review; episodes are
  then written by the style skill's Stage 3. Works for series written in this project
  and for series produced elsewhere (no scripts). Triggers on: "continue the series",
  "write the next episodes", "viet tiep series", "hoc video da lam roi viet tiep".
---

# Continue a Series from Produced Videos

## Input

| Field | Meaning |
|---|---|
| `--session <dir>` | Series session dir (`data/series/<slug>/<session-id>/`). May contain bible/outline/episodes (series written here) or only `input.json` (produced elsewhere) |
| `--canon-mode full\|transcript\|none` | How the produced videos were checked (cheapest first: none < transcript < full) |
| `--canon <dna.json>` | full: analysis of the produced videos (`story.md`, `dna.md`, `manifest.json` next to it) |
| `--transcripts <manifest.json>` | transcript: WhisperX transcripts of the produced videos (no frames were analyzed) |
| `--diff <script_diff.json>` | transcript + series has scripts: local line-by-line diff (same / changed / cut / added) from `_script_diff.py` |
| `--notes <file>` | none (or any mode): the user's notes on what changed during production |
| `--style write-series-<slug>` | The style skill. Read its SKILL.md and `references/` before writing |
| `--produced <k>` | Episodes 1..k are produced and on screen |
| `--direction follow\|new-arc` | follow = finish the remaining old outline, adapted to canon; new-arc = a new arc after episode k |
| `--new-episodes <m>` | Write the outline for episodes k+1..k+m |
| `--idea-file <path>` | Optional: the user's ideas for what comes next |

## Why canon first

Produced videos drift from scripts: scenes get cut, lines change, actors improvise, a prop or a
costume differs. Viewers only know what was on screen, so the next episodes must connect to the
VIDEO, not to the script. When the video and the script disagree, the video wins. When the video
is silent on something the script established, the script fact still stands, marked `script-only`.

## Steps

Find the next free version numbers in the session dir (`canon_vN`, `bible_vN`, `outline_vN`) and
never overwrite an existing file.

### C1 — Canon reconciliation → `canon_vN.md` + `canon_vN.json`

Use only what the mode provides — do not go looking for frames or videos in cheaper modes:
- `full`: steps 1-5 below from the canon DNA.
- `transcript` with `--diff`: the scripts are canon EXCEPT where the diff says otherwise. Use `changed`
  (what was actually said), `cut` (scripted line not said: the information it carried may be missing
  on screen) and `added` (new lines on screen) to correct the canon; read transcript text around a
  difference only when its meaning is unclear. Visuals are assumed as scripted (`assumptions`).
- `transcript` without scripts (series produced elsewhere): build the canon from the transcript
  text (who says what, events told in VO/dialogue). Visual signatures are unknown: mark them
  `unknown (no frames analyzed)` so the bible flags them for the user.
- `none`: the scripts are canon, corrected by `--notes` if given.

1. Map produced videos to episodes: `manifest.json` `sources` are in episode order (one file per
   episode). One long video holding several episodes: split by title cards, recap/opening
   sequences and the timeline; state how you split it.
2. Per produced episode, from the canon DNA (`plot_timeline`, scenes, dialogue, on-screen text):
   what happened on screen, key lines (verbatim), who appeared.
3. If the session has scripts (`episodes/epNN_v*.md`, latest version, or `final/epNN.md`):
   diff script vs screen per episode — scenes added / cut / changed, lines changed, reveals moved,
   characters added / dropped, look or name changes. Rate each difference `minor` or `story`
   (changes what later episodes can rely on).
4. Canon state after episode k: characters (name, visual signature AS SEEN — this is what later
   production must match, relationships, what each one knows/wants now), facts revealed, world
   rules shown, open questions (where opened, clues so far), threads left hanging, new elements
   the video introduced that the scripts did not have.
5. `canon_vN.json`: `{produced_upto, episodes: [{episode, source, summary, key_lines, differences:
   [{type, script, screen, impact}]}], characters: [...], revealed: [...], open_questions: [...],
   threads: [...], new_elements: [...], assumptions: [...]}`.

### C2 — Bible → `bible_vN.md` (+ `.json`)

Update the latest bible with canon (video wins). External series (no bible yet): build the bible
from canon + the style skill's Story Bible / Character Bible templates. Add a short "Changed from
previous bible" list at the top.

### C3 — Outline → `outline_vN.md` (+ `.json`)

- Episodes 1..k: one row each, marked `PRODUCED (canon)` with a one-line on-screen summary. Do not
  rewrite them.
- Episodes k+1..k+m, in the style skill's outline format (title, logline, beats, Story Template
  beats carried, reveal/clue, cliffhanger type, characters):
  - `follow`: take the remaining episodes of the old outline; keep their beats where canon allows;
    list every adaptation forced by canon ("ep 7 planned the brother reveal, but ep 4 on screen
    already showed his face → ep 7 now reveals why he hid").
  - `new-arc`: a new arc after episode k. Re-map the style skill's Story Template % positions onto
    the new episodes; pay off at least one canon open question early, open new ones; use the
    user's idea file when given.
  - Both: the first new episode picks up exactly where episode k ended on screen (its last scene,
    cliffhanger, emotional state).
- Self-check: canon respected (no contradiction with `canon_vN.json`), style skill's Self-check
  items that apply to an outline, continuity of names and visual signatures.

Then STOP for review. Do not write episode screenplays here: after approval, the style skill's
Stage 3 writes only the missing episodes (k+1..k+m).

## Rules

- Video wins over script; script-only facts stand unless the video contradicts them.
- Never copy content from the style skill's reference story; use its patterns only.
- Language: same as the existing series / the produced videos' dialogue.
- Mark assumptions (episode mapping, uncertain speakers, unclear on-screen text) instead of guessing silently.
- Never overwrite versioned files; always write the next version.
