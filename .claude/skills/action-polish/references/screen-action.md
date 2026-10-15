# Screen action guide: what every person DOES in every shot

For every skill that writes or rewrites episodes (`write-series-<slug>` Stage 3, `/refine-skill`,
`/story-editor --apply`, `/continue-series`, `/action-polish`). Dialogue rules stay in
`.claude/skills/dialogue-polish/references/vi-dialogue.md`; this guide covers the body, the hands, the
face and the objects around the lines. Base looks (face, hair, costume) stay in the asset registry
(`.claude/skills/series-assets/references/episode-contract.md`); this guide covers what CHANGES.

## The one test

Turn the sound off. From what each person does on screen, the viewer still knows who wants what,
who is hiding something and how each line lands. An actor can play every word of it in the beat's
seconds, and a camera can film it. If a beat only says "Phong nhìn", "Vy nghe", "hai người im lặng",
it fails.

## Where it lives (episode JSON)

```json
{"id": "SC3", "blocking": "Vy ngồi một mình đầu bàn dài, quay mặt ra cửa; Phong đứng sau ghế Vy, cầm bình nước; ông Hữu vào từ cửa trái",
 "beats": [{"start_sec": 26.2, "end_sec": 28.2, "shot_size": "MS", "characters": ["char_03", "char_02", "char_01"],
   "action": "Ông Hữu bước vào, điện thoại kẹp tai, cúp máy cái rụp",
   "acting": [
     {"character": "char_03", "does": "sải bước tới bàn, ném điện thoại xuống mặt kính", "face": "hàm bạnh, không nhìn ai", "holds": ""},
     {"character": "char_02", "does": "khựng tay, đặt nĩa xuống thật nhẹ, ngồi thẳng lưng", "face": "mắt cụp xuống đĩa", "holds": ""},
     {"character": "char_01", "does": "lùi nửa bước sát tường, hai tay ôm chặt bình nước trước bụng", "face": "mắt liếc theo ông Hữu", "holds": "bình nước thủy tinh"}],
   "dialogue": [{"character": "char_03", "line": "Ngân hàng lại hối nữa rồi.", "voiceover": false, "delivery": "cáu"}]}]}
```

- `scene.blocking` (one sentence, scene start): where each on-screen person is, which way they face,
  what is within reach (bàn, cửa, bếp lò). Required when 2+ characters are on screen.
- `beat.action`: the shot as the camera sees it: what is in frame, the event, what changes. Keep it
  short; do not repeat the `acting` text in it.
- `beat.acting`: one entry per character VISIBLE in the beat (the beat's `characters` that are in the
  scene `cast`; a voice heard off screen gets none). Listener included.
  - `does`: body + hands, concrete verbs, present tense: "tay run run rót trà, nước sánh ra đĩa".
  - `face`: what the face and eyes show: "mím môi, mắt không ngẩng lên". `""` when the face is not in
    frame (insert on hands, back to camera).
  - `holds`: what is in the hands at the END of the beat ("ấm trà", "điện thoại, màn hình úp xuống");
    `""` = empty hands. A registered prop uses its registry name, optionally `(prop_04)`.

## Rules

1. **Everyone visible acts, every beat.** The listener's reaction is half the scene: it shows
   whether the line lands. "Vy nghe" is not acting; "Vy ngừng nhai, đặt đũa xuống" is.
2. **Visible, not psychology.** Feeling words (buồn, tức giận, lo lắng, xúc động, hồi hộp, bối rối,
   sợ hãi, cảm thấy, đau lòng, hạnh phúc) never stand alone: write the sign the camera sees
   ("tức giận" -> "bóp méo lon nước trong tay"; "lo lắng" -> "ngón cái cạo cạo mép móng tay").
3. **Hands first.** Hands carry the subtext: run run, siết vạt áo, xoay chiếc nhẫn, gõ ngón tay lên
   bàn, nắm chặt quai túi. Each main character's bible `tell` comes back at their emotional turns
   (not every beat, so it keeps its meaning).
4. **Give every scene business.** People talk WHILE doing something that fits the place and their
   job: rót trà, gắp thức ăn, lau bàn, xếp khay, buộc dây giày, đếm tiền, sạc điện thoại, quét sân.
   The task gives the hands something to betray: the action may contradict the line
   ("Con không sao đâu." while tay run làm sánh trà ra khay). That is subtext without a riddle.
5. **Objects stay in hand.** What is held stays held until a beat puts it down, hands it over,
   pockets it or drops it, and that moment is written ("đặt ấm xuống khay", "nhét điện thoại vào túi").
   Object state carries over too: trà đầy -> vơi, bốc khói -> nguội, chén lành -> vỡ.
6. **Positions stay true.** People move only in a written beat (đứng dậy, bước tới cửa, quay lưng).
   Eye lines are written when they matter: who looks at whom, who looks away.
7. **Fit the seconds and the frame.** About one main action per ~1.5s of beat (a 1.6s CU holds one
   gesture + one look). Shot size decides what can be seen: ECU = one detail (mắt, tay, môi); CU = the
   face, a hand near the face; MCU / MS = hands and upper body; WS = whole body and positions. Do not
   write leg movements in a CU.
8. **Change, not costume.** Write what changes in the beat (cầm lên, khựng lại, quay đi, áo ướt
   sũng); the base look is the registry's.
9. **Restraint.** Small, specific gestures read bigger on a phone than big ones. No crying, screaming
   or fainting unless the scene turns on it. The style skill's body tells (the powerful kind's
   involuntary signs, the lead whose body betrays his words) are kept and placed at the turns.
10. **Voice-over beats are silent.** The VO speaker on screen keeps the mouth closed; no action that
    invites speech ("định nói", "mấp máy môi hỏi"). Use silent actions: "nhìn theo, không nói gì".
11. **Language and words.** Same language as the screenplay. Verb first, short clauses separated by
    commas; no adverbs piled up ("chậm rãi, nhẹ nhàng, từ tốn"); no camera words in `acting` (the
    camera lives in `camera`).

## Before / after

| Beat | Before (only lines) | After (`acting`) |
|---|---|---|
| CU 1.8s, mẹ: "Con không sao đâu." | Mẹ nói, giọng nhỏ | Mẹ: `does` "tay run run nhấc ấm, rót trà, nước sánh ra khay"; `face` "cười gượng, mắt không nhìn con"; `holds` "ấm trà" |
| MCU 2.0s, con nghe | Con nhìn mẹ | Con: `does` "đưa tay đỡ lấy ấm trà khỏi tay mẹ"; `face` "nhíu mày, nhìn bàn tay mẹ"; `holds` "ấm trà" |
| CU 1.6s, ông chủ: "Đầu tư thì phải có lời." | Ông Hữu nói | Ông Hữu: `does` "gõ ngón tay lên mặt đồng hồ vàng, ngả lưng ra ghế"; `face` "nhếch mép, nhìn con gái từ đầu tới chân"; `holds` "" |

## Children on screen

Any character under 18 also follows `.claude/skills/story-contract/references/minors-on-screen.md`: no sleep, bed or touching with an adult, full
clothing, no secret phone at night, a hand habit instead of a mouth habit, distress shown without tears.
Lint flag `minor_risk` (strict).

## Checks

`python3 .claude/skills/action-polish/_action_lint.py lint <session> [N...]` -> `action_check.json`.
Flags: `missing` (a visible character has no `acting`), `vague` (only "nhìn / nghe / đứng / im lặng"),
`abstract` (a feeling word with no visible sign), `overloaded` (more actions than the beat's seconds
hold), `prop_vanish` (held object gone with no beat putting it down), `no_blocking` (2+ characters on
screen, no `blocking`). Writers fix `missing`, `prop_vanish` and `no_blocking` to 0; the rest are hints.
