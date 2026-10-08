# Episode contract: writing against the asset registry

Every skill that writes or rewrites episodes (`write-series-<slug>` Stage 3, `/refine-skill`,
`/continue-series` + Stage 3) follows this when `<session>/assets/assets_vN.json` exists.
The registry decides how people, places and props LOOK; the episode decides what they DO.

## Before writing

Read the latest `assets/assets_vN.json` (highest N): characters (face/hair/body, wardrobe with
`when`), locations (name, layout, fixed_elements, variants), props, and `issues` (do not repeat a
logged problem). No registry yet -> run `/series-assets --session <dir>` first.

## In each scene (episode JSON)

```json
{"id": "SC1", "location": "Bếp kính", "loc_id": "loc_03", "variant_id": "loc_03_night",
 "int_ext": "INT", "time_of_day": "night",
 "cast": {"char_01": "char_01_o1", "char_06": "char_06_o1"},
 "referenced": ["char_02"],
 "props": ["prop_04"],
 "beats": [...]}
```

- `location` starts with the registry location `name` verbatim (a sub-area may follow: "Phòng kính
  tầng một — góc bảng điều khiển"). Never invent a new name for a registered place.
- `loc_id` null only for a title card / black screen, with `"loc_reason"`.
- `cast`: every character physically on screen in the scene -> the outfit they wear. Seen only in a
  photo/card/screen, or only named -> `referenced`. Heard only (VO, speaker) -> neither.
- Outfit = the one worn in the previous scene of that character, unless the story changes it on
  screen (gets wet, bloody, changes clothes, time skip). Use the registry outfit whose `when`
  matches.
- `props`: registered props visible in the scene. Text on a prop is copied verbatim from the registry.
- Episode header `characters`: `{"char_01": {"name": "...", "visual_signature": "<bible, verbatim>", "outfits": ["char_01_o1"]}}`.
- In the Markdown screenplay, scene headings carry the IDs:
  `### SC1 [00:00-00:12] INT. BẾP KÍNH — ĐÊM  {loc_03 · char_01:o1, char_06:o1}`.
- Action lines describe what changes (blood, wet, torn), not the base look; the base look lives in
  the registry.

## Something new is needed

A scene needs a place, outfit or prop that is not in the registry: write it with a proposed ID
(`loc_new_1`, `char_03_new_1`, `prop_new_1`) and list it at episode level:

```json
"new_assets": [{"kind": "outfit", "id": "char_03_new_1", "for": "char_03",
                "desc": "...", "why": "soaked after ep05.SC3 rain"}]
```

Then the next `/series-assets` run gives it a real ID and rewrites nothing else.

## After writing

`python3 .claude/skills/series-assets/_assets.py lint <session> <episode numbers>` -> 0 errors.
WARN lines about outfit changes must match a story reason in the script. After a batch of episodes
(Stage 3 end, refine round, continue-series), run `/series-assets --session <dir>`: new version with
the scene map and a fresh continuity report; `new_assets` get real IDs there.
