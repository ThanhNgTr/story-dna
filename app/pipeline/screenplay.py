"""Episode edits made in the web UI: manual edits (new version, no Claude) and review comments.

Manual edit: the UI sends the whole episode JSON; we write episodes/epNN_v(K+1).json + .md (rendered
in the skill's Output Format), lint it against the asset registry and log the round in
iterations.json. Never overwrites a version.

Comments: <session>/comments.json. Each pins a note to episode / scene / beat; "send" turns the open
ones into one /refine-skill feedback text with exact positions, and marks them as sent.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .. import config

HELD_SEC = 8.0


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _t(sec: float) -> str:
    """24.8 -> 00:24.8, 60 -> 01:00 (the skill's scene-heading format)."""
    m, s = divmod(round(float(sec), 1), 60)
    return f"{int(m):02d}:{int(s):02d}" if s == int(s) else f"{int(m):02d}:{s:04.1f}"


def _cell(text) -> str:
    return str(text or "").replace("|", "/").replace("\n", " ").strip() or "—"


def _speaker(ep: dict, cid: str) -> str:
    c = (ep.get("characters") or {}).get(cid) or {}
    name = c.get("name") or (ep.get("voices_without_character") or {}).get(cid) and "GIỌNG TRONG LOA" or cid
    return str(name).upper()


def _dialogue(ep: dict, beat: dict) -> str:
    parts = []
    for d in beat.get("dialogue") or []:
        who = "VO" if d.get("voiceover") else _speaker(ep, d.get("character", ""))
        delivery = f" ({d['delivery']})" if d.get("delivery") else ""
        parts.append(f'{who}{delivery}: "{d.get("line", "")}"')
    return "<br>".join(parts) or "—"


TIME_VI = {"day": "NGÀY", "night": "ĐÊM", "dawn": "BÌNH MINH", "dusk": "CHẠNG VẠNG", "morning": "SÁNG",
           "noon": "TRƯA", "afternoon": "CHIỀU", "evening": "TỐI"}


def _heading(sc: dict) -> str:
    """'INT. PLACE — ĐÊM': the scene heading of the skill's Output Format, time of day included."""
    head = sc.get("heading") or f"{sc.get('int_ext', '')}. {str(sc.get('location', '')).upper()}".strip(". ")
    tod = str(sc.get("time_of_day") or "").strip()
    word = TIME_VI.get(tod.lower(), tod.upper())
    if word and word.lower() not in head.lower():
        head = f"{head} — {word}"
    return head


def render_md(ep: dict) -> str:
    """Episode JSON -> the skill's Markdown screenplay (style skill "Output Format"): header, cast, one table
    per scene with its heading, IDs and props, then new assets, cliffhanger, ending and ledger."""
    head = [f"# EP{int(ep.get('episode', 0)):02d} — {ep.get('title', '')} ({ep.get('total_duration_sec', '?')}s)"]
    meta = [f"Logline: {ep.get('logline', '')}"]
    if ep.get("story_beats"):
        sb = ep["story_beats"]
        meta.append(f"Story beats: {sb if isinstance(sb, str) else '; '.join(map(str, sb))}")
    if ep.get("cliffhanger_type"):
        meta.append(f"Cliffhanger: {ep['cliffhanger_type']}")
    head.append(" | ".join(meta))
    cast = [f"{c.get('name', cid)} ({cid}) — {c.get('visual_signature')}"
            for cid, c in (ep.get("characters") or {}).items() if c.get("visual_signature")]
    out = head + ["", "Nhân vật: " + "; ".join(cast), ""] if cast else head + [""]
    for sc in ep.get("scenes", []):
        ids = ""
        if sc.get("loc_id") or sc.get("cast"):
            who = ", ".join(f"{c}:{o.removeprefix(c + '_')}" for c, o in (sc.get("cast") or {}).items())
            ids = "  {" + " · ".join(x for x in (sc.get("loc_id"), sc.get("variant_id"), who) if x) + "}"
        out.append(f"### {sc.get('id')} [{_t(sc.get('start_sec', 0))}-{_t(sc.get('end_sec', 0))}] {_heading(sc)}{ids}")
        if sc.get("props"):
            out.append("Props: " + ", ".join(map(str, sc["props"])))
        out += ["| Time | Shot | Action | Dialogue / VO | Camera | Light/Color | Sound |",
                "|---|---|---|---|---|---|---|"]
        for b in sc.get("beats", []):
            dur = float(b.get("end_sec", 0)) - float(b.get("start_sec", 0))
            shot = _cell(b.get("shot_size")) + (f" **[GIỮ {dur:.0f}s]**" if dur >= HELD_SEC else "")
            out.append(f"| {b.get('start_sec')}-{b.get('end_sec')} | {shot} | {_cell(b.get('action'))} | "
                       f"{_dialogue(ep, b)} | {_cell(b.get('camera'))} | {_cell(b.get('lighting_color'))} | {_cell(b.get('sound'))} |")
        out.append("")
    new_assets = [a for a in ep.get("new_assets") or [] if isinstance(a, dict)]
    if new_assets:
        out += ["**Tài sản mới đề xuất:** " + "; ".join(
            f"{a.get('id') or a.get('temp_id') or '?'} ({a.get('kind', '')}): {a.get('desc') or a.get('description') or ''}".strip()
            for a in new_assets), ""]
    if ep.get("cliffhanger"):
        kind = f" ({ep['cliffhanger_type']})" if ep.get("cliffhanger_type") else ""
        out += [f"**Cliffhanger{kind}:** {ep['cliffhanger']}", ""]
    end = ep.get("ending")
    if isinstance(end, dict) and end.get("type"):
        out += [f"**Kết ({end['type']}):** {end.get('central_question_answer') or end.get('what_happens') or ''}", ""]
    led = ep.get("ledger") or {}
    if led:
        fmt = lambda xs: ", ".join(map(str, xs)) if xs else "—"  # noqa: E731
        out.append(f"**Ledger:** mở {fmt(led.get('opened'))} | đầu mối {fmt(led.get('clues'))} | trả {fmt(led.get('answered'))}")
        out += [f"- {k}: {v}" for k, v in (ep.get("ledger_evidence") or {}).items()]
    return "\n".join(out).rstrip() + "\n"


def episode_versions(session: Path, n: int) -> list[Path]:
    files = [p for p in (session / "episodes").glob(f"ep{n:02d}_v*.json")
             if re.fullmatch(rf"ep{n:02d}_v\d+\.json", p.name)]
    return sorted(files, key=lambda p: int(re.search(r"_v(\d+)\.json$", p.name).group(1)))


def _validate(ep: dict, n: int) -> list[str]:
    errs = []
    if int(ep.get("episode", n)) != n:
        errs.append("episode number does not match")
    scenes = ep.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return errs + ["no scenes"]
    last = 0.0
    for sc in scenes:
        if not sc.get("id") or not isinstance(sc.get("beats"), list) or not sc["beats"]:
            errs.append(f"scene {sc.get('id')}: needs id and at least one beat")
            continue
        for b in sc["beats"]:
            s, e = float(b.get("start_sec", -1)), float(b.get("end_sec", -1))
            if not (0 <= s < e) or abs(s - last) > 0.05:
                errs.append(f"{sc['id']}: beat {s}-{e} breaks the timeline (expected start {last})")
            last = e
    return errs


def lint(session: Path, n: int) -> str | None:
    """Asset-registry lint for one episode, when the session has a registry."""
    if not any((session / "assets").glob("assets_v*.json")):
        return None
    script = config.SKILLS / "series-assets" / "_assets.py"
    r = subprocess.run([sys.executable, str(script), "lint", str(session), str(n)],
                       capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip()


def save_manual(session: Path, n: int, data: dict, base_version: int, note: str = "") -> dict:
    files = episode_versions(session, n)
    latest = int(re.search(r"_v(\d+)\.json$", files[-1].name).group(1)) if files else 0
    if base_version != latest:
        raise ValueError(f"Tập {n} vừa có phiên bản mới (v{latest}). Tải lại rồi sửa trên bản mới nhất.")
    errs = _validate(data, n)
    if errs:
        raise ValueError("Kịch bản không hợp lệ: " + "; ".join(errs[:5]))
    k = latest + 1
    data = {**data, "episode": n, "edited": {"by": "manual", "at": now(), "from_version": latest, "note": note}}
    out = session / "episodes" / f"ep{n:02d}_v{k}.json"
    if out.exists():
        raise ValueError(f"{out.name} đã tồn tại.")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    out.with_suffix(".md").write_text(render_md(data), encoding="utf-8")
    lint_out = lint(session, n)
    _log_round(session, "manual_edit", note or f"Sửa tay tập {n}", [f"episodes/{out.name}", f"episodes/{out.with_suffix('.md').name}"])
    return {"version": k, "file": f"episodes/{out.name}", "lint": lint_out}


def _log_round(session: Path, stage: str, text: str, files: list[str]):
    from . import iterations
    iterations.append(session, {"stage": stage, "feedback_raw": text,
                                "items": [{"text": text, "scope": "story", "target": stage, "change": text}],
                                "files_written": files, "status": "done"})


# ---------- comments ----------

def _comments_path(session: Path) -> Path:
    return session / "comments.json"


def load_comments(session: Path) -> list[dict]:
    p = _comments_path(session)
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("comments", []) if p.exists() else []
    except json.JSONDecodeError:
        return []


def _save_comments(session: Path, comments: list[dict]):
    p = _comments_path(session)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps({"comments": comments}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def add_comment(session: Path, c: dict) -> dict:
    comments = load_comments(session)
    item = {"id": uuid.uuid4().hex[:10], "episode": int(c["episode"]), "version": int(c.get("version") or 0),
            "scene": c.get("scene"), "beat": c.get("beat"), "time": c.get("time"), "quote": (c.get("quote") or "")[:300],
            "text": c["text"].strip(), "status": "open", "created_at": now()}
    comments.append(item)
    _save_comments(session, comments)
    return item


def update_comment(session: Path, cid: str, fields: dict) -> dict:
    comments = load_comments(session)
    for c in comments:
        if c["id"] == cid:
            if "text" in fields and fields["text"] is not None:
                c["text"] = fields["text"].strip()
            if fields.get("status") in ("open", "resolved"):
                c["status"] = fields["status"]
            c["updated_at"] = now()
            _save_comments(session, comments)
            return c
    raise KeyError(cid)


def delete_comment(session: Path, cid: str):
    comments = load_comments(session)
    left = [c for c in comments if c["id"] != cid]
    if len(left) == len(comments):
        raise KeyError(cid)
    _save_comments(session, left)


def feedback_from_comments(comments: list[dict], general: str = "") -> tuple[str, str]:
    """Open comments -> (feedback text for /refine-skill, target)."""
    eps = sorted({c["episode"] for c in comments})
    lines = []
    for c in sorted(comments, key=lambda c: (c["episode"], c.get("time") or 0)):
        where = [f"Tập {c['episode']}"]
        if c.get("scene"):
            where.append(c["scene"])
        if c.get("beat"):
            where.append(f"beat #{c['beat']}")
        if c.get("time") is not None:
            where.append(f"{float(c['time']):.1f}s")
        quote = f' (đoạn: "{c["quote"]}")' if c.get("quote") else ""
        lines.append(f"- {', '.join(where)}{quote}: {c['text']}")
    text = "Góp ý theo vị trí trong kịch bản:\n" + "\n".join(lines)
    if general.strip():
        text = general.strip() + "\n\n" + text
    target = f"ep{eps[0]:02d}" if len(eps) == 1 else "all_episodes"
    return text, target


def mark_sent(session: Path, ids: list[str], job_id: str):
    comments = load_comments(session)
    for c in comments:
        if c["id"] in ids:
            c["status"], c["sent_in_job"], c["sent_at"] = "sent", job_id, now()
    _save_comments(session, comments)
