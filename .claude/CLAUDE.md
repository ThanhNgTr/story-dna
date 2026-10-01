# story-dna: Video → Script → DNA → Skill Pipeline

## PROJECT SCOPE

POC system for:
- Analyzing local videos to extract narrative DNA (characters, pacing, tone, structure)
- Auto-generating reusable Claude skills from that DNA
- Letting users create scripts using those skills
- Breaking scripts into shot lists for downstream video generation

**Output**: Markdown for humans + JSON for agents
**Tech**: Claude Vision (built-in), ffmpeg (local), Python (frame extraction)
**No external APIs** in POC (no OpenRouter, Deepgram — using claude-vision + local audio fallback)

## KEY CONCEPTS

- **DNA**: Structured narrative rules extracted from reference videos
  - Character archetypes & roles
  - Narrative structure (setup/conflict/resolution timing)
  - Pacing rules (avg shot duration, cut rhythm, transitions)
  - Tone & voice (formal/casual/comedic/dramatic)
  - Hook patterns (opening 0–3s, call-to-action ending)
  - Visual style (color, camera movement)

- **Skill generation**: Auto-create `.claude/skills/write-story-<slug>/SKILL.md` from DNA
  - Embeds narrative rules into skill prompt
  - Includes character templates + pacing guidelines
  - Pulls examples from analyzed videos

- **Feedback loop**: User → script → feedback → skill patch → new script
  - Version skills as `write-story-<slug>_v1`, `v2`, etc.
  - Never overwrite — keep iteration history

## FOOTGUNS

1. **Frame extraction is slow**: 1 fps = 60 frames/min. Cap at `--max-frames` (default 30).
2. **Claude Vision context limits**: Batch frames in chunks (e.g., 10 frames per call).
3. **SKILL.md YAML must be valid**: Bad frontmatter → `/skill load` fails silently.
4. **Video codec issues**: fallback to `ffmpeg -c:v copy` if extraction stalls.
5. **Skill name conflicts**: Check `.claude/skills/` before generating new skills.

## WORKFLOW

1. **Analyze videos** (`/analyze-videos --input <dir>`)
   - Extracts frames @ 1 fps (configurable)
   - Calls Claude Vision on batches → summarizes key shots
   - Extracts audio (assumes MP4/MOV with audio track)
   - Produces: `dna.json`, `dna.md`, `videos_analyzed.json`, `frames/`

2. **Generate skill** (`/skill-creator-from-dna --dna data/.../dna.json --name <slug>`)
   - Reads `dna.json`
   - Creates `.claude/skills/write-story-<slug>/SKILL.md`
   - Embeds DNA rules into skill prompt
   - Saves metadata to `data/skills-generated/write-story-<slug>_v1.json`

3. **Create script** (`/write-story-<slug> --topic X --characters Y`)
   - Auto-generated skill from step 2
   - User provides topic, characters, plot points
   - Returns script v1 (Markdown)

4. **Refine skill** (`/refine-skill <slug> --feedback "..."`)
   - Parse user feedback (tone, pacing, characters, etc.)
   - Patch SKILL.md of `write-story-<slug>`
   - Save as `write-story-<slug>_v2.md`
   - Re-run user input through updated skill

5. **Break into shots** (`/script-to-shotlist <script.md>`)
   - Parse script into scenes/dialogue
   - Break into 1–5s shots based on DNA pacing rules
   - Output: `shotlist.json` + `shotlist.md`

## OUTPUT STYLE

- **Caveman ultra**: minimal jargon, clear structure
- No emoji
- Code examples where helpful
- JSON/Markdown over prose for data
- Timestamps in ISO 8601 (2025-10-01T14:30:00Z)

## CRITICAL RULES

1. **Reproducibility**: Always save DNA output to `data/<run-id>/` with timestamp
2. **Versioning**: Skills as `write-story-<slug>_v1`, `v2`, etc. (don't overwrite)
3. **Transcripts**: Keep iteration history in `data/<run-id>/iterations.json`
4. **Frame caching**: Reuse frames if video unchanged (check file hash)
5. **Error recovery**: Graceful fallbacks (missing audio → text-only, frame extract fails → use keyframes)

## ARCHITECTURE PATTERNS

- **Skills as modules**: Each skill is self-contained in `.claude/skills/<name>/`
- **Data layer**: All outputs go to `data/` (reproducible, versioned, auditable)
- **Claude Vision batching**: Group frames to respect context window (~50–100 frames per batch)
- **JSON as source of truth**: DNA, scripts, metadata all as JSON alongside Markdown

## GIT WORKFLOW

- Commit frequently: POC features → feature branches → PR → main
- Commit messages: `feat(skill): describe`, `fix(analyze): ...`, `docs: ...`
- Keep `.claude/` in VCS (skills are code)
- `.gitignore`: `data/`, `*.mp4`, `*.mov` (videos stay local)
