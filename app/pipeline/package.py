"""Per-episode production package (zip) for video tools such as Higgsfield.

Input: final/shots/epNN/prompts.json from /script-to-shotlist + approved reference images.
Zip layout (one folder per episode):
  HUONG_DAN.txt          how to use the package
  shots/shot_01.txt      prompt + duration + dialogue + which refs/ images to upload, in order
  refs/                  every approved reference image used by the episode, once
  clips/                 empty: save each generated clip as shot_01.mp4, shot_02.mp4, ...
  edit_list.csv          shot order and timing for the editor
  subtitles.srt          dialogue timed on the shots
  prompts.md/.json, shotlist.md/.json   originals from /script-to-shotlist
"""

from __future__ import annotations

import csv
import io
import json
import re
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from . import assets as asset_images


def prompts_file(session: Path, n: int) -> Path | None:
    p = session / "final" / "shots" / f"ep{n:02d}" / "prompts.json"
    return p if p.exists() else None


def _ascii(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()[:40]


def _ts(sec: float, srt: bool = False) -> str:
    ms = int(round(float(sec) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}" if srt else f"{m:02d}:{s:02d}"


def _shot_refs(session: Path, shot: dict, approved: dict[str, str]) -> list[Path]:
    """Images to attach: the shot's own refs, else approved images for its characters/outfits, location, props."""
    out: list[Path] = []
    for r in shot.get("refs") or []:
        for p in (session / r, session / "assets" / r):
            if p.is_file():
                out.append(p)
                break
    if out:
        return out
    outfits = shot.get("outfits") or {}
    keys = [outfits[c] if outfits.get(c) in approved else c for c in shot.get("characters") or []]
    lid = shot.get("loc_id")
    if shot.get("variant_id"):
        keys.append(shot["variant_id"])
    elif lid:
        keys += [k for k in approved if k.startswith(f"{lid}_")][:1]
    keys += shot.get("props") or []
    return [session / "assets" / approved[k] for k in keys if k in approved]


def _bible_names(session: Path) -> dict[str, str]:
    bibles = sorted(session.glob("bible_v*.json"), key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
    src = session / "final" / "bible.json" if (session / "final" / "bible.json").exists() else (bibles[-1] if bibles else None)
    try:
        b = json.loads(src.read_text(encoding="utf-8")) if src else {}
    except (OSError, json.JSONDecodeError):
        return {}
    return {c["character_id"]: c.get("name", "") for c in b.get("cast") or b.get("characters") or []
            if isinstance(c, dict) and c.get("character_id")}


def _ref_name(path: Path, names: dict[str, str]) -> str:
    """characters/char_01/char_01_sheet_v1.png -> char_01_vu_sheet_v1.png (readable, unique per source)."""
    stem = path.stem
    m = re.match(r"(char_\d+)", stem)
    if m and names.get(m.group(1)):
        stem = stem.replace(m.group(1), f"{m.group(1)}_{_ascii(names[m.group(1)])}", 1)
    return f"{stem}{path.suffix}"


def build_episode_package(session: Path, n: int, title: str = "") -> tuple[Path, str]:
    """Write the zip to a temp file. Returns (zip path, download file name)."""
    pf = prompts_file(session, n)
    if not pf:
        raise FileNotFoundError(f"ep{n:02d}: chưa có final/shots/ep{n:02d}/prompts.json (chạy /script-to-shotlist)")
    data = json.loads(pf.read_text(encoding="utf-8"))
    shots = data.get("shots") or []
    approved = asset_images.approved_refs(session)
    ep_json = session / "final" / f"ep{n:02d}.json"
    ep = json.loads(ep_json.read_text(encoding="utf-8")) if ep_json.exists() else {}
    names = _bible_names(session)
    names.update({cid: c["name"] for cid, c in (ep.get("characters") or {}).items() if (c or {}).get("name")})
    ep_title = ep.get("title") or data.get("title") or ""
    root = f"tap{n:02d}" + (f"_{_ascii(ep_title)}" if _ascii(ep_title) else "")
    aspect = data.get("aspect_ratio", "9:16")

    refs: dict[Path, str] = {}  # source image -> name inside refs/
    shot_refs: list[list[str]] = []
    missing_refs = 0
    for s in shots:
        files = _shot_refs(session, s, approved)
        missing_refs += not files
        for f in files:
            refs.setdefault(f, _ref_name(f, names))
        shot_refs.append([refs[f] for f in files])

    tmp = Path(tempfile.mkstemp(suffix=".zip", prefix=f"{root}_")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        def text(name: str, body: str):
            z.writestr(f"{root}/{name}", body)

        edit = io.StringIO()
        w = csv.writer(edit)
        w.writerow(["shot", "clip_file", "start", "end", "duration_sec", "characters", "dialogue", "sfx", "camera", "refs"])
        srt, k = [], 0
        for i, s in enumerate(shots, 1):
            no = int(s.get("shot_number") or i)
            start, end = float(s.get("start_sec", 0)), float(s.get("end_sec", 0))
            dur = s.get("duration_sec") or round(end - start, 2)
            chars = ", ".join(f"{names.get(c) or c} ({c})" if names.get(c) else c for c in s.get("characters") or [])
            lines = [d for d in s.get("dialogue") or [] if d.get("line")]
            said = "\n".join(f"  {names.get(d.get('character')) or d.get('character')}: \"{d['line']}\""
                             + (f" ({d['delivery']})" if d.get("delivery") else "") for d in lines)
            ref_list = "\n".join(f"  {j}. refs/{r}" for j, r in enumerate(shot_refs[i - 1], 1)) or \
                "  (chưa có ảnh đã duyệt: chỉ dùng prompt)"
            text(f"shots/shot_{no:02d}.txt",
                 f"SHOT {no:02d}   [{_ts(start)}-{_ts(end)}]   {dur}s   {aspect}\n\n"
                 f"Nhân vật: {chars or '-'}\n"
                 f"Hành động: {s.get('action', '')}\n"
                 f"Thoại:\n{said or '  (không thoại)'}\n"
                 f"Âm thanh: {s.get('sfx', '')}\n"
                 f"Máy quay: {s.get('camera', '')}\n\n"
                 f"Ảnh tham chiếu (upload theo thứ tự):\n{ref_list}\n\n"
                 f"Lưu clip thành: clips/shot_{no:02d}.mp4\n\n"
                 f"PROMPT (copy nguyên văn):\n{s.get('video_prompt', '')}\n")
            w.writerow([no, f"shot_{no:02d}.mp4", _ts(start), _ts(end), dur, chars,
                        " | ".join(f"{names.get(d.get('character')) or d.get('character')}: {d['line']}" for d in lines),
                        s.get("sfx", ""), s.get("camera", ""), " ".join(shot_refs[i - 1])])
            # Lines in one shot share its time evenly
            step = (end - start) / len(lines) if lines else 0
            for j, d in enumerate(lines):
                k += 1
                who = names.get(d.get("character")) or d.get("character") or ""
                tag = f"{who} (VO): " if d.get("voiceover") else ""
                srt.append(f"{k}\n{_ts(start + j * step, True)} --> {_ts(start + (j + 1) * step, True)}\n{tag}{d['line']}\n")
        text("edit_list.csv", "\ufeff" + edit.getvalue())  # BOM: Excel opens UTF-8 Vietnamese correctly
        text("subtitles.srt", "\n".join(srt))
        text("clips/DAT_CLIP_VAO_DAY.txt", "Lưu clip của từng shot ở đây: shot_01.mp4, shot_02.mp4, ...\n")
        for f in ("prompts.md", "prompts.json", "shotlist.md", "shotlist.json"):
            if (pf.parent / f).exists():
                z.write(pf.parent / f, f"{root}/{f}")
        for src, name in refs.items():
            z.write(src, f"{root}/refs/{name}", compress_type=zipfile.ZIP_STORED)  # png/jpg: already compressed
        total = shots[-1].get("end_sec") if shots else 0
        text("HUONG_DAN.txt",
             f"{title + ' — ' if title else ''}Tập {n:02d}: {ep_title}\n"
             f"{len(shots)} shot, {total}s, khung {aspect}. {len(refs)} ảnh tham chiếu.\n\n"
             "Mỗi shot:\n"
             "  1. Mở shots/shot_XX.txt.\n"
             "  2. Upload các ảnh trong mục 'Ảnh tham chiếu' (thư mục refs/) theo thứ tự.\n"
             "  3. Copy PROMPT dán vào ô prompt; đặt thời lượng và khung hình như dòng đầu file.\n"
             "  4. Tải clip về, lưu thành clips/shot_XX.mp4.\n\n"
             "Dựng video:\n"
             "  - edit_list.csv: thứ tự shot, thời điểm, thoại (mở bằng Excel / Google Sheets).\n"
             "  - Ghép clips/shot_01.mp4, shot_02.mp4, ... theo thứ tự tên file.\n"
             "  - subtitles.srt: phụ đề thoại, khớp thời gian khi các clip đúng thời lượng.\n\n"
             "Prompt bằng tiếng Anh (cho model video); thoại giữ nguyên ngôn ngữ kịch bản.\n"
             + (f"\nLưu ý: {missing_refs} shot chưa có ảnh tham chiếu đã duyệt (duyệt ảnh ở mục Ngoại hình rồi tải lại).\n"
                if missing_refs else ""))
    return tmp, f"{root}_higgsfield.zip"


async def run_shotlist_job(job) -> dict:
    """Web job: /script-to-shotlist for approved episodes that have no prompts yet (or the given ones)."""
    import asyncio

    from .. import config
    from .series import UI_NOTE, _claude, session_dir

    p = job.data["params"]
    d = session_dir(p["slug"], p["session_id"])
    final = d / "final"
    eps = [int(n) for n in p.get("episodes") or []] or sorted(
        int(m.group(1)) for f in final.glob("ep*.md") if (m := re.fullmatch(r"ep(\d+)\.md", f.name)))
    eps = [n for n in eps if (final / f"ep{n:02d}.md").exists() and (p.get("force") or not prompts_file(d, n))]
    if not eps:
        raise RuntimeError("không có tập nào cần tạo prompt (tập phải nằm trong final/: chốt season trước)")
    done, failed = [], []
    job.step("shotlist", "running", total=len(eps), done=0)
    slots = asyncio.Semaphore(config.CLAUDE_PARALLEL)

    async def one(n: int):
        async with slots:
            try:
                await _claude(job, f"/script-to-shotlist {final / f'ep{n:02d}.md'}\n\nRun non-interactively: do not ask "
                                   "questions. The episode is approved (final/). Write shotlist.json/.md and "
                                   f"prompts.json/.md into {final / 'shots' / f'ep{n:02d}'}/." + UI_NOTE,
                              f"ep{n:02d}", 3600)
            except RuntimeError as e:
                job.log(f"[ep{n:02d}] {e}")
            (done if prompts_file(d, n) else failed).append(n)
            job.step("shotlist", "running", total=len(eps), done=len(done), failed=len(failed))

    await asyncio.gather(*(one(n) for n in eps))
    job.step("shotlist", "done" if not failed else "failed", total=len(eps), done=len(done), failed=len(failed))
    if not done:
        raise RuntimeError(f"không tạo được prompt cho tập {failed}")
    return {"slug": p["slug"], "session_id": p["session_id"], "episodes": sorted(done), "failed": sorted(failed)}
