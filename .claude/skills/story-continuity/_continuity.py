#!/usr/bin/env python3
"""Continuity across episodes (no LLM): references/continuity.md.

  check    <session> [--stage outline|episodes] [--json <out>]
                                  -> cause chain (outline) + state ledger vs the written episodes;
                                     writes <session>/continuity_check.json, exit 1 on errors
  digest   <session> [N ...]      -> compact text of the written episodes (scenes, times, cast, props, lines)
                                     for building the ledger / the logic review without reading full JSON
  seams    <session> [N ...]      -> last scene of epN-1 + first scene of epN for each written pair (seam pass)
  impact   <session> --episodes 3,4 | --facts F1,F2
                                  -> later (and earlier) episodes that depend on these episodes / facts
  next     <session> state|logic  -> prints the next free continuity/<stem>_vN version
  render   <state_vN.json>        -> writes state_vN.md next to it
  validate <logic_vN.json>        -> shape of a logic review, exit 1 on errors
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

CODES = {0: "state ledger", 1: "cause chain", 2: "knowledge", 3: "character status", 4: "props",
         5: "clock", 6: "seams", 7: "clues and setups", 8: "relations"}
STATUSES = {"dead", "gone", "back", "injured", "healed"}
PROP_STATUSES = {"with", "lost", "destroyed"}
LINKS = {"continues", "time_jump", "cutaway"}
FLASHBACK = re.compile(r"hồi tưởng|flashback|quá khứ", re.I)
DAY = re.compile(r"\b(?:ngày|day)\s*(\d+)", re.I)
LOGIC_KINDS = ("contradiction", "knowledge", "motive", "coincidence", "easier_path", "timeline",
               "cause_missing", "dropped_thread", "world_rule")
SEVERITIES = ("high", "medium", "low")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)\.json$", p.name)
    return int(m.group(1)) if m else 0


def _latest(dir_: Path, stem: str) -> Path | None:
    files = [p for p in dir_.glob(f"{stem}_v*.json") if re.fullmatch(rf"{re.escape(stem)}_v\d+\.json", p.name)]
    return max(files, key=_vnum) if files else None


def _episode_files(session: Path) -> dict[int, Path]:
    """Latest draft per episode; final/epNN.json when it is newer (same rule as _story_check.py)."""
    eps: dict[int, Path] = {}
    for p in (session / "episodes").glob("ep*_v*.json") if (session / "episodes").is_dir() else []:
        m = re.fullmatch(r"ep(\d+)_v\d+\.json", p.name)
        if m:
            eps[int(m.group(1))] = _latest(session / "episodes", f"ep{m.group(1)}")
    for p in (session / "final").glob("ep*.json") if (session / "final").is_dir() else []:
        m = re.fullmatch(r"ep(\d+)\.json", p.name)
        if m and (int(m.group(1)) not in eps or p.stat().st_mtime >= eps[int(m.group(1))].stat().st_mtime):
            eps[int(m.group(1))] = p
    return dict(sorted(eps.items()))


def _ep(x) -> int | None:
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def _filled(x) -> bool:
    return bool(x.strip()) if isinstance(x, str) else x is not None and x != [] and x != {}


def _norm(s) -> str:
    s = unicodedata.normalize("NFC", str(s or "")).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, code: int, msg: str):
        self.errors.append(f"[C{code}] {msg}")

    def warn(self, code: int, msg: str):
        self.warns.append(f"[C{code}] {msg}")


class Episode:
    """One written episode: scene order, searchable text per scene, who and what is on screen."""

    def __init__(self, data: dict):
        self.data = data
        self.scenes = [s for s in data.get("scenes") or [] if isinstance(s, dict)]
        self.order = {str(s.get("id")): i for i, s in enumerate(self.scenes)}
        self.text = [_norm(" ".join(self._scene_text(s))) for s in self.scenes]
        self.cliff = _norm(data.get("cliffhanger"))

    @staticmethod
    def _scene_text(s: dict) -> list[str]:
        out = [str(s.get("blocking") or "")]
        for b in s.get("beats") or []:
            out.append(str(b.get("action") or ""))
            out += [f"{a.get('does') or ''} {a.get('face') or ''} {a.get('holds') or ''}"
                    for a in b.get("acting") or [] if isinstance(a, dict)]
            out += [str(d.get("line") or "") for d in b.get("dialogue") or [] if isinstance(d, dict)]
        return out

    def has(self, quote, scene=None) -> bool:
        q = _norm(quote)
        if not q:
            return False
        if scene is not None and str(scene) in self.order:
            i = self.order[str(scene)]
            return q in self.text[i] or (i == len(self.scenes) - 1 and q in self.cliff)
        return any(q in t for t in self.text) or q in self.cliff

    def flashback(self, i: int) -> bool:
        s = self.scenes[i]
        return s.get("flashback") is True or bool(FLASHBACK.search(str(s.get("time_of_day") or "")))

    def on_screen(self, i: int) -> set[str]:
        s = self.scenes[i]
        if isinstance(s.get("cast"), dict) and s["cast"]:
            return set(s["cast"])
        return {str(c) for b in s.get("beats") or [] for c in b.get("characters") or [] if not str(c).startswith("voice")}

    def props(self, i: int) -> set[str]:
        return {str(p) for p in self.scenes[i].get("props") or []}


def _load_session(session: Path):
    bp, op = _latest(session, "bible"), _latest(session, "outline")
    b = _load(bp) if bp else {}
    o = _load(op) if op else {}
    inp = _load(session / "input.json") if (session / "input.json").exists() else {}
    n = int(inp.get("episodes") or o.get("episode_count") or len(o.get("episodes") or []) or 0)
    return bp, op, b, o, n


def check_outline(o: dict, n: int, r: Report) -> dict[str, int]:
    """C1: events, because (earlier events only), opens_from; warns on dead-end episodes."""
    rows = {_ep(x.get("episode")): x for x in o.get("episodes") or [] if isinstance(x, dict)}
    where: dict[str, int] = {}
    for e in range(1, n + 1):
        row = rows.get(e)
        if row is None:
            continue
        events = [x for x in row.get("events") or [] if isinstance(x, dict)]
        if not events:
            r.err(1, f"outline ep{e}: no events (what happens: 1-4 concrete events with ids E{e}.k)")
        for x in events:
            eid = x.get("id")
            if not _filled(eid) or not _filled(x.get("text")):
                r.err(1, f"outline ep{e}: event without id/text")
            elif eid in where:
                r.err(1, f"outline ep{e}: event id {eid} already used in ep{where[eid]}")
            else:
                where[eid] = e
    used: set[str] = set()
    for e in range(2, n + 1):
        row = rows.get(e)
        if row is None:
            continue
        because = [c for c in row.get("because") or [] if _filled(c)]
        used |= set(because)
        if not because:
            r.err(1, f"outline ep{e}: because is empty (which earlier event makes this episode happen?)")
        for c in because:
            if c not in where:
                r.err(1, f"outline ep{e}: because {c} is not an event id")
            elif where[c] >= e:
                r.err(1, f"outline ep{e}: because {c} is in ep{where[c]}, must be an earlier episode")
        if not _filled(row.get("opens_from")):
            r.err(1, f"outline ep{e}: opens_from is empty (how does it pick up the ep{e - 1} cliffhanger?)")
    for e in range(1, n):
        ids = [x.get("id") for x in (rows.get(e) or {}).get("events") or [] if isinstance(x, dict)]
        if ids and not used & set(ids):
            r.warn(1, f"outline ep{e}: no later episode lists its events in because (dead-end episode)")
    return where


def check_ledger(st: dict, files: dict[int, Path], eps: dict[int, Episode], b: dict, n: int,
                 session: Path, r: Report):
    built = {str(k): v for k, v in ((st.get("built_from") or {}).get("episodes") or {}).items()}
    for e, f in files.items():
        rel = str(f.relative_to(session))
        if str(e) not in built:
            r.err(0, f"state ledger does not cover ep{e:02d} (rebuild: continuity/state_vN+1)")
        elif built[str(e)] != rel:
            r.warn(0, f"state ledger built from {built[str(e)]}, current is {rel}: quotes re-checked against it")

    def pos(e, scene) -> tuple[int, int]:
        x = eps.get(e)
        return e, x.order.get(str(scene), -1) if x and scene is not None else -1

    def quoted(code, label, row, ep_key="ep", scene_key="scene", quote_key="quote") -> bool:
        e, scene = _ep(row.get(ep_key)), row.get(scene_key)
        if e is None or not 0 <= e <= n:
            r.err(code, f"{label}: {ep_key} must be 0..{n}")
            return False
        if e == 0 or e not in eps:
            return True
        x = eps[e]
        if scene is not None and str(scene) not in x.order:
            r.err(code, f"{label}: scene {scene} is not in ep{e:02d}")
            return False
        if not _filled(row.get(quote_key)):
            r.err(code, f"{label}: {quote_key} missing (a verbatim piece of ep{e:02d})")
            return False
        if not x.has(row[quote_key], scene):
            r.err(code, f"{label}: {quote_key} {row[quote_key]!r} not found in ep{e:02d}" + (f".{scene}" if scene else ""))
            return False
        return True

    # C2: knowledge
    facts = {}
    for x in st.get("facts") or []:
        fid = x.get("id")
        if not _filled(fid) or fid in facts:
            r.err(2, f"fact id missing or duplicate: {fid}")
            continue
        facts[fid] = x
        if not _filled(x.get("text")):
            r.err(2, f"{fid}: text is empty")
        quoted(2, fid, x)
    learned: dict[tuple, tuple[int, int]] = {}
    for x in st.get("knowledge") or []:
        c, f = x.get("character"), x.get("fact")
        label = f"knowledge {c}/{f}"
        if f not in facts:
            r.err(2, f"{label}: unknown fact")
            continue
        if quoted(2, label, x):
            p = pos(x["ep"], x.get("scene"))
            learned[(c, f)] = min(learned.get((c, f), p), p)
    for x in st.get("uses") or []:
        c, f, e = x.get("character"), x.get("fact"), _ep(x.get("ep"))
        label = f"use {c}/{f} ep{e}"
        if f not in facts:
            r.err(2, f"{label}: unknown fact")
            continue
        if not quoted(2, label, x) or not e:
            continue
        p = pos(e, x.get("scene"))
        fe = _ep(facts[f].get("ep"))
        if fe is not None and fe > e:
            r.err(2, f"{c} uses {f} in ep{e:02d}, but {f} only happens in ep{fe:02d}")
        k = learned.get((c, f))
        if k is None:
            r.err(2, f"{c} uses {f} in ep{e:02d} ({x.get('quote')!r}) but never learns it (no knowledge row)")
        elif k[0] > p[0] or (k[0] == p[0] and min(k[1], p[1]) >= 0 and k[1] > p[1]):
            r.err(2, f"{c} uses {f} in ep{e:02d}{'.' + str(x.get('scene')) if x.get('scene') else ''} "
                     f"before learning it in ep{k[0]:02d} ({x.get('quote')!r})")

    # C3 + C4: what is on screen after a status / prop change
    status: dict[str, list] = {}
    for x in st.get("status") or []:
        c = x.get("character")
        if x.get("status") not in STATUSES:
            r.err(3, f"status {c}: status must be one of {', '.join(sorted(STATUSES))}")
            continue
        if quoted(3, f"status {c} {x.get('status')}", x):
            status.setdefault(c, []).append((pos(x["ep"], x.get("scene")), x["status"]))
    props: dict[str, list] = {}
    for x in st.get("props") or []:
        pid = x.get("prop")
        if x.get("status") not in PROP_STATUSES:
            r.err(4, f"prop {pid}: status must be with/lost/destroyed")
            continue
        if quoted(4, f"prop {pid} {x['status']}", x):
            props.setdefault(pid, []).append((pos(x["ep"], x.get("scene")), x["status"]))

    def before(rows, p):
        """Last row in force at scene p: earlier rows, plus a return / find in this same scene."""
        last = None
        for q, s in sorted(rows):
            if q < p or (q == p and s in ("back", "with")):
                last = (q, s)
        return last

    flagged: set = set()
    for e, x in eps.items():
        for i in range(len(x.scenes)):
            if x.flashback(i):
                continue
            sid = x.scenes[i].get("id")
            for c in sorted(x.on_screen(i) & set(status)):
                last = before([(q, s) for q, s in status[c] if s in ("dead", "gone", "back")], (e, i))
                if last and last[1] in ("dead", "gone") and c not in flagged:
                    flagged.add(c)
                    r.err(3, f"{c} is {last[1]} since ep{last[0][0]:02d} but on screen in ep{e:02d}.{sid}"
                             + (" (add a 'back' status row where they return)" if last[1] == "gone" else ""))
            for pid in sorted(x.props(i) & set(props)):
                last = before(props[pid], (e, i))
                if last and last[1] != "with" and pid not in flagged:
                    flagged.add(pid)
                    r.err(4, f"{pid} is {last[1]} since ep{last[0][0]:02d} but in ep{e:02d}.{sid} props"
                             + (" (add a 'with' row where it is found)" if last[1] == "lost" else ""))

    # C8: relations change only with a cause
    pairs: dict[frozenset, list] = {}
    for x in st.get("relations") or []:
        pair = x.get("pair") or []
        if len(pair) != 2:
            r.err(8, f"relation needs a pair of 2 character ids: {pair}")
            continue
        if quoted(8, f"relation {'/'.join(map(str, pair))} ep{x.get('ep')}", x):
            pairs.setdefault(frozenset(pair), []).append((pos(x["ep"], x.get("scene")), x))
    for pair, rows in pairs.items():
        rows.sort(key=lambda t: t[0])
        for (_, a), (_, z) in zip(rows, rows[1:]):
            if _norm(a.get("state")) != _norm(z.get("state")) and not _filled(z.get("cause")):
                r.err(8, f"relation {'/'.join(sorted(pair))}: {a.get('state')!r} -> {z.get('state')!r} in "
                         f"ep{z.get('ep'):02d} with no cause")

    # C5: clock
    clock = {_ep(x.get("ep")): x for x in st.get("clock") or [] if _ep(x.get("ep"))}
    for e in eps:
        if e not in clock:
            r.warn(5, f"clock has no row for ep{e:02d}")
    prev = None
    for e in sorted(clock):
        x = clock[e]
        day = _ep(x.get("day"))
        if day is None or day < 1:
            r.err(5, f"clock ep{e:02d}: day must be an int >= 1")
            continue
        if x.get("flashback"):
            continue
        if prev and day < prev[1]:
            r.err(5, f"clock: ep{e:02d} is day {day}, before ep{prev[0]:02d} (day {prev[1]}); mark a flashback or fix the day")
        prev = (e, day)
    for row in b.get("setting_timeline") or []:
        e = _ep(row.get("episode"))
        m = DAY.search(str(row.get("time") or ""))
        if e in clock and m and _ep(clock[e].get("day")) and int(m.group(1)) != clock[e]["day"] and not clock[e].get("flashback"):
            r.err(5, f"ep{e:02d}: bible setting_timeline says day {m.group(1)} ({row.get('time')!r}), clock says day {clock[e]['day']}")

    # C6: seams
    seams = {_ep(x.get("ep")): x for x in st.get("seams") or [] if _ep(x.get("ep"))}
    for e in eps:
        if e < 2 or e - 1 not in eps:
            continue
        x = seams.get(e)
        if not x:
            r.err(6, f"no seam row for ep{e - 1:02d} -> ep{e:02d} (how does ep{e:02d} pick up the cliffhanger?)")
            continue
        prev_ep, cur = eps[e - 1], eps[e]
        cq, oq = x.get("cliffhanger_quote"), x.get("opening_quote")
        last = len(prev_ep.scenes) - 1
        if not _filled(cq) or not (_norm(cq) in prev_ep.cliff or (last >= 0 and _norm(cq) in prev_ep.text[last])):
            r.err(6, f"seam ep{e:02d}: cliffhanger_quote {cq!r} not in the last scene / cliffhanger of ep{e - 1:02d}")
        if not _filled(oq) or not (cur.scenes and _norm(oq) in cur.text[0]):
            r.err(6, f"seam ep{e:02d}: opening_quote {oq!r} not in the first scene of ep{e:02d}")
        link = x.get("link")
        if link not in LINKS:
            r.err(6, f"seam ep{e:02d}: link must be continues/time_jump/cutaway")
        elif link != "continues":
            res = _ep(x.get("resolved_ep"))
            if res is None or not e <= res <= n:
                r.err(6, f"seam ep{e:02d}: ep{e - 1:02d} cliffhanger is cut away ({link}) and never resolved (resolved_ep {e}..{n})")

    # C7: clues on screen, plants paid off
    never = {q.get("id") if isinstance(q, dict) else q for q in b.get("never_answered") or []}
    clue_rows: set = set()
    for x in st.get("clues") or []:
        if quoted(7, f"clue {x.get('question')} ep{x.get('ep')}", x):
            clue_rows.add((x.get("question"), x.get("ep")))
    for q in b.get("ledger_plan") or b.get("mystery_ledger") or []:
        if not isinstance(q, dict) or q.get("id") in never:
            continue
        for c in q.get("clue_eps") or []:
            if c in eps and (q.get("id"), c) not in clue_rows:
                r.err(7, f"{q.get('id')}: clue planned in ep{c:02d} is not on screen (no clues row with a quote)")
    complete = n > 0 and all(e in eps for e in range(1, n + 1))
    hooks, ids = 0, set()
    for x in st.get("setups") or []:
        sid = x.get("id")
        if not _filled(sid) or sid in ids:
            r.err(7, f"setup id missing or duplicate: {sid}")
            continue
        ids.add(sid)
        quoted(7, f"setup {sid} plant", x)
        pe, ep = _ep(x.get("payoff_ep")), _ep(x.get("ep"))
        if pe is None:
            if x.get("sequel_hook"):
                hooks += 1
            elif complete:
                r.err(7, f"setup {sid} ({x.get('plant')!r}, ep{ep}) is never paid off")
            continue
        if ep is not None and pe < ep:
            r.err(7, f"setup {sid}: payoff ep{pe:02d} comes before the plant ep{ep:02d}")
        elif pe in eps:
            quoted(7, f"setup {sid} payoff", x, "payoff_ep", "payoff_scene", "payoff_quote")
    if hooks > 1:
        r.err(7, f"{hooks} setups marked sequel_hook (at most 1)")


def run(session: Path, stage: str | None) -> tuple[Report, dict]:
    r = Report()
    bp, op, b, o, n = _load_session(session)
    files = _episode_files(session)
    stage = stage or ("episodes" if files else "outline")
    if not op:
        r.err(1, "no outline_vK.json")
        return r, {"stage": stage}
    check_outline(o, n, r)
    meta = {"stage": stage, "episodes": n, "outline": op.name, "state": None}
    if stage == "episodes" and files:
        sp = _latest(session / "continuity", "state")
        if not sp:
            r.err(0, "no continuity/state_vN.json (build the state ledger from the written episodes)")
        else:
            eps = {e: Episode(_load(f)) for e, f in files.items()}
            check_ledger(_load(sp), files, eps, b, n, session, r)
            meta["state"] = str(sp.relative_to(session))
        meta["checked_episodes"] = sorted(files)
    return r, meta


def check(argv: list[str]) -> int:
    session = Path(argv[0])
    stage = argv[argv.index("--stage") + 1] if "--stage" in argv else None
    out = Path(argv[argv.index("--json") + 1]) if "--json" in argv else session / "continuity_check.json"
    r, meta = run(session, stage)
    for w in r.warns:
        print(f"WARN  {w}")
    for e in r.errors:
        print(f"ERROR {e}")
    print(f"continuity ({meta.get('stage')}): {len(r.errors)} errors, {len(r.warns)} warnings")
    out.write_text(json.dumps({**meta, "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "ok": not r.errors, "errors": r.errors, "warnings": r.warns},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    return 1 if r.errors else 0


def _only(args: list[str]) -> set[int]:
    return {int(x) for a in args for x in a.split(",") if x.strip().isdigit()}


def _scene_lines(sc: dict, beats: list | None = None) -> list[str]:
    head = (f"  {sc.get('id')} [{sc.get('time_of_day')}{', FLASHBACK' if sc.get('flashback') else ''}] "
            f"{sc.get('loc_id') or ''} {sc.get('location') or ''}")
    cast = sc.get("cast")
    out = [head + (f" | cast {','.join(cast)}" if isinstance(cast, dict) and cast else "")
           + (f" | props {','.join(map(str, sc['props']))}" if sc.get("props") else "")]
    held: dict = {}
    for bt in sc.get("beats") if beats is None else beats:
        t = f"    {bt.get('start_sec')}s"
        if _filled(bt.get("action")):
            out.append(f"{t} > {bt['action']}")
        for a in bt.get("acting") or []:
            if isinstance(a, dict) and "holds" in a and held.get(a.get("character")) != a["holds"]:
                held[a.get("character")] = a["holds"]
                out.append(f"{t}   {a.get('character')} holds {a['holds'] or '-'}")
        for d in bt.get("dialogue") or []:
            if isinstance(d, dict) and _filled(d.get("line")):
                out.append(f"{t} {d.get('character')}{' (VO)' if d.get('voiceover') else ''}: {d['line']}")
    return out


def digest(session: Path, only: set[int]) -> int:
    for e, f in _episode_files(session).items():
        if only and e not in only:
            continue
        ep = _load(f)
        print(f"== ep{e:02d} {ep.get('title') or ''} ({f.relative_to(session)})")
        print(f"  ledger {json.dumps(ep.get('ledger') or {}, ensure_ascii=False)}")
        for sc in ep.get("scenes") or []:
            print("\n".join(_scene_lines(sc)))
        print(f"  CLIFFHANGER: {ep.get('cliffhanger') or '-'}")
    return 0


def seams(session: Path, only: set[int]) -> int:
    files = _episode_files(session)
    _, _, _, o, _ = _load_session(session)
    rows = {_ep(x.get("episode")): x for x in o.get("episodes") or [] if isinstance(x, dict)}
    for e in files:
        if e < 2 or e - 1 not in files or (only and e not in only):
            continue
        a, z = _load(files[e - 1]), _load(files[e])
        print(f"== ep{e - 1:02d} -> ep{e:02d}   outline opens_from: {(rows.get(e) or {}).get('opens_from') or '-'}")
        if a.get("scenes"):
            last = a["scenes"][-1]
            print("\n".join(_scene_lines(last, (last.get("beats") or [])[-3:])))
        print(f"  CLIFFHANGER: {a.get('cliffhanger') or '-'}")
        print("  ---- opens with")
        if z.get("scenes"):
            first = z["scenes"][0]
            print("\n".join(_scene_lines(first, (first.get("beats") or [])[:3])))
    return 0


def impact(session: Path, eps_arg: set[int], facts_arg: set[str]) -> int:
    """Episodes outside the targets that depend on them; prints JSON {episode: [reasons]}."""
    sp = _latest(session / "continuity", "state")
    st = _load(sp) if sp else {}
    _, _, b, o, n = _load_session(session)
    files = _episode_files(session)
    out: dict[int, set[str]] = {}

    def add(e, why):
        if isinstance(e, int) and e not in eps_arg and 1 <= e <= max(n, max(files, default=0)):
            out.setdefault(e, set()).add(why)

    facts = {x.get("id"): x for x in st.get("facts") or []}
    hit = set(facts_arg) | {f for f, x in facts.items() if _ep(x.get("ep")) in eps_arg}
    learned = {(x.get("character"), x.get("fact")) for x in st.get("knowledge") or [] if _ep(x.get("ep")) in eps_arg}
    for f in facts_arg:
        for x in st.get("knowledge") or []:
            if x.get("fact") == f:
                add(_ep(x.get("ep")), f"{x.get('character')} learns {f}")
    for x in st.get("uses") or []:
        c, f = x.get("character"), x.get("fact")
        if f in hit:
            add(_ep(x.get("ep")), f"uses {f} ({facts.get(f, {}).get('text', '')})".strip())
        elif (c, f) in learned:
            add(_ep(x.get("ep")), f"{c} uses {f}, learned in a changed episode")
    for x in st.get("setups") or []:
        pe, pl = _ep(x.get("ep")), _ep(x.get("payoff_ep"))
        if pe in eps_arg:
            add(pl, f"payoff of {x.get('id')} ({x.get('plant')})")
        if pl in eps_arg:
            add(pe, f"plant of {x.get('id')} ({x.get('plant')})")
    plan = {q.get("id"): q for q in b.get("ledger_plan") or [] if isinstance(q, dict)}
    for x in st.get("clues") or []:
        if _ep(x.get("ep")) in eps_arg and x.get("question") in plan:
            add(_ep(plan[x["question"]].get("answer_ep")), f"answers {x['question']} clued in ep{x['ep']:02d}")
    changed = [x for x in st.get("status") or [] if _ep(x.get("ep")) in eps_arg]
    changed_props = {x.get("prop") for x in st.get("props") or [] if _ep(x.get("ep")) in eps_arg}
    for e, f in files.items():
        x = Episode(_load(f))
        seen = set().union(*(x.on_screen(i) for i in range(len(x.scenes))))
        for s in changed:
            if e > s["ep"] and s.get("character") in seen:
                add(e, f"{s.get('character')} {s.get('status')} in ep{s['ep']:02d}")
        scene_props = set().union(*(x.props(i) for i in range(len(x.scenes))))
        for p in sorted(changed_props & scene_props):
            if e > min(eps_arg, default=0):
                add(e, f"{p} changes hands / state in a changed episode")
    ev = {x.get("id"): _ep(row.get("episode")) for row in o.get("episodes") or [] for x in row.get("events") or []
          if isinstance(x, dict)}
    for row in o.get("episodes") or []:
        for c in row.get("because") or []:
            if ev.get(c) in eps_arg:
                add(_ep(row.get("episode")), f"because {c}")
    for e in eps_arg:
        add(e - 1, f"seam with ep{e:02d}")
        add(e + 1, f"seam with ep{e:02d}")
    res = {str(e): sorted(w) for e, w in sorted(out.items()) if e in files}
    for e, w in res.items():
        print(f"ep{int(e):02d}: " + "; ".join(w))
    print(json.dumps({"targets": sorted(eps_arg), "facts": sorted(facts_arg), "state": sp.name if sp else None,
                      "depends": res}, ensure_ascii=False))
    return 0


def next_version(session: Path, stem: str) -> int:
    return max((_vnum(p) for p in (session / "continuity").glob(f"{stem}_v*.json")), default=0) + 1


def render(path: Path) -> int:
    st = _load(path)
    md = [f"# State ledger v{st.get('version')} ({st.get('created_at') or ''})", ""]

    def table(title, cols, rows):
        md.extend([f"## {title}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)])
        for x in rows:
            md.append("| " + " | ".join(str(x.get(c) if not isinstance(x.get(c), list) else "/".join(map(str, x[c])))
                                         .replace("|", "/").replace("None", "-") for c in cols) + " |")
        md.append("")

    table("Facts", ["id", "ep", "scene", "kind", "text"], st.get("facts") or [])
    table("Who knows what", ["character", "fact", "ep", "scene", "how"],
          sorted(st.get("knowledge") or [], key=lambda x: (str(x.get("character")), _ep(x.get("ep")) or 0)))
    table("Uses", ["character", "fact", "ep", "scene", "quote"], st.get("uses") or [])
    table("Character status", ["character", "ep", "scene", "status", "note"], st.get("status") or [])
    table("Props", ["prop", "ep", "scene", "holder", "status"], st.get("props") or [])
    table("Relations", ["pair", "ep", "scene", "state", "cause"], st.get("relations") or [])
    table("Clock", ["ep", "day", "time", "flashback"], st.get("clock") or [])
    table("Clues", ["question", "ep", "scene", "clue"], st.get("clues") or [])
    table("Setups", ["id", "ep", "plant", "payoff_ep", "payoff"], st.get("setups") or [])
    table("Seams", ["ep", "link", "cliffhanger_quote", "opening_quote", "resolved_ep"], st.get("seams") or [])
    path.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {path.with_suffix('.md')}")
    return 0


def validate(path: Path) -> int:
    errors = []
    try:
        r = _load(path)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR cannot read {path}: {e}")
        return 1
    if r.get("stage") not in ("outline", "episodes"):
        errors.append("stage must be outline or episodes")
    if not _filled(r.get("summary")):
        errors.append("summary is empty")
    ids = set()
    findings = r.get("findings") or []
    for f in findings:
        fid = f.get("id")
        if not fid or fid in ids:
            errors.append(f"finding id missing or duplicate: {fid}")
        ids.add(fid)
        if f.get("kind") not in LOGIC_KINDS:
            errors.append(f"{fid}: kind must be one of {', '.join(LOGIC_KINDS)}")
        if f.get("severity") not in SEVERITIES:
            errors.append(f"{fid}: severity must be high/medium/low")
        for k in ("evidence", "problem", "fix"):
            if not _filled(f.get(k)):
                errors.append(f"{fid}: {k} is empty")
        if not isinstance(f.get("where"), dict) or not f["where"].get("file"):
            errors.append(f"{fid}: where.file missing")
    verdict = "revise" if any(f.get("severity") == "high" for f in findings) else "pass"
    if r.get("verdict") != verdict:
        errors.append(f"verdict should be {verdict} (revise when any finding is high)")
    for e in errors:
        print(f"ERROR {e}")
    print(f"validate {path.name}: {len(errors)} errors, {len(findings)} findings")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "check" and rest and not rest[0].startswith("-"):
        return check(rest)
    if cmd == "digest" and rest:
        return digest(Path(rest[0]), _only(rest[1:]))
    if cmd == "seams" and rest:
        return seams(Path(rest[0]), _only(rest[1:]))
    if cmd == "impact" and rest:
        eps = _only(rest[rest.index("--episodes") + 1:rest.index("--episodes") + 2]) if "--episodes" in rest else set()
        facts = ({x.strip() for x in rest[rest.index("--facts") + 1].split(",") if x.strip()}
                 if "--facts" in rest else set())
        if eps or facts:
            return impact(Path(rest[0]), eps, facts)
    if cmd == "next" and len(rest) == 2 and rest[1] in ("state", "logic"):
        print(next_version(Path(rest[0]), rest[1]))
        return 0
    if cmd == "render" and rest:
        return render(Path(rest[0]))
    if cmd == "validate" and rest:
        return validate(Path(rest[0]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
