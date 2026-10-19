---
name: script-to-shotlist
description: |
  Break a finished script into 1–5s shots (cuts) with timecode, visuals,
  dialogue and camera directions, then group them into 10-15s CLIPS: one
  video generation per clip, several cuts inside it, so faces, outfits,
  light and long dialogue stay consistent. Generates shotlist.json/.md
  (cuts) and prompts.json/.md (clips) for video generation. Triggers on: "break 
  into shots", "create shotlist", "shot breakdown", "shot list", 
  "scene breakdown", "storyboard script", "prompt list", "video prompts".
  Input: approved script Markdown. Output: shotlist.json/.md + prompts.json/.md
  (one self-contained multi-shot video prompt per 10-15s clip: who says what, does what, cut by cut).
---

# Script → Shot Breakdown

## When to Use This Skill

Use after a series is approved (`/write-series-<slug>` + `/refine-skill <slug> --approve`).
Input: one episode screenplay (`data/series/<slug>/<session-id>/final/epNN.md` + `.json`), or the
whole `final/` dir -> each episode is processed separately, outputs go to `final/shots/epNN/`.
Characters stay identical across episodes: build the character anchors once from the series bible
(`final/bible.md`) and reuse them for every episode.

What it does:
- Break script into discrete 1–5s shots (cuts), then group them into 10-15s clips (one prompt each)
- Create structured data for video generation (image/video AI)
- Generate visual descriptions for each shot
- Assign dialogue, actions, camera directions to shots
- Produce storyboard-like Markdown for review

**Input**: Finished script (Markdown)
**Output**: `shotlist.json` + `shotlist.md` with 1–5s shot breakdown (the cuts, for editing), and
`prompts.json` + `prompts.md` with one prompt per 10-15s clip (the unit sent to the video model)

## Quick Start

```bash
/script-to-shotlist "# My Script\n\n## Scene 1\nAlice walks into the office..."
/script-to-shotlist data/series/<slug>/<session>/final/ep01.md --targets flow              # default: Google Flow only
/script-to-shotlist data/series/<slug>/<session>/final/ep01.md --targets flow,higgsfield   # also the 10-15s clip prompts
```

Or paste script Markdown and it will output:
- `shotlist.json` - Machine-readable (for downstream tools)
- `shotlist.md` - Human-readable storyboard

## How It Works

### Step 1: Parse Script
- Identify scenes, dialogue, action beats; read the episode JSON's per-beat `acting`
  (`does` / `face` / `holds` per visible character) and each scene's `blocking`
  (`.claude/skills/action-polish/references/screen-action.md`)
- Extract character names, locations, tone cues
- Respect pacing from original DNA rules

### Step 2: Segment into Shots
- Break scenes into individual shots (1–5s each; up to ~6s when the style's longest shot allows it)
- Apply pacing rules:
  - Dialogue-heavy scenes: 2–3s per shot
  - Action-heavy scenes: 1.5–3s per shot
  - Establishing shots: 3–5s
- Distribute screen time among characters

### Step 3: Create Shot Descriptions
- For each shot, generate:
  - Visual description (for image/video generation)
  - Character actions
  - Dialogue (if any)
  - Camera direction (angle, movement, transition)
  - Audio cue (music, SFX, voiceover)
  - Mood/tone note

### Step 4: Generate Output Files
- `shotlist.json` - Structured for video gen tools
- `shotlist.md` - Storyboard for human review
- `prompts.json` + `prompts.md` - Prompt list, see Step 5

## Output Format

### `shotlist.json` (Machine-Readable)
```json
{
  "script_title": "My Script",
  "total_duration_sec": 30,
  "total_shots": 11,
  "shots": [
    {
      "shot_number": 1,
      "timecode_start": "00:00:00",
      "timecode_end": "00:00:03",
      "duration_sec": 3,
      "shot_type": "establishing",
      "location": "Office",
      "characters": [],
      "dialogue": "",
      "action": "Wide shot of modern office, morning light",
      "visual_description": "Bright, modern office space. Large windows. Minimalist decor. Camera pulls back slowly.",
      "camera_direction": "Wide static shot, slow pull-back (dolly)",
      "camera_angle": "eye level",
      "audio_cue": "Upbeat instrumental music fades in",
      "mood": "energetic, professional",
      "notes": "Set the scene, establish mood"
    },
    {
      "shot_number": 2,
      "timecode_start": "00:00:03",
      "timecode_end": "00:00:06",
      "duration_sec": 3,
      "shot_type": "close-up",
      "location": "Office",
      "characters": ["Alice"],
      "dialogue": "Good morning, team.",
      "action": "Alice sits at her desk, looks at camera",
      "visual_description": "Tight shot of Alice smiling at camera. Professional attire. Natural light on face.",
      "camera_direction": "Close-up on face, slight pan right",
      "camera_angle": "slightly above eye level",
      "audio_cue": "Alice's voice, music continues softly",
      "mood": "confident, welcoming",
      "notes": "Direct address to camera builds connection"
    }
  ]
}
```

### `shotlist.md` (Human-Readable)
```markdown
# My Script — Shot Breakdown

**Total Duration**: 30s | **Total Shots**: 11

---

## Shot 1: ESTABLISHING
**Timecode**: 00:00:00 → 00:00:03 (3s)  
**Location**: Office

### Visual
Bright, modern office space. Large windows. Minimalist decor. Camera pulls back slowly.

### Action
Wide shot of modern office, morning light

### Camera
- Direction: Wide static shot, slow pull-back (dolly)
- Angle: Eye level

### Audio
Upbeat instrumental music fades in

### Mood
Energetic, professional

### Notes
Set the scene, establish mood

---

## Shot 2: CLOSE-UP
**Timecode**: 00:00:03 → 00:00:06 (3s)  
**Location**: Office  
**Character**: Alice

### Visual
Tight shot of Alice smiling at camera. Professional attire. Natural light on face.

### Dialogue
> Good morning, team.

### Action
Alice sits at her desk, looks at camera

### Camera
- Direction: Close-up on face, slight pan right
- Angle: Slightly above eye level

### Audio
Alice's voice, music continues softly

### Mood
Confident, welcoming

### Notes
Direct address to camera builds connection

---

[... more shots ...]
```

## Step 5: Prompt List (final output of the pipeline): 10-15s clips

Input should be an APPROVED episode (`data/series/<slug>/<session-id>/final/epNN.md` from
`/refine-skill --approve`). Draft episode (`episodes/epNN_vK.md`) -> warn user, continue only if they confirm
(headless: do not continue on a draft; say the episode must be finalized first).

Write to `final/shots/epNN/`:
- `prompts.json` - one entry per CLIP (10-15s, one video generation), for video gen tools / agents
- `prompts.md` - numbered list for humans

### Targets (`--targets`, default `flow`)
`prompts.json` records `"targets"`. The clips (10-15s groups of cuts) are planned the same way for every
target: they hold the cuts, timed dialogue, `opening_state` / `closing_state`, `performance`,
`on_screen_text`, `continuity_in`, and their `veo_parts`.
- `flow` (current focus): `"targets": ["flow"]`. Each clip's own `video_prompt` is `""` and its `refs`
  is `[]`: do NOT write the 10-15s Seedance prompt. All the prompt work goes into `veo_parts` (Google
  Flow), which follow every rule below (anchors, dialogue tags, guard block, Flow-safe, minors).
  `prompts.md` lists the Flow parts per clip.
- `higgsfield`: also write each clip's 10-15s `video_prompt` and `refs` (Seedance 2 / Kling), as the
  sections below describe. Both: `"targets": ["flow", "higgsfield"]`.

Why clips: a 1-2s prompt per shot means 30-40 separate generations per episode; faces, outfits,
light and voices drift between them, and a dialogue exchange gets cut into pieces that never match.
Current video models (Seedance 2, Kling, Veo) take one prompt with several timed cuts and keep the
same people and place inside it. The style's fast cutting stays: it lives INSIDE the clip.

### Grouping shots into clips
- One clip = all or part of ONE scene of the script (a scene is one place at one time). A clip never
  crosses a scene boundary, even when both scenes share a `loc_id` (the dining room and the back
  garden of the same villa are two settings): two conversations in two places are two clips.
- Clip length 10-15s (aim ~12s). A scene shorter than 10s is its own shorter clip (do not borrow
  time from the next scene). A scene longer than 15s is split into clips of 10-15s.
- Phone calls / intercut scenes (lines alternate between two places): one clip per place, holding
  that side's lines lip-synced; the other side is an off-screen voice in the same clip. The editor
  intercuts the two clips afterwards (say so in `continuity_in`).
- Never split a dialogue line. Keep a whole exchange in one clip; when an exchange runs past 15s,
  split at a speaker change, and the next clip opens on the same framing (`continuity_in`).
- At most 5 cuts per clip (aim 3-4): video models execute 3-4 timed cuts reliably and blur the rest.
  Each cut 1.5-5s. When the style cuts faster, merge neighbouring cuts on the same subject into one
  shot with a camera move (push-in from MCU to CU, rack focus to the prop) instead of adding cuts.
- Clips are 10-15s for multi-shot models (Seedance 2, Kling). Google Flow makes only 4, 6, 8 or 10s
  per generation: every clip also carries `veo_parts` stretched to those lengths (see below).
- Clips are contiguous: `end_sec` of clip N = `start_sec` of clip N+1; last `end_sec` = episode length.
- Check before reporting done: `python3 -m app.pipeline.package check <session-dir> <episode>` ->
  0 errors (clip inside one scene, 15s max, contiguous, every line timed inside its clip, Opening /
  Ending / Rules in every prompt, `veo_parts` on every clip and valid: `duration_sec` = the stretched Flow
  length (6/8/10s), prompt starting "<duration_sec>-second"; minors rule; Flow-safe warnings fixed). Fix and re-run; also fix "more than 5 cuts" warnings.

### Character, outfit and location anchors
Source of looks, first that exists: `final/assets.json`, else the latest `assets/assets_vN.json`
(asset registry from `/series-assets`), else the bible (`final/bible.json` -> `visual_signature`).

With a registry:
- Character anchor = `characters[].prompt_en` (face/hair/body) + the outfit worn in this scene
  (`wardrobe[].prompt_en`; outfit from the episode scene `cast`, else the registry `scene_map`).
- Location anchor = `locations[].prompt_en` + the scene variant's `lighting`.
- Prop anchor = `props[].prompt_en` (text on props verbatim).
- Every prompt ends with the style suffix, FILTERED to the scene: keep the clauses that hold everywhere
  (aspect, photoreal, lens, grain, the general grade) and only the lighting clause that matches this
  scene's INT/EXT and time of day. Never put "warm practical light indoors" in an exterior clip, or a
  night clause in a day clip. `style_suffix` in prompts.json keeps the full registry text.
- Each clip lists `refs`: approved reference images from `assets/images.json` (status `approved`)
  for the characters on screen (outfit image if one exists for the worn outfit, else the character
  sheet; speaking characters first), then the location variant, then props; at most 6, as paths
  relative to the session. Empty when none is approved yet. Every clip also carries `loc_id`,
  `variant_id`, `props` and `outfits`, so the web app's "Tải gói video" zip (app/pipeline/package.py)
  can attach refs approved later.

Every clip prompt states each character's anchor ONCE, word-for-word, at the top (as "Cast"), then
refers to them by name in the cuts. Same character looks identical in every clip; the outfit changes
only where the scene `cast` changes it.
- Anchors are word-for-word EXCEPT states that change over the story (wounds, scars, bandages, stains,
  wet clothes, a prop not yet given): describe that state as it is at this moment of this episode
  (a scar the character gets in shot 6 is not in shots 1-5). Remove the clause, never contradict it.
- Cast = ONLY the characters seen in this clip, each with the ONE outfit worn in this scene. Never list
  a character who is not on screen, and never give two looks ("before / after the makeover") for one
  person. A voice heard off screen is an `OFF-SCREEN VOICE` line in the cut (see "Dialogue in
  prompts"), not described in Cast (its voice is in `Voices`).

### Clip handoff, performance, guards (every clip)
- Acting from the script: each cut's `action` = the beat's `action` + its `acting` (every visible
  character: body/hands from `does`, the face from `face`, the object from `holds`), translated, in
  that order, speaker first. Never drop a held object between cuts; hands carry the subtext (a line
  said while the hands shake keeps the shaking). A beat with no `acting` (older script): invent only
  silent, neutral business and suggest `/action-polish`.
- `opening_state`: one sentence, the exact first frame: who is where, pose, what is in hand, framing
  (from the scene `blocking` and the first beat's `holds`).
  When the clip continues the previous clip's scene it matches that clip's `closing_state`.
- `closing_state`: one sentence, the exact last frame the next clip (or the edit) picks up from.
- `performance`: one sentence, the emotional turn across the clip (from what to what, and what the
  face/body shows: "confusion first, not anger"), built from the clip's `acting` faces and hands.
  Delivery tags on lines stay as they are.
- `on_screen_text`: every piece of lettering that must be visible (sign, phone screen, document
  header, title card), verbatim with where it appears; `[]` when none. Prefer `[]`: models misspell
  text, so keep only lettering the story needs and leave the rest for post (say so in `action`).
- `continuity_in` stays for the app: how the clip joins the previous one (may repeat `opening_state`).

Prompt layout (`video_prompt`, one paragraph per item, in this order):
1. `<len>-second vertical 9:16 multi-shot clip, <INT/EXT>, <time of day>, <location anchor>.`
2. `Cast: <name>: <anchor + outfit>; ...` (only who is on screen) `Voices: ...` `Props: ...`
3. `Opening: <opening_state>`
4. `Shot 1 (0-2.5s): ...` timed cuts, each with size + camera + action + exact quoted line(s)
   (speaker, language, lip-synced or voice-over, delivery, line times).
5. `Performance: <performance>`
6. `Ending: <closing_state>` and `Sound: ...`
7. The guard block, verbatim, filling the on-screen text slot:
   `Rules: Speak only the quoted lines, word for word, each by its named speaker; no extra lines, no
   ad-lib, no narration that is not quoted. Only the listed cast appear; background people only where a
   shot names them. No subtitles, captions, watermarks or on-screen text except: <on_screen_text, or
   "none">. Keep every prop with its owner and the same faces, outfits and light in every shot.
   Natural hands and anatomy; no sudden costume change; no music with lyrics.`
8. The filtered style suffix.

### Dialogue in prompts: who speaks, how (every prompt, Seedance and Flow)
Video models confuse speakers and lip-sync inner thoughts unless every line says, in the same words
every time, WHICH kind of line it is. Each dialogue line in prompts.json has `"mode"`:
- `speaks`: said aloud by a character on screen in that cut.
- `voiceover`: narration or inner thought (`voiceover: true` in the script). Nobody's lips move, even
  when the speaker is on screen (that is the usual case: the narrator thinks while we see him).
- `offscreen`: said aloud by a character NOT in frame in that cut (phone, loudspeaker, behind a door).

Write each line with its tag, word for word, right before the quote:
- speaks: `SPEAKS (lip-synced): <who> (<visual tag>), <delivery>, <a>-<b>s: "<line>"`
- voiceover: `VOICE-OVER (inner voice, nobody's lips move): <who>, <delivery>, <a>-<b>s: "<line>"`;
  when the speaker is in the shot add "<who> keeps his/her mouth closed".
- offscreen: `OFF-SCREEN VOICE (not in frame): <who>, <through what>, <delivery>, <a>-<b>s: "<line>"`
`<who>` = the same character name as in Cast (Seedance and Flow parts alike); never a name in one
place and a description in another. `<visual tag>` = what tells him apart in THIS frame ("on the left,
grey T-shirt", "the one holding the shovel").

Rules:
- A `Voices:` line right after Cast: one voice per speaker of the clip (gender, age, timbre, accent,
  from the bible `cast[].voice`; a character not in the bible cast gets one from the registry age and
  role, e.g. "the foreman: man in his mid 40s, gruff loud voice"), e.g. `Voices: Phong: young man, low warm voice, soft Southern
  accent; Tam: man in his 30s, quick bright voice`. The VO voice is the same as that character's voice.
- At most one `speaks` speaker per cut. A two-person exchange is shot / reverse shot, one cut per
  speaker; if both must be in one frame, the visual tag gives left/right and only that one's lips move.
- A cut with no `speaks` line says "no one speaks on screen" when it has a voiceover line.
- Never call a voiceover "off screen" while its speaker is visible; "off screen" is only for `offscreen`.
- A line that runs over the next cut (L-cut) is mentioned in EVERY cut it covers: "No one speaks on
  screen; <who>'s voice-over continues over this shot." Write "No dialogue" only for a cut that no line
  overlaps; otherwise the model cuts the line or crams it.
- While a voice-over plays, no action may invite speech: never "as if to ask / about to say / opens his
  mouth"; write "his lips part, then press shut" or "says nothing". Characters with no line in the clip
  get silent performance words ("smiles silently", "watches"), never "teases", "jokes", "chats", "laughs"
  aloud, which make the model invent lines.
- Every line fits the speech rate at its own times (vi-dialogue.md: Vietnamese <= 5.0 syllables/s).
  When the script line cannot fit, do not rush it: keep it and write a `pace_warning` naming
  /dialogue-polish; `package check` warns on it.

### Veo parts (every clip): the Google Flow / Veo 3.1 version
`veo_parts`: the same clip for Google Flow, each part one generation. Flow accepts ONLY these lengths:
**4, 6, 8 or 10 seconds** (any other number is refused). A part played at script speed looked rushed in
Flow (a 6s part could not show its action), so every part is generated LONGER than its script time:
- `start_sec` / `end_sec`: the script time the part covers (absolute, as in the cuts). Script length =
  `end_sec - start_sec`, at most 8s.
- `duration_sec`: the Flow length = the smallest step that holds ~1.3x the script length
  (`app.pipeline.package.flow_duration`): up to 4.7s -> 6s, 4.7-6.2s -> 8s, 6.2-8s -> 10s (under 3.1s -> 4s).
  The whole generation is kept in the edit: the episode video runs ~1.3x the script.

Plan the split per clip so every part lands in those bands:
- Prefer parts of 5-6s of script (-> 8s) and 6.5-8s (-> 10s); 3.5-4.7s (-> 6s) for a short scene end.
  Never over 2x (a 3s part in 8s plays in slow motion): merge it with a neighbour cut.
- Examples: 13.8s clip with cuts ending at 3.0, 5.8, 8.5, 13.8 -> parts 0-5.8 (8s) + 5.8-13.8 (10s).
  12s clip -> 6 + 6 (8s + 8s). 15s clip -> 7.5 + 7.5 (10s + 10s). A clip of 8s or less is one part.
- Splits stay at cut boundaries, never inside a dialogue line; parts are contiguous and cover the clip
  exactly (first `start_sec` = clip start, last `end_sec` = clip end).
- The part prompt is written for `duration_sec`: it starts
  `"<duration_sec>-second vertical 9:16 multi-shot clip, ..."`, and every cut and line time is the
  script time scaled by `duration_sec / script length` (relative to the part), so the shots run from 0
  to `duration_sec` with no held tail. Use the extra time for the acting the script already has
  (`acting`: hands, face, what is in hand; a beat of reaction before and after a line), never for new
  events or new lines. Line delivery may be calmer; the words stay exactly the same.
- Each part is self-contained (`video_prompt` in the same layout: its own Cast = who is on screen in
  THAT part, its own Opening = the part's real first frame, only its cuts and lines with times
  relative to the part, the guard block, the style suffix). Part 1 opens on the clip's
  `opening_state`, the last part ends on its `closing_state`. Parts join on a hard cut, so the next
  part does not repeat the previous Ending; its `continuity_in` says what carries over (positions,
  props in hand, light) so the edit matches.
- Flow-safe writing (Google Flow refuses prompts that look like recreating a real person: "may
  violate our policy on videos of famous people"). The trigger was an idol-like FACE (a reference image
  built from beauty adjectives, and outfit images still made from it), not the names: on 2026-10-15
  every ep06 part passed with the character names written out. So in every part prompt:
  - Characters by NAME (the bible name, the same in every episode), in Cast, in the shots and in the
    dialogue tags; the Cast line adds the relation where it helps ("Na, Phong's younger sister").
    Older prompts.json files with `flow_labels` (role labels) are shown and packaged with the names
    swapped in (`package.named_prompt`); new files do not write `flow_labels`.
  - Short look only: age range, build, hair, outfit, one signature item, PLUS the character's 1-2
    distinctive face marks from the registry (freckles, a mole, glasses, a scar, a crooked tooth). No
    full facial anatomy list (eyes, brows, nose, lips, jaw, skin), no height in cm. Never leave a face
    with no mark at all: the model then fills in a default "pretty" face, and a young woman described
    only by hair and a silk blouse was refused as a famous person even with no image of her attached.
  - `refs` (Flow "Ingredients to Video", at most 3 images per part): one image for EVERY character on
    screen in the part (outfit image when one exists for the worn outfit, else the character sheet),
    ordered by screen time in the part (the face the camera holds on first), then the location plate
    if a slot is left. More than 3 characters on screen: the 3 with most screen time get images, the
    rest are text only; the location is then text only too. Each image must show ONE character (no
    group sheets), and the Cast line describes every character whose image is attached, in the same
    order, by name.
  - No lettering at all (signs, phone screens, title cards go to post): the guard line reads
    "... on-screen text except: none" and the location text drops sign wording.
  - Start the Cast line with "Original fictional characters, not real people."
- Minors (every character the asset registry gives an `age` under 18). The script should already follow
  `.claude/skills/story-contract/references/minors-on-screen.md`; this is the second net for what got through. Flow refused a part with a
  10-year-old as "harmful content involving minors": the child was described by body ("small and skinny",
  "barefoot", "floral shorts"), next to a man in a tank top and shorts, late at night, a bed in the room,
  touching (ruffling hair, sitting pressed beside him), sleeping side by side, and her photo attached.
  In EVERY prompt (Flow parts and the 10-15s clip prompt) where a minor is on screen:
  - No photo of the child in `refs` (text only; an adult in the part may keep theirs). Frame the child
    so a face model is not needed: medium or wide, profile, from behind, hands on a prop.
  - Describe the child by relation + age + full clothing only: "his younger sister, a 10-year-old
    schoolgirl in a white school shirt and navy trousers, chin-length hair, a yellow schoolbag". Never a
    phone or other device in the child's description, even when the registry lists one as her signature
    item: drop it from the part. No body or face words (skinny, small, slim, tanned, lips, pouting mouth), no bare feet,
    shorts, sleeveless tops, sleepwear; the adults in the same part fully dressed too (T-shirt, long
    trousers).
  - Name the child and her relation in the Cast line ("Na, Phong's younger sister"), and the relation of
    the adults ("Phong, her older brother").
  - No physical contact between an adult and the child (no hug, ruffling hair, carrying, holding, lap,
    leaning on): keep "an arm's length apart"; show care through objects and looks (hands her a bowl).
  - No bed, bedroom, sleeping, bathing, changing clothes, "late night", "alone with": move the moment to
    the evening, a doorway, a porch with the alley behind, a kitchen; a sleeping adult becomes "resting
    his head on his arms at the table" with the child sitting across.
  - No adult asleep, dozing, "eyes closed", "resting his head", "does not stir" while the child is on
    screen (renaming sleep does not help: the ep04 review found "rests his head on his arms, eyes closed"
    + "she checks he does not stir"). Keep the story beat, move the adult OUT of the frame: busy inside,
    seen from behind through a door, gone to the shop. The child then acts alone with the object.
  - Never mention a child sleeping, even off screen ("afraid to wake his sister" in a delivery tag, in
    `performance` or `continuity_in`), and no sleeping mat / bed in the text of a home where a child
    lives.
  - No shot on a child's mouth, lips or teeth: a mouth habit from the bible `tell` (chewing a strap)
    becomes a hand action (twisting the strap around a finger).
  - No crying or hurt child (tears, red-rimmed eyes, crying) next to an adult; a child's distress is a
    set jaw, fast blinking, a hand or a prop, the face in a medium shot.
  - A child using a phone to contact someone (messaging, dialling, scrolling contacts, pressing send),
    or a child alone at night: the child is OFF SCREEN in the Flow parts. Flow refused ep04 7_1 and 8_1
    (a 10-year-old alone on a porch after dark, secretly taking her brother's phone, typing, praying to
    the parents' photo, pressing send) even after every risky word was removed. Tell the beat with
    objects and sound: the phone on the step lifted out of frame, the screen as an insert (text in post),
    keys lighting up, the photo; her lines become an OFF-SCREEN VOICE ("a young girl's soft whisper").
    The part's `characters` then leaves her out, `refs` has no character image of her, and the Cast line
    says "no person on screen". Quoted lines stay word for word.
  - One adult at most in a part that shows a child, from the family (the older brother, the mother).
    Flow judges every generation alone: ep06 clip 2 part 1 (the sister twisting her phone strap between
    her brother and his co-worker, at the door after dark) was refused 5 times, also re-staged in
    daylight; it passed with the child out of the frame. Split such a clip into parts on its cuts: the
    child's cuts (alone, or with the one family member) in their own part, the other adults' cuts in
    theirs; the edit joins them. A cut that shows the child and two adults is re-framed (the child's
    side of the shot, the adults over the shoulder off frame). A line from an adult TO the child in
    another part keeps the child's name so the cut reads.
  - No device in a part that shows a child: no phone, screen, texting, dialling, keypad, tablet,
    computer in the child's hands, around her neck or on the table beside her. The device belongs to
    the adults' parts (the brother finds the sent message on his own phone, screen as a plain glow,
    message text in post); the child's part keeps her line and her face (shrug, eye-roll, grin, hands
    crossed or on a school thing). A child's line ABOUT the device stays word for word.
  - Fallback when a child's part is still refused: the child goes off screen in that part (her line
    becomes an OFF-SCREEN VOICE, Cast line "only <adults> appear on screen"), and a separate child-only
    part (no device, no other people, lit room, her line lip-synced) is offered next to it.
  - Quoted dialogue stays word for word. `package check` makes these errors: a photo of a minor in
    `refs`, risky words, a device word, or two or more adults in a part with a minor on screen.

### `prompts.json`
```json
{
  "unit": "clip",
  "prompt_format": 4,
  "targets": ["flow", "higgsfield"],
  "source_script": "data/series/<slug>/20261001-143000/final/ep01.md",
  "skill": "write-series-<slug>",
  "skill_version": "v3",
  "aspect_ratio": "9:16",
  "total_duration_sec": 90,
  "assets": "data/series/<slug>/20261001-143000/final/assets.json",
  "style_suffix": "vertical 9:16 frame, photoreal, ...",
  "characters": {"char_01": "teen girl, 16, dark wavy shoulder-length hair, navy blazer, white shirt, silver ring pendant"},
  "locations": {"loc_02": "foggy dead pine forest at night, ..."},
  "shots": [
    {
      "shot_number": 1,
      "scene": "SC1",
      "start_sec": 0, "end_sec": 12.5, "duration_sec": 12.5,
      "characters": ["char_01", "char_02"],
      "loc_id": "loc_02", "variant_id": "loc_02_night", "props": ["prop_03"],
      "outfits": {"char_01": "char_01_o1", "char_02": "char_02_o1"},
      "refs": ["assets/characters/char_01/char_01_sheet_v1.png", "assets/locations/loc_02/loc_02_night_v1.png"],
      "action": "Lan runs through the fog, stops when Minh blocks her path; they argue in whispers",
      "camera": "handheld; WS -> CU -> OTS -> CU",
      "sfx": "heavy breathing, snapping branches, wind",
      "cuts": [
        {"cut": 1, "start_sec": 0, "end_sec": 2.5, "camera": "handheld tracking WS, push-in",
         "action": "Lan runs toward camera through the fog, glances back", "dialogue": []},
        {"cut": 2, "start_sec": 2.5, "end_sec": 5.8, "camera": "static CU",
         "action": "Lan stops, out of breath",
         "dialogue": [{"character": "char_01", "line": "Nó vẫn còn ở đây.", "delivery": "thì thào, sợ",
                       "voiceover": false, "mode": "speaks", "start_sec": 2.8, "end_sec": 4.6}]}
      ],
      "dialogue": [{"character": "char_01", "line": "Nó vẫn còn ở đây.", "delivery": "thì thào, sợ",
                    "voiceover": false, "mode": "speaks", "start_sec": 2.8, "end_sec": 4.6}],
      "continuity_in": "",
      "opening_state": "Wide: Lan, far in the fog, running toward camera, torch in her right hand.",
      "closing_state": "Close-up: Lan and Minh face to face, his hand on her torch arm, both still.",
      "performance": "Lan's panic turns into suspicion when Minh blocks her; Minh stays calm, hiding something.",
      "on_screen_text": [],
      "pace_warning": [],
      "video_prompt": "12.5-second vertical 9:16 multi-shot clip, EXT, night, dense foggy pine forest (...location anchor...).\nCast: Lan: teen girl, 16, ... ; Minh: ... .\nVoices: Lan: teenage girl, thin breathy voice; Minh: teenage boy, low calm voice.\nOpening: Wide: Lan, far in the fog, running toward camera, torch in her right hand.\nShot 1 (0-2.5s): handheld tracking wide shot, Lan runs toward camera through the fog, glances back. Shot 2 (2.5-5.8s): static close-up on Lan, out of breath. SPEAKS (lip-synced): Lan (alone in frame, torch in hand), whispering in Vietnamese, terrified, 2.8-4.6s: \"Nó vẫn còn ở đây.\" Shot 3 (...) ...\nPerformance: ...\nEnding: Close-up: Lan and Minh face to face, ... Sound: heavy breathing, snapping branches, wind.\nRules: Speak only the quoted lines, ... No subtitles, captions, watermarks or on-screen text except: none. ...\nvertical 9:16 frame, photoreal, ...",
      "veo_parts": [
        {"part": 1, "start_sec": 0, "end_sec": 5.8, "duration_sec": 8, "cuts": [1, 2], "continuity_in": "",
         "refs": ["assets/characters/char_01/char_01_sheet_v1.png", "assets/locations/loc_02/loc_02_night_v1.png"],
         "video_prompt": "8-second vertical 9:16 multi-shot clip, EXT, night, foggy pine forest. Cast: Original fictional characters, not real people. The schoolgirl: teenage girl, slim, dark wavy shoulder-length hair, navy blazer, torch in hand. Opening: ... Ending: Close-up: the schoolgirl out of breath, eyes on the fog. ..."},
        {"part": 2, "start_sec": 5.8, "end_sec": 12.5, "duration_sec": 10, "cuts": [3, 4], "continuity_in": "the schoolgirl still out of breath, torch in her right hand, same fog and light",
         "refs": ["assets/characters/char_02/char_02_sheet_v1.png", "assets/locations/loc_02/loc_02_night_v1.png"],
         "video_prompt": "10-second vertical 9:16 multi-shot clip, ... (cut and line times x10/6.7) ... Opening: Over-the-shoulder: the tall boy steps out of the fog in front of the schoolgirl. ..."}
      ]
    }
  ]
}
```
`shots` is the list of clips (the key name is kept for the app). `cuts` are the clip's internal shots
(the same breakdown as `shotlist.json`, times absolute in the episode). Every dialogue line has its
own `start_sec`/`end_sec` (absolute): subtitles and lip-sync use them.

### `prompts.md`
```markdown
# <Title> - Video clips (90s, 8 clips / 32 cuts, skill <slug> v3)

## Characters
- char_01: teen girl, 16, dark wavy shoulder-length hair, navy blazer, ...

## Clips
1. [00:00-00:12.5] (12.5s) SC1 foggy forest. Cuts: WS run -> CU "Nó vẫn còn ở đây." -> OTS Minh -> CU.
   PROMPT: 12.5-second vertical 9:16 multi-shot clip, ...
```

### Prompt rules
- One prompt per clip of 10-15s (see Grouping). Inside it, numbered timed cuts (at most 5): "Shot k
  (a-bs): size + movement, who does what, who says what".
- `video_prompt` is self-contained and follows the Prompt layout above: setting anchor, Cast (on-screen
  only), Voices, Opening, timed cuts with every line tagged SPEAKS / VOICE-OVER / OFF-SCREEN VOICE
  (see "Dialogue in prompts"), Performance, Ending, Sound, the Rules guard block, the filtered style
  suffix. No "same as before".
- `continuity_in` (and the start of the prompt) describes how the clip opens when it continues the
  previous clip's scene (same framing, positions, light), so the two clips cut together.
- Dialogue rate: `.claude/skills/dialogue-polish/references/vi-dialogue.md` "Speech rate" (Vietnamese
  counted in syllables, hard limit 5.0/s; English 2.5 words/s). Time each line inside its clip. A VO line
  may run over the next cut (L-cut) without a warning; a lip-synced line may run over a cut only while
  the speaker stays on screen. Nothing runs past the clip's end. `pace_warning` ONLY for: a stretch over
  the hard limit, or a lip-synced line whose speaker is off screen while it is spoken.
- Language: prompts in English (video models), dialogue kept in the script's language.

## Integration with Video Tools

`shotlist.json` is ready to feed into:
- **Seedance** (Higgsfield) for video generation
- **Image generation AI** for visual reference frames
- **Storyboard software** for team collaboration
- **Teleprompter apps** for voiceover recording

## Notes

- Cut durations respect pacing from original DNA; prompts are per 10-15s clip
- Visual descriptions are detailed for AI image/video generation
- Camera directions include angle + movement + transitions
- Dialogue preserved exactly from script
- Mood/tone notes help maintain consistency across shots
- JSON format enables programmatic use (batch generation, etc.)
