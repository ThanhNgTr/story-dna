---
name: analyze-videos
description: |
  Learn the story and the craft of a reference video. Built for ONE long video
  (many episodes edited into one continuous cut), also works on a folder of videos.
  Detects real cuts, splits long videos into ~2-min units on cut boundaries,
  transcribes dialogue locally (WhisperX), runs one video-analyst agent per unit in
  parallel, then story-merger stitches everything into one plot + craft DNA:
  plot, acts, reveals, main/supporting characters, storytelling, camera, sound,
  color, pacing. Triggers on: "analyze video", "learn this story", "extract DNA",
  "video analysis", "phan tich video", "hoc cot truyen". Output: dna.json, dna.md,
  story.md for /skill-creator-from-dna.
---

# Analyze Videos -> Story + Craft DNA

## When to Use

- Project start, or a new reference video to learn from (rare, expensive step)
- Input: one long video (e.g. 20-40 min of episodes edited into one), or a folder of videos
- Output: `data/analyses/<run-id>/` with `dna.json`, `dna.md`, `story.md` -> `/skill-creator-from-dna`

```
/analyze-videos --input data/input/reference.mp4
```

## Pipeline

```
video ─▶ [1] _analyze.py  shots on whole video ─▶ units of ~120s (cut boundaries) ─▶ keyframes per unit
      ─▶ [2] _transcribe.py  WhisperX once per source ─▶ split per unit
      ─▶ [3] video-analyst × N units (parallel) ─▶ dna/<unit_id>.dna.json
      ─▶ [4] story-merger  (parts of ≤8 units if N > 8, then final) ─▶ dna.json + dna.md + story.md
```

All times are absolute seconds in the source video, so units stitch back into one timeline.

### Step 1 — Shots, units, frames (Python + ffmpeg, no deps)

```bash
python3 .claude/skills/analyze-videos/_analyze.py --input data/input/reference.mp4
```

| Flag | Default | Meaning |
|---|---|---|
| `--chunk-sec` | 120 | Target unit length; each boundary snaps to the nearest real cut (±50%) |
| `--chunk-min-video` | 240 | Videos shorter than this stay one unit |
| `--max-frames` | 40 | Keyframes per unit (1 per shot, spare to long shots; hook shots kept) |
| `--scene-threshold` | 0.12 | Adaptive cut sensitivity. Raise (0.2) if false cuts, lower (0.08) for dark footage |
| `--sampling uniform` | | Fallback: evenly spaced frames (auto if detection fails) |

Output in `data/analyses/<run-id>/`:
- `manifest.json`: `sources[]` (whole-video `pacing_measured`, `shots_path`, `units`) + `units[]` (`unit_id`, `t_start`, `t_end`, `chunk`, `frames[]`, `shots_path`, `pacing_measured`)
- `shots/<stem>.json` (whole video) and `shots/<unit_id>.json`
- `frames/<unit_id>/frame_NNNN_t<abs_sec>_<shot_id>.jpg`

Speed: ~17s for 3 min of 1080p (detection decodes at 320px). Known limits: fades/dissolves often merge into one shot; lightning/flashes can add a false cut.

### Step 2 — Audio: transcript (+ speakers)

```bash
.venv/bin/python .claude/skills/analyze-videos/_transcribe.py --manifest data/analyses/<run-id>/manifest.json
```

- WhisperX `large-v3-turbo` on CPU, word timestamps, ~0.65x realtime (30 min video ≈ 20 min)
- Language is auto-detected from the first 30s only. If the user says the dialogue language (e.g.
  Vietnamese) or the video opens with music, pass `--language vi` (etc.). After the run, check
  `audio.language` in the manifest; wrong -> re-run with `--language`. Vietnamese word alignment
  uses `nguyenvulebinh/wav2vec2-base-vi-vlsp2020` (downloaded on first use)
- Writes `transcripts/<stem>.json` + `transcripts/<unit_id>.json` (segments with `shot_id`, silences, `audio` summary); adds `transcript_path` + `audio` to sources and units
- Speaker labels only with `HF_TOKEN` set + pyannote diarization terms accepted on Hugging Face; otherwise agents assign speakers from frames
- No audio stream -> skipped; ASR error -> silences kept, agents infer dialogue
- No `.venv` -> skip this step (dialogue becomes `inferred`). One-time setup:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path
  ~/.local/bin/uv venv .venv --python 3.12
  ~/.local/bin/uv pip install --python .venv/bin/python whisperx \
    --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match
  ```

### Step 3 — Unit analysis (`video-analyst`, one per unit, parallel)

Frame images must NOT be read in the main context (40 frames ≈ 70k tokens). Launch all units in
one message (background), passing from `manifest.units[i]`:

```
unit_id, filename, t_start, t_end, duration_sec, chunk
frames_dir, shots_path, transcript_path
output_path: <run_dir>/dna/<unit_id>.dna.json
context: (optional) known names + visual signatures
```

Each returns a ≤250-word summary; only summaries enter the main context. If an agent fails, re-run
that unit only. More than ~12 units: launch in waves of 8-12.

### Step 4 — Story merge (`story-merger`)

- N ≤ 8 units: one call, `mode: final`, `inputs`: all `dna/*.dna.json` in order, `output`: run_dir
- N > 8: `mode: part` per group of ≤8 consecutive units -> `parts/part_NN.json` (groups in parallel),
  then one `mode: final` on the parts

Produces `dna.json` (story + characters + craft, schema in `.claude/agents/story-merger.md`),
`dna.md`, `story.md`.

### Step 5 — Review + hand off

Show the user: logline, act table, main/supporting characters, open questions, merge notes
(uncertain character matches). Then:
- New project -> `/skill-creator-from-dna --dna <run_dir>/dna.json --name <slug>`
- More reference for an existing skill -> `/skill-creator-from-dna --dna <run_dir>/dna.json --update <slug>`

## Notes

- Requires `ffmpeg` + `ffprobe`; audio step requires `.venv` (WhisperX)
- No external API: agents read images natively
- Reproducible: everything for a run lives in `data/analyses/<run-id>/`
- Frames + transcripts are the evidence: DNA rules cite times/lines, so they can be checked
