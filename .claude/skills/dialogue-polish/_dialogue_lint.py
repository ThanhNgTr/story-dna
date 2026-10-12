#!/usr/bin/env python3
"""Deterministic dialogue checks for Vietnamese scripts (no LLM). Heuristics, not a judge.

  lint     <session> [N ...]   -> flag unclear lines per episode, writes <session>/dialogue_check.json
  examples                     -> collect lines reviewers edited by hand (all sessions) into
                                  data/dialogue_examples.json (newest first), for writers to imitate

Flags (see references/vi-dialogue.md):
  telegraphic   2+ sentences and at least half of them <= 3 words ("Một tấm rèm. Sáu căn nhà trả.")
  figure        "như" comparisons beyond 2 per episode (VO metaphors pile up into riddles)
  pronoun       the narrator says both "tao" and "tôi" in VO (VO keeps one pronoun all season; spoken
                lines may change pronoun with the listener, see the bible address_matrix)
  clock         24h time ("hai mươi hai giờ") from a character who is not a machine/announcement voice
  short_heavy   more than 55% of an episode's lines are <= 3 words
  definition    the line defines a word ("X là khung ống thép...", "tức là", "gọi là", "nghĩa là"): people
                do not explain everyday words to each other; a scene shows what a thing is
  too_fast      over the Speech rate in references/vi-dialogue.md: more than 5.0 syllables/s in a scene,
                or an on-screen line longer than its beat + the next beat can hold
  narrates_action  VO retells what the same beat's `action` already shows (most of the action's content
                words are in the line): VO says what the image cannot (thought, feeling, past, secret)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MACHINE = re.compile(r"(voice|unknown|loa|speaker|system|may|announce|intercom|radio)", re.I)
SENT = re.compile(r"[^.!?…]+[.!?…]*")
CLOCK = re.compile(r"\b(mười (ba|bốn|lăm|năm|sáu|bảy|tám|chín)|hai mươi( mốt| hai| ba| tư)?) giờ\b", re.I)
FIGURE = re.compile(r"(^|[\s,.])(như|như thể|tựa như)\s", re.I)
DEFINE = re.compile(r"(^|[\s,(])(tức là|(?<!cuộc )gọi là|nghĩa là|có nghĩa là)(?=[\s,:])", re.I)
# "<thing> là <kind of thing> ..." at the start of a sentence: "Giàn giáo là khung ống thép..." (not identity
# lines like "Anh là người kéo tôi ra", which use người/cái)
DEFINE_IS = re.compile(r"(^|[.!?…]\s+)[^.!?…,]{2,30}\s+là\s+(khung|nơi|dãy|lễ|tờ|loại|kiểu|nghề|thanh|ống|bộ phận|"
                       r"giấy|dụng cụ|thiết bị)\s", re.I)
# Words that carry no content when comparing a VO line with the beat's action
STOP = set("""và của là một những các cái chiếc con người đi ra vào lên xuống có không đã đang sẽ thì mà cho với ở
trên dưới trong ngoài này đó kia ấy tôi anh chị em cô ông bà nó họ mình hai ba bốn năm lại rồi còn cũng vẫn được bị
từ tới đến qua sau trước khi lúc hôm nay ngày đêm sáng chiều tối thật rất quá nhìn thấy đứng ngồi""".split())


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


def _lines(ep: dict):
    for sc in ep.get("scenes") or []:
        for bi, b in enumerate(sc.get("beats") or []):
            for di, d in enumerate(b.get("dialogue") or []):
                if str(d.get("line") or "").strip():
                    yield sc.get("id"), bi, di, d


def _content(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if w not in STOP and not w.isdigit()}


def _narrates(line: str, action: str) -> bool:
    """VO shares most of the action's content words: it describes what is already on screen."""
    act = _content(action)
    shared = act & _content(line)
    return len(act) >= 3 and len(shared) >= 3 and len(shared) * 3 >= len(act)


def _glossary_terms(session: Path) -> list[str]:
    """Terms of the latest bible's glossary: "<term> là ..." in a line is a definition."""
    bibles = [p for p in session.glob("bible_v*.json") if re.fullmatch(r"bible_v\d+\.json", p.name)]
    if not bibles:
        return []
    try:
        b = _load(max(bibles, key=lambda p: int(re.search(r"\d+", p.name).group())))
    except (OSError, json.JSONDecodeError):
        return []
    return [str(g.get("term")).strip().lower() for g in b.get("glossary") or [] if isinstance(g, dict) and g.get("term")]


def _defines(text: str, terms: list[str]) -> bool:
    if DEFINE.search(text) or DEFINE_IS.search(text):
        return True
    low = text.lower()
    return any(re.search(rf"(^|[.!?…]\s+|,\s*){re.escape(t)}\s+là\s", low) for t in terms)


MAX_SYL_PER_SEC = 5.0  # vi-dialogue.md "Speech rate", hard limit


def _syllables(s: str) -> int:
    return len(re.findall(r"\w+", s))


def _too_fast(ep: dict) -> list[tuple[str, int, str, str]]:
    """(scene, beat index, line, note) over the speech rate: a scene's lines / its time, and each on-screen
    line / (its beat + the next beat of the same scene)."""
    out = []
    for sc in ep.get("scenes") or []:
        beats = sc.get("beats") or []
        a = float(sc.get("start_sec", beats[0].get("start_sec", 0) if beats else 0))
        b = float(sc.get("end_sec", beats[-1].get("end_sec", 0) if beats else 0))
        total = sum(_syllables(d.get("line") or "") for bt in beats for d in bt.get("dialogue") or [])
        if b > a and total / (b - a) > MAX_SYL_PER_SEC:
            out.append((sc.get("id"), -1, "", f"scene {total} syllables in {b - a:.1f}s = {total / (b - a):.1f}/s"))
        for i, bt in enumerate(beats):
            room = float(bt.get("end_sec", 0)) - float(bt.get("start_sec", 0))
            if i + 1 < len(beats):
                room += float(beats[i + 1].get("end_sec", 0)) - float(beats[i + 1].get("start_sec", 0))
            for d in bt.get("dialogue") or []:
                n = _syllables(d.get("line") or "")
                if not d.get("voiceover") and room > 0 and n / room > MAX_SYL_PER_SEC:
                    out.append((sc.get("id"), i, d["line"], f"{n} syllables, {room:.1f}s on screen"))
    return out


def _beats(ep: dict) -> dict:
    return {(sc.get("id"), bi): b for sc in ep.get("scenes") or [] for bi, b in enumerate(sc.get("beats") or [])}


def _words(s: str) -> int:
    return len(re.findall(r"\w+", s))


def lint(session: Path, only: set[int]) -> int:
    items, per_ep, self_pron = [], {}, {}
    files = _latest_eps(session)
    terms = _glossary_terms(session)
    for n, f in files.items():
        ep = _load(f)
        lines = list(_lines(ep))
        beats = _beats(ep)
        figures, short = 0, 0
        for scene, bi, _, d in lines:
            text, who = d["line"].strip(), str(d.get("character") or "")
            issues = []
            # Shouts and short questions ("Ra đây! Vũ!", "Ông nghe chưa?") are natural; machine voices are
            # meant to be clipped. Judge only a character's statements.
            sents = [s.strip() for s in SENT.findall(text) if _words(s) and not s.strip().endswith(("!", "?"))]
            if not MACHINE.search(who) and len(sents) >= 2 and sum(_words(s) <= 3 for s in sents) * 2 >= len(sents):
                issues.append("telegraphic")
            if FIGURE.search(" " + text):
                figures += 1
                if figures > 2:
                    issues.append("figure")
            if CLOCK.search(text) and not MACHINE.search(who):
                issues.append("clock")
            if _defines(text, terms):
                issues.append("definition")
            if d.get("voiceover") and _narrates(text, str((beats.get((scene, bi)) or {}).get("action") or "")):
                issues.append("narrates_action")
            if _words(text) <= 3:
                short += 1
            if d.get("voiceover"):
                low = f" {text.lower()} "
                for pr in ("tao", "tôi"):
                    if re.search(rf"[\s,.!?]{pr}[\s,.!?]", low):
                        self_pron.setdefault(who, {}).setdefault(pr, []).append((n, scene, text))
            if issues and (not only or n in only):
                items.append({"episode": n, "scene": scene, "character": who, "voiceover": bool(d.get("voiceover")),
                              "line": text, "issues": issues})
        for scene, _, line, note in _too_fast(ep):
            if not only or n in only:
                items.append({"episode": n, "scene": scene, "character": None, "line": line or None,
                              "issues": ["too_fast"], "note": note})
        per_ep[n] = {"lines": len(lines), "short_pct": round(100 * short / len(lines)) if lines else 0}
        if lines and short / len(lines) > 0.55 and (not only or n in only):
            items.append({"episode": n, "scene": None, "character": None, "line": None,
                          "issues": ["short_heavy"], "note": f"{per_ep[n]['short_pct']}% lines <= 3 words"})
    for who, prs in self_pron.items():
        if len(prs) > 1:
            for pr, uses in prs.items():
                for n, scene, text in uses[:3]:
                    if not only or n in only:
                        items.append({"episode": n, "scene": scene, "character": who, "voiceover": False,
                                      "line": text, "issues": ["pronoun"], "note": f"VO of {who} says both tao and tôi"})
    counts: dict[str, int] = {}
    for it in items:
        for i in it["issues"]:
            counts[i] = counts.get(i, 0) + 1
    report = {"checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "episodes": per_ep, "counts": counts, "items": items}
    (session / "dialogue_check.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for it in items:
        where = f"ep{it['episode']:02d}" + (f".{it['scene']}" if it.get("scene") else "")
        print(f"WARN  {where} [{','.join(it['issues'])}] {it.get('character') or ''}: {it.get('line') or it.get('note')}")
    print(f"dialogue lint: {len(files)} episodes, {len(items)} flagged lines {counts}")
    return 0


def _by_key(ep: dict) -> dict:
    return {(s, bi, di): d for s, bi, di, d in _lines(ep)}


def examples() -> int:
    """Lines changed by a manual edit (episode JSON with edited.by == manual vs the version it came from)."""
    out = []
    for session in (ROOT / "data" / "series").glob("*/*"):
        ep_dir = session / "episodes"
        for p in ep_dir.glob("ep*_v*.json") if ep_dir.is_dir() else []:
            try:
                ep = _load(p)
            except (OSError, json.JSONDecodeError):
                continue
            ed = ep.get("edited") or {}
            if ed.get("by") != "manual" or not ed.get("from_version"):
                continue
            m = re.fullmatch(r"ep(\d+)_v\d+\.json", p.name)
            base = ep_dir / f"ep{m.group(1)}_v{ed['from_version']}.json"
            if not base.exists():
                continue
            old = _by_key(_load(base))
            for k, d in _by_key(ep).items():
                o = old.get(k)
                if o and o.get("line", "").strip() != d.get("line", "").strip():
                    out.append({"before": o["line"], "after": d["line"], "character": d.get("character"),
                                "voiceover": bool(d.get("voiceover")), "series": session.parent.name,
                                "session": session.name, "episode": int(m.group(1)), "at": ed.get("at")})
    out.sort(key=lambda x: x.get("at") or "", reverse=True)
    dest = ROOT / "data" / "dialogue_examples.json"
    dest.write_text(json.dumps({"updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "count": len(out), "examples": out}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"examples: {len(out)} hand-edited lines -> {dest}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["examples"]:
        return examples()
    if len(argv) >= 2 and argv[0] == "lint":
        return lint(Path(argv[1]), {int(x) for a in argv[2:] for x in a.split(",") if x.strip()})
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
