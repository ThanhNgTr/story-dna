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
from datetime import datetime, timezone
from pathlib import Path

from . import assets as asset_images


def prompts_file(session: Path, n: int) -> Path | None:
    p = session / "final" / "shots" / f"ep{n:02d}" / "prompts.json"
    return p if p.exists() else None


def is_clip_format(pf: Path) -> bool:
    """10-15s clips (one generation, timed cuts inside). Older prompts were one per 1-5s shot."""
    try:
        return json.loads(pf.read_text(encoding="utf-8")).get("unit") == "clip"
    except (OSError, json.JSONDecodeError):
        return False


def prompts_stale(session: Path, n: int) -> bool:
    """Prompts must be made again: built from an older final/epNN.json or final/assets.json (finalized again
    since), or in the old one-prompt-per-1-5s-shot format."""
    p = prompts_file(session, n)
    if not p:
        return False
    if not is_clip_format(p):
        return True
    srcs = [f for f in (session / "final" / f"ep{n:02d}.json", session / "final" / "assets.json") if f.exists()]
    return bool(srcs and max(f.stat().st_mtime for f in srcs) > p.stat().st_mtime + 1)


def prompts_outdated(session: Path, n: int) -> bool:
    """Clip prompts in an older prompt_format (no opening/closing state, guard block, Veo parts): still usable,
    but worth remaking with the current skill."""
    p = prompts_file(session, n)
    if not p or not is_clip_format(p):
        return False
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("prompt_format") or 1) < PROMPT_FORMAT
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return False


def _clip_lines(s: dict) -> list[tuple[float, float, dict]]:
    """(start, end, line) for subtitles: the line's own times when given, else the clip's time shared evenly."""
    start, end = float(s.get("start_sec", 0)), float(s.get("end_sec", 0))
    lines = [d for d in s.get("dialogue") or [] if d.get("line")]
    if lines and all(d.get("start_sec") is not None and d.get("end_sec") is not None for d in lines):
        return [(float(d["start_sec"]), float(d["end_sec"]), d) for d in lines]
    step = (end - start) / len(lines) if lines else 0
    return [(start + j * step, start + (j + 1) * step, d) for j, d in enumerate(lines)]


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


def prompts_view(session: Path, n: int) -> dict | None:
    """prompts.json for the web reader: every shot with its prompt, speaker names and the reference images
    it attaches (paths relative to assets/, as the image route serves them). None when not made yet."""
    pf = prompts_file(session, n)
    if not pf:
        return None
    data = json.loads(pf.read_text(encoding="utf-8"))
    approved = asset_images.approved_refs(session)
    names = _bible_names(session)
    assets = (session / "assets").resolve()
    shots = []
    for sh in data.get("shots") or []:
        refs = []
        for f in _shot_refs(session, sh, approved):
            f = f.resolve()
            if f.is_relative_to(assets):
                refs.append(str(f.relative_to(assets)))
        shots.append({**{k: sh.get(k) for k in ("shot_number", "scene", "start_sec", "end_sec", "duration_sec",
                                                 "action", "dialogue", "camera", "sfx", "loc_id", "video_prompt",
                                                 "continuity_in", "opening_state", "closing_state", "performance")},
                      "on_screen_text": sh.get("on_screen_text") or [], "veo_parts": sh.get("veo_parts") or [],
                      "cuts": sh.get("cuts") or [],
                      "characters": [{"id": c, "name": names.get(c, c)} for c in sh.get("characters") or []],
                      "pace_warning": sh.get("pace_warning") or [], "refs": refs})
    return {"unit": "clip" if data.get("unit") == "clip" else "shot",
            "aspect_ratio": data.get("aspect_ratio"), "total_duration_sec": data.get("total_duration_sec"),
            "style_suffix": data.get("style_suffix"), "names": names, "stale": prompts_stale(session, n),
            "check": dict(zip(("errors", "warnings"), check_clips(session, n))) if data.get("unit") == "clip" else None,
            "built_at": datetime.fromtimestamp(pf.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "shots": shots}


CLIP_MAX_SEC = 15.5  # 15s + rounding
VEO_MAX_SEC = 8.25   # Veo 3.1 / Flow: 8s per generation + rounding
MAX_CUTS = 5         # timed cuts a video model executes reliably in one generation
EPS = 0.25           # seconds of overlap that do not count (rounded timecodes)
PROMPT_FORMAT = 2    # opening/closing state, performance, guard block, veo_parts
PROMPT_MARKERS = ("Opening:", "Ending:", "No subtitles")


def _check_prompt(tag: str, prompt: str) -> list[str]:
    missing = [m for m in PROMPT_MARKERS if m not in (prompt or "")]
    return [f"{tag}: prompt has no {', '.join(missing)} (skill Step 5 prompt layout)"] if missing else []


LINE_TAGS = {"speaks": "SPEAKS (lip-synced)", "voiceover": "VOICE-OVER", "offscreen": "OFF-SCREEN VOICE"}


def line_mode(d: dict, on_screen) -> str:
    """speaks (on screen, lip-synced) | voiceover (narration / inner thought, no lips move) | offscreen."""
    if d.get("mode") in LINE_TAGS:
        return d["mode"]
    if d.get("voiceover"):
        return "voiceover"
    return "speaks" if d.get("character") in on_screen else "offscreen"


def dialogue_tag_warnings(tag: str, prompt: str, lines: list[dict], on_screen) -> list[str]:
    """Every line must be quoted word for word in the prompt, and the nearest line tag before it must be the
    one of its mode: video models otherwise lip-sync inner thoughts and give lines to the wrong person."""
    out, pos = [], 0
    prompt = (prompt or "").replace("“", '"').replace("”", '"')
    for d in lines:
        text = (d.get("line") or "").strip()
        if not text:
            continue
        i = prompt.find(f'"{text}"', pos)
        if i < 0:
            out.append(f'{tag}: line not quoted word for word: "{text[:40]}"')
            continue
        mode = line_mode(d, on_screen)
        if d.get("voiceover") and mode != "voiceover":
            out.append(f'{tag}: "{text[:30]}" is a voice-over in the script but mode is {mode}')
        if mode == "speaks" and d.get("character") not in on_screen:
            out.append(f'{tag}: "{text[:30]}" is lip-synced but its speaker is not in the clip')
        before = prompt[pos:i]
        last = max(LINE_TAGS.values(), key=lambda t: before.rfind(t))
        if before.rfind(last) < 0:
            out.append(f'{tag}: "{text[:30]}" has no {LINE_TAGS[mode]} tag before it')
        elif last != LINE_TAGS[mode]:
            out.append(f'{tag}: "{text[:30]}" is tagged {last}, should be {LINE_TAGS[mode]}')
        pos = i + len(text) + 2
    return out


SHOT_RE = re.compile(r"Shot\s+\d+\s*\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s\)")
LINE_TIME_RE = re.compile(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)s\s*[:;][^\"]{0,80}\"")
SPEECH_INVITES = re.compile(r"as if to (?:ask|speak|say|talk)|about to (?:speak|say|ask)|opens? (?:his|her) mouth to", re.I)
MAX_SYL_PER_SEC = 5.0  # vi-dialogue.md "Speech rate"


def shot_dialogue_warnings(tag: str, prompt: str) -> list[str]:
    """Inside one prompt: a shot that says "No dialogue" while a timed line overlaps it (an L-cut the prompt
    contradicts), and actions that invite speech while a voice-over plays."""
    prompt = (prompt or "").replace("“", '"').replace("”", '"')
    shots = list(SHOT_RE.finditer(prompt))
    lines = [(float(m.group(1)), float(m.group(2))) for m in LINE_TIME_RE.finditer(prompt)]
    out = []
    for k, m in enumerate(shots):
        a, b = float(m.group(1)), float(m.group(2))
        body = prompt[m.end(): shots[k + 1].start() if k + 1 < len(shots) else len(prompt)]
        if "No dialogue" in body and any(min(b, l1) - max(a, l0) > EPS for l0, l1 in lines):
            out.append(f"{tag}: shot {a}-{b}s says \"No dialogue\" but a line runs over it "
                       "(write \"... voice-over continues over this shot\")")
        if "VOICE-OVER" in body and SPEECH_INVITES.search(body):
            out.append(f"{tag}: shot {a}-{b}s has a voice-over and an action that invites speech "
                       f"(\"{SPEECH_INVITES.search(body).group(0)}\")")
    return out


def pace_warnings(tag: str, lines: list[dict]) -> list[str]:
    out = []
    for d in lines:
        s0, s1, text = d.get("start_sec"), d.get("end_sec"), (d.get("line") or "").strip()
        if s0 is None or s1 is None or not text or float(s1) - float(s0) <= 0:
            continue
        n = len(re.findall(r"\w+", text))
        rate = n / (float(s1) - float(s0))
        if rate > MAX_SYL_PER_SEC + 0.05:
            out.append(f'{tag}: "{text[:30]}" {n} syllables in {float(s1) - float(s0):.1f}s = {rate:.1f}/s '
                       f"(max {MAX_SYL_PER_SEC}): shorten with /dialogue-polish")
    return out


def _fold(text: str) -> str:
    """Lower case without Vietnamese marks: 'Ông Hữu' and 'Mr. Huu' both contain 'huu'."""
    text = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def flow_warnings(tag: str, part: dict, names: dict[str, str]) -> list[str]:
    """Google Flow refused a personal name + a detailed face + several portrait refs, and accepted a role
    label + a short look + one portrait: warn on names outside quoted dialogue and on >1 character image."""
    out = []
    spoken_removed = _fold(re.sub(r'"[^"]*"|“[^”]*”', " ", part.get("video_prompt") or ""))
    found = sorted({n for n in names.values() for w in [_fold(n).split()[-1]] if len(w) >= 2
                    and re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", spoken_removed)})
    if found:
        out.append(f"{tag}: names outside dialogue ({', '.join(found)}): use the role labels (flow_labels)")
    faces = [r for r in part.get("refs") or [] if "characters/" in r]
    if len(faces) > 1:
        out.append(f"{tag}: {len(faces)} character images, Flow accepts one (keep the main subject)")
    return out


def _check_veo_parts(tag: str, c: dict, a: float, b: float) -> list[str]:
    """Every clip carries veo_parts (the Flow / Veo 3.1 version): contiguous, cover the clip, <= 8s each,
    split on cut boundaries and never inside a dialogue line."""
    parts = c.get("veo_parts") or []
    if not parts:
        return [f"{tag}: no veo_parts (the Google Flow / Veo version, one part per 8s at most)"]
    errors, prev = [], a
    cut_ends = {round(float(x.get("end_sec", 0)), 2) for x in c.get("cuts") or []}
    for part in parts:
        p0, p1 = float(part.get("start_sec", 0)), float(part.get("end_sec", 0))
        ptag = f"{tag} veo part {part.get('part')} [{p0}-{p1}]"
        if p1 - p0 > VEO_MAX_SEC:
            errors.append(f"{ptag}: {p1 - p0:.1f}s, max 8s")
        if abs(p0 - prev) > EPS:
            errors.append(f"{ptag}: starts at {p0}, previous part ended at {prev}")
        if p1 < b - EPS and cut_ends and not any(abs(p1 - e) <= EPS for e in cut_ends):
            errors.append(f"{ptag}: ends inside a cut (split only at cut boundaries)")
        for d in c.get("dialogue") or []:
            s0, s1 = d.get("start_sec"), d.get("end_sec")
            if s0 is not None and s1 is not None and float(s0) < p1 - EPS < float(s1) - EPS and p1 < b - EPS:
                errors.append(f"{ptag}: splits the line {str(d.get('line'))[:40]}")
        errors += _check_prompt(ptag, part.get("video_prompt", ""))
        prev = p1
    if abs(prev - b) > EPS:
        errors.append(f"{tag}: veo_parts end at {prev}, clip ends at {b}")
    return errors


def check_clips(session: Path, n: int) -> tuple[list[str], list[str]]:
    """(errors, warnings) for final/shots/epNN/prompts.json in clip format, against final/epNN.json:
    each clip inside ONE scene (one place, one time: two conversations in two places never share a video),
    at most 15s, clips contiguous over the episode, every dialogue line timed inside its clip; format 2 also:
    Opening / Ending / guard block in every prompt and valid veo_parts (Veo makes 8s at most)."""
    pf = prompts_file(session, n)
    if not pf:
        return [f"ep{n:02d}: no prompts.json"], []
    data = json.loads(pf.read_text(encoding="utf-8"))
    if data.get("unit") != "clip":
        return [f'ep{n:02d}: prompts.json is not "unit": "clip" (old one-prompt-per-shot format)'], []
    ep_f = session / "final" / f"ep{n:02d}.json"
    scenes = json.loads(ep_f.read_text(encoding="utf-8")).get("scenes", []) if ep_f.exists() else []
    errors, warns = [], []
    clips = data.get("shots") or []
    fmt2 = int(data.get("prompt_format") or 1) >= PROMPT_FORMAT
    names = _bible_names(session)
    if clips and not fmt2:
        warns.append("older prompt format (no opening/closing state, guard block or Veo parts): remake the prompts")
    prev_end = 0.0
    for c in clips:
        no, a, b = c.get("shot_number"), float(c.get("start_sec", 0)), float(c.get("end_sec", 0))
        tag = f"clip {no} [{a}-{b}]"
        if b - a > CLIP_MAX_SEC:
            errors.append(f"{tag}: {b - a:.1f}s, max 15s")
        if b - a < 4 and len(clips) > 1:
            warns.append(f"{tag}: only {b - a:.1f}s")
        if abs(a - prev_end) > EPS:
            errors.append(f"{tag}: starts at {a}, previous clip ended at {prev_end} (clips must be contiguous)")
        if len(c.get("cuts") or []) > MAX_CUTS:
            warns.append(f"{tag}: {len(c['cuts'])} cuts, at most {MAX_CUTS} per generation (merge cuts)")
        if fmt2:
            errors += _check_prompt(tag, c.get("video_prompt", ""))
            errors += [f"{tag}: no {k}" for k in ("opening_state", "closing_state") if not c.get(k)]
            errors += _check_veo_parts(tag, c, a, b)
            on_screen = set(c.get("characters") or [])
            lines = sorted(c.get("dialogue") or [], key=lambda d: float(d.get("start_sec") or 0))
            if lines and "Voices:" not in (c.get("video_prompt") or ""):
                warns.append(f"{tag}: no Voices: line (one voice per speaker)")
            warns += dialogue_tag_warnings(tag, c.get("video_prompt", ""), lines, on_screen)
            warns += shot_dialogue_warnings(tag, c.get("video_prompt", ""))
            warns += pace_warnings(tag, lines)
            for vp in c.get("veo_parts") or []:
                ptag = f"{tag} veo part {vp.get('part')}"
                warns += flow_warnings(ptag, vp, names)
                p0, p1 = float(vp.get("start_sec", 0)), float(vp.get("end_sec", 0))
                inside = [d for d in lines if p0 - EPS <= float(d.get("start_sec") or 0) < p1 - EPS]
                warns += dialogue_tag_warnings(ptag, vp.get("video_prompt", ""), inside, on_screen)
                warns += shot_dialogue_warnings(ptag, vp.get("video_prompt", ""))
        prev_end = b
        inside = [sc for sc in scenes
                  if min(b, float(sc.get("end_sec", 0))) - max(a, float(sc.get("start_sec", 0))) > EPS]
        if len(inside) > 1:
            where = "; ".join(f"{sc.get('id')} {sc.get('loc_id') or ''} {sc.get('heading') or sc.get('location') or ''}".strip()
                              for sc in inside)
            errors.append(f"{tag}: spans {len(inside)} scenes ({where}); split at the scene boundary")
        elif inside and c.get("scene") and c["scene"] != inside[0].get("id"):
            warns.append(f"{tag}: labelled {c['scene']} but its time is in {inside[0].get('id')}")
        for d in c.get("dialogue") or []:
            s0, s1 = d.get("start_sec"), d.get("end_sec")
            if s0 is None or s1 is None:
                errors.append(f"{tag}: line without start/end time: {str(d.get('line'))[:40]}")
            elif float(s0) < a - EPS or float(s1) > b + EPS:
                errors.append(f"{tag}: line {s0}-{s1} is outside the clip: {str(d.get('line'))[:40]}")
    total = float(data.get("total_duration_sec") or (scenes[-1].get("end_sec") if scenes else prev_end) or 0)
    if clips and abs(prev_end - total) > 0.5:
        errors.append(f"clips end at {prev_end}, episode is {total}s")
    return errors, warns


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
    clip = data.get("unit") == "clip"
    unit, unit_up, txt_dir = ("clip", "CLIP", "prompts") if clip else ("shot", "SHOT", "shots")

    refs: dict[Path, str] = {}  # source image -> name inside refs/
    shot_refs: list[list[str]] = []
    part_refs: dict[tuple[int, int], list[str]] = {}  # (clip index, part) -> names inside refs/
    missing_refs = 0
    for s in shots:
        files = _shot_refs(session, s, approved)
        missing_refs += not files
        for f in files:
            refs.setdefault(f, _ref_name(f, names))
        shot_refs.append([refs[f] for f in files])
        for vp in s.get("veo_parts") or []:
            found = [f for f in _shot_refs(session, {"refs": vp.get("refs") or []}, {}) if f.is_file()]
            for f in found:
                refs.setdefault(f, _ref_name(f, names))
            part_refs[(len(shot_refs), vp.get("part"))] = [refs[f] for f in found]

    tmp = Path(tempfile.mkstemp(suffix=".zip", prefix=f"{root}_")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        def text(name: str, body: str):
            z.writestr(f"{root}/{name}", body)

        edit = io.StringIO()
        w = csv.writer(edit)
        w.writerow([unit, "clip_file", "start", "end", "duration_sec", "characters", "dialogue", "sfx", "camera", "refs"])
        srt, k = [], 0
        for i, s in enumerate(shots, 1):
            no = int(s.get("shot_number") or i)
            start, end = float(s.get("start_sec", 0)), float(s.get("end_sec", 0))
            dur = s.get("duration_sec") or round(end - start, 2)
            chars = ", ".join(f"{names.get(c) or c} ({c})" if names.get(c) else c for c in s.get("characters") or [])
            timed = _clip_lines(s)
            lines = [d for _, _, d in timed]
            said = "\n".join(f"  [{_ts(a)}] {names.get(d.get('character')) or d.get('character')}"
                             + {"voiceover": " (VO)", "offscreen": " (ngoài khung)"}.get(
                                 line_mode(d, set(s.get("characters") or [])), "") + f": \"{d['line']}\""
                             + (f" ({d['delivery']})" if d.get("delivery") else "") for a, _, d in timed)
            cuts = "\n".join(f"  {c.get('cut', j)}. [{_ts(c.get('start_sec', 0))}-{_ts(c.get('end_sec', 0))}] "
                              f"{c.get('camera', '')}: {c.get('action', '')}"
                              for j, c in enumerate(s.get("cuts") or [], 1))
            ref_list = "\n".join(f"  {j}. refs/{r}" for j, r in enumerate(shot_refs[i - 1], 1)) or \
                "  (chưa có ảnh đã duyệt: chỉ dùng prompt)"
            text(f"{txt_dir}/{unit}_{no:02d}.txt",
                 f"{unit_up} {no:02d}   [{_ts(start)}-{_ts(end)}]   {dur}s   {aspect}\n\n"
                 f"Nhân vật: {chars or '-'}\n"
                 f"Hành động: {s.get('action', '')}\n"
                 + (f"Các cảnh cắt trong clip:\n{cuts}\n" if cuts else "")
                 + (f"Nối tiếp clip trước: {s['continuity_in']}\n" if s.get("continuity_in") else "")
                 + f"Thoại:\n{said or '  (không thoại)'}\n"
                 f"Âm thanh: {s.get('sfx', '')}\n"
                 f"Máy quay: {s.get('camera', '')}\n\n"
                 f"Ảnh tham chiếu (upload theo thứ tự):\n{ref_list}\n\n"
                 f"Lưu clip thành: clips/{unit}_{no:02d}.mp4\n\n"
                 + (f"Khung đầu: {s['opening_state']}\nKhung cuối: {s['closing_state']}\n"
                    if s.get("opening_state") else "")
                 + (f"Diễn xuất: {s['performance']}\n" if s.get("performance") else "")
                 + f"\nPROMPT (Seedance 2 / Kling, {dur}s, copy nguyên văn):\n{s.get('video_prompt', '')}\n"
                 + "".join(f"\nPROMPT VEO 3.1 / FLOW phần {vp.get('part')} [{_ts(vp.get('start_sec', 0))}-"
                           f"{_ts(vp.get('end_sec', 0))}] (lưu thành clips/{unit}_{no:02d}_{vp.get('part')}.mp4)\n"
                           f"Ảnh cho phần này (chỉ những ảnh này): "
                           f"{', '.join('refs/' + r for r in part_refs.get((i, vp.get('part')), [])) or 'không'}\n"
                           f"{vp.get('video_prompt', '')}\n" for vp in s.get("veo_parts") or []))
            w.writerow([no, f"{unit}_{no:02d}.mp4", _ts(start), _ts(end), dur, chars,
                        " | ".join(f"{names.get(d.get('character')) or d.get('character')}: {d['line']}" for d in lines),
                        s.get("sfx", ""), s.get("camera", ""), " ".join(shot_refs[i - 1])])
            for a, b, d in timed:
                k += 1
                who = names.get(d.get("character")) or d.get("character") or ""
                tag = f"{who} (VO): " if d.get("voiceover") else ""
                srt.append(f"{k}\n{_ts(a, True)} --> {_ts(b, True)}\n{tag}{d['line']}\n")
        text("edit_list.csv", "\ufeff" + edit.getvalue())  # BOM: Excel opens UTF-8 Vietnamese correctly
        text("subtitles.srt", "\n".join(srt))
        text("clips/DAT_CLIP_VAO_DAY.txt", f"Lưu video của từng {unit} ở đây: {unit}_01.mp4, {unit}_02.mp4, ...\n")
        for f in ("prompts.md", "prompts.json", "shotlist.md", "shotlist.json"):
            if (pf.parent / f).exists():
                z.write(pf.parent / f, f"{root}/{f}")
        for src, name in refs.items():
            z.write(src, f"{root}/refs/{name}", compress_type=zipfile.ZIP_STORED)  # png/jpg: already compressed
        total = shots[-1].get("end_sec") if shots else 0
        text("HUONG_DAN.txt",
             f"{title + ' — ' if title else ''}Tập {n:02d}: {ep_title}\n"
             f"{len(shots)} {unit}, {total}s, khung {aspect}. {len(refs)} ảnh tham chiếu.\n"
             + ("Mỗi clip 10-15s là MỘT lần tạo video: prompt đã ghi sẵn các cảnh cắt bên trong, nên nhân vật,\n"
                "trang phục và ánh sáng giữ nguyên trong cả đoạn hội thoại.\n" if clip else "") + "\n"
             f"Mỗi {unit}:\n"
             f"  1. Mở {txt_dir}/{unit}_XX.txt.\n"
             "  2. Upload các ảnh trong mục 'Ảnh tham chiếu' (thư mục refs/) theo thứ tự.\n"
             "  3. Copy PROMPT dán vào ô prompt; đặt thời lượng và khung hình như dòng đầu file.\n"
             f"  4. Tải video về, lưu thành clips/{unit}_XX.mp4.\n\n"
             "Dựng video:\n"
             f"  - edit_list.csv: thứ tự {unit}, thời điểm, thoại (mở bằng Excel / Google Sheets).\n"
             f"  - Ghép clips/{unit}_01.mp4, {unit}_02.mp4, ... theo thứ tự tên file.\n"
             "  - subtitles.srt: phụ đề thoại, khớp thời gian khi các clip đúng thời lượng.\n\n"
             "Prompt bằng tiếng Anh (cho model video); thoại giữ nguyên ngôn ngữ kịch bản.\n"
             "Seedance 2 / Kling: dùng PROMPT chính (một clip tối đa 15s) với mọi ảnh tham chiếu của clip.\n"
             "Veo 3.1 / Google Flow (tối đa 8s): dùng các 'PROMPT VEO phần 1, 2...' và CHỈ upload ảnh ghi ở phần đó\n"
             "  (tối đa 1 ảnh nhân vật; gọi nhân vật bằng vai, không tên riêng, để Flow không chặn vì 'người nổi tiếng').\n"
             + ("\nCẢNH BÁO: prompt kiểu cũ (mỗi shot 1-5s một video, dễ lệch nhân vật). Tạo lại prompt video (clip 10-15s).\n"
                if not clip else
                "\nCẢNH BÁO: prompt được tạo từ bản kịch bản cũ hơn bản chốt hiện tại. Tạo lại prompt video trước khi quay.\n"
                if prompts_stale(session, n) else "")
             + (f"\nLưu ý: {missing_refs} {unit} chưa có ảnh tham chiếu đã duyệt (duyệt ảnh ở mục Ngoại hình rồi tải lại).\n"
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
    eps = [n for n in eps if (final / f"ep{n:02d}.md").exists() and (p.get("force") or not prompts_file(d, n) or prompts_stale(d, n)
                                                          or prompts_outdated(d, n))]
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
                                   f"prompts.json/.md into {final / 'shots' / f'ep{n:02d}'}/. prompts.json is "
                                   '"unit": "clip", "prompt_format": 2: one prompt per 10-15s clip, at most 5 timed '
                                   "cuts, a start/end time on every dialogue line, opening/closing state, "
                                   "performance, the Rules guard block, and veo_parts for clips over 8s "
                                   "(skill Step 5); replace any older "
                                   "per-shot prompts.json." + UI_NOTE,
                              f"ep{n:02d}", 3600)
            except RuntimeError as e:
                job.log(f"[ep{n:02d}] {e}")
            if prompts_file(d, n):
                errs, warns = check_clips(d, n)
                for m in errs + warns:
                    job.log(f"[ep{n:02d}] {'ERROR' if m in errs else 'WARN'} {m}")
            (done if prompts_file(d, n) else failed).append(n)
            job.step("shotlist", "running", total=len(eps), done=len(done), failed=len(failed))

    await asyncio.gather(*(one(n) for n in eps))
    job.step("shotlist", "done" if not failed else "failed", total=len(eps), done=len(done), failed=len(failed))
    if not done:
        raise RuntimeError(f"không tạo được prompt cho tập {failed}")
    return {"slug": p["slug"], "session_id": p["session_id"], "episodes": sorted(done), "failed": sorted(failed)}


if __name__ == "__main__":
    # python3 -m app.pipeline.package check <session-dir> <episode>
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "check":
        errs, warns = check_clips(Path(sys.argv[2]), int(sys.argv[3]))
        for m in warns:
            print("WARN ", m)
        for m in errs:
            print("ERROR", m)
        print(f"check ep{int(sys.argv[3]):02d}: {len(errs)} errors, {len(warns)} warnings")
        sys.exit(1 if errs else 0)
    print("usage: python3 -m app.pipeline.package check <session-dir> <episode>")
    sys.exit(2)
