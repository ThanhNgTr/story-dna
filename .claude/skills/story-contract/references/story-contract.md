# Story contract: what every series must contain

Every skill that writes a bible, outline or episodes (`write-series-<slug>` Stage 2/3,
`/refine-skill`, `/continue-series`) follows this. It sits ABOVE the style skill: when a style
rule conflicts with it (e.g. "the finale ends mid-decision", "leave 2 questions unanswered"), the
contract wins and the style rule applies only where it does not break the contract. The style
decides HOW the story is told; the contract decides THAT it is a complete story.

Checked by `python3 .claude/skills/story-contract/_story_check.py <session> [--stage outline|episodes]`
-> 0 errors before showing the outline and before reporting episodes done.

## The 7 requirements

| # | Requirement | Where it lives | Checked |
|---|---|---|---|
| 1 | Complete story Start -> End, ending is `happy` or `bad` | bible `main_plot`, `ending`; last episode `ending` | resolution in last episode, central question answered |
| 2 | One main plot | bible `main_plot` | all fields set, beats in order and in the right % |
| 3 | Main character + supporting characters around them | bible `cast` | 1-2 `main`, >=2 `supporting`, every non-main has `relation_to_main` |
| 4 | Dialogue for the characters | bible `cast[].voice.sample_lines`; episode `dialogue` | >=2 sample lines; every episode has spoken lines by >=2 characters |
| 5 | Clear setting, and how it changes | bible `world.setting`, `world.locations`, `setting_timeline` | one timeline row per episode, setting changes >=3 times |
| 6 | Climaxes | bible `climaxes`; outline `climax` | 1 `midpoint`, 1 `final`, no stretch > 3 episodes without one |
| 7 | Secrets and mysteries, built correctly | bible `ledger_plan`, `cast[].secret` | central question, open -> clues -> answer, always >=1 open until the finale |

## Bible (`bible_vK.json`) — required fields

Added to the style skill's bible shape (keep its other fields).

```json
{
  "main_plot": {
    "central_question": "Will Vu get Ha out of the house alive?",
    "protagonist_goal": "...", "opposition": "who/what stands in the way",
    "stakes": "what is lost if the goal fails",
    "start_state": "protagonist + world at episode 1",
    "inciting_incident": {"episode": 1, "event": "..."},
    "midpoint":          {"episode": 5, "event": "a reveal that turns the goal around"},
    "lowest_point":      {"episode": 8, "event": "all seems lost"},
    "climax":            {"episode": 9, "event": "the final confrontation"},
    "resolution":        {"episode": 10, "event": "how it ends"},
    "end_state": "protagonist + world after the last scene"
  },
  "ending": {
    "type": "happy | bad", "episode": 10,
    "what_happens": "...", "protagonist_fate": "...",
    "central_question_answer": "the answer, said plainly",
    "final_image": "the last shot of the season"
  },
  "cast": [{"character_id": "char_02", "tier": "supporting", "relation_to_main": "roommate; covers for him, then betrays him in ep6",
            "want": "...", "need": "...", "secret": "...", "secret_reveal_ep": 6,
            "arc": {"start": "...", "end": "..."},
            "voice": {"style": "...", "sample_lines": ["...", "..."]}}],
  "world": {
    "setting": {"place": "...", "era": "...", "time_span": "10 days in November"},
    "locations": [{"id": "L1", "name": "...", "look": "...", "first_ep": 1, "role_in_story": "..."}]
  },
  "setting_timeline": [
    {"episode": 1, "locations": ["L1", "L2"], "time": "day 1, evening", "change": "arrives; phone taken"},
    {"episode": 2, "locations": ["L2"], "time": "day 1, night", "change": null}
  ],
  "climaxes": [
    {"episode": 3, "level": "minor", "event": "..."},
    {"episode": 5, "level": "midpoint", "event": "..."},
    {"episode": 9, "level": "final", "event": "..."}
  ],
  "ledger_plan": [
    {"id": "Q1", "question": "...", "tier": "central | major | minor",
     "open_ep": 1, "clue_eps": [2, 4], "answer_ep": 9, "answer": "the true answer, plainly"}
  ],
  "never_answered": []
}
```

Rules:
- `main_plot`: episodes in order inciting <= midpoint <= lowest_point <= climax <= resolution.
  Inciting in the first 20% of episodes, midpoint 35-65%, climax in the last 25%, resolution = last episode.
- `ending.type` is `happy` or `bad` (a mixed ending picks the side the protagonist lands on and
  says the cost in `what_happens`). `ending.episode` = last episode. The ending is seen on screen,
  not implied: the central question is answered inside the last episode.
- Cast: 1-2 `main`. >=2 `supporting`. Every `supporting`/`minor` has `relation_to_main` (how they
  stand to the main character and how that changes). Main + supporting have `want`, `need`,
  `arc.start`, `arc.end`, `voice.sample_lines` (>=2). Every main character has a `secret` with
  `secret_reveal_ep` <= last episode.
- Setting: `world.setting` says place, era and time span. >=2 locations, each with `first_ep`.
  `setting_timeline` has exactly one row per episode; its `locations` use location ids; `change`
  says what is new about place/time/state (new place, time jump, place damaged, power shifts),
  null if nothing; >=3 rows with a change across the season.
- Climaxes: exactly one `midpoint` and one `final`; `final` episode = `main_plot.climax.episode`.
  Add `minor` / `major` so that no run of more than 3 episodes has no climax.
- Mysteries: >=3 questions, exactly one `central` (= `main_plot.central_question` in substance).
  For each: `open_ep` < every clue < `answer_ep`; `answer` written out (the writer must know the
  truth from the start, so clues are fair). Central answered in the last 25%. Every question
  answered by the last episode, except at most 1 `minor` question in `never_answered` (a sequel
  hook). At the end of every episode except the last, at least one question is still open.

## Outline (`outline_vK.json`) — required per episode

```json
{"episode": 5, "act": 2, "main_plot_step": "what moves in the main plot this episode",
 "locations": ["L2", "L3"], "setting_change": "first night in the basement" ,
 "climax": "midpoint", "ledger": {"opened": ["Q4"], "clues": ["Q1"], "answered": ["Q3"]},
 "cliffhanger_type": "...", "characters": ["char_01", "char_03"]}
```

- Episodes 1..N, no gaps. `act` 1/2/3. `climax` null or a level, matching bible `climaxes`.
- `ledger` matches `ledger_plan` (opened at `open_ep`, answered at `answer_ep`).
- Episodes 1..N-1 end on a cliffhanger. The last episode has `"ending": "happy|bad"` (= bible) and
  `cliffhanger_type: "resolution"`; a one-line sequel hook after the resolution is allowed.
- The main character is in >=80% of episodes.

## Episodes (`epNN_vK.json`) — required

- Every scene: `location` and `time_of_day`.
- Spoken lines: >=4 lines per episode, by >=2 different characters, at least one not voiceover.
  Every speaker is in `characters`.
- `ledger` (opened / clues / answered) matches the outline row.
- Last episode: `"ending": {"type": "happy|bad", "central_question_answer": "..."}` matching the
  bible, and its scenes show the resolution (the protagonist's fate is on screen).
