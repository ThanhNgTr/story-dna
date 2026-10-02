# story-dna

Long reference video → story + craft DNA → series-writing skill → 10-20 episode screenplay (POC)

Learn how a reference story is built (plot, characters, storytelling, camera, sound, color,
pacing) from one long video, then turn a rough, fragmented idea into a series told the same way:
series bible + season outline + episode screenplays of 1-2 minutes each.

## Quick Start

0. **One-time setup** (audio transcription, local CPU, no sudo):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path
   ~/.local/bin/uv venv .venv --python 3.12
   ~/.local/bin/uv pip install --python .venv/bin/python whisperx \
     --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match
   ```

1. **Learn the reference video** (one long video; many episodes edited into one cut):
   ```
   /analyze-videos --input data/input/reference.mp4
   ```
   Produces `data/analyses/<run-id>/dna.json`, `dna.md`, `story.md`

2. **Generate the series skill**:
   ```
   /skill-creator-from-dna --dna data/analyses/<run-id>/dna.json --name <slug>
   ```
   Creates `.claude/skills/write-series-<slug>/`

3. **Write your series** from a rough idea (notes, scattered scenes, any language):
   ```
   /write-series-<slug> --idea-file my_notes.md --episodes 12 --episode-sec 90
   ```
   Adaptation map + bible + season outline -> stops for your review

4. **Review loop**:
   ```
   /refine-skill <slug> --feedback "move the big reveal earlier; less voiceover"
   /refine-skill <slug> --approve outline     # then episodes get written
   /refine-skill <slug> --feedback "ep04: ending too soft"
   /refine-skill <slug> --approve             # final/ (bible, outline, ep01..epN)
   ```

5. **Optional production**: `/script-to-shotlist data/series/<slug>/<session-id>/final/ep01.md`,
   then the briefs in [PRODUCTION_PIPELINE.md](PRODUCTION_PIPELINE.md).

## Web App (local POC)

The same pipeline with a browser UI, for one user or an internal team, running on your own machine.

```bash
./run_app.sh            # http://127.0.0.1:8765
```

| Screen | What you do |
|---|---|
| Dashboard | Environment check (ffmpeg, WhisperX, Claude CLI, HF_TOKEN), analyses, skills, series, recent jobs |
| 1 Analyze video | Pick the long video with the folder browser, set dialogue language, start. Live progress per step and per unit |
| Analysis result | Read `story.md` / `dna.md`, unit status, resume an unfinished run, generate the `write-series-<slug>` skill |
| 2 Write series | Pick a skill, paste or upload your idea, episodes (10-20) and length (60-120 s) -> adaptation + bible + outline |
| Continue from produced videos | On a series page (or "continue a series produced elsewhere" on the dashboard): pick the episodes already made as videos (or an existing analysis), how many are produced, how many new episodes, and the direction (follow the old outline adapted to what is on screen, or a new arc). Three ways to check the produced episodes, cheapest first: **skip** (videos follow the scripts; add notes on changes, ~1 Claude call), **quick** (local WhisperX transcript + local line-by-line script diff via `.claude/skills/continue-series/_script_diff.py`; Claude reads only the diff, no frames), **full** (frames analyzed like a reference video, ~$0.45 per video minute). Claude then writes a canon report (script vs screen, video wins), updates the bible and writes the outline for the next episodes; approve -> only the missing episodes are written. Optionally also updates the style skill from the real videos |
| Hide / restore | Every analysis, skill, series and job has a **Hide** button; hidden items are listed under "Hidden" at the bottom of the dashboard with **Restore**. Nothing is deleted: analyses/series/jobs are only flagged (`data/ui_state.json`); a hidden skill moves to `data/archive/skills/` so Claude stops loading it until restored |
| Series session | Read every document and episode, send feedback (per episode / outline / all), approve outline -> episodes, approve season, download the screenplay `.md` |

How it works:
- Backend: FastAPI (`app/`), background jobs in `data/jobs/<id>.json` + `.log`; a failed or interrupted job can be resumed and skips finished steps and units.
- Claude: the app runs the Claude Code CLI headless (`claude -p`) with the account logged in on this machine, in the project dir, so the project skills and agents are used as-is (`app/claude_runner.py` is the only place that calls Claude). The CLI is found via `CLAUDE_BIN`, `PATH`, or the VS Code extension.
- Analysis is orchestrated by the backend (`app/pipeline/analyze.py`): scripts, then up to `STORY_DNA_PARALLEL` (default 4) `video-analyst` runs at once, then `story-merger`. Also runnable without the UI: `.venv/bin/python -m app.pipeline.analyze --run data/analyses/<run-id>`.
- The folder browser only shows paths under `STORY_DNA_BROWSE_ROOTS` (default: your home dir). The server binds to 127.0.0.1 only.
- The cost shown per job is what the Claude CLI reports; on a subscription it reflects usage, not a bill.

## User Guide

Run every `/...` command inside Claude Code (terminal or VS Code), opened at the project folder.
Run `bash` commands in a normal terminal. Prefer a UI? See [Web App](#web-app-local-poc).

### 1. Setup (one time)

| Step | Command | Check |
|---|---|---|
| ffmpeg | `sudo apt install ffmpeg` (Ubuntu) / `brew install ffmpeg` (macOS) | `ffmpeg -version` |
| Python 3.10+ | preinstalled on Linux/macOS | `python3 --version` |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh -s -- --no-modify-path` | `~/.local/bin/uv --version` |
| WhisperX (~2.5 GB) | the `uv venv` + `uv pip install` commands in Quick Start step 0 | `.venv/bin/python -c "import whisperx"` |

Optional, **speaker labels** (know which line belongs to whom, more accurate):
1. Create an account and a Read token at https://huggingface.co/settings/tokens
2. Open https://huggingface.co/pyannote/speaker-diarization-community-1 and accept the terms
3. `cp .env.example .env`, put the token in `HF_TOKEN=` (`.env` is gitignored, loaded by `./run_app.sh`), `chmod 600 .env`, restart the app. In a plain terminal session: `export HF_TOKEN=...` instead

Without a token everything still runs; the AI guesses speakers from the frames (marked `speaker_unsure`).

### 2. Prepare input

- **Reference video**: copy it into `data/input/` (mp4, mov, mkv, avi, webm). One long video made of
  several episodes edited together is the intended case; a folder of videos also works.
- **Your idea**: any text/markdown file, fragments are fine, in any language, e.g. `data/input/idea.md`:
  ```markdown
  Setting: a fishing village on the central coast, storm season.
  Characters: Mai (17, the lighthouse keeper's daughter), Tuan (best friend), Mr. Bay (village chief).
  Scene I want: Mai finds a letter from her mother in a sealed room.
  Scene I want: the whole village goes quiet when someone mentions the storm night 10 years ago.
  Ending: not decided, want a twist.
  ```

### 3. Run step by step

**Step 1 — Learn the reference video** (rare, slowest step)
```
/analyze-videos --input data/input/reference.mp4
```
- Non-English dialogue (e.g. Vietnamese): say so in the command ("dialogue is Vietnamese"), the AI then
  transcribes with `--language vi`. Whisper detects the language from the first 30s only and can be
  wrong if the video opens with music.
- Time (CPU): shot detection ~1 min; transcript ~0.65x video length (30 min video ≈ 20 min);
  AI analysis ~3 min per 2-min unit, units run in parallel.
- Check in `data/analyses/<run-id>/`:
  - `story.md`: the plot retold in order — is it the right story?
  - `dna.md`: main/supporting characters, acts, mysteries, camera/sound/color rules
  - merge notes in `dna.md`: what the AI was unsure about (e.g. whether two characters are one person)
  - `manifest.json` -> `audio.language` must match the video's language

**Step 2 — Generate the series skill** (once per reference video)
```
/skill-creator-from-dna --dna data/analyses/<run-id>/dna.json --name <slug>
```
- `<slug>`: lowercase, hyphens, e.g. `storm-village`. This creates the new command `/write-series-storm-village`.
- Add another reference video to an existing skill: `--update <slug>`.

**Step 3 — Write the series from your idea**
```
/write-series-<slug> --idea-file data/input/idea.md --episodes 12 --episode-sec 90
```

| Option | Default | Meaning |
|---|---|---|
| `--idea` / `--idea-file` | required | Idea as text, or a file path |
| `--episodes` | 12 | Number of episodes, 10–20 |
| `--episode-sec` | 90 | Episode length, 60–120 seconds |
| `--characters` | - | Names + roles, e.g. `"Mai (lead), Tuan (friend)"` |
| `--sample` | - | Existing draft; the AI keeps its content and applies the style |
| `--auto` | off | Write all episodes without stopping for outline review |

The AI stops after writing **adaptation.md** (how your idea maps onto the reference story structure),
the **bible** (world, characters) and the **outline** (one summary per episode), in
`data/series/<slug>/<session-id>/`.

**Step 4 — Feedback and approval** (repeat until happy)
```
/refine-skill <slug> --feedback "move the brother twist to episode 7; less voiceover"
/refine-skill <slug> --approve outline      # approve outline -> the AI writes the episodes
/refine-skill <slug> --feedback "episode 4 ending is weak, add a scene where Mr. Bay lies"
/refine-skill <slug> --approve              # finalize the season
```
- Feedback in any language. The AI splits it: **general** feedback ("every cliffhanger feels the same")
  also patches the skill for future runs; **story-specific** feedback ("rename Tuan") changes only this series.
- Every change creates a new version (`outline_v2`, `ep04_v2`...); old versions are kept.

**Step 5 — Get the result**
- Final screenplays: `data/series/<slug>/<session-id>/final/` — `bible.md`, `outline.md`, `ep01.md` ... `epNN.md`
  (plus `.json` for other tools), `series.md` = index.
- Optional video production: `/script-to-shotlist .../final/ep01.md`, then the briefs in [PRODUCTION_PIPELINE.md](PRODUCTION_PIPELINE.md).

### 4. Switch to a new reference video

Delete the generated skill `.claude/skills/write-series-*` and the data in `data/analyses/*`, `data/series/*`,
`data/skills-generated/*` (or ask Claude to "reset the project per CLAUDE.md"), then start again at step 1.

### 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `ffmpeg: command not found` | Install ffmpeg (section 1) |
| `.venv/bin/python: No such file` | WhisperX not installed; still runs, but dialogue is only guessed from frames |
| Transcript in the wrong language / gibberish | Re-run the transcript with `--language <code>` (e.g. `vi`) |
| Odd repeated lines ("Thank you", "Please subscribe...") | Whisper hallucinates over music; the analysts filter them, see `dropped_segments` |
| Too many / too few shots | Re-analyze with `--scene-threshold 0.2` (fewer) or `0.08` (more, dark footage) |
| A character split in two / two merged into one | Check the merge notes, fix through feedback in step 4 |
| `/write-series-...` does not appear | Check `.claude/skills/write-series-<slug>/SKILL.md` exists, restart the Claude Code session |
| Diarization off although a token is set | Model terms not accepted on Hugging Face, or `HF_TOKEN` not exported in the same terminal |

## Directory Structure

```
.
├── .claude/
│   ├── CLAUDE.md                       # project guide + footguns
│   ├── agents/
│   │   ├── video-analyst.md            # one per ~2-min unit: scenes, characters, dialogue, plot events, craft
│   │   └── story-merger.md             # stitches units into one plot + craft DNA
│   └── skills/
│       ├── analyze-videos/             # _analyze.py (shots, units, frames), _transcribe.py (WhisperX)
│       ├── skill-creator-from-dna/     # DNA -> write-series-<slug>
│       ├── refine-skill/               # feedback loop + approve
│       ├── script-to-shotlist/         # optional: episode -> 1-5s shots + video prompts
│       ├── direct-video/               # optional production briefs
│       ├── cinematographer-brief/
│       ├── sound-design-brief/
│       └── production-design-brief/
├── data/                               # gitignored
│   ├── analyses/<run-id>/              # manifest, shots, frames, transcripts, dna/, dna.json, story.md
│   ├── series/<slug>/<session-id>/     # input, adaptation, bible, outline, episodes, final/
│   └── skills-generated/               # skill metadata per version
└── .venv/                              # WhisperX (gitignored)
```

## Prerequisites

- `ffmpeg` + `ffprobe`
- Python 3.10+ (frame extraction, no packages)
- `.venv` with WhisperX for dialogue (optional but strongly recommended)
- Optional `HF_TOKEN` (+ accepted pyannote terms) for speaker labels

## Notes

- No external APIs: Claude reads frames natively, audio is transcribed locally
- Every DNA rule cites evidence (time, scene, quoted line)
- Skills and series files are versioned; nothing is overwritten
- New reference video: reset per CLAUDE.md "PROJECT RESET"
