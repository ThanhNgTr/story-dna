---
name: story-contract
description: |
  Check and fix a series session so it is a complete story: a main plot from start to a
  happy or bad ending, a main character with supporting characters around them, dialogue,
  a clear setting and how it changes, climaxes, and secrets/mysteries that are opened, clued
  and answered. Runs _story_check.py on the bible, outline and episodes, then repairs what
  fails (new file versions only). Used by write-series-<slug>, /refine-skill and
  /continue-series after every outline or episode write. Triggers on: "story check",
  "kiem tra kich ban", "cot truyen day du", "story contract". Input: --session <dir>.
---

# Story Contract

The contract: `references/story-contract.md`. It overrides style rules of any `write-series-<slug>`
skill where they conflict (the style says how, the contract says that the story is complete).

```bash
/story-contract --session data/series/<slug>/<session-id>
python3 .claude/skills/story-contract/_story_check.py <session> [--stage outline|episodes]
```

## Steps

1. Run `_story_check.py <session>`. It writes `<session>/story_check.json` and prints
   `ERROR [Rn] ...` lines (Rn = requirement number in the contract).
2. 0 errors -> report OK (warnings listed, not fixed unless trivial). Done.
3. Errors -> fix them, in this order: bible (R1 ending, R2 main_plot, R3 cast, R5 setting,
   R6 climaxes, R7 ledger) -> outline -> episodes. Fixes are content, not just fields: when the
   season has no ending, write one; when a question is never answered, decide the answer and
   place it; when an episode has no dialogue, write the lines.
   - Write the next version (`bible_vK+1`, `outline_vK+1`, `epNN_vK+1`, md + json); never
     overwrite a `*_vK` file. Keep the user's idea and the style skill's rules.
   - A bible/outline change that moves beats -> re-write only the episodes it touches.
   - Episodes keep `.claude/skills/series-assets/references/episode-contract.md` when `assets/` exists.
4. Re-run `_story_check.py` until 0 errors (max 3 rounds; then list what is left and why).
5. Log the round (`iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to `rounds` (older sessions hold a plain list: append to that list; never replace the file's other rounds)): `{"round", "timestamp", "stage": "story_check", "errors_before",
   "errors_after", "files_written"}`.
