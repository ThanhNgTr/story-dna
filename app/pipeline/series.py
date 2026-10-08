"""Series side: generate the skill, write outline/episodes, feedback loop, export screenplay .md.

Claude does the writing through the project skills (/skill-creator-from-dna, /write-series-<slug>,
/refine-skill); this module builds the prompts, checks outputs and reads session state for the UI.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .. import config
from ..claude_runner import run_claude
from ..jobs import Job


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "series"


def skill_dir(slug: str) -> Path:
    return config.SKILLS / f"write-series-{slug}"


# Claude Code protects .claude/ from headless writes (allow rules do not lift it). So Claude edits a
# staged copy under data/, and the backend validates it and installs it into .claude/skills/.
STAGING = config.DATA / "skills-staging"


def staging_dir(slug: str) -> Path:
    return STAGING / f"write-series-{slug}"


def stage_skill(slug: str) -> Path:
    """Fresh staged copy of the live skill (empty dir if the skill does not exist yet)."""
    st = staging_dir(slug)
    if st.exists():
        shutil.rmtree(st)
    if skill_dir(slug).exists():
        shutil.copytree(skill_dir(slug), st)
    else:
        st.mkdir(parents=True)
    return st


def validate_skill(path: Path, slug: str) -> dict:
    import yaml
    text = (path / "SKILL.md").read_text()
    parts = text.split("---", 2)
    if not text.startswith("---") or len(parts) < 3:
        raise RuntimeError("SKILL.md has no YAML frontmatter")
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict) or fm.get("name") != f"write-series-{slug}" or not fm.get("description"):
        raise RuntimeError(f"SKILL.md frontmatter invalid (name must be write-series-{slug}, description required)")
    return fm


def install_skill(slug: str) -> str | None:
    """Validate the staged skill and copy it into .claude/skills/. Returns the version, or None if unchanged."""
    st = staging_dir(slug)
    if not (st / "SKILL.md").exists():
        raise RuntimeError(f"{st}/SKILL.md was not written")
    live = skill_dir(slug)
    if (live / "SKILL.md").exists() and (live / "SKILL.md").read_text() == (st / "SKILL.md").read_text() \
            and not _changed(st, live):
        return None
    fm = validate_skill(st, slug)
    # Never overwrite existing version snapshots
    for snap in (live / "versions").glob("*") if (live / "versions").exists() else []:
        staged = st / "versions" / snap.name
        if staged.exists() and staged.read_bytes() != snap.read_bytes():
            raise RuntimeError(f"staged copy changed immutable snapshot {snap.name}")
    shutil.copytree(st, live, dirs_exist_ok=True)
    # Immutable snapshot of this version, if Claude did not write one
    snap = live / "versions" / f"SKILL_{fm.get('version')}.md"
    if fm.get("version") and not snap.exists():
        snap.parent.mkdir(exist_ok=True)
        shutil.copy2(live / "SKILL.md", snap)
    return str(fm.get("version"))


def _changed(a: Path, b: Path) -> bool:
    for f in a.rglob("*"):
        if f.is_file():
            g = b / f.relative_to(a)
            if not g.exists() or g.read_bytes() != f.read_bytes():
                return True
    return False


UI_NOTE = ("\n\nWEB APP: the user reviews and approves in a web UI with buttons (Feedback, Approve outline, "
           "Approve season). Do not write slash-command or CLI instructions into any document.")


def skill_info(slug: str) -> dict:
    """Name, short description, version and source analysis of a generated skill (for the UI)."""
    import yaml
    info = {"slug": slug, "name": f"write-series-{slug}", "description": "", "version": None, "run_id": None}
    try:
        text = (skill_dir(slug) / "SKILL.md").read_text()
        fm = yaml.safe_load(text.split("---", 2)[1]) or {}
        desc = " ".join(str(fm.get("description", "")).split())
        # Every generated description starts with the same boilerplate; show the style-specific part
        i = desc.find("told the way")
        if i >= 0:
            desc = "Phong cách: " + desc[i + len("told the way"):].strip()
        j = desc.find(" Use whenever")
        info["description"] = desc[:j] if j > 0 else desc
        info["version"] = fm.get("version")
    except Exception:
        pass
    metas = sorted(config.DATA.glob(f"skills-generated/write-series-{slug}_v*.json"))
    for meta in reversed(metas):
        try:
            m = json.loads(meta.read_text())
            src = m.get("dna_sources") or [m.get("dna_source")]
            run = next((Path(x).parent.name for x in src if x), None)
            if run:
                info["run_id"] = run
                break
        except Exception:
            pass
    return info


def staging_note(slug: str) -> str:
    return (f"\n\nAPP MODE: this session cannot write inside .claude/. The editable copy of the skill "
            f"write-series-{slug} is {staging_dir(slug)} (same layout: SKILL.md, references/, versions/). "
            "Read and write the skill ONLY there; treat it exactly as .claude/skills/write-series-"
            f"{slug}/. The app validates and installs it afterwards. Other outputs (data/...) go to their "
            "usual paths.")


def list_series_skills() -> list[str]:
    return sorted(p.name.removeprefix("write-series-") for p in config.SKILLS.glob("write-series-*")
                  if (p / "SKILL.md").exists())


def session_dir(slug: str, session_id: str) -> Path:
    return config.SERIES / slug / session_id


def _version(p: Path) -> int:
    m = re.search(r"_v(\d+)\.", p.name)
    return int(m.group(1)) if m else 0


def latest(paths) -> Path | None:
    paths = list(paths)
    return max(paths, key=_version) if paths else None


def session_state(slug: str, session_id: str) -> dict:
    d = session_dir(slug, session_id)
    episodes = {}
    for p in (d / "episodes").glob("ep*_v*.md"):
        num = int(re.match(r"ep(\d+)_", p.name).group(1))
        if num not in episodes or _version(p) > _version(episodes[num]):
            episodes[num] = p
    iterations = []
    if (d / "iterations.json").exists():
        try:
            iterations = json.loads((d / "iterations.json").read_text())
        except json.JSONDecodeError:
            pass
    outline_approved = any("outline" in json.dumps(it).lower() and "approved" in json.dumps(it).lower()
                           for it in (iterations if isinstance(iterations, list) else []))
    inp = json.loads((d / "input.json").read_text()) if (d / "input.json").exists() else {}
    produced = int(inp.get("produced_upto") or 0)
    planned = int(inp.get("episodes") or 0)
    # Episodes the outline plans that have neither a script nor a produced video yet
    missing = [n for n in range(produced + 1, planned + 1) if n not in episodes]
    final_dir = d / "final"
    final_eps = {int(m.group(1)) for f in final_dir.glob("ep*.md") if (m := re.match(r"ep(\d+)\.md$", f.name))}
    return {
        "dir": d,
        "input": inp,
        "produced_upto": produced,
        "planned": planned,
        "missing": missing,
        "canon": latest(d.glob("canon_v*.md")),
        "final_complete": final_dir.exists() and not missing and set(episodes) <= final_eps,
        "adaptation": d / "adaptation.md" if (d / "adaptation.md").exists() else None,
        "bible": latest(d.glob("bible_v*.md")),
        "outline": latest(d.glob("outline_v*.md")),
        "versions": {k: sorted(d.glob(f"{k}_v*.md"), key=_version) for k in ("bible", "outline", "canon")},
        "episodes": dict(sorted(episodes.items())),
        "final": (d / "final").exists(),
        "outline_approved": outline_approved or bool(episodes),
        "iterations": iterations if isinstance(iterations, list) else [],
    }


def list_sessions() -> list[dict]:
    out = []
    for d in sorted(config.SERIES.glob("*/*"), reverse=True):
        if d.is_dir():
            st = session_state(d.parent.name, d.name)
            out.append({"slug": d.parent.name, "session_id": d.name, "episodes": len(st["episodes"]),
                        "planned": st["input"].get("episodes"), "final": st["final_complete"],
                        "has_outline": st["outline"] is not None, "missing": st["missing"],
                        "produced": st["produced_upto"],
                        "title": st["input"].get("title") or d.name})
    return out


def _check(cond: bool, msg: str):
    if not cond:
        raise RuntimeError(msg)


async def _claude(job: Job, prompt: str, tag: str, timeout_sec: int = 5400):
    job.log(f"[{tag}] prompt: {prompt[:300]}")
    res = await run_claude(prompt, log=lambda s: job.log(f"[{tag}] {s}"), timeout_sec=timeout_sec)
    job.add_cost(res.cost_usd)
    job.data.setdefault("result", {})["last_reply"] = res.text[-3000:]
    job.save()
    _check(res.ok, f"{tag} failed: {res.error}")
    return res


STORY_CHECK = config.SKILLS / "story-contract" / "_story_check.py"


def _story_check(d: Path, stage: str) -> dict:
    """Deterministic story-contract check; writes and returns <session>/story_check.json."""
    import subprocess
    subprocess.run(["python3", str(STORY_CHECK), str(d), "--stage", stage], cwd=str(config.ROOT),
                   capture_output=True, text=True, timeout=120)
    try:
        return json.loads((d / "story_check.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "errors": ["story_check.py produced no report"], "warnings": []}


def story_check_view(slug: str, session_id: str) -> dict | None:
    """Fresh check for the UI (fast, no Claude). None before an outline exists."""
    st = session_state(slug, session_id)
    if st["outline"] is None:
        return None
    rep = _story_check(st["dir"], "episodes" if st["episodes"] else "outline")
    return {k: rep.get(k) for k in ("ok", "stage", "checked_at", "errors", "warnings")}


async def fix_story(job: Job) -> dict:
    """Web job: check the session and let Claude repair what the story contract flags."""
    p = job.data["params"]
    st = session_state(p["slug"], p["session_id"])
    _check(st["outline"] is not None, "no outline yet")
    rep = await enforce_story_contract(job, st["dir"], "episodes" if st["episodes"] else "outline")
    return {"slug": p["slug"], "session_id": p["session_id"], "ok": rep.get("ok")}


async def enforce_story_contract(job: Job, d: Path, stage: str) -> dict:
    """Check the session against the story contract; on errors let Claude repair once, then re-check.

    Never fails the job: what is left stays in story_check.json and the UI shows it.
    """
    job.step("story_check", "running")
    rep = _story_check(d, stage)
    if not rep.get("ok"):
        job.log(f"[story_check] {len(rep['errors'])} errors, repairing: " + "; ".join(rep["errors"][:5]))
        try:
            await _claude(job, f"/story-contract --session {d}\n\nStage: {stage}. Run non-interactively: do "
                               "not ask questions; keep the user's idea and the style skill's rules." + UI_NOTE,
                          "story_check", 3600)
        except RuntimeError as e:
            job.log(f"[story_check] repair failed: {e}")
        rep = _story_check(d, stage)
    job.step("story_check", "done" if rep.get("ok") else "failed",
             errors=len(rep.get("errors", [])), warnings=len(rep.get("warnings", [])))
    job.data.setdefault("result", {})["story_check"] = {"ok": rep.get("ok"), "errors": rep.get("errors", [])[:30]}
    job.save()
    return rep


async def create_skill(job: Job) -> dict:
    p = job.data["params"]
    run_dir, slug = Path(p["run_dir"]), p["slug"]
    update = bool(p.get("update")) and skill_dir(slug).exists()
    mode = f"--update {slug}" if update else f"--name {slug}"
    job.step("skill", "running")
    stage_skill(slug)
    await _claude(job, f"/skill-creator-from-dna --dna {run_dir / 'dna.json'} {mode}\n\n"
                       "Run non-interactively: do not ask questions; if something is ambiguous, choose "
                       "the documented default and note it in the skill's Data limits." + staging_note(slug),
                  "skill")
    version = install_skill(slug)
    _check(version is not None or update, "skill was not written")
    job.step("skill", "done", skill=f"write-series-{slug}", version=version)
    # Vietnamese summary for the UI; optional, never fails the skill build
    from .summary import summarize_skill
    job.step("summary", "running")
    job.step("summary", "done" if await summarize_skill(job, slug) else "failed")
    return {"slug": slug}


def new_session(slug: str, idea: str, episodes: int, episode_sec: int, title: str) -> str:
    sid = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    d = session_dir(slug, sid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "idea.md").write_text(idea)
    (d / "input.json").write_text(json.dumps({
        "title": title, "idea_file": str(d / "idea.md"), "episodes": episodes, "episode_sec": episode_sec,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, indent=2, ensure_ascii=False))
    return sid


async def write_outline(job: Job) -> dict:
    p = job.data["params"]
    slug, sid = p["slug"], p["session_id"]
    d = session_dir(slug, sid)
    job.step("outline", "running")
    await _claude(job, (
        f"/write-series-{slug} --idea-file {d / 'idea.md'} --episodes {p['episodes']} "
        f"--episode-sec {p['episode_sec']}\n\n"
        f"Session dir already exists, use it exactly: {d} (input.json and idea.md are there; keep them).\n"
        "Run Stage 1 (adaptation.md) and Stage 2 (bible_v1, outline_v1) only, then stop for review. "
        "Do not ask questions; write the screenplay in the language of the idea." + UI_NOTE), "outline")
    st = session_state(slug, sid)
    _check(st["outline"] is not None, "outline was not written")
    job.step("outline", "done")
    await enforce_story_contract(job, d, "outline")
    return {"slug": slug, "session_id": sid}


async def refine(job: Job) -> dict:
    """feedback text, or approve='outline' (writes episodes) / approve='final'."""
    p = job.data["params"]
    slug, sid = p["slug"], p["session_id"]
    if p.get("approve") == "outline":
        missing = session_state(slug, sid)["missing"]
        _check(bool(missing), "no episodes left to write (all planned episodes exist)")
        p["writing"] = missing
        step, timeout = "episodes", 7200
        prompt = (f"/refine-skill {slug} --session {sid} --approve outline\n\n"
                  f"Write ONLY these episodes: {', '.join(str(n) for n in missing)}. Episodes already written or "
                  "marked PRODUCED (canon) must not be rewritten.")
    elif p.get("approve") == "final":
        step, prompt, timeout = "final", f"/refine-skill {slug} --session {sid} --approve", 1800
    else:
        target = f" (target: {p['target']})" if p.get("target") else ""
        step = "feedback"
        prompt = f"/refine-skill {slug} --session {sid} --feedback {json.dumps(p['feedback'], ensure_ascii=False)}{target}"
        timeout = 5400
    job.step(step, "running")
    stage_skill(slug)
    await _claude(job, prompt + "\n\nRun non-interactively: do not ask questions; for ambiguous feedback "
                                "pick the most reasonable reading and log it in iterations.json."
                  + UI_NOTE + staging_note(slug), step, timeout)
    version = install_skill(slug)
    if version:
        job.log(f"[{step}] skill updated -> {version}")
    if step == "episodes":
        left = session_state(slug, sid)["missing"]
        _check(len(left) < len(p["writing"]), "no episodes were written")
        if left:
            job.log(f"[episodes] still missing: {left} (approve the outline again to write them)")
    if step == "final":
        _check(session_state(slug, sid)["final"], "final/ was not created")
    job.step(step, "done")
    if step != "final":
        st = session_state(slug, sid)
        await enforce_story_contract(job, st["dir"], "episodes" if st["episodes"] else "outline")
    return {"slug": slug, "session_id": sid}


async def build_assets(job: Job) -> dict:
    """/series-assets: build or update the asset registry (looks), optionally with look feedback."""
    p = job.data["params"]
    slug, sid = p["slug"], p["session_id"]
    d = session_dir(slug, sid)
    before = {x.name for x in (d / "assets").glob("assets_v*.json")}
    job.step("assets", "running")
    fb = f" --feedback {json.dumps(p['feedback'], ensure_ascii=False)}" if p.get("feedback") else ""
    await _claude(job, f"/series-assets --session {d}{fb}\n\nRun non-interactively: do not ask questions; "
                       "for ambiguous feedback pick the most reasonable reading and log it in iterations.json."
                  + UI_NOTE, "assets", 3600)
    new = sorted({x.name for x in (d / "assets").glob("assets_v*.json")} - before, key=lambda n: _version(Path(n)))
    _check(bool(new), "no new assets_vN.json was written")
    job.step("assets", "done", version=new[-1])
    return {"slug": slug, "session_id": sid, "assets": new[-1]}


async def continue_series(job: Job) -> dict:
    """Check the produced episodes (canon) as cheaply as the chosen mode allows, then /continue-series.

    canon_mode: none (no video), transcript (local WhisperX + local script diff, no frames), full (frames).
    """
    from . import analyze
    p = job.data["params"]
    slug, sid = p["slug"], p["session_id"]
    mode = p.get("canon_mode") or "transcript"
    d = session_dir(slug, sid)
    k, m = int(p["produced_upto"]), int(p["new_episodes"])
    canon_args = f"--canon-mode {mode}"
    run_dir = None

    if mode != "none":
        if p.get("run_id"):
            run_dir = config.ANALYSES / p["run_id"]
            p["run_dir"] = str(run_dir)
            job.step("canon_source", "skipped", note=f"dùng bản phân tích {p['run_id']}")
        elif mode == "full":
            run_dir = Path((await analyze.run_analysis(job))["run_dir"])
        else:  # transcript: audio only, no frames, no Claude
            p["audio_only"] = True
            run_dir = await analyze.step_extract(job)
            await analyze.step_transcribe(job, run_dir)
        job.data["result"]["run_dir"] = str(run_dir)
        job.save()
        if mode == "full":
            _check((run_dir / "dna.json").exists(), "analysis has no dna.json")
            canon_args += f" --canon {run_dir / 'dna.json'}"
        else:
            canon_args += f" --transcripts {run_dir / 'manifest.json'}"
            has_scripts = any((d / "episodes").glob("ep*_v*.*")) or (d / "final").exists()
            if has_scripts:
                job.step("diff", "running")
                out = run_dir / "script_diff.json"
                await analyze.run_script(job, ["python3", str(config.SKILLS / "continue-series" / "_script_diff.py"),
                                              "--session", str(d), "--manifest", str(run_dir / "manifest.json"),
                                              "--produced", str(k), "--out", str(out)])
                canon_args += f" --diff {out}"
                job.step("diff", "done")

    if p.get("update_skill") and run_dir and (run_dir / "dna.json").exists():
        p["update"] = True
        await create_skill(job)

    inp = json.loads((d / "input.json").read_text()) if (d / "input.json").exists() else {}
    inp.update({"produced_upto": k, "episodes": k + m})
    inp.setdefault("continuations", []).append({
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "canon_mode": mode,
        "canon_run": str(run_dir) if run_dir else None, "produced_upto": k, "new_episodes": m,
        "direction": p["direction"]})
    n = len(inp["continuations"])
    extra = ""
    if p.get("idea", "").strip():
        (d / f"continue_idea_{n}.md").write_text(p["idea"].strip())
        extra += f" --idea-file {d / f'continue_idea_{n}.md'}"
    if p.get("notes", "").strip():
        (d / f"production_notes_{n}.md").write_text(p["notes"].strip())
        extra += f" --notes {d / f'production_notes_{n}.md'}"
    (d / "input.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False))

    before = {k_: len(list(d.glob(f"{k_}_v*.md"))) for k_ in ("canon", "outline")}
    job.step("continue", "running")
    await _claude(job, (
        f"/continue-series --session {d} {canon_args} --style write-series-{slug} "
        f"--produced {k} --direction {p['direction']} --new-episodes {m}{extra}\n\n"
        "Run non-interactively: do not ask questions; state assumptions in canon_vN.json." + UI_NOTE),
        "continue", 5400)
    after = {k_: len(list(d.glob(f"{k_}_v*.md"))) for k_ in ("canon", "outline")}
    _check(after["canon"] > before["canon"], "canon report was not written")
    _check(after["outline"] > before["outline"], "continuation outline was not written")
    job.step("continue", "done")
    await enforce_story_contract(job, d, "outline")
    return {"slug": slug, "session_id": sid}


def export_screenplay(slug: str, session_id: str) -> Path:
    """One .md screenplay: bible + outline + every episode (final/ if approved, else latest drafts)."""
    st = session_state(slug, session_id)
    d = st["dir"]
    final = d / "final"
    if st["final_complete"]:
        bible = final / "bible.md" if (final / "bible.md").exists() else st["bible"]
        outline = final / "outline.md" if (final / "outline.md").exists() else st["outline"]
        episodes = sorted(final.glob("ep[0-9]*.md"), key=lambda p: int(re.match(r"ep(\d+)", p.name).group(1)))
        status = "FINAL"
    else:
        bible, outline, episodes = st["bible"], st["outline"], list(st["episodes"].values())
        status = "DRAFT"
    title = st["input"].get("title") or f"{slug} {session_id}"
    parts = [f"# {title}\n\n_Screenplay ({status}) — skill write-series-{slug}, session {session_id}, "
             f"exported {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_\n"]
    for heading, path in (("Series Bible", bible), ("Season Outline", outline)):
        if path and path.exists():
            parts.append(f"\n---\n\n## {heading}\n\n" + _demote(path.read_text()))
    if st["produced_upto"]:
        parts.append(f"\n---\n\n_Episodes 1–{st['produced_upto']} are produced videos (canon); "
                     "their on-screen version is summarized in the canon report._\n")
    if episodes:
        parts.append("\n---\n\n## Episodes\n")
        for ep in episodes:
            parts.append("\n" + _demote(ep.read_text(), 2) + "\n")
    if st["canon"]:
        parts.append("\n---\n\n## Appendix: produced episodes vs scripts (canon)\n\n" + _demote(st["canon"].read_text()))
    out = d / f"screenplay_{status.lower()}.md"
    out.write_text("".join(parts))
    return out


def _demote(md: str, levels: int = 1) -> str:
    """Shift headings down so the combined file keeps one H1."""
    return re.sub(r"^(#{1,5}) ", lambda m: "#" * min(6, len(m.group(1)) + levels) + " ", md, flags=re.M)
