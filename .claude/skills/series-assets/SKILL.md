---
name: series-assets
description: |
  Build the asset registry of a series session so every episode shows the same faces,
  costumes, places and props: characters (fixed face/hair/body + wardrobe per episode),
  locations (canonical sets with layout, fixed elements and day/night variants), key props,
  a scene map (every scene -> loc_id + variant + outfit per character) and a continuity
  report of drift found in the scripts. Text only; reference images come later. Each
  run writes a new version (assets_vN). Triggers on: "asset registry", "character sheet",
  "wardrobe", "costume continuity", "location bible", "quan ly nhan vat", "quan ly boi canh",
  "trang phuc", "dong nhat giua cac tap". Input: --session <dir>.
---

# Series Asset Registry

## Input

| Field | Meaning |
|---|---|
| `--session <dir>` | `data/series/<slug>/<session-id>/` with a bible (episodes optional) |
| `--feedback "<text>"` | Optional: user corrections (e.g. "Linh đổi áo ở tập 6", "bếp là phòng riêng") -> new version |

## Why

Episodes are written one at a time, so the same room gets five names and nobody tracks what a
character wears. Image/video generation then draws a new face and a new room every shot. The
registry is the single source for looks: scripts refer to IDs, prompts copy the registry text.

Two moments:
- **Before episodes** (end of `write-series-<slug>` Stage 2): bible + outline only. Looks are
  fixed before anyone writes a scene; Stage 3 writes against them (`references/episode-contract.md`).
- **After episodes** (end of Stage 3, after a refine round or `/continue-series`, or for a series
  written before this skill existed): adds the scene map, absorbs `new_assets`, reports drift.

## Steps

Commands are written out in full (headless runs only allow commands that start with `python3`, and
shell variables do not carry over between calls). `<session>` = the session dir.

1. `python3 .claude/skills/series-assets/_assets.py scan <session>` -> `<session>/assets/_scan.json`; `python3 .claude/skills/series-assets/_assets.py next <session>` -> N.
   Read `_scan.json` (bible cast + world, every scene with raw location, characters, lighting,
   beat actions). If `canon` is set, read `<session>/<canon>` too: looks AS SEEN on produced video win
   over the scripts. If `prev_assets` is set, read it and keep its IDs stable; apply `--feedback`.
   If `outline` is set, read it for planned look changes (injury, disguise, time skip).
   No episodes in the scan -> bible-only registry (schema.md rules): no scene_map, no issues
   except contradictions inside the bible/outline.
   Read an episode file directly only when a scene in the scan is ambiguous.
2. Write `<session>/assets/assets_vN.json` following `references/schema.md`:
   - **characters**: one per bible cast member. Split `visual_signature` into face / hair /
     body / signature props. Fill what the script implies; anything you add to make the face
     drawable goes in `inferred`. `invariants` = what must never change. `prompt_en` describes
     the person WITHOUT clothes-specific text.
     Faces must not read as a beauty template: never stack glamour adjectives ("fair smooth skin, small
     oval face, large round eyes, slim nose, pink lips"); give every face at least two ordinary,
     distinctive features (a mole, freckles, a slightly crooked tooth, uneven brows, a wide nose bridge,
     a chipped front tooth, acne marks, heavy eyelids). An idol-like face makes video tools (Google
     Flow) refuse every clip with that character as a "famous person", and is less memorable on screen. Each outfit has its own `prompt_en`.
     Characters under 18 (`age` < 18): `prompt_en` names age, hair and one signature item only (a
     schoolbag, a hair clip, a toy; never a phone or other device), no body or face-shape words
     (skinny, small, slim, tanned skin, lips, mouth); their outfits are full
     clothing (school uniform, T-shirt + long trousers), no shorts, sleeveless tops, sleepwear or bare
     feet. Video tools (Google Flow) refuse clips that describe a child's body ("harmful content
     involving minors"); see script-to-shotlist "Minors".
     A new face (character sheet re-made after a refusal) means every outfit image made from the old
     sheet is outdated: `python3 -m app.pipeline.assets plan` lists them again and packages attach the
     new sheet until the new outfit images are approved (ep06 was refused for an outfit with the old face).
     Items with `prompt_stale: true` were edited by hand: rewrite their `prompt_en` from the Vietnamese
     fields (see references/schema.md) and drop the flag.
   - **wardrobe**: read every beat action that mentions the character. Default outfit from the
     bible; add an outfit only where the script shows a change (wet, torn, bloody, jacket off,
     flashback, uniform swap). Record `when`.
   - **locations**: cluster the `location_strings`. Bible locations keep their `bible_id`.
     Sub-areas of one set stay one location (put them in `layout`); a room with its own look
     (e.g. kitchen, basement machine room) becomes its own `loc_id` with `parent`. Every alias
     goes in `aliases`. Variants come from `time_of_day` + scene lighting.
   - **props**: objects that recur or carry plot (scratched text, keys, cards, devices). Text on
     them verbatim.
   - **scene_map**: EVERY scene in the scan. On-screen characters get an outfit; voice-only get
     nothing; seen only in a photo/card/screen or only named -> `referenced`. List the props seen
     in each scene (search beat actions case-insensitively, aliases included).
   - **issues**: drift you found. Examples: one place with conflicting descriptions, a bible ID
     used for the wrong room, a costume that changes with no reason, a prop that changes look,
     a scene location that contradicts the action. Each has a concrete `fix`.
3. `python3 .claude/skills/series-assets/_assets.py validate <session> <session>/assets/assets_vN.json`. Fix every ERROR and re-run until it
   passes. Fix WARNs on `outfit.episodes` / `prop.episodes`; any other WARN that stays gets its
   reason in that scene's `note`.
4. `python3 .claude/skills/series-assets/_assets.py render <session>/assets/assets_vN.json` -> `assets_vN.md`.
5. Log the round: `iterations.json` is `{"session", "slug", "rounds": [...]}`: append one object to `rounds` (older sessions hold a plain list: append to that list; never replace the file's other rounds): `{round, timestamp, stage: "assets",
   feedback_raw, items, files_written}`. Missing file -> create `{"session", "slug", "rounds": [<this round>]}`.
6. Report: counts (characters, outfits, locations, props, scenes), the high-severity issues,
   and the paths. Do not edit episodes or the bible here; the issues list says what to change.

## Rules

- Never overwrite an existing `assets_vK.json/.md`; always a new N.
- Evidence: every face/outfit/location detail cites `bible.*` or `epNN.SCx.bY`; else `inferred`.
- Keep IDs stable across versions (`char_*` from the bible; `loc_*`, `prop_*`, outfit IDs from
  the previous version). Removed items stay out; never reuse their IDs.
- Do not soften the story: no gore, injuries or ages changed in descriptions. Content limits of
  image tools are handled when images are made, not here.
- This skill writes no images. Reference images are made from the registry by
  `python3 -m app.pipeline.assets generate --session <dir>` (Codex) or the web app, into
  `assets/characters|locations|props/` + `assets/images.json`. Keep IDs stable so they stay linked.
