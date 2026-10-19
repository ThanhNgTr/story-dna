"""Export a series session as one offline HTML "story atlas" (tree, screenplays, documents, notes, refs).

The viewer (atlas_template.html) is the interactive-short-film viewer; a linear series becomes a chain of
`auto` exits with one ending. Approved reference images are embedded as small JPEG data URLs.

  python3 -m app.pipeline.atlas --session data/series/<slug>/<id> [--out file.html] [--no-images]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import assets as asset_images

TEMPLATE = Path(__file__).with_name("atlas_template.html")
IMAGE_WIDTH = 640
FRAME_WIDTH = 360  # scene frames repeat the same plates; keep them small


def _load(p: Path | None) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _text(p: Path | None) -> str:
    return p.read_text(encoding="utf-8") if p and p.exists() else ""


def _version(p: Path) -> int:
    m = re.search(r"_v(\d+)\.", p.name)
    return int(m.group(1)) if m else 0


def _pick(session: Path, final_name: str, pattern: str, folder: str = "") -> Path | None:
    """final/<name> when the series is finalized, else the newest draft version."""
    fin = session / "final" / final_name
    if fin.exists():
        return fin
    cand = list((session / folder).glob(pattern)) if (session / folder).exists() else []
    return max(cand, key=_version) if cand else None


def _episode_files(session: Path, n: int, ext: str) -> Path | None:
    return _pick(session, f"ep{n:02d}.{ext}", f"ep{n:02d}_v*.{ext}", "episodes")


def _mmss(sec) -> str:
    s = int(round(float(sec or 0)))
    return f"{s // 60:02d}:{s % 60:02d}"


def _names(bible: dict, registry: dict, episodes: list[dict]) -> dict[str, str]:
    names = {c["character_id"]: c.get("name") or c["character_id"]
             for c in bible.get("cast") or [] if isinstance(c, dict) and c.get("character_id")}
    for c in registry.get("characters") or []:
        names.setdefault(c.get("char_id"), c.get("name") or c.get("char_id"))
    for ep in episodes:
        for a in ep.get("new_assets") or []:
            if a.get("for"):
                names.setdefault(a["for"], a.get("desc", a["for"]).split(",")[0])
    return names


def screenplay_text(ep: dict, names: dict[str, str]) -> str:
    """Plain-text screenplay (the viewer shows scripts as preformatted text, not Markdown)."""
    who = lambda cid: names.get(cid, cid).upper()
    out = [f"{ep.get('title', '')} — tập {ep.get('episode')} ({ep.get('total_duration_sec', '')}s)"]
    if ep.get("logline"):
        out += ["", ep["logline"]]
    for sc in ep.get("scenes") or []:
        cast = ", ".join(f"{names.get(c, c)} ({o})" for c, o in (sc.get("cast") or {}).items())
        out += ["", "", f"{sc.get('id')}  [{_mmss(sc.get('start_sec'))}-{_mmss(sc.get('end_sec'))}]  "
                        f"{sc.get('int_ext', '')}. {str(sc.get('location', '')).upper()} — {sc.get('time_of_day', '')}"]
        if cast:
            out.append(f"  Cast: {cast}")
        for b in sc.get("beats") or []:
            out += ["", f"[{b.get('start_sec')}-{b.get('end_sec')}s] {b.get('shot_size', '')} · {b.get('camera', '')}",
                    b.get("action", "")]
            for d in b.get("dialogue") or []:
                tag = " (V.O.)" if d.get("voiceover") else ""
                out.append(f"\n                    {who(d.get('character', ''))}{tag}")
                if d.get("delivery"):
                    out.append(f"               ({d['delivery']})")
                out.append(f"          {d.get('line', '')}")
            if b.get("sound"):
                out.append(f"  Âm thanh: {b['sound']}")
    if ep.get("cliffhanger"):
        out += ["", "", f"CLIFFHANGER ({ep.get('cliffhanger_type', '')}): {ep['cliffhanger']}"]
    return "\n".join(out) + "\n"


def _clips(session: Path, n: int, names: dict[str, str], aspect: str) -> list[dict]:
    prompts = _load(session / "final" / "shots" / f"ep{n:02d}" / "prompts.json")
    clips = []
    for i, s in enumerate(prompts.get("shots") or [], 1):
        dur = round(float(s.get("duration_sec") or 0), 1)
        settings = lambda model, dur=dur: {"model": model, "duration_seconds": dur, "aspect_ratio": aspect,
                                  "mode": "Image to Video" if s.get("refs") else "Text to Video"}
        refs = "\n\nReference images: " + ", ".join(s["refs"]) if s.get("refs") else ""
        prompt = s.get("video_prompt", "") + refs
        # Veo / Flow makes 8s at most: clips over 8s carry veo_parts (one generation each)
        flow = "\n\n".join(f"PART {vp.get('part')} ({vp.get('start_sec')}-{vp.get('end_sec')}s)\n{vp.get('video_prompt', '')}"
                           for vp in s.get("veo_parts") or []) + refs if s.get("veo_parts") else prompt
        clips.append({
            "id": f"EP{n:02d}-C{i:02d}", "start": s.get("start_sec"), "end": s.get("end_sec"), "duration_seconds": dur,
            "scene": s.get("scene"),
            "dialogue": [{"speaker": names.get(d.get("character"), d.get("character")), "text": d.get("line")}
                         for d in s.get("dialogue") or []],
            "flow_prompt": flow, "seedance_prompt": prompt,
            "flow_settings": settings("Veo 3.1", min(dur, 8)), "seedance_settings": settings("Seedance 2.0"),
            "references": s.get("refs") or [], "status": "prompt_only", "rendered_video": None,
        })
    return clips


def _flat(v) -> str:
    """Registry fields can be strings, lists or {part: text} dicts; make one readable line."""
    if isinstance(v, dict):
        return "; ".join(_flat(x) for x in v.values() if x)
    if isinstance(v, list):
        return "; ".join(_flat(x) for x in v if x)
    return str(v or "")


def _data_url(src: Path, width: int = IMAGE_WIDTH) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(asset_images.thumbnail(src, width).read_bytes()).decode()


def _scene_frames(session: Path, nodes: list[dict], eps: dict[int, dict], names: dict[str, str]) -> list[dict]:
    """One frame per scene: heading, cast, beat actions; image = the approved plate of its location variant
    (a set reference, not a storyboard frame)."""
    approved = asset_images.approved_refs(session)
    frames = []
    for node in nodes:
        for i, sc in enumerate(eps[node["episode"]].get("scenes") or [], 1):
            key = sc.get("variant_id")
            beats = sc.get("beats") or []
            frame = {
                "id": f"{node['id']}-{sc.get('id', i)}", "node_id": node["id"], "order": i, "kind": "scene",
                "title": f"{sc.get('id')} · {sc.get('location', '')}",
                "description": " / ".join(b.get("action", "") for b in beats[:3]),
                "scene": f"{sc.get('int_ext', '')}. {sc.get('location', '')} — {sc.get('time_of_day', '')}",
                "time_range": f"{_mmss(sc.get('start_sec'))}-{_mmss(sc.get('end_sec'))}",
                "characters": [names.get(c, c) for c in sc.get("cast") or {}],
                "location": key or sc.get("loc_id", ""),
                "status": "reviewed",
            }
            if key in approved and (session / "assets" / approved[key]).is_file():
                frame["image_file"] = approved[key]
                frame["image"] = {"data_url": _data_url(session / "assets" / approved[key], FRAME_WIDTH)}
            frames.append(frame)
    return frames


def _references(session: Path, registry: dict) -> list[dict]:
    """Approved reference images (character sheets, outfits, location plates, props) as JPEG data URLs."""
    titles, descs = {}, {}
    for c in registry.get("characters") or []:
        titles[c["char_id"]] = f"{c.get('name')} — nhân dạng"
        descs[c["char_id"]] = " | ".join(_flat(c.get(k)) for k in ("face", "hair", "body") if c.get(k))
        for o in c.get("wardrobe") or []:
            titles[o["outfit_id"]] = f"{c.get('name')} — {o.get('name', o['outfit_id'])}"
            descs[o["outfit_id"]] = _flat(o.get("desc"))
    for loc in registry.get("locations") or []:
        for v in loc.get("variants") or []:
            titles[v["variant_id"]] = f"{loc.get('name')} — {v.get('time_of_day', '')}"
            descs[v["variant_id"]] = f"{_flat(loc.get('desc'))} {_flat(v.get('lighting'))}".strip()
    for p in registry.get("props") or []:
        titles[p["prop_id"]], descs[p["prop_id"]] = p.get("name", p["prop_id"]), _flat(p.get("desc"))
    index = asset_images.load_index(session)["items"]
    refs = []
    for key, rel in asset_images.approved_refs(session).items():
        src = session / "assets" / rel
        if not src.is_file():
            continue
        meta = next((i for i in index[key]["images"] if i["file"] == rel), {})
        refs.append({
            "id": key, "kind": index[key].get("kind", "reference"), "title": titles.get(key, key),
            "description": descs.get(key, ""), "prompt": meta.get("prompt", ""), "status": "reviewed",
            "image_file": rel,
            "image": {"data_url": _data_url(src)},
        })
    order = {"character": 0, "location": 1, "prop": 2}
    return sorted(refs, key=lambda r: (order.get(r["kind"], 3), r["id"]))


def _documents(session: Path, bible: dict, outline_md: str, bible_md: str) -> list[dict]:
    def bullets(items):
        return "\n".join(f"- {x}" for x in items if x)

    plot = bible.get("main_plot") or {}
    ending = bible.get("ending") or {}
    overview = "\n".join([
        f"# {bible.get('title', '')}", "", bible.get("logline", ""), "",
        "## Tiền đề", bible.get("premise", ""), "", "## Chủ đề", bible.get("theme", ""), "",
        "## Cốt truyện chính",
        bullets([f"**Câu hỏi trung tâm:** {plot.get('central_question', '')}",
                 f"**Mục tiêu nhân vật chính:** {plot.get('protagonist_goal', '')}"]), "",
        f"## Kết thúc ({ending.get('type', '')}, tập {ending.get('episode', '')})", ending.get("what_happens", ""), "",
        "## Cao trào", bullets(f"Tập {c.get('episode')} ({c.get('level')}): {c.get('event')}"
                              for c in bible.get("climaxes") or []),
    ])
    docs = [{"id": "overview", "title": "Tổng quan", "content": overview},
            {"id": "bible", "title": "Series bible", "content": bible_md},
            {"id": "outline", "title": "Dàn ý mùa", "content": outline_md}]
    extra = [("adaptation", "Bản đồ chuyển thể", session / "adaptation.md"),
             ("assets", "Nhân vật, bối cảnh, đạo cụ", _pick(session, "assets.md", "assets_v*.md", "assets")),
             ("editor", "Biên tập (review mới nhất)", max((session / "editor").glob("review_v*.md"), key=_version,
                                                         default=None) if (session / "editor").exists() else None)]
    docs += [{"id": i, "title": t, "content": _text(p)} for i, t, p in extra if _text(p).strip()]
    return docs


def build_payload(session: Path, with_images: bool = True) -> dict:
    session = session.resolve()
    bible = _load(_pick(session, "bible.json", "bible_v*.json"))
    outline = _load(_pick(session, "outline.json", "outline_v*.json"))
    registry = _load(_pick(session, "assets.json", "assets_v*.json", "assets"))
    planned = outline.get("episodes") or []
    eps = {o["episode"]: _load(_episode_files(session, o["episode"], "json")) for o in planned}
    names = _names(bible, registry, list(eps.values()))
    aspect = bible.get("aspect_ratio", "9:16")
    ending = bible.get("ending") or {}
    last = planned[-1]["episode"] if planned else 0

    nodes, scripts = [], {}
    for o in planned:
        n, ep = o["episode"], eps[o["episode"]]
        nid = f"EP{n:02d}"
        nxt = next((p for p in planned if p["episode"] > n), None)
        nodes.append({
            "id": nid, "episode": n, "title": f"{nid}: {o.get('title', '')}",
            "duration_seconds": ep.get("total_duration_sec") or outline.get("episode_sec") or 60,
            "ending": (ending.get("type", "end").upper() + " — " + bible.get("title", "")) if n == last else None,
            "early_exit": False, "requires": {}, "set": {},
            "exits": [{"id": f"A_{nid}_EP{nxt['episode']:02d}", "kind": "auto", "label": nxt.get("title", ""),
                       "to": f"EP{nxt['episode']:02d}", "when": {}, "set": {}, "bait": False,
                       "consequence": o.get("cliffhanger", "")}] if nxt else [],
            "script_file": str(_episode_files(session, n, "md") or ""),
            "synopsis": ep.get("logline") or o.get("logline", ""),
            "continuity_note": ep.get("cliffhanger") or o.get("cliffhanger", ""),
            "video_clips": _clips(session, n, names, aspect),
        })
        if ep:
            scripts[nid] = screenplay_text(ep, names)

    check = _load(session / "story_check.json")
    total = sum(nd["duration_seconds"] for nd in nodes)
    missing = [nd["id"] for nd in nodes if nd["id"] not in scripts]
    cast = {names.get(c.get("char_id"), c.get("char_id")): c.get("prompt_en", "")
            for c in registry.get("characters") or []}
    style = registry.get("style")
    setting = (bible.get("world") or {}).get("setting") if isinstance(bible.get("world"), dict) else bible.get("world")
    setting = setting.get("place", "") if isinstance(setting, dict) else str(setting or "")
    tree = {
        "project": {
            "id": f"{bible.get('skill', 'series')}-{session.name}", "title": bible.get("title") or session.name,
            "version": f"bible v{bible.get('version', '?')} / outline v{outline.get('version', '?')}",
            "logline": bible.get("logline", ""), "synopsis": bible.get("premise", ""),
            "episodes_per_route": str(len(nodes)), "target_duration_seconds": outline.get("episode_sec") or 60,
            "duration_tolerance_seconds": 5, "structure": "linear", "allow_early_endings": False,
            "max_unique_nodes": len(nodes), "language": bible.get("language", "vi"),
            "audience": "", "setting": setting,
            "content_target": "", "video_profiles": ["google-flow-veo-3.1", "seedance-2.0"],
            "video_prompt_profile": {"cast": cast, "style": json.dumps(style, ensure_ascii=False)
                                     if isinstance(style, (dict, list)) else (style or ""),
                                     "references": [], "flow_model": "Veo 3.1", "seedance_model": "Seedance 2.0",
                                     "aspect_ratio": aspect},
            "notes": f"Skill: {bible.get('skill', '')} {bible.get('skill_version', '')}. Session: {session.name}.",
        },
        "start": nodes[0]["id"] if nodes else "",
        "state": {"domains": {}, "initial": {}},
        "nodes": nodes,
    }
    payload = {
        "format": "interactive-short-film-project", "schema_version": 1, "tree": tree,
        "validation": {
            "valid": bool(check.get("ok", True)), "complete": not missing,
            "errors": [str(e) for e in check.get("errors") or []],
            "warnings": [str(w) for w in check.get("warnings") or []] + [f"{m}: chưa có kịch bản" for m in missing],
            "stats": {"unique_assets": len(nodes), "footage_seconds": total, "decision_count": 0, "bait_count": 0,
                      "route_count": 1, "min_episodes": len(nodes), "max_episodes": len(nodes),
                      "min_runtime_seconds": total, "max_runtime_seconds": total,
                      "endings": [{"node_id": nodes[-1]["id"], "ending": nodes[-1]["ending"], "early_exit": False,
                                   "count": 1, "min_episodes": len(nodes), "max_episodes": len(nodes)}] if nodes else [],
                      "routes": [" → ".join(nd["id"] for nd in nodes)]},
        },
        "scripts": scripts,
        "documents": _documents(session, bible, _text(_pick(session, "outline.md", "outline_v*.md")),
                                _text(_pick(session, "bible.md", "bible_v*.md"))),
        "visuals": {"frames": _scene_frames(session, nodes, eps, names) if with_images else [],
                    "references": _references(session, registry) if with_images else []},
        "review": {"schema_version": 1, "project_id": f"{bible.get('skill', 'series')}-{session.name}",
                   "notes": [], "deleted_notes": []},
    }
    revision = hashlib.sha256(json.dumps([tree, scripts], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    payload["meta"] = {"project_id": tree["project"]["id"], "revision_id": revision,
                       "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "script_count": len(scripts), "missing_scripts": missing}
    return payload


def render(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    title = payload["tree"]["project"]["title"].replace("&", "&amp;").replace("<", "&lt;")
    html = TEMPLATE.read_text(encoding="utf-8")
    return (html.replace("__LANG__", payload["tree"]["project"]["language"], 1)
                .replace("__TITLE__", f"Story Map — {title}", 1)
                .replace("__STORY_DATA__", data, 1))


def export(session: Path, out: Path | None = None, with_images: bool = True) -> Path:
    out = out or session / "final" / "atlas.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(build_payload(session, with_images)), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--no-images", action="store_true", help="skip embedding approved reference images")
    a = ap.parse_args(argv)
    out = export(a.session, a.out, not a.no_images)
    print(f"{out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
