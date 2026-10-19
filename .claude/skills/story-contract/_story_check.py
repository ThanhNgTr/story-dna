#!/usr/bin/env python3
"""Check a series session against references/story-contract.md (no LLM).

  _story_check.py <session> [--stage outline|episodes] [--json <out>]

stage outline  -> bible + outline (run before showing the outline)
stage episodes -> bible + outline + every written episode (default when episodes exist)
Prints WARN/ERROR lines, writes <session>/story_check.json, exit 1 on errors.
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ENDINGS = {"happy", "bad"}
LEVELS = {"minor", "major", "midpoint", "final"}
TIERS = {"central", "major", "minor"}
# references/minors-on-screen.md "The bible": a child's tell / signature puts it in every scene, and Google Flow refused
# Na (10) whose tell was chewing her phone strap and whose signature prop was the phone (ep04, ep06)
AGE_VI = re.compile(r"(\d{1,2})\s*tuổi")
CHILD_MOUTH = re.compile(r"\b(cắn|nhai|ngậm|mút|liếm|môi|miệng|bite|bites|biting|chew\w*|suck\w*|lick\w*|lips|mouth)\b", re.I)
CHILD_DEVICE = re.compile(r"\b(điện thoại|di động|máy tính bảng|máy tính|màn hình|nhắn tin|phones?|smartphone|keypad|"
                          r"tablet|laptop|screen)\b", re.I)
CHILD_BODY = re.compile(r"\b(gầy|ốm nhom|nhỏ con|da ngăm|da trắng|mắt to|môi|skinny|petite|slim|lips)\b", re.I)


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _latest(dir_: Path, stem: str) -> Path | None:
    best, best_n = None, -1
    for p in dir_.glob(f"{stem}_v*.json"):
        m = re.fullmatch(rf"{re.escape(stem)}_v(\d+)\.json", p.name)
        if m and int(m.group(1)) > best_n:
            best, best_n = p, int(m.group(1))
    return best


def _episode_files(session: Path) -> dict[int, Path]:
    """Latest draft per episode; final/epNN.json when it is newer (same rule as _assets.py)."""
    eps: dict[int, Path] = {}
    if (session / "episodes").is_dir():
        for p in (session / "episodes").glob("ep*_v*.json"):
            m = re.fullmatch(r"ep(\d+)_v\d+\.json", p.name)
            if m:
                eps[int(m.group(1))] = _latest(session / "episodes", f"ep{m.group(1)}")
    if (session / "final").is_dir():
        for p in (session / "final").glob("ep*.json"):
            m = re.fullmatch(r"ep(\d+)\.json", p.name)
            if m and (int(m.group(1)) not in eps or p.stat().st_mtime >= eps[int(m.group(1))].stat().st_mtime):
                eps[int(m.group(1))] = p
    return dict(sorted(eps.items()))


def _ep(x) -> int | None:
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def _filled(x) -> bool:
    return bool(x.strip()) if isinstance(x, str) else x is not None and x != [] and x != {}


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, req: int, msg: str):
        self.errors.append(f"[R{req}] {msg}")

    def warn(self, req: int, msg: str):
        self.warns.append(f"[R{req}] {msg}")


def check_bible(b: dict, n: int, r: Report):
    # R1 + R2: main plot and ending
    mp = b.get("main_plot") or {}
    if not mp:
        r.err(2, "bible: no main_plot")
    for k in ("central_question", "protagonist_goal", "opposition", "stakes", "start_state", "end_state"):
        if mp and not _filled(mp.get(k)):
            r.err(2, f"bible.main_plot.{k} is empty")
    order = ("inciting_incident", "midpoint", "lowest_point", "climax", "resolution")
    eps = {}
    for k in order:
        v = mp.get(k) if isinstance(mp.get(k), dict) else {}
        e = _ep(v.get("episode"))
        if mp and (e is None or not 1 <= e <= n or not _filled(v.get("event"))):
            r.err(2, f"bible.main_plot.{k} needs episode 1..{n} and event")
        eps[k] = e
    seq = [eps[k] for k in order if eps[k] is not None]
    if seq != sorted(seq):
        r.err(2, f"bible.main_plot beats out of order: {eps}")
    if eps.get("inciting_incident") and eps["inciting_incident"] > max(1, math.ceil(0.2 * n)):
        r.warn(2, f"inciting incident in ep{eps['inciting_incident']} (should be in the first 20%)")
    if eps.get("midpoint") and not math.floor(0.35 * n) <= eps["midpoint"] <= math.ceil(0.65 * n):
        r.warn(2, f"midpoint in ep{eps['midpoint']} (should be at 35-65% of {n})")
    if eps.get("climax") and eps["climax"] < math.ceil(0.75 * n):
        r.err(2, f"climax in ep{eps['climax']} (must be in the last 25%: ep{math.ceil(0.75 * n)}+)")
    if eps.get("resolution") and eps["resolution"] != n:
        r.err(1, f"resolution in ep{eps['resolution']}, must be the last episode ({n})")

    end = b.get("ending") or {}
    if not end:
        r.err(1, "bible: no ending")
    else:
        if end.get("type") not in ENDINGS:
            r.err(1, f"bible.ending.type must be happy or bad, got {end.get('type')!r}")
        if _ep(end.get("episode")) != n:
            r.err(1, f"bible.ending.episode must be {n}")
        for k in ("what_happens", "protagonist_fate", "central_question_answer", "final_image"):
            if not _filled(end.get(k)):
                r.err(1, f"bible.ending.{k} is empty")

    # R3 + R4: cast
    cast = b.get("cast") or []
    mains = [c for c in cast if c.get("tier") == "main"]
    sups = [c for c in cast if c.get("tier") == "supporting"]
    if not 1 <= len(mains) <= 2:
        r.err(3, f"cast needs 1-2 main characters, has {len(mains)}")
    if len(sups) < 2:
        r.err(3, f"cast needs >=2 supporting characters, has {len(sups)}")
    for c in cast:
        cid = c.get("character_id") or c.get("name")
        tier = c.get("tier")
        if tier != "main" and not _filled(c.get("relation_to_main")):
            r.err(3, f"{cid}: no relation_to_main")
        if tier in ("main", "supporting"):
            for k in ("want", "need"):
                if not _filled(c.get(k)):
                    r.err(3, f"{cid}: {k} is empty")
            arc = c.get("arc") or {}
            if not (_filled(arc.get("start")) and _filled(arc.get("end"))):
                r.err(3, f"{cid}: arc.start / arc.end missing")
            lines = ((c.get("voice") or {}).get("sample_lines")) or []
            if len([x for x in lines if _filled(x)]) < 2:
                r.err(4, f"{cid}: needs >=2 voice.sample_lines")
        if tier == "main":
            if not _filled(c.get("secret")):
                r.err(7, f"{cid}: main character has no secret")
            elif not (_ep(c.get("secret_reveal_ep")) and 1 <= c["secret_reveal_ep"] <= n):
                r.err(7, f"{cid}: secret_reveal_ep must be 1..{n}")

    for c in cast:  # minors: the design every child scene inherits
        cid = c.get("character_id") or c.get("name")
        m = AGE_VI.search(str(c.get("visual_signature") or ""))
        age = c.get("age") if isinstance(c.get("age"), (int, float)) else int(m.group(1)) if m else None
        if age is None or age >= 18:
            continue
        tell, look = str(c.get("tell") or ""), str(c.get("visual_signature") or "")
        for field, text, pats in (("tell", tell, (CHILD_MOUTH, CHILD_DEVICE)), ("visual_signature", look, (CHILD_DEVICE,))):
            hits = sorted({h.group(0).lower() for pat in pats for h in pat.finditer(text)})
            if hits:
                r.err(3, f"{cid} (minor, {age}): {field} has {', '.join(hits)}: a hand / school-thing habit, no mouth "
                         f"habit or device (minors-on-screen.md \"The bible\")")
        body = sorted({h.group(0).lower() for h in CHILD_BODY.finditer(look)})
        if body:
            r.warn(3, f"{cid} (minor, {age}): visual_signature describes the body ({', '.join(body)}): clothes, hair, props")

    # R5: setting
    world = b.get("world") or {}
    st = world.get("setting")
    if isinstance(st, dict):
        for k in ("place", "era", "time_span"):
            if not _filled(st.get(k)):
                r.err(5, f"bible.world.setting.{k} is empty")
    elif not _filled(st):
        r.err(5, "bible.world.setting is empty")
    else:
        r.warn(5, "bible.world.setting is free text; use {place, era, time_span}")
    locs = {l.get("id"): l for l in world.get("locations") or [] if l.get("id")}
    if len(locs) < 2:
        r.err(5, f"bible.world.locations needs >=2 with id, has {len(locs)}")
    for lid, l in locs.items():
        if not _filled(l.get("name")) or not _filled(l.get("look")):
            r.err(5, f"location {lid}: name/look empty")
        if not _ep(l.get("first_ep")):
            r.err(5, f"location {lid}: first_ep missing")
    tl = b.get("setting_timeline") or []
    rows = {_ep(x.get("episode")): x for x in tl}
    missing = [e for e in range(1, n + 1) if e not in rows]
    if missing:
        r.err(5, f"setting_timeline missing episodes {missing}")
    used = set()
    for e, x in sorted((k, v) for k, v in rows.items() if k):
        for lid in x.get("locations") or []:
            used.add(lid)
            if lid not in locs:
                r.err(5, f"setting_timeline ep{e}: unknown location {lid}")
        if not x.get("locations"):
            r.err(5, f"setting_timeline ep{e}: no locations")
        if not _filled(x.get("time")):
            r.err(5, f"setting_timeline ep{e}: no time")
    changes = sum(1 for x in tl if _filled(x.get("change")))
    if tl and changes < 3:
        r.err(5, f"setting changes only {changes} times (need >=3)")
    for lid in set(locs) - used:
        r.warn(5, f"location {lid} never used in setting_timeline")

    # R6: climaxes
    cl = b.get("climaxes") or []
    bad = [x for x in cl if x.get("level") not in LEVELS or not _ep(x.get("episode"))]
    if bad:
        r.err(6, f"climaxes with bad level/episode: {bad[:2]}")
    by_level = {lv: [x["episode"] for x in cl if x.get("level") == lv] for lv in LEVELS}
    if len(by_level["midpoint"]) != 1:
        r.err(6, f"climaxes need exactly 1 midpoint, have {len(by_level['midpoint'])}")
    if len(by_level["final"]) != 1:
        r.err(6, f"climaxes need exactly 1 final, have {len(by_level['final'])}")
    elif eps.get("climax") and by_level["final"][0] != eps["climax"]:
        r.err(6, f"final climax ep{by_level['final'][0]} != main_plot.climax ep{eps['climax']}")
    peaks = sorted({x["episode"] for x in cl if _ep(x.get("episode"))})
    prev = 0
    for e in peaks + [n + 1]:
        if e - prev - 1 > 3 and e <= n:
            r.err(6, f"no climax in ep{prev + 1}-ep{e - 1} (max 3 episodes without one)")
        prev = e

    # R7: mysteries
    ledger = b.get("ledger_plan") or []
    never = {q.get("id") for q in (b.get("never_answered") or []) if isinstance(q, dict)} | \
            {q for q in (b.get("never_answered") or []) if isinstance(q, str)}
    if len(ledger) < 3:
        r.err(7, f"ledger_plan needs >=3 questions, has {len(ledger)}")
    central = [q for q in ledger if q.get("tier") == "central"]
    if len(central) != 1:
        r.err(7, f"ledger_plan needs exactly 1 central question, has {len(central)}")
    if len(never) > 1:
        r.err(7, f"never_answered allows at most 1 minor question, has {len(never)}")
    for q in ledger:
        qid, o, a = q.get("id"), _ep(q.get("open_ep")), _ep(q.get("answer_ep"))
        if q.get("tier") not in TIERS:
            r.err(7, f"{qid}: tier must be central/major/minor")
        if not o or not 1 <= o <= n:
            r.err(7, f"{qid}: open_ep must be 1..{n}")
            continue
        if qid in never:
            if q.get("tier") != "minor":
                r.err(7, f"{qid}: only a minor question may stay unanswered")
            continue
        if not a or not o < a <= n:
            r.err(7, f"{qid}: answer_ep must be after open_ep ({o}) and <= {n}")
            continue
        if not _filled(q.get("answer")):
            r.err(7, f"{qid}: answer is empty (the writer must know the truth)")
        for c in q.get("clue_eps") or []:
            if not (isinstance(c, int) and o <= c <= a):
                r.err(7, f"{qid}: clue ep{c} outside open..answer ({o}..{a})")
        if q.get("tier") == "central" and a < math.ceil(0.75 * n):
            r.err(7, f"{qid}: central question answered in ep{a}, must be in the last 25%")
        if q.get("tier") != "minor" and not q.get("clue_eps"):
            r.warn(7, f"{qid}: answered with no clue episodes (unfair reveal)")
    for e in range(1, n):
        open_ = [q for q in ledger if _ep(q.get("open_ep")) and q["open_ep"] <= e
                 and (q.get("id") in never or not _ep(q.get("answer_ep")) or q["answer_ep"] > e)]
        if not open_:
            r.err(7, f"no mystery open at the end of ep{e} (curiosity drops)")
    return {k: eps[k] for k in eps}


def check_outline(o: dict, b: dict, n: int, r: Report):
    rows = {_ep(x.get("episode")): x for x in o.get("episodes") or []}
    missing = [e for e in range(1, n + 1) if e not in rows]
    if missing:
        r.err(2, f"outline missing episodes {missing}")
    locs = {l.get("id") for l in (b.get("world") or {}).get("locations") or []}
    never = {q.get("id") if isinstance(q, dict) else q for q in b.get("never_answered") or []}
    plan = {q.get("id"): q for q in b.get("ledger_plan") or []}
    climaxes = {x.get("episode"): x.get("level") for x in b.get("climaxes") or []}
    mains = {c.get("character_id") for c in b.get("cast") or [] if c.get("tier") == "main"}
    main_in = {m: 0 for m in mains}
    for e in range(1, n + 1):
        x = rows.get(e)
        if not x:
            continue
        k = f"outline ep{e}"
        if x.get("act") not in (1, 2, 3):
            r.err(2, f"{k}: act must be 1/2/3")
        if not _filled(x.get("main_plot_step")):
            r.err(2, f"{k}: main_plot_step empty")
        for lid in x.get("locations") or []:
            if lid not in locs:
                r.err(5, f"{k}: unknown location {lid}")
        if not x.get("locations"):
            r.err(5, f"{k}: no locations")
        if (x.get("climax") or None) != climaxes.get(e):
            r.err(6, f"{k}: climax {x.get('climax')!r} != bible climaxes {climaxes.get(e)!r}")
        led = x.get("ledger") or {}
        for qid, q in plan.items():
            if q.get("open_ep") == e and qid not in (led.get("opened") or []):
                r.err(7, f"{k}: ledger.opened misses {qid}")
            if q.get("answer_ep") == e and qid not in never and qid not in (led.get("answered") or []):
                r.err(7, f"{k}: ledger.answered misses {qid}")
        for qid in led.get("answered") or []:
            if qid in plan and plan[qid].get("answer_ep") != e:
                r.err(7, f"{k}: answers {qid}, bible says ep{plan[qid].get('answer_ep')}")
        for m in mains:
            main_in[m] += m in (x.get("characters") or [])
        if e < n:
            if not _filled(x.get("cliffhanger_type")) or x.get("cliffhanger_type") == "resolution":
                r.err(6, f"{k}: needs a cliffhanger (not the last episode)")
        else:
            end = (b.get("ending") or {}).get("type")
            if x.get("ending") != end:
                r.err(1, f"{k}: last episode ending {x.get('ending')!r} != bible ending {end!r}")
            if x.get("cliffhanger_type") != "resolution":
                r.err(1, f"{k}: last episode cliffhanger_type must be 'resolution'")
    for m, cnt in main_in.items():
        if cnt < math.ceil(0.8 * n):
            r.err(3, f"main character {m} in {cnt}/{n} episodes (need >=80%)")


def check_episodes(files: dict[int, Path], b: dict, o: dict, n: int, r: Report):
    rows = {_ep(x.get("episode")): x for x in o.get("episodes") or []}
    plan = {q.get("id"): q for q in b.get("ledger_plan") or []}
    answered: set[str] = set()
    for e, f in files.items():
        ep = _load(f)
        k = f"ep{e:02d}"
        chars = set((ep.get("characters") or {}).keys())
        lines = []
        for sc in ep.get("scenes") or []:
            if not _filled(sc.get("location")) or not _filled(sc.get("time_of_day")):
                r.err(5, f"{k}.{sc.get('id')}: location/time_of_day missing")
            for bt in sc.get("beats") or []:
                lines += [d for d in bt.get("dialogue") or [] if _filled(d.get("line"))]
        speakers = {d.get("character") for d in lines}
        if len(lines) < 4:
            r.err(4, f"{k}: only {len(lines)} spoken lines (need >=4)")
        if len(speakers) < 2:
            r.err(4, f"{k}: only {len(speakers)} speaking character(s) (need >=2)")
        if lines and all(d.get("voiceover") for d in lines):
            r.err(4, f"{k}: every line is voiceover; needs on-screen dialogue")
        for s in speakers - chars:
            r.warn(4, f"{k}: speaker {s} not in episode characters")
        led = ep.get("ledger") or {}
        answered |= set(led.get("answered") or [])
        want = (rows.get(e) or {}).get("ledger") or {}
        for part in ("opened", "answered"):
            miss = set(want.get(part) or []) - set(led.get(part) or [])
            if miss:
                r.err(7, f"{k}: ledger.{part} misses {sorted(miss)} from the outline")
        if e == n:
            end, bend = ep.get("ending") or {}, b.get("ending") or {}
            if end.get("type") != bend.get("type"):
                r.err(1, f"{k}: ending.type {end.get('type')!r} != bible {bend.get('type')!r}")
            if not _filled(end.get("central_question_answer")):
                r.err(1, f"{k}: ending.central_question_answer empty")
    if n in files and set(range(1, n + 1)) <= set(files):
        never = {q.get("id") if isinstance(q, dict) else q for q in b.get("never_answered") or []}
        left = sorted(q for q in plan if q not in answered and q not in never)
        if left:
            r.err(7, f"season ends with unanswered questions {left}")


def run(session: Path, stage: str | None) -> tuple[Report, dict]:
    r = Report()
    bp, op = _latest(session, "bible"), _latest(session, "outline")
    files = _episode_files(session)
    stage = stage or ("episodes" if files else "outline")
    inp = _load(session / "input.json") if (session / "input.json").exists() else {}
    if not bp or not op:
        r.err(2, "no bible_vK.json / outline_vK.json")
        return r, {"stage": stage}
    b, o = _load(bp), _load(op)
    # Older skills name these differently; never_answered may sit in the outline
    b.setdefault("cast", b.get("characters") if isinstance(b.get("characters"), list) else [])
    b.setdefault("ledger_plan", b.get("mystery_ledger") or [])
    b.setdefault("never_answered", o.get("never_answered") or [])
    n = int(inp.get("episodes") or o.get("episode_count") or len(o.get("episodes") or []))
    check_bible(b, n, r)
    check_outline(o, b, n, r)
    if stage == "episodes":
        check_episodes(files, b, o, n, r)
    return r, {"stage": stage, "episodes": n, "bible": bp.name, "outline": op.name,
               "checked_episodes": sorted(files) if stage == "episodes" else []}


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    session = Path(argv[0])
    stage = argv[argv.index("--stage") + 1] if "--stage" in argv else None
    out = Path(argv[argv.index("--json") + 1]) if "--json" in argv else session / "story_check.json"
    r, meta = run(session, stage)
    for w in r.warns:
        print(f"WARN  {w}")
    for e in r.errors:
        print(f"ERROR {e}")
    print(f"story_check ({meta.get('stage')}): {len(r.errors)} errors, {len(r.warns)} warnings")
    out.write_text(json.dumps({**meta, "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "ok": not r.errors, "errors": r.errors, "warnings": r.warns},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
