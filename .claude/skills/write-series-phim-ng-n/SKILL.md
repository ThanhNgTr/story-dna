---
name: write-series-phim-ng-n
version: v1
stable_version: v1
description: |
  Turn a rough or fragmented story idea into a 10-20 episode vertical series (60-120s episodes)
  told the way a Chinese "tổng tài" revenge short drama (CEO romance + face-slap + heir-in-hiding
  family war) is told: a heroine who is never the victim (she caused the crisis the enemy blames
  her for), enemies' traps turned back on them, public face-slaps with documents and exact odd
  numbers in front of witnesses, a three-tier villain ladder ending with an impostor posing as
  family, and a quiet powerful male lead whose old love is revealed layer by layer. Signature
  craft: cold open mid-conflict, every episode ends on a cut-off line or stunned face,
  CU shot/reverse cut on every line (~2.2s shots, 51% CU), static camera, papers as weapons.
  Use whenever the user wants to develop an idea, notes, scattered scenes or a draft into a
  series, season outline, episode scripts or screenplay in this style, even if they only paste
  fragments. Output: series bible + season outline + episode screenplays (md + json).
---

# Write Series: Phim Ngắn (CEO revenge drama)

Learned from: `data/analyses/20261019-025904/dna.json` + `film_analysis.json` — one vertical video
"Cô gái bị mẹ chồng sỉ nhục giữa công ty, liền ký đơn ly hôn quay xe làm vợ CEO khiến họ câm nín.mp4",
9663.6s (~161 min, ~98 mini-episodes), 81 units. Reference plot: `references/reference-story.md`.
Cast: `references/reference-characters.md`. Audit + retention study: `references/film-analysis.md`.
Read Data limits before trusting numbers. `Ref: <n>` = seconds in the source.

## Quick Start

```
/write-series-phim-ng-n --idea "..." | --idea-file notes.md [--episodes 12] [--episode-sec 90]
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

Session dir: `data/series/phim-ng-n/<session-id>/` (session-id = UTC `YYYYMMDD-HHMMSS`).
Save `input.json` first: the raw idea, every flag value, and this skill's version.

### Stage 1 — Adaptation map (adaptation.md)

1. Extract every element from the idea: premise, characters, places, scenes, lines, endings, themes.
2. Map each onto a Story Template beat and a Character Bible role.
   Table columns: `user element | beat/role function | reference analog`.
3. Empty beats/roles: invent something original for the user's world, marked `[from template]`.
4. Conflicts: the user's idea wins. Adjust the template and note why in one line.
5. Compression: the reference is ~98 mini-episodes; a season here is 10-20. Pick beats, do not
   copy every event. Keep the cast to 2 main + 4-7 supporting + extras (reference has 16 named).
6. Name the fixtures this style cannot run without (from the user's world; invent if missing):
   - **the transactional bond** the heroine wants out of (marriage / contract / debt of gratitude) and
     the exact sum or favor that "paid it off" (Ref 27.4 "Ơn tình nợ nần sớm đã trả hết rồi");
   - **her hidden standing** (lineage, money, ownership) that enemies do not know (Ref 1625);
   - **leverage objects**: 3-5 papers/things that win or lose fights (divorce paper, ledger,
     test result, will, heirloom) (Ref 1536, 3536, 5387, 6864);
   - **the villain ladder**: outsider -> inside the family -> impostor posing as kin; tier 3 is on
     screen or named in the first 5% as harmless (Ref 317.5);
   - **the lead's backstory in 4-6 pieces**, the last = what SHE once did for HIM (Ref 9480);
   - **the trap list**: each enemy trap + how it turns back + what she gains from it;
   - **money scale + family tree** (one currency table, one tree; reference weakness);
   - **5-8 signature lines** of the couple for callbacks in the second half.

### Stage 2 — Bible + outline (bible_v1.md/.json, outline_v1.md/.json)

- **Bible:** title, logline, premise, theme, world rules (4-6: what money/papers/media can do, the
  families' house rules, the heirloom that marks the head), locations with look, cast (tier, role,
  want/need/flaw/secret, tell, visual_signature, voice + 2 sample lines), ledger plan (question ->
  clue episodes -> answer episode, with `audience_knows_ep` and `heroine_knows_ep`), villain
  ladder, trap list, leverage objects, lead backstory pieces with episodes, money scale, family
  tree, signature lines, relationship ladder, motifs (3-5).
- **Outline:** one row per episode — title, logline, beats, which Story Template beat(s) it
  carries (% position), reveal/clue, cliffhanger type (Hook Patterns), characters.
- **Spread:** beat at p% -> episode `ceil(p/100 * N)`; no episode carries more than 3 beats.
- **Minors on screen (before planning)**: read `.claude/skills/story-contract/references/minors-on-screen.md`.
  Child characters (incl. a flashback of the heroine as a child) get daylight / early-evening scenes
  in open or shared places; no sleep, bed or touching with an adult, no phone / screen in the child's
  shot, at most one adult in it; the child's tell and props are hand / school things, never a mouth
  habit or a device; every outline row with a minor on screen names when and where.
- **Looks**: after the bible, run `/series-assets --session <session-dir>` (bible-only) ->
  `assets/assets_v1.md/.json` (fixed faces, default + planned outfits incl. her "battle" look,
  canonical locations with variants, key props: the leverage papers, the heirloom, cars). Show it
  with the outline.
- **Dialogue setup**: bible also has `address_matrix` (xưng hô per pair; the family tree decides it)
  + `glossary` (ONLY invented/unusual terms and how a character or sign makes them clear; never
  everyday words) per `.claude/skills/dialogue-polish/references/vi-dialogue.md`.
- **Cause chain**: every outline row has `events` (1-4, ids `E<ep>.<k>`: what happens), `because`
  (episodes 2..N: earlier event ids that make it happen; chance is not a cause) and `opens_from`
  (how it picks up the previous cliffhanger), per `.claude/skills/story-continuity/references/continuity.md`.
  Every trap has the event that set it; every rescue has the event that brought the rescuer there.
  `python3 .claude/skills/story-continuity/_continuity.py check <session-dir> --stage outline` -> 0 errors.
- **Story contract**: bible + outline carry the fields of
  `.claude/skills/story-contract/references/story-contract.md` (main_plot, ending, setting_timeline,
  climaxes, ledger tier + answer; outline act, main_plot_step, locations, setting_change, climax);
  `python3 .claude/skills/story-contract/_story_check.py <session-dir> --stage outline` -> 0 errors.
- STOP and show the outline unless `--auto`. User approves with
  `/refine-skill phim-ng-n --approve outline` or gives feedback.

### Stage 3 — Episodes (episodes/epNN_v1.md/.json)

- Each episode follows the Episode Template and the rule sections below.
- Write against the asset registry (latest `assets/assets_vN.json`) per `.claude/skills/series-assets/references/episode-contract.md`:
  every scene has `loc_id`, `variant_id`, `cast` (outfit per on-screen character), `referenced`,
  `props`; new things go in `new_assets`. Subagents get the registry and contract paths too.
- N > 6: write in parallel with general-purpose subagents, 3-4 consecutive episodes each; give each
  the bible, outline (its `events` / `because` / `opens_from` are the contract between writers), this
  SKILL.md path, `.claude/skills/story-continuity/references/continuity.md` and its episode numbers.
  Episodes written while others exist read the latest `continuity/state_vN.md` first.
- Seam pass: `python3 .claude/skills/story-continuity/_continuity.py seams <session-dir>`; at every package
  boundary (or pair that does not join) the later episode's first 3s continue the exact cliffhanger.
- Continuity pass after all episodes: names, visual signatures (verbatim), ledger timing (audience
  vs heroine), callbacks, money figures against the bible scale, timecodes adding up. Then build the
  state ledger (`/story-continuity` "Check + repair" step 3: `continuity/state_vN.json`) and
  `python3 .claude/skills/story-continuity/_continuity.py check <session-dir>` -> 0 errors (story
  breaks fixed in the episodes, not in the ledger).
- Then `python3 .claude/skills/series-assets/_assets.py lint <session-dir>` -> 0 errors, and
  `/series-assets --session <session-dir>` (scene map, `new_assets` get real IDs, drift report).
- Minors on screen: re-read `.claude/skills/story-contract/references/minors-on-screen.md` before
  writing an episode with a child; `_action_lint.py` `minor_risk` = 0 (strict).
- Acting: every beat carries `acting` (per visible character, listener included: `does` = body +
  hands, `face`, `holds`) and every 2+ character scene a `blocking`, per
  `.claude/skills/action-polish/references/screen-action.md` (lines said while doing something: lật
  hồ sơ, đặt bút ký, tháo kính râm; papers and cups stay in hand until a beat puts them down).
  `python3 .claude/skills/action-polish/_action_lint.py lint <session-dir>`: `missing` / `prop_vanish` / `no_blocking` = 0.
- `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session-dir>`; rewrite flagged lines.
  `definition` / `narrates_action` = 0 (cut, show, or turn into speech between the characters on screen).
- `python3 .claude/skills/story-contract/_story_check.py <session-dir>` -> 0 errors.
- Write `series.md` (index + all episodes) and reply with: outline table, open threads, file paths.

## Story Template (season arc)

% of the season (reference: % of 9663.6s). Reference events in `references/reference-story.md`.

| % | Beat function | Why it works | Ref |
|---|---|---|---|
| 0-1 | Cold open mid-crisis: an enemy demands the heroine clean up a scandal; she calmly says she arranged it. Within the episode: role-reversal line ("it's me who's leaving") + she cuts their money. One line plants her origin wound | "Victim is the author": the viewer is let in on her plan one beat late; pleasure of the late reveal | 2.8 "đám phóng viên đó là do tôi sắp xếp"; 33.8 khóa thẻ; 61.8 "Là tôi muốn đá con trai bà"; 31.4 mother insult |
| 1-3 | The powerful man appears as an ally WITH a condition, and is the stranger from a shared secret; the condition binds her plan (finish the divorce fast) | Lead enters by shared secret + mutual need, not a meet-cute; first debt between them | 119.6 "Là anh?"; 203.6 condition |
| 3-4 | Plant: someone reports her "true" lineage, naming the future impostor as her kin (false info the viewer believes) | Long-range twist planted as a harmless fact | 317.5 (A11) |
| 4-6 | Enemy trap #1 (set on screen) turns back the same night, with a side gain for her (signature, evidence); she wins alone, the lead walks in after | Trap boomerang; she does not need saving | 289 set; 378-473 (A3); 425 |
| 6-9 | Public choice: the lead picks her over the rival in front of a crowd; in private they trade "plan for plan" | Romance step + alliance, both earned | 629; 770 |
| 9-10 | The enemy's own trap material exposes them at their event; she announces the break publicly | Payoff of 4-6% inside 5%; public | 913; 944 |
| 11-13 | He proposes as "responsibility"; she refuses: one deal is just traded for another (theme said once) | States the theme; keeps romance a negotiation | 1038; 1164 |
| 13-15 | Deal over a concrete asset, then a REAL loss: smear media, his family cuts ties ("quả nhiên cũng chẳng đáng tin") | She must lose for wins to count | 1283; 1398 |
| 16 | ACT-1 CLIMAX: face-slap ledger before the press: exact odd sum read aloud; the torn paper "was a photocopy" | Documents + witnesses + exact number | 1536-1567 |
| 17-20 | Identity reveal: a powerful family arrives to claim "the heir"; the lead is shocked; a third person says he has loved her for years. New enemy tier enters as the old one falls | Stakes jump from in-laws to a dynasty; lead's 2nd layer | 1625; 1655 (A8); 1923 |
| 21-27 | Tier-2 enemies inside the family + the "mother" sides with the rival; an ally reverses a public humiliation; ally kidnapped, she goes alone, the lead (planted on the way) rescues | Danger raises stakes; ladder climbs | 2028; 2111; 2486-2561 |
| 30-31 | Audience-only scene: the "mother" is the puppeteer (heroine does not know yet). The patriarch offers everything with moral strings; she refuses; he collapses | Dramatic irony; refusal shows she cannot be bought | 2918 (A4); 3009 |
| 36-39 | Public charity face-slap -> patriarch dies, will names her -> ultimatum with deadline + hostage -> "Tôi thương em" -> allies confirm the puppeteer | Close one question, open a bigger one; romance right after danger | 3460; 3536; 3571; 3661; 3763 |
| 42-46 | She takes the inheritance on her terms; a room trap meant for her is reversed (the plotter's pawn lies in it) | Trap boomerang #2, different type | 4079-4151; 4385 |
| 48-56 | MIDPOINT CLIMAX: "the family takes MY name" -> she overturns the tier-2 enemy at the shareholders' meeting by the patriarch's own rule -> on stage: "I am the head. I decide." | Power position taken before witnesses | 4675; 4744; 5387 |
| 57-60 | She overhears the "mother" wanted her dead — she already suspected; the lead buys the heirloom for her and gives back her own line | She is never the last to know; callback | 5518, 5606 (A5); 5782 |
| 64-69 | She admits she has fallen for him; the fallen pawn (rival) stands at the edge; she saves her and spares her | Kindness breaks the face-slap chain; mercy now, payback later | 6233; 6588-6672 |
| 71-74 | The shock she did NOT foresee: test proves the "mother" is not her mother; the impostor's real name via her own son; then "where is my real mother?". Couple confirmed | Close a question, open a bigger one; her one real wound | 6864; 6952; 7114 |
| 75-86 | Impostor expelled; she baits the lead's rival with land; the lead fakes a downfall; the land-price trap springs (the old patriarch realizes SHE set it); the lead is exiled; she rescues him publicly ("he is mine") with his old line reversed | Victim-is-author at scale; role-reversed rescue | 7259; 7343; 7835; 8091 (A18); 8319; 8366 |
| 88-90 | The spared pawn pays back with evidence; she accuses the impostor | Mercy paid; fair-play clue chain | 8508; 8563 |
| 92-95 | FINAL CLIMAX: the impostor confesses in ONE line (motive was clued earlier) and tries to take everyone down (fire/threat at the old place of the crime); the lead and the son shield her; the impostor falls | Stakes up to life at ~94% | 8859; 8957; 9054-9161 |
| 95-98 | Aftermath in one scene: who fell; grave/memorial of what was lost; the last piece of the lead's love: she once saved him | Grief + root of love; ladder fully paid | 9193.8 (A2); 9363; 9480 |
| 99-100 | Ending: she refuses the dynasty and founds her own company with him ("we'll be competitors"), then "Em đồng ý"; the old enemy walks away. One romantic wink may stay open | Freedom + love; contract `happy` ending | 9567-9596; 9612; 9507 |

Acts: 1 = 0-20%, 2 = 20-40%, 3 = 40-70%, 4 = 70-89%, 5 = 89-100%.
Outline `act` field (story contract, 1-3 only): style act 1 -> 1, acts 2-3 -> 2, acts 4-5 -> 3.
Climaxes: act-1 16%, midpoint 48-56%, final 92-95%; a public reversal every ~10-15% between them
(22, 36, 60, 86%). Bad ending (if the idea asks): same shape, the final climax costs her what she chose.

### Mystery / reveal ledger pattern

- 12 big questions opened, 11 answered, 1 left open as a wink (9507); 3-4 open at once, peak 4 in
  act 2, 1 at the finale. Max 4 open in any episode.
- Two clocks per question: `audience_knows` (enemy-side scene) leads `heroine_knows` by ~10-15% of
  the season (puppeteer 2918 vs 3763; son 5580 vs 6924; A4, A6).
- Withholding: median ~12% of the season, max ~50% ("mother": false plant 3% -> answer 71% -> full
  truth 93%). Small questions answered within 1-3 episodes. Close a big one -> open a bigger one in
  the same episode (3684 -> 3763; 6864 -> 6869 "where is my mother?").
- Answer channels: test/document, a witness's confession, an overheard enemy talk, a flashback.

### Subplots

| Function | Setup % | Payoff % | Ref |
|---|---|---|---|
| Romance spine: transaction -> alliance -> proposal refused -> "I love you" -> kiss -> confirmed -> wedding | 1 | 99 | 119.6 -> 9596 |
| Hidden lineage / inheritance (raises stakes from in-laws to a dynasty; ends with her refusing it) | 3 | 99 | 317.5 -> 9567 |
| Impostor posing as kin (mother -> puppeteer -> not mother -> real identity) | 3 (false plant) / 21 | 71 / 93 | 317.5, 2028 -> 6864, 8957 |
| Hostage ally (forces a concession; lets the lead save her once) | 18 | 38 | 1739 -> 3684 |
| Mirror rival: enemy -> discarded pawn -> spared -> pays back with evidence | 3 | 68 / 88 | 284 -> 6588, 8563 |
| Young suitor = the impostor's son (shows she chooses; bridge to the final villain) | 22 | 72 / 98 | 2111 -> 6924, 9451 |
| Lead's family war (cousin rival, patriarch, forced fiancée; fake downfall) | 15 | 86-99 | 1429 -> 8366, 9538 |

## Episode Template (60-120s)

Reference mini-episodes 56.5-126s, mean 98.6s; hook every ~48s, strong hook every ~124s (A10).
Seconds below for 90s (film_analysis episode_template); scale by %.

| Time | Beat | Rule | Ref |
|---|---|---|---|
| 0-8s (0-9%) | Hook | Continue the exact cut-off moment; answer the cliffhanger's half-line within the first 20s (premiere: cold open mid-conflict) | 119.59 answers "Là anh?"; 5047; 6864 |
| 8-25s (9-28%) | Setup | ONE new piece of info by assistant report, phone, headline or gossip, with a prop or text for the eye | 2746 "Sếp, không hay rồi"; 6030 headline |
| 25-50s (28-56%) | Turn | The opponent presses: insult, demand, house rule or deadline; she seems cornered | 3571 "Trước 8 giờ sáng mai"; 5076 |
| 50-75s (56-83%) | Reveal | Her prepared move, a document, an ally entering, or a truth said aloud | 1536; 2111; 3460; 5391 |
| 75-90s (83-100%) | Cliffhanger | Cut mid-sentence before the decisive name/noun, a newcomer steps in, a deadline, or a held CU of the stunned face. Never end on a closed scene | 4780.9 "Là cung..."; 1923; 5787 |

- 60s: setup 8s, keep turn + reveal. 120s: add a comic/sweet pocket (<=20s) before the reveal (4452).
- Every episode moves a ledger question or a rung of the relationship ladder; danger is followed by
  romance (3661 after 3571; 7091 after 6952); recap <= 15-20s with a new decision (6141 sags).

## Story Bible (world-building template)

| Device | Pattern | Ref |
|---|---|---|
| Money is power | Cards, allowances, investment; locking a card is a punishment; investors pull out together | 33.8; 87 |
| Media is a weapon for both sides | Reporters, leaked photos, hot search, press conferences | 2.8; 1398; 1536 |
| Families as institutions | 3-4 great families; each has a patriarch who decides projects and marriages; house rules ("marry first to enter", embezzlers lose shares) | 4744; 5076 |
| Heirloom = right to rule | One object only the head may wear; whoever wears it claims the house | 5331; 5387 |
| Marriage as transaction | Engagements, alliances, contract marriages; the heroine's arc is out of transactional love | 1139; 1164 |
| Papers decide | Divorce paper, ledger of what was paid, DNA test, will, contract clauses; original vs photocopy | 1536-1567; 3536; 6864 |
| Gratitude as a leash | Elders bind her with old favors ("ông vẫn luôn coi cháu như con gái ruột") | 835; 3006 |
| Locations | her office (white desk, orange leather chair, glass walls); hotel suite (amber, rattan sofa); in-laws' villa (carved wood, cream-brown); his family house (mauve curtains, red wood, golden deer statue); dynasty HQ (bowing guards, stone floor); hospital VIP room; banquet/auction hall (bronze-gold, white-pink flowers); abandoned factory / rooftop at night | world.locations |
| Motifs | papers as weapons; photocopy vs original; sunglasses on before battle; heirloom necklace; the white SUV / her sports car; marriage as a deal; "who is on top" reversed; wine glass / water glass as trap | world.motifs |

## Character Bible (role templates)

Contract tiers: main = heroine + male lead; all others supporting/minor, each tied to the heroine.
The impostor is the main antagonist but is set as `supporting` in the contract (1-2 main rule).

| Role | Function | Screen | Intro | Recognizable by | Want vs need | Voice | Arc | Ref |
|---|---|---|---|---|---|---|---|---|
| Heroine (main) | Drives every line of plot; sets traps instead of reacting | ~40%, most lines | Seated still behind a desk, giving orders while an enemy shouts | white/black/cream + red lips, silver jewelry, one battle accessory (sunglasses) | escape the transactional bond, take back what is hers vs learn to lean on someone and see who is true | short, cold, ironic, rhetorical questions; wins with papers; VO "mình" when surprised | controls everything alone -> lets him in -> spares an enemy -> refuses the dynasty, builds her own | Cố Vãn Đường |
| Quiet powerful lead (main) | Partner, rescuer, money and files; also a mystery (what did he arrange) | ~22% | Revealed as the stranger of a shared secret, with a condition | one signature suit color + a pin, a ring, a white car | marry and protect her vs tell the truth instead of hiding to protect | low, few words, teasing; flat declarations; soft when caring | partner -> rescuer -> secret lover -> hidden owner -> exiled -> shields her -> husband | Hoắc Vân Thâm |
| Parasite ex-partner (supporting) | First target; humiliated publicly | ~4% | Through his mother's demand | messy hair, flashy ring | money, his mistress vs stand on his own | arrogant, then begging | trap backfires -> exposed -> ruined | Lục Thịnh |
| Loud ex-in-law (supporting) | Public face of the first tier; opens the season, closes it by walking away | ~5% | Shouting in her office (0s) | wine-red velvet, pearls | money and face vs face consequences | shrill, accusing, playing to the crowd | slapped twice -> loses bid -> turns away at the wedding | Lục Mỹ Anh |
| Mirror rival (supporting) | Poorer mirror of the heroine; pawn of tier 1 then tier 3; tests her mercy; pays back with evidence | ~5% | Name card on screen beside the ex | curly hair, red lips, black chain bag | a role, a rich man vs be seen as more than a pawn | whiny, tattling; later choked | enemy -> discarded -> saved -> leaves with evidence given | Lâm Kiều Kiều |
| Impostor "kin" (supporting, main antagonist) | Pulls every string; final enemy | ~6% | Named early as harmless family; appears siding with the rival | dark red lips, short low bun; one object for the climax (lighter) | keep the stolen name, own all families vs live as herself | fake-sweet, money reminders; one scream line when exposed | "mother" -> puppeteer -> not mother -> real name -> falls | Tần Thư Tú / Lục Du |
| Inside-family enemy (supporting) | Tier 2: hostage, ultimatum, overturned by the rules | ~4% | Ordering sabotage | navy pinstripe, a mole | head of the house vs accept losing | barks orders | sabotage -> hostage -> loses shares -> wheelchair | Tần Thiệu Hùng |
| Lead's rival cousin (supporting) | Takes the land bait; enemy of the lead | ~4% | Squeezing her hand to force a deal | thin gold glasses, letter pin, red pocket square | land + heir seat vs learn from defeat | oily, condescending | bullies -> bites the bait -> loses all ("Phó con khỉ!") | Hoắc Tuấn Thành |
| Patriarchs (minor, 1-3) | Bind by blood and gratitude; each falls in turn | ~2% each | With a rule or a cane | glasses, brocade, cane/fan | control vs see who manipulates them | commanding, then soft | bind -> fall (illness, death, exile) | Lục Chấn Hoa, Tần Nghĩa, ông nội Hoắc |
| Her assistant (supporting) | Reports = exposition; comic chorus ("Sếp, không hay rồi") | ~8% | Name card + report | bow-neck blouse, purple phone case | help the boss vs be trusted | fast, calls her "Sếp" | messenger -> confidant | Cảnh Trừng |
| Young suitor (supporting, optional) | Shows she chooses; bridge to the final villain (her son) | ~6% | Steps in to save a public humiliation | ash-dyed hair, silver hoop | be seen as a man vs face the truth about his mother | smooth, calls her "chị" | admirer -> refused -> shields her -> leaves | Tạ Nhiên |
| Media friend / hostage ally (minor) | PR weapon + teller of his past; hostage then investigator | ~2-4% | Braid + camellia / bandaged head | - | - | playful / weak but firm | - | Nguyên Nhã, Từ Việt |

- Each supporting character holds one lever (money, file, media, hostage, heir right) so each fight
  has an object to win or lose (1257, 1536, 2486, 6864). Small roles get a name card at first
  appearance (104.8, 284.2). Past told by a third party (gossip, short flashback), then an instant
  reaction (2661-2770). A villain turns only for a reason she gives (rescue, mercy), never by a long apology (6380-6660).

## Storytelling Rules

- **Victim is the author**: in every big confrontation she has a move prepared 1-2 episodes before
  but unsaid; let the enemy finish accusing, then turn it (2.8; 1567 "bản phô tô"; 7343 "Lừa anh đó").
- **Trap boomerang**: write each enemy trap together with how it turns back and what she gains;
  show the trap being set first (289). Vary trap type (contract, room, media, land) and who turns it.
- **Public face-slap by ledger**: a document with an exact odd number read aloud, witnesses (press,
  guests, shareholders), cut to the loser's face. One every ~10-15% of the season (1536, 3460, 4744).
- **Villain ladder**: outsider -> inside the family -> impostor posing as kin; each new tier enters
  as the last falls (1923, 2918, 8957); tier 3 present from the first 5%.
- **Lead's love is older than the story**: reveal 4-6 layers (partner, rescuer, secret love,
  hidden owner, the one she saved); one layer every ~10-15% (1048, 1655, 4091, 7835, 9480).
- **Callback reversal**: 5-8 couple lines from the first half return in the second half with the
  speaker or power reversed (1048 -> 8415; 4659 -> 5788).
- **Cut mid-sentence, answer within 20s**: cut before the decisive noun/name; the next episode answers
  in its first 20s and opens a new consequence. What is behind the cut must change the situation (A6 risk).
- **She is never the last to know** (A5): others may hide things "so she won't worry"; she already
  knew or planned it. Exactly one shock she did not foresee.
- **Spare the fallen enemy**: at ~65-70% save and spare a low-tier villain who was publicly punished
  first; at ~85-90% they pay back with evidence (6610; 8563).
- **Wink at the genre**: after a big vow or an over-the-top twist, one short line names it ("Xem phim
  ngắn nhiều quá rồi hả?", 1575). At most once per ~10 episodes.
- **Exposition + POV**: news-like lines, assistant reports, phone reads, headlines, gossip, each key
  fact with a prop or on-screen text; close third on her, cutaways to the enemy side (irony).
- **Avoid** (film_analysis weaknesses): recaps > 20s; act-3 sag (40-70% still needs a big reveal every
  ~10-15% and comedy max 1 episode); inconsistent money (one scale in the bible); impostor without a
  reason never to be tested (give one + earlier clues); allies' mistakes with no cost; off-screen
  resolutions (settle climaxes on screen); last-second rescues not planted (the rescuer has a reason
  and a route shown before); forced kisses, drug-and-film traps, sexual innuendo (refused by video
  tools; use a battle of wills instead); a final villain explained by a 3-minute monologue (spread the
  motive over 3-4 earlier scenes, keep one closing line); romanticizing the lead's hiding (she
  challenges him on screen, he pays); family titles that contradict (one family tree, `address_matrix`).

## Pacing Guidelines

| Metric | Value | Ref |
|---|---|---|
| Avg / median shot | 2.65s / ~2.2s (median estimated) | craft.pacing |
| Cuts per minute | 22.6 -> ~34 shots per 90s, ~23 per 60s, ~45 per 120s | 3648 shots / 9663.6s |
| By act (avg shot) | 1: 2.6s, 2: 2.13s, 3: 2.93s, 4: 2.64s, 5: 3.43s | by_act |
| Fastest | fights, fire, exposure videos 0.5-0.9s; part 3 1.9s/shot (31.6 cuts/min) | cut_rhythm_notes |
| Longest | inner monologue or phone listening 12-24s (rare, max 1 per episode) | 498, 5440 |
| Cut type | hard cuts on each line (shot/reverse); card cuts straight into the next episode | cut_rhythm_notes |
| Story events | big event every ~115-174s in the reference -> here >= 1 per episode; hook every ~45s | A10 |

## Tone & Voice Guidelines

- Tone: CEO romance + upper-class face-slap revenge, self-aware and wryly funny; the heroine always
  holds the upper hand; love sweet with thorns. Energy medium-high, peaking at each episode end;
  calmer in the aftermath and wedding. Emotions: contempt, gloating, jealousy, tension, sweetness,
  shock, grief.
- Speech rate: NOT measured reliably (A1: ASR timing drifts, wpm/speech share unusable). The limit is
  vi-dialogue.md "Speech rate" (<= 5.0 syllables/s).
- Lines: exchanges mostly 3-12 syllables ("Là anh?", "Tôi quyết định."). Long speeches (40-90
  syllables) only at a press statement, a fallen enemy's grievance, or a villain's confession.
  VO ~5.5% of lines (analyst labels): heroine's wry self-talk when surprised, enemies' inner
  calculations, the lead's hidden investigation, headlines. VO says "mình"; spoken lines "tôi/em/cháu".
- Patterns: "not A, but B" reframing; mirror condition ("you want me to fall? your house falls
  first"); rhetorical question as a blow; short maxims about debt and deals; an exact number as the
  punchline; two-clause declarations.
- Style examples (attitude only):
  - "Vậy sao? Nhưng mà đám phóng viên đó là do tôi sắp xếp hết á." (heroine, 2.79)
  - "Chẳng qua cũng chỉ là từ một cuộc giao dịch này đổi sang một cuộc giao dịch khác." (heroine, 1164)
  - "Cái tôi đưa cho bà đương nhiên là bản phô tô rồi. Bà đang nghĩ cái gì vậy?" (heroine, 1567)
  - "Không phải vì hợp tác... Mà là vì... Tôi thương em." (lead, 3661)
  - "Tôi là chủ nhà họ Tần. Tôi quyết định." (heroine, 5391)

### Dialogue language

Vietnamese (or any non-English) screenplay: follow `.claude/skills/dialogue-polish/references/vi-dialogue.md`
(it overrides the numbers and lines above on conflict). Clarity first: the viewer watches once on a
phone; hide facts, not grammar. The reference lines above show ATTITUDE only: never translate their
sentence shape (they are a dub of Chinese; avoid dub-isms and Sino-Vietnamese stiffness unless a
character is written that way). Line lengths are averages, not caps. Xưng hô fixed by the bible
`address_matrix`. Lines are speech, not description: characters talk TO each other for a reason; VO
says what the image cannot (never retells the shot, never defines a word); invented terms become
clear in use, everyday words are never explained; every scene with 2+ characters on screen has a
spoken exchange. The reference's VO share is a measured average, not a target: after an opening
pitch, VO stays <= ~50% of lines. Imitate the newest hand edits in `data/dialogue_examples.json`
when it exists.

## Visual Guidance

Aspect 9:16. Shot mix: CU 51%, MCU 23.5%, MS 13%, WS 6.5%, ECU 6%. Camera almost static; rhythm
comes from cutting shot/reverse on each line.

### Camera

| When | How | Ref |
|---|---|---|
| Confrontation or flirting | CU/MCU shot/reverse with a blurred foreground shoulder/glass; cut every 1-2s on the line | CU ~51%; part 3 1.9s/shot |
| Decisive object (paper, card, test, lighter) | ECU insert 0.5-1.5s before the character uses it | 472-481; 534; 9057 |
| Rescue / lead's entrance | backlit in a doorway, low angle or cut up from the feet, one beat slower | 2561; 8685 |
| Public win | WS of the room, then CU of the winner, intercut CU of the loser | 3452-3484; 5387 |
| Episode end | hold the stunned reaction CU; light push-in; title card overlay + sting | 1009.7; 1188.6; 1561.4 |
| Chaos (shoving, emergency, fight, reporters) | light handheld only here; whip/blur transitions | camera.movement |
| Signature shots | ECU documents as weapons; ECU hands (tie pull, tight handshake); high WS of beaten thugs with her in sunglasses; split screen of two women; ECU lighter/blood/bare foot at peak danger | signature_shots |

### Color and lighting

- Palette: cream/white/beige high-key homes and offices; warm orange wood (office, his house);
  red wood + mauve for stifling family houses; teal/navy + orange bokeh for night confrontations;
  bronze-gold for banquets; his suit color (green/teal) and red lips/blood as the two accents.
- Costume color = role: heroine white/black/cream + red lips; lead green/grey/white pinstripe;
  older villainesses wine-red or black-white stripes; male enemies navy.
- Split rivals in one scene by background: one warm orange, one cold blue (1931-1990).
- At a climax, blood/fire/red lips are the only warm accent on a cold frame (8861-9138).
- Looks: office soft day; suite amber, wine-brown when tense; night car low-key blue LED; banquet
  gold, foreground flowers; hospital pale beige-blue; factory black-navy + orange fire; wedding
  soft sunset, white and grass green. Lighting: soft beauty key by day; low-key cold + backlight
  in danger; warm rim and bokeh in intimate scenes.

## Sound Guidance

- Dialogue-driven; speech share and wpm not usable (A1). VO short, mostly the heroine's asides.
- Music (inferred, no audio evidence): dramatic bed in confrontations; piano/synth for the couple;
  dark ambient in cars/lifts; sting on each end card; sad strings at the grave; comic cue after a
  takedown; tense bed under the villain's one-line confession.
- Silence: a 0.5-1.2s pause before a decisive line (1039-1040 before "Kết hôn với tôi", ASR-timed,
  approximate); ~3.6s of silence on the final card. J-cut: a phone voice over the next establishing shot (231.7).
- SFX: cup slammed on a desk, water splash, card-lock beep, phone ring, car/lift doors, cane strike,
  porcelain breaking, Zippo click, roaring fire, suitcase wheels.

## Hook Patterns

- **0-3s premiere**: an enemy demands she fix a crisis; she says calmly she caused it. One static
  shot, the hook is the line (first cut ~5s).
- **0-60s premiere**: debt already repaid, loveless marriage, her intent to leave, and one origin
  insult; end on the role-reversal line.
- **0-3s other episodes**: the exact frame/line after last episode's cut; answer the half-line within 20s.
- **Mid-episode (25-50s)**: the opponent's demand, rule or deadline; a "Sếp, không hay rồi" report.
- **Ending families** (reference counts: reveal 13, danger 10, power reversal 10, romance 5, loss 1):
  reveal (cut mid-sentence before the name; identity; villain), danger (hostage, deadline, life or
  death, newcomer threat), power reversal (face-slap, declaration, trap reversed), romance (public
  choice, kiss/hand under the card, grand gesture), loss (exile, cut ties). Never 3 episodes in a
  row from the same family; romance right after danger.
- **Finale** (ep N): opens on the climax cut, then aftermath + ending shown (independence +
  "Em đồng ý" in the reference); `cliffhanger_type: "resolution"`; at most one wink left open.

## Output Format

`episodes/epNN_vK.md`:

```markdown
# EP03 — <Title> (90s)
Logline: ... | Story beats: <template beats> | Cliffhanger: <type>

### SC1 [00:00-00:12] INT. <PLACE> — DAY  {loc_01 · char_01:o1}
| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |
|---|---|---|---|---|---|---|
| 0.0-1.8 | CU | <frame / event><br>**Name**: <does>; mặt: <face>; cầm: <holds> | "..." | static, OTS blurred shoulder | cream high-key | cup on desk |
```
(`python3 -m app.pipeline.screenplay render <session-dir> <N>` writes this md from the JSON; a scene's
`blocking` prints as a `Vị trí:` line under its heading.)

`episodes/epNN_vK.json` (read by `/script-to-shotlist`):

```json
{
  "skill": "write-series-phim-ng-n", "skill_version": "v1", "session": "<session-id>",
  "episode": 3, "title": "...", "total_duration_sec": 90, "aspect_ratio": "9:16",
  "logline": "...", "story_beats": "<template beats + %>", "cliffhanger_type": "<hook pattern name>",
  "characters": {"char_01": {"name": "...", "visual_signature": "<bible, verbatim>", "outfits": ["char_01_o1"]}},
  "scenes": [{"id": "SC1", "start_sec": 0, "end_sec": 12, "location": "<registry name>", "loc_id": "loc_01", "variant_id": "loc_01_day",
    "cast": {"char_01": "char_01_o1"}, "referenced": [], "props": ["prop_01"], "int_ext": "INT", "time_of_day": "day",
    "blocking": "<who is where, facing whom, what is within reach>",
    "beats": [{"start_sec": 0, "end_sec": 1.8, "shot_size": "CU", "characters": ["char_01"], "action": "...",
      "acting": [{"character": "char_01", "does": "<body + hands>", "face": "<visible expression>", "holds": "<in hand at beat end, or empty>"}],
      "dialogue": [{"character": "char_01", "line": "...", "voiceover": false, "delivery": "cold"}],
      "camera": "...", "lighting_color": "...", "sound": "..."}]}],
  "new_assets": [], "cliffhanger": "...", "ledger": {"opened": [], "clues": [], "answered": []}
}
```
Last episode adds `"ending": {"type": "happy|bad", "central_question_answer": "..."}`. A scene told as
a flashback adds `"flashback": true` (continuity: the dead and the gone may appear there).

`bible_vK.json`: `{title, logline, premise, theme, world: {setting, rules[], locations[], motifs[]},
cast: [{character_id, name, tier, role, want, need, flaw, secret, tell, visual_signature, voice:
{style, sample_lines[]}}], ledger_plan: [{id, question, tier, open_ep, audience_knows_ep,
heroine_knows_ep, clue_eps[], answer_ep, answer}], villain_ladder: [{tier, character_id, enters_ep,
falls_ep}], traps: [{ep, set_by, target, turns_back_ep, gain}], leverage: [{prop, used_ep}],
lead_backstory: [{piece, reveal_ep}], money_scale, family_tree, signature_lines: [{line, speaker,
callback_ep}], relationships[], address_matrix, glossary}` + story contract fields (main_plot,
ending, setting_timeline, climaxes, cast relation_to_main/arc/secret_reveal_ep).

`outline_vK.json`: `{episodes: [{episode, title, logline, beats[], template_beats: [{pct, function}],
reveal, cliffhanger_type, characters[], act, main_plot_step, locations[], setting_change, climax,
ledger, events: [{id, text}], because[], opens_from}], never_answered[]}`; last episode `ending` +
`cliffhanger_type: "resolution"`.

## Self-check

- [ ] Beats placed via `ceil(p/100 * N)`, max 3 per episode; ep 1 owns the crisis in 3s, role-reversal + origin plant in 60s
- [ ] Each episode: hook answers the last cut within 20s, one new info, a turn, a reveal, a cut-off
      cliffhanger; no 3 consecutive endings from the same family; danger followed by romance
- [ ] Villain ladder of 3 tiers; tier 3 on screen or named in the first 5%; one false plant paid ~70%
- [ ] Every trap set on screen before it fires, turns back, and gives her a concrete gain
- [ ] A public reversal with documents/exact number + witnesses every ~10-15%; climaxes at ~16%,
      48-56%, 92-95%; never >3 episodes without one
- [ ] Ledger: max 4 big questions open; `audience_knows` before `heroine_knows`; she is never the
      last to know; one unforeseen shock; all answered by the finale except at most 1 wink
- [ ] Lead's backstory revealed in 4-6 pieces, last = what she did for him; his hiding is challenged on screen
- [ ] Money matches the bible scale; titles match the family tree / `address_matrix`; recap <= 20s
- [ ] ~34 shots per 90s, ~51% CU, static camera; signatures verbatim; timecodes sum to `--episode-sec`
- [ ] Every scene has `loc_id` + `variant_id` and every on-screen character an outfit from the asset
      registry; `_assets.py lint` 0 errors
- [ ] `_story_check.py` 0 errors; `_continuity.py check` 0 errors (cause chain, state ledger covers
      every episode, every rescue and trap planted)
- [ ] `_dialogue_lint.py`: 0 `definition` / `narrates_action`; `_action_lint.py`: 0 `missing` /
      `prop_vanish` / `no_blocking` / `minor_risk`; no forced kiss, drug trap or sexual innuendo

## Data limits

- One video, 9663.6s (~161 min), ~98 mini-episodes (film_analysis; DNA said ~100), 81 units in 11
  parts. Chinese drama dubbed into Vietnamese; no title on screen. A 12 x 90s season is ~8x shorter:
  the template keeps order and % of beats, not every event; cast cut from 16 named to ~8-10.
- High-severity audit applied over the DNA: A1 ASR times drift up to ~20s, so speech_pct 22, 158 wpm
  and silence timings are not rules (project speech limit instead); A2 real-mother question closed
  (9193.8); A3 trap boomerang + consistent divorce line added; A4 audience knows the puppeteer at
  ~2918, not 3763; A5 "lead hides info to stretch episodes" replaced by "she already knew".
- DNA `reveal_rhythm_sec` 23 unexplained (A10): replaced by big event ~174s mean / 115s median,
  strong hook ~124s, any hook ~48s. Break candidates all strength 3 (A12): film_analysis cuts used.
- Speakers not diarized (transcript `diarized: false`): attribution by analysts, `speaker_unsure` in
  parts 3-4; VO share 5.5% from analyst labels. Music inferred. Median shot pooled from part medians.
- Money in dub vs subtitles disagrees (600 tỷ vs 2亿; land 48.000/54.000 tỷ): keep one scale per series.
- Not carried over (reference facts only; video tools refuse them): forced kiss (1160), drug-and-film
  trap (289-396), sexual audio/innuendo (710, 4818, wedding night 9634).
- Ending: happy (independence + wedding) with one deliberate wink (did he arrange the hotel night),
  allowed by the contract as the one minor open question.
- Contract tiers: DNA tags the impostor `main`; this skill sets main = heroine + lead (default).
- Slug `phim-ng-n` = the app's slug of "phim ngắn" (kept). Non-interactive run: defaults 12 eps, 90s.

## Changelog

- v1 (2026-10-21T02:13:37Z): generated from `data/analyses/20261019-025904/dna.json` +
  `film_analysis.json` (one 9663.6s video, 81 units). High-severity audit items A1-A5 applied over
  the DNA; medium items A6-A11 folded into the template and ledger. Non-interactive run.
