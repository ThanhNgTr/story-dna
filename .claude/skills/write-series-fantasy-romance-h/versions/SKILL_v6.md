---
name: write-series-fantasy-romance-h
version: v6
stable_version: v5
description: |
  Turn a rough or fragmented story idea into a 10-20 episode vertical series (60-120s episodes)
  told the way a fantasy-romance "humiliated then face-slapped" short drama is told: a 25-30s
  first-person pitch that gives away the twist up front (dramatic irony), a poor kind heroine
  humiliated by a villain three times before ever-bigger crowds, a lonely privileged child who
  becomes her matchmaker, a cold all-powerful male lead whose body betrays the feelings his mouth
  denies, kindness shown through hot food instead of words, and a public power reversal that makes
  the villain repeat his own insult. Signature craft: near-continuous wry first-person VO, ~30
  cuts/min (2s shots, 55% CU/ECU), grey-teal for the human world and gold only for power. Use
  whenever the user wants to develop an idea, notes, scattered scenes or a draft into a series,
  season outline, episode scripts or screenplay in this style, even if they only paste fragments.
  Output: series bible + season outline + episode screenplays (md + json).
---

# Write Series: Fantasy Romance H

Learned from: `data/analyses/20261012-015632/dna.json` + `film_analysis.json` — `phim .mp4`,
2842.17s, 24 units. The file is ONE ~1422s story played twice; every % here is on 1422s (A3).
Reference plot: `references/reference-story.md`. Cast: `references/reference-characters.md`.
Audit and retention study: `references/film-analysis.md`. Read Data limits before trusting numbers.

## Quick Start

```
/write-series-fantasy-romance-h --idea "..." | --idea-file notes.md [--episodes 12] [--episode-sec 90]
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

## Story Contract (overrides this skill on conflict)

Every series must be a complete story: `.claude/skills/story-contract/references/story-contract.md`.
Main plot with one central question, start -> `happy` or `bad` ending shown in the last episode,
1-2 main characters + >=2 supporting characters tied to them, dialogue in every episode, setting
and how it changes (`setting_timeline`), climaxes (midpoint + final, never >3 episodes without
one), mysteries opened -> clued -> answered (only 1 minor question may stay open). The style rules
below decide HOW it is told; where one says "nothing is resolved" or "leave questions open", it
applies to episodes 1..N-1 only. Check: `python3 .claude/skills/story-contract/_story_check.py
<session-dir>` -> 0 errors.

## Workflow

Session dir: `data/series/fantasy-romance-h/<session-id>/` (session-id = UTC `YYYYMMDD-HHMMSS`).
Save `input.json` first: the raw idea, every flag value, and this skill's version.

### Stage 1 — Adaptation map (adaptation.md)

1. Extract every element from the idea: premise, characters, places, scenes, lines, endings, themes.
2. Map each onto a Story Template beat and a Character Bible role.
   Table columns: `user element | beat/role function | reference analog`.
3. Empty beats/roles: invent something original for the user's world, marked `[from template]`.
4. Conflicts: the user's idea wins. Adjust the template and note why in one line.
5. Name the six fixtures this style cannot run without, from the user's world (invent if missing):
   **the vertical class order** (who is "above", who "below"), **the heroine's concrete wound**
   (said aloud by the villain as one line), **the warm object** (food/drink that is love),
   **the power color + body tells** of the powerful kind, **the visible bond** (a sign that cannot
   be faked), **the wound keyword** (one word she uses against herself, he later reverses).

### Stage 2 — Bible + outline (bible_v1.md/.json, outline_v1.md/.json)

- **Bible:** title, logline, premise, theme, world rules (4-6, incl. the class order and the bond
  sign), locations with look, cast (tier, role, want/need/flaw/secret, visual_signature, voice + 2
  sample lines, body tell), irony + mystery ledger plan (question -> clue episodes -> answer
  episode), relationship ladders, the three humiliation rungs with their witnesses, motifs (3-5).
- **Outline:** one row per episode — title, logline, beats, which Story Template beat(s) it carries
  (% position), reveal/clue, cliffhanger type (Hook Patterns), characters.
- **Spread:** beat at p% -> episode `ceil(p/100 * N)`; no episode carries more than 3 beats.
- **Minors on screen (before planning)**: read `.claude/skills/story-contract/references/minors-on-screen.md`. A child character
  (the matchmaker) gets daylight / early-evening scenes in open or shared places; no sleep, bed or
  touching with an adult, no secret phone contact at night, a hand habit instead of a mouth habit (bible
  `tell`). Every outline row with a minor on screen names when and where. Video tools refuse the rest.
- **Looks**: after the bible, run `/series-assets --session <session-dir>` (bible-only) ->
  `assets/assets_v1.md/.json`: fixed face/hair/body per character, default + planned outfits,
  canonical locations with day/night variants, key props (the warm object, the summoning device,
  the bond mark). Show it with the outline; look feedback goes to `/series-assets --feedback`.
- **Dialogue setup**: the bible also has `address_matrix` (xưng hô per character pair) and
  `glossary` (ONLY invented/unusual terms + how a character or sign makes them clear; never
  everyday words like jobs, objects, places), and `voice.style` in the
  screenplay's language (see `.claude/skills/dialogue-polish/references/vi-dialogue.md`).
- **Cause chain (outline)**: every outline row has `events` (1-4, ids `E<ep>.<k>`: what HAPPENS),
  `because` (episodes 2..N: earlier event ids that make this episode happen; chance is not a cause)
  and `opens_from` (how its first seconds pick up the previous cliffhanger), per
  `.claude/skills/story-continuity/references/continuity.md`. A humiliation rung, a warm-object
  callback or the matchmaker's scheme happens because of something someone did before.
  `python3 .claude/skills/story-continuity/_continuity.py check <session-dir> --stage outline` -> 0 errors.
- **Story contract (outline)**: bible + outline carry the contract fields (`main_plot`, `ending`,
  `relation_to_main`, `arc`, `setting_timeline`, `climaxes`, ledger `tier` + `answer`; outline
  `act`, `main_plot_step`, `locations`, `setting_change`, `climax`). Then
  `python3 .claude/skills/story-contract/_story_check.py <session-dir> --stage outline` -> 0 errors.
- STOP and show the outline unless `--auto`. The user approves with
  `/refine-skill fantasy-romance-h --approve outline` or gives feedback.

### Stage 3 — Episodes (episodes/epNN_v1.md/.json)

- Each episode follows the Episode Template and every rule section below.
- Write against the asset registry (latest `assets/assets_vN.json`), following
  `.claude/skills/series-assets/references/episode-contract.md`: every scene has `loc_id`,
  `variant_id`, `cast` (outfit per on-screen character), `referenced`, `props`; anything new goes in
  `new_assets`. Subagents get the registry path and the contract path too.
- N > 6: write in parallel with general-purpose subagents, 3-4 consecutive episodes each. Give each
  the bible, the outline (its `events` / `because` / `opens_from` are the contract between writers:
  an episode shows its own events and opens from the previous row's cliffhanger as planned), this
  SKILL.md path, `.claude/skills/story-continuity/references/continuity.md` and its episode numbers.
  Episodes written while others already exist (a second wave, missing episodes) read the latest
  `continuity/state_vN.md` first: who knows what, who holds what, which day it is.
- Seam pass after all writers replied: `python3 .claude/skills/story-continuity/_continuity.py seams <session-dir>`;
  at every package boundary (and any pair that does not join) rewrite the first scene of the later
  episode so its first 3s continue the exact cliffhanger moment of the episode before (Episode
  Template "Hook").
- Continuity pass after all episodes: names, visual signatures (verbatim from the bible), ledger
  timing, humiliation-rung wording (the payoff must quote rung 3), warm-object callbacks, timecodes
  summing to `--episode-sec`. Then build the state ledger (`/story-continuity` "Check + repair"
  step 3: `continuity/state_vN.json` from the written episodes) and
  `python3 .claude/skills/story-continuity/_continuity.py check <session-dir>` -> 0 errors (story
  breaks fixed in the episodes, not in the ledger).
- Then `python3 .claude/skills/series-assets/_assets.py lint <session-dir>` -> 0 errors, and
  `/series-assets --session <session-dir>` (scene map, `new_assets` get real IDs, drift report).
- Minors on screen: re-read `.claude/skills/story-contract/references/minors-on-screen.md` before writing an episode with a child;
  `_action_lint.py` flags `minor_risk` (night scene, sleep / bed / touching / bare skin / crying / secrecy /
  body words with a child on screen) as strict: 0 before the episode is done. Subagents get the path too.
- Acting: every beat carries `acting` (per visible character, listener included: `does` = body +
  hands, `face`, `holds` = what is in hand) and every 2+ character scene a `blocking` line, following
  `.claude/skills/action-polish/references/screen-action.md`: lines are said WHILE doing something
  (rót trà, gắp đồ ăn, siết quai túi); the heroine's hem-tug and the lead's body tells land at their
  turns; objects stay in hand until a beat puts them down. Then
  `python3 .claude/skills/action-polish/_action_lint.py lint <session-dir>`: `missing`, `prop_vanish`,
  `no_blocking` = 0. Subagents get the guide path too.
- Dialogue: `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session-dir>`; rewrite
  flagged lines that fail `.claude/skills/dialogue-polish/references/vi-dialogue.md`. `definition`
  and `narrates_action` flags must be 0: a line that explains a word or retells the shot is cut,
  shown, or turned into speech between the characters on screen.
- Story contract: `python3 .claude/skills/story-contract/_story_check.py <session-dir>` -> 0 errors.
- Write `series.md` (index + all episodes) and reply with: outline table, open threads, file paths.

## Story Template (season arc)

Reference positions are measured on the 1422s story (13 reference episodes ~ one season). Rows
marked `projected` are added so the season resolves (story contract); the reference ends on a cut.

| % | Beat function | Why it works | Ref |
|---|---|---|---|
| 0-2 | Pitch VO 25-30s: world order -> heroine's wound -> accident -> surprising companion -> identity twist -> promised relationship. Twist told now | Viewer watches for WHEN she finds out, not WHAT; every scene she does not know becomes suspense | 0-29s pitch, A5 |
| 3-7 | Humiliation rung 1 (private, street): villain + new partner mock her concrete wound; she freezes. VO: she is numb | Debt opens; wound is concrete and spoken | 81 metro; 93.5 "hoàn toàn vô cảm" |
| 8-10 | A friend's urgent favor drops her into the other world; she accepts because "life can't get worse" | Accident with consent: she chooses the door | 118 "Cháu trai nào cơ?"; 148 |
| 13-17 | Finds the privileged child alone and abandoned; he rejects her and says the theme as his wound ("you all price me") | Theme spoken once, by the wounded side character | 186, 216, 244 |
| 18-22 | She answers with a warm object and silence, not questions; he lets her in (hand). Home: cheap warm place, food, his species tell shows | Kindness that costs her something; first rung of the child ladder | 255-278 cocoa; 298-331 ribs, horns |
| 24-26 | Calm VO "for the first time today things felt light" -> rung 2 (private, by phone): villain's message hits her wound; she cries | Warm then stabbed; fixed bad-news channel = phone | 339 -> 362 voicemail |
| 28-30 | The child defends her by listing her actions, names himself, brags about his powerful relative | First person on her side; clue to the power above | 392 "Hắn sai rồi", 420 |
| 32-35 | Child's secret decision, then secret summons with a deadline | Hidden plan = forward pull; deadline replaces events | 451-475 tail; 502-509 watch call |
| 38-40 | Child's motive told (wants to stay; wants the powerful one to see her worth) | Short mystery (~6%) paid fast; keeps the matchmaker active | 534-561 VO, A6 |
| 41-44 | Powerful male lead's arrival as spectacle: distant sign, landing, boots-to-face reveal | Entrance grammar makes power felt before a word | 583-632 meteor |
| 45-48 | She wants to hide; the child names her flaw aloud; she suspects she was set up | Wound named by an outsider before the lover can see it | 647, 679 |
| 50-54 | MIDPOINT CLIMAX: he enters her poor home; the bond flares visibly (audience told what it means, she is not) | Second irony layer opens as the first one (who he is) is answered | 704 enter; 770 aura |
| 55-58 | Matchmaker exposes him ("you like her"); he denies with clumsy logic; tell (red ears) | Mouth denies, body confesses: comedy + secret shared with viewer | 797-800 |
| 60-67 | He refuses her food, then his body betrays him and he cleans the plate; lame excuse. She hides her body/wound | Warm object unlocks the second, more powerful character | 852; 883-956 |
| 68-73 | Small touch (hands over a tissue), tell again; he finds a reason to stay the night | Touch ladder rises one rung; he steps forward, she does not notice | 978, 1031-1036 |
| 74-77 | Most peaceful moment -> a third person reveals by phone who he really is, wrapped in a threat ("he can crush you; don't look like a gold-digger") | Satisfies curiosity and creates the new wall in one beat | 1059-1065 -> 1090-1117 |
| 79-82 | She lies ("nobody called"), pushes him away with the wound keyword ("we're not the same world") | Her inner flaw becomes the antagonist; conditional misunderstanding, short | 1147-1169 |
| 83-84 | He reverses the keyword with power ("if I say we're the same world, we are") + promise "I'll be there" -> duty pulls him away | Promise with a condition = loaded gun for the climax | 1178, 1198 |
| 85-90 | Rung 3 (public, crowd): villain humiliates her in front of witnesses with a refutable claim ("no man of rank would ever claim you"); friend defends; she breaks | Max debt, same witnesses who will see the payoff | 1205-1307 |
| 91-92 | `projected` Heroine's active choice inside the climax: she steps in front of the child / answers back once | Fixes the reference weakness (she is saved, does nothing); contract agency | weakness: "Nữ chính bị cứu hai lần" |
| 93-95 | Villain insults the child; child's power erupts (spectacle); the male lead arrives by the same grammar, twice as fast | Promise paid; entrance reflex "he's here" | 1317-1357 |
| 96-98 | FINAL CLIMAX: public reversal: villain forced down, he claims her in front of the same crowd, power mark glows, he makes the villain repeat his own insult | Payoff uses the villain's exact line at the same level of publicity | 1380-1410, A8 |
| 98-100 | `projected` Resolution: she learns the bond (the pitch's promise is paid), chooses on screen (accept = happy / refuse or loss = bad), villain's sentence carried out, child's home question answered | Contract ending; pitch promise must be paid (film_analysis risk) | ending TODO (not in DNA) |

Acts: 1 = 0-10%, 2 = 10-34%, 3 = 34-67%, 4 = 67-100% (A3; DNA act 5 is the repeat, dropped).
Outline `act` field (story contract, 1-3 only): style act 1 -> 1, acts 2-3 -> 2, act 4 -> 3.
Climaxes: midpoint 50-54%, final 93-98%; between them keep a "mini-climax" every <=3 episodes
(spectacle arrival 41-44%, identity reveal 77%, rung 3 at 85-90%).

### Mystery / reveal ledger pattern

- Two kinds (A5): **irony** (viewer knows from the pitch, heroine does not; held 70-100% of the
  season) and **mystery** (viewer does not know; held 6-50%).
- Keep 2-5 questions open at once (ref 3, 4, 5, 3, 2, 3, 3). Never answer one without opening
  another in the same episode (704 answers "who is the balcony man", 770 opens the bond).
- Withhold: child-motive mystery ~6% (468 -> 558); balcony teaser ~48% (26 -> 704); identity irony
  ~75% (25 -> 1090); bond irony to the finale.
- Ratio ~7 opened : 4 answered in the reference; contract: all answered by the finale except 1 minor.
- Answer channel: a third person by phone (identity), VO (motive), action (promise kept).

### Subplots

| Function | Setup % | Payoff % | Ref |
|---|---|---|---|
| Self-worth wound (spine) | 7 | 97-100 | 93 -> 1385 |
| Matchmaker's hidden plan | 32 | 39 (VO) / 56 (exposed) | 451 -> 558, 797 |
| Warm object = love (opens child, then lead) | 18 | 64 | 255 -> 910 |
| Humiliation ladder + face-slap with villain's own line | 2-6 | 96-99 | 81, 362, 1205 -> 1410 |
| Friend: favor -> warner -> defender | 7 | 77 / 92 | 104, 1090, 1306 |
| Lead hides feelings: tell -> excuse -> stay -> public claim | 54 | 97 | 770 -> 1385 |
| `projected` Who abandoned/"prices" the child (contract answer) | 17 | 98-100 | 241, open in ref |

## Episode Template (60-120s)

Reference episodes: 66-132s, mean ~109s, 2-3 story-changing events each (film_analysis cuts).
Seconds below for 90s; scale per Scaling.

| Time | Beat | Rule | Ref |
|---|---|---|---|
| 0-3s | Hook | Continue the exact frame/line of the last cliffhanger; no long recap (premiere: world-order line over a spectacle frame) | ep2 opens "Cháu bên nhà chồng mình" |
| 3-15s | Payoff prev | Answer part of last episode's question, widen it into a new one | blurry photo -> "right child?" |
| 15-40s | Setup | VO sets the episode's small goal + one wound detail | sweater hem 852 |
| 40-65s | Turn | Story-changing event #1: reaction against expectation (refusal, denial, bad news) | 216, 892 |
| 65-80s | Reveal | Event #2: new info or a new body tell; one short closing line | 797, 978 |
| 80-90s | Cliffhanger | One of 5 types (Hook Patterns); cut BEFORE the reaction | 119, 358, 590, 1319 |

- Scaling: 60s -> setup 10s, keep 2 events. 120s -> add one warm/comic pocket of 20-25s between
  turn and reveal (ref 333-339 stealing fruit on the sofa before the voicemail).
- Event every 30-45s (ref median 38s), micro-beat (tell, VO button, reaction) every ~20-25s
  (`reveal_rhythm_sec` 23).
- No two consecutive episodes end on the same cliffhanger type.
- A humiliation/pain episode is followed by a warm or comic one within 1 episode (362 -> 392).
- Recap at most 3-5s (the reference's full replay is padding, do not copy).

## Story Bible (world-building template)

| Device | Pattern | Ref |
|---|---|---|
| Vertical class order | The powerful kind lives ABOVE (sky, towers, floating mansion); humans scrape by below. Gap is said as space: "ground under my feet vs sky above the clouds" | 0.07; 1123 |
| Species tells | Powerful kind has involuntary body signs (horns, tail, slit eyes, red ears, scales) that betray emotion | 316, 468, 797 |
| Visible bond | Meeting a destined mate triggers a sign that cannot be faked; viewer is told, heroine is not | 765-794 |
| Power that bends people | Pressure forces kneeling; a mark glows when protecting | 1380-1385 |
| Families hand children off | Powerful families send kids to relatives/academies; a child can be left alone | 119.87, 186 |
| Higher authority | A council can summon even the ruler -> separates the couple before the climax | 1174-1198 |
| Locations | public transit gate (humiliation, cold); elite academy gate (gothic fog, supercars); heroine's tiny flat (taped window, velvet sofa, amber lamp: the warm base); empty lot behind the block (landing stage, puddles); upscale glass café (public stage, glass to shatter); floating mansion (mentioned, cold) | world.locations |
| Motifs | above vs below; gold vs grey; hot food/drink = love; hands; worn sweater + hem tug; phone = bad news; body betrays feeling; seen vs hiding; shattered glass + kneeling | world.motifs |

## Character Bible (role templates)

Contract tiers: main = heroine + male lead; child, friend, villain = supporting (each tied to her).

| Role | Function | Screen | Intro | Recognizable by | Want vs need | Voice | Arc | Ref |
|---|---|---|---|---|---|---|---|---|
| Heroine-narrator (main) | Ordinary human whose kindness unlocks the powerful | ~43%, ~70% of lines (mostly VO) | Pitch VO + concrete wound before any action | worn soft clothes, one muted color, hem-tugging tell | survive unseen vs believe she deserves to be seen and chosen | wry self-mocking VO; warm with child; stiff-formal with lead | numb -> kind act -> named -> pushes away -> claimed publicly (+ `projected`: chooses) | Linh Khuê |
| Child matchmaker (supporting) | Causes the meeting, carries the theme, says what the couple won't, triggers the climax | ~27% | Alone, hostile: "I don't know you" | species tells, crest uniform, a summoning device | stay / not be priced vs someone who actually comes for him | short, blunt, bossy; serious when true; one exposing line per episode | hostile -> hand -> defends -> plots -> explodes to protect | Cảnh Viêm |
| Cold powerful lead (main) | Romantic object + power savior | ~19%, fewest lines | Teaser silhouette -> summoned -> spectacle -> boots-to-face -> enters her home | gold/power color only on him, 1-2 tells (red ears, aura, mark) | keep dignity, keep her vs admit feelings and say them | deep, clipped, formal; clumsy logic to deny; absolute verdicts | denial -> body betrays (eat, stay) -> keyword reversal -> public claim | Cảnh Uy |
| Best friend (supporting) | Favor that starts it, info channel + warning, witness who defends | ~7% | Panicked phone call | one strong outerwear look | fix her mistake | rushed, exclamations; sharp when defending | favor -> warn -> defend | Hân Nghi |
| Villain ex (supporting) | Voice of society on her worth; 3 rungs; his insult = setup of the payoff | ~5% | Arm in arm with new partner, mocking | spotless expensive look vs her worn clothes | show status (`projected`: give a concrete gain + reason to be there) | condescending, theatrical, longest lines | smug -> bullies remotely -> slurs the child -> kneels | Thế Khang |
| Villain's partner (minor) | Chorus of contempt | ~2% | With villain | diamonds, satin | show off | fake-sweet, loud | - | char_06 |
| Crowd (minor) | Same witnesses for humiliation and payoff | ~2% | - | uniforms | - | none | - | char_07 |

Introduce side characters hostile first, softened by one small act, never by explanation (216 ->
255 -> 273). Each character gets one body tell instead of stated emotion.

## Storytelling Rules

- **Pitch then retell**: 25-30s VO pitch gives premise + twist, then the story restarts in order
  (A5). The pitch must not contradict the body (A12) and its promise must be paid in-season.
- **Dramatic irony over mystery** for the big secrets; short real mysteries for side motives.
- **VO first person, frequent**: inner life, wry jokes, judgments, time jumps ("Chiều tối hôm
  sau," + something only she can say), one-line VO "button" after each beat ("Lần này, nó không hất
  ra nữa."). VO says only what the image can't: never retells the action of the same beat, never
  sets a scene the shot shows, never defines a word. World rules come from characters (an order,
  a threat, a sign), not from VO explanations.
- **Exposition by third person on the phone**, wrapped in a threat (1088-1117).
- **Warm then stabbed**: end each warm scene with a VO line declaring peace, then the bad-news
  channel (phone) rings (339 -> 341; 1065 -> 1065.86). Vary sender and type of news.
- **Humiliation ladder**: 3 rungs, witnesses grow (private street -> private phone -> public
  crowd); rung 3 is a refutable claim; payoff = the act before the same crowd + the villain's line.
- **Insult = prophecy** (A8): the villain's contempt describes her real virtue ("good for babysitting
  and cooking"); the story proves it is what wins.
- **Keyword reversal**: she says the wound keyword twice (two pain levels), he reverses it once.
- **Matchmaker exposes**: each episode the child gives one short line that exposes one of the couple.
- **Mouth denies, body confesses**: cold statement -> tell -> someone calls it -> lame reason; each
  denial clumsier, each tell leads to a bigger act (eat -> stay -> public claim).
- **Entrance grammar**: summon -> deadline -> distant spectacle -> bottom-up reveal; reuse once at
  the climax, twice as fast. Max 2 full spectacle entrances per season.
- **Avoid** (film_analysis weaknesses): full replays/padding; POV leaks (pick: VO knows only what she
  can know, or let another character say it); villain without motive arriving by coincidence;
  heroine with no action in the climax; logic holes about guarding a precious child (give a stated
  reason tied to the "who prices him" mystery); unpaid pitch promise; body-shaming and stock class
  slurs as the wound (choose a wound specific to her); VO narrating the visible action; 100s+
  stretches with no event (ref 797-910 sags).

## Pacing Guidelines

| Metric | Value | Ref |
|---|---|---|
| Avg / median shot | 1.99s / 1.9s | craft.pacing |
| Cuts per minute | 30.2 -> ~45 shots per 90s, ~30 per 60s, ~60 per 120s | 1430 shots / 2842s |
| By act | act 1 1.7s; acts 2-3 2.1s; act 4 2.05s | by_act (estimates) |
| Fastest | pitch/intro 1.52s; phone cross-cuts ~0.5s | cut_rhythm_notes |
| Slowest | apartment dialogue 2.2-2.5s; longest shot ~5.7s (never longer) | cut_rhythm_notes |
| Cut type | hard cuts only; one shot per subtitle/VO phrase | cut_rhythm_notes |
| Story events | every 30-45s; micro-beat every ~23s | film_analysis reveal_cadence |

## Tone & Voice Guidelines

- Tone: fantasy romance melodrama with warm comedy; humiliation/loneliness -> chosen family ->
  romantic comedy -> face-slap power fantasy. Energy high at the pitch and each arrival, medium at
  home, explosive at the climax. Emotions: shame, numbness, tenderness, embarrassed comedy, awe,
  possessiveness, gloating.
- Speech: VO near-continuous (~85-95% of runtime, inferred A2); ~224 words/min over runtime ->
  ~330 words per 90s in the reference (TTS-read). Here the limit is vi-dialogue.md "Speech rate":
  <= 5.0 syllables/s over any line or scene (comfortable 3.5-4.5); fewer, clearer lines beat speed.
- Lines: VO ~65-75% of all lines in the reference (inferred, TTS-read). Here: the pitch may be
  all VO; after it, VO <= ~50% of lines and every scene with 2+ characters on screen has a spoken
  exchange (vi-dialogue.md rule 16). Spoken lines 3-12 words; villain longest (15-25);
  male lead fewest and shortest (power = few words); VO 8-30 words.
- Patterns: denial + action proof ("Hắn sai rồi... Nhưng cô đã không làm vậy."); list of actions
  instead of praise ("Cô đã đến đón tôi. Cô cho tôi ăn."); clumsy-logic denial; rhetorical question
  at the wound; keyword reversal; one-line VO button; verdict as a short command.
- Style examples (attitude only):
  - "Đời tôi lúc này đâu thể tồi tệ hơn được nữa." (heroine VO, 151)
  - "Các người đều giống nhau. Cứ hỏi tôi là ai, rồi định giá tôi đáng bao nhiêu." (child, ~241)
  - "Anh không có, chỉ là trong này hơi nóng..." (lead, 800)
  - "Ở thành phố này, nếu tôi nói chúng ta cùng một thế giới thì chính là như vậy." (lead, 1178)
  - "Thử nói lại lần nữa xem." (lead, 1410)

### Dialogue language (overrides the numbers and lines above on conflict)

Vietnamese (or any non-English) screenplay: follow `.claude/skills/dialogue-polish/references/vi-dialogue.md`. Clarity first: the viewer watches
once on a phone; hide facts, not grammar. The reference lines above show ATTITUDE only: never
translate their sentence shape. Line lengths above are averages, not caps: a line may run to ~18
words when it needs to be clear. No chains of noun fragments, no riddle lines, at most 1-2 VO
metaphors per episode, xưng hô fixed by the bible `address_matrix`. Lines are speech, not
description (rules 14-16): characters talk TO each other for a reason; VO says what the image
cannot; invented terms become clear in use, everyday words are never explained. Imitate the newest hand edits in `data/dialogue_examples.json` when it
exists (how this reviewer rewrites lines).

## Visual Guidance

Aspect 9:16. Shot mix: CU 38%, ECU 17%, MS 17%, MCU 15%, WS 11%, insert 1%, OTS/EWS <1%.
Movement: mostly static or slow push-in/drift; light handheld on streets and calls; no whip pans;
rack focus indoors. The cut carries the rhythm.

### Camera

| When | How | Ref |
|---|---|---|
| Small emotion or comic detail | ECU/CU on ears, hands, eyes, food (~55% of shots CU/ECU) | 200, 797, 928 |
| Powerful character shows power | low angle, bottom-up reveal boots -> face, ECU slit eyes, rim light | 599-632, 704-720, 1357-1383 |
| Heroine humiliated | OTS from her looking up at the villain, CU crying face, cold grey background | 1231-1306 |
| Phone call / urgent reveal | fast cross-cut (~0.5s), handheld, CU lips/screen | 103-123, 1087-1120 |
| Class gap | WS / high angle on the city or an empty street | 1136-1141 |
| Signature inserts | ECU red ears; ECU slit eyes; ECU summoning device; ECU hot cup; ECU full plate then clean plate; ECU glowing mark; WS powerful kind over the city | signature_shots |

### Color and lighting

- Palette: desaturated grey-teal for the human world and humiliation; beige/dusty pink/olive for the
  heroine; black + cream for the rich; gold/amber ONLY for the powerful kind (horns, embroidery,
  eyes, lightning, aura); warm amber indoors at her home.
- Gold appears exactly when a powerful character reveals power (583-632, 770, 1337-1357).
- In a cold scene the only warm spot is the hot drink/food (cocoa in a grey alley 255; ribs 298).
- Looks: street/transit = cold grey, wet reflective ground; academy = blue gothic fog, warm bokeh,
  gold in eyes/horns; her flat = tungsten amber + teal TV glow at night; his arrival = white-blue
  backlit hallway, rim light, gold flare on the bond; café = teal on the victim, amber bokeh on the
  villains, darkening as the child's anger rises, then gold backlit smoke on the explosion.
- Lighting: soft overcast outside; practical/candle warmth inside; rim + gold glow only with power.

## Sound Guidance

- VO near-continuous (inferred A2; DNA speech_pct 32.3% is an ASR artifact). Short sharp spoken lines.
- Music (inferred, not measured): trailer fantasy-romance bed on the pitch; sad piano/strings when
  alone; tense drone/strings + stinger at confrontations; impact boom + orchestra on arrivals and
  power; light comic cue at food scenes.
- Silence: the only verified silence is ~4s before the end card (1419.84-1424.02). Use 1 hold of
  silence max per episode, before the verdict/cut. The DNA rule "4-5s silence before a verdict"
  inside scenes is unverified (A2).
- SFX: phone buzz/voicemail, school bell, lightning crack on landing, doorbell/lock click, glass
  shatter, table slam, boots crunching glass, plates and cutlery, cartoon TV.
- Spectacle SFX doubled as a caption ("ĐOÀNG!", 1337).

## Hook Patterns

- **0-3s premiere**: one line stating the world order over a spectacle frame (powerful kind over the
  city) -> metro/street of the heroine (first cut ~2s).
- **0-30s premiere**: pitch montage ~1.5s/shot: wound, villain couple, companion with warm object,
  teaser silhouette of the lead; VO ends on the relationship promise.
- **0-3s other episodes**: the exact frame/line after last episode's cut.
- **Mid-episode**: a body tell or a refused offer at 40-65s; matchmaker's exposing line.
- **Ending (rotate, never the same type twice in a row)**: (1) threat about to explode (239, 1319);
  (2) bad news crashes a calm moment (358, 1104, 1205); (3) withheld info / silent decision (119,
  475); (4) power arrival / spectacle (590, 718); (5) comic suspense (909 "Anh im lặng một
  thoáng."). Cut BEFORE the reaction.
- **Finale** (ep N): opens on the verdict cut ("say it again"), then resolution: the villain's
  sentence, the heroine learns the bond and chooses, the ending shown; `cliffhanger_type:
  "resolution"`. The reference never shows this (projected).

## Output Format

`episodes/epNN_vK.md`:

```markdown
# EP03 — <Title> (90s)
Logline: ... | Story beats: <template beats + %> | Cliffhanger: <type>

### SC1 [00:00-00:12] EXT. <PLACE> — NIGHT  {loc_01 · char_01:o1}
| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.8 | ECU | <frame / event><br>**Name**: <does>; mặt: <face>; cầm: <holds> | VO: "..." | static push-in | grey-teal, wet street | phone buzz |
```
(`python3 -m app.pipeline.screenplay render <session-dir> <N>` writes this md from the JSON; a scene's
`blocking` prints as a `Vị trí:` line under its heading.)

`episodes/epNN_vK.json` (read by `/script-to-shotlist`):

```json
{
  "skill": "write-series-fantasy-romance-h", "skill_version": "v5", "session": "<session-id>",
  "episode": 3, "title": "...", "total_duration_sec": 90, "aspect_ratio": "9:16",
  "logline": "...", "story_beats": "<template beats + %>", "cliffhanger_type": "<hook pattern name>",
  "characters": {"char_01": {"name": "...", "visual_signature": "<bible, verbatim>", "outfits": ["char_01_o1"]}},
  "scenes": [{"id": "SC1", "start_sec": 0, "end_sec": 12, "location": "<registry name>", "loc_id": "loc_01", "variant_id": "loc_01_night",
    "cast": {"char_01": "char_01_o1"}, "referenced": [], "props": ["prop_01"], "int_ext": "EXT", "time_of_day": "night",
    "blocking": "<who is where, facing whom, what is within reach>",
    "beats": [{"start_sec": 0, "end_sec": 1.8, "shot_size": "ECU", "characters": ["char_01"], "action": "...",
      "acting": [{"character": "char_01", "does": "<body + hands>", "face": "<visible expression>", "holds": "<in hand at beat end, or empty>"}],
      "dialogue": [{"character": "char_01", "line": "...", "voiceover": true, "delivery": "wry"}],
      "camera": "...", "lighting_color": "...", "sound": "..."}]}],
  "new_assets": [], "cliffhanger": "...", "ledger": {"opened": [], "clues": [], "answered": []}
}
```
Last episode adds `"ending": {"type": "happy|bad", "central_question_answer": "..."}`. A scene told as a flashback
adds `"flashback": true` (continuity: the dead and the gone may appear there).

`bible_vK.json`: `{title, logline, premise, theme, world: {setting, rules[], locations[], motifs[]},
cast: [{character_id, name, tier, role, want, need, flaw, secret, tell, visual_signature, voice:
{style, sample_lines[]}}], ledger_plan: [{id, question, kind: irony|mystery, tier, open_ep,
clue_eps[], answer_ep, answer}], humiliation_rungs: [{ep, witnesses, line}], wound_keyword,
warm_object, relationships[], address_matrix, glossary}` + story contract fields (main_plot, ending,
setting_timeline, climaxes, cast relation_to_main/arc/secret_reveal_ep).

`outline_vK.json`: `{episodes: [{episode, title, logline, beats[], template_beats: [{pct, function}],
reveal, cliffhanger_type, characters[], act, main_plot_step, locations[], setting_change, climax,
ledger, events: [{id, text}], because[], opens_from}], never_answered[]}`; last episode `ending` +
`cliffhanger_type: "resolution"`.

## Self-check

- [ ] Every Story Template beat is placed via `ceil(p/100 * N)`; no episode holds more than 3
- [ ] Ep 1 opens with a 25-30s pitch that states the twist and the relationship promise; the pitch
      matches the body and its promise is paid in the finale
- [ ] Three humiliation rungs with growing witnesses; rung 3 is a refutable claim; the payoff
      happens before the same crowd and quotes rung 3
- [ ] Heroine makes at least one active choice in the final climax (not only rescued)
- [ ] 2-5 questions open in every episode 1..N-1; nothing answered without a new one opened;
      at the finale at most 1 minor question open
- [ ] Each episode: >=2 story-changing events, micro-beat ~every 23s, cliffhanger type differs from
      the previous episode; pain episode followed by a warm/comic one
- [ ] ~30 cuts/min (~45 shots per 90s), no shot over ~5.7s, ~55% CU/ECU
- [ ] Gold only on the powerful kind at power moments; the only warm spot in cold scenes is the
      hot food/drink
- [ ] Male lead: fewest lines, one tell per appearance, each denial clumsier, tells escalate to acts
- [ ] Visual signatures appear verbatim from the bible in every episode JSON
- [ ] Every scene has `loc_id` + `variant_id`, every on-screen character an outfit from the asset
      registry; `_assets.py lint` reports 0 errors
- [ ] Scene timecodes sum exactly to `--episode-sec`
- [ ] Story contract: `_story_check.py` reports 0 errors
- [ ] Continuity: every episode 2..N has `because` + `opens_from`; the state ledger covers every
      written episode; `_continuity.py check` reports 0 errors (nobody knows a fact before learning
      it, every planned clue and every plant is on screen, every episode picks up its cliffhanger)
- [ ] Dialogue reads as natural spoken language, xưng hô per `address_matrix`; `_dialogue_lint.py`
      flags fixed or justified; 0 `definition` / `narrates_action`; every 2+ character scene has
      a spoken exchange
- [ ] Every beat has `acting` for each visible character (listener too), every 2+ character scene a
      `blocking`; `_action_lint.py` reports 0 `missing` / `prop_vanish` / `no_blocking`
- [ ] Scenes with a minor follow minors-on-screen.md (daylight / open place, no sleep, bed, touching,
      secret phone at night); `_action_lint.py` reports 0 `minor_risk`

## Data limits

- **The source is one ~1422s story played twice** (0-1421.93, 1424.1-2842.17). The DNA's % (acts,
  timeline, breaks) were on 2842s; this skill recomputes all on 1422s (film_analysis A3, high).
  The DNA insight "face-slap at ~50%" is wrong; it sits at 94-99%.
- **ASR timestamps are ±20s** (A1, high); event times are approximate, subtitle times preferred.
- **Speech share**: DNA speech_pct 32.3% and the "4-5s silence before a verdict" rule are ASR
  artifacts (A2, high). VO is near-continuous (inferred). Words/min 224 is over total runtime.
- **"Cut mid-sentence" cliffhangers were ASR window cuts**, not edit cuts (A4, high): not used.
- **"Who is the boy" is irony, not mystery** (A5, high): the pitch tells the viewer at ~25s.
- Removed from the ledger: "Derik" and the returned key (localization residue / backstory, A7).
- Line "Đồ ngu xuẩn. Ngươi chán sống rồi à." reassigned to the child (A9).
- **The reference ends on a cliffhanger**: no resolution, no confession, the bond never learned by
  the heroine. Rows 91-92% and 98-100% of the Story Template are projected so the season resolves
  (story contract); the finale shape (public reversal with the villain's own line) is measured.
- 13 reference episodes (66-132s) ≈ one season; mapping 1:1 onto 10-20 episodes is a default.
- **Music is inferred** from visuals only. **Speakers not diarized** (no HF_TOKEN); line counts and
  screen time include the repeat (ratios valid, absolute counts ~2x).
- Pacing by act is estimated from per-unit averages; median shot is a pooled estimate.
- Contract tiers: the DNA tags the child as `main`; this skill sets main = heroine + male lead and
  the child as top supporting, to fit the contract's 1-2 main characters (default chosen).
- Ambiguities in this non-interactive run were resolved to documented defaults (12 eps, 90s).

## Changelog

- v1 (2026-10-12T10:15:00Z): generated from `data/analyses/20261012-015632/dna.json` +
  `film_analysis.json` (`phim .mp4`, 2842.17s = 1422s story x2, 24 units). High-severity audit
  items A1-A5 applied over the DNA. Non-interactive run.
- v2 (2026-10-12T10:40:00Z): dialogue = speech, not description (vi-dialogue rules 14-16); VO never
  retells the shot or defines words; glossary only invented terms; VO <= ~50% of lines after the
  pitch; lint `definition` / `narrates_action` must be 0.
- v3 (2026-10-12T15:30:00Z): outline `act` mapped to the contract's 1-3; episode JSON carries
  `logline`, `story_beats`, `cliffhanger_type`, character `outfits` (read by the app); speech rate =
  vi-dialogue.md "Speech rate" (<= 5.0 syllables/s, lint `too_fast`).
- v4 (2026-10-14T00:00:00Z): on-screen action per beat: `acting` [{character, does, face, holds}]
  for every visible character, scene `blocking`, objects kept in hand
  (`action-polish/references/screen-action.md`, lint `_action_lint.py`).
- v5 (2026-10-14T12:00:00Z): minors on screen (`.claude/skills/story-contract/references/minors-on-screen.md`): child scenes staged in daylight / open places, no
  sleep, bed, touching or secret phone at night; read at outline and episode time; lint `minor_risk` strict.
  Learned from Google Flow refusing ep04 ("harmful content involving minors").
- v6 (2026-10-16T00:00:00Z): continuity across episodes (`.claude/skills/story-continuity/`): outline
  cause chain (`events`, `because`, `opens_from`); parallel writers get it plus the state ledger;
  seam pass at package boundaries; state ledger `continuity/state_vN.json` built after Stage 3,
  `_continuity.py check` 0 errors.
