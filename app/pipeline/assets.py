"""Reference images for the asset registry (/series-assets), made with Codex image_gen.

The registry (assets/assets_vN.json) says how things look; this module turns it into reference
images and keeps their review state in assets/images.json (the registry itself is never edited):

  characters/<char_id>/<char_id>_sheet_vK.png   face close-up + 3 full-body views, default outfit
  characters/<char_id>/<outfit_id>_vK.png       every other outfit, same person (sheet attached)
  locations/<loc_id>/<variant_id>_vK.png        empty plate per light variant (first variant attached)
  props/<prop_id>_vK.png                        the prop alone, text verbatim

Images start as `draft`; the user approves or rejects. Approved images are the `refs` that
/script-to-shotlist and video tools attach. Never overwrites an image: a redo is version K+1.

CLI:  python3 -m app.pipeline.assets plan|generate|status --session <dir> [--kinds character,outfit]
                                     [--ids char_01,loc_02_night] [--force]
      python3 -m app.pipeline.assets approve|reject --session <dir> <file relative to assets/>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .. import codex_runner, config

KINDS = ("character", "outfit", "location", "prop")
DEFAULT_KINDS = ("character", "outfit", "location")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_registry(session: Path) -> tuple[Path, dict]:
    best, best_n = None, -1
    for p in (session / "assets").glob("assets_v*.json"):
        m = re.fullmatch(r"assets_v(\d+)\.json", p.name)
        if m and int(m.group(1)) > best_n:
            best, best_n = p, int(m.group(1))
    if not best:
        raise RuntimeError(f"no assets/assets_vN.json in {session} (run /series-assets first)")
    return best, json.loads(best.read_text(encoding="utf-8"))


def _index_path(session: Path) -> Path:
    return session / "assets" / "images.json"


def load_index(session: Path) -> dict:
    p = _index_path(session)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"items": {}}


def save_index(session: Path, index: dict):
    p = _index_path(session)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def ref_image(session: Path, index: dict, key: str) -> Path | None:
    """Approved image of `key`, else its newest draft (a draft sheet still anchors its outfits)."""
    imgs = index["items"].get(key, {}).get("images", [])
    for status in ("approved", "draft"):
        cand = [i for i in imgs if i["status"] == status]
        if cand:
            return session / "assets" / cand[-1]["file"]
    return None


def approved_refs(session: Path) -> dict[str, str]:
    """{key: path relative to assets/} of approved images (what shotlist prompts attach)."""
    out = {}
    for key, item in load_index(session)["items"].items():
        ok = [i for i in item.get("images", []) if i["status"] == "approved"]
        if ok:
            out[key] = ok[-1]["file"]
    return out


def _default_outfit(c: dict) -> dict | None:
    ward = c.get("wardrobe") or []
    return next((o for o in ward if "default" in (o.get("when") or "").lower()), ward[0] if ward else None)


def _style(reg: dict, plate: bool) -> str:
    st = reg.get("style") or {}
    if plate:
        return st.get("prompt_suffix_en") or f"vertical {st.get('aspect_ratio', '9:16')} frame, photoreal cinematic still"
    # Sheets are landscape studio references: keep the medium/grade, drop the framing and lighting look
    return f"{st.get('medium', 'photoreal cinematic still')}, fine film grain"


def plan(session: Path, kinds=DEFAULT_KINDS, ids: set[str] | None = None, force: bool = False) -> list[dict]:
    """Ordered tasks: sheets before the outfits that attach them, first variant before the others."""
    reg_path, reg = latest_registry(session)
    index = load_index(session)
    tasks: list[dict] = []

    def add(key, kind, folder, prompt, refs_from=(), owner=None):
        if ids and key not in ids and (owner or key) not in ids:
            return
        imgs = index["items"].get(key, {}).get("images", [])
        if not force and any(i["status"] in ("approved", "draft") for i in imgs):
            return
        tasks.append({"key": key, "kind": kind, "folder": folder, "prompt": prompt,
                      "refs_from": list(refs_from), "registry": reg_path.name})

    if "character" in kinds or "outfit" in kinds:
        for c in reg.get("characters", []):
            cid, base = c["char_id"], _default_outfit(c)
            if "character" in kinds:
                add(cid, "character", f"characters/{cid}", (
                    "Use case: identity reference sheet for a film character.\n"
                    "Layout: landscape. One large face close-up on the left; three full-body views on the right "
                    "(front, three-quarter, side). Same person in every view. Plain light grey studio backdrop, "
                    "even soft light, no text, no labels, no watermark.\n"
                    f"Subject: {c.get('prompt_en', '')}\n"
                    + (f"Outfit: {base.get('prompt_en') or base.get('desc', '')}\n" if base else "")
                    + f"Style: {_style(reg, plate=False)}."))
            if "outfit" in kinds:
                for o in c.get("wardrobe", []):
                    if base and o["outfit_id"] == base["outfit_id"]:
                        continue
                    add(o["outfit_id"], "outfit", f"characters/{cid}", (
                        "Use case: costume reference for a film character.\n"
                        "Image 1 is the identity reference: keep the SAME person (face, hair, build).\n"
                        "Layout: landscape, two full-body views (front, three-quarter) on a plain light grey "
                        "studio backdrop, even soft light, no text, no watermark.\n"
                        f"Outfit ({o.get('when', '')}): {o.get('prompt_en') or o.get('desc', '')}\n"
                        f"Style: {_style(reg, plate=False)}."), refs_from=[cid], owner=cid)

    if "location" in kinds:
        for l in reg.get("locations", []):
            variants = l.get("variants") or [{"variant_id": f"{l['loc_id']}_base", "lighting": ""}]
            first = variants[0]["variant_id"]
            for v in variants:
                same = v["variant_id"] != first
                add(v["variant_id"], "location", f"locations/{l['loc_id']}", (
                    "Use case: empty location plate (set reference) for a film.\n"
                    + ("Image 1 is the same place at another time: keep layout, architecture and every fixed "
                       "element identical; change only time of day and light.\n" if same else "")
                    + f"Place: {l.get('prompt_en', '')}\n"
                    f"Fixed elements: {', '.join(l.get('fixed_elements', []))}\n"
                    f"Time and light: {v.get('prompt_en') or (v.get('time_of_day', '') + ', ' + v.get('lighting', ''))}\n"
                    "No people, no text overlays, no watermark. Wide establishing framing.\n"
                    f"Style: {_style(reg, plate=True)}."),
                    refs_from=[first] if same else [], owner=l["loc_id"])

    if "prop" in kinds:
        for p in reg.get("props", []):
            add(p["prop_id"], "prop", "props", (
                "Use case: prop reference for a film.\n"
                f"Prop: {p.get('prompt_en') or p.get('desc', '')}\n"
                "The prop alone, centred, on a neutral dark surface, soft key light; any text or numbers on "
                "it exactly as written above. No hands, no watermark.\n"
                f"Style: {_style(reg, plate=False)}."))
    return tasks


def _next_file(session: Path, folder: str, stem: str) -> Path:
    d = session / "assets" / folder
    n = 1 + max([int(m.group(1)) for p in d.glob(f"{stem}_v*.png")
                 if (m := re.fullmatch(rf"{re.escape(stem)}_v(\d+)\.png", p.name))] or [0])
    return d / f"{stem}_v{n}.png"


async def generate_images(job, session: Path, kinds=DEFAULT_KINDS, ids: set[str] | None = None,
                          force: bool = False) -> dict:
    tasks = plan(session, kinds, ids, force)
    job.step("images", "running", total=len(tasks), done=0, failed=0)
    done = failed = 0
    for t in tasks:
        index = load_index(session)
        refs = [r for k in t["refs_from"] if (r := ref_image(session, index, k))]
        if len(refs) < len(t["refs_from"]):
            job.log(f"skip {t['key']}: reference {t['refs_from']} has no image yet")
            failed += 1
            continue
        stem = f"{t['key']}_sheet" if t["kind"] == "character" else t["key"]
        out = _next_file(session, t["folder"], stem)
        res = await codex_runner.generate_image(t["prompt"], out, refs=refs, log=job.log)
        index = load_index(session)
        item = index["items"].setdefault(t["key"], {"kind": t["kind"], "images": []})
        if res.ok:
            done += 1
            item["images"].append({
                "file": str(out.relative_to(session / "assets")), "status": "draft", "created_at": now(),
                "sec": round(res.sec), "registry": t["registry"], "prompt": t["prompt"],
                "refs": [str(r.relative_to(session / "assets")) for r in refs]})
            item.pop("last_error", None)
        else:
            failed += 1
            item["last_error"] = {"at": now(), "error": res.error}
            job.log(f"FAILED {t['key']}: {res.error}")
        save_index(session, index)
        job.step("images", "running", total=len(tasks), done=done, failed=failed)
    job.step("images", "done", total=len(tasks), done=done, failed=failed)
    return {"images_done": done, "images_failed": failed}


def set_status(session: Path, file_rel: str, status: str) -> str:
    """approve -> the image becomes the reference of its key (previous approved -> 'old'); reject."""
    if status not in ("approved", "rejected", "draft"):
        raise ValueError(status)
    index = load_index(session)
    for key, item in index["items"].items():
        for img in item.get("images", []):
            if img["file"] == file_rel:
                if status == "approved":
                    for other in item["images"]:
                        if other is not img and other["status"] == "approved":
                            other["status"] = "old"
                img["status"], img["reviewed_at"] = status, now()
                save_index(session, index)
                return key
    raise KeyError(f"{file_rel} not in images.json")


def _registry_or_none(session: Path) -> tuple[Path, dict] | tuple[None, None]:
    try:
        return latest_registry(session)
    except RuntimeError:
        return None, None


def view_model(session: Path) -> dict | None:
    """Everything the web UI shows for the registry: data, images per key, pending work."""
    reg_path, reg = _registry_or_none(session)
    if not reg:
        return None
    index = load_index(session)

    def images(key):
        item = index["items"].get(key, {})
        imgs = [dict(i, name=Path(i["file"]).name) for i in item.get("images", []) if i["status"] != "old"]
        return {"images": list(reversed(imgs)), "error": (item.get("last_error") or {}).get("error")}

    eps = sorted({int(m["episode"]) for m in reg.get("scene_map", [])})
    for c in reg.get("characters", []):
        c["_img"] = images(c["char_id"])
        base = _default_outfit(c)
        for o in c.get("wardrobe", []):
            o["_img"] = images(o["outfit_id"])
            o["_default"] = o is base
        c["_matrix"] = [", ".join(sorted({m["characters"][c["char_id"]].removeprefix(c["char_id"] + "_")
                                          for m in reg.get("scene_map", []) if int(m["episode"]) == e
                                          and c["char_id"] in (m.get("characters") or {})})) for e in eps]
    for l in reg.get("locations", []):
        for v in l.get("variants", []):
            v["_img"] = images(v["variant_id"])
        l["_scenes"] = [f"ep{int(m['episode']):02d}.{m['scene']}" for m in reg.get("scene_map", [])
                        if m.get("loc_id") == l["loc_id"]]
    for p in reg.get("props", []):
        p["_img"] = images(p["prop_id"])
    order = {"high": 0, "medium": 1, "low": 2}
    reg["issues"] = sorted(reg.get("issues", []), key=lambda i: order.get(i.get("severity"), 3))
    pending = {k: len(plan(session, (k,))) for k in KINDS}
    counts = {"approved": 0, "draft": 0, "rejected": 0}
    for item in index["items"].values():
        for i in item.get("images", []):
            if i["status"] in counts:
                counts[i["status"]] += 1
    return {"reg": reg, "file": reg_path.name, "episodes": eps, "pending": pending, "counts": counts}


def _strip_ui(x):
    """Drop the view-model helper keys (_img, _matrix, ...) before a registry is written."""
    if isinstance(x, dict):
        return {k: _strip_ui(v) for k, v in x.items() if not k.startswith("_")}
    if isinstance(x, list):
        return [_strip_ui(v) for v in x]
    return x


def save_registry_edit(session: Path, base_file: str, data: dict, note: str = "") -> dict:
    """Manual edit from the UI -> assets_v(N+1).json/.md, validated like a /series-assets run.

    Refuses when the registry moved on since the page loaded (base_file is no longer the latest).
    """
    import subprocess
    import sys
    reg_path, _ = latest_registry(session)
    if reg_path.name != base_file:
        raise ValueError(f"Kho vừa có phiên bản mới ({reg_path.name}). Tải lại rồi sửa trên bản mới nhất.")
    n = int(re.search(r"_v(\d+)", reg_path.name).group(1)) + 1
    out = reg_path.with_name(f"assets_v{n}.json")
    if out.exists():
        raise ValueError(f"{out.name} đã tồn tại.")
    reg = _strip_ui(data)
    reg.update({"version": n, "created_at": now(),
                "edited": {"by": "manual", "from": reg_path.name, "note": note}})
    out.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    tool = config.SKILLS / "series-assets" / "_assets.py"
    v = subprocess.run([sys.executable, str(tool), "validate", str(session), str(out)],
                       capture_output=True, text=True, timeout=60)
    if v.returncode != 0:
        out.unlink()
        errs = [l.removeprefix("ERROR ") for l in v.stdout.splitlines() if l.startswith("ERROR")]
        raise ValueError("Kho không hợp lệ: " + "; ".join(errs[:5]))
    subprocess.run([sys.executable, str(tool), "render", str(out)], capture_output=True, text=True, timeout=60)
    from .screenplay import _log_round
    _log_round(session, "assets_manual", note or f"Sửa tay kho ngoại hình -> {out.name}",
               [f"assets/{out.name}", f"assets/{out.with_suffix('.md').name}"])
    return {"file": out.name, "version": n,
            "warnings": [l.removeprefix("WARN  ") for l in v.stdout.splitlines() if l.startswith("WARN")]}


def set_status_many(session: Path, files: list[str], status: str) -> int:
    done = 0
    for f in files:
        try:
            set_status(session, f, status)
            done += 1
        except KeyError:
            pass
    return done


def thumbnail(src: Path, width: int) -> Path:
    """Cached JPEG thumbnail under assets/.thumbs/ (sheets are ~2.5 MB PNGs)."""
    from PIL import Image
    assets = next(p for p in src.parents if p.name == "assets")
    dest = assets / ".thumbs" / f"{src.relative_to(assets).with_suffix('')}_{width}.jpg"
    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im.thumbnail((width, width * 2))
            im.convert("RGB").save(dest, quality=82)
    return dest


async def run_images_job(job) -> dict:
    """Job entry (kind 'images'): params slug, session_id, kinds[], ids[], force."""
    p = job.data["params"]
    session = config.SERIES / p["slug"] / p["session_id"]
    return await generate_images(job, session, tuple(p.get("kinds") or DEFAULT_KINDS),
                                 set(p.get("ids") or []) or None, bool(p.get("force")))


class _CliJob:
    data: dict = {}

    def log(self, msg: str):
        print(msg, flush=True)

    def step(self, name: str, status: str, **extra):
        print(f"[{name}] {status} {extra}", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "generate", "status", "approve", "reject"])
    ap.add_argument("file", nargs="?", help="approve/reject: image path relative to assets/")
    ap.add_argument("--session", required=True, type=Path)
    ap.add_argument("--kinds", default=",".join(DEFAULT_KINDS))
    ap.add_argument("--ids", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    kinds = tuple(k for k in a.kinds.split(",") if k in KINDS)
    ids = {i for i in a.ids.split(",") if i} or None
    if a.cmd == "plan":
        for t in plan(a.session, kinds, ids, a.force):
            print(f"{t['kind']:9} {t['key']:20} refs={t['refs_from']}")
    elif a.cmd == "generate":
        print(asyncio.run(generate_images(_CliJob(), a.session, kinds, ids, a.force)))
    elif a.cmd == "status":
        for key, item in load_index(a.session)["items"].items():
            states = ", ".join(f"{Path(i['file']).name}:{i['status']}" for i in item["images"])
            err = f"  last_error: {item['last_error']['error'][:80]}" if item.get("last_error") else ""
            print(f"{item['kind']:9} {key:20} {states}{err}")
    else:
        if not a.file:
            ap.error("approve/reject need the image path")
        print(set_status(a.session, a.file, "approved" if a.cmd == "approve" else "rejected"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
