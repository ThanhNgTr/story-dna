#!/usr/bin/env python3
"""Deterministic helpers for /story-editor (no LLM).

  next     <session>              -> prints the next free review version N
  validate <review_vN.json>       -> shape + score/verdict consistency, exit 1 on errors
  latest   <session>              -> prints the latest editor/review_vN.json path (empty if none)
  plan     <session> [F1,F3|all] [--review <file>]
                                  -> writes editor/apply_plan.json for --apply: chosen findings, source and
                                     target file per bible/outline/episode, episode packages for subagents;
                                     --review: another findings file (continuity/logic_vN.json), plan and
                                     notes then go next to it
  render   <epNN_vK.json>...      -> writes the .md screenplay next to each episode JSON (app's renderer)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAX_PACKAGES = 4  # parallel subagents in apply mode
DIMENSIONS = ("theme", "protagonist", "supporting_cast", "antagonist", "dialogue",
              "setup_payoff", "stakes", "emotion", "originality")
SEVERITIES = ("high", "medium", "low")


def _versions(session: Path, stem: str) -> dict[int, Path]:
    out = {}
    for p in (session / "editor").glob(f"{stem}_v*.json"):
        m = re.fullmatch(rf"{stem}_v(\d+)\.json", p.name)
        if m:
            out[int(m.group(1))] = p
    return out


def latest(session: Path, stem: str = "review") -> Path | None:
    v = _versions(session, stem)
    return v[max(v)] if v else None


def next_version(session: Path) -> int:
    return max(_versions(session, "review"), default=0) + 1


def verdict_of(scores: dict) -> tuple[float, str]:
    vals = [int(scores[d]["score"]) for d in DIMENSIONS if d in scores]
    avg = round(sum(vals) / len(vals), 1) if vals else 0.0
    ok = len(vals) == len(DIMENSIONS) and min(vals) >= 3 and avg >= 3.5
    return avg, "pass" if ok else "revise"


def validate(path: Path) -> int:
    errors, warns = [], []
    try:
        r = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR cannot read {path}: {e}")
        return 1
    if r.get("stage") not in ("outline", "episodes"):
        errors.append("stage must be outline or episodes")
    for k in ("summary", "theme_statement"):
        if not str(r.get(k) or "").strip():
            errors.append(f"{k} is empty")
    scores = r.get("scores") or {}
    for d in DIMENSIONS:
        s = scores.get(d)
        if not isinstance(s, dict):
            errors.append(f"scores.{d} missing")
            continue
        if not isinstance(s.get("score"), int) or not 1 <= s["score"] <= 5:
            errors.append(f"scores.{d}.score must be an int 1-5")
        if not str(s.get("why") or "").strip():
            errors.append(f"scores.{d}.why is empty")
        if isinstance(s.get("score"), int) and s["score"] > 2 and not s.get("evidence"):
            errors.append(f"scores.{d}: score > 2 needs evidence")
    if not errors:
        avg, verdict = verdict_of(scores)
        if abs(float(r.get("average") or 0) - avg) > 0.05:
            errors.append(f"average should be {avg}")
        if r.get("verdict") != verdict:
            errors.append(f"verdict should be {verdict}")
    findings = r.get("findings") or []
    if not 1 <= len(findings) <= 25:
        warns.append(f"{len(findings)} findings (expected 5-20)")
    ids = set()
    for f in findings:
        fid = f.get("id")
        if not fid or fid in ids:
            errors.append(f"finding id missing or duplicate: {fid}")
        ids.add(fid)
        if f.get("dimension") not in DIMENSIONS:
            errors.append(f"{fid}: dimension must be one of {', '.join(DIMENSIONS)}")
        if f.get("severity") not in SEVERITIES:
            errors.append(f"{fid}: severity must be high/medium/low")
        for k in ("evidence", "problem", "fix"):
            if not str(f.get(k) or "").strip():
                errors.append(f"{fid}: {k} is empty")
        if not isinstance(f.get("where"), dict) or not f["where"].get("file"):
            errors.append(f"{fid}: where.file missing")
    if len(r.get("strengths") or []) < 2:
        warns.append("fewer than 2 strengths")
    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"validate {path.name}: {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)\.json$", p.name)
    return int(m.group(1)) if m else 0


def _latest_doc(session: Path, kind: str) -> Path | None:
    files = [p for p in session.glob(f"{kind}_v*.json") if re.fullmatch(rf"{kind}_v\d+\.json", p.name)]
    return max(files, key=_vnum) if files else None


def _episode_files(session: Path) -> dict[int, tuple[Path, Path]]:
    """n -> (source, target): source = latest draft, or final/epNN.json when newer; target = next draft."""
    drafts: dict[int, list[Path]] = {}
    for p in (session / "episodes").glob("ep*_v*.json"):
        m = re.fullmatch(r"ep(\d+)_v\d+\.json", p.name)
        if m:
            drafts.setdefault(int(m.group(1)), []).append(p)
    out = {}
    for n, files in drafts.items():
        last = max(files, key=_vnum)
        fin = session / "final" / f"ep{n:02d}.json"
        src = fin if fin.exists() and fin.stat().st_mtime > last.stat().st_mtime else last
        out[n] = (src, session / "episodes" / f"ep{n:02d}_v{_vnum(last) + 1}.json")
    return out


def _touches(f: dict, n_eps: list[int]) -> set:
    """bible / outline / episode numbers a finding rewrites (its `affects` plus `where`)."""
    out: set = set()
    where = f.get("where") or {}
    tokens = [str(x).lower() for x in (f.get("affects") or [])] + [str(where.get("file") or "").lower()]
    for t in tokens:
        if t.startswith("bible"):
            out.add("bible")
        elif t.startswith("outline"):
            out.add("outline")
        elif t in ("all", "all_episodes", "episodes"):
            out.update(n_eps)
        elif m := re.search(r"ep(\d+)", t):
            out.add(int(m.group(1)))
    if isinstance(where.get("episode"), int):
        out.add(where["episode"])
    return out


def _packages(eps: dict[int, list[str]]) -> list[dict]:
    """Episodes -> at most MAX_PACKAGES groups with balanced finding counts (episodes of a group in order)."""
    if not eps:
        return []
    k = min(MAX_PACKAGES, max(1, (len(eps) + 1) // 2))
    bins: list[dict] = [{"episodes": [], "load": 0} for _ in range(k)]
    for n in sorted(eps, key=lambda n: (-len(eps[n]), n)):
        b = min(bins, key=lambda b: (b["load"], len(b["episodes"])))
        b["episodes"].append(n)
        b["load"] += len(eps[n])
    out = []
    for b in bins:
        if b["episodes"]:
            ns = sorted(b["episodes"])
            out.append({"episodes": ns, "findings": sorted({i for n in ns for i in eps[n]}, key=_fid)})
    return sorted(out, key=lambda p: p["episodes"][0])


def _fid(i: str) -> int:
    m = re.search(r"\d+", i)
    return int(m.group()) if m else 0


def plan(session: Path, ids: str = "", review: Path | None = None) -> int:
    session = session.resolve()
    review = review.resolve() if review else latest(session)
    if not review or not review.exists():
        print(f"ERROR no {review or 'editor/review_vN.json'}")
        return 1
    out_dir = review.parent
    r = json.loads(review.read_text(encoding="utf-8"))
    findings = r.get("findings") or []
    if ids.strip().lower() == "all":
        chosen = findings
    elif ids.strip():
        want = [x.strip() for x in ids.split(",") if x.strip()]
        unknown = sorted(set(want) - {f.get("id") for f in findings})
        if unknown:
            print(f"ERROR unknown finding ids: {', '.join(unknown)}")
            return 1
        chosen = [f for f in findings if f.get("id") in want]
    else:
        chosen = [f for f in findings if f.get("severity") in ("high", "medium")]
    try:
        inp = json.loads((session / "input.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        inp = {}
    produced = int(inp.get("produced_upto") or 0)
    ep_files = _episode_files(session)
    rel = lambda p: str(p.relative_to(session))  # noqa: E731

    docs: dict[str, dict] = {}
    eps: dict[int, list[str]] = {}
    skipped = []
    for f in sorted(chosen, key=lambda f: _fid(f.get("id", ""))):
        fid = f.get("id")
        for t in sorted(_touches(f, sorted(ep_files)), key=str):
            if t in ("bible", "outline"):
                src = _latest_doc(session, t)
                if src:
                    d = docs.setdefault(t, {"source": rel(src), "target": f"{t}_v{_vnum(src) + 1}.json", "findings": []})
                    d["findings"].append(fid)
            elif t <= produced:
                skipped.append({"id": fid, "episode": t, "reason": "produced episode (canon) is never rewritten"})
            elif t in ep_files:
                eps.setdefault(t, []).append(fid)
            else:
                skipped.append({"id": fid, "episode": t, "reason": "episode has no script"})

    out = {
        "review": rel(review),
        "findings": [f.get("id") for f in chosen],
        "docs": docs,
        "episodes": {str(n): {"source": rel(ep_files[n][0]), "target": rel(ep_files[n][1]), "findings": eps[n]}
                     for n in sorted(eps)},
        "packages": _packages(eps),
        "notes_file": rel(out_dir / "apply_notes.json"),
        "skipped": skipped,
    }
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "apply_plan.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"plan {rel(path)}: {len(chosen)} findings, docs {sorted(docs) or '-'}, "
          f"{len(eps)} episodes in {len(out['packages'])} packages, {len(skipped)} skipped")
    for i, pk in enumerate(out["packages"], 1):
        print(f"  package {i}: episodes {pk['episodes']} findings {pk['findings']}")
    return 0


def render(paths: list[Path]) -> int:
    sys.path.insert(0, str(ROOT))
    from app.pipeline.screenplay import render_md
    for p in paths:
        ep = json.loads(p.read_text(encoding="utf-8"))
        p.with_suffix(".md").write_text(render_md(ep), encoding="utf-8")
        print(f"wrote {p.with_suffix('.md')}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "plan":
        review = Path(argv[argv.index("--review") + 1]) if "--review" in argv else None
        rest = [a for i, a in enumerate(argv[2:], 2) if a != "--review" and argv[i - 1] != "--review"]
        return plan(Path(argv[1]), rest[0] if rest else "", review)
    if len(argv) >= 2 and argv[0] == "render":
        return render([Path(a) for a in argv[1:]])
    if len(argv) != 2:
        print(__doc__)
        return 2
    cmd, arg = argv[0], Path(argv[1])
    if cmd == "next":
        print(next_version(arg))
    elif cmd == "latest":
        print(latest(arg) or "")
    elif cmd == "validate":
        return validate(arg)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
