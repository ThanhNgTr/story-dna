# Vietnamese dialogue guide (clarity first)

For every skill that writes or rewrites dialogue / VO in Vietnamese (`write-series-<slug>` Stage 3,
`/refine-skill`, `/story-editor --apply`, `/continue-series`, `/dialogue-polish`).

**It overrides style skills on conflict.** Style skills learned from a reference (often in another
language) give word caps ("under 8 words", "two to four words", "single-word orders") and ask for
"ambiguous" lines. Translated into Vietnamese those produce riddles. Keep the style's INTENT (short,
tense, unsoftened, VO that undercuts) and drop any cap that makes a line unclear.

## The one test

The viewer watches once, on a phone, maybe without sound at first (subtitles). After each line they
must know: **who** is talking to **whom**, **what** they mean on the surface, and roughly **why**
they say it. Mystery comes from what is HIDDEN (a fact, a motive), never from words that cannot be
parsed. Hide facts, not grammar.

Read every line aloud: would a Vietnamese person aged 20-35 say exactly this in that situation? If
it sounds like a translated novel, a poem or a slogan, rewrite it.

## Rules

1. **Full spoken sentences.** Subject + verb unless the context makes the subject obvious (a reply,
   an order). No chains of noun fragments ("Mùi chanh. Như ai vừa lau sạch một người.").
2. **Particles make it human.** Use spoken particles where people would: à, ừ, ờ, đấy, đâu, mà,
   chứ, nhỉ, nhé, thôi, đi, hả, sao, vậy, rồi. A line with none often sounds like a robot or a
   subtitle translation.
3. **Xưng hô is fixed per pair.** The bible's `address_matrix` decides who calls whom what
   (tao-mày, tôi-anh, em-anh, cháu-ông...). Never switch inside a scene without a story reason (anger,
   distance, intimacy), and when it switches, the switch IS the beat. VO uses one pronoun all season.
4. **One image per line, at most one figure of speech per scene.** Metaphors ("như...", "là một
   món quà") only in VO, max 1-2 per episode, and the plain meaning must be obvious. Never two
   abstract sentences in a row.
5. **Clear referents.** "nó", "cái đó", "người đó", "ở đây" point to something on screen or named
   in the same scene. Otherwise use the name.
6. **World terms are introduced plainly once.** A rule, a code name, a number system ("Điều Năm",
   "khách 07", "cụm", "niêm phong") is explained in plain words the first time (dialogue, VO or a
   visible sign), then reused as is.
7. **Numbers and time as people say them.** "mười giờ tối", "bốn năm nay", "phòng số hai". The
   formal 24h style ("hai mươi hai giờ") only for a machine / announcement voice, and say so.
8. **No calques from English.** Avoid: "Tôi ngủ cả đêm" (-> "Tôi ngủ một mạch tới sáng"), "Điều đó
   có nghĩa là...", "Bạn ổn chứ?" between Vietnamese people who use other pronouns, overuse of "được /
   bị" passives, "Cảm ơn" as filler, "đúng không" tag on every question.
9. **Subtext = a clear surface line with a second reason under it.** "Mày ăn gì chưa?" said to stop
   a friend from leaving is subtext. "Nhà chỉ không trả lại." is a riddle. The surface must be plain.
10. **VO says what the protagonist thinks or feels, plainly, and may contradict the image.** Irony
    works only if both sides are understood: show the lie, then VO "Tôi nói dối. Nói dối dễ hơn
    phải nhờ cô ấy." Not "Nói dối rẻ hơn là nhờ."
11. **Length serves clarity.** Short is good; cryptic is not. A spoken line up to ~18 words is fine
    when it needs to be clear. Keep the style's TOTAL words per episode roughly; shorten elsewhere.
12. **Each character sounds like themselves** (age, region, class, job): the bible's `voice.style`
    is a speaking style in Vietnamese terms (ví dụ: "nói cộc, hay chửi thề nhẹ, gọi bạn là mày"),
    not an English description.
13. **Announcements, rules, system voices** may be formal and cold, but still grammatical Vietnamese.

## Before / after (from a real draft)

| Draft (unclear) | Why | Rewrite |
|---|---|---|
| VO: "Nhà này dọn sạch mọi thứ. Trừ cái nó không nhìn thấy." | "nó" unclear, slogan | VO: "Cái nhà này xóa sạch mọi dấu vết. Chỉ trừ chỗ camera không quay tới." |
| VO: "Một tấm rèm. Sáu căn nhà trả." | noun fragments, cause missing | VO: "Chỉ vì một tấm rèm bị mở, cả sáu căn nhà phải chịu phạt." |
| VO: "Mùi chanh. Như ai vừa lau sạch một người." | metaphor without plain meaning | VO: "Phòng cô ấy thơm mùi nước lau sàn. Như thể có ai vừa xóa cô ấy khỏi đây." |
| "Tôi ngủ cả đêm." | calque, unnatural | "Tôi ngủ một mạch tới sáng mà." |
| "Hai mươi hai giờ. Rèm đóng. Chúc khách ngủ ngon." | fine ONLY as a machine voice | (giữ, ghi rõ: giọng loa tự động) |
| "Nhà chỉ không trả lại." | riddle | "Cái nhà này không giữ ai cả. Nó chỉ không bao giờ trả người về." |
| VO: "Nói dối rẻ hơn là nhờ." | compressed idiom from English | VO: "Tôi lại nói dối. Nói dối còn dễ hơn mở miệng nhờ cô ấy." |
| "Khách tám. Ngày bốn." | formal code, never explained | "Khách số tám, hôm nay là ngày thứ tư của anh." |

## Bible fields (Vietnamese series)

- `address_matrix`: `[{"pair": ["char_01", "char_05"], "a_to_b": "mày", "a_self": "tao", "b_to_a": "mày", "b_self": "tao", "why": "bạn đại học thân"}]`
- `voice.style` in Vietnamese speaking terms; `voice.sample_lines` that pass this guide.
- `glossary`: world terms with a plain explanation and the episode where it is first explained.
