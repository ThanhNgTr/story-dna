#!/usr/bin/env python3
"""Deterministic checks of on-screen action (no LLM). Heuristics, not a judge.

  lint <session> [N ...]   -> flag beats whose people do nothing visible, writes <session>/action_check.json

Flags (see references/screen-action.md):
  missing      a character visible in the beat (beat `characters` in the scene `cast`) has no `acting` entry
  vague        `does` is only a look / listen / stand ("nhìn Vy", "đứng im") and `face` is empty
  abstract     a feeling word ("buồn", "tức giận", "lo lắng") with almost nothing visible around it
  overloaded   more actions than the beat's seconds hold (~1 per 1.5s, at least 2)
  prop_vanish  an object held earlier in the scene is gone and no beat puts it down / hands it over
  no_blocking  2+ characters on screen in the scene and no `blocking`
  minor_risk   a character under 18 on screen in a night scene, or near sleep / bed / touching / bare skin /
               crying / secrecy / body words (story-contract/references/minors-on-screen.md): Google Flow
               refuses such clips as "harmful content involving minors"
Writers fix missing / prop_vanish / no_blocking / minor_risk to 0; the others are hints.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STRICT = ("missing", "prop_vanish", "no_blocking", "minor_risk")
NIGHT = re.compile(r"night|midnight|late|đêm|khuya|tối muộn", re.I)
# minors-on-screen.md rules 2-7, Vietnamese and English (action / acting text of a beat with a child on screen)
MINOR_RISK = re.compile(
    r"\b(ngủ|giường|chiếu|chăn|mền|màn ngủ|tắm|thay đồ|thay áo|cởi (?:áo|quần|đồ)|chân trần|chân đất|quần đùi|quần short|áo ba lỗ|"
    r"đồ ngủ|ôm (?:chầm|lấy|chặt|nhau|anh|em|chị|cô|chú|bé|con|cháu|ba|bố|mẹ|vai|cổ)|bế|cõng|xoa đầu|vuốt tóc|hôn|thơm má|dắt tay|nắm lấy tay|nắm tay nhau|lau nước mắt|khóc|nước mắt|"
    r"lén|khuya|nửa đêm|gầy|ốm nhom|môi|miệng|cắn|nhắm mắt|gục|thiếp|nằm (?:xuống|ngủ|co|nghiêng|dài|cạnh)|"
    r"sleep\w*|asleep|bed|blanket|mat|bath\w*|undress\w*|barefoot|shorts|tank top|hug\w*|carr(?:y|ies)|lap|"
    r"kiss\w*|ruffl\w*|cr(?:y|ies|ying)|tears?|sneak\w*|secretly|skinny|lips|mouth|teeth|eyes closed|doz\w*)\b", re.I)
AGE_VI = re.compile(r"(\d{1,2})\s*tuổi")
FEELING = re.compile(r"(^|[\s,;])(buồn( bã)?|tức( giận| tối)?|giận( dữ)?|lo lắng|lo âu|xúc động|hồi hộp|bối rối|sợ hãi|"
                     r"cảm thấy|đau lòng|hạnh phúc|vui vẻ|thất vọng|ngại ngùng|xấu hổ|căng thẳng|bất an)(?=$|[\s,;.])", re.I)
VAGUE = re.compile(r"^(nhìn|nghe|lắng nghe|đứng|ngồi|im lặng|im|đứng im|ngồi im|chờ|đợi|gật đầu)(\s+\S+){0,2}$", re.I)
RELEASE = re.compile(r"(đặt|để|buông|thả|đưa|trao|chìa|cất|nhét|đút|ném|rơi|úp|gác|dựng|treo|cài|giao|trả|vứt|quăng|"
                     r"gạt|đẩy|đổ|bỏ|giấu|dúi|cắm|kẹp|ấn vào tay|cầm lấy)", re.I)
CLAUSE = re.compile(r"[,;]|\s(?:rồi|và|xong)\s", re.I)
STOP = set("""và của là một những các cái chiếc con đi ra vào lên xuống có không đã đang sẽ thì mà cho với ở
trên dưới trong ngoài này đó kia ấy nó họ lại rồi còn cũng vẫn được bị từ tới đến qua hơi rất quá""".split())


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _latest_eps(session: Path) -> dict[int, Path]:
    eps: dict[int, tuple[int, Path]] = {}
    for p in (session / "episodes").glob("ep*_v*.json"):
        m = re.fullmatch(r"ep(\d+)_v(\d+)\.json", p.name)
        if m and (int(m.group(1)) not in eps or int(m.group(2)) > eps[int(m.group(1))][0]):
            eps[int(m.group(1))] = (int(m.group(2)), p)
    out = {n: p for n, (_, p) in eps.items()}
    for p in (session / "final").glob("ep*.json") if (session / "final").is_dir() else []:
        m = re.fullmatch(r"ep(\d+)\.json", p.name)
        if m and (int(m.group(1)) not in out or p.stat().st_mtime >= out[int(m.group(1))].stat().st_mtime):
            out[int(m.group(1))] = p
    return dict(sorted(out.items()))


def minor_ids(session: Path) -> set[str]:
    """Characters under 18: the asset registry `age` (final/assets.json, else the latest assets_vN.json), else the
    bible cast `age` or "<n> tuổi" in its visual signature."""
    out: set[str] = set()
    regs = [session / "final" / "assets.json"] if (session / "final" / "assets.json").exists() else sorted(
        (session / "assets").glob("assets_v*.json"), key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
    for c in (_load(regs[-1]).get("characters") or []) if regs else []:
        if isinstance(c, dict) and isinstance(c.get("age"), (int, float)) and c["age"] < 18 and c.get("char_id"):
            out.add(c["char_id"])
    bibles = sorted(session.glob("bible_v*.json"), key=lambda p: int(re.search(r"_v(\d+)", p.name).group(1)))
    for c in (_load(bibles[-1]).get("cast") or []) if bibles else []:
        if not isinstance(c, dict) or not c.get("character_id"):
            continue
        age = c.get("age")
        m = AGE_VI.search(str(c.get("visual_signature") or ""))
        age = age if isinstance(age, (int, float)) else int(m.group(1)) if m else None
        if age is not None and age < 18:
            out.add(c["character_id"])
    return out


def minor_problems(ep: dict, minors: set[str]) -> list[dict]:
    """minor_risk items: a night scene with a child on screen, and beats whose action / acting (anyone's: an adult
    asleep beside the child counts) has a risky word while a child is on screen. Dialogue is not checked."""
    items = []
    for sc in ep.get("scenes") or []:
        beats = sc.get("beats") or []
        kids = sorted({c for b in beats for c in visible(sc, b) if c in minors})
        if not kids:
            continue
        if NIGHT.search(str(sc.get("time_of_day") or "")):
            items.append({"scene": sc.get("id"), "beat": None, "character": kids[0], "issues": ["minor_risk"],
                          "note": f"night scene ({sc.get('time_of_day')}) with a minor on screen: daylight / early evening, open place"})
        for bi, b in enumerate(beats):
            seen = [c for c in visible(sc, b) if c in minors]
            if not seen:
                continue
            text = " ".join([str(b.get("action") or "")] + [f"{a.get('does') or ''} {a.get('face') or ''} {a.get('holds') or ''}"
                                                              for a in b.get("acting") or [] if isinstance(a, dict)])
            hits = sorted({m.group(0).lower() for m in MINOR_RISK.finditer(text)})
            if hits:
                items.append({"scene": sc.get("id"), "beat": bi, "character": seen[0], "issues": ["minor_risk"],
                              "text": str(b.get("action") or "")[:120], "note": ", ".join(hits)})
    return items


def visible(scene: dict, beat: dict) -> list[str]:
    """Characters seen in the beat: its `characters` that are in the scene `cast` (voices are not seen)."""
    chars = [str(c) for c in beat.get("characters") or []]
    cast = scene.get("cast")
    if isinstance(cast, dict) and cast:
        return [c for c in chars if c in cast]
    return [c for c in chars if not c.startswith("voice")]


def _norm(s) -> str:
    return re.sub(r"\s*\(prop_[\w-]+\)", "", str(s or "")).strip().lower()


def _content(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if w not in STOP}


def check_episode(ep: dict, minors: set[str] = frozenset()) -> tuple[list[dict], dict]:
    """(flagged items, coverage) for one episode JSON."""
    items, beats_seen, beats_ok = (minor_problems(ep, set(minors)) if minors else []), 0, 0
    for sc in ep.get("scenes") or []:
        sid, beats = sc.get("id"), sc.get("beats") or []
        on_screen = {c for b in beats for c in visible(sc, b)}
        if len(on_screen) >= 2 and not str(sc.get("blocking") or "").strip():
            items.append({"scene": sid, "beat": None, "character": None, "issues": ["no_blocking"],
                          "note": f"{len(on_screen)} characters on screen"})
        held: dict[str, str] = {}
        for bi, b in enumerate(beats):
            seen = visible(sc, b)
            acting = {str(a.get("character")): a for a in b.get("acting") or [] if isinstance(a, dict)}
            speakers = {d.get("character") for d in b.get("dialogue") or [] if not d.get("voiceover") and d.get("line")}
            dur = float(b.get("end_sec", 0)) - float(b.get("start_sec", 0))
            if seen:
                beats_seen += 1
                beats_ok += all(c in acting for c in seen)
            for c in seen:
                if c not in acting:
                    role = "speaker" if c in speakers else "listener" if speakers else "on screen"
                    items.append({"scene": sid, "beat": bi, "character": c, "issues": ["missing"], "note": role})
            for c, a in acting.items():
                does, face = str(a.get("does") or "").strip(), str(a.get("face") or "").strip()
                issues, note = [], ""
                if VAGUE.match(does) and not face:
                    issues.append("vague")
                for text in (does, face):
                    m = FEELING.search(text)
                    if m and len(_content(FEELING.sub(" ", text))) < 3:
                        issues.append("abstract")
                        note = m.group(2)
                        break
                n = len([x for x in CLAUSE.split(does) if x.strip()])
                if n > max(2, int(dur / 1.5) + 1):
                    issues.append("overloaded")
                    note = note or f"{n} actions in {dur:.1f}s"
                if "holds" in a:
                    now = _norm(a.get("holds"))
                    before = held.get(c, "")
                    if before and before not in now and not RELEASE.search(does):
                        issues.append("prop_vanish")
                        note = note or f"held '{before}' before"
                    held[c] = now
                if issues:
                    items.append({"scene": sid, "beat": bi, "character": c, "issues": issues, "text": does, "note": note})
    return items, {"beats": beats_seen, "covered": beats_ok,
                   "pct": round(100 * beats_ok / beats_seen) if beats_seen else 100}


def lint(session: Path, only: set[int]) -> int:
    items, per_ep = [], {}
    files = _latest_eps(session)
    minors = minor_ids(session)
    for n, f in files.items():
        if only and n not in only:
            continue
        found, cov = check_episode(_load(f), minors)
        per_ep[n] = {**cov, "file": str(f.relative_to(session))}
        items += [{"episode": n, **it} for it in found]
    counts: dict[str, int] = {}
    for it in items:
        for i in it["issues"]:
            counts[i] = counts.get(i, 0) + 1
    report = {"checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "episodes": per_ep, "counts": counts, "strict": sum(counts.get(k, 0) for k in STRICT), "items": items}
    (session / "action_check.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for it in items:
        where = f"ep{it['episode']:02d}.{it['scene']}" + (f"#{it['beat']}" if it.get("beat") is not None else "")
        print(f"WARN  {where} [{','.join(it['issues'])}] {it.get('character') or ''}: {it.get('text') or it.get('note')}")
    cov = ", ".join(f"ep{n:02d} {c['pct']}%" for n, c in per_ep.items())
    print(f"action lint: {len(per_ep)} episodes, {len(items)} flags {counts}; acting coverage: {cov}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "lint":
        return lint(Path(argv[1]), {int(x) for a in argv[2:] for x in a.split(",") if x.strip()})
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
