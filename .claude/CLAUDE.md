# story-dna: Long Video → Story + Craft DNA → Series Skill → 10-20 Episode Screenplay

## PROJECT SCOPE

POC system for:
- Learning a reference story from ONE long video (many episodes edited into one continuous cut):
  plot, acts, reveals, main/supporting characters, storytelling, camera, sound, color, pacing
- Auto-generating a reusable series-writing skill from that DNA
- Turning a user's fragmented idea into a series in the same style: bible + season outline +
  10-20 episode screenplays (1-2 min each)
- Optional: breaking approved episodes into shot lists / production briefs

**Output**: Markdown for humans + JSON for agents
**Tech**: Claude Vision (built-in), ffmpeg (local), Python, WhisperX (local CPU, project `.venv/`)
**No external APIs** (no OpenRouter, Deepgram, Anthropic API key). Exception: reference images via the
Codex CLI on the user's ChatGPT login (built-in image_gen, no OpenAI API key)

## KEY CONCEPTS

- **Unit**: a ~2-min slice of the long video, cut on a real shot boundary, analyzed by one agent.
  Units exist only for analysis — the story is continuous; times are absolute in the source.
- **DNA** (`dna.json`): story (synopsis, acts, plot timeline, mystery ledger, subplots, arcs,
  episode break candidates) + characters (tier main/supporting/minor, want/need, voice, visual
  signature) + craft rules with evidence (character building, storytelling, pacing, camera,
  sound, color/lighting, world)
- **Story Template**: the reference plot abstracted into beat FUNCTIONS at % of the season, so a
  different idea can be told the same way. Content (names, places, events) is never copied.
- **Series session**: `data/series/<slug>/<session-id>/` — input, adaptation map, bible, outline,
  episodes, iterations, final/
- **Story contract** (`.claude/skills/story-contract/`): every series is a complete story — main plot,
  start -> happy/bad ending shown in the last episode, main + supporting cast tied to the main
  character, dialogue, setting + how it changes, climaxes, mysteries opened -> clued -> answered.
  Overrides style skills on conflict. `_story_check.py <session>` -> 0 errors; the web app runs it after
  outline / episodes / feedback / continue and lets Claude repair once (`/story-contract`).
- **Story editor** (`.claude/skills/story-editor/`): judges DEPTH after the contract — 9 dimensions
  (theme, protagonist, supporting cast, antagonist, dialogue/subtext, setup/payoff, stakes, emotion,
  originality) scored 1-5 with quoted evidence -> `editor/review_vN.json/.md`; `--apply` writes next
  versions for chosen findings (`editor/applied_vN.json`). Web: auto review after outline; page "Biên tập".
  Apply is planned by `_editor.py plan` (`editor/apply_plan.json`: source/target per file, episode packages),
  bible/outline + `editor/apply_notes.json` (per-episode decisions) first, then one subagent per package in
  parallel; md via `_editor.py render`.
- **Continuity** (`.claude/skills/story-continuity/`): logic ACROSS episodes. Outline rows carry `events` (E<ep>.<k>),
  `because` (earlier event ids) and `opens_from`; after Stage 3 Claude builds `continuity/state_vN.json` from the written
  episodes (facts, who knows what since when, uses, status, props, relations, clock, clues, setups, seams; every row quotes
  the episode verbatim). `_continuity.py check <session>` (`[C0]`..`[C8]`) -> 0 errors: nobody uses a fact before learning
  it, dead/gone/lost stay off screen, days never run back, each episode picks up its cliffhanger, planned clues and plants
  are on screen. Parallel writers get the cause chain; a seam pass (`_continuity.py seams`) fixes package boundaries;
  `_continuity.py impact --episodes N` lists dependent episodes for refine. `--review` = logic review (plot holes,
  coincidences, motives) -> `continuity/logic_vN.json`; `--apply` reuses `_editor.py plan --review`. Web: runs after
  story check (outline / episodes / feedback / editor apply / continue), card "Liên mạch giữa các tập" on the overview.
- **Dialogue clarity** (`.claude/skills/dialogue-polish/`): `references/vi-dialogue.md` overrides style
  word caps / "ambiguous line" rules (hide facts, not grammar; xưng hô per bible `address_matrix`;
  `glossary` = invented terms only; lines are speech, not description: no definitions, VO never retells the shot). `_dialogue_lint.py lint <session>` flags unclear lines; `/dialogue-polish` rewrites only
  dialogue (next versions + `dialogue/polish_vN.json`). Speech rate (one limit for every skill): vi-dialogue.md "Speech rate",
  Vietnamese <= 5.0 syllables/s, lint flag `too_fast`. Manual edits feed `data/dialogue_examples.json`
  (before/after) that writers imitate. Web: page "Lời thoại", button "Làm rõ thoại" per episode.
- **Screen action** (`.claude/skills/action-polish/`): `references/screen-action.md` = what people DO on screen.
  Every beat has `acting: [{character, does, face, holds}]` for each visible character (listener too: body +
  hands, face, what is in hand), every 2+ character scene a `blocking`; objects stay in hand until a beat puts
  them down. `_action_lint.py lint <session>` (`missing` / `prop_vanish` / `no_blocking` must be 0);
  `/action-polish` adds it to existing episodes (only action/acting/blocking change; `action/polish_vN.json`).
  Shotlist cuts and `performance` are built from it. Web: button "Bổ sung diễn xuất" per episode.
- **Minors on screen** (`.claude/skills/story-contract/references/minors-on-screen.md`): read BEFORE the outline and each episode. Child characters
  (registry/bible age < 18) get daylight / open-place scenes; no sleep, bed, touching, bare skin, secret phone at night,
  mouth habits, crying next to an adult (Google Flow refused ep04 as "harmful content involving minors"); no phone /
  screen in the child's shot and at most one (family) adult in it (ep06 refused 5x: child + phone strap + 2 men).
  Starts at the bible: a child's `tell` / signature props are hand or school things (`_story_check.py` errors).
  `_action_lint.py` flag `minor_risk` is strict; `script-to-shotlist` "Minors" is the second net (`package check`).
- **Feedback loop**: `rule` feedback patches the skill (new version), `story` feedback edits only
  this series. Live SKILL.md = latest; immutable `versions/SKILL_vN.md`.

## FOOTGUNS

1. **Frame budget**: keyframes per detected shot, `--max-frames` per unit (default 40). Fast-cut units have more shots than frames; pacing is still measured on all shots.
2. **Vision context**: never read frames in the main context. One `video-analyst` per unit; >12 units -> waves of 8-12.
3. **Merge size**: >8 units -> `story-merger mode=part` per ≤8 units, then `mode=final`.
4. **Transcription is slow on CPU**: ~0.4x realtime, in ~10-min resumable chunks; the web job starts each chunk's analysts while the next is transcribed.
5. **Speaker labels** need `HF_TOKEN` + pyannote terms; without them agents assign speakers from frames (`speaker_unsure`).
   CPU diarization ≈ 2.5x the audio length: `--diarize auto` only up to 60 min (`STORY_DNA_DIARIZE_MAX_MIN`); labels are per chunk.
6. **SKILL.md YAML must be valid**: parse the frontmatter after every write; bad YAML -> skill fails silently.
7. **Skill name conflicts**: check `.claude/skills/` before generating.
8. **Headless Claude cannot write inside `.claude/`** (protected even with allow rules). The web app stages skill edits in `data/skills-staging/write-series-<slug>/`, then validates + installs them into `.claude/skills/`.
9. **Scene detection limits**: fades/dissolves merge into one shot; flashes can add false cuts (`--scene-threshold`).
10. **Codex images are slow and plan-limited**: ~1-4 min each, one at a time (`STORY_DNA_CODEX_PARALLEL=1`);
    a full series is ~25 images ≈ 1h. A refusal or plan limit shows as `last_error` in `images.json`.
    Codex binary lives in the versioned VS Code extension dir; `config.find_codex_bin()` / `CODEX_BIN`.

## WORKFLOW

```
long video ─▶ [1] analyze-videos ─▶ dna.json + story.md ─▶ [2] skill-creator-from-dna ─▶ write-series-<slug>
                                                                                          │
user idea (fragments) ─▶ [3] write-series-<slug> ─▶ adaptation + bible + outline ◀─┐      │
                                                    (approve outline)              │      │
                                                  ─▶ episodes ep01..epN ◀── [4] refine-skill (loop)
                                                    (approve) ─▶ final/ ─▶ [5] script-to-shotlist ─▶ briefs (optional)
```

1. **Analyze** (`/analyze-videos --input <video>`) — rare
   - `_analyze.py`: shots on the whole video, units of ~120s on cut boundaries, keyframes per unit
   - `_transcribe.py` (`.venv`): WhisperX once per source, split per unit
   - `video-analyst` × N units (parallel) -> `story-merger` -> `dna.json`, `dna.md`, `story.md`
   - `film-analyst` (text only, no frames): audits the DNA + why it hooks -> `film_analysis.md/.json`
2. **Generate skill** (`/skill-creator-from-dna --dna <run>/dna.json --name <slug>`) — rare
   - `.claude/skills/write-series-<slug>/` (SKILL.md + references/reference-story.md + versions/)
   - More reference later: `--update <slug>`
3. **Write series** (`/write-series-<slug> --idea-file notes.md --episodes 12 --episode-sec 90`)
   - Stage 1 adaptation map -> Stage 2 bible + outline (stop for approval) -> Stage 3 episodes
4. **Refine** (`/refine-skill <slug> --feedback "..."`, `--approve outline`, `--approve`)
4b. **Asset registry** (`/series-assets --session <dir> [--feedback "..."]`) — bible-only at end of Stage 2,
   refreshed after Stage 3 / refine rounds / continue-series. Episodes follow
   `series-assets/references/episode-contract.md` (scene `loc_id`, `variant_id`, `cast` outfits, `props`);
   `_assets.py lint <session>` checks them; `/script-to-shotlist` builds prompts from the registry
   - Reference images: `python3 -m app.pipeline.assets plan|generate|status|approve|reject --session <dir>`
     (or web job `images`): Codex makes character sheets, outfits, location plates per variant, props into
     `assets/characters|locations|props/`; review state in `assets/images.json`; approved = refs for shotlists
   - Web: series page, group "Ngoại hình" (Nhân vật & trang phục / Bối cảnh / Đạo cụ / Lỗi liên tục): build/update
     the registry (job `assets`), generate images (job `images`), approve/reject each image
   - `_assets.py scan` -> Claude builds `assets/assets_vN.json/.md`: characters (face/hair/body, wardrobe
     per episode), locations (canonical sets, variants), props, scene map (every scene -> loc/outfits),
     continuity issues. `_assets.py validate` must pass (every scene + on-screen character mapped)
   - Text only; `assets/characters/<id>/`, `assets/locations/<id>/` reserved for reference images
5. **Continue after production** (`/continue-series --session <dir> --canon <run>/dna.json --style write-series-<slug> --produced <k> --direction follow|new-arc --new-episodes <m>`)
   - Produced videos are analyzed with step 1, then reconciled with the scripts as CANON (video wins) -> `canon_vN`, bible/outline next version; approve -> only missing episodes are written
   - Works for series produced outside the app (no scripts: bible built from the videos)
6. **Optional production** (focus: Google Flow; `STORY_DNA_VIDEO_TARGETS` default `flow`, `flow,higgsfield` also writes the
   10-15s clip prompts and enables the Higgsfield zip): `/script-to-shotlist final/epNN.md --targets flow` -> `final/shots/epNN/prompts.json` (`"unit": "clip"`: one
   prompt per 10-15s clip with <=5 timed cuts + timed lines; older per-shot files count as `prompts_stale`).
   `"prompt_format": 2`: each clip has opening/closing state, performance, `on_screen_text`, a fixed Rules guard
   block, and `veo_parts` on EVERY clip (Google Flow / Veo 3.1 version, split on cuts; `prompt_format: 3`: each part's
   `duration_sec` is a Flow length 4/6/8/10s = ~1.3x its script time (`flow_duration`: 4s -> 6s, 6s -> 8s), cuts and lines
   retimed over the whole length, the edit keeps it all (video ~1.3x the script); `prompt_format: 4` also: minors
   (registry `age` < 18) get no photo ref, no body / bare-skin / bed / touching words (`minor_problems`, Flow refused a 10-year-old)): character names
   (tested 2026-10-15: names pass; old `flow_labels` files get names swapped in, `package.named_prompt`), short looks + 1-2 face marks, <=3 images per part (every on-screen character first, then the location), no lettering (Flow refused
   an idol-like face as "famous people", incl. outfit images still built from that face; not the names, not the number of images); `package check` enforces it, older files only warn. Web "Tải gói video"
   (`app/pipeline/package.py`) zips per episode: shot prompts + approved refs + `subtitles.srt` + `edit_list.csv`
   (Higgsfield = 10-15s clips; "Tải gói Flow" `?target=flow` = one Google Flow generation per `veo_parts` entry:
   `parts/clip_NN_K.txt`, only that part's images (each ref swapped for the NEWEST approved image of its item:
   `package.current_ref`; never a minor's photo), `flow_queue.json/.csv` for batch tools, `trim_to_sec` because Flow makes 8s). Every Flow part also has `seedance_prompt` (Seedance 2.0, same span / length / images / lines; `app/pipeline/seedance.py build`,
   Claude writes only `veo_parts[].seedance` {scene, acting per cut, exclusions}); the Flow zip carries `seedance/clip_NN_K.txt`. Then `/direct-video`,
   `/cinematographer-brief`, `/sound-design-brief`, `/production-design-brief`

## PROJECT RESET (new reference video)

Keep: `analyze-videos`, `skill-creator-from-dna`, `refine-skill`, `continue-series`, `series-assets`, `story-contract`, `story-continuity`, `story-editor`, `dialogue-polish`, `action-polish`, `script-to-shotlist`, the 4 brief
skills, agents `video-analyst` + `story-merger` + `film-analyst`. Remove: generated `.claude/skills/write-series-*`,
`data/analyses/*`, `data/series/*`, `data/skills-generated/*`.

## WEB UI

- Old UI: Jinja pages (`app/templates/`). New UI: React + Vite + Tailwind + shadcn (Base UI) in `web/`, built into
  `app/static/ui/` (committed; users need Python only), served at `/ui`, JSON API in `app/api.py`.
- Users run the app locally (handoff). Priority of the migration: screenplay reading/review first.
- After changing `web/`: `cd web && npm run build`, commit `app/static/ui/`. shadcn here uses Base UI: `render={<X />}`, not `asChild`.
- Manual episode edits and comments never call Claude; they write the next `epNN_vK` / `comments.json`.
- `final/` can go stale: any draft (bible, outline, epNN, `assets/assets_vN`) newer AND different from its
  `final/` copy -> `final_stale`, stage "Có sửa sau khi chốt"; "Chốt lại" (`series.refinalize`, no Claude, fresh
  mtimes) copies it and rebuilds `final/series.md`; prompts built from an older `final/epNN.json` or
  `final/assets.json` are `prompts_stale`. Shotlist API refuses stale episodes / stale assets.
- Tests: `.venv/bin/python -m pytest -q` (`tests/`, no Claude/network; `requirements-dev.txt`). Run after touching
  the check scripts, `app/pipeline/series.py`, `package.py` or the project API payload.

## OUTPUT STYLE

- **Caveman ultra**: minimal jargon, clear structure
- No emoji
- JSON/Markdown over prose for data
- Timestamps ISO 8601 (2025-10-01T14:30:00Z)
- Screenplay language = language of the user's idea unless told otherwise

## CRITICAL RULES

1. **Reproducibility**: every analysis run in `data/analyses/<run-id>/` (manifest, shots, frames, transcripts, dna)
2. **Evidence**: DNA rules cite time / scene / quoted line. Never invent; mark inferences.
3. **Versioning**: never overwrite `versions/SKILL_vN.md` or `*_vK` files; metadata `write-series-<slug>_vN.json`
4. **History**: `data/series/<slug>/<session-id>/iterations.json` logs every feedback round
   (`{session, slug, rounds: [...]}`; old sessions are a plain list: app code reads/writes ONLY via
   `app/pipeline/iterations.py`, skills append to `rounds` and never replace earlier rounds)
5. **Error recovery**: no audio -> visual-only dialogue (`inferred`); detection fails -> uniform frames; agent fails -> re-run that unit only

## ARCHITECTURE PATTERNS

- **Skills as modules**: `.claude/skills/<name>/`; agents in `.claude/agents/`
- **Data layer**: all outputs in `data/` (gitignored)
- **Absolute time**: unit/shot/transcript times are seconds in the source video
- **JSON as source of truth**, Markdown alongside for review

## GIT WORKFLOW

- Feature branches -> PR -> main. Messages: `feat(analyze): ...`, `fix(skill): ...`, `docs: ...`
- Keep `.claude/` in VCS (skills are code)
- `.gitignore`: `data/`, videos, `.venv/`
