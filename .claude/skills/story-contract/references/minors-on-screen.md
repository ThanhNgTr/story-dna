# Minors on screen: write scenes a video tool will make

For every skill that plans or writes the story (`write-series-<slug>` Stage 2 outline + Stage 3 episodes,
`/refine-skill`, `/continue-series`, `/story-editor --apply`, `/action-polish`, `/dialogue-polish` when it
moves a line). Read it BEFORE planning the outline and BEFORE writing each episode, not after.

A minor = any character under 18: bible `cast[].age` / visual signature ("10 tuổi"), or the asset registry
`age`. The story may give a child any role (the matchmaker, the reason the hero works); what changes is
HOW their scenes are staged.

## Why

Google Flow (Veo) refuses a clip as "harmful content involving minors" from the whole scene, not a word.
Refused in this project (ep04, Na, 10): a child described by body (skinny, barefoot, shorts) next to a man
in a tank top; late night, a bed / sleeping mat in the room; touching (ruffling hair, sitting pressed
together); an adult asleep beside the child; and, after all of that was removed, still: a child ALONE on a
porch after dark, secretly using her brother's phone to message someone. ep06 (2026-10-15): Na (10) in the
doorway with her brother AND his co-worker, twisting her phone strap, saying "the phone texted by itself":
refused 5 times, also re-staged in daylight. The same story passed only when the child was out of the frame
(adults + an off-screen voice); a child-only shot is generated on its own and cut in.
The root was the bible: her `tell` (chewing the phone strap), her signature prop (a keypad phone on a neck
strap) and her secret (texting from her brother's phone) put a phone in every scene she was in. A script
that needs those shots cannot be produced; the prompt step can only hide the child, and the episode loses
her face.

## Rules (the story keeps its beats; the staging changes)

1. **Time and place.** A child's scenes are in daylight or early evening with the light on, in an open or
   shared place: the yard, the alley with neighbours, the shop, the school gate, a meal at the table with
   the door open. Not "late night", "midnight", "khuya", not a dark small room.
2. **No sleep, no bed.** No bed, sleeping mat (chiếu), blanket, sleeping, dozing, waking up, bathing,
   changing clothes while a child is on screen, and no adult asleep next to a child. A tired adult
   "rests at the table", "has gone out to wash up", off screen.
3. **No touching between an adult and a child.** No hug, carrying, piggyback, lap, ruffling hair, kiss,
   holding hands, wiping tears, sitting pressed together. Care is shown through things and looks:
   a bowl pushed across the table, a jacket left on the chair, a shared laugh, an arm's length apart.
4. **Full clothing.** School uniform or T-shirt + long trousers; no shorts, sleeveless tops, sleepwear,
   bare feet. Adults in the same scene fully dressed too (no tank top, no shorts).
5. **No secret contact.** A child does not secretly use a phone or computer to contact anyone, alone,
   at night. If the plot needs the child to reach someone, do it openly and in daylight ("Anh Hai cho em
   mượn điện thoại nhắn cô giáo" with the brother in the room; at school with a teacher nearby; on her
   own keypad phone at the shop counter), or let the act happen OFF screen and show the result.
6. **No harm or distress shots.** No injured child, no child in danger, no crying child next to an adult.
   Distress = a set jaw, fast blinking, a fist on the knee, in a medium shot.
7. **The body is not described.** Action and `acting` name what the child DOES (counts on her fingers,
   pushes the bowl, runs to the gate), never body or face shape (skinny, small, lips, mouth, legs), never a
   close shot on the mouth (a mouth habit becomes a hand habit: twisting a strap).
8. **No device in a child's hands or shot.** No phone, tablet, computer, screen, texting, calling, contact
   list in a shot where the child is seen, and not as the child's prop. A plot where the child contacts
   someone (matchmaker, calls for help) keeps the beat: the act happens OFF screen, the result is shown
   on the adult side (the adult finds the sent message on his own phone, the guest arrives holding hers),
   and the child's scene is about the words and the face (the denial, the confession), hands empty or on
   a school thing (a notebook, a pencil, a schoolbag strap).
9. **One adult at most in the child's shot.** A beat that shows a child shows at most one adult, from the
   family or the one who looks after them (parent, older sibling, teacher). Other adults (co-workers,
   guests, bosses, strangers) are in their own shots of the same scene; the edit cuts between them. A
   shared meal or a crowded alley stays a shared place: the camera gives the child her own shots.

## The bible (before the outline)

The child's design decides every later scene. In the bible `cast[]` entry of a minor:
- `tell` is a hand or object habit (counts on her fingers, twists the schoolbag strap, taps a pencil),
  never a mouth habit (biting, chewing, sucking) and never a device.
- `visual_signature` and the signature props: clothes, hair, a school thing, a toy, a charm; no phone or
  other device, no body or face shape words (skinny, small, dark-skinned, big eyes, lips).
- A role built on contact (matchmaker, messenger, informant) is staged by rule 8: the child decides and
  speaks, the contact itself happens off screen or openly through an adult ("Anh Hai, nhắn chị Vy giùm em").
`_story_check.py` flags a minor's `tell` / `visual_signature` with a mouth habit or a device.

## Dialogue

Lines may stay as written (a sister telling her brother to sleep is fine as a line); the staging around
it follows the rules. Because the child gets her own shots (rule 9) and may be cut in from a separate
generation, a line TO the child names her the first time in a scene ("Na! Em nhắn hả?", not "Em nhắn
hả?"): the viewer must know who is spoken to when the child is not in the same frame.

## Checks

- Outline: every episode row that has a minor on screen says where and when (daylight / evening, place).
- Bible: `_story_check.py` (rule 8 + "The bible": a minor's tell / signature with a mouth habit or device).
- Episodes: `python3 .claude/skills/action-polish/_action_lint.py lint <session> [N...]` flags
  `minor_risk` (rules 1-9 in action / acting / scene time: devices, two or more adults in the child's beat) as a STRICT flag: fix to 0 before the episode is
  done. The prompt step (`script-to-shotlist` "Minors") is the second net, not the first.
