"""Seedance 2.0 prompt beside every Google Flow part: `veo_parts[].seedance_prompt`.

Same script span, same length (Flow 4/6/8/10s; Seedance takes 4-15s), same images and the same timed lines as
the Flow part, so both versions drop into the same edit (edit_list.csv, subtitles.srt). Layout = the producer's
Seedance template: header (three beats), CLIP id + Scene, Cast + voices, style + fixed guards, exact opening state,
ordered action and exact dialogue, acting progression, camera / light, synchronous audio, exact closing state,
continuity exclusions, "No text on screen."

Written by /script-to-shotlist, optional per part (the rest comes from the clip and the Flow part):
  vp["seedance"] = {"scene": "INT. ... - DAY", "acting": ["<cut 1>", "<cut 2>", ...], "camera": "...",
                    "audio": "...", "exclusions": "..."}
Costume changes inside an episode: top-level `characters` holds the face only and `outfits` {outfit_id: text};
each part's Cast then adds the outfit the clip's `outfits` gives that character.

  python3 -m app.pipeline.seedance build <session-dir> <episode>   # fills seedance_prompt, adds them to prompts.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HEAD = ("Create {art} {dur}-second narrative audio-video clip. Preserve chronological cause and reaction, character "
        "identity and prop continuity. Beat1 establishes the stated opening; beat2 performs the ordered source actions "
        "and exact speech with concurrent reactions; beat3 settles into the stated final state. These beats share the "
        "full clip duration, not three equal fixed slots. Use only the camera/cut instructions written below; do not "
        "add automatic montage or a second scene.")
CAST_HEAD = "Only people present or explicitly heard in the source appear. No invented actor or reference attachment."
GUARDS = ("Original fictional cast, no celebrity likeness. Natural skin, plausible hands and props. {narration} "
          "TV-14 restraint: no violence shown, no injury detail, no weapons, no drug use, no sexual content. Preserve "
          "who owns every phone, card, key, necklace and document. Spoken {lang} is exact; lettering on screen is a "
          "prop insert only.")
AUDIO_TAIL = ("Use only the quoted dialogue, keep each named voice with its speaker, allow the specified reactions "
              "and breaths. No paraphrase, duplicate line or ad-lib.")
EXCLUSIONS_TAIL = ("No invented dialogue, characters or future events. Keep speaker, anatomy, prop ownership and "
                   "location exact.")
REQUIRED = ("narrative audio-video clip", "Exact opening state:", "Ordered action and exact dialogue",
            "Acting progression across the clip:", "Camera and blocking:", "Synchronous audio:",
            "Exact closing state for the next edit:", "Continuity exclusions:", "No text on screen.")
LANGS = {"en": "English", "vi": "Vietnamese"}


def _g(x: float) -> str:
    return f"{round(float(x), 1):g}"


def _sentence(s: str) -> str:
    s = (s or "").strip()
    return s if not s or s[-1] in ".!?\"'" else s + "."


def _art(n: int) -> str:
    return "an" if str(n)[:1] == "8" or n in (11, 18) else "a"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _first(name: str) -> str:
    """'Vivian Cole' -> VIVIAN, '"Celeste Thornton" (Lydia Langford)' -> CELESTE, 'The auctioneer' -> THE AUCTIONEER."""
    name = (name or "").strip('"“” ')
    return (name if name.lower().startswith("the ") else name.split(" ")[0]).upper()


def _registry(session: Path) -> dict:
    f = session / "final" / "assets.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _lighting(reg: dict, loc_id: str | None, variant_id: str | None) -> str:
    for loc in reg.get("locations") or []:
        if loc.get("loc_id") == loc_id:
            for v in loc.get("variants") or []:
                if v.get("variant_id") == variant_id:
                    return v.get("prompt_en") or ""
    return ""


def _scene_heading(reg: dict, clip: dict, data: dict) -> str:
    loc = (data.get("locations") or {}).get(clip.get("loc_id")) or ""
    place = loc.split(":")[0].strip() or str(clip.get("loc_id") or "")
    ie = "EXT" if any(l.get("int_ext") == "EXT" for l in reg.get("locations") or [] if l.get("loc_id") == clip.get("loc_id")) else "INT"
    tod = (str(clip.get("variant_id") or "").rsplit("_", 1)[-1] or "day").upper()
    return f"{ie}. {place.upper()} - {tod}"


def _language(session: Path) -> str:
    f = session / "final" / "bible.json"
    try:
        b = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, json.JSONDecodeError):
        b = {}
    code = (b.get("production_language") or b.get("language") or "en").split("-")[0]
    return LANGS.get(code, code)


def _style(vp: dict, data: dict) -> str:
    """The Flow part's filtered style suffix (its last line), else the registry suffix."""
    last = (vp.get("video_prompt") or "").strip().splitlines()[-1:] or [""]
    style = last[0] if last[0].startswith("vertical") else data.get("style_suffix") or ""
    return _sentence(style)


def _flow_sound(vp: dict) -> str:
    m = re.search(r"Sound: (.+)", vp.get("video_prompt") or "")
    return m.group(1).strip() if m else ""


def _line(d: dict, mode: str, names: dict[str, str]) -> str:
    who = _first(names.get(d.get("character")) or d.get("character") or "")
    how = d.get("delivery_en") or ""
    tag = {"voiceover": f"voice-over, {how}; nobody's lips move" if how else "voice-over; nobody's lips move",
           "offscreen": f"off-screen, not in frame, {how}" if how else "off-screen, not in frame"}.get(mode, how)
    return f'{who} ({tag}): "{d.get("line", "")}"' if tag else f'{who}: "{d.get("line", "")}"'


def build_part(data: dict, clip: dict, vp: dict, *, ep: int, last: bool, names: dict[str, str], reg: dict,
               lang: str = "English") -> str:
    from .package import line_mode

    dur = int(vp.get("duration_sec") or round(float(vp["end_sec"]) - float(vp["start_sec"])))
    a, b = float(vp["start_sec"]), float(vp["end_sec"])
    scale = dur / (b - a) if b > a else 1.0
    sd = vp.get("seedance") or {}
    on_screen = list(vp.get("characters") or clip.get("characters") or [])
    cuts = [c for c in clip.get("cuts") or [] if c.get("cut") in (vp.get("cuts") or [])] or clip.get("cuts") or []
    lines = [d for c in cuts for d in c.get("dialogue") or []]
    modes = [line_mode(d, set(on_screen)) for d in lines]

    chars, voices = data.get("characters") or {}, data.get("voices") or {}
    # an episode with costume changes: characters = face only, outfits = {outfit_id: text}, the clip's outfit added
    worn = {cid: (data.get("outfits") or {}).get(oid) for cid, oid in (clip.get("outfits") or {}).items()}
    cast = []
    for cid in on_screen:
        if cid in chars:
            v = voices.get(cid, "")
            v = v.split(": ", 1)[1] if ": " in v[:40] else v
            look = f"{chars[cid]}; {worn[cid]}" if worn.get(cid) else chars[cid]
            cast.append(_sentence(_cap(look)) + (f" Voice: {_sentence(v)}" if v else ""))
    for cid in dict.fromkeys(d.get("character") for d, m in zip(lines, modes)
                             if m == "offscreen" and d.get("character") not in on_screen):  # out of one cut only
        v = voices.get(cid, "")
        v = v.split(": ", 1)[1] if ": " in v[:40] else v
        cast.append(f"Heard only, not seen: {names.get(cid) or cid}." + (f" Voice: {_sentence(v)}" if v else ""))
    owners = {_first(names.get(c) or ""): c for c in names}
    props = []
    for pid in clip.get("props") or []:  # a prop "<Name>'s ..." only while its owner is in frame
        txt = (data.get("props") or {}).get(pid)
        m = re.match(r"(\w+)'s ", txt or "")
        owner = owners.get(m.group(1).upper()) if m else None
        if txt and (owner is None or owner in on_screen):
            props.append(txt)
    if not cast:
        cast.append("No people appear in this clip.")

    narration = ("No subtitles or music montage; the only narration is the quoted voice-over." if "voiceover" in modes
                 else "No subtitles, narrator or music montage.")
    style = f"American prestige melodrama in present-day New York: {_style(vp, data)}"

    actions = []
    for i, c in enumerate(cuts):
        cam = (c.get("camera") or "").strip()
        lead = _cap(cam) if i == 0 else f"Cut to {cam}"
        actions.append(f"Action: {lead}: {_sentence(c.get('action') or '')}" if cam else f"Action: {_sentence(_cap(c.get('action') or ''))}")
        for d in c.get("dialogue") or []:
            actions.append(_line(d, line_mode(d, set(on_screen)), names))

    acting = sd.get("acting") or []
    if isinstance(acting, list) and len(acting) == len(cuts):
        spans = []
        for c, t in zip(cuts, acting):
            x = max(0.0, (float(c["start_sec"]) - a) * scale)
            y = dur if c is cuts[-1] else (float(c["end_sec"]) - a) * scale
            spans.append(f"{_g(x)}-{_g(y)}s: {_sentence(t)}")
        acting_txt = " ".join(spans)
    else:
        acting_txt = f"0-{dur}s: {_sentence(acting if isinstance(acting, str) and acting else vp.get('performance') or clip.get('performance') or '')}"

    camera = sd.get("camera") or "; then ".join(_cap(c.get("camera") or "") if i == 0 else (c.get("camera") or "")
                                                 for i, c in enumerate(cuts) if c.get("camera"))
    light = _lighting(reg, clip.get("loc_id"), clip.get("variant_id"))
    audio = sd.get("audio") or _flow_sound(vp) or clip.get("sfx") or "room tone"
    post = clip.get("post_text") or []
    closing = _sentence(vp.get("closing_state") or clip.get("closing_state") or "")
    closing += (" The final frame holds clean; any title or end card is added in post." if last
                else " The final frame holds clean for the next cut.")
    excl = _sentence(sd.get("exclusions") or "")
    no_text = "No on-screen text (all lettering is added in post)." if post else "No on-screen text."

    out = [
        HEAD.format(art=_art(dur), dur=dur),
        f"CLIP EP{ep:02d}-C{int(clip.get('shot_number') or 0):02d}-P{vp.get('part') or 1}. "
        f"Scene: {sd.get('scene') or _scene_heading(reg, clip, data)}.",
        " ".join([CAST_HEAD] + cast + ([f"Props: {'; '.join(props)}."] if props else [])),
        f"{style} {GUARDS.format(narration=narration, lang=lang)}",
        f"Exact opening state: {_sentence(vp.get('opening_state') or clip.get('opening_state') or '')}",
        f"Ordered action and exact dialogue, occurring within this {dur}-second clip:\n" + "\n".join(actions),
        f"Acting progression across the clip: {acting_txt}",
        f"Camera and blocking: {_sentence(camera)}" + (f" Light and color: {_sentence(_cap(light))}" if light else ""),
        f"Synchronous audio: {_sentence(_cap(audio))} {AUDIO_TAIL}",
        f"Exact closing state for the next edit: {closing}",
        " ".join(x for x in ("Continuity exclusions:", excl, no_text, EXCLUSIONS_TAIL) if x),
        "No text on screen.",
    ]
    return "\n".join(out)


def problems(tag: str, vp: dict, lines: list[dict]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for one part's seedance_prompt. No prompt (older files): a warning."""
    p = vp.get("seedance_prompt") or ""
    if not p:
        return [], [f"{tag}: no Seedance prompt (python3 -m app.pipeline.seedance build <session> <episode>)"]
    errs = []
    dur = vp.get("duration_sec")
    if dur and not p.startswith(f"Create {_art(int(dur))} {int(dur)}-second"):
        errs.append(f"{tag}: Seedance prompt does not start with 'Create {_art(int(dur))} {int(dur)}-second'")
    if dur and not 4 <= int(dur) <= 15:
        errs.append(f"{tag}: Seedance takes 4-15s, part is {dur}s")
    errs += [f"{tag}: Seedance prompt has no '{k}'" for k in REQUIRED if k not in p]
    errs += [f"{tag}: Seedance prompt misses the line \"{d['line'][:40]}\"" for d in lines
             if d.get("line") and f'"{d["line"]}"' not in p]
    return errs, []


def build_episode(session: Path, n: int) -> int:
    from .package import _bible_names, prompts_file

    pf = prompts_file(session, n)
    if not pf:
        raise FileNotFoundError(f"ep{n:02d}: no prompts.json")
    data = json.loads(pf.read_text(encoding="utf-8"))
    bible = _bible_names(session)
    names = dict(bible)
    ep_f = session / "final" / f"ep{n:02d}.json"
    ep = json.loads(ep_f.read_text(encoding="utf-8")) if ep_f.exists() else {}
    names.update({cid: c["name"] for cid, c in (ep.get("characters") or {}).items() if (c or {}).get("name")})
    # extras have no bible name: the label of their voice ("The auctioneer: man about 50, ..."), also over a
    # script-language name the episode gives them ("Giọng lạ trong điện thoại")
    names.update({cid: v.split(": ", 1)[0] for cid, v in (data.get("voices") or {}).items()
                  if cid not in bible and ": " in v[:40]})
    reg, lang = _registry(session), _language(session)
    clips = data.get("shots") or []
    count = 0
    for i, clip in enumerate(clips):
        parts = clip.get("veo_parts") or []
        for j, vp in enumerate(parts):
            vp["seedance_prompt"] = build_part(data, clip, vp, ep=n, last=(i == len(clips) - 1 and j == len(parts) - 1),
                                               names=names, reg=reg, lang=lang)
            count += 1
    targets = list(data.get("targets") or ["flow"])
    if "seedance" not in targets:
        targets.append("seedance")
    data["targets"] = targets
    pf.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = pf.with_name("prompts.md")
    if md.exists():
        md.write_text(add_to_md(md.read_text(encoding="utf-8"), clips), encoding="utf-8")
    return count


SEEDANCE_MD = re.compile(r"\n*#### Seedance part [^\n]*\n\n```text\n.*?\n```", re.S)


def add_to_md(md: str, clips: list[dict]) -> str:
    """Put each part's Seedance prompt right after its Flow part block (replaces earlier Seedance blocks)."""
    md = SEEDANCE_MD.sub("", md)
    for clip in clips:
        for vp in clip.get("veo_parts") or []:
            if not vp.get("seedance_prompt"):
                continue
            c, k = clip.get("shot_number"), vp.get("part")
            m = re.search(rf"#### Flow part {c}\.{k} [^\n]*\n\n```text\n.*?\n```", md, re.S)
            if not m:
                continue
            block = (f"\n\n#### Seedance part {c}.{k} [{_g(vp['start_sec'])}-{_g(vp['end_sec'])}s script -> "
                     f"{vp.get('duration_sec')}s] same images as Flow part {c}.{k}\n\n```text\n{vp['seedance_prompt']}\n```")
            md = md[:m.end()] + block + md[m.end():]
    return md


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "build":
        print(f"ep{int(sys.argv[3]):02d}: {build_episode(Path(sys.argv[2]), int(sys.argv[3]))} Seedance prompts")
        sys.exit(0)
    print("usage: python3 -m app.pipeline.seedance build <session-dir> <episode>")
    sys.exit(2)
