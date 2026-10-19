#!/usr/bin/env python3
"""Deterministic helpers for /series-assets (no LLM).

  scan     <session>                 -> <session>/assets/_scan.json  (compact digest for the agent)
  next     <session>                 -> prints the next free assets version N
  validate <session> <assets_vN.json> -> coverage + schema check, exit 1 on errors
  render   <assets_vN.json>          -> writes assets_vN.md next to it
  lint     <session> [N ...]         -> check episodes (all, or numbers N) against the latest
                                        assets_vN.json: loc/variant/outfit/prop IDs, exit 1 on errors

Episode source per episode: the newer of final/epNN.json and the latest episodes/epNN_vK.json.
Episodes written against a registry carry per scene: loc_id, variant_id, cast {char_id: outfit_id},
referenced [char_id], props [prop_id] (see references/episode-contract.md).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NON_VISUAL = re.compile(r"^(voice|unknown|vo_|narrator)", re.I)


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _latest(dir_: Path, stem: str) -> Path | None:
    """Latest <stem>_vN.json in dir_."""
    best, best_n = None, -1
    for p in dir_.glob(f"{stem}_v*.json"):
        m = re.fullmatch(rf"{re.escape(stem)}_v(\d+)\.json", p.name)
        if m and int(m.group(1)) > best_n:
            best, best_n = p, int(m.group(1))
    return best


def _episode_files(session: Path) -> dict[int, Path]:
    eps: dict[int, Path] = {}
    ep_dir = session / "episodes"
    if ep_dir.is_dir():
        for p in ep_dir.glob("ep*_v*.json"):
            m = re.fullmatch(r"ep(\d+)_v\d+\.json", p.name)
            if m:
                n = int(m.group(1))
                eps[n] = _latest(ep_dir, f"ep{m.group(1)}")
    final = session / "final"
    if final.is_dir():
        for p in final.glob("ep*.json"):
            m = re.fullmatch(r"ep(\d+)\.json", p.name)
            # A draft re-written after approval (refine round) is newer than the final copy
            if m and (int(m.group(1)) not in eps or p.stat().st_mtime >= eps[int(m.group(1))].stat().st_mtime):
                eps[int(m.group(1))] = p
    return dict(sorted(eps.items()))


def _bible_file(session: Path) -> Path | None:
    return _latest(session, "bible") or (session / "final" / "bible.json" if (session / "final" / "bible.json").exists() else None)


def _name_patterns(cast: list[dict]) -> dict[str, re.Pattern]:
    # Case-sensitive, word-bounded: "Mai" must not match "ngày mai"
    return {c["character_id"]: re.compile(rf"(?<!\w){re.escape(c['name'])}(?!\w)")
            for c in cast if c.get("name")}


def scan(session: Path) -> Path:
    bible_p = _bible_file(session)
    if not bible_p:
        sys.exit(f"no bible_vN.json in {session}")
    bible = _load(bible_p)
    cast = bible.get("cast", [])
    cast_ids = {c["character_id"] for c in cast}
    names = _name_patterns(cast)
    canon_p = _latest(session, "canon")
    outline_p = _latest(session, "outline")
    prev_p = _latest(session / "assets", "assets") if (session / "assets").is_dir() else None

    episodes, loc_strings, appearances, unknown_ids = [], {}, {}, set()
    for n, f in _episode_files(session).items():
        ep = _load(f)
        scenes = []
        for sc in ep.get("scenes", []):
            present, by_name, actions, light = [], [], [], []
            for i, b in enumerate(sc.get("beats", []), 1):
                ids = [c for c in b.get("characters", []) or [] if isinstance(c, str)]
                for c in ids:
                    if c in cast_ids:
                        present.append(c)
                    elif not NON_VISUAL.match(c):
                        unknown_ids.add(c)
                text = b.get("action", "") or ""
                hit = [cid for cid, pat in names.items() if pat.search(text)]
                by_name += [c for c in hit if c not in ids]
                if text:
                    actions.append({"beat": i, "chars": sorted(set(ids) | set(hit)), "action": text})
                if b.get("lighting_color"):
                    light.append(b["lighting_color"])
            chars = sorted(set(present) | set(by_name))
            key = f"ep{n:02d}.{sc.get('id')}"
            loc_strings.setdefault(sc.get("location", ""), []).append(key)
            for c in chars:
                appearances.setdefault(c, set()).add(n)
            scenes.append({
                "scene": sc.get("id"), "heading": sc.get("heading"), "raw_location": sc.get("location"),
                "int_ext": sc.get("int_ext"), "time_of_day": sc.get("time_of_day"),
                "characters": chars, "matched_by_name_only": sorted(set(by_name) - set(present)),
                "lighting": sorted(set(light)), "actions": actions,
                # IDs the writer already set (episode-contract); null for older episodes
                "loc_id": sc.get("loc_id"), "variant_id": sc.get("variant_id"), "cast": sc.get("cast"),
                "referenced": sc.get("referenced"), "props": sc.get("props"),
            })
        episodes.append({"episode": n, "file": str(f.relative_to(session)), "title": ep.get("title"),
                         "new_assets": ep.get("new_assets") or [], "scenes": scenes})

    out = {
        "session": session.name, "slug": session.parent.name, "language": bible.get("language"),
        "aspect_ratio": bible.get("aspect_ratio"),
        "bible": str(bible_p.relative_to(session)),
        "canon": str(canon_p.relative_to(session)) if canon_p else None,
        "outline": str(outline_p.relative_to(session)) if outline_p else None,
        "prev_assets": str(prev_p.relative_to(session)) if prev_p else None,
        "bible_cast": [{k: c.get(k) for k in ("character_id", "name", "age", "tier", "role", "visual_signature")}
                       for c in cast],
        "bible_world": {k: bible.get("world", {}).get(k) for k in ("setting", "locations", "motifs", "color_rule")},
        "location_strings": loc_strings,
        "appearances": {c: sorted(v) for c, v in sorted(appearances.items())},
        "unknown_character_ids": sorted(unknown_ids),
        "episodes": episodes,
    }
    dest = session / "assets" / "_scan.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_sc = sum(len(e["scenes"]) for e in episodes)
    print(f"scan: {len(episodes)} episodes, {n_sc} scenes, {len(loc_strings)} distinct location strings, "
          f"{len(cast)} cast -> {dest}")
    return dest


def next_version(session: Path) -> int:
    p = _latest(session / "assets", "assets") if (session / "assets").is_dir() else None
    return int(re.search(r"_v(\d+)", p.name).group(1)) + 1 if p else 1


def validate(session: Path, assets_p: Path) -> int:
    a = _load(assets_p)
    scan_p = session / "assets" / "_scan.json"
    sc = _load(scan_p) if scan_p.exists() else _load(scan(session))
    errors, warns = [], []

    for key in ("characters", "locations", "props", "scene_map", "issues"):
        if not isinstance(a.get(key), list):
            errors.append(f"missing list '{key}'")
    if errors:
        return _report(errors, warns)

    chars = {c.get("char_id"): c for c in a["characters"]}
    outfits = {}
    for cid, c in chars.items():
        for k in ("name", "face", "hair", "body", "wardrobe", "prompt_en"):
            if not c.get(k):
                errors.append(f"{cid}: missing '{k}'")
        for o in c.get("wardrobe", []):
            oid = o.get("outfit_id", "")
            if not o.get("prompt_en"):
                warns.append(f"{oid}: outfit has no prompt_en")
            if not oid.startswith(f"{cid}_"):
                errors.append(f"{cid}: outfit_id '{oid}' must start with '{cid}_'")
            if oid in outfits:
                errors.append(f"duplicate outfit_id {oid}")
            outfits[oid] = cid
    for c in sc["bible_cast"]:
        if c["character_id"] not in chars:
            errors.append(f"bible character {c['character_id']} ({c['name']}) missing from registry")

    locs, variants = {}, {}
    for l in a["locations"]:
        lid = l.get("loc_id")
        if lid in locs:
            errors.append(f"duplicate loc_id {lid}")
        locs[lid] = l
        for k in ("name", "desc", "fixed_elements", "variants", "prompt_en"):
            if not l.get(k):
                errors.append(f"{lid}: missing '{k}'")
        for v in l.get("variants", []):
            variants[v.get("variant_id")] = lid
    prop_ids = {p.get("prop_id") for p in a["props"]}

    mapped = {}
    for m in a["scene_map"]:
        key = f"ep{int(m.get('episode', 0)):02d}.{m.get('scene')}"
        mapped[key] = m
        lid = m.get("loc_id")
        if lid is None:
            if not m.get("reason"):
                errors.append(f"{key}: loc_id null needs 'reason' (e.g. title card)")
        elif lid not in locs:
            errors.append(f"{key}: unknown loc_id {lid}")
        elif m.get("variant_id") and variants.get(m["variant_id"]) != lid:
            errors.append(f"{key}: variant {m['variant_id']} not a variant of {lid}")
        for cid, oid in (m.get("characters") or {}).items():
            if cid not in chars:
                errors.append(f"{key}: unknown char {cid}")
            elif outfits.get(oid) != cid:
                errors.append(f"{key}: {cid} wears unknown/foreign outfit {oid}")
        for pid in m.get("props", []) or []:
            if pid not in prop_ids:
                errors.append(f"{key}: unknown prop {pid}")
        for lid2 in m.get("extra_locs", []) or []:
            if lid2 not in locs:
                errors.append(f"{key}: unknown extra loc {lid2}")
        for cid in m.get("referenced", []) or []:
            if cid in (m.get("characters") or {}):
                errors.append(f"{key}: {cid} both on screen and referenced")

    for ep in sc["episodes"]:
        for s in ep["scenes"]:
            key = f"ep{ep['episode']:02d}.{s['scene']}"
            m = mapped.get(key)
            if not m:
                errors.append(f"{key}: scene not in scene_map ({s['raw_location']})")
                continue
            if s.get("loc_id") and s["loc_id"] != m.get("loc_id"):
                warns.append(f"{key}: episode says {s['loc_id']}, scene_map says {m.get('loc_id')} (log an issue)")
            worn = set((m.get("characters") or {}).keys()) | set(m.get("referenced") or [])
            for cid in s["characters"]:
                if cid not in worn:
                    (warns if cid in s["matched_by_name_only"] else errors).append(
                        f"{key}: {cid} on screen but no outfit assigned")

    # Outfit episode lists should match the scene map
    used: dict[str, set] = {}
    for m in a["scene_map"]:
        for oid in (m.get("characters") or {}).values():
            used.setdefault(oid, set()).add(int(m.get("episode", 0)))
    have_eps = bool(sc["episodes"])
    for c in a["characters"] if have_eps else []:
        for o in c.get("wardrobe", []):
            declared, real = set(o.get("episodes") or []), used.get(o.get("outfit_id"), set())
            if declared != real:
                warns.append(f"{o.get('outfit_id')}: episodes {sorted(declared)} != scene_map {sorted(real)}")
    p_used: dict[str, set] = {}
    for m in a["scene_map"]:
        for pid in m.get("props", []) or []:
            p_used.setdefault(pid, set()).add(int(m.get("episode", 0)))
    for p in a["props"] if have_eps else []:
        declared, real = set(p.get("episodes") or []), p_used.get(p.get("prop_id"), set())
        if declared != real:
            warns.append(f"{p.get('prop_id')}: episodes {sorted(declared)} != scene_map {sorted(real)}")
    for i in a["issues"]:
        if i.get("severity") not in ("high", "medium", "low"):
            warns.append(f"issue without severity high|medium|low: {str(i)[:80]}")
    return _report(errors, warns)


def lint(session: Path, only: set[int]) -> int:
    """Episodes vs registry. Run by the writer after each episode and in the continuity pass."""
    assets_p = _latest(session / "assets", "assets") if (session / "assets").is_dir() else None
    if not assets_p:
        print("lint: no assets/assets_vN.json yet -> run /series-assets first")
        return 1
    a = _load(assets_p)
    chars = {c["char_id"]: c for c in a.get("characters", [])}
    outfits = {o["outfit_id"]: (c["char_id"], o) for c in a.get("characters", []) for o in c.get("wardrobe", [])}
    locs = {l["loc_id"]: l for l in a.get("locations", [])}
    variants = {v["variant_id"]: l["loc_id"] for l in a.get("locations", []) for v in l.get("variants", [])}
    props = {p["prop_id"] for p in a.get("props", [])}
    errors, warns, last_outfit = [], [], {}
    files = _episode_files(session)
    for n, f in files.items():
        ep = _load(f)
        for na in ep.get("new_assets") or []:
            warns.append(f"ep{n:02d}: new_assets pending -> re-run /series-assets: {str(na)[:100]}")
        for sc in ep.get("scenes", []):
            key = f"ep{n:02d}.{sc.get('id')}"
            lid, cast, ref = sc.get("loc_id", "MISSING"), sc.get("cast") or {}, set(sc.get("referenced") or [])
            check = not only or n in only
            if lid == "MISSING":
                check and errors.append(f"{key}: no loc_id")
            elif lid is None:
                if check and not sc.get("loc_reason"):
                    errors.append(f"{key}: loc_id null needs loc_reason")
            elif lid not in locs:
                check and errors.append(f"{key}: unknown loc_id {lid}")
            else:
                v = sc.get("variant_id")
                if check and v and variants.get(v) != lid:
                    errors.append(f"{key}: variant {v} is not a variant of {lid}")
                elif check and not v:
                    warns.append(f"{key}: no variant_id")
                if check and sc.get("location") and not sc["location"].startswith(locs[lid]["name"]):
                    warns.append(f"{key}: location text '{sc['location']}' should start with '{locs[lid]['name']}'")
            on_screen = {c for b in sc.get("beats", []) for c in (b.get("characters") or []) if isinstance(c, str)}
            for c in sorted(on_screen):
                if c not in chars:
                    if check and not NON_VISUAL.match(c):
                        errors.append(f"{key}: character {c} not in registry")
                elif c not in cast and c not in ref:
                    check and errors.append(f"{key}: {c} on screen without outfit in scene cast")
            for c, oid in cast.items():
                owner = outfits.get(oid, (None, None))[0]
                if owner != c:
                    check and errors.append(f"{key}: {c} wears unknown/foreign outfit {oid}")
                    continue
                prev = last_outfit.get(c)
                if check and prev and prev[1] != oid:
                    warns.append(f"{key}: {c} outfit {prev[1]} ({prev[0]}) -> {oid}; when: '{outfits[oid][1].get('when', '')}'")
                last_outfit[c] = (key, oid)
            for pid in sc.get("props") or []:
                if check and pid not in props:
                    errors.append(f"{key}: unknown prop {pid}")
    print(f"lint against {assets_p.name}: {len(files)} episodes" + (f" (checked {sorted(only)})" if only else ""))
    return _report(errors, warns, "lint")


def _report(errors, warns, label="validate") -> int:
    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"{label}: {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


def render(assets_p: Path) -> Path:
    a = _load(assets_p)
    eps = sorted({int(m["episode"]) for m in a["scene_map"]})
    out = [f"# Asset registry — {a.get('series', '')} v{a.get('version', '')}", "",
           f"Session: {a.get('session', '')} | Created: {a.get('created_at', '')} | "
           f"Sources: {a.get('sources', {}).get('bible', '')} + {len(a.get('sources', {}).get('episodes', []))} episodes", ""]
    if a.get("style"):
        out += ["## Global look", ""] + [f"- **{k}**: {v}" for k, v in a["style"].items()] + [""]

    out += ["## Characters", ""]
    for c in a["characters"]:
        out += [f"### {c['char_id']} — {c['name']} ({c.get('tier', '')}, {c.get('age', '?')}"
                + (f", looks {c['apparent_age']}" if c.get("apparent_age") else "") + ")", ""]
        face = c.get("face", {})
        out += ["- **Face**: " + ("; ".join(f"{k}: {v}" for k, v in face.items()) if isinstance(face, dict) else str(face)),
                f"- **Hair**: {c.get('hair', '')}",
                "- **Body**: " + ("; ".join(f"{k}: {v}" for k, v in c['body'].items()) if isinstance(c.get('body'), dict) else str(c.get('body', ''))),
                f"- **Signature props**: {', '.join(c.get('signature_props', []))}",
                f"- **Never changes**: {', '.join(c.get('invariants', []))}",
                f"- **Prompt (EN)**: `{c.get('prompt_en', '')}`"]
        if c.get("inferred"):
            out.append(f"- *Inferred (not in script)*: {', '.join(c['inferred'])}")
        out += ["", "| Outfit | Description | When | Episodes |", "|---|---|---|---|"]
        out += [f"| {o['outfit_id']} {o.get('name', '')} | {o.get('desc', '')} | {o.get('when', '')} | {', '.join(map(str, o.get('episodes', [])))} |"
                for o in c.get("wardrobe", [])]
        out.append("")

    out += ["## Wardrobe matrix (episode -> outfit)", "",
            "| Character | " + " | ".join(f"E{e:02d}" for e in eps) + " |",
            "|---|" + "---|" * len(eps)]
    for c in a["characters"]:
        row = []
        for e in eps:
            worn = sorted({m["characters"][c["char_id"]].removeprefix(c["char_id"] + "_")
                           for m in a["scene_map"] if int(m["episode"]) == e and c["char_id"] in (m.get("characters") or {})})
            row.append(", ".join(worn) or "·")
        out.append(f"| {c['name']} | " + " | ".join(row) + " |")
    out.append("")

    out += ["## Locations", ""]
    for l in a["locations"]:
        out += [f"### {l['loc_id']} — {l['name']}" + (f" (bible {l['bible_id']})" if l.get("bible_id") else ""), "",
                f"{l.get('int_ext', '')}" + (f" | inside {l['parent']}" if l.get("parent") else ""), "",
                f"{l.get('desc', '')}", "",
                f"- **Layout**: {l.get('layout', '')}",
                f"- **Fixed elements**: {', '.join(l.get('fixed_elements', []))}",
                f"- **Aliases in scripts**: {'; '.join(l.get('aliases', []))}",
                f"- **Prompt (EN)**: `{l.get('prompt_en', '')}`", "",
                "| Variant | Time | Lighting / palette |", "|---|---|---|"]
        out += [f"| {v['variant_id']} | {v.get('time_of_day', '')} | {v.get('lighting', '')} |" for v in l.get("variants", [])]
        out.append("")

    if a["props"]:
        out += ["## Props", "", "| ID | Name | Look | Owner | Episodes |", "|---|---|---|---|---|"]
        out += [f"| {p['prop_id']} | {p.get('name', '')} | {p.get('desc', '')} | {p.get('owner') or ''} | "
                f"{', '.join(map(str, p.get('episodes', [])))} |" for p in a["props"]]
        out.append("")

    out += ["## Scene map", "", "| Scene | Location | Variant | Characters (outfit) | Props | Note |", "|---|---|---|---|---|---|"]
    for m in a["scene_map"]:
        who = ", ".join(f"{c}:{o.removeprefix(c + '_')}" for c, o in (m.get("characters") or {}).items())
        if m.get("referenced"):
            who += (", " if who else "") + "ref: " + ", ".join(m["referenced"])
        loc = " + ".join([m.get("loc_id") or "—"] + list(m.get("extra_locs") or []))
        out.append(f"| ep{int(m['episode']):02d}.{m['scene']} | {loc} | {m.get('variant_id') or ''} | {who} | "
                   f"{', '.join(m.get('props', []) or [])} | {m.get('reason') or m.get('note') or ''} |")
    out.append("")

    out += ["## Continuity issues", ""]
    if not a["issues"]:
        out.append("None found.")
    else:
        out += ["| Sev | Where | Type | Problem | Fix |", "|---|---|---|---|---|"]
        order = {"high": 0, "medium": 1, "low": 2}
        for i in sorted(a["issues"], key=lambda i: order.get(i.get("severity"), 3)):
            out.append(f"| {i.get('severity')} | {i.get('where', '')} | {i.get('type', '')} | {i.get('problem', '')} | {i.get('fix', '')} |")
    out.append("")

    dest = assets_p.with_suffix(".md")
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"render: {dest}")
    return dest


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, args = argv[0], [Path(x) for x in argv[1:]]
    if cmd == "scan":
        scan(args[0])
    elif cmd == "next":
        print(next_version(args[0]))
    elif cmd == "validate" and len(args) == 2:
        return validate(args[0], args[1])
    elif cmd == "render":
        render(args[0])
    elif cmd == "lint":
        return lint(args[0], {int(x) for a in argv[2:] for x in a.split(",") if x.strip()})
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
