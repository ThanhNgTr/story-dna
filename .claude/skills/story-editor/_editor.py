#!/usr/bin/env python3
"""Deterministic helpers for /story-editor (no LLM).

  next     <session>              -> prints the next free review version N
  validate <review_vN.json>       -> shape + score/verdict consistency, exit 1 on errors
  latest   <session>              -> prints the latest editor/review_vN.json path (empty if none)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

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


def main(argv: list[str]) -> int:
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
