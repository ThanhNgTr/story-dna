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
- **Feedback loop**: `rule` feedback patches the skill (new version), `story` feedback edits only
  this series. Live SKILL.md = latest; immutable `versions/SKILL_vN.md`.

## FOOTGUNS

1. **Frame budget**: keyframes per detected shot, `--max-frames` per unit (default 40). Fast-cut units have more shots than frames; pacing is still measured on all shots.
2. **Vision context**: never read frames in the main context. One `video-analyst` per unit; >12 units -> waves of 8-12.
3. **Merge size**: >8 units -> `story-merger mode=part` per ≤8 units, then `mode=final`.
4. **Transcription is slow on CPU**: ~0.65x realtime (30 min video ≈ 20 min). Run it in the background.
5. **Speaker labels** need `HF_TOKEN` + pyannote terms; without them agents assign speakers from frames (`speaker_unsure`).
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
6. **Optional production**: `/script-to-shotlist final/epNN.md`, then `/direct-video`,
   `/cinematographer-brief`, `/sound-design-brief`, `/production-design-brief`

## PROJECT RESET (new reference video)

Keep: `analyze-videos`, `skill-creator-from-dna`, `refine-skill`, `continue-series`, `series-assets`, `script-to-shotlist`, the 4 brief
skills, agents `video-analyst` + `story-merger` + `film-analyst`. Remove: generated `.claude/skills/write-series-*`,
`data/analyses/*`, `data/series/*`, `data/skills-generated/*`.

## WEB UI

- Old UI: Jinja pages (`app/templates/`). New UI: React + Vite + Tailwind + shadcn (Base UI) in `web/`, built into
  `app/static/ui/` (committed; users need Python only), served at `/ui`, JSON API in `app/api.py`.
- Users run the app locally (handoff). Priority of the migration: screenplay reading/review first.
- After changing `web/`: `cd web && npm run build`, commit `app/static/ui/`. shadcn here uses Base UI: `render={<X />}`, not `asChild`.
- Manual episode edits and comments never call Claude; they write the next `epNN_vK` / `comments.json`.

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
