"""Reference-image prompts: manual edits must not be silently overridden by an old English prompt."""

import json

from conftest import write

from app.pipeline import assets


def registry(**loc_over):
    loc = {"loc_id": "loc_01", "name": "Cổng kính", "int_ext": "EXT", "desc": "Cổng vào biệt thự.",
           "layout": "Dốc đi lên tới cổng.", "fixed_elements": ["hai tấm kính cổng"],
           "variants": [{"variant_id": "loc_01_dusk", "time_of_day": "dusk", "lighting": "chiều muộn"}],
           "prompt_en": "Glass gate on a foggy hillside. Dense fog swallows everything beyond."}
    loc.update(loc_over)
    return {"version": 1, "characters": [], "props": [], "scene_map": [], "issues": [], "locations": [loc],
            "style": {"prompt_suffix_en": "photoreal"}}


def test_mark_stale_when_vietnamese_changes_but_english_does_not():
    old = registry()
    new = registry(fixed_elements=["hai tấm kính cổng", "Biệt thự 2 tầng ngay sau cổng"])
    assert assets.mark_stale_prompts(old, new) == ["loc_01"]
    assert new["locations"][0]["prompt_stale"] is True


def test_rewritten_english_clears_the_flag():
    old = registry(prompt_stale=True)
    new = registry(prompt_en="Glass gate, the two-storey villa right behind it.")
    new["locations"][0]["prompt_stale"] = True
    assert assets.mark_stale_prompts(old, new) == []
    assert "prompt_stale" not in new["locations"][0]


def test_location_prompt_carries_layout_and_drops_stale_english(tmp_path):
    d = tmp_path / "s"
    write(d / "assets" / "assets_v1.json", registry())
    edited = registry(fixed_elements=["hai tấm kính cổng", "Biệt thự 2 tầng ngay sau cổng"])
    edited["edited"] = {"by": "manual", "from": "assets_v1.json"}
    write(d / "assets" / "assets_v2.json", edited)
    prompt = assets.plan(d, ("location",), force=True)[0]["prompt"]
    assert "Biệt thự 2 tầng ngay sau cổng" in prompt and "Layout (where things are)" in prompt
    assert "swallows everything" not in prompt  # the stale English that contradicted the edit
    assert "must never hide, shrink or push them away" in prompt


def test_in_sync_english_is_kept(tmp_path):
    d = tmp_path / "s"
    write(d / "assets" / "assets_v1.json", registry(prompt_en="Glass gate; the villa stands right behind it."))
    prompt = assets.plan(d, ("location",), force=True)[0]["prompt"]
    assert "Place: Glass gate; the villa stands right behind it." in prompt


def test_image_from_older_description_is_outdated(tmp_path):
    d = tmp_path / "s"
    write(d / "assets" / "assets_v1.json", registry())
    write(d / "assets" / "assets_v2.json", registry(layout="Biệt thự ngay sau cổng, cách 20 m."))
    write(d / "assets" / "images.json", {"items": {"loc_01_dusk": {"kind": "location", "images": [
        {"file": "locations/loc_01/a.png", "status": "approved", "registry": "assets_v1.json", "created_at": "x"},
        {"file": "locations/loc_01/b.png", "status": "draft", "registry": "assets_v2.json", "created_at": "y"}]}}})
    vm = assets.view_model(d)
    imgs = {i["name"]: i["outdated"] for i in vm["reg"]["locations"][0]["variants"][0]["_img"]["images"]}
    assert imgs == {"a.png": True, "b.png": False}
