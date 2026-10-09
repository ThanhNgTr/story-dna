# Story editor rubric: depth

The story contract (`../story-contract/`) checks that the parts EXIST. This rubric judges whether
they WORK. A script can pass the contract and still be flat: this is where that gets caught.

Score each dimension 1-5. Every score cites evidence from the files (episode, scene, quoted line
or bible field). No evidence -> no score above 2 ("not on the page").

| Score | Meaning |
|---|---|
| 5 | Strong: a viewer would feel it; nothing to fix |
| 4 | Works; small polish only |
| 3 | Present but thin or generic; a clear fix would lift it |
| 2 | Weak: told not shown, inconsistent, or only in the bible, not in the scenes |
| 1 | Missing or works against the story |

Pass: every dimension >= 3 and average >= 3.5. Otherwise verdict `revise`.

## Dimensions

### 1. `theme` — Chủ đề
- One idea the story argues (a question about people, not a topic): "Is a lie that protects
  someone still a betrayal?" not "lies".
- The main plot, at least two subplots and the ending each answer it from a different angle.
- The ending's happy/bad outcome is the theme's answer, not luck.
- Red flags: theme only in the bible; ending unrelated to it; every character holds the same view.

### 2. `protagonist` — Chiều sâu nhân vật chính
- Wound (what happened before ep1), the lie they believe because of it, want (outer goal) vs need
  (inner change) in conflict.
- The arc moves through CHOICES under pressure, each costing something, not through things
  happening to them. Find the 3-4 choices that turn the arc; name the episode of each.
- The secret matters to the plot and to someone else when revealed.
- Red flags: passive protagonist; change announced in VO not shown; need never tested.

### 3. `supporting_cast` — Nhân vật phụ
- Each supporting character wants something of their own, and it collides with the main
  character's want at least once.
- Each has a function: mirror (what the hero could become), mentor, ally who tests, love,
  rival. Two characters with the same function -> merge or differentiate.
- At least one changes the protagonist's mind or path; at least one changes themselves.
- Red flags: helpers who exist only to deliver information; disappear without payoff.

### 4. `antagonist` — Phản diện / lực cản
- A reason that makes sense from inside (they think they are right); a want, not just "evil".
- Strong enough that the protagonist can really lose; acts, does not just wait.
- Often mirrors the protagonist (same wound, opposite choice).
- Red flags: faceless system with no human face; motive revealed only in exposition at the end.

### 5. `dialogue` — Lời thoại và ẩn ý
- Characters rarely say exactly what they feel; tension sits under the words (subtext).
- Each main voice is recognizable without the name tag (rhythm, vocabulary, what they avoid).
- Exposition hides inside conflict (an argument, a lie, a bargain), never a lecture.
- VO adds a layer (irony, a lie, what the image does not show), never repeats the image.
- Red flags: characters explaining the plot to each other; same voice for everyone; "As you know...".
- Clarity (Vietnamese: `../dialogue-polish/references/vi-dialogue.md`): a viewer understands every
  line on first hearing; riddle lines, noun-fragment chains and unexplained world terms score <= 2.
- Quote the 2-3 strongest and weakest lines.

### 6. `setup_payoff` — Gài và trả
- Every reveal has a clue the viewer could have caught before it (fair twist).
- Objects, lines and rules planted early come back changed (a prop, a promise, a world rule).
- No payoff without setup; no setup without payoff (except the one allowed sequel hook).
- Red flags: twist from nowhere; a planted detail dropped; coincidence solving a problem.
- List each important plant -> payoff with episode numbers; mark the missing ones.

### 7. `stakes` — Mức cược và leo thang
- What the protagonist loses is concrete and personal, and grows: self -> someone loved ->
  everything they believe.
- Each episode costs something (relationship, safety, trust, a lie exposed); no free wins.
- The final climax demands the protagonist's own choice using what the arc taught them.
- Red flags: stakes stated not felt; same level of danger every episode; rescue by others.

### 8. `emotion` — Cảm xúc và khoảnh khắc
- Each episode has one moment built to make the viewer feel (fear, shame, longing, relief) and
  the craft serves it (held shot, silence, a small gesture).
- Every scene turns: a value changes (trust -> suspicion, safe -> exposed). Scenes that do not
  turn are cut or merged.
- Some light against the dark (warmth, humour, tenderness) so the dark lands.
- Red flags: one flat emotional note for the whole season; scenes that only move information.

### 9. `originality` — Độc đáo, tránh sáo mòn
- What only this story has (a world detail, a relationship, a rule) and whether scenes use it.
- Clichés named, with a fresher turn: the amnesia twist, the "it was a dream", the evil twin, the
  villain monologue, the convenient overheard conversation.
- The style skill's reused devices (flash-forward, cliffhanger shape) are fine; copied content is not.

## Findings

Each finding is one concrete problem with one concrete fix:
- `where`: file + episode + scene (or bible field), so the user can open it.
- `evidence`: the quoted line or the exact field/beat. Never a paraphrase only.
- `problem`: why it weakens the story, in one or two sentences.
- `fix`: what to write instead, specific enough to apply ("in ep04 SC2, Linh refuses to hand over the
  key and lies about why; Vũ sees the lie and says nothing" — not "add more conflict").
- `severity`: `high` (hurts the whole season: theme, protagonist arc, unfair twist, antagonist with
  no motive), `medium` (an episode or a character), `low` (a line, a polish).

5-20 findings. Prefer fewer, bigger fixes over many small ones. Also list 3-5 `strengths` to keep.

Fixes must stay inside: the user's idea, the style skill's rules, the story contract, and canon
(produced episodes, `canon_vN.json`). Never propose a fix that breaks the contract.
