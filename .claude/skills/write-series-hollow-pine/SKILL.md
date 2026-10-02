---
name: write-series-hollow-pine
version: v1
description: |
  Turn a rough or fragmented story idea into a 10-20 episode vertical micro-drama series (60-120s
  episodes) told the way a boarding-school supernatural mystery is told: open on a bloodied
  flash-forward then title-card rewind the clock, drop the protagonist into a closed institution
  that takes away her means of escape and binds everyone under one collective-punishment rule,
  and let her cynical first-person voiceover undercut every official lie while she hides her real
  reason for coming. Mysteries open fast and almost never close; a physical object with scratched
  text carries the central question; allies arrive through one small action, authority figures
  through one unsoftened line. Cuts are fast (~24/min, ~2.5s per shot) with one deliberately held
  10-13s take per episode; cold teal-blue fog means danger and warm amber lamplight means the
  institution is watching. Every episode ends mid-decision on an irreversible internal choice.
  Use whenever the user wants to develop an idea, notes, scattered scenes, a logline or a draft
  into a series, season outline, episode scripts or screenplay in this style, even if they only
  paste fragments. Output: series bible + season outline + episode screenplays (md + json).
---

# Write Series: Hollow Pine

Learned from: `data/analyses/20261002-071408/dna.json` — `Tập 1.mp4`, 91.3 sec, 1 unit (one episode).
Reference plot: `references/reference-story.md`. Cast: `references/reference-characters.md`.

**Read the Data limits section before trusting any season-level number.** The measured sample is a
single 91-second episode. Episode-level craft is measured; season-level structure is projected.

## Quick Start

```
/write-series-hollow-pine --idea "..." | --idea-file notes.md [--episodes 12] [--episode-sec 90]
                          [--characters "..."] [--sample draft.md] [--continue <session-dir>] [--auto]
```

## Input

| Field | Default | Meaning |
|---|---|---|
| `--idea` / `--idea-file` | required | User's idea: logline, scattered scenes, notes, any language |
| `--episodes` | 12 | 10-20 |
| `--episode-sec` | 90 | 60-120 |
| `--characters` | - | Names + roles; missing roles filled from Character Bible |
| `--sample` | - | User draft: keep its content, apply this style |
| `--continue` | - | Existing session dir: keep bible, extend or revise |
| `--auto` | off | Skip the outline approval stop |

## Workflow

Session dir: `data/series/hollow-pine/<session-id>/` (session-id = UTC `YYYYMMDD-HHMMSS`).
Save `input.json` first: the raw idea, every flag value, and this skill's version.

### Stage 1 — Adaptation map (adaptation.md)

1. Extract every element from the idea: premise, characters, places, scenes, lines, endings, themes.
2. Map each onto a Story Template beat and a Character Bible role.
   Table columns: `user element | beat/role function | reference analog`.
3. Empty beats/roles: invent something original for the user's world, marked `[from template]`.
4. Conflicts: the user's idea wins. Adjust the template and note why in one line.
5. Name the four fixtures this style cannot run without, drawn from the user's world:
   **the closed world**, **the thing taken away on arrival**, **the collective-punishment rule**,
   **the erased person**. If the idea supplies none of them, invent them and say so.

### Stage 2 — Bible + outline (bible_v1.md/.json, outline_v1.md/.json)

- **Bible:** title, logline, premise, theme, world rules (5, one of them collective-punishment),
  locations with look, cast (tier, role, want/need/flaw/secret, visual_signature, voice + 2 sample
  lines), mystery ledger plan (question -> clue episodes -> answer episode), relationship arcs,
  motif list (3-5, at least one never explained).
- **Outline:** one row per episode — title, logline, beats, which Story Template beat(s) it carries
  (% position), reveal/clue, cliffhanger type, characters.
- **Spread:** beat at p% -> episode `ceil(p/100 * N)`.
- STOP and show the outline unless `--auto`. The user approves with
  `/refine-skill hollow-pine --approve outline` or gives feedback.

### Stage 3 — Episodes (episodes/epNN_v1.md/.json)

- Each episode follows the Episode Template and every rule section below.
- N > 6: write in parallel with general-purpose subagents, 3-4 episodes each. Give each the bible,
  the outline, this SKILL.md path and its episode numbers.
- Continuity pass after all episodes: names, visual signatures (verbatim from the bible), ledger
  timing, motif callbacks, timecodes summing to `--episode-sec`.
- Write `series.md` (index + all episodes) and reply with: outline table, open threads, file paths.

## Story Template (season arc)

Positions are % of the season. `measured` = the beat function is present in the analysed episode.
`projected` = extrapolated from the reference's mystery ledger, open threads, stated devices and
reveal rhythm; the reference does not contain this beat. See Data limits.

| % | Beat function | Why it works | Ref |
|---|---|---|---|
| 0-2 | Flash-forward: protagonist alone, injured, fleeing through the dangerous zone, calling a name the audience has no reason to know yet | Buys a danger hook without spoiling the ending; the unknown name becomes the season's first debt | measured, t=0.58 |
| 2-3 | Hard cut to black; title card names the world and rewinds the clock by a stated amount; a graphic transition and a drained-colour image carry the jump | The rewind converts a spoiler into a promise | measured, t=9.53 |
| 3-6 | Protagonist arrives at the closed world and is stripped of her means of escape by a gatekeeper who gives orders in single words | Removes the easy exit before the audience thinks to ask about it | measured, t=17.93 |
| 6-9 | One authority figure recites all the world's rules in one scene, flat and unsoftened, ending on a collective-punishment rule | Spends the exposition budget once instead of drip-feeding | measured, t=23.09-27.85 |
| 9-10 | VO undercuts the rule within 7 seconds of hearing it — states the theme as an accusation | Voice and thematic stance land in one line | measured, t=34.26 |
| 10-13 | A physical object with scratched/altered text plants the central mystery; in the same scene the protagonist lies about it to an ally while her VO tells the viewer the truth | Dramatic irony from the first act, no exposition spent | measured, t=40.68-42.06 |
| 13-16 | Unexplained motif figure appears inside a deliberately long take, does one gesture, says nothing | Plants a debt the season can draw on later | measured, t=37.83 |
| 16-20 | Night one: the protagonist breaks the newest rule, following others into the forbidden zone | Proves rules are made to be broken before the audience is bored of them | measured, t=51.99 |
| 20-23 | A peer weaponizes the authority's rule against the group, in the authority's own words | Shows the institution has already won without appearing on screen | measured, t=59.78 |
| 23-26 | Protagonist confesses one long-held personal/supernatural tie to a single ally; the ally's reaction implies he shares it | Converts a secret into a bond and a new question at once | measured, t=67.49 |
| 26-30 | First real disappearance: someone is lost, and the collective-punishment rule fires for the first time | Turns a stated rule into lived cost; the whole cast becomes suspects of each other | projected from world rule t=27.85 + subplot payoff pattern |
| 30-36 | The ally she lied to discovers the lie; her flaw costs her the person she most needs | The flaw named in the DNA has to be paid for | projected from char_01 flaw |
| 36-42 | First answer in the season, to the smallest open question, and it opens a larger one | Honours the measured pattern of opening faster than closing | projected from ledger (5 open, 0 answered) |
| 42-48 | The unexplained motif pays off for the first time; it meant something all along and still is not explained fully | Reference rule: let a motif accrue meaning instead of explaining it | projected from motif list |
| 48-52 | Midpoint: she reaches the forbidden place itself and encounters the source of the mystery indirectly — heard, glimpsed, never confirmed | Keeps the central question alive past the midpoint | projected from open thread "house with the lit window" |
| 52-58 | The institution stops being general and targets her specifically; her cover story collapses | The lie she arrived with is spent, so she must operate in the open | projected from secret + flaw |
| 58-64 | The silent omen figure's role lands, or an ally turns out to belong to the institution | The reference seeds a character with no stated function; a season has to cash that | projected from char_07 |
| 64-72 | The erased person is found, or proved dead — the question she came for is answered, and the answer reframes her motive | The season's declared want is resolved before the finale so the need can take over | projected from want vs need |
| 72-80 | She demonstrates what she is; "what I am" moves from question to fact, and it frightens the people who stayed loyal | The DNA names this as the protagonist's unstated need | projected from need + t=84.07 |
| 80-88 | Lowest point: an ally is lost, the collective-punishment rule falls on everyone, and she is blamed for it | The rule stated in the premiere delivers its full weight | projected from Rule Six escalation |
| 88-92 | The premiere's flash-forward image is reached and passed; the audience finally sees why she was bloodied and who she was calling | Pays the structural debt the cold open created | projected from t=0.58 + 9.53 device |
| 92-97 | She confronts the buried truth and what the institution's lie cost; the theme is answered out loud | Theme: "the lies institutions tell to control people, and what it costs to go looking" | projected from theme |
| 97-100 | Finale ends mid-decision on a new irreversible choice, with an ambiguous spoken warning from an unidentified voice; one season question stays unanswered | The reference's only demonstrated ending mode | measured pattern, t=84.07 |

### Mystery / reveal ledger pattern

- **Questions open far faster than they close.** The reference opens 5 questions, drops 1 clue and
  answers 0 in 91 seconds (Ref: mystery_ledger). Carry **4-6 open questions at any time**.
- **Spacing:** a reveal or clue beat every **17 seconds** of screen time (Ref:
  `reveal_rhythm_sec=17`) — about **5 per 90-second episode**.
- **Answer rate:** one question answered per **2-3 episodes** (projected: the only measured rate is
  zero, which cannot run for a season). Each answer must open a larger question.
- **Open-and-corroborate:** at least once a season, drop a clue **within 2 seconds** of opening the
  question it belongs to (Ref: Q2 opened t=40.68, clue t=42.06).
- **Never answered in season:** keep **2** questions open at the finale. In the reference these are
  the unexplained name from the cold open and the origin of the protagonist's supernatural tie.

### Subplots

Two subplot shapes, both from the reference:

1. **Thematic proof subplot** — an idea stated by authority, then weaponized by a peer, inside a
   short span. Set up at 6-9%, paid off at 20-23% (Ref: Rule Six, 27.85s -> 59.78s, 32 seconds
   apart). Run a new instance of this shape every 3-4 episodes with a different rule.
2. **Open personal subplot** — the protagonist's unexplained tie to the world, set up at 23-26% and
   deliberately never resolved on schedule (Ref: the six-year voice, setup 67.49s, no payoff). Drip
   one clue every 2 episodes, pay off only partially at 72-80%.

## Episode Template (60-120s)

Percentages scale to `--episode-sec`. Seconds shown for the 90s default.

| Time (90s) | % | Beat | Rule | Ref |
|---|---|---|---|---|
| 0.0-3.0 | 0-3 | **Hook** | Open on an image, not a situation: danger in progress, or a rule being broken, with no context given | t=0.58 bloodied chase |
| 0.5-4.0 | 1-4 | **VO aphorism** | First VO line is a flat, bitter declarative about a lie. Max 12 words. Never a question | t≈2 "They call this place a school. Remember that. It's the first lie." |
| 3.0-10.0 | 3-11 | **Orientation** | Title/time card only if the episode jumps time; otherwise one wide that locates us. Drained colour or a graphic marks any jump | t=9.53 title card + rewind graphic |
| 10.0-40.0 | 11-45 | **Setup** | Someone with power states or enforces something. VO undercuts it within 7 seconds. Dialogue stays under 8 words a line | t=23.09-34.26 |
| 37.0-50.0 | 41-55 | **Held take** | One deliberately long take of 10-13s bridging two clue beats. The only slow thing in the episode | sc04b, 12.5s |
| 40.0-50.0 | 45-55 | **Mid reveal** | A physical object, or VO truth the other characters do not get. If the protagonist speaks here, she lies | t=40.68-42.06 |
| 50.0-68.0 | 55-75 | **Escalation** | Move into the forbidden space. A group forms and pressures itself. Shots tighten | t=51.99-59.78 |
| 68.0-80.0 | 75-89 | **Confession** | One character says one true thing aloud; another reacts in a way that implies a secret of their own | t=67.49 "You've heard it before." |
| 80.0-84.0 | 89-93 | **Decision** | The protagonist refuses to wait. State the cost of waiting, then refuse | t=81.78 |
| 84.0-90.0 | 93-100 | **Cliffhanger** | End mid-**decision**, not mid-action: internal VO line framing a choice as irreversible, then a short ambiguous spoken line from an unidentified voice. Hold on her face and cut | t=84.07 "Choose carefully." |

Episode break hooks ranked by the reference (Ref: `episode_break_candidates`):
`reveal_cut_short` (strength 3) > `cold_open_mystery` (3) > `object_clue_reveal` (2).

## Story Bible (world-building template)

Reusable world devices, each with its reference evidence. Rebuild all of them inside the user's
world; never reuse the reference's content.

| Device | Pattern | Ref |
|---|---|---|
| **The closed world** | An isolated institution reached through a single threshold that locks behind the cast | forest gate, padlocked, claw-scratched |
| **The thing taken on arrival** | A gatekeeper confiscates the cast's means of contacting outside help, in the first minute, with no explanation offered | "Phones." / "All of them.", t=17.93 |
| **Five stated rules** | Exactly five, delivered in one scene by one authority. Four are ordinary prohibitions; the fifth is collective punishment and is the only one that matters | t=17.93-27.85 |
| **The collective-punishment rule** | If one of us is lost, all of us answer. It converts the peer group into mutual surveillance and gives every later scene a built-in pressure source | Rule Six, t=27.85 |
| **The forbidden place** | A named zone the rules prohibit, with a worse sub-zone inside it ("the part where the trees are dead") and exactly one warm light in it | t=56.4-91.33 |
| **The erased person** | Someone the institution removed from its own records, whose trace survives on a physical object | ELI / "STILL HERE", t=42.06 |
| **Scratched text as clue** | Carved, scratched or damaged writing on an object carries mystery information. Never deliver it as dialogue | t=42.06 |
| **Surveillance both ways** | Characters watch from inside through rain-streaked glass, and are watched back from a lit window | t=51.99, t=84.07 |
| **An unexplained gesture** | One recurring physical motif tied to fate or chance, performed by a character who never explains it | coin flip, t=37.83 |
| **A voice with no body** | Something calls to the protagonist and has done for years; its source is never confirmed | t=67.49 |

Locations: build **4**, each with a single-sentence look that fixes palette and light source — one
threshold, one institutional interior, one private night interior, one forbidden exterior.

Motifs: build **3-5**. At least one is introduced with no explanation and still unexplained at the
finale (Ref: `insights_for_writing` — let a motif accrue meaning rather than explaining it).

## Character Bible (role templates)

| Role | Tier | Screen % | Lines/ep | Plot function | How introduced | Want vs need | Voice pattern | Arc pattern | Ref |
|---|---|---|---|---|---|---|---|---|---|
| **Secret-mission protagonist** | main | 60-70 | 15-25 (VO + spoken) | Drives every scene; her VO narrates the world and withholds her true motive from everyone on screen while giving it to the viewer | In danger, mid-action, before she is anyone | Wants to find the erased person; needs to accept what connects her to this place | Cynical aphoristic VO; terse evasive spoken lines. The two tracks contradict each other | Guarded -> gives motive to viewer -> gives one secret to one ally -> refuses to wait -> chooses irreversibly | char_01 |
| **Roommate confidant** | supporting | 12-18 | 1-3 | The mechanism that gets the protagonist out of locked rooms; a protective presence carried without dialogue | One small protective action: wakes her, shushes her | Wants to keep her safe and unseen; no stated need | Whispers, fragments, two to four words | Stays close, then becomes the one with the most to lose | char_02 |
| **Probing ally** | supporting | 10-15 | 1-3 | Pressure, not company. Nearly exposes her lie; later receives her one confession | A question asked at the moment she is most exposed | Wants to understand; secretly shares her experience | Short questions aimed at her secret. Both of his reference lines are questions or accusations | Suspicious peer -> confidant -> the one who knows what she is | char_05 |
| **Reciting authority** | supporting | 8-12 | 3-5 | States the world's rules outright; owns the collective-punishment rule that peers later misuse | One unsoftened recitation. No backstory, no menace in delivery — all menace in content | Wants control; no interiority offered | Flat, measured, ominous. Declarative sentences, no contractions of feeling | Appears, states, recurs as consequence rather than as a person | char_04 |
| **Peer enforcer** | minor | 6-10 | 1-3 | Proves the authority has already won by repeating its language back to the group | Mid-crowd, rallying, using the authority's exact phrasing | Wants the group accountable; believes he is the responsible one | Assertive, rallying, blame-logic. Counts people out loud | Enforcer -> the one who leads a group into the worst outcome | char_06 |
| **Threshold gatekeeper** | minor | 6-10 | 1-2 | Takes away the means of escape at the entrance, before any rule is explained | Single-word orders. Never explains, never argued with | Wants compliance | One or two words at a time | Static; recurs at every threshold | char_03 |
| **Silent omen figure** | minor | 4-6 | 0 | Does nothing except accrue meaning. One gesture tied to chance or fate, no lines, no confirmed role | Inside the episode's longest take; gesture, smirk, no address | Unknown by design | None. Visual only | A debt the season cashes at 58-64% | char_07 |

Cast size: **6-8 named roles**. One main. **The protagonist holds ~63% of all lines** (Ref: 22 of
~35). Five of seven reference characters have **two lines or fewer**. Resist giving supporting cast
more voice — the economy is the style.

Visual signatures: write one for every character as a single comma-separated string covering build,
hair, eyes/skin, one distinguishing accessory, and clothing including whether they are in uniform or
out of it. Reuse it **verbatim** in every episode JSON (Ref: char_02 is deliberately out of uniform
so she reads as off-duty against the uniformed crowd).

## Storytelling Rules

| Rule | Ref |
|---|---|
| Open on a flash-forward of danger, then title-card rewind to the true start by a stated interval | sc01 t=0-9.53, card at 9.53 |
| Dual-track narration: spoken dialogue plus a VO that contradicts or undercuts it | t=27.85 vs t=34.26 |
| Spend exposition once: one authority states all world rules in one scene | t=23.09-30.53 |
| Plant the central mystery as a physical object with altered text, never as dialogue | t=42.06 |
| Let the protagonist lie on screen in the same scene where her VO tells the viewer the truth | t=40.68 then t=42.06 |
| Prove a stated rule's real consequence inside the same episode: authority states it, a peer weaponizes it | t=27.85 -> t=59.78 |
| Introduce allies through one small protective or curious action, not through dialogue | t=51.99, t=42.06 |
| Introduce authority through one defining line with no softening | t=17.93, t=23.09, t=37.83 |
| Use a recurring motif early with no explanation; let it accrue meaning across episodes | coin flip, scratch marks |
| End mid-decision, not mid-action: an internal unresolved choice plus a short ambiguous spoken command | t=84.07 |
| POV: first-person VO from the protagonist over third-person visual coverage. Never VO another character | `pov` field |

Any flash-forward must land within **2-3 episodes** of being shown, at the stated interval
(Ref: "48 HOURS EARLIER"). One season-level flash-forward is planted in the premiere and lands at
88-92% (projected).

## Pacing Guidelines

Measured on the reference episode (Ref: `craft.pacing`, `measured: true`):

| Metric | Value |
|---|---|
| Average shot duration | 2.47s |
| Median shot duration | 1.5s |
| Cuts per minute | 23.7 |
| Cut rhythm | fast |
| Shots per 90s episode | **~36** (24/min) |
| Shots per 60s / 120s episode | ~24 / ~48 |
| Act 1 average shot | 1.5s |
| Act 2 average shot | 2.6s |
| Act 3 average shot | 3.4s |
| Longest take | 12.5s, exactly one per episode |

Shape per episode: shots **tighten** through the first three quarters (1.53s / 2.73s / 2.42s
average) and **loosen** in the final quarter (4.81s) as the ending becomes dialogue-driven. Keep
every shot under 3s except the one held take.

## Tone & Voice Guidelines

Tone: suspenseful YA supernatural mystery. Energy builds from quiet dread to urgent nighttime
confrontation. Emotions in play: fear, secrecy, dread, resolve (Ref: `craft.tone`).

Dialogue budget (Ref: `craft.sound`):

| Metric | Value |
|---|---|
| Speech share of runtime | 58% |
| Words per minute, over total runtime | 151.8 |
| Words per 90s episode | **~225** (range 190-240) |
| Words per 60s / 120s episode | ~150 / ~300 |
| Average line length | 6-7 words |
| Longest line | ~14 words |
| VO share of words | ~55-60% (derived: char_01 holds 22 of ~35 lines) |

Rules: VO is literary, declarative and bitter; spoken dialogue is terse, urgent and often evasive.
No character except the protagonist gets a speech. Supporting characters get 1-3 lines per episode.
Never let a character explain the plot to another character — if information must move, move it on
an object or in VO.

Reference lines as style models (verbatim from the reference — **never copy into output**):

> "They call this place a school. Remember that. It's the first lie."
> "It means rich parents paying a fortune to throw their kids away politely."
> "The others were sent here to be forgotten. I came for the one they erased."
> "Six gone, six here."
> "Whoever I follow tonight becomes the one who knows what I am."

## Visual Guidance

### Camera

Shot size mix per episode (Ref: `shot_size_distribution` ECU 8 / CU 14 / MCU 9 / WS 6):
**CU ~38%, MCU ~24%, ECU ~22%, WS ~16%.** Faces dominate; wides are rare and used to locate or to
show scale of threat.

| When | How | Ref |
|---|---|---|
| A secret or VO reveal is delivered | Slow push-in to CU/ECU on the protagonist's face | sc04b, t=37.83-50.33 |
| Authority speaks the world's rules | Static frontal-symmetrical wide, slight low angle | sc04a, t=23.09-37.83 |
| Two clue beats need bridging | One held tracking shot of 10-13s, no cut | sc04b, 12.5s |
| Danger in the forbidden exterior | Fog-backlit wide, figures as silhouettes | sc01, sc06 |
| A time jump occurs | Graphic transition (rewind icon) over a drained-colour image | t=9.53 |

Movement: mostly static to light handheld. Angles: predominantly eye-level; frontal-symmetrical for
institutional spaces; slight low angle for authority.

Signature shots to reuse: ECU push-in on the protagonist's eyes; fog-backlit forest wide; graphic
rewind transition; frontal symmetrical wide of authority in front of a rules board.

### Color and lighting

Palette: cold teal-blue night exteriors with heavy fog; warm amber interiors from practical lamps;
one desaturated black-and-white insert at a clue beat.

| Where / mood | Look |
|---|---|
| Forbidden exterior at night (fear, danger) | Cold teal-green fog, backlit silhouettes, low-key |
| Institutional interior (institutional dread) | Warm amber lamp-lit interior against cold teal window light |
| Clue flash insert | Desaturated black-and-white |
| Private night interior (watching) | Cold blue moonlight through rain-streaked glass, one warm streetlamp accent |

Lighting: low-key, motivated practical sources only (lamps, window glow, streetlamp), heavy fog
diffusion, naturalistic rim and backlight on faces.

**Core rule:** warm light is reserved for enclosed, authority-controlled spaces; cold light for
exteriors and danger (Ref: sc04a warm hall vs sc01/sc06 cold forest). A single warm light inside a
cold exterior means something is watching.

## Sound Guidance

| Element | Rule | Ref |
|---|---|---|
| Speech density | ~58% of runtime carries speech or VO; the track is rarely empty | `speech_pct=58.1` |
| Voiceover | Present throughout, protagonist only. Place a VO line within 7s of any authority statement so it can undercut it | `voiceover: true`, t=30.53 -> 34.26 |
| Music | Low drone / ambient tension bed under VO and chase beats. **Inferred from visuals only — no music cue was confirmed in the reference transcript** | `music_style_guess` |
| Silence | Not used in the reference (`silence_count=0`). Tension is carried by VO and ambience, not pauses. Use silence only as a deliberate exception | `silence_usage` |
| SFX | Rain on glass, forest wind and ambience, a whoosh on any graphic transition | `sfx` |

## Hook Patterns

**0-3s (every episode):** an image of danger or rule-breaking already in progress, no context. The
first VO line is a flat declarative about a lie (Ref: t=0.58 + the "first lie" VO).

**Mid-episode (45-55%):** a physical object whose altered text reveals more than anyone says out
loud; the protagonist lies about it in the same scene (Ref: t=42.06, break candidate strength 2).

**Ending (93-100%):** mid-decision cut. Internal VO framing a choice as irreversible and
self-revealing, then a short ambiguous spoken line from an unidentified voice, then hold on the
face (Ref: t=84.07, break candidate strength 3).

**Season premiere:** the full flash-forward + title-card rewind, and five world rules stated in one
scene. **Season finale:** the same mid-decision ending at a larger scale, with two questions left
unanswered and one new name spoken for the first time (projected from the reference's ending type
`cliffhanger` and its 5 unanswered questions).

## Output Format

`episodes/epNN_vK.md`:

```markdown
# EP03 — <Title> (90s)
Logline: ... | Story beats: <template beats + %> | Cliffhanger: <type>

### SC1 [00:00-00:12] EXT. <PLACE> — NIGHT
| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.8 | ECU | char_01 ... | VO: "..." | handheld | teal fog | drone, breath |
```

`episodes/epNN_vK.json` (read by `/script-to-shotlist`):

```json
{
  "skill": "write-series-hollow-pine", "skill_version": "v1", "session": "<session-id>",
  "episode": 3, "title": "...", "total_duration_sec": 90, "aspect_ratio": "9:16",
  "characters": {"char_01": {"name": "...", "visual_signature": "..."}},
  "scenes": [{"id": "SC1", "start_sec": 0, "end_sec": 12, "location": "...", "int_ext": "EXT",
    "time_of_day": "night",
    "beats": [{"start_sec": 0, "end_sec": 1.8, "shot_size": "ECU", "characters": ["char_01"],
      "action": "...",
      "dialogue": [{"character": "char_01", "line": "...", "voiceover": true, "delivery": "whisper"}],
      "camera": "...", "lighting_color": "...", "sound": "..."}]}],
  "cliffhanger": "...", "ledger": {"opened": [], "clues": [], "answered": []}
}
```

`bible_vK.json`: `{title, logline, premise, theme, world: {setting, rules[], locations[], motifs[]},
cast: [{character_id, name, tier, role, want, need, flaw, secret, visual_signature, voice: {style,
sample_lines[]}}], ledger_plan: [{question, open_ep, clue_eps[], answer_ep}], relationships[]}`

`outline_vK.json`: `{episodes: [{episode, title, logline, beats[], template_beats: [{pct, function}],
reveal, cliffhanger_type, characters[]}], never_answered[]}`

## Self-check

- [ ] Every Story Template beat is assigned to an episode via `ceil(p/100 * N)`, and no episode holds more than 3
- [ ] Premiere contains: flash-forward, title-card rewind, means of escape removed, five rules in one scene, collective-punishment rule last
- [ ] The premiere's flash-forward lands at 88-92% of the season
- [ ] 4-6 mystery questions are open in every episode; one answered per 2-3 episodes; exactly 2 unanswered at the finale
- [ ] Each episode has a reveal or clue beat roughly every 17s (~5 per 90s)
- [ ] Every episode ends mid-decision: VO irreversible-choice line + short ambiguous spoken line + hold on face
- [ ] Each episode has exactly one held take of 10-13s, and no other shot over 3s
- [ ] Shot count matches ~24/min (~36 per 90s); shot mix ≈ CU 38 / MCU 24 / ECU 22 / WS 16
- [ ] Word count per episode within 190-240 for 90s; average line 6-7 words; protagonist holds ~60% of lines
- [ ] No supporting character exceeds 3 lines in an episode; no character explains plot to another
- [ ] Visual signatures appear verbatim from the bible in every episode JSON
- [ ] Warm light only in enclosed authority spaces; cold teal only outside; any lone warm light outside means something is watching
- [ ] At least one motif is still unexplained at the finale
- [ ] Scene timecodes sum exactly to `--episode-sec`

## Data limits

- **Sample size: one 91.3-second episode** (`Tập 1.mp4`, 1 analysis unit). This is the single largest
  limit on this skill. Episode-level craft — pacing, shot mix, palette, dialogue economy, hook and
  cliffhanger shape — is **measured**. Season-level structure beyond ~26% is **projected** from the
  reference's mystery ledger, open threads, stated devices, character flaws and reveal rhythm.
  Every projected Story Template row is labelled `projected`. Treat them as the documented default,
  not as evidence, and override them freely with `/refine-skill hollow-pine --feedback "..."`.
- **The reference does not resolve anything.** It opens 5 questions and answers 0. The
  "one answer per 2-3 episodes" rate is a chosen default, because the measured rate of zero cannot
  sustain a 10-20 episode season.
- **No character is named** in the reference — no name is spoken or shown on screen. All role
  templates are functional. Character names in output come from the user's idea or are invented.
- **Music is inferred from visuals only.** No music cue was confirmed from the transcript. Treat the
  drone/ambient bed as a suggestion, not a measured rule.
- **Speakers were not diarized** (no `HF_TOKEN`); speaker attribution came from frame analysis, so
  line counts per character are approximate.
- **`words_per_min = 151.8` is read as over total runtime**, not speech-only. That yields ~225 words
  per 90s episode, which matches the reference's ~35 short lines across 91s. If treated as
  speech-only it would be ~130 words; the higher figure is the documented default here.
- **VO-vs-dialogue word split was not measured.** The ~55-60% VO share is derived from line counts
  (char_01 holds 22 of ~35 lines), not from an audio track split.
- **Act boundaries within the episode are used as the premiere's shape**, not as season acts. The
  reference's 0-14 / 14-62 / 62-100% act split describes 91 seconds, not a season.
- **Silence is unmeasured as a technique** (`silence_count=0`), so this skill has no rule for it
  beyond "the reference does not use it."
- TODO (not in DNA): season length of the original series; whether episodes after the first keep the
  flash-forward device; music; any resolution of any question.

## Changelog

- v1 (2026-10-02T07:14:08Z): generated from `data/analyses/20261002-071408/dna.json`
  (`Tập 1.mp4`, 91.3s, 1 unit). Non-interactive run; all ambiguities resolved to documented
  defaults and recorded in Data limits.
