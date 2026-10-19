"""Vietnamese summaries for the UI (the analysis and the skills are written in English).

  <run>/summary_vi.json                                  what the reference video is, why it hooks
  data/skills-generated/write-series-<slug>_summary_vi.json   what a writing style does, its rules

One cheap Claude call each (Sonnet, read + write only). Run automatically after an analysis or a
skill build; failures there never fail the parent job. Also a job of its own ("summary") for
analyses and skills made before this existed.
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import config
from ..claude_runner import run_claude
from ..jobs import Job
from . import series

MODEL = "sonnet"

RUN_SCHEMA = """{
  "title_vi": "tên phim/series (giữ tên gốc nếu là tên riêng)",
  "genre_vi": "thể loại, một cụm",
  "logline_vi": "1 câu",
  "synopsis_vi": "6-10 câu, kể đúng theo thứ tự truyện",
  "characters": [{"name": "tên trong video", "tier": "main|supporting|minor", "role_vi": "vai trò, 1 cụm", "desc_vi": "1-2 câu: là ai, muốn gì, trông thế nào"}],
  "why_it_hooks_vi": ["3-6 ý: vì sao người xem bị cuốn"],
  "style_vi": {"story": "1-2 câu", "pacing": "1-2 câu, có số liệu nếu có", "camera": "1-2 câu", "sound": "1-2 câu", "color": "1-2 câu"},
  "episodes_hint_vi": "1-2 câu: video chia thành tập 1-2 phút thế nào"
}"""

SKILL_SCHEMA = """{
  "version": "<the skill's frontmatter version, e.g. v2>",
  "tagline_vi": "1 câu ngắn: phong cách này kể chuyện thế nào",
  "description_vi": "3-5 câu dễ hiểu cho người viết",
  "best_for_vi": ["2-4 loại ý tưởng hợp với phong cách này"],
  "not_for_vi": ["1-3 loại ý tưởng không hợp"],
  "rules_vi": {
    "story": ["3-5 luật về cấu trúc mùa / tập, bí ẩn, cliffhanger"],
    "characters": ["2-4 luật về nhân vật"],
    "pacing": ["2-4 luật về nhịp, độ dài shot, có số liệu"],
    "camera": ["2-3 luật"],
    "sound": ["2-3 luật"],
    "color": ["2-3 luật"]
  }
}"""


def run_summary_path(run_dir: Path) -> Path:
    return run_dir / "summary_vi.json"


def skill_summary_path(slug: str) -> Path:
    return config.DATA / "skills-generated" / f"write-series-{slug}_summary_vi.json"


def load(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


async def summarize_run(job: Job, run_dir: Path, force: bool = False) -> bool:
    out = run_summary_path(run_dir)
    if load(out) and not force:
        return True
    if not (run_dir / "dna.json").exists():
        job.log("[summary] no dna.json yet; skip")
        return False
    srcs = [run_dir / f for f in ("dna.json", "story.md", "film_analysis.md") if (run_dir / f).exists()]
    prompt = (
        "Đọc các file phân tích video sau (tiếng Anh): " + ", ".join(str(s) for s in srcs) + ".\n"
        f"Viết tóm tắt TIẾNG VIỆT cho người dùng không rành tiếng Anh vào đúng file {out} (JSON hợp lệ, UTF-8), "
        f"đúng cấu trúc:\n{RUN_SCHEMA}\n"
        "Chỉ dùng thông tin có trong các file; không bịa. Văn phong rõ ràng, ngắn gọn, không emoji. "
        "Chỉ ghi file đó, không sửa file nào khác. Trả lời 'ok' khi xong."
    )
    res = await run_claude(prompt, model=MODEL, log=lambda s: job.log(f"[summary] {s}"), timeout_sec=900)
    job.add_cost(res.cost_usd)
    return bool(res.ok and load(out))


async def summarize_skill(job: Job, slug: str, force: bool = False) -> bool:
    skill_md = series.skill_dir(slug) / "SKILL.md"
    if not skill_md.exists():
        return False
    version = series.skill_info(slug).get("version")
    out = skill_summary_path(slug)
    cur = load(out)
    if cur and cur.get("version") == version and not force:
        return True
    prompt = (
        f"Đọc skill viết series {skill_md} (tiếng Anh).\n"
        f"Viết tóm tắt TIẾNG VIỆT của phong cách này cho người viết vào đúng file {out} (JSON hợp lệ, UTF-8), "
        f"đúng cấu trúc:\n{SKILL_SCHEMA}\n"
        f"version phải là \"{version}\". Chỉ dùng thông tin có trong skill; không chép tên/sự kiện của truyện mẫu. "
        "Không emoji. Chỉ ghi file đó, không sửa file nào khác. Trả lời 'ok' khi xong."
    )
    res = await run_claude(prompt, model=MODEL, log=lambda s: job.log(f"[summary] {s}"), timeout_sec=900)
    job.add_cost(res.cost_usd)
    return bool(res.ok and load(out))


async def run_summary_job(job: Job) -> dict:
    """Job kind 'summary': params target = 'run' | 'skill', id = run id | slug, force."""
    p = job.data["params"]
    job.step("summary", "running")
    if p["target"] == "run":
        ok = await summarize_run(job, config.ANALYSES / p["id"], bool(p.get("force")))
    else:
        ok = await summarize_skill(job, p["id"], bool(p.get("force")))
    if not ok:
        raise RuntimeError("summary_vi.json was not written")
    job.step("summary", "done")
    return {"target": p["target"], "id": p["id"]}
