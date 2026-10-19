# Continuity: every event follows from the ones before it

The story contract (`../story-contract/`) checks that the parts EXIST. This file makes the parts
FIT across episodes: why each episode happens (cause chain), who knows what and since when, who
is where and in what state, what is in whose hands, what day it is, how each episode picks up the
last cliffhanger, and that every clue and plant is on screen.

Checked by `python3 .claude/skills/story-continuity/_continuity.py check <session> [--stage outline|episodes]`
-> 0 errors (writes `<session>/continuity_check.json`). Error codes:

| Code | What | Where it lives |
|---|---|---|
| C0 | State ledger exists and covers every written episode | `continuity/state_vN.json` |
| C1 | Cause chain: each episode happens because of an earlier event; each opening picks up the last cliffhanger | outline `events`, `because`, `opens_from` |
| C2 | Knowledge: nobody acts on a fact before they learn it | ledger `facts`, `knowledge`, `uses` |
| C3 | Character status: the dead stay dead, the gone come back on screen only after a `back` row | ledger `status` |
| C4 | Props: a destroyed or lost object does not reappear (until found) | ledger `props` |
| C5 | Clock: days never run backwards; the clock agrees with bible `setting_timeline` | ledger `clock` |
| C6 | Seams: every episode opening is tied to the previous cliffhanger, and a cut-away cliffhanger is resolved | ledger `seams` |
| C7 | Clues and plants: every planned clue is on screen; every plant is paid off | ledger `clues`, `setups` |
| C8 | Relations: a relationship changes state only with a cause on screen | ledger `relations` |

Every ledger row that points at an episode (ep >= 1) carries a `quote`: a short verbatim piece
(3-15 words) of a dialogue line, an `action` / `acting` text or the `cliffhanger` of that episode
(and that scene, when `scene` is set). The checker finds it in the file; a quote it cannot find
is an error. Quotes from dialogue survive action rewrites best; prefer them.

## Outline (`outline_vK.json`): cause chain, per episode

```json
{"episode": 5,
 "events": [{"id": "E5.1", "text": "Linh lấy chìa khóa kho trong túi áo Vũ"},
            {"id": "E5.2", "text": "Vũ thấy chìa khóa mất, nghi Linh"}],
 "because": ["E4.2", "E3.1"],
 "opens_from": "ep04 kết ở cảnh Vũ nghe tiếng gõ cửa: ep05 mở bằng cánh cửa bật ra"}
```

- `events`: 1-4 per episode, ids `E<episode>.<k>`, each a concrete thing that HAPPENS (a choice,
  a discovery, a loss), not a mood.
- `because` (episodes 2..N): >= 1 event id from an EARLIER episode that causes this episode's
  first event. A cause is something a character did or found, not "time passes". Coincidence is not
  a cause: if two strangers meet by chance, the cause is why each one was there.
- `opens_from` (episodes 2..N): how the first seconds continue the previous episode's cliffhanger
  (the same moment, or a named time jump that is resolved inside this episode).
- Warning when no later episode lists an episode's events in `because`: a dead-end episode (its
  events change nothing). Fine for at most one breather episode.

## State ledger (`continuity/state_vN.json`)

Built from the WRITTEN episodes (not the plan) after Stage 3 and after every round that rewrites
episodes. Never overwrite a version: write `state_vN+1.json` (`_continuity.py next <session> state`)
and render the md with `_continuity.py render <state.json>`.

```json
{
  "version": 2, "created_at": "2026-10-16T09:00:00Z", "language": "vi",
  "built_from": {"bible": "bible_v4.json", "outline": "outline_v3.json",
                 "episodes": {"1": "episodes/ep01_v2.json", "2": "final/ep02.json"}},
  "facts": [
    {"id": "F1", "text": "Phong từng là kỹ sư kết cấu", "ep": 0, "kind": "backstory"},
    {"id": "F2", "text": "Khóa giàn giáo bị cưa trước khi đổ", "ep": 1, "scene": "SC2", "kind": "event",
     "quote": "vết cưa còn mới"}
  ],
  "knowledge": [
    {"character": "char_01", "fact": "F1", "ep": 0, "how": "chính anh"},
    {"character": "char_02", "fact": "F1", "ep": 9, "scene": "SC2", "how": "đọc hồ sơ trong cặp anh",
     "quote": "Kỹ sư kết cấu, hạng nhất"}
  ],
  "uses": [
    {"character": "char_02", "fact": "F1", "ep": 10, "scene": "SC1", "quote": "anh là kỹ sư mà"}
  ],
  "status": [
    {"character": "char_05", "ep": 8, "scene": "SC3", "status": "gone", "note": "bị công an đưa đi",
     "quote": "Mời anh về đồn"}
  ],
  "props": [
    {"prop": "prop_01", "ep": 1, "scene": "SC2", "holder": "char_01", "status": "with", "quote": "nhét chiếc khóa gãy vào túi"},
    {"prop": "prop_01", "ep": 6, "scene": "SC1", "holder": null, "status": "lost", "quote": "túi áo trống trơn"}
  ],
  "relations": [
    {"pair": ["char_01", "char_02"], "ep": 1, "scene": "SC3", "state": "người lạ, chị ơn", "quote": "..."},
    {"pair": ["char_01", "char_02"], "ep": 3, "scene": "SC2", "state": "ăn trưa cùng nhau",
     "cause": "anh chia nửa hộp cơm, cô đổi xưng em", "quote": "Tay nhiễm trùng thì gọi em"}
  ],
  "clock": [{"ep": 1, "day": 1, "time": "sáng"}, {"ep": 2, "day": 2, "time": "chiều -> tối"}],
  "clues": [{"question": "Q1", "ep": 2, "scene": "SC3", "clue": "vết cưa trên khóa", "quote": "vết cưa còn mới"}],
  "setups": [
    {"id": "S1", "plant": "Phong gõ bút lên góc giàn giáo", "ep": 3, "scene": "SC4", "quote": "phải chịu tải gấp đôi",
     "payoff": "anh chỉ ra đúng chỗ khóa bị cưa trước hội đồng", "payoff_ep": 11, "payoff_scene": "SC2",
     "payoff_quote": "chỗ này chịu tải gấp đôi"}
  ],
  "seams": [
    {"ep": 2, "cliffhanger_quote": "Anh ấy chỉ mang áo cho con", "opening_quote": "Anh ấy chỉ mang áo cho con",
     "link": "continues"},
    {"ep": 5, "cliffhanger_quote": "Ai cho cô vào đây?", "opening_quote": "Ba ngày sau",
     "link": "time_jump", "resolved_ep": 5, "note": "câu hỏi được trả lời ở SC2 bằng hồi tưởng"}
  ]
}
```

Rules per list:
- `facts`: what is TRUE in the story and matters to the plot (secrets, events, identities, world
  rules). `ep: 0` = true before episode 1 (backstory, no quote needed). Every bible `secret` and
  every `ledger_plan` answer is a fact.
- `knowledge`: one row per character per fact they know, with the episode/scene where they learn
  it. The owner of a secret knows it from `ep: 0`. The viewer is not a character.
- `uses`: every moment a character SHOWS they know a fact (says it, acts on it, hides it on purpose).
  The checker errors when the use comes before the learning (same episode: scene order counts).
- `status`: `dead`, `gone` (left, locked up, abroad), `back` (returns after `gone`), `injured`,
  `healed`. A `dead` or `gone` character on screen later is an error unless the scene is a
  flashback (scene `"flashback": true`, or "hồi tưởng" / "flashback" in its `time_of_day`).
- `props`: story props (registry ids `prop_NN` when `assets/` exists). `status`: `with` (holder
  has it), `lost`, `destroyed`. After `destroyed` the prop is never in a later scene `props`;
  after `lost` only once a later `with` row says who found it.
- `relations`: pairs from the bible `relationships` / ladders; one row where each pair starts and one
  per change. A row whose `state` differs from the pair's previous row needs `cause`.
- `clock`: one row per episode: story day (int, day 1 = episode 1) and time. Days never go back;
  an episode told as flashback says `"flashback": true`. When the bible `setting_timeline` row
  names a day ("ngày 4", "day 4"), the clock must say the same day.
- `clues`: one row per clue the viewer sees, for every `ledger_plan` question and each of its
  `clue_eps` (written episodes only).
- `setups`: plants (an object, a line, a skill, a promise) that come back. `payoff_ep` null is an
  error once every episode is written, except one `"sequel_hook": true`.
- `seams`: one row per episode 2..N whose previous episode is written. `cliffhanger_quote` comes from
  the previous episode's last scene (or its `cliffhanger`), `opening_quote` from this episode's first
  scene. `link`: `continues` (same moment), `time_jump` or `cutaway` (then `resolved_ep` = the episode
  where the cliffhanger's question is answered on screen, normally this one).

## Writing against the ledger

Anyone who writes or rewrites an episode after other episodes exist (a second writing wave,
`/refine-skill`, `/story-editor --apply`, `/continue-series`) reads the latest
`continuity/state_vN.md` first: what each character knows at the end of the previous episode,
where they are, what they hold, which day it is, which plants still wait for a payoff.

Before rewriting an episode, list what depends on it:
`python3 .claude/skills/story-continuity/_continuity.py impact <session> --episodes 3` (or
`--facts F2,F7`). It names later episodes that use a fact learned or established there, carry a
plant or a clue from it, list its events in `because`, or share a seam with it. Re-check those
episodes; rewrite them when the change breaks them.
