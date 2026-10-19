# story-dna

Learn how a story is told from one long reference video, then write your own series the same way.

```
reference video ─▶ story + craft DNA ─▶ writing style (skill) ─▶ your idea ─▶ bible + outline ─▶ 10-20 episode screenplays
                                                                                            └─▶ characters, costumes, locations + reference images
```

What you get:

- **Analysis of a reference video** (many episodes edited into one cut, or a folder of episodes): plot, acts,
  reveals, main and supporting characters, storytelling, pacing, camera, sound, color. Every rule cites the
  time, scene or line it comes from. Vietnamese summary for reading.
- **A reusable writing style** (`write-series-<slug>`): the reference plot abstracted into beat functions, plus
  craft rules. Content (names, places, events) is never copied.
- **Your series**: a fragmented idea in any language becomes an adaptation map, a series bible, a season outline
  and 10-20 vertical micro-drama episodes of 60-120 s, written in the idea's language.
- **Quality checks**: a **story contract** (complete plot to a happy or bad ending, main + supporting cast,
  dialogue, setting changes, climaxes, mysteries opened -> clued -> answered) checked automatically; a **script
  editor** that scores depth (theme, characters, antagonist, subtext, setup/payoff, stakes, emotion,
  originality) with quoted evidence and fixes; a **dialogue pass** that makes Vietnamese lines clear and
  natural and learns from your own hand edits.
- **Review loop**: comment on a beat, edit in place, compare versions, approve; general feedback improves the
  style for the next series.
- **Looks registry**: fixed faces, costumes per episode, locations with day/night variants, props, and the
  continuity errors between episodes; reference images generated with Codex.
- **Production helpers**: shot lists, one multi-shot video prompt per 10-15 s clip (faces and dialogue stay consistent), and a per-episode **video package**
  (zip: prompt per shot, approved reference images, subtitles `.srt`, edit list `.csv`) for Higgsfield or any
  video tool; director / camera / sound / design briefs.

Everything runs on your own machine. The browser app is the main way to use it; every step also works as a
Claude Code command.

## Contents

- [Requirements](#requirements)
- [Install](#install)
- [Run the app](#run-the-app)
- [Using the app, step by step](#using-the-app-step-by-step)
- [Command line (Claude Code)](#command-line-claude-code)
- [Time and cost](#time-and-cost)
- [Configuration](#configuration)
- [Where things are stored](#where-things-are-stored)
- [Development](#development)
- [Switch to a new reference video](#switch-to-a-new-reference-video)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)

## Requirements

| What | Needed for | Check |
|---|---|---|
| **Claude Code CLI, logged in** | everything (analysis, styles, writing) | `claude --version`, then `claude` once to log in |
| `ffmpeg` + `ffprobe` | reading videos | `ffmpeg -version` |
| Python 3.10+ and [uv](https://docs.astral.sh/uv/) | the app and transcription | `python3 --version`, `~/.local/bin/uv --version` |
| WhisperX in `.venv/` (~2.5 GB) | real dialogue transcripts (recommended; without it dialogue is guessed from frames) | `.venv/bin/python -c "import whisperx"` |
| Hugging Face token (optional) | speaker labels in transcripts | see [Install](#install) step 4 |
| Codex CLI, logged in with ChatGPT (optional) | reference images of characters / locations / props | ChatGPT/Codex extension in VS Code, or `codex` on PATH |
| Node 20+ (optional) | only to change the web UI | `node --version` |

Linux, macOS, and Windows through WSL2. The Claude CLI is found via `CLAUDE_BIN`, `PATH` or the VS Code extension; Codex via
`CODEX_BIN`, `PATH` or the VS Code ChatGPT extension.

## Install

### One command (recommended)

| System | Command |
|---|---|
| Ubuntu / Debian / Fedora / Arch, macOS (needs [Homebrew](https://brew.sh)) | `./install.sh` |
| Windows 10/11 | PowerShell in the story-dna folder: `powershell -ExecutionPolicy Bypass -File .\install.ps1` (sets up WSL2 + Ubuntu, copies the project to `~/story-dna` inside it, runs `install.sh` there) |

`install.sh` installs what is missing and skips what is there (safe to run again): ffmpeg / git / curl (asks
before `sudo`), uv, Python 3.12 in `.venv`, the web app packages, WhisperX (CPU), Claude Code (official
installer), Codex CLI (optional, via Homebrew or npm), `.env`. Then log in once: `claude` (and `codex login`
for images), and start with `./run_app.sh`.

Options: `--yes` (no questions), `--no-whisperx` (skip the 2.5 GB download; dialogue is then guessed from
frames), `--no-codex`, `--check` (only report what is installed and what is missing).

Notes: Fedora gets `ffmpeg-free` from its own repos (common H.264/AAC files work; RPM Fusion's `ffmpeg` is the
full build). Intel Macs: no current PyTorch, so WhisperX is skipped. WSL2: open
http://127.0.0.1:8765/ui/ in the Windows browser; keep videos inside the Linux home (`~/story-dna/data/input`).

### Manual

1. **ffmpeg**: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS).
2. **uv + Python environment + WhisperX** (local CPU, no sudo):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path
   ~/.local/bin/uv venv .venv --python 3.12
   ~/.local/bin/uv pip install --python .venv/bin/python whisperx \
     --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match
   ```
   The web app's own packages (`app/requirements.txt`) are installed into the same `.venv` by `./run_app.sh`
   on first start.
3. **Claude Code**: install it and log in once (`claude`). The app uses that account; no API key.
4. **Optional, speaker labels**:
   1. Create a Read token at https://huggingface.co/settings/tokens
   2. Accept the terms at https://huggingface.co/pyannote/speaker-diarization-community-1
   3. `cp .env.example .env`, set `HF_TOKEN=`, `chmod 600 .env`. Without it everything runs; speakers are
      guessed from the frames and marked `speaker_unsure`.
5. **Optional, reference images**: install the ChatGPT/Codex extension in VS Code (or the Codex CLI) and log in
   with ChatGPT. Images use your ChatGPT plan, no OpenAI API key.

## Run the app

```bash
./run_app.sh
```

Open **http://127.0.0.1:8765/ui/**. The server listens on this machine only. Jobs run in the background:
you can close the tab, and you get a notification when a job finishes.

**Hướng dẫn** in the top bar explains the whole workflow in Vietnamese. The older pages are still at
http://127.0.0.1:8765/ (same data); every flow now exists in the new UI. Production briefs are commands
(see [Command line](#command-line-claude-code)).

## Using the app, step by step

### 1. Learn a reference video (rare, slowest step)

**Học video mẫu** in the top bar.

- Pick a video, or a whole folder of episodes, on this machine (under `data/input/` by default), or drag & drop
  files to upload them. The page lists the episodes in order with durations and an estimated time.
- Choose the dialogue language (more accurate than auto-detect when the video opens with music).
- Already analyzed? The app offers the old result instead of starting again.

The video page shows progress per 2-minute unit, then a Vietnamese overview: logline, synopsis, characters,
why viewers get hooked, how it is filmed. The full English story, DNA and film analysis are in the other tabs.

### 2. Create a writing style

On the video page: **Tạo phong cách viết**, give it a short name (lowercase, hyphens, e.g. `storm-village`).
About 10-20 minutes. Another reference video can later **update** the same style instead of making a new one.

The style page shows what kind of ideas it fits, its main rules in Vietnamese, the version history and the
series that use it.

### 3. Start a series

**Series mới**: pick a style, write or paste the idea (a template, a `.md`/`.txt` file or drag & drop work;
fragments are fine), choose 10-20 episodes and 60-120 s per episode.

```
Bối cảnh: làng chài miền Trung, mùa bão.
Nhân vật: Mai (17, con gái người gác hải đăng), Tuấn (bạn thân), ông Bảy (trưởng làng).
Cảnh muốn có: Mai tìm thấy thư của mẹ trong căn phòng bị niêm phong.
Kết: chưa nghĩ ra, muốn có twist.
```

Claude writes the adaptation map (how your idea fits the style's story structure), the series bible and the
season outline, checks the **story contract** (and repairs what is missing once), runs the **script editor**,
then **stops for your review**. Empty parts are filled from the style and marked; where your
idea and the style disagree, your idea wins.

### 4. Review the outline, then write the episodes

Read the bible and outline in the project. Not right yet: send feedback. Right: **Duyệt outline → viết tập**.
Claude writes every episode (about 2 minutes per episode).

The overview shows **Kiểm tra cốt truyện** (7 requirements, pass/fail, **Sửa tự động**). **Biên tập** in the
sidebar shows the editor's 9 scores with evidence and a list of findings: tick the ones to fix and press
**Áp dụng**; Claude writes new versions and re-checks. Switches on that page turn the automatic editor pass
on/off after the outline and after the episodes (cost and time).

### 5. Read, comment, edit, compare

Each episode opens as scene cards: action, dialogue and voice-over styled apart, a scene timeline, a "story"
view or a "full technical" view (camera, light, sound).

- **Comment**: hover a beat, click **Góp ý** (select text first to quote it). Collect notes across episodes,
  then **Gửi N góp ý cho Claude sửa** sends them as one round with exact positions.
- **Edit directly**: **Sửa trực tiếp** to change words yourself; saved as the next version, no Claude call.
- **Compare**: word-level diff between any two versions.
- **Dialogue** (**Lời thoại** in the sidebar, or **Làm rõ thoại** on an episode): lines that are hard to follow
  (noun-fragment chains, stacked metaphors, pronoun switches, machine-style clock times) are flagged;
  Claude rewrites only the wording (scenes and timing stay) following `.claude/skills/dialogue-polish/references/vi-dialogue.md`.
  Every line you change with **Sửa trực tiếp** is kept as a before/after example that the next writing rounds imitate.

Feedback that is about this series changes only this series. Feedback that applies to any series ("every
cliffhanger feels the same") also improves the style, as a new style version.

### 6. Looks: characters, costumes, locations, props

**Ngoại hình** in the project sidebar.

- **Lập kho** builds the registry from the bible and episodes: face, hair and build per character, which
  costume each one wears in which episode, every location with its time-of-day variants, props, and a list of
  **continuity errors** between episodes with suggested fixes.
- **Sửa** changes a character, location or prop by hand (new registry version). **Nhờ Claude sửa** takes
  free-text corrections. **Cập nhật từ các tập** re-reads the latest episodes.
- **Tạo ảnh còn thiếu** asks Codex for a character sheet (face + 3 full-body views), extra costumes of the same
  person, one image per location and time of day, and props. Review them in **Duyệt ảnh**; approved images
  become the references for shot lists and video tools, and the character avatars in the episode reader.
- Scene headers in the episode reader link to their location and costumes.

### 7. Finalize and export

**Chốt season** copies the latest bible, outline, episodes and looks registry into `final/`. Download the whole
screenplay as one `.md` from the project overview.

Changed something after finalizing (feedback, editor fixes, dialogue pass, a hand edit)? The project shows
**Có sửa sau khi chốt** with what changed; **Chốt lại** copies those into `final/` (no Claude). Video prompts
built from the older `final/` are marked to be made again.

### 8. After production

- **Continue a series** (**Viết tiếp từ video đã quay** on the projects page or in a series sidebar) whose
  first episodes are already made into videos: the produced videos are checked
  against the scripts (video wins), the bible is updated, and the next episodes are outlined, either following
  the old plan or as a new arc. Three checking levels, cheapest first: skip (your notes only), quick
  (transcript + line-by-line diff), full (frames analyzed like a reference video).
- **Video prompts**: **Tạo prompt video** (overview, all episodes; or one episode) splits each finalized
  episode into 10-15 s clips (one generation each, timed cuts inside, every line timed); **Xem prompt video** on
  an episode shows them with copy buttons and reference images. Then **Tải gói video** per episode: a zip with
  `prompts/clip_NN.txt` (prompt, cuts, dialogue, which reference images to upload in order), `refs/`, `clips/`
  (save each generated video as `clip_NN.mp4`), `subtitles.srt` and `edit_list.csv`.
- **Production briefs** per approved episode (commands): see [PRODUCTION_PIPELINE.md](PRODUCTION_PIPELINE.md).

## Command line (Claude Code)

Every step is also a command inside Claude Code opened at the project folder (`claude`, or the VS Code
extension). Results land in the same folders, so the app shows them too.

| Step | Command |
|---|---|
| Learn a reference video | `/analyze-videos --input data/input/reference.mp4` (say the dialogue language, e.g. "dialogue is Vietnamese") |
| Create a style | `/skill-creator-from-dna --dna data/analyses/<run-id>/dna.json --name <slug>` (`--update <slug>` to add a video to a style) |
| Write a series | `/write-series-<slug> --idea-file data/input/idea.md --episodes 12 --episode-sec 90` |
| Feedback / approve | `/refine-skill <slug> --feedback "..."`, `--approve outline`, `--approve` |
| Looks registry | `/series-assets --session data/series/<slug>/<session-id> [--feedback "..."]` |
| Story contract | `/story-contract --session <session-dir>` (check + repair); check only: `python3 .claude/skills/story-contract/_story_check.py <session-dir>` |
| Script editor | `/story-editor --session <session-dir>` (review), `--apply F1,F3` or `--apply all` |
| Dialogue | `/dialogue-polish --session <session-dir> [--episodes 3,4]`; flags only: `python3 .claude/skills/dialogue-polish/_dialogue_lint.py lint <session-dir>` |
| Reference images | `.venv/bin/python -m app.pipeline.assets plan\|generate\|status\|approve\|reject --session <session-dir>` |
| Continue after production | `/continue-series --session <dir> --canon <run>/dna.json --style write-series-<slug> --produced <k> --direction follow\|new-arc --new-episodes <m>` |
| Shot list + video prompts | `/script-to-shotlist data/series/<slug>/<session-id>/final/ep01.md` |
| Briefs | `/direct-video`, `/cinematographer-brief`, `/sound-design-brief`, `/production-design-brief` |

`/write-series-<slug>` options:

| Option | Default | Meaning |
|---|---|---|
| `--idea` / `--idea-file` | required | Idea as text, or a file path |
| `--episodes` | 12 | Number of episodes, 10-20 |
| `--episode-sec` | 90 | Episode length, 60-120 seconds |
| `--characters` | - | Names + roles, e.g. `"Mai (lead), Tuan (friend)"` |
| `--sample` | - | Existing draft; keeps its content and applies the style |
| `--auto` | off | Write all episodes without stopping for outline review |

Analysis without Claude Code open: `.venv/bin/python -m app.pipeline.analyze --run data/analyses/<run-id>`
(resume) or `--video <path>`.

## Time and cost

Measured on a CPU-only laptop; your numbers vary with the machine and the Claude plan. The app learns from
finished jobs and shows "time left" for running ones.

| Step | Time | Notes |
|---|---|---|
| Learn a video | ~1.5 h for 50 min of video | transcript ~0.65x video length; ~3-4 min per 2-min unit, 4 units at once; merge 6-18 min. Full frame analysis ≈ $0.45 per video minute of Claude usage |
| Create a style | 10-20 min | |
| Bible + outline | 5-10 min | |
| Episodes | ~2 min per episode | |
| Feedback round | 3-10 min | |
| Story contract check | seconds | repair (when needed) 5-15 min |
| Script editor | 5-15 min | ≈ $1-2 per review; applying fixes 5-20 min |
| Dialogue pass | 2-4 min per episode | |
| Video prompts | 3-8 min per episode | 4 episodes at once |
| Looks registry | 5-10 min | |
| Reference image (Codex) | 1-4 min each | one at a time; ~25 images for a 10-episode series |
| Vietnamese summary | ~1 min | ≈ $0.2 (Sonnet) |

On a Claude subscription the cost shown per job reflects usage, not a bill. The project header shows the sum
for that series.

## Configuration

Put overrides in `.env` (copy `.env.example`; gitignored, loaded by `./run_app.sh`).

| Variable | Default | Meaning |
|---|---|---|
| `HF_TOKEN` | - | Hugging Face token for speaker labels |
| `CLAUDE_BIN` | auto | Path to the `claude` binary |
| `CODEX_BIN` | auto | Path to the `codex` binary |
| `PORT` | 8765 | Web app port |
| `STORY_DNA_PARALLEL` | 4 | Claude processes at once during analysis |
| `STORY_DNA_CODEX_PARALLEL` | 1 | Images generated at once |
| `STORY_DNA_VIDEO_TARGETS` | `flow` | Video prompts to write: `flow` (Google Flow only) or `flow,higgsfield` (also 10-15s clip prompts + Higgsfield zip; slower) |
| `STORY_DNA_CODEX_TIMEOUT` | 600 | Seconds before one image attempt is abandoned |
| `STORY_DNA_BROWSE_ROOTS` | `~` | Folders the video picker may show (`:`-separated) |
| `STORY_DNA_PERMISSION_MODE` | `acceptEdits` | Permission mode of the headless Claude runs |

## Where things are stored

All results are files under `data/` (gitignored). JSON is the source of truth; Markdown sits next to it for
reading. Nothing is overwritten: every change is a new version (`bible_v2`, `ep04_v3`, `assets_v2`,
`SKILL_v3`).

```
data/
├── input/                              # reference videos (copied or uploaded)
├── analyses/<run-id>/                  # one per reference video
│   ├── manifest.json, shots/, frames/, transcripts/, dna/   # per-unit work
│   ├── dna.json, dna.md, story.md      # merged plot + craft DNA
│   ├── film_analysis.md/.json          # why it hooks, how to split into episodes
│   └── summary_vi.json                 # Vietnamese summary for the app
├── series/<slug>/<session-id>/         # one per series
│   ├── input.json, idea.md, adaptation.md
│   ├── bible_vN.md/.json, outline_vN.md/.json, canon_vN.md/.json
│   ├── episodes/epNN_vK.md/.json       # every version of every episode
│   ├── assets/assets_vN.md/.json       # looks registry
│   ├── assets/characters|locations|props/, images.json   # reference images + review state
│   ├── story_check.json, dialogue_check.json   # latest automatic checks
│   ├── editor/review_vN.json/.md, applied_vN.json  # script editor rounds
│   ├── dialogue/polish_vN.json         # dialogue pass: every before/after line
│   ├── comments.json                   # review comments
│   ├── iterations.json                 # every feedback / approval / edit round
│   └── final/                          # approved season: bible, outline, epNN, assets, series.md
│       └── shots/epNN/                 # shotlist + prompts.json/.md for the video package
├── dialogue_examples.json              # lines reviewers rewrote by hand (writers imitate them)
├── skills-generated/                   # style metadata per version + Vietnamese summaries
├── jobs/<id>.json + .log               # background jobs (resume after a restart)
├── archive/skills/                     # hidden styles (restorable)
└── ui_state.json                       # hidden projects / videos / jobs
```

```
.claude/
├── CLAUDE.md                           # project rules and footguns (read this before changing anything)
├── agents/                             # video-analyst, story-merger, film-analyst
└── skills/
    ├── analyze-videos/                 # _analyze.py (shots, units, frames), _transcribe.py (WhisperX)
    ├── skill-creator-from-dna/         # DNA -> write-series-<slug>
    ├── write-series-<slug>/            # generated styles (SKILL.md, references/, versions/)
    ├── refine-skill/                   # feedback, approve
    ├── series-assets/                  # looks registry, _assets.py scan/validate/render/lint
    ├── continue-series/                # continue after production
    ├── story-contract/                 # complete-story requirements + _story_check.py
    ├── story-editor/                   # depth rubric + _editor.py
    ├── dialogue-polish/                # Vietnamese dialogue guide + _dialogue_lint.py
    ├── script-to-shotlist/             # shots + video prompts
    └── direct-video/, cinematographer-brief/, sound-design-brief/, production-design-brief/
app/                                    # FastAPI backend + older pages
web/                                    # React UI source (built into app/static/ui/)
```

## Development

- **Backend**: FastAPI in `app/`. `app/api.py` is the JSON API for the React UI (Server-Sent Events at
  `/api/events` and `/api/jobs/<id>/events`); `app/main.py` mounts it and still serves the older pages.
  Long work runs as jobs (`app/jobs.py`), resumable, skipping finished steps and units.
- **Claude** is called only in `app/claude_runner.py` (headless `claude -p` in the project dir, so project skills
  and agents load as usual). **Codex** only in `app/codex_runner.py`.
- **Pipelines**: `app/pipeline/analyze.py` (analysis), `series.py` (styles, outline, refine, continue,
  registry), `assets.py` (reference images), `screenplay.py` (comments, manual edits, JSON -> Markdown),
  `summary.py` (Vietnamese summaries); `app/eta.py` estimates time left.
- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn (Base UI) in `web/`. The build is committed in
  `app/static/ui/` so users need Python only. After changing `web/`:
  ```bash
  ./run_app.sh      # terminal 1: the backend (API, jobs) on :8765 - the dev UI needs it
  cd web && npm install
  npm run dev       # terminal 2: open http://localhost:5173/ui/ (hot reload; /api is proxied to :8765)
  npm run build     # writes app/static/ui/ - commit it
  ```
  Without the backend the dev UI shows a red "Không kết nối được máy chủ" banner and reconnects by itself.
- **Unit tests** (no Claude, no network) cover the deterministic checks and the app's file logic:
  ```bash
  uv pip install --python .venv/bin/python -r requirements-dev.txt   # once
  .venv/bin/python -m pytest -q
  ```
- **Browser tests** (system Chrome via `playwright-core`): `web/scripts/e2e-*.mjs`. They write data, so run them
  against a copy of a session (the scripts say which), never on real work.
- Headless Claude cannot write inside `.claude/`; style edits go through `data/skills-staging/` and are installed
  by the backend. Other footguns: `.claude/CLAUDE.md`.

## Switch to a new reference video

Keep the tool skills and agents; remove the generated styles `.claude/skills/write-series-*` and the data in
`data/analyses/*`, `data/series/*`, `data/skills-generated/*` (or ask Claude to "reset the project per
CLAUDE.md"). Then start again at step 1. To keep old work instead, just hide it in the app.

## Troubleshooting

| Symptom | Fix |
|---|---|
| App says "claude CLI not found" | Install Claude Code and log in, or set `CLAUDE_BIN` in `.env` |
| `/ui/` shows "not built" | `cd web && npm install && npm run build` (or use a copy with `app/static/ui/` committed) |
| Port 8765 in use | `PORT=8800 ./run_app.sh` |
| A job shows "interrupted" | The server was restarted while it ran; open the job and click **Chạy tiếp** (finished parts are skipped) |
| `ffmpeg: command not found` | Install ffmpeg |
| `.venv/bin/python: No such file` | Run the install step 2; without WhisperX dialogue is only guessed from frames |
| Transcript in the wrong language / gibberish | Analyze again with the right dialogue language |
| Odd repeated lines ("Thank you", "Please subscribe...") | Whisper hallucinates over music; the analysts drop them (`dropped_segments`) |
| Too many / too few shots | `/analyze-videos ... --scene-threshold 0.2` (fewer) or `0.08` (more, dark footage) |
| A character split in two / two merged into one | Check the merge notes in `dna.md`, fix it through feedback |
| `/write-series-...` does not appear in Claude Code | Check `.claude/skills/write-series-<slug>/SKILL.md` exists, restart the Claude Code session |
| Speaker labels off although a token is set | Model terms not accepted on Hugging Face, or `HF_TOKEN` not in `.env` / not exported |
| "Codex CLI not found" / no images | Install and log in to the ChatGPT/Codex extension, or set `CODEX_BIN` |
| An image keeps failing | See the error under the item (usually a content refusal or a plan limit); edit the description, try later |
| Episodes and the looks registry disagree | **Ngoại hình → Cập nhật từ các tập**, then check **Lỗi liên tục** |

## Limits

- Local, single machine: the app uses the Claude Code (and Codex) accounts logged in on that machine. Serving
  other people over the internet would need the Claude API, logins and a job queue.
- The only external service besides Claude is Codex for images, on the user's ChatGPT plan.
- Analyses and styles are written in English (they are read by Claude); the app adds Vietnamese summaries.
  Screenplays follow the language of your idea.
- Reference images keep faces consistent across shots well, but not perfectly; review every image.
