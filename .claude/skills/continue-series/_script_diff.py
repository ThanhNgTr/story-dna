#!/usr/bin/env python3
"""
Compare the scripted dialogue/VO of produced episodes with what was actually said on screen.
Local and free: no Claude, no frames. Feeds /continue-series --canon-mode transcript.

Usage:
    python3 _script_diff.py --session data/series/<slug>/<sid> --manifest data/analyses/<run>/manifest.json \
        --produced 5 [--out data/analyses/<run>/script_diff.json]

Script side: final/epNN.json, else latest episodes/epNN_vK.json (beats[].dialogue[].line),
falling back to the Dialogue/VO column of the episode .md tables.
Screen side: WhisperX transcripts from the manifest (sources in episode order).

In-order word diff (like a text diff) of all scripted lines vs the spoken words. Per scripted line:
same (>= 80% of its words said in order), changed (partly said or reworded: shows what was said),
cut (not said). Spoken stretches with no scripted counterpart (>= 3 words) are reported as added.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

SAME = 0.8


def norm(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.split()


def _version(p: Path) -> int:
    m = re.search(r"_v(\d+)\.", p.name)
    return int(m.group(1)) if m else 0


def episode_files(session: Path, n: int) -> tuple[Path | None, Path | None]:
    final = session / "final"
    if (final / f"ep{n:02d}.json").exists() or (final / f"ep{n:02d}.md").exists():
        j, m = final / f"ep{n:02d}.json", final / f"ep{n:02d}.md"
        return (j if j.exists() else None), (m if m.exists() else None)
    js = sorted((session / "episodes").glob(f"ep{n:02d}_v*.json"), key=_version)
    ms = sorted((session / "episodes").glob(f"ep{n:02d}_v*.md"), key=_version)
    return (js[-1] if js else None), (ms[-1] if ms else None)


def lines_from_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    out = []
    for sc in data.get("scenes", []):
        for b in sc.get("beats", []):
            for d in b.get("dialogue", []) or []:
                if d.get("line"):
                    out.append({"who": d.get("character") or d.get("character_id"), "line": d["line"],
                                "vo": bool(d.get("voiceover")), "scene": sc.get("id")})
    return out


QUOTED = re.compile(r"[\"“”]([^\"“”]{2,})[\"“”]")


def lines_from_md(path: Path) -> list[dict]:
    out, col = [], None
    for row in path.read_text().splitlines():
        if not row.strip().startswith("|"):
            col = None if not row.strip() else col
            continue
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if col is None:
            col = next((i for i, c in enumerate(cells) if re.search(r"dialog|thoại|lời|vo\b", c, re.I)), None)
            continue
        if col >= len(cells) or set(cells[col]) <= set("-: "):
            continue
        cell = cells[col]
        quoted = QUOTED.findall(cell)
        for q in quoted or [re.sub(r"^[\w .()/-]{1,30}:\s*", "", cell)]:
            if q.strip() and q.strip() not in ("-", "—"):
                out.append({"who": None, "line": q.strip(), "vo": cell.upper().startswith("VO"), "scene": None})
    return out


def transcript_words(path: Path) -> list[tuple[str, float]]:
    words = []
    for seg in json.loads(path.read_text()).get("segments", []):
        for w in norm(seg.get("text", "")):
            words.append((w, seg.get("start", 0.0)))
    return words


def align(lines: list[dict], words: list[tuple[str, float]]) -> dict:
    """In-order diff of the scripted word stream vs the spoken word stream (like a text diff)."""
    tokens = [w for w, _ in words]
    script, owner = [], []
    for i, ln in enumerate(lines):
        for w in norm(ln["line"]):
            script.append(w)
            owner.append(i)
    sm = SequenceMatcher(None, script, tokens, autojunk=False)
    equal = [0] * len(lines)
    span: dict[int, list[int]] = {}
    added = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("equal", "replace"):
            for k in range(i1, i2):
                line = owner[k]
                if op == "equal":
                    equal[line] += 1
                # map script token k to its screen position (proportional inside a replace block)
                j = j1 + (k - i1) if op == "equal" else j1 + int((k - i1) * (j2 - j1) / max(1, i2 - i1))
                if j < j2:
                    span.setdefault(line, []).append(j)
        if op == "insert" and j2 - j1 >= 3:
            added.append({"screen": " ".join(tokens[j1:j2]), "t_sec": round(words[j1][1], 1)})
        if op == "replace" and (j2 - j1) - (i2 - i1) >= 5:  # much more said than scripted here
            added.append({"screen": " ".join(tokens[j1:j2]), "t_sec": round(words[j1][1], 1), "partly_replaces_script": True})
    result = {"same": 0, "changed": [], "cut": [], "added": added}
    for i, ln in enumerate(lines):
        n = len(norm(ln["line"]))
        if not n:
            continue
        ratio = equal[i] / n
        if ratio >= SAME:
            result["same"] += 1
        elif i in span and ratio >= 0.25 or (i in span and len(span[i]) >= max(2, n // 2)):
            a, b = min(span[i]), max(span[i]) + 1
            result["changed"].append({"script": ln["line"], "screen": " ".join(tokens[a:b]),
                                      "words_kept": round(ratio, 2), "t_sec": round(words[a][1], 1), "who": ln["who"]})
        else:
            result["cut"].append({"script": ln["line"], "who": ln["who"], "words_kept": round(ratio, 2)})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--session", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--produced", type=int, required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    session, manifest_path = Path(args.session), Path(args.manifest)
    m = json.loads(manifest_path.read_text())
    sources = [s for s in m["sources"] if s.get("transcript_path")]
    one_per_episode = len(sources) == args.produced
    report = {"produced": args.produced, "mapping": "one video per episode" if one_per_episode
              else f"{len(sources)} video(s) for {args.produced} episodes: lines matched anywhere in all transcripts",
              "episodes": []}

    all_words = [w for s in sources for w in transcript_words(Path(s["transcript_path"]))]
    for n in range(1, args.produced + 1):
        jpath, mpath = episode_files(session, n)
        lines = lines_from_json(jpath) if jpath else (lines_from_md(mpath) if mpath else [])
        src = sources[n - 1] if one_per_episode else None
        words = transcript_words(Path(src["transcript_path"])) if src else all_words
        ep = {"episode": n, "script_file": str(jpath or mpath) if (jpath or mpath) else None,
              "video": src["filename"] if src else None, "script_lines": len(lines)}
        if not lines:
            ep["note"] = "no script found for this episode: use the transcript as canon"
        else:
            ep.update(align(lines, words))
            if not one_per_episode:
                ep["added"] = []  # cannot attribute extra lines to an episode when videos != episodes
        report["episodes"].append(ep)

    out = Path(args.out) if args.out else manifest_path.parent / "script_diff.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    for ep in report["episodes"]:
        print(f"ep{ep['episode']:02d}: {ep['script_lines']} lines, same {ep.get('same', 0)}, "
              f"changed {len(ep.get('changed', []))}, cut {len(ep.get('cut', []))}, added {len(ep.get('added', []))}")
    print(str(out))


if __name__ == "__main__":
    main()
