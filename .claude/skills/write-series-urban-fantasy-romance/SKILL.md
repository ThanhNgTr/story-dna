---
name: write-series-urban-fantasy-romance
version: v3
description: |
  Turn a rough or fragmented story idea into a 10-20 episode vertical micro-drama series
  (60-120s episodes) told the way an urban-fantasy dragon-shifter romance melodrama is told:
  a cold-open flash-forward spoiler, a class-wounded first-person narrator whose unconditional
  kindness to an abandoned child of a hidden aristocracy draws the involuntary fated-mate bond
  of that child's terrifyingly powerful guardian, escalating through public humiliation to a
  destructive public claiming. Dense literary voiceover carries the plot, dialogue stays short
  and reactive, cold characters crack through involuntary physical tells, cuts run fast
  (~30/min, ~2s per shot), and colour encodes status (cold grey-blue = poverty and humiliation,
  warm amber = bonding, blinding gold = power). Use whenever the user wants to develop an idea,
  notes, scattered scenes, a logline or a draft into a series, season outline, episode scripts
  or screenplay in this style, even if they only paste fragments. Output: series bible + season
  outline + episode screenplays (md + json).
---

# Write Series: Urban Fantasy Romance

Learned from: `data/analyses/20261002-050718/dna.json` — one source, `phim.mp4`, 2842.2s
(~47.4 min), 24 analysis units. Vertical micro-drama (9:16), DramaBox-style narrated recap.

Reference plot: `references/reference-story.md`. Reference cast: `references/reference-characters.md`.
Read both before Stage 2. Never copy names, places, lines or specific events from them — only the
functions in this file get transplanted.

## Quick Start

```
/write-series-urban-fantasy-romance --idea "..." | --idea-file notes.md [--episodes 12]
    [--episode-sec 90] [--characters "..."] [--sample draft.md] [--continue <session-dir>] [--auto]
```

## Input

| Field | Default | Meaning |
|---|---|---|
| `--idea` / `--idea-file` | required | User's idea: logline, scattered scenes, notes, any language |
| `--episodes` | 12 | 10-20 |
| `--episode-sec` | 90 | 60-120 |
| `--characters` | - | Names + roles; missing roles filled from the Character Bible below |
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

Session dir: `data/series/urban-fantasy-romance/<session-id>/` (session-id = UTC `YYYYMMDD-HHMMSS`).
Save `input.json` first (raw idea text, all flags, resolved defaults, ISO timestamp).

### Stage 1 — Adaptation map (adaptation.md)

1. Extract every element from the idea: premise, characters, places, scenes, lines, endings, themes.
2. Map each onto a Story Template beat and a Character Bible role. Table:
   `user element -> beat/role function -> reference analog`.
3. Empty beats/roles: invent something original inside the user's world, marked `[from template]`.
4. Conflicts: the user's idea wins. Adjust the template and note why.
5. Name the genre swap explicitly. The reference's supernatural layer is **one** possible skin for
   "hidden aristocracy with a visible bodily marker". If the user's idea has no supernatural
   element, translate each world rule to its functional equivalent (see Story Bible) and record
   the substitution here.

### Stage 2 — Bible + outline (bible_v1.md/.json, outline_v1.md/.json)

- **Bible**: title, logline, premise, theme, world rules, locations (with look), cast (tier, role,
  want/need/flaw/secret, visual_signature, voice + 2 sample lines), mystery ledger plan
  (question -> clue episodes -> answer episode), relationship arcs.
- **Outline**: one row per episode — title, logline, beats, which Story Template beat(s) it
  carries (% position), reveal/clue, cliffhanger type, characters.
- **Spread**: map Story Template % positions onto episodes — a beat at p% goes to episode
  `ceil(p/100 * N)`.
- **Looks**: after the bible, run `/series-assets --session <session-dir>` (bible-only) ->
  `assets/assets_v1.md/.json`: fixed face/hair/body per character, default + planned outfits,
  canonical locations with day/night variants, key props. Show it together with the outline; look
  feedback goes to `/series-assets --feedback`.
- **Story contract (outline)**: bible + outline carry the contract fields (`main_plot`, `ending`,
  `relation_to_main`, `arc`, `setting_timeline`, `climaxes`, ledger `tier` + `answer`; outline
  `act`, `main_plot_step`, `locations`, `setting_change`, `climax`). Then
  `python3 .claude/skills/story-contract/_story_check.py <session-dir> --stage outline` -> 0 errors
  before stopping.
- **STOP** and show the outline unless `--auto`. User approves with
  `/refine-skill urban-fantasy-romance --approve outline` or gives feedback.

### Stage 3 — Episodes (episodes/epNN_v1.md/.json)

- Each episode follows the Episode Template and every rule section below.
- Write against the asset registry (latest `assets/assets_vN.json`), following
  `.claude/skills/series-assets/references/episode-contract.md`: every scene has `loc_id`, `variant_id`, `cast` (outfit per on-screen
  character), `referenced`, `props`; anything new goes in `new_assets`. Subagents get the
  registry path and the contract path too.
- N > 6: write in parallel with general-purpose subagents, 3-4 episodes each; give each the bible,
  the outline, this SKILL.md path and its episode numbers.
- Continuity pass after all episodes: names, visual signatures (verbatim), ledger timing,
  callbacks, timecodes adding up to `--episode-sec` per episode.
- Then `python3 .claude/skills/series-assets/_assets.py lint <session-dir>` -> 0 errors, and
  `/series-assets --session <session-dir>` (scene map, `new_assets` get real IDs, drift report).
- Story contract: `python3 .claude/skills/story-contract/_story_check.py <session-dir>` -> 0 errors
  (dialogue in every episode, ledger as planned, last episode carries `ending` and resolves the
  central question on screen).
- Write `series.md` (index + all episodes) and reply with: outline table, open threads, file paths.

## Story Template (season arc)

Positions are % of the season. The reference re-tells its own first act twice (narrated recap);
these beats are the **deduplicated** spine, so each appears once. See
`references/reference-story.md` for why.

| % | Beat function | Why it works | Ref |
|---|---|---|---|
| 0-2 | Cold open spoils the premise as a flash-forward: narrator states the single impossible fact of the season ("I was about to take in a lost boy who was secretly a prince") over an image of the world's apex power | The spoiler is the bait, not the story — it buys 20% of runtime for slow bonding | t=3.81 |
| 0-3 | VO states the world's two-tier rule in one sentence: who rules above, who scrapes by below | One line of worldbuilding does all the class work for the season | t=0.07 |
| 1-4 | Protagonist is publicly humiliated by the person who discarded her; her numbness is named in VO, not shown in tears | Establishes the wound and the antagonist in a single street scene | t=29.07-68.37 |
| 3-6 | Inciting phone call: an ally begs an urgent favor — collect a child from the elite world's gate | Escalations open on a call, never face to face | t=94.23 |
| 7-10 | She arrives at the gate of the elite world and feels hopelessly out of place among its wealth | Pure class contrast, no dialogue needed | t=141-186 |
| 8-12 | She finds the child abandoned in a nearby dark place — visibly marked as not-ordinary (horns, slit eyes) — and he coldly rejects her help, accusing everyone of pricing him | Reveals the supernatural/aristocratic layer visually before anyone explains it | t=213.31 |
| 9-13 | She answers his cruelty with silence and a hot drink instead of argument; he drinks, then lets her hold his hand | The whole found-family engine, bought with one wordless gesture | t=268.74 |
| 13-20 | Home: he bluntly names her poverty, regrets it, doesn't apologize; she cooks him a full meal; a running joke is born around his physical marker | Domestic scene converts the premise into affection; the joke becomes the season's callback | t=269-421 |
| 21-23 | One truly light beat with no plot in it (cartoons, stolen fruit, pretend indifference) | The audience must feel safe right before the knife | t=427-441 |
| 24-28 | A cruel voice message from the antagonist shatters the warmth; she cries quietly; the child defends her fiercely and finally gives his real name | Cruelty by recording is more helpless than cruelty in person; the name is the reward for the defense | t=341.28-419.75 |
| 30-34 | The child secretly contacts his powerful guardian on hidden tech, staging a "rescue" — not to leave, but so the guardian will see her worth | The child, not the heroine, drives the romance; keeps her passive without making her weak | t=471.29, 678.17 |
| 35-40 | Destructive arrival: a streak of light / impossible force detonates in the street outside; then a silhouette in the doorway, assembled in fragments before the face | Spends the season's biggest spectacle beat on an entrance, not a fight | t=583.46-703.79 |
| 41-45 | On sight of her, the guardian's body ignites an involuntary, unfakeable bond signal — which he immediately denies and shuts off on command | The romance is confirmed to the audience and withheld from the characters | t=765.68 |
| 46-52 | Comic facade crack: he refuses her cooking as beneath him, then secretly devours the entire plate when he thinks no one is watching; the child calls out the hypocrisy | Body betrays words — the only way this character type is ever shown to want something | t=890.21 |
| 52-58 | Morning after: the apartment immaculate, him flawlessly composed; small touch-tells (brushed fingers, flushed ear-tips, a tended cut lip); he stays the night "to watch over her" | Slow-burn intimacy made entirely of involuntary reflexes | t=977.73, 2404.55, 2459.94 |
| 59-66 | Bombshell by phone: the ally reveals the child is the heir of an ancient bloodline and the guardian is the apex authority of two worlds, who could crush her without blinking | The single mystery the season closes — and it reframes every earlier scene | t=1103.0, 2514.57 |
| 66-72 | She denies the bond, says they are not from the same world, and formally asks him to take the young lord home; his grip tightens with possessiveness she doesn't see | Her flaw, not an external obstacle, is what blocks the romance at the midpoint | t=2253-2342 |
| 72-78 | Before separating he vows the opposite: "if I say we share a world, then it is so… if anything happens, I'll be there" — then duty calls him away | Plant the promise, then remove the protector, so the climax can need him | t=1932-2250 |
| 79-86 | Second, worse public humiliation: the antagonist mocks her new low status in front of a crowd; the ally slams the table and shuts him down; she finds her own voice for the first time | Repeat the act-1 humiliation with her changed — that contrast is the arc | t=1247.22, 2366-2510 |
| 87-93 | The antagonist turns on the child — a slur, a grabbed jacket, a raised hand — and the child's power erupts visibly: slit eyes, rippling markings, cracking glass | Hurt the child, not the heroine, to earn the destruction | t=2744.26 |
| 94-97 | The environment detonates; the protector walks in through the wreckage and his authority alone forces the antagonist to his knees, without a blow | Power shown as atmosphere, never as choreography | t=2771.47-2784.93 |
| 98-99 | Ignoring the antagonist entirely, he crosses the room, pulls her into an embrace that leaves a glowing mark on her skin, and declares she is the only one who matters | The claiming answers her self-worth wound in an image, not a speech | t=2807.8 |
| 100 | He turns a low, verdict-like voice on the antagonist and the threat is carried out on screen; the central question is answered and the happy/bad ending lands | Story contract: the season resolves; the romance may stay unspoken but its outcome is shown | t=2838.43 |

### Mystery / reveal ledger pattern

- Run **3-5 questions open at once**. Never fewer than 3 after 20%.
- Close the identity bombshell at 59-66% and every other question by the finale (story
  contract; at most 1 minor left open) — the reference ends with 7 of 8 unanswered, which this
  skill no longer copies. *Ref: mystery ledger.*
- Spacing on the closed thread: open at ~4% -> clues at ~11% and ~20% -> answer at ~39-65%.
  Minimum two clues before any answer.
- The **romance question gets clues and never an answer**. The bond signal fires at 41-45%, again
  at 77%, and is marked on her body at 98% — and is still never confirmed in dialogue. That
  withholding is the hook for the next season. *Ref: fated-mate ledger row, answered=open.*
- Reveal rhythm: a reveal or clue every **~55s** of runtime. At 90s/episode that is **1-2 per
  episode** — never an episode with zero. *Ref: `reveal_rhythm_sec: 55`.*
- Never answer in person what can be answered by phone call or voice message. *Ref: 94.23, 341.28,
  1103.0, 2505.74.*

### Subplots

Run exactly five, each with a fixed job:

| Subplot function | Set up | Paid off | Rule |
|---|---|---|---|
| Ally's mistaken-identity favor | 3% | 88% | The error that starts the plot is the same fact as the big reveal |
| The child's secret matchmaking | 17% | 74% | Comic engine; externalizes the romance the adults won't speak |
| The bond | 27% | never | Recurs as an involuntary signal, denied every time |
| Protagonist's self-worth wound | 20% | never | Challenged by the child (72%) and by the claiming (98%); not healed |
| Antagonist's escalating cruelty | 2% | 100% | Three escalations: in person -> recorded -> physical against the child |

## Episode Template (60-120s, default 90s)

Times below are for a 90s episode; scale proportionally for 60-120s.

| Time | Beat | Rule | Ref |
|---|---|---|---|
| 0-3s | Hook. One VO line that either spoils something or lands mid-crisis, over an arresting image (ECU on a glowing eye, a streak in the sky, a hand on a phone). Never a location establisher. | Episode 1 uses the season's flash-forward spoiler; later episodes open on the unresolved image the previous episode cut away from | t=3.81 |
| 3-15s | Re-entry. VO re-states who she is and what she wants in one sentence, as if the viewer just arrived. Episodes 1 / mid-season / finale may reuse opening VO lines near-verbatim — but always add one new fact. | Viewers join mid-series; recap is a feature | t=1447.16-1525.55 reuses 26.7-101.7 |
| 15-45s | Setup/escalation. Two or three short scenes, each ~10-15s. Dialogue short and reactive; VO carries causality between them. | ~32% speech; VO is the connective tissue across fast cuts | `speech_pct: 32.3` |
| 45-75s | Turn. One reveal, clue, or involuntary tell. Physical before verbal: ECU on eyes or hands *before* anyone speaks. | 1-2 reveals per episode at the 55s rhythm | t=765.68, 2194.42, 2744.26 |
| 75-87s | Pressure. The scene escalates one notch — a phone rings, a door opens, a hand rises. | Escalations open on a call or an entrance | t=341.28 |
| 87-90s | Cliffhanger. Cut on one of: mid-sentence/mid-word VO cutoff; cut away right before a reaction; an unexplained supernatural tell. | All 12 reference break candidates are one of these three | episode_break_candidates |

**Density per 90s episode** (from measured pacing):
- ~45 shots, avg 1.99s, median 1.93s, ~30 cuts/min. Never slow the cutting for a slow scene —
  bridge with ECU inserts instead. *Ref: `avg_shot_duration_sec: 1.99`, `cuts_per_min: 30.2`.*
- Shot mix: ~19 CU, ~10 ECU, ~8 MS, ~4 MCU, ~4 WS. *Ref: shot_size_distribution.*
- ~29s of speech total -> **~105-115 words** of spoken text, of which ~70-80% is VO.
  60s episode: ~70-75 words. 120s: ~140-145 words. *Ref: `speech_pct` 32.3 x `words_per_min` 224.5.*
- 2-4 short silences of 0.5-1.4s at emotional or confrontational beats. No dead air beyond that.

**Cliffhanger density**: every episode ends on one. In the final 15% of the season, also end the
*mid-point* of each episode on a withheld reaction — the reference clusters 5 of its 12 strongest
breaks into the last 12% of runtime.

## Story Bible (world-building template)

Reusable world devices. Each is a *function* — swap the dragon skin for whatever the user's idea
needs, but keep the function.

| Device | Function | Reference skin | Ref |
|---|---|---|---|
| Two-tier world stated in one VO line | Makes every later class humiliation land without explanation | Dragons rule the sky, humans scrape by below | t=0.07 |
| Hidden aristocracy living among ordinary people | Lets a palace-level power walk into a one-room apartment | Dragon clans inside a modern city | world.setting |
| An involuntary, unfakeable bodily signal of fate | Confirms the romance to the audience while the characters deny it | Golden aura / eye-glow on meeting a fated mate | t=765.68 |
| A visible birth marker on the child | Shows the premise instead of explaining it | Small horns, tail, vertical slit pupils | t=186.07 |
| Authority that forces a room to kneel and leaves a mark on skin | Resolves threats with atmosphere, never a fight | Dragon lord's wrath, glowing sigils | t=1383.88 |
| Spectacular arrival with destructive impact | Turns an entrance into the season's action beat | Meteor-fall of golden light, thunderous landing | t=583.46 |
| One piece of insider tech the child uses in secret | Lets the child drive the plot without an adult | Communicator watch | t=489.18 |
| A forbidden/cold place the child refuses to return to | Gives the child a want, and the heroine's poverty a dignity | The mansion with its own French chef | world.locations |

**Four locations, no more.** The reference runs on exactly four: the elite world's gate (gothic,
supercars, chauffeurs); the protagonist's worn home (one broken detail repeated — a tape-patched
window); the cold rich house (described, barely seen); one glass-walled public place where she is
humiliated and later rescued. Reuse each 3+ times so returning to it carries memory.

**Motifs to thread** (pick 5-7 and repeat them): cold wind or rain as emotional backdrop; a light
or power overhead as a reminder of hierarchy and fate; worn clothing vs. glamorous clothing; phone
messages as vectors of outside judgment; hot food or drink as care and trust; a body part that
glints or flushes to betray hidden emotion; a body betraying stated intentions; broken glass as
the aftermath of power; one class-contrast prop (a key, a patched window, a coat).
*Ref: world.motifs.*

## Character Bible (role templates)

| Role | Tier | Screen share | Plot function | Introduced | Made recognizable by | Want vs need | Voice pattern | Arc pattern | Ref |
|---|---|---|---|---|---|---|---|---|---|
| The overlooked caretaker / narrator | main | ~49%, ~60% of all lines | Emotional POV; her unrewarded kindness sets every reveal in motion | First-person VO narrating her own humiliation, before anyone else speaks | Worn specific wardrobe (one coat, one home sweater, an apron) + one broken detail in her home | Wants to survive and keep her dignity / needs to believe she deserves to be seen without earning it | Dense literary retrospective VO; spoken lines soft, hesitant, gently teasing, short | Numb -> silent kindness -> stunned witness -> publicly claimed -> wound still open | Linh Khuê, char_01 |
| The precocious child catalyst | main | ~26% | Bridges the two leads; his secret scheming literally causes the romance | Found abandoned, visibly marked, rejecting help with a cold line | The physical marker (horns/eyes/tail) + an ornate crested jacket that doesn't fit his situation | Wants to stay with her / needs to be trusted rather than priced | Sharp and defensive, then sulky affection, proud when speaking of his guardian, feral when enraged | Guarded -> accepts care -> engineers the meeting -> erupts with real power defending her | Cảnh Viêm, char_02 |
| The cold apex power | main | ~25%, **only ~9% of lines** | Antagonist-turned-protector; his power resolves every threat, his denial drives the romance | Destructive arrival first, silhouette second, face third; **name withheld for most of the season** | Height, one impossible feature (glowing slit eyes), one ornate garment; the entrance style itself | Wants to retrieve the child and keep his image / needs to be seen wanting something ordinary | Cold, clipped, formal; drops to a low verdict-like register when enraged; **build him from tells, not speech** | Aloof -> involuntary signal (denied) -> comic cracks -> claims her publicly -> unresolved threat | Cảnh Uy, char_03 |
| The classist discarder | supporting | ~8% | Generates the humiliation beats that force the apex power to intervene; triggers the climax | In person on a cold street, flaunting a new partner | Tailored suit; mostly a voice on a phone and a caller ID | Wants to reassert superiority / **no need — a static antagonist, deliberately** | Curt in person, smug and cutting by recording, silent when overpowered | Smug -> recorded cruelty -> public humiliation -> attacks the child -> forced to kneel, left under threat | Thế Khang, char_04 |
| The ally who delivers reveals | supporting | ~10% | Inciting-incident device and conduit for both identity reveals | Panicked phone call asking an urgent favor | One consistent coat; usually heard, not seen | Wants the favor done, then to warn her / no need shown | Urgent, apologetic, rushed on the phone; sharp and commanding when defending her in public | Favor-asker -> reveal-deliverer -> ally in the public confrontation | Hân Nghi, char_05 |
| The condescending trophy partner | minor | ~4% | Amplifies the antagonist's cruelty with performative politeness | Beside the antagonist in the first street scene | Jewelry, silk, red lipstick against the heroine's worn coat | — | Sweetly condescending; cruelty wrapped in manners | Static | char_06 |
| The deferential attendant (offscreen) | minor | ~1% | Establishes the apex power's title and the duty that pulls him away before the climax | An offscreen voice using his formal title | Never seen | — | Formal, deferential, 1-2 lines total | Static | char_07 |

**Cast size**: 3 main + 2 supporting + 2 minor. Do not exceed 7 named roles in a season.

**Rules**:
1. Introduce the protagonist through VO narrating her own humiliation before any other character
   speaks. *Ref: t=6.59-26.7.*
2. Delay naming a major character for several scenes — the child was seen at 186.07 and named at
   419.75; the male lead was seen at 598.63 and named at **2253.33** (79% of the way in). Carry
   identification on the visual signature and relationships. *Ref: character_building.*
3. Reveal a cold character's hidden warmth through an involuntary physical tell, never dialogue:
   flushed ear-tips, secretly finishing the food he refused, a grip tightening on a cup.
   *Ref: 977.73, 890.21, 2404.55, 2314.15.*
4. The child is both comic relief and the only character who says the emotional truth out loud.
   Give him the season's thesis line. *Ref: t=2071.32.*
5. Visual signatures are repeated **verbatim** at every appearance. Write them once in the bible
   and copy the exact wording into every episode's `characters` block.

## Storytelling Rules

- **Devices**: cold-open flash-forward spoiler; dense first-person literary VO; a narrated
  mid-story recap that re-establishes the premise; phone calls and voice messages as the delivery
  vector for reveals and inciting incidents; burned-in captions mirroring the VO.
  *Ref: storytelling.devices.*
- **Exposition**: almost entirely first-person retrospective VO, punctuated by short naturalistic
  dialogue and phone-call reveals. If a fact can be narrated, narrate it; do not stage a scene to
  explain something. *Ref: exposition_method.*
- **POV**: first-person retrospective from the protagonist, with occasional omniscient-feeling
  narration of other characters' inner states — she may narrate what *he* secretly felt. Use that
  licence; it is how the male lead gets interiority with 41 lines. *Ref: storytelling.pov.*
- **Narration**: a single narrator voice reads both narration and quoted character lines.
- **Rule — recap verbatim, plus one new fact**: when re-entering the origin thread (mid-season,
  and at the top of the finale), reuse the opening VO lines near word-for-word, but never just
  replay the beat — always add information that recontextualizes it. *Ref: 1447.16-1525.55 repeats
  26.7-101.7.*
- **Rule — escalate by phone**: open each dramatic escalation with a call or voice message rather
  than an in-person confrontation. *Ref: 94.23, 341.28, 1088.0, 2505.74.*
- **Rule — show the tell before the explanation**: a supernatural or emotional truth appears as a
  physical event first; the VO explains it one beat later, or in the next episode.
  *Ref: cliffhanger_patterns.*
- **Cliffhanger patterns**, in order of frequency: mid-sentence/mid-word VO cutoff; cut away right
  before a reaction or reveal; a scene ending on an unexplained physical tell (glow, eruption).

## Pacing Guidelines

| Measure | Value |
|---|---|
| Avg shot | 1.99s |
| Median shot | 1.93s |
| Cuts/min | 30.2 (`fast`) |
| Range across 24 units | 23.2 - 39.0 cuts/min |
| Shots per 60s / 90s / 120s episode | ~30 / ~45 / ~60 |
| By act | Act 1 1.96s, Act 2 1.95s, Act 3 2.06s per shot |

- The cut rate **does not change with register**. Contemplative VO passages cut as fast as
  confrontations; ECU inserts (eyes, hands, phones) are the connective tissue.
  *Ref: cut_rhythm_notes.*
- Only the quietest emotional-dialogue episodes may dip toward 23 cuts/min (~2.6s/shot). Never
  below that.
- The climax act cuts very slightly *slower* (2.06s) — let the destruction and the claiming hold.

## Tone & Voice Guidelines

- **Tone**: melancholic urban-fantasy romance easing into tender found-family warmth, class-conflict
  melodrama and supernatural wonder, with recurring comedic beats. *Ref: tone.overall.*
- **Energy**: quiet and introspective in domestic VO beats, spiking sharply at each supernatural or
  confrontational reveal — while the cutting stays fast throughout. *Ref: tone.energy.*
- **Emotions to hit across the season**: longing, humiliation, numbness, guarded trust, tenderness,
  awe, embarrassment, shame, protective rage. *Ref: tone.emotions.*
- **Word budget**: speech is 32.3% of runtime at ~224.5 wpm -> **~105-115 words per 90s episode**
  (~70-75 at 60s, ~140-145 at 120s). VO is 70-80% of that. *Ref: sound.speech_pct, words_per_min.*
- **Line length**: spoken dialogue in 1-2 short clauses. VO sentences may be long and literary —
  that asymmetry is the style.
- **Register split**: the protagonist's VO is literary; the child is blunt and colloquial; the
  apex power is formal and clipped; the antagonist is cutting and status-obsessed.
- Reference lines, as style examples only (never reuse):
  - VO, premise: *"Ngay từ đầu tôi đã biết thằng bé không thuộc về mình."*
  - VO, class gulf: *"Khoảng cách giữa chúng tôi không chỉ là tiền bạc, còn là khoảng cách giữa mặt đất dưới chân tôi và bầu trời trên những tầng mây."*
  - VO, world rule: *"Đây không phải hơi thở rồng bình thường. Đó là tín hiệu khế ước cổ xưa... Hoàn toàn trong vô thức, không thể giả mạo."*
  - Apex power, vow: *"Ở thành phố này, nếu tôi nói chúng ta cùng một thế giới thì chính là như vậy."*
  - Child, thesis: *"Sao cô cứ luôn hành động như thể mình không đáng để người khác nhìn thấy vậy?"*
  - Final cutoff: *"Dám công khai cô ấy sao?"*

**Language**: write the screenplay in the language of the user's idea unless told otherwise.

## Visual Guidance

### Camera

| When | How | Ref |
|---|---|---|
| Dialogue | Eye-level shot/reverse-shot, static or handheld-feel close coverage | camera.angles |
| Hidden power or emotion surfacing | Cut to an ECU on the eyes or hands **before** anything is said | t=765.68, 2194.42, 2744.26 |
| A dominant character entering | Low-angle, backlit or silhouetted, assembled in fragments (boots, coat, then face) | t=703.79, 2784.93 |
| Emotional beat | Slow push-in | camera.movement |
| The apex power's arrival | Slow, deliberate tracking/dolly | camera.movement |
| Worldbuilding or recap | Static wide b-roll | camera.movement |
| Supernatural reveal / dominance | Low angle | camera.angles |

**Signature shots** to place at least once each per season: a wide of the apex power's form above
a foggy skyline; ECU on glowing slit eyes (recurring in nearly every unit — use it as the series'
visual signature); ECU on hands (phone, tissue, cup, hidden tech, the mark); the fragmented slow
reveal of a powerful arrival; a silhouette/backlit reveal in a doorway; a wide of destruction or
impact. *Ref: camera.signature_shots.*

### Color and lighting

| Where / mood | Look | Ref |
|---|---|---|
| Present-day exteriors: street, elite gate, public humiliation | Cold desaturated grey-blue daylight, flat overcast, class-contrast wardrobe | color_lighting.looks |
| Her home, domestic bonding | Warm amber lamp and kitchen light, cozy low-key browns | color_lighting.looks |
| Supernatural beats: arrival, bond signal, rescue | Blinding gold/orange against cool blue-grey, high contrast, low-key backlight | color_lighting.looks |

**Rule**: reserve blinding gold/orange high-contrast light **exclusively** for power beats —
arrivals, the bond signal, sigils, rage. Never for an ordinary emotional scene. *Ref: 583.46,
2007.06, 765.68, 2194.42, 2807.8.*

## Sound Guidance

- **Speech**: 32.3% of runtime, ~224.5 wpm, voiceover-led. Dialogue is short and reactive; VO is
  the connective tissue across fast cuts. *Ref: sound.rules.*
- **Music (inferred from visuals only — not measured)**: soft romantic/ambient under quiet domestic
  scenes; swelling orchestral stings on supernatural reveals and entrances; moody piano/strings
  under confrontation and VO-heavy passages. *Ref: music_style_guess, marked inferred.*
- **Silence**: short 0.5-1.4s pauses at emotional beats and immediately before or after
  confrontational lines. No extended dead air. *Ref: silence_usage.*
- **SFX palette**: wind gusts; car engine roar; phone ringtone/vibration; footsteps on wet
  pavement; a simmering pot and cutlery on a plate; thunder/impact boom; doorbell chime; door lock
  click; a hand slamming a table; glass shattering; chairs scraping. *Ref: sound.sfx.*
- **Rule**: deliver the antagonist's cruelest lines through a recorded voice message, not in
  person — it maximizes the protagonist's helplessness. *Ref: 341.28-362.42, 1766.32-1790.99.*

## Hook Patterns

- **0-3s**: a VO line that spoils or lands mid-crisis, over an arresting image. Three reliable
  forms: (a) the impossible fact stated flatly ("dragons rule the sky; I was about to feed one
  dinner"); (b) the unresolved image the last episode cut away from; (c) a quoted cruelty with no
  context yet. Never open on a location establisher. *Ref: t=3.81.*
- **Mid-episode**: an involuntary physical tell shown with no explanation; or a phone starting to
  ring while the current scene is still unresolved. *Ref: camera.rules, storytelling.rules.*
- **Ending**: one of the three cliffhanger patterns — mid-word VO cutoff, reaction withheld, or an
  unexplained supernatural tell.
- **Season premiere**: the flash-forward spoiler of the whole premise. Give away the ending of the
  season's A-question in the first 10 seconds; it is bait, not a leak. *Ref: insight 1.*
- **Season finale (story contract)**: the apex power turns a low verdict-like voice on the
  antagonist and the verdict is carried out; the central question is answered and the happy/bad
  ending lands; the romance is marked on the body but never
  spoken. *Ref: t=2838.43.*

## Output Format

`episodes/epNN_vK.md`:

```markdown
# EP03 — <Title> (90s)
Logline: ... | Story beats: <template beats + %> | Cliffhanger: <type>

### SC1 [00:00-00:12] EXT. <PLACE> — NIGHT  {loc_01 · char_01:o1}
| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.8 | ECU | char_01 ... | VO: "..." | handheld | cold grey-blue | wind, phone buzz |
```

`episodes/epNN_vK.json` (read by `/script-to-shotlist`):

```json
{
  "skill": "write-series-urban-fantasy-romance", "skill_version": "v1", "session": "<session-id>",
  "episode": 3, "title": "...", "total_duration_sec": 90, "aspect_ratio": "9:16",
  "characters": {"char_01": {"name": "...", "visual_signature": "..."}},
  "scenes": [{"id": "SC1", "start_sec": 0, "end_sec": 12, "location": "<registry name>", "loc_id": "loc_01", "variant_id": "loc_01_night",
    "cast": {"char_01": "char_01_o1"}, "referenced": [], "props": ["prop_01"], "int_ext": "EXT", "time_of_day": "night",
    "beats": [{"start_sec": 0, "end_sec": 1.8, "shot_size": "ECU", "characters": ["char_01"], "action": "...",
      "dialogue": [{"character": "char_01", "line": "...", "voiceover": true, "delivery": "whisper"}],
      "camera": "...", "lighting_color": "...", "sound": "..."}]}],
  "new_assets": [], "cliffhanger": "...", "ledger": {"opened": [], "clues": [], "answered": []}
}
```

`bible_vK.json`: `{title, logline, premise, theme, world: {setting, rules[], locations[{name, look}],
motifs[]}, cast[{character_id, name, tier, role, want, need, flaw, secret, visual_signature,
voice: {style, sample_lines[]}}], ledger_plan[{id, question, tier, open_ep, clue_eps[], answer_ep, answer}],
relationship_arcs[{a, b, arc}]}` + story contract fields (main_plot, ending, setting_timeline, climaxes,
cast relation_to_main/arc/secret_reveal_ep)

`outline_vK.json`: `{episodes: [{episode, title, logline, duration_sec, beats[], template_beats[{pct,
function}], reveal, cliffhanger_type, characters[], act, main_plot_step, locations[], setting_change,
climax, ledger}], never_answered[]}`; last episode `ending` + `cliffhanger_type: "resolution"`

## Self-check

Before reporting Stage 3 complete:

- [ ] Every Story Template beat is assigned to an episode, and its episode number equals
      `ceil(pct/100 * N)` (±1 episode)
- [ ] 3-5 mystery questions open at once after 20%; the identity bombshell at 59-66%; every question but <=1 minor answered by the finale
- [ ] The romance/bond question has clues but **no** dialogue confirmation
- [ ] Every episode contains 1-2 reveals or clues (~55s rhythm); none has zero
- [ ] Every episode except the finale ends on one of the three cliffhanger patterns
- [ ] Episode 1 opens with a flash-forward spoiler in the first 10s; the finale resolves the threat on screen
- [ ] Scene timecodes in each episode sum to `--episode-sec` exactly
- [ ] Shot count ≈ 0.5 x duration_sec (~45 per 90s); avg shot ~2.0s; shot mix ≈ 43% CU, 22% ECU,
      17% MS, 9% MCU, 9% WS
- [ ] Spoken words per episode within ±15% of `0.323 x duration_sec x 224.5 / 60`; VO is 70-80%
- [ ] Visual signatures copied **verbatim** from the bible in every episode
- [ ] Every scene has `loc_id` + `variant_id`, every on-screen character an outfit from the asset
      registry; `_assets.py lint` reports 0 errors
- [ ] Blinding gold/orange light appears only on power beats
- [ ] At most 7 named characters; at most 4 locations, each reused 3+ times
- [ ] Every major reveal arrives by phone call or voice message, not face-to-face exposition
- [ ] The cold lead's warmth is shown only through involuntary tells, never a confession
- [ ] Story contract: `_story_check.py` reports 0 errors (complete plot, happy/bad ending shown,
      main + supporting cast, dialogue, setting timeline, climaxes, every mystery answered but <=1)

## Data limits

- **One source only**: `phim.mp4`, 2842.2s (~47.4 min), 24 units. Single genre sample, single
  creative team — rules are patterns from one work, not a validated genre model.
- **Runtime is inflated by a recap device**: the reference re-tells its first act twice (mid-story
  narrated recap at 50-68%, and again in act 3), producing duplicate beats (two arrivals, two bond
  ignitions, two humiliations). The Story Template is built on the **deduplicated** spine, so
  template % positions are *not* the reference's raw timestamps. The `Ref:` timestamps point at the
  first occurrence.
- **Music is inferred from visuals only** — no audio-feature analysis was run. Treat all music
  guidance as a guess.
- **Speakers were not diarized** (no HF token). Speaker attribution came from frames; some lines
  may be misattributed.
- **One garbled transcription** at t=2221.26 ("Anh, anh giết cô ấy.") read contextually as
  "Anh thích cô ấy".
- **One continuity inconsistency in the source**: the ally appears as the antagonist's companion in
  one unit before reverting to ally. Not treated as a pattern to copy.
- **No on-screen title**; the reference is identified by its characters.
- **Defaults chosen, not derived from a user**: `--episodes 12`, `--episode-sec 90`. The reference
  was never cut into episodes — its 12 break candidates average ~237s apart, i.e. closer to
  ~2-min units than to 90s episodes. 90s is the project-wide default, scaled by the Episode
  Template's density figures.
- **No measured music, score, or music-cue timing. No shot-level colour measurement** — palette is
  from analyst description.
- TODO (not in DNA): season-length pacing beyond 47 min; how the story resolves (the reference
  ends mid-threat), so the 100% beat is a cliffhanger by necessity, not by choice.

## Changelog

- v1 (2026-10-02T00:00:00Z): generated from `data/analyses/20261002-050718/dna.json`
- v2 (2026-10-08T12:30:00Z): episodes are written against the asset registry (/series-assets):
  bible-only registry at Stage 2, scene IDs + outfits per Stage 3 episode-contract, lint in the
  continuity pass. No story/style rule changed.
- v3 (2026-10-08T09:41:01Z): story contract (story-contract skill): complete plot to a happy/bad ending shown in the last episode, main_plot / ending / setting_timeline / climaxes / ledger answers in bible + outline, _story_check.py at Stage 2 and 3. Finale and unanswered-question rules now apply to episodes 1..N-1 only (drift from the reference's open ending, requested by the user).
