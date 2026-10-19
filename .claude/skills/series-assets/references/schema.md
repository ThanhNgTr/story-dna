# assets_vN.json schema

One file per version in `<session>/assets/`. Text in `desc`/`name` fields is in the series language;
`prompt_en` fields are English (image models follow English more reliably).
`prompt_en` is a faithful translation of the Vietnamese fields (`desc`, `layout`, `fixed_elements`, face/hair/
body, `lighting`), never a separate idea: it names every fixed element and says WHERE each one is relative to
the others and how far ("the two-storey villa stands right behind the gate, ~20 m up the path, its facade
filling the upper half of a wide shot"). Atmosphere (fog, darkness) may soften the background but must never
hide, shrink or push away a fixed element: never write "fog swallows everything beyond" when a building is a
fixed element. When a run rewrites `prompt_en`, remove `prompt_stale` from that item (the app sets it when a
manual edit changed the Vietnamese fields but not `prompt_en`; prompts then fall back to the Vietnamese).

```json
{
  "series": "hollow-pine",
  "session": "20261002-073411",
  "version": 1,
  "created_at": "2026-10-08T10:00:00Z",
  "language": "vi",
  "sources": {"bible": "bible_v1.json", "canon": null, "prev_assets": null,
              "episodes": ["final/ep01.json", "..."]},
  "style": {
    "aspect_ratio": "9:16",
    "medium": "photoreal live-action, cinematic still",
    "palette_rule": "one line: the style skill's Color and lighting rule applied to this series (bible world.color_rule if present)",
    "prompt_suffix_en": "appended to every image prompt: lens/grade/film look"
  },
  "characters": [{
    "char_id": "char_01",
    "name": "Vũ",
    "tier": "main",
    "age": 29,
    "apparent_age": "late 20s",
    "face": {"shape": "", "eyes": "", "brows": "", "nose": "", "mouth": "", "skin": "", "marks": ""},
    "hair": "",
    "body": {"height": "", "build": "", "posture": ""},
    "signature_props": ["prop_01"],
    "invariants": ["what must never change across episodes, e.g. 'white earphone cable around neck'"],
    "wardrobe": [{
      "outfit_id": "char_01_o1",
      "name": "default",
      "desc": "garments top to bottom, colour, material, condition",
      "when": "default | after X happens | flashback",
      "episodes": [1, 2, 3],
      "prompt_en": "the outfit alone in English, for image/video prompts"
    }],
    "prompt_en": "one paragraph: apparent age, ethnicity if stated, face, hair, build, posture. NO outfit (outfit prompt is added per shot)",
    "evidence": [{"src": "bible.cast.visual_signature", "quote": ""}, {"src": "ep03.SC3.b17", "quote": ""}],
    "inferred": ["face.nose", "body.height"]
  }],
  "locations": [{
    "loc_id": "loc_01",
    "bible_id": "L1",
    "name": "Cổng kính sườn đồi",
    "parent": null,
    "int_ext": "EXT",
    "desc": "",
    "layout": "where things are relative to each other (behind / left of / ~20 m up the slope), entrances, camera-useful axes; every fixed element is placed here",
    "fixed_elements": ["things that must appear the same every time"],
    "aliases": ["every raw script location string mapped here"],
    "variants": [{"variant_id": "loc_01_night", "time_of_day": "night", "lighting": "light + palette",
                  "prompt_en": "time of day + light in English, for image prompts"}],
    "prompt_en": "",
    "evidence": [], "inferred": []
  }],
  "props": [{
    "prop_id": "prop_01",
    "name": "",
    "desc": "exact look; scratched text verbatim",
    "owner": "char_02",
    "episodes": [3, 8],
    "prompt_en": ""
  }],
  "scene_map": [{
    "episode": 3,
    "scene": "SC1",
    "raw_location": "Bếp kính (L2), nhìn ra sân chung",
    "loc_id": "loc_05",
    "extra_locs": [],
    "variant_id": "loc_05_night",
    "time_of_day": "night",
    "characters": {"char_01": "char_01_o1", "char_06": "char_06_o1"},
    "referenced": [],
    "props": ["prop_02"],
    "reason": null,
    "note": null
  }],
  "issues": [{
    "severity": "high | medium | low",
    "type": "location_alias_conflict | location_not_in_bible | character_not_in_bible | outfit_unexplained_change | look_contradiction | prop_drift | name_or_id_drift | timeline",
    "where": "ep03.SC1.b5",
    "problem": "",
    "fix": "concrete edit to the script or bible"
  }]
}
```

## Reference images (not in this file)

Images live in `assets/images.json` (made by `python3 -m app.pipeline.assets generate`, Codex
image_gen): `{"items": {"<char_id | outfit_id | variant_id | prop_id>": {"kind", "images": [{"file",
"status": "draft|approved|rejected|old", "prompt", "refs", ...}]}}}`. The registry never stores image
paths, so a new registry version does not lose the reviewed images; keys stay stable across versions.

## Rules

- `loc_id` null only for non-places (title card, black screen); then `reason` is required.
- Sub-areas of one set (a corner, a doorway) are the SAME `loc_id`; record them in `layout`.
  A separate room with its own look gets its own `loc_id` with `parent` set.
- One outfit per character per continuous story time. A new outfit needs a story reason in `when`
  (time skip, getting wet/bloody, a disguise). No reason found -> `outfit_unexplained_change` issue.
- `outfit.episodes` must equal the episodes where the scene_map uses it (validator checks).
- Characters only heard (voice, VO, offscreen speaker) get no outfit in that scene.
- Characters only seen in a photo/ID card/screen or only named go in `referenced`, never in
  `characters` (they are not physically there, so no outfit and no wardrobe episode).
- Cross-cut scene (two places in one scene): main place in `loc_id`, others in `extra_locs`.
- `time_of_day`: the real story time when heading and `time_of_day` disagree; log a `timeline` issue.
- `reason`: only for null `loc_id`. Any other remark goes in `note`.
- Sub-part of a bible location (e.g. L4 `interior_mouth`): `bible_id` = `"L4.interior_mouth"`.
- Script contradicts the bible look (e.g. outfit handed over later than the bible implies): keep the
  bible version in the registry and log a `look_contradiction` issue; the user decides.
- Bible-only registry (no episodes yet): `scene_map` is `[]`; wardrobe holds the default outfit of
  each character plus changes the outline already plans (`episodes` = planned episodes, may be
  `[]`); props = those the bible/outline name. `outfit.episodes` is then checked only once episodes exist.
- Episode scenes that already carry `loc_id` / `cast` / `props` (episode-contract): copy them into
  `scene_map` unless they are wrong; a correction is logged as an issue.
- `new_assets` in an episode: give each a real ID (next free number), add it, map the scene to it.
- `prop.episodes` must equal the episodes where the scene_map lists it (validator warns).
