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
  - Live `write-story-<slug>/SKILL.md` = latest; snapshots in `versions/SKILL_v1.md`, `v2`, etc.
  - Never overwrite — keep iteration history

## FOOTGUNS

1. **Frame budget**: keyframes per detected shot, capped at `--max-frames` (default 30). Fast-cut videos have more shots than frames — raise to 40+ or shots get skipped (pacing still measured on all).
2. **Claude Vision context limits**: Batch frames in chunks (e.g., 10 frames per call).
3. **SKILL.md YAML must be valid**: Bad frontmatter → `/skill load` fails silently.
4. **Video codec issues**: fallback to `ffmpeg -c:v copy` if extraction stalls.
5. **Skill name conflicts**: Check `.claude/skills/` before generating new skills.

## WORKFLOW

Core flow. Steps 1–2 run rarely (project start, or learning a new viral idea).
Steps 3–6 run per script.

```
video list ─▶ [1] analyze ─▶ dna.json ─▶ [2] skill-creator ─▶ write-story-<slug> (CORE)
                                                                  │
user topic + sample script ─▶ [3] write-story-<slug> ─▶ script vK  │
                                   ▲                         │     │
                                   └── [4] refine-skill ◀── feedback (loop until approve)
                                                             │
                                          approve ─▶ [5] final.md ─▶ [6] script-to-shotlist
                                                                          └▶ prompts.json/.md (OUTPUT)
```

1. **Analyze videos** (`/analyze-videos --input <dir>`)
   - Detects real cuts (ffmpeg scene score), measures pacing in code, extracts keyframes per shot; one `video-analyst` agent per video, `series-merger` merges
   - Learns series: context/world, characters, plot patterns, pacing, tone, hooks
   - Produces: `dna.json`, `dna.md`, `manifest.json`, `frames/`

2. **Generate skill** (`/skill-creator-from-dna --dna data/.../dna.json --name <slug>`)
   - Creates `.claude/skills/write-story-<slug>/SKILL.md` with Story Bible + Character Bible + DNA rules
   - New viral idea for an existing skill: `--update <slug>` → merges DNA, version bump
   - Saves metadata to `data/skills-generated/write-story-<slug>_vN.json`

3. **Create script** (`/write-story-<slug> --topic X --characters Y --sample <file>`)
   - User provides topic, characters, optional sample script to follow
   - Returns `data/scripts/<slug>/<session-id>/script_v1.md` + `.json`

4. **Feedback loop** (`/refine-skill <slug> --feedback "..."`)
   - Human in the loop. Feedback split into `rule` (patch skill) vs `script` (one-off edit)
   - Live SKILL.md bumped to vN+1, old one snapshot in `versions/SKILL_vN.md`
   - Re-generates script on same input → script vK+1. Repeat.

5. **Finalize** (`/refine-skill <slug> --approve`)
   - Marks skill version stable, writes `final.md` + `final.json`

6. **Prompt list** (`/script-to-shotlist <final.md>`)
   - Breaks final script into 1–5s shots based on DNA pacing rules
   - Output: `shotlist.json/.md` + `prompts.json/.md` (per shot: who says what, does what, camera, self-contained video prompt)

Optional after step 6: `/direct-video`, `/cinematographer-brief`, `/sound-design-brief`, `/production-design-brief`.
`/write-compelling-short-form` = hand-written generic framework (Hollow Pine DNA), use only when no generated skill fits.

## OUTPUT STYLE

- **Caveman ultra**: minimal jargon, clear structure
- No emoji
- Code examples where helpful
- JSON/Markdown over prose for data
- Timestamps in ISO 8601 (2025-10-01T14:30:00Z)

## CRITICAL RULES

1. **Reproducibility**: Always save DNA output to `data/<run-id>/` with timestamp
2. **Versioning**: Live SKILL.md + immutable `versions/SKILL_vN.md` snapshots, metadata `write-story-<slug>_vN.json` (don't overwrite)
3. **Transcripts**: Keep iteration history in `data/scripts/<slug>/<session-id>/iterations.json`
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
