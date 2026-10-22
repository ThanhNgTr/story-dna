"""Per-episode production packages (zip): Higgsfield (Seedance / Kling, 10-15s clips) below, and Google Flow
(Veo 3.1, one generation per veo part) in build_flow_package.

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
from . import seedance


def prompts_file(session: Path, n: int) -> Path | None:
    p = session / "final" / "shots" / f"ep{n:02d}" / "prompts.json"
    return p if p.exists() else None


def has_higgsfield(data: dict) -> bool:
    """prompts.json carries the 10-15s clip prompts (Higgsfield: Seedance / Kling). Files without `targets` are
    older ones that always had them; `"targets": ["flow"]` files have only the Flow parts."""
    return "higgsfield" in (data.get("targets") or ["higgsfield", "flow"])


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


DEFAULT_DIALOGUE_LANGUAGE = "en-US"  # spoken lines in video prompts, unless the bible's production_language says otherwise
VI_LETTERS = re.compile("[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.I)


def dialogue_language(session: Path) -> str:
    """Language of the spoken lines in the video prompts: bible `production_language`, else American English.
    The screenplay keeps its own language (the reading version)."""
    bibles = sorted(session.glob("bible_v*.json"), key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
    src = session / "final" / "bible.json" if (session / "final" / "bible.json").exists() else (bibles[-1] if bibles else None)
    try:
        lang = (json.loads(src.read_text(encoding="utf-8")).get("production_language") or "") if src else ""
    except (OSError, json.JSONDecodeError, AttributeError):
        lang = ""
    return lang.strip() or DEFAULT_DIALOGUE_LANGUAGE


def wrong_language_lines(data: dict, lang: str) -> list[str]:
    """Spoken lines of an English production still written in Vietnamese (prompts made before the language rule)."""
    if not lang.lower().startswith("en"):
        return []
    return [d.get("line") or "" for c in data.get("shots") or [] for d in c.get("dialogue") or []
            if VI_LETTERS.search(d.get("line") or "")]


def outdated_reasons(session: Path, n: int) -> list[str]:
    """Why clip prompts are worth remaking with the current skill (still usable): older prompt_format, dialogue not in
    the production language, Flow parts without their Seedance prompt."""
    p = prompts_file(session, n)
    if not p or not is_clip_format(p):
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        fmt = int(data.get("prompt_format") or 1)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return []
    out = []
    if fmt < PROMPT_FORMAT:
        out.append("định dạng cũ (Flow chưa giãn 6/8/10s, chưa có quy tắc trẻ em)")
    lang = dialogue_language(session)
    if wrong_language_lines(data, lang):
        out.append(f"thoại chưa phải tiếng Anh ({lang})")
    if any(not vp.get("seedance_prompt") for c in data.get("shots") or [] for vp in c.get("veo_parts") or []):
        out.append("chưa có prompt Seedance")
    return out


def prompts_outdated(session: Path, n: int) -> bool:
    return bool(outdated_reasons(session, n))


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


def current_ref(session: Path, ref: str) -> str | None:
    """A ref written into prompts.json -> the image to use NOW, relative to assets/: the newest approved image of the
    same registry item (an image made again after a refusal replaces the old one everywhere), None when that item
    has no approved image any more. An image built on a replaced face (outfit made from a rejected sheet) gives way to
    the current identity sheet. Files the image index does not know are kept as written."""
    index = asset_images.load_index(session)
    rel = ref.removeprefix("assets/")
    for item in index["items"].values():
        if any(i.get("file") == rel for i in item.get("images", [])):
            ok = [i for i in item.get("images", []) if i.get("status") == "approved"]
            if not ok:
                return None
            if asset_images.built_on_replaced(index, ok[-1]):
                return next((c for r in ok[-1]["refs"] if (c := asset_images.newest_approved(index, r))), None)
            return ok[-1]["file"]
    return rel


def _shot_refs(session: Path, shot: dict, approved: dict[str, str]) -> list[Path]:
    """Images to attach: the shot's own refs (each swapped for the newest approved image of its item), else approved
    images for its characters/outfits, location, props."""
    out: list[Path] = []
    dropped = False  # an item with no approved image left: attach nothing for it rather than guess
    for r in shot.get("refs") or []:
        cur = current_ref(session, r)
        if cur is None:
            dropped = True
            continue
        for p in (session / "assets" / cur, session / cur):
            if p.is_file() and p not in out:
                out.append(p)
                break
    if out or dropped:
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


def named_prompt(text: str, labels: dict[str, str], names: dict[str, str]) -> str:
    """Flow parts written with role labels ("the young worker") -> the character names. Tested 2026-10-15: the
    "famous people" refusals came from the idol-like face, not from names; names keep who-is-who clear."""
    for cid, label in sorted(labels.items(), key=lambda kv: -len(kv[1] or "")):
        if label and names.get(cid):
            text = re.sub(rf"(?<![\w-]){re.escape(label)}(?![\w-])", names[cid], text, flags=re.I)
    return text


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
    labels = data.get("flow_labels") or {}
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
                      "on_screen_text": sh.get("on_screen_text") or [],
                      "veo_parts": [{**vp, "refs": [c for r in vp.get("refs") or [] if (c := current_ref(session, r))],
                                     "video_prompt": named_prompt(vp.get("video_prompt") or "", labels, names),
                                     "continuity_in": named_prompt(vp.get("continuity_in") or "", labels, names)}
                                    for vp in sh.get("veo_parts") or []],
                      "cuts": sh.get("cuts") or [],
                      "characters": [{"id": c, "name": names.get(c, c)} for c in sh.get("characters") or []],
                      "pace_warning": sh.get("pace_warning") or [], "refs": refs})
    return {"unit": "clip" if data.get("unit") == "clip" else "shot",
            "aspect_ratio": data.get("aspect_ratio"), "total_duration_sec": data.get("total_duration_sec"),
            "style_suffix": data.get("style_suffix"), "names": names, "stale": prompts_stale(session, n),
            "targets": data.get("targets") or ["higgsfield", "flow"],
            "check": dict(zip(("errors", "warnings"), check_clips(session, n))) if data.get("unit") == "clip" else None,
            "built_at": datetime.fromtimestamp(pf.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "shots": shots}


CLIP_MAX_SEC = 15.5  # 15s + rounding
VEO_STEPS = (4, 6, 8, 10)  # lengths Google Flow accepts (s); the longest model step in use is 10s
VEO_TOLERANCE = 0.15   # a length this much over a step still uses that step
FLOW_STRETCH = 1.3     # a part of script time t is generated over ~1.3 t (4s -> 6s, 6s -> 8s): room to act and speak
FLOW_MAX_RATIO = 2.0   # generated / script length above this plays too slow
VEO_MAX_SEC = 8.25     # script time per part (generated up to 10s)
FLOW_MAX_REFS = 3      # images per Flow "Ingredients to Video" generation (characters first, then the location)
MAX_CUTS = 5         # timed cuts a video model executes reliably in one generation
EPS = 0.25           # seconds of overlap that do not count (rounded timecodes)
PROMPT_FORMAT = 4    # 2: opening/closing state, performance, guard block, veo_parts; 3: veo_parts[].duration_sec on a Flow
                     # step; 4: parts stretched (~1.3x, cuts and lines retimed over the whole step), minors rule
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


def flow_warnings(tag: str, part: dict, names: dict[str, str], minors: set[str] = frozenset()) -> list[str]:
    """Images Flow takes: warn on more images than Flow takes, and on a character on screen in the part with no
    image while a slot is free. (Names are fine: the "famous people" refusals came from an idol-like face.)"""
    out = []
    refs = part.get("refs") or []
    if len(refs) > FLOW_MAX_REFS:
        out.append(f"{tag}: {len(refs)} images, Flow takes {FLOW_MAX_REFS} (characters first, then the location)")
    elif len(refs) < FLOW_MAX_REFS:
        have = {m.group(1) for r in refs for m in [re.search(r"(char_\d+)", r)] if m and "characters/" in r}
        missing = [c for c in part.get("characters") or [] if c in names and c not in have and c not in minors]
        if missing:
            out.append(f"{tag}: on screen without an image ({', '.join(missing)}) while a slot is free")
    return out


# Flow refused a part with a 10-year-old ("harmful content involving minors"): body words for the child, bare feet and
# shorts, a man in a tank top and shorts, late night, a bed in the room, touching, sleeping side by side, a child photo.
MINOR_RISK = re.compile(
    r"\b(barefoot|bare (feet|legs|arms|shoulders|skin)|shorts|tank top|vest top|singlet|underwear|pajamas?|pyjamas?|"
    r"nightgown|swimsuit|skinny|slim|small and|petite|tiny body|lips|pouting|bed|bedroom|blanket|asleep|sleeping|sleeps|"
    r"lies down|lying|bath|bathing|shower|changing clothes|undress\w*|hug\w*|cuddl\w*|embrac\w*|kiss\w*|ruffl\w*|"
    r"strok\w*|caress\w*|pats? her|pats? his|on (his|her) lap|carries her|carries him|leans on|pressed against|"
    r"right beside|late night|midnight|alone with|"
    # an adult asleep beside the child, the child's mouth, a crying child (ep04 review after the first refusal)
    r"eyes closed|doz\w*|naps?|napping|stirs?|breathing|wakes?|waking|teeth|tears?|tearful|crying|cries|"
    r"red-rimmed|straw mat|sleeping mat)\b", re.I)
# ep06: a part with Na (10) twisting her phone strap beside her brother and his co-worker was refused 5 times (also in
# daylight); it passed with the child out of the frame. A device near the child, or 2+ adults in her part, is an error.
MINOR_DEVICE = re.compile(r"\b(phones?|smartphone|keypad|text(?:s|ing|ed)|text messages?|messag\w*|dial(?:s|ed|ing|led|ling)?|contacts list|tablet|laptop|"
                          r"computer)\b|(?<![-\w])(?<!on )(?<!off )screens?\b", re.I)


def minor_ids(session: Path) -> set[str]:
    """Characters under 18 in the asset registry (final/assets.json, else the latest assets_vN.json)."""
    reg = session / "final" / "assets.json"
    if not reg.exists():
        regs = sorted((session / "assets").glob("assets_v*.json"), key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
        reg = regs[-1] if regs else None
    try:
        chars = json.loads(reg.read_text(encoding="utf-8")).get("characters") or [] if reg else []
    except (OSError, json.JSONDecodeError):
        return set()
    out = set()
    for c in chars:
        age = c.get("age") if isinstance(c, dict) else None
        if isinstance(age, (int, float)) and age < 18 and c.get("char_id"):
            out.add(c["char_id"])
    return out


def minor_problems(tag: str, item: dict, minors: set[str]) -> list[str]:
    """A clip or Flow part with a character under 18 on screen: no photo of the child, no words Flow's minors filter
    reads as unsafe (body, bare skin, bed / sleep, touching, late night alone). Quoted dialogue is not checked."""
    kids = [c for c in item.get("characters") or [] if c in minors]
    if not kids:
        return []
    out = []
    photos = [r for r in item.get("refs") or [] if any(f"/{k}/" in r or f"/{k}_" in r for k in kids)]
    if photos:
        out.append(f"{tag}: photo of a minor ({', '.join(kids)}) in refs: describe the child in text only")
    text = re.sub(r'"[^"]*"|“[^”]*”', " ", f"{item.get('video_prompt') or ''} {item.get('continuity_in') or ''}")
    hits = sorted({m.group(0).lower() for m in MINOR_RISK.finditer(text)})
    if hits:
        out.append(f"{tag}: minor on screen ({', '.join(kids)}) with risky words: {', '.join(hits)}")
    devices = sorted({m.group(0).lower() for m in MINOR_DEVICE.finditer(text)})
    if devices:
        out.append(f"{tag}: minor on screen ({', '.join(kids)}) with a device ({', '.join(devices)}): keep the device "
                   "out of the child's part (adult's own part, or the child off screen)")
    adults = [c for c in item.get("characters") or [] if c not in minors]
    if len(adults) > 1:
        out.append(f"{tag}: minor on screen ({', '.join(kids)}) with {len(adults)} adults ({', '.join(adults)}): split "
                   "the part, the child alone or with one family member")
    return out


def fit_duration(real: float) -> int | None:
    """Smallest Flow step that holds `real` seconds as written (format 3 parts: trimmed, held tail). None: too long."""
    for step in VEO_STEPS:
        if real <= step + VEO_TOLERANCE:
            return step
    return None


def flow_duration(real: float) -> int | None:
    """Flow generation length for a part of `real` seconds of script: the smallest step that holds ~1.3x it, so the
    action and lines are not rushed (4s -> 6s, 6s -> 8s, 7s -> 10s); the longest step when only that one holds it."""
    target = real * FLOW_STRETCH
    for step in VEO_STEPS:
        if target <= step + VEO_TOLERANCE:
            return step
    return max(VEO_STEPS) if real <= max(VEO_STEPS) + VEO_TOLERANCE else None


def _check_veo_parts(tag: str, c: dict, a: float, b: float, fmt: int = 2) -> tuple[list[str], list[str]]:
    """(errors, warnings). Every clip carries veo_parts (the Flow / Veo 3.1 version): contiguous, cover the clip,
    <= 8s of script each, split on cut boundaries and never inside a dialogue line. Format 3+: each part has
    duration_sec = a Flow length and its prompt is written for it; format 4: that length is the stretched one
    (flow_duration: ~1.3x the script time) and the whole generation is kept."""
    parts = c.get("veo_parts") or []
    if not parts:
        return [f"{tag}: no veo_parts (the Google Flow / Veo version, one part per 8s at most)"], []
    errors, warns, prev = [], [], a
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
        if fmt >= 3:
            dur, real = part.get("duration_sec"), p1 - p0
            if dur not in VEO_STEPS:
                errors.append(f"{ptag}: duration_sec {dur} is not a Flow length {'/'.join(map(str, VEO_STEPS))}s")
            elif real > dur + VEO_TOLERANCE:
                errors.append(f"{ptag}: {real:.1f}s does not fit duration_sec {dur}s")
            else:
                if not re.match(rf"\s*{dur}(\.0+)?-second\b", part.get("video_prompt") or ""):
                    errors.append(f"{ptag}: prompt must start with \"{dur}-second\" (its Flow length)")
                want = flow_duration(real) if fmt >= 4 else fit_duration(real)
                if fmt >= 4 and real > 0 and dur / real > FLOW_MAX_RATIO:
                    warns.append(f"{ptag}: {real:.1f}s of script over {dur}s plays too slow: merge with a neighbour cut")
                elif want is not None and dur != want:
                    warns.append(f"{ptag}: {real:.1f}s of script -> {want}s, duration_sec is {dur}s")
        prev = p1
    if abs(prev - b) > EPS:
        errors.append(f"{tag}: veo_parts end at {prev}, clip ends at {b}")
    return errors, warns


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
    fmt = int(data.get("prompt_format") or 1)
    fmt2, fmt3 = fmt >= 2, fmt >= PROMPT_FORMAT
    minors = minor_ids(session)
    clip_prompts = has_higgsfield(data)  # Flow-only files have no 10-15s clip prompt to check
    names = _bible_names(session)
    if clips and not fmt2:
        warns.append("older prompt format (no opening/closing state, guard block or Veo parts): remake the prompts")
    elif clips and not fmt3:
        warns.append("older prompt format (Flow parts not stretched to 6/8/10s, no minors rule): remake the prompts")
    prev_end = 0.0
    no_seedance = 0  # Flow parts without their Seedance twin (older files): one warning for the episode
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
            if clip_prompts:
                errors += _check_prompt(tag, c.get("video_prompt", ""))
            errors += [f"{tag}: no {k}" for k in ("opening_state", "closing_state") if not c.get(k)]
            e, w = _check_veo_parts(tag, c, a, b, fmt)
            errors += e
            warns += w
            if minors:
                found = minor_problems(tag, c, minors) if clip_prompts else []
                (errors if fmt3 else warns).extend(found)
                for vp in c.get("veo_parts") or []:
                    found = minor_problems(f"{tag} veo part {vp.get('part')}", vp, minors)
                    (errors if fmt3 else warns).extend(found)
            on_screen = set(c.get("characters") or [])
            lines = sorted(c.get("dialogue") or [], key=lambda d: float(d.get("start_sec") or 0))
            if clip_prompts:
                if lines and "Voices:" not in (c.get("video_prompt") or ""):
                    warns.append(f"{tag}: no Voices: line (one voice per speaker)")
                warns += dialogue_tag_warnings(tag, c.get("video_prompt", ""), lines, on_screen)
                warns += shot_dialogue_warnings(tag, c.get("video_prompt", ""))
            warns += pace_warnings(tag, lines)
            for vp in c.get("veo_parts") or []:
                ptag = f"{tag} veo part {vp.get('part')}"
                warns += flow_warnings(ptag, vp, names, minors)
                p0, p1 = float(vp.get("start_sec", 0)), float(vp.get("end_sec", 0))
                inside = [d for d in lines if p0 - EPS <= float(d.get("start_sec") or 0) < p1 - EPS]
                seen = set(vp["characters"]) if isinstance(vp.get("characters"), list) else on_screen
                # a part may keep a speaker out of frame (e.g. a child, for Flow): the line is then an off-screen voice
                inside = [{**x, "mode": "offscreen"} if x.get("mode") == "speaks" and x.get("character") not in seen else x
                          for x in inside]
                warns += dialogue_tag_warnings(ptag, vp.get("video_prompt", ""), inside, seen)
                warns += shot_dialogue_warnings(ptag, vp.get("video_prompt", ""))
                if vp.get("seedance_prompt"):
                    errors += seedance.problems(ptag, vp, inside)[0]
                else:
                    no_seedance += 1
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
    lang = dialogue_language(session)
    if wrong := wrong_language_lines(data, lang):
        warns.append(f"{len(wrong)} spoken line(s) not in {lang} (e.g. \"{wrong[0][:40]}\"): remake the prompts")
    if no_seedance and "seedance" in (data.get("targets") or []):
        warns.append(f"{no_seedance} Flow part(s) without a Seedance prompt: python3 -m app.pipeline.seedance build "
                     f"{session} {n}")
    return errors, warns


def build_episode_package(session: Path, n: int, title: str = "") -> tuple[Path, str]:
    """Write the zip to a temp file. Returns (zip path, download file name)."""
    pf = prompts_file(session, n)
    if not pf:
        raise FileNotFoundError(f"ep{n:02d}: chưa có final/shots/ep{n:02d}/prompts.json (chạy /script-to-shotlist)")
    data = json.loads(pf.read_text(encoding="utf-8"))
    if not has_higgsfield(data):
        raise FileNotFoundError(f"Tập {n}: prompt chỉ có bản Google Flow (không có prompt clip 10-15s cho Higgsfield). "
                                "Dùng 'Tải gói Flow'.")
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
                           f"{_ts(vp.get('end_sec', 0))}] {_part_len(vp)}s (lưu thành clips/{unit}_{no:02d}_{vp.get('part')}.mp4)\n"
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
             "Prompt bằng tiếng Anh (cho model video); thoại đúng như trong prompt (ngôn ngữ sản xuất của series).\n"
             "Seedance 2 / Kling: dùng PROMPT chính (một clip tối đa 15s) với mọi ảnh tham chiếu của clip.\n"
             "Veo 3.1 / Google Flow (tối đa 8s): dùng các 'PROMPT VEO phần 1, 2...' và CHỈ upload ảnh ghi ở phần đó\n"
             f"  (tối đa {FLOW_MAX_REFS} ảnh: các nhân vật trên hình trước, rồi bối cảnh; gọi nhân vật bằng vai, không tên riêng,\n"
             "  để Flow không chặn vì 'người nổi tiếng').\n"
             + ("\nCẢNH BÁO: prompt kiểu cũ (mỗi shot 1-5s một video, dễ lệch nhân vật). Tạo lại prompt video (clip 10-15s).\n"
                if not clip else
                "\nCẢNH BÁO: prompt được tạo từ bản kịch bản cũ hơn bản chốt hiện tại. Tạo lại prompt video trước khi quay.\n"
                if prompts_stale(session, n) else "")
             + (f"\nLưu ý: {missing_refs} {unit} chưa có ảnh tham chiếu đã duyệt (duyệt ảnh ở mục Ngoại hình rồi tải lại).\n"
                if missing_refs else ""))
    return tmp, f"{root}_higgsfield.zip"


def _part_len(vp: dict) -> int | None:
    """Flow generation length of a veo part: its duration_sec when it is a Flow step, else the step that holds it
    as written (older prompts were written for the script length)."""
    dur = vp.get("duration_sec")
    if dur in VEO_STEPS:
        return int(dur)
    return fit_duration(float(vp.get("end_sec", 0)) - float(vp.get("start_sec", 0)))


def _flow_mode(images: list[str]) -> str:
    return "Ingredients to Video" if images else "Text to Video"


def build_flow_package(session: Path, n: int, title: str = "") -> tuple[Path, str]:
    """Google Flow / Veo 3.1 zip: one generation per `veo_parts` entry (<= 8s), only that part's images.

      HUONG_DAN_FLOW.txt     how to run it in Flow
      parts/clip_01_1.txt    one Flow generation: mode, images, aspect, save name, trim, PROMPT
      flow_queue.json/.csv   the same, one row per part, for batch tools
      refs/                  images used by the parts (<= 1 character image + location plate per part)
      clips/                 empty: save each part as clip_01_1.mp4, clip_01_2.mp4, ...
      edit_list.csv          part order, times in the episode, trim length
      subtitles.srt          dialogue timed on the episode
      prompts.json           original from /script-to-shotlist
    """
    pf = prompts_file(session, n)
    if not pf:
        raise FileNotFoundError(f"ep{n:02d}: chưa có final/shots/ep{n:02d}/prompts.json (chạy /script-to-shotlist)")
    data = json.loads(pf.read_text(encoding="utf-8"))
    shots = data.get("shots") or []
    if not any(s.get("veo_parts") for s in shots):
        raise FileNotFoundError(f"Tập {n}: prompt chưa có bản Veo / Flow (định dạng cũ). Bấm 'Nâng cấp prompt video' rồi tải lại.")
    ep_json = session / "final" / f"ep{n:02d}.json"
    ep = json.loads(ep_json.read_text(encoding="utf-8")) if ep_json.exists() else {}
    names = _bible_names(session)
    names.update({cid: c["name"] for cid, c in (ep.get("characters") or {}).items() if (c or {}).get("name")})
    labels = data.get("flow_labels") or {}
    ep_title = ep.get("title") or data.get("title") or ""
    root = f"tap{n:02d}" + (f"_{_ascii(ep_title)}" if _ascii(ep_title) else "") + "_flow"
    aspect = data.get("aspect_ratio", "9:16")
    orient = "Portrait (dọc)" if aspect == "9:16" else "Landscape (ngang)" if aspect == "16:9" else aspect
    unit = "clip" if data.get("unit") == "clip" else "shot"

    stretched = int(data.get("prompt_format") or 1) >= 4  # parts written for the whole generation: keep all of it
    minors = minor_ids(session)  # never attach a child's photo to Flow (refused as harmful content involving minors)
    refs: dict[Path, str] = {}
    rows, skipped, clock = [], [], 0.0  # clock: time in the edited Flow video
    for i, s in enumerate(shots, 1):
        no = int(s.get("shot_number") or i)
        parts = s.get("veo_parts") or []
        if not parts:
            skipped.append(no)
            continue
        timed = _clip_lines(s)
        for vp in parts:
            k = vp.get("part") or 1
            a, b = float(vp.get("start_sec", 0)), float(vp.get("end_sec", 0))
            found = [f for f in _shot_refs(session, {"refs": vp.get("refs") or []}, {}) if f.is_file()
                     and not any(f.name.startswith(f"{k}_") for k in minors)]
            for f in found:
                refs.setdefault(f, _ref_name(f, names))
            images = [f"refs/{refs[f]}" for f in found]
            lines = [(x, y, d) for x, y, d in timed if a - 0.05 <= x < b]
            dur = _part_len(vp)
            keep = float(dur) if stretched and dur else min(b - a, dur or b - a)
            scale = keep / (b - a) if b > a else 1.0  # script second -> second in the generated clip
            rows.append({
                "episode": n, unit: no, "part": k, "scene": s.get("scene"),
                "id": f"{unit}_{no:02d}_{k}", "start_sec": a, "end_sec": b, "duration_sec": dur,
                "needed_sec": round(b - a, 2), "trim_to_sec": round(keep, 2),
                "video_start": round(clock, 2), "video_end": round(clock + keep, 2),
                "aspect_ratio": aspect, "mode": _flow_mode(images),
                "images": images, "characters": [names.get(c) or c for c in vp.get("characters") or []],
                "dialogue": [{"who": names.get(d.get("character")) or d.get("character"), "name": names.get(d.get("character")),
                              "voiceover": bool(d.get("voiceover")),
                              "mode": line_mode(d, set(vp.get("characters") or [])), "line": d["line"],
                              "start_sec": round((x - a) * scale, 2), "end_sec": round((y - a) * scale, 2)}
                             for x, y, d in lines],
                "continuity_in": named_prompt(vp.get("continuity_in") or "", labels, names),
                "save_as": f"clips/{unit}_{no:02d}_{k}.mp4",
                "prompt": named_prompt(vp.get("video_prompt") or "", labels, names),
                "seedance_prompt": vp.get("seedance_prompt") or ""})
            clock += keep

    tmp = Path(tempfile.mkstemp(suffix=".zip", prefix=f"{root}_")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        def text(name: str, body: str):
            z.writestr(f"{root}/{name}", body)

        q, e = io.StringIO(), io.StringIO()
        qw, ew = csv.writer(q), csv.writer(e)
        qw.writerow(["id", "save_as", "mode", "aspect_ratio", "duration_sec", "needed_sec", "trim_to_sec", "images", "prompt",
                     "seedance_prompt"])
        ew.writerow(["order", "clip_file", "start", "end", "keep_sec", "scene", "dialogue"])
        for j, r in enumerate(rows, 1):
            said = "\n".join(f"  [{d['start_sec']:.1f}s] {d['who']}"
                              + {"voiceover": " (VO, không mấp máy môi)", "offscreen": " (ngoài khung)"}.get(d["mode"], "")
                              + f": \"{d['line']}\"" for d in r["dialogue"])
            dur = r["duration_sec"]
            tail = (f"  (khi dựng lấy {r['trim_to_sec']}s đầu; {dur - r['trim_to_sec']:.1f}s cuối là khung giữ)"
                    if dur and dur - r["trim_to_sec"] > 0.05 else "  (giữ nguyên cả clip khi dựng)")
            text(f"parts/{r['id']}.txt",
                 f"{r['id'].upper()}   [{_ts(r['start_sec'])}-{_ts(r['end_sec'])}]   tạo {dur or '?'}s   {aspect}\n\n"
                 + (f"Flow: thời lượng {dur}s, chế độ {r['mode']}, khung {orient}, 1 kết quả mỗi lần.\n" if dur else
                    f"CẢNH BÁO: phần dài {r['needed_sec']}s, quá {max(VEO_STEPS)}s của Flow: tạo lại prompt video.\n")
                 + f"Ảnh (chỉ những ảnh này, đúng thứ tự): {', '.join(r['images']) or 'không có (tạo từ chữ)'}\n"
                 f"Lưu video thành: {r['save_as']}{tail}\n"
                 + (f"Nối tiếp phần trước: {r['continuity_in']}\n" if r["continuity_in"] else "")
                 + f"Thoại trong phần này:\n{said or '  (không thoại)'}\n"
                 f"\nPROMPT (copy nguyên văn vào Flow):\n{r['prompt']}\n"
                 + (f"\nPROMPT SEEDANCE 2.0 (cùng phần, cùng ảnh, thời lượng {dur}s; bản riêng: seedance/{r['id']}.txt):\n"
                    f"{r['seedance_prompt']}\n" if r["seedance_prompt"] else ""))
            if r["seedance_prompt"]:
                text(f"seedance/{r['id']}.txt",
                     f"{r['id'].upper()}   Seedance 2.0   {dur}s   {aspect}\n"
                     f"Ảnh (cùng ảnh với Flow, đúng thứ tự): {', '.join(r['images']) or 'không có'}\n"
                     f"Lưu video thành: {r['save_as']} (cùng tên với bản Flow: chọn một trong hai bản khi dựng)\n\n"
                     f"PROMPT:\n{r['seedance_prompt']}\n")
            qw.writerow([r["id"], r["save_as"], r["mode"], aspect, r["duration_sec"], r["needed_sec"], r["trim_to_sec"],
                         " ".join(r["images"]), r["prompt"], r["seedance_prompt"]])
            ew.writerow([j, Path(r["save_as"]).name, _ts(r["video_start"]), _ts(r["video_end"]), r["trim_to_sec"],
                         r["scene"] or "", " | ".join(f"{d['who']}: {d['line']}" for d in r["dialogue"])])
        text("flow_queue.json", json.dumps({"episode": n, "title": ep_title, "series": title, "aspect_ratio": aspect,
                                            "model": "Veo 3.1", "names": names, "parts": rows},
                                           ensure_ascii=False, indent=2))
        text("flow_queue.csv", "\ufeff" + q.getvalue())
        text("edit_list.csv", "\ufeff" + e.getvalue())
        srt = []
        lines = [(r["video_start"] + d["start_sec"], r["video_start"] + d["end_sec"], d) for r in rows for d in r["dialogue"]]
        for k, (a, b, d) in enumerate(lines, 1):
            who = d.get("name") or d.get("who") or ""
            srt.append(f"{k}\n{_ts(a, True)} --> {_ts(b, True)}\n{who + ' (VO): ' if d.get('voiceover') else ''}{d['line']}\n")
        text("subtitles.srt", "\n".join(srt))
        text("clips/DAT_CLIP_VAO_DAY.txt", f"Lưu video của từng phần ở đây: {unit}_01_1.mp4, {unit}_01_2.mp4, ...\n")
        z.write(pf, f"{root}/prompts.json")
        for src, name in refs.items():
            z.write(src, f"{root}/refs/{name}", compress_type=zipfile.ZIP_STORED)
        total = shots[-1].get("end_sec") if shots else 0
        text("HUONG_DAN_FLOW.txt",
             f"{title + ' — ' if title else ''}Tập {n:02d}: {ep_title}\n"
             f"{len(rows)} lần tạo trên Google Flow, khung {aspect}. {len(refs)} ảnh tham chiếu.\n"
             f"Kịch bản {total}s -> video dựng xong khoảng {round(clock)}s"
             + (" (mỗi phần được giãn ~1.3 lần cho đủ thời gian diễn và nói).\n\n" if stretched else ".\n\n")
             + "Mỗi file parts/XX.txt là MỘT lần tạo trên Flow:\n"
             "  1. Flow -> New project. Cài đặt: model video của Flow, khung " + orient + ", số kết quả 1,\n"
             "     thời lượng đúng số ghi trong file (6, 8 hoặc 10s: prompt được viết cho đúng độ dài đó).\n"
             "  2. Chế độ ghi trong file: 'Ingredients to Video' -> thêm ĐÚNG các ảnh ghi trong file (thư mục refs/);\n"
             "     'Text to Video' -> không thêm ảnh.\n"
             "  3. Copy PROMPT dán nguyên văn. Không thêm tên nhân vật: prompt gọi nhân vật bằng vai\n"
             "     (Flow chặn tên riêng + mặt chi tiết như 'người nổi tiếng').\n"
             "  4. Tải video về, lưu đúng tên ghi trong file (clips/clip_01_1.mp4 ...).\n\n"
             + ("Seedance 2.0: mỗi phần có thêm bản prompt Seedance (seedance/XX.txt, cuối mỗi file parts/XX.txt):\n"
                "  cùng đoạn kịch bản, cùng thời lượng, cùng ảnh và cùng thoại, nên ghép chung một edit_list và\n"
                "  subtitles.srt. Seedance: thời lượng đúng số ghi trong file, khung " + aspect + ", thêm đúng các ảnh ghi trong file.\n\n"
                if any(r["seedance_prompt"] for r in rows) else "")
             + "Chạy hàng loạt: flow_queue.json / flow_queue.csv có đủ các phần theo thứ tự\n"
             "(id, save_as, mode, images, prompt, trim_to_sec).\n\n"
             "Dựng video:\n"
             "  - Ghép clips/ theo thứ tự trong edit_list.csv, mỗi phần giữ keep_sec giây đầu\n"
             "    (prompt mới: cả clip).\n"
             "  - subtitles.srt đã tính theo thời gian của video dựng (không phải thời gian kịch bản).\n"
             + (f"\nCẢNH BÁO: {unit} {', '.join(map(str, skipped))} chưa có bản Veo; tạo lại prompt video.\n" if skipped else "")
             + ("\nCẢNH BÁO: prompt được tạo từ bản kịch bản cũ hơn bản chốt hiện tại. Tạo lại prompt video trước khi quay.\n"
                if prompts_stale(session, n) else ""))
    return tmp, f"{root}.zip"


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

    lang = dialogue_language(d)
    lang_note = (f"Spoken dialogue language: {lang} (skill Step 5 'Language'): every spoken line, voice-over, subtitle, "
                 + ("name card and post_text in natural American English for a US audience, " if lang.lower().startswith("en")
                    else f"name card and post_text in {lang}, ")
                 + "each line translating its script line exactly (line_vi = the script line); the screenplay stays "
                   "as it is. ")
    targets = ",".join(config.VIDEO_TARGETS)
    clip_note = ("one prompt per 10-15s clip (Higgsfield) plus " if "higgsfield" in config.VIDEO_TARGETS
                 else "10-15s clips WITHOUT a clip video_prompt (Flow only), ")

    async def one(n: int):
        async with slots:
            try:
                await _claude(job, f"/script-to-shotlist {final / f'ep{n:02d}.md'} --targets {targets}\n\nRun "
                                   "non-interactively: do not ask questions. The episode is approved (final/). Write "
                                   f"shotlist.json/.md and prompts.json/.md into {final / 'shots' / f'ep{n:02d}'}/. "
                                   f'prompts.json is "unit": "clip", "prompt_format": {PROMPT_FORMAT}, '
                                   f'"targets": {json.dumps(list(config.VIDEO_TARGETS))}: {clip_note}'
                                   "veo_parts on every clip (Flow lengths stretched ~1.3x to 6/8/10s, minors rule), "
                                   "at most 5 timed cuts per clip, a start/end time on every dialogue line, "
                                   + lang_note +
                                   "opening/closing state, performance, the Rules guard block (skill Step 5), veo_parts[].seedance "
                                   "{scene, acting per cut, exclusions} (skill 'Seedance twin', the app builds seedance_prompt); "
                                   "replace any older prompts.json. Then python3 -m app.pipeline.package check "
                                   f"{d} {n} -> 0 errors." + UI_NOTE,
                              f"ep{n:02d}", 3600)
            except RuntimeError as e:
                job.log(f"[ep{n:02d}] {e}")
            if prompts_file(d, n):
                try:
                    seedance.build_episode(d, n)  # Seedance twin of every Flow part, from the same data
                except (OSError, ValueError, KeyError, TypeError) as e:
                    job.log(f"[ep{n:02d}] Seedance: {e}")
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


def _asset_labels(session: Path) -> dict[str, str]:
    """{item key: readable label} from the latest registry: char_01 -> Vu, char_01_o1 -> Vu do di lam,
    loc_01_day -> Cong truong day, prop_01 -> Hop com. Bible names when there is no registry yet."""
    labels = dict(_bible_names(session))
    try:
        _, reg = asset_images.latest_registry(session)
    except (RuntimeError, OSError, json.JSONDecodeError):
        return labels
    for c in reg.get("characters", []):
        name = c.get("name") or labels.get(c.get("char_id"), "")
        labels[c.get("char_id")] = name
        for o in c.get("wardrobe", []):
            labels[o.get("outfit_id")] = f"{name} {o.get('name', '')}".strip()
    for loc in reg.get("locations", []):
        for v in loc.get("variants", []):
            labels[v.get("variant_id")] = f"{loc.get('name', '')} {v.get('time_of_day', '')}".strip()
    for pr in reg.get("props", []):
        labels[pr.get("prop_id")] = pr.get("name", "")
    return labels


REF_FOLDERS = {"character": "nhan_vat", "outfit": "trang_phuc", "location": "boi_canh", "prop": "dao_cu"}


def build_refs_package(session: Path, title: str = "") -> tuple[Path, str]:
    """Every reference image still in use (approved + waiting for review; rejected / replaced left out) in one
    zip: da_duyet/<kind>/ and cho_duyet/<kind>/, readable file names, danh_sach.csv. Returns (zip path, name)."""
    index = asset_images.load_index(session)
    labels = _asset_labels(session)
    root = "anh_tham_chieu" + (f"_{_ascii(title)}" if _ascii(title) else "")
    rows, used = [], set()
    for key, item in sorted(index.get("items", {}).items()):
        folder = REF_FOLDERS.get(item.get("kind"), "khac")
        for img in item.get("images", []):
            src = session / "assets" / img.get("file", "")
            if img.get("status") not in ("approved", "draft") or not src.is_file():
                continue
            label = _ascii(labels.get(key, ""))
            stem = src.stem.replace(key, f"{key}_{label}", 1) if label and key in src.stem else src.stem
            status_dir = "da_duyet" if img["status"] == "approved" else "cho_duyet"
            arc = f"{status_dir}/{folder}/{stem}{src.suffix}"
            k = 2
            while arc in used:
                arc, k = f"{status_dir}/{folder}/{stem}_{k}{src.suffix}", k + 1
            used.add(arc)
            rows.append((src, arc, key, labels.get(key, ""), img["status"], img.get("created_at", "")))
    if not rows:
        raise FileNotFoundError("Chưa có ảnh tham chiếu nào (đã duyệt hoặc chờ duyệt).")
    tmp = Path(tempfile.mkstemp(suffix=".zip", prefix=f"{root}_")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["file", "ma", "ten", "trang_thai", "tao_luc", "goc"])
        for src, arc, key, label, status, created in rows:
            z.write(src, f"{root}/{arc}", compress_type=zipfile.ZIP_STORED)  # png/jpg are compressed already
            w.writerow([arc, key, label, "đã duyệt" if status == "approved" else "chờ duyệt", created,
                        str(src.relative_to(session / "assets"))])
        z.writestr(f"{root}/danh_sach.csv", "\ufeff" + buf.getvalue())
    return tmp, f"{root}.zip"


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
